from __future__ import annotations

import json

from aiohttp import WSMsgType, web
from aiortc import RTCSessionDescription

from .common import close_peer, create_peer, parse_candidate


async def signaling(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    pc, peer_id, tasks = create_peer()
    print(f"[{peer_id}] signaling websocket opened")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                payload = json.loads(msg.data)

                if payload["type"] == "offer":
                    description = payload["description"]
                    await pc.setRemoteDescription(
                        RTCSessionDescription(
                            sdp=description["sdp"],
                            type=description["type"],
                        )
                    )
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    await ws.send_json(
                        {
                            "type": "answer",
                            "description": {
                                "sdp": pc.localDescription.sdp,
                                "type": pc.localDescription.type,
                            },
                        }
                    )
                    print(f"[{peer_id}] answer sent")
                elif payload["type"] == "candidate":
                    await pc.addIceCandidate(parse_candidate(payload.get("candidate")))
                else:
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": f"unknown signaling message: {payload['type']}",
                        }
                    )
            elif msg.type == WSMsgType.ERROR:
                print(f"[{peer_id}] websocket error: {ws.exception()!r}")
    finally:
        await close_peer(pc, tasks, peer_id)

    return ws
