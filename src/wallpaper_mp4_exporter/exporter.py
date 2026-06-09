from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .crypto import IWALLPAPER_AES_KEY, decrypt_aes_ecb, parse_aes_key, write_decrypted
from .manifest import write_manifest
from .media import can_probe, doctor, ffprobe, remux_or_transcode, require_tool, run, sha256, transcode
from .messages import done_message, is_zh, scan_message
from .models import Candidate, ExportOptions, ExportResult, ProbeInfo, Progress
from .preview import create_preview_html
from .profiles import prepare_media_input
from .scanner import (
    COVER_EXTENSIONS,
    UUID_RE,
    VIDEO_EXTENSIONS,
    copy_cover,
    extract_current_ids,
    find_cover,
    find_cover_by_stem,
    infer_layout,
    iter_video_files,
    safe_id,
    scan_candidates,
)
from .worker import export_candidate


VALID_PROFILES = {"auto", "plain", "aes-ecb", "aes-128-ecb", "iwallpaper"}
VALID_LAYOUTS = {"auto", "generic", "iwallpaper"}
VALID_COMPATIBILITY = {"copy", "mac", "universal"}


def export_wallpapers(options: ExportOptions, progress: Progress | None = None) -> ExportResult:
    emit: Progress = progress or (lambda _message, _event=None: None)
    validate_options(options)

    source = options.source.expanduser().resolve()
    output = options.output.expanduser().resolve()
    videos_output = output / "videos"
    covers_output = output / "covers"
    tmp_parent = output / "_tmp" if options.keep_temp else Path(tempfile.mkdtemp(prefix="wallpaper-mp4-exporter-"))
    zh = is_zh(options.locale)

    videos_output.mkdir(parents=True, exist_ok=True)
    covers_output.mkdir(parents=True, exist_ok=True)
    tmp_parent.mkdir(parents=True, exist_ok=True)

    scan = scan_candidates(source, options.layout, options.limit)
    candidates = candidates_from_scan(scan)
    started_at = datetime.now(timezone.utc).isoformat()
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    emit(scan_message(scan["layout"], len(candidates), zh), {"type": "scan", **scan})

    try:
        for index, candidate in enumerate(candidates, start=1):
            entry = export_candidate(
                candidate=candidate,
                index=index,
                total=len(candidates),
                options=options,
                videos_output=videos_output,
                covers_output=covers_output,
                tmp_parent=tmp_parent,
                emit=emit,
                zh=zh,
            )
            if entry["status"] == "failed":
                failures.append(entry)
            else:
                entries.append(entry)
    finally:
        if not options.keep_temp:
            shutil.rmtree(tmp_parent, ignore_errors=True)

    manifest_path = write_manifest(
        output=output,
        source=source,
        started_at=started_at,
        options=options,
        layout=scan["layout"],
        current_ids=scan["current_ids"],
        entries=entries,
        failures=failures,
    )
    preview_path = None if options.no_html else create_preview_html(output, entries, options.locale)

    emit(done_message(len(entries), len(failures), zh), {"type": "done"})
    return ExportResult(
        manifest_path=manifest_path,
        preview_path=preview_path,
        output=output,
        entries=entries,
        failures=failures,
    )


def validate_options(options: ExportOptions) -> None:
    source = options.source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    if options.profile not in VALID_PROFILES:
        raise ValueError(f"Unknown profile: {options.profile}")
    if options.layout not in VALID_LAYOUTS:
        raise ValueError(f"Unknown layout: {options.layout}")
    if options.compatibility not in VALID_COMPATIBILITY:
        raise ValueError(f"Unknown compatibility mode: {options.compatibility}")


def candidates_from_scan(scan: dict[str, Any]) -> list[Candidate]:
    return [
        Candidate(
            id=item["id"],
            video=Path(item["video"]),
            cover=Path(item["cover"]) if item.get("cover") else None,
            current=bool(item.get("current")),
        )
        for item in scan["candidates"]
    ]


__all__ = [
    "Candidate",
    "COVER_EXTENSIONS",
    "ExportOptions",
    "ExportResult",
    "IWALLPAPER_AES_KEY",
    "ProbeInfo",
    "Progress",
    "UUID_RE",
    "VIDEO_EXTENSIONS",
    "can_probe",
    "copy_cover",
    "create_preview_html",
    "decrypt_aes_ecb",
    "doctor",
    "export_wallpapers",
    "extract_current_ids",
    "ffprobe",
    "find_cover",
    "find_cover_by_stem",
    "infer_layout",
    "iter_video_files",
    "parse_aes_key",
    "prepare_media_input",
    "remux_or_transcode",
    "require_tool",
    "run",
    "safe_id",
    "scan_candidates",
    "sha256",
    "transcode",
    "write_decrypted",
]
