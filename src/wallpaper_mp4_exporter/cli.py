from __future__ import annotations

import argparse
import json
import locale
import os
import sys
from pathlib import Path

from .exporter import ExportOptions, doctor, export_wallpapers, parse_aes_key, scan_candidates


def default_locale() -> str:
    raw = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or locale.getlocale()[0]
        or ""
    )
    return "zh-CN" if raw.lower().startswith("zh") else "en"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wallpaper-mp4-exporter",
        description="Export wallpaper caches or media folders to playable MP4 files.",
    )
    sub = parser.add_subparsers(dest="command")

    export = sub.add_parser("export", help="Export videos from a local source path.")
    add_export_args(export)

    scan = sub.add_parser("scan", help="List videos and matching covers without exporting.")
    scan.add_argument("--source", type=Path, required=True, help="File, cache directory, or media directory.")
    scan.add_argument("--layout", choices=("auto", "generic", "iwallpaper"), default="auto")
    scan.add_argument("--limit", type=int, default=0)

    web = sub.add_parser("web", help="Start the local browser UI.")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8765)
    web.add_argument("--open", action="store_true", help="Open the UI in the default browser.")

    sub.add_parser("doctor", help="Check ffmpeg, ffprobe, and AES support.")
    return parser


def add_export_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", type=Path, required=True, help="File, cache directory, or media directory.")
    parser.add_argument("--output", type=Path, default=Path("exports"), help="Export directory.")
    parser.add_argument(
        "--profile",
        choices=("auto", "plain", "aes-ecb", "aes-128-ecb", "iwallpaper"),
        default="auto",
        help="How to read source media before converting.",
    )
    parser.add_argument(
        "--layout",
        choices=("auto", "generic", "iwallpaper"),
        default="auto",
        help="How to scan videos and covers inside the source path.",
    )
    parser.add_argument(
        "--compatibility",
        choices=("copy", "mac", "universal"),
        default="universal",
        help="copy keeps streams, mac remuxes with fallback, universal converts non-H.264/AAC to H.264/AAC.",
    )
    parser.add_argument(
        "--key",
        help="AES key for aes-ecb or auto custom attempts. Accepts text:, hex:, base64:, or raw text.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace existing exported files.")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N matches.")
    parser.add_argument("--no-html", action="store_true", help="Do not create preview.html.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep decrypted temporary media files.")
    parser.add_argument(
        "--locale",
        choices=("en", "zh-CN"),
        default=default_locale(),
        help="Language used by generated preview.html. Defaults to the current locale.",
    )


def print_progress(message: str, _event: dict | None = None) -> None:
    print(message)


def run_export(args: argparse.Namespace) -> int:
    options = ExportOptions(
        source=args.source,
        output=args.output,
        profile=args.profile,
        layout=args.layout,
        compatibility=args.compatibility,
        aes_key=parse_aes_key(args.key),
        limit=args.limit,
        overwrite=args.overwrite,
        no_html=args.no_html,
        keep_temp=args.keep_temp,
        locale=args.locale,
    )
    result = export_wallpapers(options, progress=print_progress)
    print()
    print(f"Output: {result.output}")
    print(f"Manifest: {result.manifest_path}")
    if result.preview_path:
        print(f"Preview: {result.preview_path}")
    print(f"Exported: {len(result.entries)}")
    print(f"Failed: {len(result.failures)}")
    return 1 if result.failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        return run_export(args)
    if args.command == "scan":
        print(json.dumps(scan_candidates(args.source, args.layout, args.limit), indent=2, ensure_ascii=False))
        return 0
    if args.command == "web":
        from .web.server import run_server

        run_server(args.host, args.port, open_browser=args.open)
        return 0
    if args.command == "doctor":
        print(json.dumps(doctor(), indent=2, ensure_ascii=False))
        return 0

    parser.print_help(sys.stderr)
    return 2
