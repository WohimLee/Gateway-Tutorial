from __future__ import annotations

import asyncio
import json
import uuid

from aiohttp import WSMsgType, web

from .common import TICK_INTERVAL_MS, error_response, event_frame, now_ms, send_json
from .methods import handle_method


async def tick_loop(ws: web.WebSocketResponse, stop: asyncio.Event) -> None:
    seq = 100
    try:
        while not stop.is_set():
            await asyncio.sleep(TICK_INTERVAL_MS / 1000)
            seq += 1
            await send_json(
                ws,
                event_frame(
                    "tick",
                    {"ts": now_ms()},
                    seq=seq,
                    state_version={"presence": 1, "health": 1},
                ),
            )
    except (asyncio.CancelledError, ConnectionResetError):
        return


async def gateway_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    stop_ticks = asyncio.Event()
    tick_task = asyncio.create_task(tick_loop(ws, stop_ticks))
    connected = False
    challenge_nonce = str(uuid.uuid4())
    await send_json(
        ws,
        event_frame(
            "connect.challenge",
            {"nonce": challenge_nonce, "ts": now_ms()},
            seq=0,
            state_version={"presence": 0, "health": 0},
        ),
    )

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    frame = json.loads(msg.data)
                except json.JSONDecodeError:
                    await send_json(
                        ws,
                        error_response(
                            "invalid-json",
                            "INVALID_JSON",
                            "websocket text frames must contain JSON",
                        ),
                    )
                    continue

                if not isinstance(frame, dict) or frame.get("type") != "req":
                    frame_id = str(frame.get("id") if isinstance(frame, dict) else "invalid-frame")
                    await send_json(
                        ws,
                        error_response(
                            frame_id,
                            "INVALID_FRAME",
                            "expected request frame: {type:'req', id, method, params}",
                        ),
                    )
                    continue

                connected = await handle_method(ws, frame, connected=connected)
            elif msg.type == WSMsgType.ERROR:
                break
    finally:
        stop_ticks.set()
        tick_task.cancel()
        await asyncio.gather(tick_task, return_exceptions=True)

    return ws
