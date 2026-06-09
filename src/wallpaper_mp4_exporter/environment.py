from __future__ import annotations

import os
import platform
from pathlib import Path


SOURCE_ENV = "WALLPAPER_MP4_EXPORTER_SOURCE"
OUTPUT_ENV = "WALLPAPER_MP4_EXPORTER_OUTPUT"


def default_paths() -> dict[str, object]:
    source, source_reason = default_source_path()
    output, output_reason = default_output_path()
    return {
        "source": str(source) if source else "",
        "source_exists": bool(source and source.exists()),
        "source_reason": source_reason,
        "output": str(output),
        "output_reason": output_reason,
    }


def default_source_path() -> tuple[Path | None, str]:
    env_source = os.environ.get(SOURCE_ENV)
    if env_source:
        return Path(env_source).expanduser(), "env"

    home = Path.home()
    for candidate, reason in source_candidates(home):
        if is_iwallpaper_cache_root(candidate):
            return candidate, reason
    return None, "not_detected"


def default_output_path() -> tuple[Path, str]:
    env_output = os.environ.get(OUTPUT_ENV)
    if env_output:
        return Path(env_output).expanduser(), "env"

    downloads = downloads_dir(Path.home())
    return downloads / "mp4导出", "downloads"


def downloads_dir(home: Path) -> Path:
    xdg_path = xdg_user_dir(home, "XDG_DOWNLOAD_DIR")
    if xdg_path:
        return xdg_path
    return home / "Downloads"


def xdg_user_dir(home: Path, key: str) -> Path | None:
    config = home / ".config" / "user-dirs.dirs"
    if not config.exists():
        return None

    try:
        lines = config.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith(f"{key}="):
            continue
        value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        value = value.replace("$HOME", str(home)).replace("${HOME}", str(home))
        return Path(value).expanduser()
    return None


def source_candidates(home: Path) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    if platform.system() == "Darwin":
        candidates.append(
            (
                home / "Library" / "Containers" / "com.macosgame.iwallpaper" / "Data" / "Documents",
                "iwallpaper_known_container",
            )
        )
        candidates.extend((path, "macos_container_scan") for path in macos_container_documents(home))
    return candidates


def macos_container_documents(home: Path) -> list[Path]:
    containers = home / "Library" / "Containers"
    if not containers.exists():
        return []
    return sorted(path for path in containers.glob("*/Data/Documents") if path.is_dir())


def is_iwallpaper_cache_root(path: Path) -> bool:
    return path.is_dir() and (path / "Videos").is_dir() and (
        (path / "DesktopImage").exists() or (path / "Images").exists() or (path / "screen").exists()
    )
