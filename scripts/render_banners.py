#!/usr/bin/env python3
"""重新生成 README 首屏横幅（中英文 × 深浅色），需要本机安装 Chrome 或 Chromium。

改文案：编辑下方 COPY，然后运行 `python3 scripts/render_banners.py`。
渲染时从 Google Fonts 加载 Noto Sans SC 与 Inter，需要联网。
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "assets" / "native-subtitle-quote-image-icon.png"
OUT_DIR = ROOT / "assets"
WIDTH, HEIGHT, SCALE = 1200, 340, 2

COPY = {
    "zh": {
        "kicker": "NATIVE SUBTITLE QUOTE IMAGE",
        "title": "原生字幕拼图",
        "title_size": 78,
        "tagline": "把视频里的一段话，做成一张能直接发的 3:4 字幕长图",
        "pills": ["原生字幕 · 不重绘", "脚本字幕 · 不冒充原字幕"],
    },
    "en": {
        "kicker": "原生字幕拼图",
        "title": "Native Subtitle<br>Quote Image",
        "title_size": 56,
        "tagline": "Turn any video moment into a ready-to-post 3:4 quote image",
        "pills": ["Native · never redrawn", "Scripted · never passed off as native"],
    },
}

# 与 GitHub 浅色、深色主题的前景、次要文字和边框色保持一致。
THEMES = {
    "light": {"fg": "#1f2328", "muted": "#59636e", "pill": "#f6f8fa", "border": "#d1d9e0"},
    "dark": {"fg": "#f0f6fc", "muted": "#9198a1", "pill": "#151b23", "border": "#3d444d"},
}
ACCENT = "#e8542f"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
]
CHROME_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def build_html(lang, theme, icon_src="icon.png"):
    copy, colors = COPY[lang], THEMES[theme]
    pills = "".join(f"<span>{text}</span>" for text in copy["pills"])
    return f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;800&family=Inter:wght@500;800&display=block" rel="stylesheet">
<style>
html,body{{margin:0;background:transparent}}
body{{width:{WIDTH}px;height:{HEIGHT}px;display:flex;align-items:center;justify-content:center;gap:48px;
 font-family:Inter,'Noto Sans SC',sans-serif;color:{colors['fg']}}}
img{{width:216px;height:216px;filter:drop-shadow(0 12px 24px rgba(0,0,0,.28))}}
.kicker{{font-size:17px;font-weight:500;letter-spacing:.2em;color:{colors['muted']};margin-bottom:10px}}
h1{{font-size:{copy['title_size']}px;font-weight:800;line-height:1.08;margin:0 0 16px;letter-spacing:-.01em}}
.tagline{{font-size:25px;color:{colors['muted']};margin-bottom:22px;white-space:nowrap}}
.pills{{display:flex;gap:12px}}
.pills span{{font-size:19px;font-weight:500;padding:8px 16px;border-radius:999px;background:{colors['pill']};border:1px solid {colors['border']}}}
.pills span::before{{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;background:{ACCENT};margin-right:10px;vertical-align:2px}}
</style>
<body><img src="{icon_src}" alt=""><div>
<div class="kicker">{copy['kicker']}</div><h1>{copy['title']}</h1>
<div class="tagline">{copy['tagline']}</div><div class="pills">{pills}</div>
</div></body>
"""


def find_chrome(explicit=None):
    for candidate in (explicit, os.environ.get("CHROME")):
        if candidate:
            return candidate
    for path in CHROME_CANDIDATES:
        if Path(path).is_file():
            return path
    for command in CHROME_COMMANDS:
        found = shutil.which(command)
        if found:
            return found
    return None


def render(chrome, html_path, png_path):
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--force-device-scale-factor={SCALE}",
            f"--window-size={WIDTH},{HEIGHT}",
            "--default-background-color=00000000",
            "--virtual-time-budget=8000",
            "--allow-file-access-from-files",
            f"--screenshot={png_path}",
            html_path.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lang", choices=sorted(COPY), action="append", help="只生成指定语言，可重复")
    parser.add_argument("--theme", choices=sorted(THEMES), action="append", help="只生成指定主题，可重复")
    parser.add_argument("--chrome", help="Chrome/Chromium 可执行文件路径；也可用 CHROME 环境变量")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="输出目录，默认 assets/")
    args = parser.parse_args()

    chrome = find_chrome(args.chrome)
    if not chrome:
        sys.exit("找不到 Chrome 或 Chromium，请用 --chrome 或 CHROME 环境变量指定路径。")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copyfile(ICON, tmp / "icon.png")
        for lang in args.lang or sorted(COPY):
            for theme in args.theme or sorted(THEMES):
                html_path = tmp / f"{lang}-{theme}.html"
                html_path.write_text(build_html(lang, theme), encoding="utf-8")
                png_path = (args.out_dir / f"banner-{lang}-{theme}.png").resolve()
                render(chrome, html_path, png_path)
                if not png_path.is_file() or png_path.stat().st_size == 0:
                    sys.exit(f"渲染失败: {png_path}")
                print(f"完成: {png_path.relative_to(ROOT) if png_path.is_relative_to(ROOT) else png_path}")


if __name__ == "__main__":
    main()
