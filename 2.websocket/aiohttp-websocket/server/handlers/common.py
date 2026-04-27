from __future__ import annotations

import json
import time
from typing import Any

from aiohttp import web


PROTOCOL_VERSION = 3
WS_PATH = "/__openclaw__/ws"
MAX_PAYLOAD = 2 * 1024 * 1024
MAX_BUFFERED_BYTES = 8 * 1024 * 1024
TICK_INTERVAL_MS = 15_000

METHODS = [
    "health",
    "status",
    "models.list",
    "tools.catalog",
    "sessions.list",
    "sessions.subscribe",
    "sessions.unsubscribe",
    "chat.history",
    "chat.send",
    "agent",
    "wake",
    "node.list",
]

EVENTS = [
    "connect.challenge",
    "agent",
    "chat",
    "session.message",
    "sessions.changed",
    "presence",
    "tick",
    "health",
    "heartbeat",
    "shutdown",
    "node.invoke.request",
]

STARTED_AT_MS = int(time.time() * 1000)

MOCK_SESSIONS: dict[str, list[dict[str, Any]]] = {
    "main": [
        {
            "role": "user",
            "content": [{"type": "text", "text": "hello gateway"}],
            "timestamp": 1_737_264_000_000,
            "__openclaw": {"id": "msg-user-1", "seq": 1},
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "hello from mock OpenClaw websocket"}],
            "timestamp": 1_737_264_001_000,
            "__openclaw": {"id": "msg-assistant-1", "seq": 2},
        },
    ],
}


def now_ms() -> int:
    return int(time.time() * 1000)


def event_frame(
    event: str,
    payload: Any | None = None,
    *,
    seq: int | None = None,
    state_version: dict[str, int] | None = None,
) -> dict[str, Any]:
    frame: dict[str, Any] = {"type": "event", "event": event}
    if payload is not None:
        frame["payload"] = payload
    if seq is not None:
        frame["seq"] = seq
    if state_version is not None:
        frame["stateVersion"] = state_version
    return frame


def ok_response(frame_id: str, payload: Any | None = None) -> dict[str, Any]:
    frame: dict[str, Any] = {"type": "res", "id": frame_id, "ok": True}
    if payload is not None:
        frame["payload"] = payload
    return frame


def error_response(
    frame_id: str,
    code: str,
    message: str,
    *,
    details: Any | None = None,
    retryable: bool | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    if retryable is not None:
        error["retryable"] = retryable
    return {"type": "res", "id": frame_id, "ok": False, "error": error}


def snapshot(client: dict[str, Any] | None = None) -> dict[str, Any]:
    client = client or {}
    device_id = (
        client.get("instanceId")
        or client.get("modelIdentifier")
        or client.get("id")
        or "mock-device"
    )
    return {
        "presence": [
            {
                "host": "mock-gateway",
                "version": client.get("version", "0.0.0"),
                "platform": client.get("platform", "unknown"),
                "deviceFamily": client.get("deviceFamily", "desktop"),
                "mode": client.get("mode", "operator"),
                "ts": now_ms(),
                "deviceId": device_id,
                "roles": ["operator"],
                "scopes": ["operator.read", "operator.write"],
                "instanceId": client.get("instanceId", "mock-instance"),
            }
        ],
        "health": {"ok": True, "status": "ready"},
        "stateVersion": {"presence": 1, "health": 1},
        "uptimeMs": now_ms() - STARTED_AT_MS,
        "configPath": "~/.openclaw/openclaw.json",
        "stateDir": "~/.openclaw",
        "sessionDefaults": {
            "defaultAgentId": "main",
            "mainKey": "main",
            "mainSessionKey": "main",
            "scope": "agent",
        },
        "authMode": "none",
    }


def hello_ok(params: dict[str, Any], conn_id: str) -> dict[str, Any]:
    max_protocol = int(params.get("maxProtocol") or PROTOCOL_VERSION)
    protocol = min(PROTOCOL_VERSION, max_protocol)
    client = params.get("client") if isinstance(params.get("client"), dict) else {}
    return {
        "type": "hello-ok",
        "protocol": protocol,
        "server": {
            "version": "mock-openclaw-gateway/0.1.0",
            "connId": conn_id,
        },
        "features": {
            "methods": METHODS,
            "events": EVENTS,
        },
        "snapshot": snapshot(client),
        "canvasHostUrl": "http://127.0.0.1:8081/__openclaw__/canvas/",
        "auth": {
            "deviceToken": f"mock-device-token-{conn_id}",
            "role": params.get("role", "operator"),
            "scopes": params.get("scopes", ["operator.read", "operator.write"]),
            "issuedAtMs": now_ms(),
        },
        "policy": {
            "maxPayload": MAX_PAYLOAD,
            "maxBufferedBytes": MAX_BUFFERED_BYTES,
            "tickIntervalMs": TICK_INTERVAL_MS,
        },
    }


async def send_json(ws: web.WebSocketResponse, frame: dict[str, Any]) -> None:
    await ws.send_str(json.dumps(frame, ensure_ascii=False))
