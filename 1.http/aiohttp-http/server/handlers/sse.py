from __future__ import annotations

import asyncio
import json
from typing import Any

from aiohttp import web

from .common import MOCK_SESSIONS, error_body, now_ms, session_snapshot


async def session_history(request: web.Request) -> web.StreamResponse:
    session_key = request.match_info["sessionKey"]
    if session_key not in MOCK_SESSIONS:
        raise web.HTTPNotFound(
            text=json.dumps(error_body("not_found", f"Session not found: {session_key}")),
            content_type="application/json",
        )
    messages = MOCK_SESSIONS.get(session_key, [])
    payload = {
        "sessionKey": session_key,
        "items": messages,
        "messages": messages,
        "hasMore": False,
        **session_snapshot(session_key),
    }

    accept = request.headers.get("accept", "").lower()
    if "text/event-stream" not in accept:
        return web.json_response(payload)

    response = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
        },
    )
    await response.prepare(request)
    await write_sse(response, "history", payload)
    await asyncio.sleep(0.2)
    await write_sse(
        response,
        "message",
        {
            "sessionKey": session_key,
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "mock streaming history update"}],
                "timestamp": now_ms(),
                "__openclaw": {"id": "msg-stream-1", "seq": len(messages) + 1},
            },
            "messageId": "msg-stream-1",
            "messageSeq": len(messages) + 1,
            **session_snapshot(session_key),
        },
    )
    await response.write_eof()
    return response


async def write_sse(response: web.StreamResponse, event: str, payload: Any) -> None:
    await response.write(f"event: {event}\n".encode())
    await response.write(f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode())
