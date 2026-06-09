from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .messages import failure_message
from .models import Candidate, ExportOptions, Progress
from .worker import export_candidate


MAX_EXPORT_THREADS = 20


def export_thread_count(total: int) -> int:
    if total <= 0:
        return 0
    return min(total, MAX_EXPORT_THREADS)


def export_candidates_parallel(
    candidates: list[Candidate],
    options: ExportOptions,
    videos_output: Path,
    covers_output: Path,
    tmp_parent: Path,
    emit: Progress,
    zh: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    total = len(candidates)
    if total == 0:
        return [], []

    ordered: list[dict[str, Any] | None] = [None] * total
    with ThreadPoolExecutor(max_workers=export_thread_count(total), thread_name_prefix="wallpaper-export") as executor:
        futures = {
            executor.submit(
                export_candidate,
                candidate,
                index,
                total,
                options,
                videos_output,
                covers_output,
                tmp_parent,
                emit,
                zh,
            ): (index - 1, candidate)
            for index, candidate in enumerate(candidates, start=1)
        }

        for future in as_completed(futures):
            position, candidate = futures[future]
            try:
                ordered[position] = future.result()
            except Exception as exc:
                failure = {
                    "id": candidate.id,
                    "title": candidate.title,
                    "status": "failed",
                    "source_video": str(candidate.video),
                    "error": str(exc),
                }
                ordered[position] = failure
                emit(failure_message(exc, zh), {"type": "failure", "failure": failure})

    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for entry in ordered:
        if not entry:
            continue
        if entry["status"] == "failed":
            failures.append(entry)
        else:
            entries.append(entry)
    return entries, failures
