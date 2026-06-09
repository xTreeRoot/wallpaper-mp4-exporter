from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


Progress = Callable[[str, dict[str, Any] | None], None]


@dataclass(frozen=True)
class ProbeInfo:
    duration: float | None
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
        }


@dataclass(frozen=True)
class Candidate:
    id: str
    video: Path
    cover: Path | None
    current: bool
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "video": str(self.video),
            "cover": str(self.cover) if self.cover else None,
            "current": self.current,
        }


@dataclass(frozen=True)
class ExportOptions:
    source: Path
    output: Path
    profile: str = "auto"
    layout: str = "auto"
    compatibility: str = "universal"
    aes_key: bytes | None = None
    limit: int = 0
    overwrite: bool = False
    no_html: bool = False
    keep_temp: bool = False
    locale: str = "en"


@dataclass(frozen=True)
class ExportResult:
    manifest_path: Path
    preview_path: Path | None
    output: Path
    entries: list[dict[str, Any]]
    failures: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": str(self.manifest_path),
            "preview_path": str(self.preview_path) if self.preview_path else None,
            "output": str(self.output),
            "entries": self.entries,
            "failures": self.failures,
        }
