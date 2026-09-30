#!/usr/bin/env python3
"""重新生成 README 首屏横幅（中文、英文各一张），需要本机安装 Chrome 或 Chromium。

横幅自带深色背景，GitHub 浅色、深色主题共用一张。
改文案：编辑下方 COPY；换展示图：编辑 SHOWCASE。然后运行 `python3 scripts/render_banners.py`。
渲染时从 Google Fonts 加载 Noto Sans SC 与 Inter，需要联网。
输出为带透明圆角的 WebP，比 PNG 小一个数量级。
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
ICON = ROOT / "assets" / "native-subtitle-quote-image-icon.png"
OUT_DIR = ROOT / "assets"
WIDTH, HEIGHT, SCALE = 900, 400, 2
WEBP_QUALITY = 90

# 扇形叠放的三张成品图：左、中、右。中间一张在最上层。
SHOWCASE = [
    ROOT / "examples" / "gallery" / "agi-capability-to-value.jpg",
    ROOT / "examples" / "demo-native-subtitle-collage.jpg",
    ROOT / "examples" / "gallery" / "smaller-coding-models.jpg",
]

COPY = {
    "zh": {
        "kicker": "NATIVE SUBTITLE QUOTE IMAGE",
        "title": "原生字幕拼图",
        "title_size": 50,
        "tagline": "把视频里的一段话，<br>做成一张能直接发的 3:4 字幕长图",
        "rule": "原生字幕不重绘 · 脚本字幕不冒充原字幕",
    },
    "en": {
        "kicker": "原生字幕拼图",
        "title": "Native Subtitle<br>Quote Image",
        "title_size": 42,
        "tagline": "Turn any video moment into<br>a ready-to-post 3:4 quote image",
        "rule": "Native never redrawn · Scripted never faked",
    },
}

ACCENT = "#e8542f"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
]
CHROME_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def build_html(lang, icon_src="icon.png", showcase_srcs=("s1.jpg", "s2.jpg", "s3.jpg")):
    copy = COPY[lang]
    left, middle, right = showcase_srcs
    return f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;800&family=Inter:wght@500;800&display=block" rel="stylesheet">
<style>
html,body{{margin:0;background:transparent}}
.card{{position:relative;width:{WIDTH - 2}px;height:{HEIGHT - 2}px;border-radius:20px;overflow:hidden;
 background:radial-gradient(600px 300px at 85% 30%,rgba(232,84,47,.22),transparent 60%),linear-gradient(160deg,#1a2029,#0d1117 70%);
 border:1px solid #30363d;color:#f0f6fc;font-family:Inter,'Noto Sans SC',sans-serif}}
.txt{{position:absolute;left:52px;top:0;bottom:0;width:420px;display:flex;flex-direction:column;justify-content:center}}
.row{{display:flex;align-items:center;gap:12px;margin-bottom:18px}}
.row img{{width:44px}}
.row b{{font-size:13px;font-weight:500;letter-spacing:.18em;color:#9198a1}}
h1{{font-size:{copy['title_size']}px;font-weight:800;line-height:1.15;margin:0 0 14px;letter-spacing:-.01em}}
p{{font-size:17px;line-height:1.6;color:#b1bac4;margin:0 0 20px}}
.rule{{font-size:13px;font-weight:500;color:#9198a1}}
.rule i{{display:inline-block;width:7px;height:7px;border-radius:50%;background:{ACCENT};margin-right:8px;vertical-align:1px}}
.fan img{{position:absolute;width:190px;border-radius:10px;box-shadow:0 20px 40px rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.08)}}
.fan .l{{right:250px;top:78px;transform:rotate(-8deg)}}
.fan .m{{right:140px;top:48px;z-index:2}}
.fan .r{{right:40px;top:78px;transform:rotate(8deg)}}
</style>
<body><div class="card">
<div class="txt"><div class="row"><img src="{icon_src}" alt=""><b>{copy['kicker']}</b></div>
<h1>{copy['title']}</h1><p>{copy['tagline']}</p><div class="rule"><i></i>{copy['rule']}</div></div>
<div class="fan"><img class="l" src="{left}" alt=""><img class="m" src="{middle}" alt=""><img class="r" src="{right}" alt=""></div>
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
        for index, image in enumerate(SHOWCASE, start=1):
            shutil.copyfile(image, tmp / f"s{index}.jpg")
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
