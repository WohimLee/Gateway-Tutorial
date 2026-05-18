# aiohttp WebRTC tutorial

This example uses `aiohttp` for HTTP signaling and `aiortc` for WebRTC media.
The server receives real-time audio/video tracks and consumes frames.

The browser page uses WebSocket signaling with trickle ICE, so it sends the
offer immediately and streams ICE candidates as they are discovered. The
`POST /offer` endpoint is kept as a simpler non-trickle reference path for the
Python client.

Run the server:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --project 3.webrtc python 3.webrtc/server/app.py
```

The server only exposes signaling and receiving endpoints. It does not open
camera/microphone devices and does not serve a browser UI.

Open the browser client file separately:

```text
3.webrtc/browser-client/index.html
```

Click start in the page. The browser will ask for camera and microphone
permission, then send both tracks to `ws://127.0.0.1:8082/ws`.

You can also run the Python aiortc client in another terminal:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --project 3.webrtc python 3.webrtc/client.py
```

On macOS, the default Python client uses FFmpeg's `avfoundation` input:

```text
default:default
```

If your device names differ, list FFmpeg devices first:

```bash
ffmpeg -f avfoundation -list_devices true -i ""
```

Then pass the selected input:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --project 3.webrtc python 3.webrtc/client.py --source "0:0"
```

Endpoints:

```text
GET  /health
GET  /ws
POST /offer
```

`GET /ws` accepts JSON signaling messages:

```json
{ "type": "offer", "description": { "sdp": "...", "type": "offer" } }
```

```json
{ "type": "candidate", "candidate": { "candidate": "...", "sdpMid": "0", "sdpMLineIndex": 0 } }
```

`POST /offer` accepts a WebRTC offer in the simpler non-trickle flow:

```json
{ "sdp": "...", "type": "offer" }
```

and returns an answer:

```json
{ "sdp": "...", "type": "answer" }
```
