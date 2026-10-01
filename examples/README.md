# README 示例 / README examples

这组图由 v2.3.0 的 `render-script` 从真实视频重新渲染。沿用此前公开示例的来源、时间点及中文台词，不代表对视频观点或翻译准确性的独立核验。

**字幕来源：后期中文字幕（scripted），不是原生字幕。** 原视频未随仓库分发；画面、节目标识及内容的权利仍归各自权利人，MIT 许可不授予第三方视频素材的使用权。处理或重新发布素材前，请自行确认所需授权。

| 输出 | 来源 | 参数 |
| --- | --- | --- |
| [编程模型](gallery/smaller-coding-models.jpg) | [Matt Wolfe](https://www.youtube.com/watch?v=ACYAYsVMmT8) | natural / width 1440 |
| [能力与价值](gallery/agi-capability-to-value.jpg) | [80,000 Hours](https://www.youtube.com/watch?v=31Uhv12ZLHU) | natural / width 1440 |
| [任务时长](gallery/task-duration.jpg) | [80,000 Hours](https://www.youtube.com/watch?v=31Uhv12ZLHU) | natural / width 1440 |

每张 6 个时间点、1440 × 1215；主画面保留源视频 16:9，不强制裁成竖屏、不做非等比拉伸；字幕条之间无空隙。全部时间点和台词在 `render_examples.py` 中。总览由同版工具的 `contact_sheet` 生成。

## 复现 / Reproduce

自行准备有权处理的视频：

```text
source/
  ACYAYsVMmT8/video.mp4
  31Uhv12ZLHU/video.mp4
```

在仓库根目录运行（使用新的输出目录，工具默认拒绝覆盖成品）：

```bash
python3 examples/render_examples.py --source-dir /path/to/source --out-dir /path/to/new-output
```

需要 Pillow、FFmpeg 和中文字体；本次使用 macOS `STHeiti Medium.ttc`。不同字体可能导致字形变化。

These examples use **post-rendered Chinese scripted subtitles**, not burned-in native subtitles. They were rebuilt with v2.3.0 using the previously published examples' sources and lines. Source videos are not bundled; third-party footage and logos are not covered by the MIT license. Ensure you have the required rights before using or republishing them. The command above reads local videos and produces images plus line JSON files in a new output directory.
