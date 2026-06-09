from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Any

from .models import Candidate


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
COVER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
UUID_RE = re.compile(
    rb"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
)


def safe_id(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip(".-")
    return cleaned or "wallpaper"


def infer_layout(source: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if source.is_file():
        return "generic"
    if (source / "Videos").exists() and (
        (source / "DesktopImage").exists() or (source / "Images").exists() or (source / "screen").exists()
    ):
        return "iwallpaper"
    return "generic"


def extract_current_ids(source: Path) -> list[str]:
    screen_file = source / "screen"
    if not screen_file.exists():
        return []

    seen: set[str] = set()
    result: list[str] = []
    for match in UUID_RE.finditer(screen_file.read_bytes()):
        value = match.group().decode("ascii").upper()
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def iter_video_files(source: Path, layout: str) -> list[Path]:
    if source.is_file():
        return [source] if source.suffix.lower() in VIDEO_EXTENSIONS else []

    if layout == "iwallpaper":
        video_dir = source / "Videos" if (source / "Videos").exists() else source
        return sorted(
            path
            for path in video_dir.iterdir()
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
        )

    return sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def find_cover_by_stem(directories: list[Path], stem: str) -> Path | None:
    lowered = stem.lower()
    for directory in directories:
        if not directory.exists() or not directory.is_dir():
            continue
        for child in directory.iterdir():
            if child.is_file() and child.suffix.lower() in COVER_EXTENSIONS and child.stem.lower() == lowered:
                return child
    return None


def find_cover(source: Path, video: Path, layout: str) -> Path | None:
    root = source.parent if source.is_file() else source
    if layout == "iwallpaper" and root.name == "Videos":
        root = root.parent

    directories = [video.parent]
    if layout == "iwallpaper":
        directories.extend([root / "DesktopImage", root / "Images"])
    else:
        directories.extend(
            [
                root / "covers",
                root / "cover",
                root / "images",
                root / "Images",
                root / "DesktopImage",
            ]
        )
    return find_cover_by_stem(directories, video.stem)


def scan_candidates(source: Path, layout: str = "auto", limit: int = 0) -> dict[str, Any]:
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    effective_layout = infer_layout(source, layout)
    files = iter_video_files(source, effective_layout)
    if limit:
        files = files[:limit]

    current_ids = extract_current_ids(source) if effective_layout == "iwallpaper" and source.is_dir() else []
    current_set = set(current_ids)
    used_ids: dict[str, int] = {}
    candidates: list[Candidate] = []

    for path in files:
        base = safe_id(path.stem)
        count = used_ids.get(base, 0)
        used_ids[base] = count + 1
        candidate_id = base if count == 0 else f"{base}-{hashlib.sha1(str(path).encode()).hexdigest()[:8]}"
        candidates.append(
            Candidate(
                id=candidate_id,
                video=path,
                cover=find_cover(source, path, effective_layout),
                current=path.stem.upper() in current_set,
            )
        )

    return {
        "source": str(source),
        "layout": effective_layout,
        "current_ids": current_ids,
        "candidates": [candidate.to_dict() for candidate in candidates],
    }


def copy_cover(candidate: Candidate, covers_output: Path, overwrite: bool) -> str | None:
    if not candidate.cover or not candidate.cover.exists():
        return None

    dst = covers_output / f"{candidate.id}{candidate.cover.suffix.lower()}"
    if overwrite or not dst.exists():
        shutil.copy2(candidate.cover, dst)
    return str(dst)
