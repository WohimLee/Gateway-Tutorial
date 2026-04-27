from __future__ import annotations

import asyncio

from aiohttp import ClientSession


BASE_URL = "http://127.0.0.1:8080"


async def show_json(session: ClientSession, method: str, path: str, **kwargs) -> None:
    async with session.request(method, path, **kwargs) as response:
        print(method, path, response.status, await response.json())


async def show_text(session: ClientSession, method: str, path: str, **kwargs) -> None:
    async with session.request(method, path, **kwargs) as response:
        text = await response.text()
        print(method, path, response.status, text[:100].replace("\n", " "))


async def main() -> None:
    async with ClientSession(BASE_URL) as session:
        print("\n# REST")
        await show_json(session, "GET", "/health")
        await show_json(session, "GET", "/ready")
        await show_json(session, "POST", "/tools/invoke", json={"tool": "memory_search"})
        await show_json(session, "POST", "/sessions/main/kill")
        await show_json(session, "POST", "/hooks/wake", json={"text": "wake up", "mode": "now"})
        await show_json(session, "POST", "/hooks/agent", json={"message": "run agent"})
        await show_json(session, "POST", "/hooks/github", json={"event": "push"})
        await show_json(session, "POST", "/api/channels/mattermost/command", json={"text": "/ask hi"})
        await show_json(session, "POST", "/api/channels/slack/events", json={"type": "event_callback"})
        await show_json(session, "POST", "/plugins/demo/webhook", json={"ok": True})

        print("\n# REST JSON history")
        await show_json(session, "GET", "/sessions/main/history")

        print("\n# SSE history")
        async with session.get(
            "/sessions/main/history",
            headers={"Accept": "text/event-stream"},
        ) as response:
            print("GET /sessions/main/history", response.status)
            async for chunk in response.content:
                print(chunk.decode().rstrip())

        print("\n# OpenAI-compatible")
        await show_json(session, "GET", "/v1/models")
        await show_json(session, "GET", "/v1/models/wigainneo%2Fdefault")
        await show_json(
            session,
            "POST",
            "/v1/chat/completions",
            json={
                "model": "wigainneo/default",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        await show_json(
            session,
            "POST",
            "/v1/responses",
            json={"model": "wigainneo/default", "input": "hi"},
        )
        await show_json(
            session,
            "POST",
            "/v1/embeddings",
            json={"model": "wigainneo/default", "input": "hi"},
        )

        print("\n# Static resources")
        await show_text(session, "GET", "/__wigainneo__/a2ui/")
        await show_text(session, "GET", "/__wigainneo__/canvas/")
        await show_text(session, "GET", "/control")


if __name__ == "__main__":
    asyncio.run(main())
