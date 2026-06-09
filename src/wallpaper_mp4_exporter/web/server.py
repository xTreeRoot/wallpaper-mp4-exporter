from __future__ import annotations

import json
import mimetypes
import platform
import subprocess
import threading
import time
import uuid
import webbrowser
from copy import deepcopy
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..environment import default_paths
from ..exporter import ExportOptions, doctor, export_wallpapers, parse_aes_key, scan_candidates


WEB_DIR = Path(__file__).resolve().parent
INDEX_FILE = WEB_DIR / "index.html"
STATIC_FILES = {
    "/api.js": (WEB_DIR / "api.js", "application/javascript; charset=utf-8"),
    "/app.js": (WEB_DIR / "app.js", "application/javascript; charset=utf-8"),
    "/i18n.js": (WEB_DIR / "i18n.js", "application/javascript; charset=utf-8"),
    "/styles.css": (WEB_DIR / "styles.css", "text/css; charset=utf-8"),
}
JOBS: dict[str, "Job"] = {}
JOBS_LOCK = threading.Lock()


@dataclass
class Job:
    id: str
    status: str = "running"
    logs: list[str] = field(default_factory=list)
    result: dict | None = None
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def append(self, message: str) -> None:
        self.logs.append(message)

    def begin_result(self, output: Path) -> None:
        self.result = {
            "manifest_path": None,
            "preview_path": None,
            "output": str(output.expanduser().resolve()),
            "entries": [],
            "failures": [],
        }

    def record_event(self, event: dict | None) -> None:
        if not event or not self.result:
            return
        event_type = event.get("type")
        if event_type in {"exported", "skipped"} and event.get("entry"):
            self.result["entries"].append(event["entry"])
        elif event_type == "failure" and event.get("failure"):
            self.result["failures"].append(event["failure"])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "logs": list(self.logs),
            "result": deepcopy(self.result),
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "WallpaperMP4Exporter/0.1"

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html", "/en", "/en-US", "/zh", "/zh-CN"}:
            self.send_file(INDEX_FILE, "text/html; charset=utf-8", head_only=True)
            return
        if parsed.path in STATIC_FILES:
            path, content_type = STATIC_FILES[parsed.path]
            self.send_file(path, content_type, head_only=True)
            return
        if parsed.path == "/api/media":
            self.send_path_from_query(parsed.query, head_only=True)
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Not found")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html", "/en", "/en-US", "/zh", "/zh-CN"}:
            self.send_file(INDEX_FILE, "text/html; charset=utf-8")
            return
        if parsed.path in STATIC_FILES:
            path, content_type = STATIC_FILES[parsed.path]
            self.send_file(path, content_type)
            return
        if parsed.path == "/api/doctor":
            self.send_json(doctor())
            return
        if parsed.path == "/api/defaults":
            self.send_json(default_paths())
            return
        if parsed.path.startswith("/api/jobs/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                self.send_error_json(HTTPStatus.NOT_FOUND, "Job not found")
                return
            self.send_json(job.to_dict())
            return
        if parsed.path == "/api/media":
            self.send_path_from_query(parsed.query)
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/scan":
                source = Path(str(payload.get("source", ""))).expanduser()
                layout = str(payload.get("layout") or "auto")
                limit = int(payload.get("limit") or 0)
                self.send_json(scan_candidates(source, layout, limit))
                return
            if parsed.path == "/api/export":
                self.start_export(payload)
                return
            if parsed.path == "/api/pick-path":
                self.pick_path(payload)
                return
            self.send_error_json(HTTPStatus.NOT_FOUND, "Not found")
        except Exception as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))

    def pick_path(self, payload: dict) -> None:
        kind = str(payload.get("kind") or "directory")
        if kind not in {"file", "directory", "output"}:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Unknown path picker kind")
            return
        self.send_json({"path": pick_local_path(kind, str(payload.get("locale") or "en"))})

    def start_export(self, payload: dict) -> None:
        job = Job(id=uuid.uuid4().hex[:12])
        with JOBS_LOCK:
            JOBS[job.id] = job

        def runner() -> None:
            try:
                options = ExportOptions(
                    source=Path(str(payload.get("source", ""))).expanduser(),
                    output=Path(str(payload.get("output") or "exports")).expanduser(),
                    profile=str(payload.get("profile") or "auto"),
                    layout=str(payload.get("layout") or "auto"),
                    compatibility=str(payload.get("compatibility") or "universal"),
                    aes_key=parse_aes_key(payload.get("key") or None),
                    overwrite=bool(payload.get("overwrite")),
                    limit=int(payload.get("limit") or 0),
                    locale=str(payload.get("locale") or "en"),
                )
                with JOBS_LOCK:
                    job.begin_result(options.output)

                def progress(message: str, _event: dict | None = None) -> None:
                    with JOBS_LOCK:
                        job.append(message)
                        job.record_event(_event)

                result = export_wallpapers(options, progress=progress)
                with JOBS_LOCK:
                    job.status = "done" if not result.failures else "done-with-failures"
                    job.result = result.to_dict()
            except Exception as exc:
                with JOBS_LOCK:
                    job.status = "failed"
                    job.error = str(exc)
                    job.append(f"failed: {exc}")
            finally:
                with JOBS_LOCK:
                    job.finished_at = time.time()

        thread = threading.Thread(target=runner, name=f"export-{job.id}", daemon=True)
        thread.start()
        self.send_json({"job_id": job.id})

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def send_path_from_query(self, query: str, head_only: bool = False) -> None:
        values = parse_qs(query)
        raw_path = (values.get("path") or [""])[0]
        if not raw_path:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Missing path")
            return
        path = Path(raw_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "File not found")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_file(path, content_type, head_only=head_only)

    def send_file(self, path: Path, content_type: str, head_only: bool = False) -> None:
        try:
            file_size = path.stat().st_size
        except OSError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return

        start = 0
        end = file_size - 1
        status = HTTPStatus.OK
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            status = HTTPStatus.PARTIAL_CONTENT
            requested = range_header.removeprefix("bytes=").split(",", 1)[0]
            start_text, _, end_text = requested.partition("-")
            start = int(start_text) if start_text else 0
            end = int(end_text) if end_text else end
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))

        content_length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Accept-Ranges", "bytes")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if head_only:
            return
        with path.open("rb") as handle:
            handle.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = handle.read(min(1024 * 512, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"error": message}, status=status)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> None:
    address = (host, port)
    httpd = ThreadingHTTPServer(address, RequestHandler)
    url = f"http://{host}:{port}"
    print(f"Wallpaper MP4 Exporter is running at {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()


def picker_prompt(kind: str, locale: str) -> str:
    zh = locale.lower().startswith("zh")
    if kind == "file":
        return "选择媒体文件或缓存视频" if zh else "Select a media file or cached video"
    if kind == "output":
        return "选择输出文件夹" if zh else "Select an output folder"
    return "选择壁纸缓存目录或媒体文件夹" if zh else "Select a cache or media folder"


def pick_local_path(kind: str, locale: str = "en") -> str | None:
    if platform.system() == "Darwin":
        try:
            return pick_path_with_osascript(kind, locale)
        except RuntimeError:
            raise
        except Exception:
            pass
    return pick_path_with_tkinter(kind, locale)


def pick_path_with_osascript(kind: str, locale: str = "en") -> str | None:
    prompt = picker_prompt(kind, locale)
    if kind == "file":
        script = f'POSIX path of (choose file with prompt "{prompt}")'
    elif kind == "output":
        script = f'POSIX path of (choose folder with prompt "{prompt}")'
    else:
        script = f'POSIX path of (choose folder with prompt "{prompt}")'

    proc = subprocess.run(["osascript", "-e", script], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        if "User canceled" in stderr or "用户已取消" in stderr:
            return None
        raise RuntimeError(stderr or "Path picker failed")
    value = proc.stdout.strip()
    return value or None


def pick_path_with_tkinter(kind: str, locale: str = "en") -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise RuntimeError("No native path picker is available in this Python environment.") from exc

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        title = picker_prompt(kind, locale)
        if kind == "file":
            value = filedialog.askopenfilename(title=title)
        elif kind == "output":
            value = filedialog.askdirectory(title=title, mustexist=False)
        else:
            value = filedialog.askdirectory(title=title, mustexist=True)
    finally:
        root.destroy()
    return value or None
