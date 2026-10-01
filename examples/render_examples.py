#!/usr/bin/env python3
"""Rebuild the README examples from locally supplied source videos (not bundled)."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "skills/native-subtitle-quote-image/scripts/native_subtitle_stitch.py"
JOBS = [
    ("ACYAYsVMmT8", "smaller-coding-models", [(810, "Meta同时发布了新的代码模型"), (835, "它在编程基准上表现接近前沿系统"), (860, "调用成本更低，速度也更快"), (888, "对真实开发者来说"), (910, "最强分数不一定是最佳选择"), (925, "稳定、价格和延迟同样决定价值")]),
    ("31Uhv12ZLHU", "agi-capability-to-value", [(300, "第一组证据来自AI公司的收入增长"), (350, "企业正为模型能力支付真实成本"), (410, "先进芯片的需求也持续上升"), (470, "资本市场不是能力证明"), (525, "但它能说明技术开始进入生产流程"), (575, "时间线判断不能忽略这种经济反馈")]),
    ("31Uhv12ZLHU", "task-duration", [(600, "METR追踪模型能完成多长的任务"), (635, "数据显示任务时长大约每4个月翻倍"), (680, "这是目前最受关注的趋势之一"), (720, "但指标主要来自干净的编程任务"), (780, "而且只计算约50%的成功概率"), (835, "趋势惊人，解释却必须保持克制")]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="<video-id>/video.mp4 directories")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    for video_id, _, _ in JOBS:
        source = args.source_dir / video_id / "video.mp4"
        if not source.is_file():
            parser.error(f"Missing source video: {source}")
    expected = [args.out_dir / "demo-output-overview.jpg"]
    expected.extend(args.out_dir / f"{name}.{ext}" for _, name, _ in JOBS for ext in ("json", "jpg"))
    if any(path.exists() for path in expected):
        parser.error("Output files already exist; choose a new output directory.")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for video_id, name, lines in JOBS:
        script = args.out_dir / f"{name}.json"
        script.write_text(json.dumps({"lines": [{"t": t, "text": text} for t, text in lines]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        target = args.out_dir / f"{name}.jpg"
        subprocess.run([sys.executable, str(RENDERER), "render-script", str(args.source_dir / video_id / "video.mp4"), "--script", str(script), "--out", str(target), "--layout", "natural", "--width", "1440"], check=True)
        paths.append(target)
    spec = importlib.util.spec_from_file_location("stitch", RENDERER)
    stitch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stitch)
    stitch.contact_sheet(paths, args.out_dir / "demo-output-overview.jpg", columns=3)


if __name__ == "__main__":
    main()
