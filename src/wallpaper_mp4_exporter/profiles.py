from __future__ import annotations

from pathlib import Path

from .crypto import IWALLPAPER_AES_KEY, write_decrypted
from .media import can_probe
from .models import ExportOptions


def prepare_media_input(src: Path, tmp: Path, options: ExportOptions) -> tuple[Path, str]:
    profile = options.profile

    if profile == "plain":
        return src, "plain"

    if profile in {"aes-ecb", "aes-128-ecb"}:
        if not options.aes_key:
            raise ValueError("profile aes-ecb requires --key")
        write_decrypted(src, tmp, options.aes_key)
        return tmp, "aes-ecb"

    if profile == "iwallpaper":
        if can_probe(src):
            return src, "plain"
        write_decrypted(src, tmp, IWALLPAPER_AES_KEY)
        return tmp, "iwallpaper-aes-128-ecb"

    if profile != "auto":
        raise ValueError(f"Unknown profile: {profile}")

    if can_probe(src):
        return src, "plain"

    key_attempts: list[tuple[str, bytes]] = []
    if options.aes_key:
        key_attempts.append(("aes-ecb", options.aes_key))
    key_attempts.append(("iwallpaper-aes-128-ecb", IWALLPAPER_AES_KEY))

    errors: list[str] = []
    for label, key in key_attempts:
        try:
            write_decrypted(src, tmp, key)
            if can_probe(tmp):
                return tmp, label
            errors.append(f"{label}: decrypted file is not readable media")
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    raise RuntimeError("Could not read media as plain or supported AES profile. " + "; ".join(errors))
