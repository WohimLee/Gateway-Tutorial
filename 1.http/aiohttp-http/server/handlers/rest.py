from __future__ import annotations

import json

from aiohttp import web

from .common import MOCK_SESSIONS, error_body, now_ms, read_json, run_id


async def live_probe(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "ok": True,
            "status": "live",
        }
    )


async def ready_probe(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "ready": True,
            "failing": [],
            "uptimeMs": now_ms() - request.app["started_at_ms"],
        }
    )


async def invoke_tool(request: web.Request) -> web.Response:
    body = await read_json(request)
    tool = str(body.get("tool") or "").strip()
    if not tool:
        raise web.HTTPBadRequest(
            text=json.dumps(error_body("invalid_request", "tools.invoke requires body.tool")),
            content_type="application/json",
        )
    args = body.get("args") if isinstance(body.get("args"), dict) else {}
    return web.json_response(
        {
            "ok": True,
            "result": {
                "tool": tool,
                "action": body.get("action"),
                "args": args,
                "sessionKey": body.get("sessionKey", "main"),
                "dryRun": bool(body.get("dryRun")),
                "content": f"mock result from OpenClaw tool '{tool}'",
            },
        }
    )


async def kill_session(request: web.Request) -> web.Response:
    session_key = request.match_info["sessionKey"]
    existed = session_key in MOCK_SESSIONS
    if not existed:
        raise web.HTTPNotFound(
            text=json.dumps(error_body("not_found", f"Session not found: {session_key}")),
            content_type="application/json",
        )
    return web.json_response(
        {
            "ok": True,
            "killed": existed,
        }
    )


async def hook_wake(request: web.Request) -> web.Response:
    body = await read_json(request)
    return web.json_response(
        {
            "ok": True,
            "mode": body.get("mode", "next-heartbeat"),
        }
    )


async def hook_agent(request: web.Request) -> web.Response:
    body = await read_json(request)
    if not body.get("message"):
        raise web.HTTPBadRequest(
            text=json.dumps(error_body("invalid_request", "hook agent requires body.message")),
            content_type="application/json",
        )
    return web.json_response(
        {
            "ok": True,
            "runId": run_id("hook"),
        }
    )


async def hook_mapping(request: web.Request) -> web.Response:
    body = await read_json(request)
    return web.json_response(
        {
            "ok": True,
            "runId": run_id("hook"),
        }
    )


async def mattermost_command(request: web.Request) -> web.Response:
    body = await read_json(request)
    if not body.get("text"):
        raise web.HTTPBadRequest(
            text=json.dumps(error_body("invalid_request", "mattermost command requires body.text")),
            content_type="application/json",
        )
    return web.json_response(
        {
            "ok": True,
            "channel": "mattermost",
            "type": "slash-command",
            "text": body.get("text", ""),
        }
    )


async def mattermost_dynamic(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "ok": True,
            "channel": "mattermost",
            "path": request.match_info["tail"],
        }
    )


async def slack_dynamic(request: web.Request) -> web.Response:
    body = await read_json(request)
    return web.json_response(
        {
            "ok": True,
            "channel": "slack",
            "path": request.match_info["tail"],
            "received": body,
        }
    )


async def plugin_route(request: web.Request) -> web.Response:
    body = await read_json(request)
    return web.json_response(
        {
            "ok": True,
            "pluginId": request.match_info["pluginId"],
            "path": request.match_info["tail"],
            "method": request.method,
            "received": body,
        }
    )
