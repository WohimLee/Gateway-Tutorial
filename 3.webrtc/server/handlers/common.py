from __future__ import annotations

import asyncio
import contextlib
import time

from aiohttp import web
from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection
from aiortc.mediastreams import MediaStreamError
from aiortc.rtcicetransport import RTCIceCandidate
from aiortc.sdp import candidate_from_sdp

from config import FRAME_LOG_INTERVAL, STUN_SERVERS
from state import pcs


async def consume_track(peer_id: str, track) -> None:
    started_at = time.monotonic()
    frame_count = 0
    print(f"[{peer_id}] receiving {track.kind} track id={track.id}")

    try:
        while True:
            frame = await track.recv()
            frame_count += 1

            if frame_count == 1 or frame_count % FRAME_LOG_INTERVAL == 0:
                elapsed = max(time.monotonic() - started_at, 0.001)
                rate = frame_count / elapsed
                extra = ""
                if track.kind == "video":
                    extra = f" size={frame.width}x{frame.height}"
                elif track.kind == "audio":
                    extra = f" samples={frame.samples} rate={frame.sample_rate}"
                print(
                    f"[{peer_id}] {track.kind} frames={frame_count} "
                    f"rate={rate:.1f}/s pts={frame.pts}{extra}"
                )
    except MediaStreamError:
        print(f"[{peer_id}] {track.kind} track ended after {frame_count} frames")
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"[{peer_id}] {track.kind} track error: {exc!r}")


def create_peer() -> tuple[RTCPeerConnection, str, set[asyncio.Task[None]]]:
    config = RTCConfiguration(iceServers=[RTCIceServer(urls=STUN_SERVERS)])
    pc = RTCPeerConnection(configuration=config)
    pcs.add(pc)

    peer_id = f"pc-{id(pc):x}"
    tasks: set[asyncio.Task[None]] = set()
    print(f"[{peer_id}] created")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        print(f"[{peer_id}] connection state: {pc.connectionState}")
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            await close_peer(pc, tasks, peer_id)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange() -> None:
        print(f"[{peer_id}] ice state: {pc.iceConnectionState}")

    @pc.on("track")
    def on_track(track) -> None:
        task = asyncio.create_task(consume_track(peer_id, track))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

        @track.on("ended")
        async def on_ended() -> None:
            print(f"[{peer_id}] track ended: {track.kind}")

    return pc, peer_id, tasks


def parse_candidate(payload: dict | None) -> RTCIceCandidate | None:
    if payload is None:
        return None

    candidate_sdp = payload["candidate"]
    if candidate_sdp.startswith("candidate:"):
        candidate_sdp = candidate_sdp[len("candidate:") :]

    candidate = candidate_from_sdp(candidate_sdp)
    candidate.sdpMid = payload.get("sdpMid")
    candidate.sdpMLineIndex = payload.get("sdpMLineIndex")
    return candidate


async def close_peer(
    pc: RTCPeerConnection,
    tasks: set[asyncio.Task[None]],
    peer_id: str,
) -> None:
    if pc not in pcs:
        return

    pcs.discard(pc)
    for task in list(tasks):
        task.cancel()
    for task in list(tasks):
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await pc.close()
    print(f"[{peer_id}] closed")


async def on_shutdown(_: web.Application) -> None:
    coros = [pc.close() for pc in pcs]
    if coros:
        await asyncio.gather(*coros)
    pcs.clear()
