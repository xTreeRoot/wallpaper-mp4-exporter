from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ExportOptions


def write_manifest(
    output: Path,
    source: Path,
    started_at: str,
    options: ExportOptions,
    layout: str,
    current_ids: list[str],
    entries: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> Path:
    manifest = {
        "created_at": started_at,
        "source": str(source),
        "output": str(output),
        "profile": options.profile,
        "layout": layout,
        "compatibility": options.compatibility,
        "locale": options.locale,
        "current_ids": current_ids,
        "entries": entries,
        "failures": failures,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path
