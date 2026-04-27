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
        print("\n# REST /tools/invoke success sample")
        await show_json(
            session,
            "POST",
            "/tools/invoke",
            json={
                "tool": "sessions_list",
                "action": "json",
                "args": {},
                "sessionKey": "main",
                "dryRun": False,
            },
        )
        print("\n# REST /tools/invoke failure sample")
        await show_json(
            session,
            "POST",
            "/tools/invoke",
            json={
                "action": "json",
                "args": {},
                "sessionKey": "main",
            },
        )
        print("\n# REST session success/failure samples")
        await show_json(session, "POST", "/sessions/main/kill")
        await show_json(session, "POST", "/sessions/missing/kill")
        print("\n# REST webhook success/failure samples")
        await show_json(session, "POST", "/hooks/wake", json={"text": "wake up", "mode": "now"})
        await show_json(session, "POST", "/hooks/agent", json={"message": "run agent"})
        await show_json(session, "POST", "/hooks/agent", json={})
        await show_json(session, "POST", "/hooks/github", json={"event": "push"})
        await show_json(session, "POST", "/api/channels/mattermost/command", json={"text": "/ask hi"})
        await show_json(session, "POST", "/api/channels/mattermost/command", json={})
        await show_json(session, "POST", "/api/channels/slack/events", json={"type": "event_callback"})
        await show_json(session, "POST", "/plugins/demo/webhook", json={"ok": True})

        print("\n# REST JSON history success/failure samples")
        await show_json(session, "GET", "/sessions/main/history")
        await show_json(session, "GET", "/sessions/missing/history")

        print("\n# SSE history success sample")
        async with session.get(
            "/sessions/main/history",
            headers={"Accept": "text/event-stream"},
        ) as response:
            print("GET /sessions/main/history", response.status)
            async for chunk in response.content:
                print(chunk.decode().rstrip())

        print("\n# SSE history failure sample")
        await show_json(
            session,
            "GET",
            "/sessions/missing/history",
            headers={"Accept": "text/event-stream"},
        )

        print("\n# OpenAI-compatible success samples")
        await show_json(session, "GET", "/v1/models")
        await show_json(session, "GET", "/v1/models/openclaw%2Fdefault")
        await show_json(
            session,
            "POST",
            "/v1/chat/completions",
            json={
                "model": "openclaw/default",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        await show_json(
            session,
            "POST",
            "/v1/responses",
            json={"model": "openclaw/default", "input": "hi"},
        )
        await show_json(
            session,
            "POST",
            "/v1/embeddings",
            json={"model": "openclaw/default", "input": "hi"},
        )

        print("\n# OpenAI-compatible failure samples")
        await show_json(session, "GET", "/v1/models/missing-model")
        await show_json(
            session,
            "POST",
            "/v1/chat/completions",
            json={"model": "openclaw/default"},
        )
        await show_json(
            session,
            "POST",
            "/v1/responses",
            json={"model": "openclaw/default"},
        )
        await show_json(
            session,
            "POST",
            "/v1/embeddings",
            json={"model": "openclaw/default"},
        )

        print("\n# Static resources success/failure samples")
        await show_text(session, "GET", "/__openclaw__/a2ui/")
        await show_text(session, "GET", "/__openclaw__/canvas/")
        await show_text(session, "GET", "/control")
        await show_text(session, "GET", "/__openclaw__/a2ui/missing.js")


if __name__ == "__main__":
    asyncio.run(main())
