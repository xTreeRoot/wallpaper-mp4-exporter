from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import ProbeInfo


def require_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"Missing required tool: {name}. Install ffmpeg and make sure it is on PATH.")
    return found


def doctor() -> dict[str, Any]:
    result = {
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "cryptography": False,
    }
    try:
        import cryptography  # noqa: F401

        result["cryptography"] = True
    except ImportError:
        pass
    return result


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def ffprobe(path: Path) -> ProbeInfo:
    ffprobe_bin = require_tool("ffprobe")
    proc = run(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe failed: {path}")

    payload = json.loads(proc.stdout)
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    duration_text = payload.get("format", {}).get("duration") or video.get("duration")
    duration = float(duration_text) if duration_text else None
    return ProbeInfo(
        duration=duration,
        width=video.get("width"),
        height=video.get("height"),
        video_codec=video.get("codec_name"),
        audio_codec=audio.get("codec_name"),
    )


def can_probe(path: Path) -> bool:
    try:
        ffprobe(path)
        return True
    except Exception:
        return False


def remux_or_transcode(src: Path, dst: Path, compatibility: str, probe: ProbeInfo) -> str:
    ffmpeg_bin = require_tool("ffmpeg")
    should_transcode = compatibility == "universal" and not (
        probe.video_codec == "h264" and probe.audio_codec in (None, "aac")
    )

    if should_transcode:
        transcode(src, dst, ffmpeg_bin)
        return "transcode-h264-aac"

    cmd = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(dst),
    ]
    proc = run(cmd)
    if proc.returncode == 0:
        return "remux-copy"

    if compatibility == "copy":
        raise RuntimeError(proc.stderr.strip() or f"ffmpeg remux failed: {src}")

    transcode(src, dst, ffmpeg_bin)
    return "fallback-transcode-h264-aac"


def transcode(src: Path, dst: Path, ffmpeg_bin: str) -> None:
    cmd = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(dst),
    ]
    proc = run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffmpeg transcode failed: {src}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
