# aiohttp HTTP REST tutorial

This example mimics the HTTP side of OpenClaw's gateway with aiohttp.

Run the server:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python 1.http/aiohttp-http/server/app.py
```

Run the demo client in another terminal:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python 1.http/aiohttp-http/client.py
```

Endpoint groups:

- REST: health/readiness, tools, sessions, hooks, Mattermost/Slack/plugin webhooks
- SSE: `GET /sessions/{sessionKey}/history` with `Accept: text/event-stream`
- OpenAI-compatible: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/embeddings`
- Static resources: `/__openclaw__/a2ui...`, `/__openclaw__/canvas...`, `/control...`

## Request and response samples

OpenClaw-style tool invoke request:

```json
{
  "tool": "sessions_list",
  "action": "json",
  "args": {},
  "sessionKey": "main",
  "dryRun": false
}
```

Success response sample:

```json
{
  "ok": true,
  "result": {
    "tool": "sessions_list",
    "action": "json",
    "args": {},
    "sessionKey": "main",
    "dryRun": false,
    "content": "mock result from OpenClaw tool 'sessions_list'"
  }
}
```

REST failure response sample:

```json
{
  "ok": false,
  "error": {
    "type": "invalid_request",
    "message": "tools.invoke requires body.tool"
  }
}
```

SSE failure response sample:

```json
{
  "ok": false,
  "error": {
    "type": "not_found",
    "message": "Session not found: missing"
  }
}
```

OpenAI-compatible failure response sample:

```json
{
  "error": {
    "message": "'messages' is required and must be a non-empty array.",
    "type": "invalid_request_error"
  }
}
```

Static resource failure sample:

```text
HTTP 404
static asset not found
```
