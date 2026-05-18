
# http 服务
# UV_CACHE_DIR=/tmp/uv-cache uv run python 1.http/aiohttp-http/server/app.py

# websocket 服务
# UV_CACHE_DIR=/tmp/uv-cache uv run python 2.websocket/aiohttp-websocket/server/app.py

# webrtc 服务
## 启动网页端：http://127.0.0.1:8082/
UV_CACHE_DIR=/tmp/uv-cache uv run 3.webrtc/server/app.py

# UV_CACHE_DIR=/tmp/uv-cache uv run 3.webrtc/client.py
