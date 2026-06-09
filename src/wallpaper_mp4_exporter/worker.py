from __future__ import annotations

from pathlib import Path
from typing import Any

from .media import ffprobe, remux_or_transcode, sha256
from .messages import failure_message, skip_message, wrote_message
from .models import Candidate, ExportOptions, ProbeInfo, Progress
from .profiles import prepare_media_input
from .scanner import candidate_filename_stem, copy_cover


def export_candidate(
    candidate: Candidate,
    index: int,
    total: int,
    options: ExportOptions,
    videos_output: Path,
    covers_output: Path,
    tmp_parent: Path,
    emit: Progress,
    zh: bool,
) -> dict[str, Any]:
    output_stem = candidate_filename_stem(candidate)
    out_mp4 = videos_output / f"{output_stem}.mp4"
    tmp_media = tmp_parent / f"{output_stem}{candidate.video.suffix.lower() or '.mp4'}"
    display_name = candidate.title or candidate.video.name
    emit(f"[{index}/{total}] {display_name}", {"type": "item", "id": candidate.id, "title": candidate.title})

    try:
        if out_mp4.exists() and not options.overwrite:
            entry = existing_entry(candidate, out_mp4, covers_output, options.overwrite)
            emit(skip_message(out_mp4.name, zh), {"type": "skipped", "entry": entry})
            return entry

        prepared, encryption = prepare_media_input(candidate.video, tmp_media, options)
        input_probe = ffprobe(prepared)
        mode = remux_or_transcode(prepared, out_mp4, options.compatibility, input_probe)
        output_probe = ffprobe(out_mp4)
        cover_path = copy_cover(candidate, covers_output, options.overwrite)
        entry = {
            "id": candidate.id,
            "title": candidate.title,
            "status": "exported",
            "current": candidate.current,
            "source_video": str(candidate.video),
            "output_video": str(out_mp4),
            "cover": cover_path,
            "encryption": encryption,
            "mode": mode,
            "source_size": candidate.video.stat().st_size,
            "output_size": out_mp4.stat().st_size,
            "sha256": sha256(out_mp4),
            **output_probe.to_dict(),
        }
        emit(wrote_message(out_mp4.name, mode, zh), {"type": "exported", "entry": entry})
        return entry
    except Exception as exc:
        failure = {
            "id": candidate.id,
            "title": candidate.title,
            "status": "failed",
            "source_video": str(candidate.video),
            "error": str(exc),
        }
        emit(failure_message(exc, zh), {"type": "failure", "failure": failure})
        return failure
    finally:
        if not options.keep_temp and tmp_media.exists():
            tmp_media.unlink()


def existing_entry(candidate: Candidate, out_mp4: Path, covers_output: Path, overwrite: bool) -> dict[str, Any]:
    try:
        out_probe = ffprobe(out_mp4)
    except Exception:
        out_probe = ProbeInfo(None, None, None, None, None)
    cover_path = copy_cover(candidate, covers_output, overwrite)
    return {
        "id": candidate.id,
        "title": candidate.title,
        "status": "exists",
        "current": candidate.current,
        "source_video": str(candidate.video),
        "output_video": str(out_mp4),
        "cover": cover_path,
        "mode": "skipped-existing",
        "sha256": sha256(out_mp4),
        **out_probe.to_dict(),
    }
