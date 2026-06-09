from __future__ import annotations

import base64
import re
from pathlib import Path


IWALLPAPER_AES_KEY = b"NSData".ljust(16, b"\0")


def parse_aes_key(value: str | None) -> bytes | None:
    """Parse a user key from text:, hex:, base64:, or raw UTF-8 text."""
    if not value:
        return None

    text = value.strip()
    if text.startswith("hex:"):
        key = bytes.fromhex(text[4:])
    elif text.startswith("base64:"):
        key = base64.b64decode(text[7:], validate=True)
    elif text.startswith("text:"):
        key = text[5:].encode("utf-8")
    elif len(text) in {32, 48, 64} and re.fullmatch(r"[0-9a-fA-F]+", text):
        key = bytes.fromhex(text)
    else:
        key = text.encode("utf-8")

    if len(key) not in {16, 24, 32}:
        raise ValueError("AES key must be 16, 24, or 32 bytes. Use text:, hex:, or base64: input.")
    return key


def decrypt_aes_ecb(data: bytes, key: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except ImportError as exc:
        raise RuntimeError(
            "AES profiles require the optional dependency: pip install 'wallpaper-mp4-exporter[aes]'"
        ) from exc

    decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    padded = decryptor.update(data) + decryptor.finalize()
    if not padded:
        raise ValueError("decrypted output is empty")

    pad_len = padded[-1]
    if not 1 <= pad_len <= 16:
        raise ValueError("bad PKCS#7 padding")
    if padded[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("bad PKCS#7 padding bytes")
    return padded[:-pad_len]


def write_decrypted(src: Path, dst: Path, key: bytes) -> None:
    dst.write_bytes(decrypt_aes_ecb(src.read_bytes(), key))
