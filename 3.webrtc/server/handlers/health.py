from __future__ import annotations

from aiohttp import web

from state import pcs


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True, "peerConnections": len(pcs)})
