from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def create_preview_html(output: Path, entries: list[dict[str, Any]], locale: str = "en") -> Path | None:
    playable = [entry for entry in entries if entry.get("output_video")]
    if not playable:
        return None

    zh = locale.lower() in {"zh", "zh-cn", "zh_cn"}
    text = {
        "html_lang": "zh-CN" if zh else "en",
        "title": "壁纸 MP4 导出预览" if zh else "Wallpaper MP4 Export Preview",
        "select": "已导出视频" if zh else "Exported video",
        "badge": f"{len(playable)} 个 MP4 文件" if zh else f"{len(playable)} MP4 file(s)",
        "id": "ID",
        "mode": "模式" if zh else "Mode",
        "codec": "编码" if zh else "Codec",
        "size": "尺寸" if zh else "Size",
        "seconds": "秒数" if zh else "Seconds",
        "aria": "视频预览" if zh else "Video preview",
    }

    def rel(value: str | None) -> str:
        if not value:
            return ""
        path = Path(value)
        try:
            return path.relative_to(output).as_posix()
        except ValueError:
            return path.as_posix()

    preferred = next((entry for entry in playable if entry.get("current")), playable[0])
    options = "\n".join(
        f'        <option value="{html.escape(rel(entry["output_video"]))}" '
        f'data-cover="{html.escape(rel(entry.get("cover")))}"'
        f'{" selected" if entry["id"] == preferred["id"] else ""}>'
        f'{html.escape(entry["id"])}</option>'
        for entry in playable
    )
    rows = "\n".join(
        "          <tr>"
        f"<td>{html.escape(entry['id'])}</td>"
        f"<td>{html.escape(entry.get('mode') or '')}</td>"
        f"<td>{html.escape(entry.get('video_codec') or '')}</td>"
        f"<td>{html.escape(str(entry.get('width') or ''))}x{html.escape(str(entry.get('height') or ''))}</td>"
        f"<td>{html.escape(str(round(entry.get('duration') or 0, 2)))}</td>"
        "</tr>"
        for entry in playable
    )
    cover = rel(preferred.get("cover"))
    video = rel(preferred["output_video"])
    page = f"""<!doctype html>
<html lang="{text['html_lang']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(text['title'])}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #101214;
      --panel: #181c20;
      --panel-2: #20262b;
      --text: #f2f5f7;
      --muted: #a9b3bd;
      --line: #37414a;
      --blue: #4f8cff;
      --green: #43c59e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      min-height: 100vh;
    }}
    .stage {{
      position: relative;
      min-height: 52vh;
      background: #050607;
    }}
    video {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      background: #050607;
    }}
    aside {{
      border-left: 1px solid var(--line);
      background: var(--panel);
      padding: 24px;
      overflow: auto;
    }}
    h1 {{
      margin: 0 0 18px;
      font-size: 24px;
      line-height: 1.2;
    }}
    label {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    select {{
      width: 100%;
      min-height: 44px;
      color: var(--text);
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 12px;
      font: inherit;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 22px;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    .badge {{
      display: inline-block;
      margin-top: 16px;
      color: #061311;
      background: var(--green);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
    }}
    @media (max-width: 880px) {{
      main {{ grid-template-columns: 1fr; }}
      aside {{ border-left: 0; border-top: 1px solid var(--line); }}
      .stage {{ min-height: 58vh; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="stage" aria-label="{html.escape(text['aria'])}">
      <video id="preview" autoplay muted loop playsinline controls poster="{html.escape(cover)}">
        <source src="{html.escape(video)}" type="video/mp4">
      </video>
    </section>
    <aside>
      <h1>{html.escape(text['title'])}</h1>
      <label for="picker">{html.escape(text['select'])}</label>
      <select id="picker">
{options}
      </select>
      <span class="badge">{html.escape(text['badge'])}</span>
      <table>
        <thead>
          <tr><th>{html.escape(text['id'])}</th><th>{html.escape(text['mode'])}</th><th>{html.escape(text['codec'])}</th><th>{html.escape(text['size'])}</th><th>{html.escape(text['seconds'])}</th></tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </aside>
  </main>
  <script>
    const video = document.getElementById('preview');
    const picker = document.getElementById('picker');
    picker.addEventListener('change', () => {{
      const option = picker.options[picker.selectedIndex];
      video.poster = option.dataset.cover || '';
      video.src = option.value;
      video.play();
    }});
  </script>
</body>
</html>
"""
    html_path = output / "preview.html"
    html_path.write_text(page, encoding="utf-8")
    return html_path
