# aiohttp HTTP REST tutorial

This example mimics the HTTP side of OpenClaw's gateway with aiohttp.

Run the server:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python 1.http-rest/aiohttp-http/server/app.py
```

Run the demo client in another terminal:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python 1.http-rest/aiohttp-http/client.py
```

Endpoint groups:

- REST: health/readiness, tools, sessions, hooks, Mattermost/Slack/plugin webhooks
- SSE: `GET /sessions/{sessionKey}/history` with `Accept: text/event-stream`
- OpenAI-compatible: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/embeddings`
- Static resources: `/__openclaw__/a2ui...`, `/__openclaw__/canvas...`, `/control...`
