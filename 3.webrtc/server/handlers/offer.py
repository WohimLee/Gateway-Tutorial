from __future__ import annotations

import json

from aiohttp import web
from aiortc import RTCSessionDescription

from .common import create_peer


async def offer(request: web.Request) -> web.Response:
    params = await request.json()
    offer_description = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc, _, _ = create_peer()

    await pc.setRemoteDescription(offer_description)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
            ensure_ascii=False,
        ),
    )
