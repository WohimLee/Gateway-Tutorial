# aiohttp WebSocket tutorial

This example mimics the JSON frame shape of OpenClaw's Gateway WebSocket protocol.

Run the server:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python 2.websocket/aiohttp-websocket/server/app.py
```

Run the demo client in another terminal:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python 2.websocket/aiohttp-websocket/client.py
```

WebSocket endpoint:

```text
GET /__openclaw__/ws
```

Frame types:

```json
{ "type": "req", "id": "1", "method": "status", "params": {} }
```

```json
{ "type": "res", "id": "1", "ok": true, "payload": {} }
```

```json
{ "type": "event", "event": "session.message", "payload": {}, "seq": 1 }
```

The server sends `connect.challenge` first. The first client request should be
`method: "connect"`, and the successful response contains a `hello-ok` payload.

Failure response sample:

```json
{
  "type": "res",
  "id": "8",
  "ok": false,
  "error": {
    "code": "METHOD_NOT_FOUND",
    "message": "Unknown gateway method: unknown.method",
    "details": { "method": "unknown.method" },
    "retryable": false
  }
}
```
