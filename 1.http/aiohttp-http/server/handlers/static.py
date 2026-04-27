from __future__ import annotations

from aiohttp import web


def missing_static_asset(request: web.Request) -> bool:
    tail = request.match_info.get("tail", "")
    return tail in {"missing.js", "missing.css", "not-found.png"}


async def a2ui_static(request: web.Request) -> web.Response:
    if missing_static_asset(request):
        raise web.HTTPNotFound(text="static asset not found", content_type="text/plain")
    return web.Response(
        text="""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Mock A2UI</title></head>
  <body><h1>Mock A2UI</h1><p>Served by aiohttp.</p></body>
</html>
""".strip(),
        content_type="text/html",
    )


async def canvas_static(request: web.Request) -> web.Response:
    if missing_static_asset(request):
        raise web.HTTPNotFound(text="static asset not found", content_type="text/plain")
    return web.Response(
        text="""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Mock Canvas</title></head>
  <body><h1>Mock Canvas</h1><p>Canvas static resource endpoint.</p></body>
</html>
""".strip(),
        content_type="text/html",
    )


async def control_ui_static(request: web.Request) -> web.Response:
    if missing_static_asset(request):
        raise web.HTTPNotFound(text="static asset not found", content_type="text/plain")
    return web.Response(
        text="""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Mock Control UI</title></head>
  <body><h1>Mock Control UI</h1><p>controlUiBasePath = /control</p></body>
</html>
""".strip(),
        content_type="text/html",
    )
