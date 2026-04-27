from __future__ import annotations

from aiohttp import web

from handlers import WS_PATH, gateway_ws, health


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get(WS_PATH, gateway_ws)
    return app


app = create_app()


if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8081)
