# README 示例 / README examples

README 共展示 7 张图：4 张历史作品，以及 3 张 v2.3.0 原比例示例。所有案例均为 **后期脚本字幕（scripted）**。

## 精选历史成品 / Curated archive

| 案例 / Example | 字幕 / Copy | 来源 / Source | 台词与时间点 / Script |
| --- | --- | --- | --- |
| [陈数：工作投入，生活简单](gallery/chen-shu-simple-life.jpg) | 中文整理配文 · 5 句 | [网易谈心社 / Bilibili](https://www.bilibili.com/video/BV1Ym4y1W7CJ/) | [JSON](scripts/chen-shu-simple-life.json) |
| [UnJaded Jade：人生不能同时全部展开](gallery/jade-twenties-ko.jpg) | 韩文本地化 · 6 句 | [YouTube](https://www.youtube.com/watch?v=8kYXvq_h9Kk) | [JSON](scripts/jade-twenties-ko.json) |
| [Jordan Welch：AI 服务（英文）](gallery/jordan-ai-services-en.jpg) | 英文整理配文 · 6 句 | [YouTube](https://www.youtube.com/watch?v=RzFHcZA6uxA) | [JSON](scripts/jordan-ai-services-en.json) |
| [Jordan Welch：AI 服务（韩文）](gallery/jordan-ai-services-ko.jpg) | 韩文本地化 · 6 句 | [同一视频](https://www.youtube.com/watch?v=RzFHcZA6uxA) | [JSON](scripts/jordan-ai-services-ko.json) |


四张均为 1080 × 1440，直接复制既有 JPG，未改动像素、重新压缩或拉伸。Jordan Welch 两张使用相同的 6 个时间点，可对照英韩配文。陈数脚本同时保留存档中的 `source_text`，便于区分原文记录与整理配文。

来源链接取自本地制作记录，未重新核验视频在线状态或逐字翻译；这些图片展示排版效果，不作为人物的逐字引语。历史渲染版本及完整参数未确定，所附 JSON 用于追溯台词和时间点，不保证逐像素复现历史成品。结构化记录见 [gallery-manifest.json](gallery-manifest.json)。

These four 1080 × 1440 JPGs are copied unchanged from archived outputs. They demonstrate Chinese, English, and Korean scripted copy; the Jordan Welch pair shares the same timestamps. Source links come from archived production metadata and were not rechecked online. Chen Shu's script retains archived `source_text` alongside the edited copy. The original render versions and complete settings are unknown, so the JSON files document lines and timestamps rather than guarantee pixel-identical reproduction. These are not verified verbatim quotations.

Third-party footage, likenesses, logos, and text remain subject to their respective rights; the repository's MIT license does not grant rights to this material. Source videos are not included.

## v2.3.0 原比例示例 / Natural-layout examples

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
