from __future__ import annotations

import asyncio
import json
from typing import Any

from aiohttp import ClientSession, WSMsgType


WS_URL = "http://127.0.0.1:8081/__openclaw__/ws"


def req(frame_id: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    frame: dict[str, Any] = {
        "type": "req",
        "id": frame_id,
        "method": method,
    }
    if params is not None:
        frame["params"] = params
    return frame


async def send_frame(ws, frame: dict[str, Any]) -> None:
    print("client ->", json.dumps(frame, ensure_ascii=False))
    await ws.send_str(json.dumps(frame, ensure_ascii=False))


async def recv_frame(ws) -> dict[str, Any]:
    msg = await ws.receive()
    if msg.type != WSMsgType.TEXT:
        raise RuntimeError(f"unexpected websocket message: {msg.type}")
    frame = json.loads(msg.data)
    print("server <-", json.dumps(frame, ensure_ascii=False))
    return frame


async def main() -> None:
    async with ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            print("\n# Server pre-connect challenge event")
            challenge = await recv_frame(ws)
            nonce = challenge["payload"]["nonce"]

            print("\n# Connect request and hello-ok response")
            await send_frame(
                ws,
                req(
                    "1",
                    "connect",
                    {
                        "minProtocol": 3,
                        "maxProtocol": 3,
                        "client": {
                            "id": "cli",
                            "displayName": "Tutorial CLI",
                            "version": "0.1.0",
                            "platform": "macos",
                            "deviceFamily": "desktop",
                            "modelIdentifier": "MacBookAir",
                            "mode": "cli",
                            "instanceId": "tutorial-cli-1",
                        },
                        "role": "operator",
                        "scopes": ["operator.read", "operator.write"],
                        "caps": ["tool-events"],
                        "commands": [],
                        "permissions": {},
                        "auth": {"token": "mock-token"},
                        "locale": "zh-CN",
                        "userAgent": "gateway-tutorial/0.1.0",
                        "device": {
                            "id": "mock-device-fingerprint",
                            "publicKey": "mock-public-key",
                            "signature": "mock-signature",
                            "signedAt": 1_737_264_000_000,
                            "nonce": nonce,
                        },
                    },
                ),
            )
            await recv_frame(ws)
            await recv_frame(ws)

            print("\n# Successful req/res samples")
            await send_frame(ws, req("2", "status"))
            await recv_frame(ws)
            await send_frame(ws, req("3", "sessions.list"))
            await recv_frame(ws)
            await send_frame(ws, req("4", "chat.history", {"sessionKey": "main"}))
            await recv_frame(ws)

            print("\n# Successful chat.send plus event frames")
            await send_frame(
                ws,
                req(
                    "5",
                    "chat.send",
                    {
                        "sessionKey": "main",
                        "message": "用 websocket 发一条消息",
                        "idempotencyKey": "tutorial-chat-send-1",
                    },
                ),
            )
            await recv_frame(ws)
            await recv_frame(ws)
            await recv_frame(ws)

            print("\n# Failure req/res samples")
            await send_frame(ws, req("6", "chat.history", {"sessionKey": "missing"}))
            await recv_frame(ws)
            await send_frame(ws, req("7", "chat.send", {"sessionKey": "main"}))
            await recv_frame(ws)
            await send_frame(ws, req("8", "unknown.method"))
            await recv_frame(ws)


if __name__ == "__main__":
    asyncio.run(main())
