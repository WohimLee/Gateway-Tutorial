from __future__ import annotations

import json
import time
import uuid
from typing import Any

from aiohttp import web


HOOKS_BASE_PATH = "/hooks"
CONTROL_UI_BASE_PATH = "/control"

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
            "content": [{"type": "text", "text": "hello from mock OpenClaw gateway"}],
            "timestamp": 1_737_264_001_000,
            "__openclaw": {"id": "msg-assistant-1", "seq": 2},
        },
    ]
}

MOCK_MODELS = [
    "openclaw",
    "openclaw/default",
    "openclaw/coder",
]


async def read_json(request: web.Request) -> dict[str, Any]:
    if not request.can_read_body:
        return {}
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise web.HTTPBadRequest(
            text=json.dumps({"ok": False, "error": "invalid json"}),
            content_type="application/json",
        ) from exc
    return body if isinstance(body, dict) else {"value": body}


def now_ms() -> int:
    return int(time.time() * 1000)


def error_body(error_type: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"type": error_type, "message": message}}


def openai_error(message: str, error_type: str = "invalid_request_error") -> dict[str, Any]:
    return {"error": {"message": message, "type": error_type}}


def session_snapshot(session_key: str) -> dict[str, Any]:
    return {
        "session": {
            "key": session_key,
            "sessionId": f"mock-session-{session_key}",
            "kind": "chat",
            "channel": "webchat",
            "subject": "Mock Gateway Tutorial",
            "label": "Mock Gateway Tutorial",
            "displayName": "Mock Gateway Tutorial",
            "updatedAt": now_ms(),
            "status": "idle",
            "model": "openclaw/default",
            "modelProvider": "mock",
        },
        "sessionId": f"mock-session-{session_key}",
        "kind": "chat",
        "channel": "webchat",
        "subject": "Mock Gateway Tutorial",
    }


def run_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"
