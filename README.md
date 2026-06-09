# Wallpaper MP4 Exporter

[中文文档](README.zh-CN.md)

A local, open-source CLI and browser UI for exporting wallpaper caches or media folders to playable MP4 files.

It is intentionally not tied to one computer or one application path. You point it at a folder or file, choose a scan layout and read profile, and it writes ordinary MP4 files plus covers, a manifest, and a standalone `preview.html`.

## Features

- Local web UI for scan, export, logs, and video preview.
- CLI for repeatable batch exports.
- Generic recursive media-folder scanning.
- Optional cache-layout support for folders shaped like `Videos/`, `Images/`, and `DesktopImage/`.
- Profiles for plain media, AES-ECB encrypted media, and an iWallpaper-compatible legacy cache profile.
- MP4 output with three compatibility modes:
  - `universal`: H.264/AAC for broad playback support.
  - `mac`: remux first, transcode only if remux fails.
  - `copy`: remux streams without transcoding.
- Output includes:
  - `videos/*.mp4`
  - `covers/*`
  - `manifest.json`
  - `preview.html`

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe`
- `cryptography` for AES-based cache profiles; it is installed by default

Install ffmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# Windows
winget install Gyan.FFmpeg
```

## Install

```bash
git clone https://github.com/xTreeRoot/wallpaper-mp4-exporter.git
cd wallpaper-mp4-exporter
python3 -m pip install -e .
```

## Web UI

```bash
wallpaper-mp4-exporter web --open
```

Default URL:

```text
http://127.0.0.1:8765
```

Chinese UI:

```text
http://127.0.0.1:8765/zh-CN
```

The default page follows the browser `Accept-Language` setting. You can also switch languages from the selector in the top-right corner.

Use the form to set:

- `Source file or folder`: where the app reads from. It can be a cache folder, media folder, or single media file. The page auto-fills a detected iWallpaper cache folder on the current computer when one exists; otherwise use the folder/file picker.
- `Output path`: where exported files are written. The default is `~/Downloads/mp4导出`.
- `Read mode`: keep `Auto` unless you know the source needs a specific reader.
- `Folder structure`: keep `Auto` unless you need to force ordinary-folder or iWallpaper-style scanning.
- `Playback compatibility`: `Best compatibility MP4` is recommended for live wallpaper use and broad playback support.
- `Limit`: maximum number of videos to export. `0` means export everything; use `1` or `2` for a quick test.
- `Encryption key`: under advanced options. Usually leave it empty; auto mode already handles known supported encrypted caches.
- `Overwrite existing MP4 files`: checked by default so repeated exports refresh existing MP4 files.

## Environment Defaults

The web UI derives defaults from the current user's machine. It does not hard-code a username or a single computer path:

- `WALLPAPER_MP4_EXPORTER_SOURCE` overrides the source path.
- `WALLPAPER_MP4_EXPORTER_OUTPUT` overrides the output path.
- Without an output override, exports default to `mp4导出` under the current user's downloads directory.
- On macOS, the app detects the current user's iWallpaper cache folder and scans `~/Library/Containers/*/Data/Documents` for cache folders shaped like `Videos/` plus `DesktopImage/`, `Images/`, or `screen`.
- If no source path is detected, the source field stays empty and the user can choose a folder or file from the picker.

Example:

```bash
WALLPAPER_MP4_EXPORTER_SOURCE="/path/to/cache-or-media" \
WALLPAPER_MP4_EXPORTER_OUTPUT="$HOME/Downloads/mp4导出" \
wallpaper-mp4-exporter web --open
```

## CLI

Generic media folder:

```bash
wallpaper-mp4-exporter export \
  --source /path/to/media-folder \
  --output ./exports \
  --layout generic \
  --profile plain \
  --compatibility universal
```

Auto profile:

```bash
wallpaper-mp4-exporter export \
  --source /path/to/cache-or-media \
  --output ./exports \
  --profile auto \
  --layout auto \
  --locale zh-CN
```

AES-ECB cache with a custom key:

```bash
wallpaper-mp4-exporter export \
  --source /path/to/cache \
  --output ./exports \
  --profile aes-ecb \
  --key hex:00112233445566778899aabbccddeeff
```

iWallpaper-compatible cache layout:

```bash
wallpaper-mp4-exporter export \
  --source "$HOME/Library/Containers/com.macosgame.iwallpaper/Data/Documents" \
  --output ./exports \
  --layout iwallpaper \
  --profile iwallpaper
```

Scan only:

```bash
wallpaper-mp4-exporter scan --source /path/to/source --layout auto
```

Check tools:

```bash
wallpaper-mp4-exporter doctor
```

## Profiles

| Profile | Purpose |
| --- | --- |
| `auto` | Try ordinary media first, then supported AES attempts. |
| `plain` | Treat files as normal readable media. |
| `aes-ecb` | Decrypt with a user-provided AES key and PKCS#7 padding. |
| `aes-128-ecb` | Compatibility alias for `aes-ecb`. |
| `iwallpaper` | Read legacy iWallpaper-style cached downloads. |

AES keys accept:

- `text:1234567890abcdef`
- `hex:00112233445566778899aabbccddeeff`
- `base64:ABEiM0RVZneImaq7zN3u/w==`
- raw text, when it is exactly 16, 24, or 32 bytes after UTF-8 encoding

## Layouts

| Layout | Discovery behavior |
| --- | --- |
| `generic` | Recursively scans the source path for video files and matches covers by filename stem. |
| `iwallpaper` | Reads videos from `Videos/`, covers from `DesktopImage/` or `Images/`, and current IDs from `screen` when present. |
| `auto` | Uses `iwallpaper` when that folder shape is detected, otherwise `generic`. |

## Output

```text
exports/
  videos/
    example.mp4
  covers/
    example.png
  manifest.json
  preview.html
```

`preview.html` is standalone and can be opened from the output folder. The web UI also has an inline preview player for exported MP4 files.

## Notes

This project is for exporting and converting local media you have the right to use. It does not download paid content, bypass network access controls, or remove DRM. Some wallpaper apps store cached media in private or encrypted formats; support for a profile only means the tool can read local files that already exist on your machine.

## Development

Run from source without installing:

```bash
PYTHONPATH=src python3 -m wallpaper_mp4_exporter doctor
PYTHONPATH=src python3 -m wallpaper_mp4_exporter web
```

Compile check:

```bash
python3 -m compileall src
```

## License

MIT
