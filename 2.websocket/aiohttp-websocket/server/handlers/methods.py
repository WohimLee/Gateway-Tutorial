from __future__ import annotations

import uuid
from typing import Any

from aiohttp import web

from .common import (
    MOCK_SESSIONS,
    PROTOCOL_VERSION,
    STARTED_AT_MS,
    error_response,
    event_frame,
    hello_ok,
    now_ms,
    ok_response,
    send_json,
    snapshot,
)


async def handle_method(
    ws: web.WebSocketResponse,
    frame: dict[str, Any],
    *,
    connected: bool,
) -> bool:
    frame_id = str(frame.get("id") or "")
    method = str(frame.get("method") or "")
    params = frame.get("params") if isinstance(frame.get("params"), dict) else {}

    if not frame_id:
        await send_json(ws, error_response("missing-id", "INVALID_FRAME", "request id is required"))
        return connected

    if method == "connect":
        min_protocol = int(params.get("minProtocol") or 0)
        max_protocol = int(params.get("maxProtocol") or 0)
        if min_protocol > PROTOCOL_VERSION or max_protocol < PROTOCOL_VERSION:
            await send_json(
                ws,
                error_response(
                    frame_id,
                    "PROTOCOL_VERSION_UNSUPPORTED",
                    "protocol version mismatch",
                    details={"serverProtocol": PROTOCOL_VERSION},
                    retryable=False,
                ),
            )
            return False
        await send_json(ws, ok_response(frame_id, hello_ok(params, str(uuid.uuid4()))))
        client = params.get("client") if isinstance(params.get("client"), dict) else {}
        await send_json(
            ws,
            event_frame(
                "presence",
                snapshot(client)["presence"],
                seq=1,
                state_version={"presence": 1, "health": 1},
            ),
        )
        return True

    if not connected:
        await send_json(
            ws,
            error_response(
                frame_id,
                "CONNECT_REQUIRED",
                "first client request must be method=connect",
                retryable=False,
            ),
        )
        return connected

    if method == "health":
        await send_json(ws, ok_response(frame_id, {"ok": True, "status": "ready"}))
    elif method == "status":
        await send_json(
            ws,
            ok_response(
                frame_id,
                {
                    "ok": True,
                    "version": "mock-openclaw-gateway/0.1.0",
                    "uptimeMs": now_ms() - STARTED_AT_MS,
                    "protocol": PROTOCOL_VERSION,
                },
            ),
        )
    elif method == "models.list":
        await send_json(
            ws,
            ok_response(
                frame_id,
                {
                    "models": [
                        {"id": "openclaw/default", "provider": "mock", "name": "OpenClaw Default"},
                        {"id": "openclaw/coder", "provider": "mock", "name": "OpenClaw Coder"},
                    ]
                },
            ),
        )
    elif method == "sessions.list":
        await send_json(
            ws,
            ok_response(
                frame_id,
                {
                    "sessions": [
                        {
                            "key": "main",
                            "sessionId": "mock-session-main",
                            "kind": "chat",
                            "channel": "webchat",
                            "subject": "Mock WebSocket Session",
                            "updatedAt": now_ms(),
                        }
                    ]
                },
            ),
        )
    elif method == "chat.history":
        await handle_chat_history(ws, frame_id, params)
    elif method in {"sessions.subscribe", "sessions.unsubscribe"}:
        await send_json(ws, ok_response(frame_id, {"subscribed": method.endswith("subscribe")}))
    elif method == "chat.send":
        await handle_chat_send(ws, frame_id, params)
    elif method == "node.list":
        await send_json(
            ws,
            ok_response(
                frame_id,
                {
                    "nodes": [
                        {
                            "id": "mock-ios-node",
                            "status": "online",
                            "caps": ["camera", "canvas", "screen", "location"],
                        }
                    ]
                },
            ),
        )
    else:
        await send_json(
            ws,
            error_response(
                frame_id,
                "METHOD_NOT_FOUND",
                f"Unknown gateway method: {method}",
                details={"method": method},
                retryable=False,
            ),
        )
    return connected


async def handle_chat_history(
    ws: web.WebSocketResponse,
    frame_id: str,
    params: dict[str, Any],
) -> None:
    session_key = str(params.get("sessionKey") or "main")
    if session_key not in MOCK_SESSIONS:
        await send_json(ws, error_response(frame_id, "NOT_FOUND", f"Session not found: {session_key}"))
        return

    await send_json(
        ws,
        ok_response(
            frame_id,
            {
                "sessionKey": session_key,
                "messages": MOCK_SESSIONS[session_key],
                "hasMore": False,
            },
        ),
    )


async def handle_chat_send(
    ws: web.WebSocketResponse,
    frame_id: str,
    params: dict[str, Any],
) -> None:
    session_key = str(params.get("sessionKey") or "main")
    text = str(params.get("message") or params.get("text") or "").strip()
    if not text:
        await send_json(
            ws,
            error_response(frame_id, "INVALID_REQUEST", "chat.send requires params.message"),
        )
        return

    message = {
        "role": "assistant",
        "content": [{"type": "text", "text": f"mock reply to: {text}"}],
        "timestamp": now_ms(),
        "__openclaw": {"id": f"msg-{uuid.uuid4()}", "seq": 3},
    }
    MOCK_SESSIONS.setdefault(session_key, []).append(message)
    await send_json(ws, ok_response(frame_id, {"status": "ok", "sessionKey": session_key}))
    await send_json(
        ws,
        event_frame(
            "session.message",
            {
                "sessionKey": session_key,
                "message": message,
                "messageId": message["__openclaw"]["id"],
                "messageSeq": message["__openclaw"]["seq"],
            },
            seq=2,
            state_version={"presence": 1, "health": 1},
        ),
    )
    await send_json(ws, event_frame("chat", {"sessionKey": session_key, "status": "completed"}, seq=3))
