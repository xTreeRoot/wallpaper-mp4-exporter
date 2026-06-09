from __future__ import annotations

import json
import plistlib
import re
import sqlite3
from pathlib import Path
from typing import Any


UUID_TEXT_RE = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)
TITLE_KEYS = ("title", "name", "displayName", "wallpaperName", "tagsStr")
ID_KEYS = ("id", "uuid", "recordID", "recordId", "videoID", "videoId", "filename", "file", "video")
SIDECAR_NAMES = ("metadata.json", "wallpapers.json", "index.json", "manifest.json")


def load_title_map(source: Path, layout: str = "auto") -> dict[str, str]:
    roots = metadata_roots(source)
    titles: dict[str, str] = {}

    for root in roots:
        titles.update(load_sidecar_titles(root))
        titles.update(load_iwallpaper_screen_titles(root))
        titles.update(load_iwallpaper_cloudkit_titles(root))

    return titles


def metadata_roots(source: Path) -> list[Path]:
    base = source.expanduser()
    if base.is_file():
        base = base.parent

    roots: list[Path] = []

    def add(path: Path) -> None:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            return
        if resolved.exists() and resolved.is_dir() and resolved not in roots:
            roots.append(resolved)

    add(base)
    for parent in list(base.parents)[:6]:
        add(parent)

    for root in list(roots):
        if root.name in {"Videos", "Images", "DesktopImage"}:
            add(root.parent)
        add(root / "Documents")

    return roots


def load_sidecar_titles(root: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    for name in SIDECAR_NAMES:
        path = root / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        collect_titles_from_json(data, titles)
    return titles


def collect_titles_from_json(value: Any, titles: dict[str, str]) -> None:
    if isinstance(value, list):
        for item in value:
            collect_titles_from_json(item, titles)
        return

    if not isinstance(value, dict):
        return

    record_id = first_string(value, ID_KEYS)
    title = normalize_title(first_string(value, TITLE_KEYS))
    if record_id and title:
        titles[normalize_key(record_id)] = title

    for child in value.values():
        if isinstance(child, (dict, list)):
            collect_titles_from_json(child, titles)


def load_iwallpaper_screen_titles(root: Path) -> dict[str, str]:
    screen = root / "screen"
    if not screen.is_file():
        return {}

    try:
        plist = plistlib.loads(screen.read_bytes())
    except Exception:
        return {}

    objects = plist.get("$objects") if isinstance(plist, dict) else None
    if not isinstance(objects, list):
        return {}

    titles: dict[str, str] = {}
    for item in objects:
        if not isinstance(item, dict) or "RecordID" not in item or "ValueStore" not in item:
            continue
        record_id = record_name(objects, item.get("RecordID"))
        values = record_values(objects, item.get("ValueStore"))
        title = normalize_title(first_string(values, TITLE_KEYS))
        if record_id and title:
            titles[normalize_key(record_id)] = title
    return titles


def load_iwallpaper_cloudkit_titles(root: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    for db_path in cloudkit_db_candidates(root):
        if not db_path.is_file():
            continue
        try:
            connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        except sqlite3.Error:
            continue
        try:
            rows = connection.execute("SELECT recordID, recordData FROM '7'")
            for record_id, record_data in rows:
                title = extract_cloudkit_title(record_data)
                if record_id and title:
                    titles[normalize_key(str(record_id).split(":", 1)[0])] = title
        except sqlite3.Error:
            continue
        finally:
            connection.close()
    return titles


def cloudkit_db_candidates(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for base in (root, *list(root.parents)[:4]):
        candidates.extend(
            [
                base / "CloudKit" / "cloudd_db" / "db",
                base / "Data" / "CloudKit" / "cloudd_db" / "db",
            ]
        )

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def extract_cloudkit_title(record_data: bytes | memoryview | None) -> str | None:
    if not record_data:
        return None

    data = bytes(record_data)
    for key in (b"tagsStr", b"title", b"displayName", b"name"):
        start = 0
        while True:
            index = data.find(key, start)
            if index == -1:
                break
            title = extract_length_prefixed_string(data[index : index + 512])
            if title:
                return title
            start = index + len(key)
    return None


def extract_length_prefixed_string(window: bytes) -> str | None:
    marker = b"\x08\x03:"
    start = 0
    while True:
        marker_index = window.find(marker, start)
        if marker_index == -1:
            return None
        length_index = marker_index + len(marker)
        length, value_index = read_varint(window, length_index)
        if length is not None and value_index + length <= len(window):
            value = window[value_index : value_index + length].decode("utf-8", errors="ignore")
            title = normalize_title(value)
            if title:
                return title
        start = marker_index + 1


def read_varint(data: bytes, index: int) -> tuple[int | None, int]:
    shift = 0
    value = 0
    for offset in range(10):
        if index + offset >= len(data):
            return None, index
        byte = data[index + offset]
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index + offset + 1
        shift += 7
    return None, index


def record_name(objects: list[Any], uid: Any) -> str | None:
    record = object_for_uid(objects, uid)
    if not isinstance(record, dict):
        return None
    name = object_for_uid(objects, record.get("RecordName"))
    return str(name) if isinstance(name, str) else None


def record_values(objects: list[Any], uid: Any) -> dict[str, Any]:
    store = object_for_uid(objects, uid)
    if not isinstance(store, dict):
        return {}
    values = object_for_uid(objects, store.get("RecordValues"))
    resolved = resolve_value(objects, values)
    return resolved if isinstance(resolved, dict) else {}


def resolve_value(objects: list[Any], value: Any, depth: int = 0) -> Any:
    if depth > 20:
        return None

    resolved = object_for_uid(objects, value)
    if resolved is not value:
        return resolve_value(objects, resolved, depth + 1)

    if isinstance(value, dict):
        keys = value.get("NS.keys")
        values = value.get("NS.objects")
        if isinstance(keys, list) and isinstance(values, list) and len(keys) == len(values):
            return {
                str(resolve_value(objects, key, depth + 1)): resolve_value(objects, item, depth + 1)
                for key, item in zip(keys, values)
            }
        return {
            key: resolve_value(objects, item, depth + 1)
            for key, item in value.items()
            if key != "$class"
        }

    if isinstance(value, list):
        return [resolve_value(objects, item, depth + 1) for item in value]

    return value


def object_for_uid(objects: list[Any], value: Any) -> Any:
    index = getattr(value, "data", None)
    if isinstance(index, int) and 0 <= index < len(objects):
        return objects[index]
    return value


def first_string(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            return value
    return None


def normalize_key(value: str) -> str:
    path = Path(str(value))
    stem = path.stem if path.suffix else str(value)
    return stem.split(":", 1)[0].upper()


def normalize_title(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).replace("\x00", " ").split()).strip(" .-_")
    if not cleaned or cleaned.lower() in {"null", "(null)", "none", "true", "false", "0", "1"}:
        return None
    if UUID_TEXT_RE.fullmatch(cleaned):
        return None
    return cleaned[:120]
