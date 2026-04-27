from __future__ import annotations

import json
import time
import uuid
from typing import Any
from urllib.parse import unquote

from aiohttp import web

from .common import MOCK_MODELS, openai_error, read_json


def raise_openai_bad_request(message: str) -> None:
    raise web.HTTPBadRequest(
        text=json.dumps(openai_error(message)),
        content_type="application/json",
    )


def openai_model(model_id: str) -> dict[str, Any]:
    return {
        "id": model_id,
        "object": "model",
        "created": 0,
        "owned_by": "openclaw",
        "permission": [],
    }


async def list_models(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "object": "list",
            "data": [openai_model(model_id) for model_id in MOCK_MODELS],
        }
    )


async def retrieve_model(request: web.Request) -> web.Response:
    model_id = unquote(request.match_info["modelId"])
    if model_id not in MOCK_MODELS:
        raise web.HTTPNotFound(
            text=json.dumps(openai_error(f"Model '{model_id}' not found.")),
            content_type="application/json",
        )
    return web.json_response(openai_model(model_id))


async def chat_completions(request: web.Request) -> web.Response:
    body = await read_json(request)
    model = body.get("model") or "openclaw/default"
    messages = body.get("messages") if isinstance(body.get("messages"), list) else []
    if not messages:
        raise_openai_bad_request("'messages' is required and must be a non-empty array.")
    last_user = next(
        (
            msg.get("content")
            for msg in reversed(messages)
            if isinstance(msg, dict) and msg.get("role") == "user"
        ),
        "",
    )
    return web.json_response(
        {
            "id": f"chatcmpl_{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"mock chat completion response to: {last_user}",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    )


async def responses(request: web.Request) -> web.Response:
    body = await read_json(request)
    if "input" not in body:
        raise_openai_bad_request("'input' is required.")
    user_input = body.get("input", "")
    response_id = f"resp_{uuid.uuid4()}"
    output_id = f"msg_{uuid.uuid4()}"
    return web.json_response(
        {
            "id": response_id,
            "object": "response",
            "created_at": int(time.time()),
            "status": "completed",
            "model": body.get("model", "openclaw/default"),
            "output": [
                {
                    "type": "message",
                    "id": output_id,
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": f"mock response output for: {user_input}",
                        }
                    ],
                    "status": "completed",
                }
            ],
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        }
    )


async def embeddings(request: web.Request) -> web.Response:
    body = await read_json(request)
    if "input" not in body:
        raise_openai_bad_request("'input' is required.")
    raw_input = body.get("input", "")
    inputs = raw_input if isinstance(raw_input, list) else [raw_input]
    return web.json_response(
        {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": index,
                    "embedding": [0.1, 0.2, 0.3],
                }
                for index, _ in enumerate(inputs)
            ],
            "model": body.get("model", "openclaw/default"),
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }
    )
