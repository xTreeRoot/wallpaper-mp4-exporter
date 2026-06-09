from __future__ import annotations


def is_zh(locale: str) -> bool:
    return locale.lower() in {"zh", "zh-cn", "zh_cn"}


def scan_message(layout: str, count: int, zh: bool) -> str:
    if zh:
        return f"在 {layout} 布局中找到 {count} 个候选文件。"
    return f"Found {count} candidate(s) in {layout} layout."


def skip_message(filename: str, zh: bool) -> str:
    return f"  跳过已存在文件 {filename}" if zh else f"  skipped existing {filename}"


def wrote_message(filename: str, mode: str, zh: bool) -> str:
    return f"  已写入 {filename}（{mode}）" if zh else f"  wrote {filename} ({mode})"


def failure_message(error: Exception, zh: bool) -> str:
    return f"  失败：{error}" if zh else f"  failed: {error}"


def done_message(exported: int, failed: int, zh: bool) -> str:
    return f"完成。成功 {exported} 个，失败 {failed} 个。" if zh else f"Done. Exported {exported}, failed {failed}."
