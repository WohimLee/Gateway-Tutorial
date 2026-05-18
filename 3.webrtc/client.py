from __future__ import annotations

import argparse
import asyncio
import json
import platform

from aiohttp import ClientSession
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer


OFFER_URL = "http://127.0.0.1:8082/offer"


def default_media_args() -> tuple[str, str, dict[str, str]]:
    system = platform.system().lower()
    if system == "darwin":
        return "default:default", "avfoundation", {
            "framerate": "30",
            "video_size": "1280x720",
        }
    if system == "linux":
        return "/dev/video0", "v4l2", {
            "framerate": "30",
            "video_size": "1280x720",
        }
    if system == "windows":
        return "video=Integrated Camera", "dshow", {
            "framerate": "30",
            "video_size": "1280x720",
        }
    return "default", "", {}


async def wait_for_ice_gathering(pc: RTCPeerConnection) -> None:
    if pc.iceGatheringState == "complete":
        return

    done = asyncio.Event()

    @pc.on("icegatheringstatechange")
    def on_icegatheringstatechange() -> None:
        if pc.iceGatheringState == "complete":
            done.set()

    await done.wait()


async def main() -> None:
    source, fmt, options = default_media_args()

    parser = argparse.ArgumentParser(description="Send local camera/microphone to aiortc server.")
    parser.add_argument("--offer-url", default=OFFER_URL)
    parser.add_argument("--source", default=source, help="FFmpeg input source.")
    parser.add_argument("--format", default=fmt, help="FFmpeg input format.")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()

    player = MediaPlayer(
        args.source,
        format=args.format or None,
        options=options,
    )
    pc = RTCPeerConnection()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        print("connection state:", pc.connectionState)
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            await pc.close()

    if player.audio and not args.no_audio:
        pc.addTrack(player.audio)
        print("added audio track")
    if player.video and not args.no_video:
        pc.addTrack(player.video)
        print("added video track")

    if not pc.getTransceivers():
        raise RuntimeError("no local audio/video track was opened")

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await wait_for_ice_gathering(pc)

    async with ClientSession() as session:
        async with session.post(
            args.offer_url,
            json={
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type,
            },
        ) as response:
            response.raise_for_status()
            answer_payload = await response.json()
            print("server answer:", json.dumps({"type": answer_payload["type"]}, ensure_ascii=False))

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=answer_payload["sdp"], type=answer_payload["type"])
    )

    print("streaming. Press Ctrl+C to stop.")
    try:
        while pc.connectionState not in {"failed", "closed", "disconnected"}:
            await asyncio.sleep(1)
    finally:
        await pc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
