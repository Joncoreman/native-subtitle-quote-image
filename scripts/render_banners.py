#!/usr/bin/env python3
"""重新生成 README 首屏横幅（中文、英文各一张），需要本机安装 Chrome 或 Chromium。

横幅自带深色背景，GitHub 浅色、深色主题共用一张。
改标题：编辑下方 COPY；改边缘插画：替换 assets/banner-ornaments.png。
运行 `python3 scripts/render_banners.py`；渲染时从 Google Fonts 加载手写字体，需要联网。
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ROOT / "assets" / "banner-ornaments.png"
OUT_DIR = ROOT / "assets"
WIDTH, HEIGHT, SCALE = 1120, 350, 2
WEBP_QUALITY = 90

COPY = {
    "zh": {
        "title": "原生字幕拼图",
        "title_size": 86,
        "font": "'ZCOOL KuaiLe', 'Noto Sans SC', sans-serif",
    },
    "en": {
        "title": "NATIVE SUBTITLE<br>QUOTE IMAGE",
        "title_size": 70,
        "font": "'Kalam', cursive",
    },
}

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
]
CHROME_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def build_html(lang, background_src="background.png"):
    copy = COPY[lang]
    return f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@700&family=Noto+Sans+SC:wght@700&family=ZCOOL+KuaiLe&display=block" rel="stylesheet">
<style>
html,body{{margin:0;background:transparent}}
.card{{position:relative;width:{WIDTH}px;height:{HEIGHT}px;overflow:hidden;
 background:#111113 url('{background_src}') center/cover no-repeat;
 display:flex;align-items:center;justify-content:center}}
h1{{max-width:780px;margin:0;text-align:center;white-space:nowrap;
 font-family:{copy['font']};font-size:{copy['title_size']}px;font-weight:700;
 line-height:1.08;letter-spacing:.005em;color:#ddd9ff;
 text-shadow:0 2px 1px rgba(0,0,0,.42)}}
</style>
<body><div class="card"><h1>{copy['title']}</h1></div></body>
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
    parser.add_argument("--chrome", help="Chrome/Chromium 可执行文件路径；也可用 CHROME 环境变量")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="输出目录，默认 assets/")
    args = parser.parse_args()

    chrome = find_chrome(args.chrome)
    if not chrome:
        sys.exit("找不到 Chrome 或 Chromium，请用 --chrome 或 CHROME 环境变量指定路径。")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copyfile(BACKGROUND, tmp / "background.png")
        for lang in args.lang or sorted(COPY):
            html_path = tmp / f"{lang}.html"
            html_path.write_text(build_html(lang), encoding="utf-8")
            png_path = tmp / f"{lang}.png"
            render(chrome, html_path, png_path)
            if not png_path.is_file() or png_path.stat().st_size == 0:
                sys.exit(f"渲染失败: {lang}")
            out_path = (args.out_dir / f"banner-{lang}.webp").resolve()
            with Image.open(png_path) as image:
                image.save(out_path, "WEBP", quality=WEBP_QUALITY, method=6)
            print(f"完成: {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}")


if __name__ == "__main__":
    main()
