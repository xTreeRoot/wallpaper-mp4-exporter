# Wallpaper MP4 Exporter

[English README](README.md)

一个本地运行的开源工具，提供命令行和浏览器界面，用来把壁纸缓存或普通媒体目录导出为可播放的 MP4 文件。

它不会绑定某一台电脑，也不会只绑定某一个应用路径。你只需要指定一个文件夹或文件，选择扫描布局和读取方式，它就会输出普通 MP4、封面、`manifest.json` 和独立可打开的 `preview.html`。

## 功能

- 本地 Web UI：支持扫描、导出、日志查看和视频预览。
- CLI：适合重复执行和批处理。
- 通用媒体目录递归扫描。
- 支持类似 `Videos/`、`Images/`、`DesktopImage/` 的缓存目录结构。
- 支持普通媒体、AES-ECB 加密媒体、iWallpaper 兼容缓存 profile。
- MP4 输出支持三种兼容模式：
  - `universal`：输出 H.264/AAC，兼容性最好。
  - `mac`：优先无损封装，失败时转码。
  - `copy`：只复制原始音视频流，不转码。
- 导出内容包括：
  - `videos/*.mp4`
  - `covers/*`
  - `manifest.json`
  - `preview.html`

## 环境要求

- Python 3.10+
- `ffmpeg` 和 `ffprobe`
- AES 解密依赖 `cryptography`，普通安装会自动安装

安装 ffmpeg：

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# Windows
winget install Gyan.FFmpeg
```

## 安装

```bash
git clone https://github.com/xTreeRoot/wallpaper-mp4-exporter.git
cd wallpaper-mp4-exporter
python3 -m pip install -e .
```

## Web UI

```bash
wallpaper-mp4-exporter web --open
```

默认地址：

```text
http://127.0.0.1:8765
```

中文界面：

```text
http://127.0.0.1:8765/zh-CN
```

表单参数：

默认页面会根据浏览器 `Accept-Language` 自动选择语言。右上角也可以手动切换语言，选择会保存在浏览器里。

- `来源文件/文件夹`：程序读取的位置，可以是缓存目录、普通媒体目录或单个媒体文件。页面会自动填入当前电脑上检测到的 iWallpaper 缓存目录；没有检测到时可以点“选择文件夹”或“选择文件”。
- `输出路径`：导出结果保存的位置，默认是当前用户的 `Downloads/mp4导出`。
- `文件读取方式`：建议保持“自动识别”，程序会自己尝试普通媒体和已支持的缓存格式。
- `文件夹结构`：建议保持“自动识别”，程序会自己判断普通文件夹或 iWallpaper 风格缓存。
- `播放兼容性`：建议选择“最大兼容 MP4”，更适合作为动态壁纸或给更多播放器播放。
- `导出数量`：最多导出多少个。`0` 表示全部导出，先测试可以填 `1` 或 `2`。
- `加密密钥`：在“高级选项”里，通常留空。自动识别会处理已支持的加密缓存，只有明确知道某个缓存需要自定义密钥时才填写。
- `覆盖已存在的 MP4 文件`：默认勾选，重复导出时会更新已有 MP4。

## 环境适配

Web UI 会按 clone 者当前电脑自动填默认值，不写死某个用户名或某台机器的路径：

- 如果设置了 `WALLPAPER_MP4_EXPORTER_SOURCE`，优先用它作为来源路径。
- 如果设置了 `WALLPAPER_MP4_EXPORTER_OUTPUT`，优先用它作为输出路径。
- 未设置输出路径时，默认使用当前用户的下载目录下的 `mp4导出`。
- macOS 上会探测当前用户的 iWallpaper 缓存目录，也会扫描当前用户 `~/Library/Containers/*/Data/Documents` 里符合 `Videos/` + `DesktopImage/`/`Images/`/`screen` 结构的缓存目录。
- 没有探测到来源时，来源输入框会保持空白，用户通过“选择文件夹”或“选择文件”选择即可。

示例：

```bash
WALLPAPER_MP4_EXPORTER_SOURCE="/path/to/cache-or-media" \
WALLPAPER_MP4_EXPORTER_OUTPUT="$HOME/Downloads/mp4导出" \
wallpaper-mp4-exporter web --open
```

## CLI

普通媒体目录：

```bash
wallpaper-mp4-exporter export \
  --source /path/to/media-folder \
  --output ./exports \
  --layout generic \
  --profile plain \
  --compatibility universal
```

自动识别：

```bash
wallpaper-mp4-exporter export \
  --source /path/to/cache-or-media \
  --output ./exports \
  --profile auto \
  --layout auto \
  --locale zh-CN
```

使用自定义 AES-ECB 密钥：

```bash
wallpaper-mp4-exporter export \
  --source /path/to/cache \
  --output ./exports \
  --profile aes-ecb \
  --key hex:00112233445566778899aabbccddeeff
```

iWallpaper 兼容缓存布局：

```bash
wallpaper-mp4-exporter export \
  --source "$HOME/Library/Containers/com.macosgame.iwallpaper/Data/Documents" \
  --output ./exports \
  --layout iwallpaper \
  --profile iwallpaper
```

只扫描不导出：

```bash
wallpaper-mp4-exporter scan --source /path/to/source --layout auto
```

检查依赖：

```bash
wallpaper-mp4-exporter doctor
```

## 读取方式

| Profile | 用途 |
| --- | --- |
| `auto` | 先按普通媒体读取，再尝试受支持的 AES 方式。 |
| `plain` | 把文件当作普通可读媒体处理。 |
| `aes-ecb` | 使用用户提供的 AES 密钥和 PKCS#7 padding 解密。 |
| `aes-128-ecb` | `aes-ecb` 的兼容别名。 |
| `iwallpaper` | 读取 iWallpaper 风格的本地缓存下载文件。 |

AES 密钥支持：

- `text:1234567890abcdef`
- `hex:00112233445566778899aabbccddeeff`
- `base64:ABEiM0RVZneImaq7zN3u/w==`
- 原始文本，但 UTF-8 编码后必须正好是 16、24 或 32 字节

## 目录布局

| Layout | 发现规则 |
| --- | --- |
| `generic` | 递归扫描源路径中的视频文件，并按同名文件匹配封面。 |
| `iwallpaper` | 从 `Videos/` 读取视频，从 `DesktopImage/` 或 `Images/` 读取封面，存在 `screen` 时读取当前壁纸 ID。 |
| `auto` | 检测到 iWallpaper 风格目录时使用 `iwallpaper`，否则使用 `generic`。 |

## 输出结构

```text
exports/
  videos/
    example.mp4
  covers/
    example.png
  manifest.json
  preview.html
```

`preview.html` 是独立 HTML，可以直接从导出目录打开。Web UI 也内置了导出后的视频预览播放器。

## 说明

本项目用于导出和转换你有权使用的本地媒体文件。它不会下载付费内容、绕过网络访问控制，也不会移除 DRM。有些壁纸软件会把本地缓存保存为私有或加密格式；某个 profile 能读取，只表示工具能处理你机器上已经存在的本地文件。

## 开发

不安装也可以从源码运行：

```bash
PYTHONPATH=src python3 -m wallpaper_mp4_exporter doctor
PYTHONPATH=src python3 -m wallpaper_mp4_exporter web
```

编译检查：

```bash
python3 -m compileall src
```

## 许可证

MIT
