from __future__ import annotations

import time

from aiohttp import web

from handlers import (
    a2ui_static,
    canvas_static,
    chat_completions,
    control_ui_static,
    embeddings,
    hook_agent,
    hook_mapping,
    hook_wake,
    invoke_tool,
    kill_session,
    list_models,
    live_probe,
    mattermost_command,
    mattermost_dynamic,
    plugin_route,
    ready_probe,
    responses,
    retrieve_model,
    session_history,
    slack_dynamic,
)


def create_app() -> web.Application:
    app = web.Application()
    app["started_at_ms"] = int(time.time() * 1000)

    # REST endpoints: health/readiness probes.
    app.router.add_get("/health", live_probe, allow_head=True)
    app.router.add_get("/healthz", live_probe, allow_head=True)
    app.router.add_get("/ready", ready_probe, allow_head=True)
    app.router.add_get("/readyz", ready_probe, allow_head=True)

    # REST endpoints: tools, sessions, hooks, channel/plugin webhooks.
    app.router.add_post("/tools/invoke", invoke_tool)
    app.router.add_post("/sessions/{sessionKey}/kill", kill_session)
    app.router.add_post("/hooks/wake", hook_wake)
    app.router.add_post("/hooks/agent", hook_agent)
    app.router.add_post("/hooks/{mappingPath:.*}", hook_mapping)
    app.router.add_post("/api/channels/mattermost/command", mattermost_command)
    app.router.add_route("*", "/api/channels/mattermost/{tail:.*}", mattermost_dynamic)
    app.router.add_route("*", "/api/channels/slack/{tail:.*}", slack_dynamic)
    app.router.add_route("*", "/plugins/{pluginId}/{tail:.*}", plugin_route)

    # SSE endpoint: also returns REST JSON unless Accept includes text/event-stream.
    app.router.add_get("/sessions/{sessionKey}/history", session_history)

    # OpenAI-compatible endpoints.
    app.router.add_get("/v1/models", list_models)
    app.router.add_get("/v1/models/{modelId:.*}", retrieve_model)
    app.router.add_post("/v1/chat/completions", chat_completions)
    app.router.add_post("/v1/responses", responses)
    app.router.add_post("/v1/embeddings", embeddings)

    # Static resource endpoints.
    app.router.add_get("/__wigainneo__/a2ui", a2ui_static, allow_head=True)
    app.router.add_get("/__wigainneo__/a2ui/{tail:.*}", a2ui_static, allow_head=True)
    app.router.add_get("/__wigainneo__/canvas", canvas_static, allow_head=True)
    app.router.add_get("/__wigainneo__/canvas/{tail:.*}", canvas_static, allow_head=True)
    app.router.add_get("/control/{tail:.*}", control_ui_static, allow_head=True)
    app.router.add_get("/control", control_ui_static, allow_head=True)

    return app


app = create_app()


if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8080)
