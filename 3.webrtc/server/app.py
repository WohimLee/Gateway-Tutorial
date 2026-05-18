from __future__ import annotations

from aiohttp import web

from config import HEALTH_PATH, HOST, PORT, SIGNALING_PATH, WEBRTC_PATH
from handlers import health, offer, on_shutdown, signaling


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get(HEALTH_PATH, health, allow_head=True)
    app.router.add_get(SIGNALING_PATH, signaling)
    app.router.add_post(WEBRTC_PATH, offer)
    app.on_shutdown.append(on_shutdown)
    return app


app = create_app()


if __name__ == "__main__":
    web.run_app(app, host=HOST, port=PORT)
