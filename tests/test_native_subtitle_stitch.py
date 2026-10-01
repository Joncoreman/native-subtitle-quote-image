import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "native-subtitle-quote-image"
    / "scripts"
    / "native_subtitle_stitch.py"
)
ENV_SCRIPT = (
    ROOT
    / "skills"
    / "native-subtitle-quote-image"
    / "scripts"
    / "check_environment.py"
)
SPEC = importlib.util.spec_from_file_location("native_subtitle_stitch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HelperTests(unittest.TestCase):
    def test_parse_aspect_and_safe_title(self):
        self.assertEqual(MODULE.parse_aspect("3:4"), (3.0, 4.0))
        self.assertEqual(MODULE.safe_title('a/b:c*?"<>|'), "a_b_c")

    def test_default_sample_times_cover_range_with_24_frames(self):
        times = MODULE.build_sample_times(0, 230, None, 48)
        self.assertEqual(len(times), 24)
        self.assertEqual(times[0], 0)
        self.assertAlmostEqual(times[-1], 230)

    def test_sample_times_enforce_frame_cap(self):
        with self.assertRaisesRegex(SystemExit, "超过上限"):
            MODULE.build_sample_times(0, 100, 1, 48)

    def test_focus_times_add_before_middle_and_after(self):
        times = MODULE.build_focus_times([1, 3], 0.5, 5, 48)
        self.assertEqual(times, [0.5, 1.0, 1.5, 2.5, 3.0, 3.5])

    def test_focus_times_clip_and_deduplicate_edges(self):
        times = MODULE.build_focus_times([0, 2.7], 0.5, 3, 48)
        self.assertEqual(times, [0.0, 0.5, 2.2, 2.7])

    def test_auto_layout_keeps_subtitle_strips_compact(self):
        self.assertEqual(MODULE.choose_hero_fraction(4), 0.7)
        self.assertEqual(MODULE.choose_hero_fraction(3), 0.775)
        self.assertEqual(MODULE.choose_hero_fraction(2), 0.82)
        self.assertEqual(MODULE.choose_hero_fraction(7), 0.48)
        self.assertEqual(MODULE.choose_hero_fraction(4, 0.6), 0.6)

    def test_script_lines_require_increasing_timestamps_and_text(self):
        lines = MODULE.normalize_script_lines(
            {
                "lines": [
                    {"t": 1, "text": "First"},
                    {"t": 2, "text": "Second"},
                ]
            },
            3,
        )
        self.assertEqual(lines[1]["text"], "Second")
        with self.assertRaisesRegex(SystemExit, "严格递增"):
            MODULE.normalize_script_lines(
                {
                    "lines": [
                        {"t": 2, "text": "First"},
                        {"t": 1, "text": "Second"},
                    ]
                },
                3,
            )
        with self.assertRaisesRegex(SystemExit, "最多支持 7"):
            MODULE.normalize_script_lines(
                {
                    "lines": [
                        {"t": index / 10, "text": f"Line {index}"}
                        for index in range(8)
                    ]
                },
                3,
            )

    def test_native_times_share_script_mode_cap(self):
        times = MODULE.normalize_times([index / 10 for index in range(7)])
        self.assertEqual(len(times), 7)
        with self.assertRaisesRegex(SystemExit, "最多支持 7"):
            MODULE.normalize_times([index / 10 for index in range(8)])

    def test_cjk_detection_covers_chinese_japanese_and_korean(self):
        self.assertTrue(MODULE.contains_cjk("中文"))
        self.assertTrue(MODULE.contains_cjk("かな"))
        self.assertTrue(MODULE.contains_cjk("한글"))
        self.assertFalse(MODULE.contains_cjk("English"))

    def test_environment_check_local_mode_is_machine_readable(self):
        proc = subprocess.run(
            [sys.executable, str(ENV_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["mode"], "local")
        self.assertTrue(payload["ok"])
        components = {item["component"] for item in payload["components"]}
        self.assertIn("Python 3.10+", components)
        self.assertIn("yt-dlp", components)
        self.assertIn("CJK font", components)

    def test_environment_check_url_mode_guides_cookie_recovery(self):
        proc = subprocess.run(
            [sys.executable, str(ENV_SCRIPT), "--url-mode"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn("不要退回本地模式", proc.stdout)
        self.assertIn("--cookies-from-browser chrome", proc.stdout)

    def test_render_one_has_requested_dimensions(self):
        frame = Image.new("RGB", (640, 360), "#336699")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / "render.jpg"
            MODULE.render_one(
                "unused.mp4",
                [0, 1, 2, 3, 4],
                out,
                (3, 4),
                300,
                0.68,
                0.96,
                0.42,
            )
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (300, 400))

    def test_render_one_auto_layout_gives_hero_seventy_percent(self):
        def fake_frame(_video, seconds):
            color = "#cc0000" if seconds == 0 else "#0033cc"
            return Image.new("RGB", (640, 360), color)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", side_effect=fake_frame
        ):
            out = Path(tmp) / "auto-layout.jpg"
            MODULE.render_one(
                "unused.mp4",
                [0, 1, 2, 3, 4],
                out,
                (3, 4),
                300,
                0.78,
                0.96,
                None,
            )
            with Image.open(out) as rendered:
                self.assertGreater(rendered.getpixel((10, 279))[0], 180)
                self.assertGreater(rendered.getpixel((10, 280))[2], 150)

    def test_missing_input_is_readable_without_traceback(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "render",
                "/no/such/video.mp4",
                "--manifest",
                "/no/such/manifest.json",
                "--out-dir",
                "/tmp/unused-native-subtitle-output",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("视频不存在或不是文件", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


class NaturalGeometryTests(unittest.TestCase):
    def test_crop_and_same_width_keep_exact_source_pixels(self):
        frame = Image.new("RGB", (1280, 720), "black")
        ImageDraw.Draw(frame).ellipse((100, 100, 300, 300), fill="white")
        cropped, y0, y1 = MODULE.crop_band(frame, 0, 0.72)
        result = MODULE.scale_to_width(cropped, 1280)
        self.assertEqual((y0, y1), (0, 518))
        self.assertEqual(result.size, (1280, 518))
        self.assertEqual(result.tobytes(), frame.crop((0, 0, 1280, 518)).tobytes())

    def test_scaling_preserves_circle_geometry(self):
        frame = Image.new("RGB", (1280, 518), "black")
        ImageDraw.Draw(frame).ellipse((100, 100, 300, 300), fill="white")
        result = MODULE.scale_to_width(frame, 640)
        bounds = result.convert("L").point(lambda p: 255 if p > 127 else 0).getbbox()
        self.assertEqual(result.size, (640, 259))
        self.assertLessEqual(abs((bounds[2] - bounds[0]) - (bounds[3] - bounds[1])), 1)

    def test_native_natural_retains_full_width_and_band_height(self):
        frame = Image.new("RGB", (640, 360), "#336699")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / "native.jpg"
            MODULE.render_one("unused", [0, 1, 2, 3, 4], out, (3, 4), None,
                              0.78, 0.96, None, layout="natural")
            with Image.open(out) as rendered:
                # 主图 345 + 四条 (345 - 280)，没有填满固定画布。
                self.assertEqual(rendered.size, (640, 605))

    def test_scripted_crop_does_not_stretch_hero_back_to_source_height(self):
        frame = Image.new("RGB", (1280, 720), "black")
        ImageDraw.Draw(frame).ellipse((100, 100, 300, 300), fill="white")
        lines = [{"t": index, "text": f"Line {index}"} for index in range(5)]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ), mock.patch.object(MODULE, "draw_scripted_subtitle") as draw_text:
            out = Path(tmp) / "script.jpg"
            MODULE.scripted_render_one("unused", lines, out, (3, 4), None,
                                       0.88, None, None, None,
                                       layout="natural", frame_bottom=0.72)
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (1280, 806))
                bounds = rendered.crop((0, 0, 1280, 518)).convert("L").point(
                    lambda p: 255 if p > 127 else 0
                ).getbbox()
                self.assertEqual(bounds[2] - bounds[0], bounds[3] - bounds[1])
            self.assertEqual([call.args[1] for call in draw_text.call_args_list],
                             [line["text"] for line in lines])

    def test_cli_rejects_conflicting_layout_and_invalid_crop_before_io(self):
        for options, message in [
            (["--layout", "natural", "--aspect", "3:4"], "不接受"),
            (["--layout", "natural", "--hero-fraction", "0.7"], "不接受"),
            (["--frame-top", "0.8", "--frame-bottom", "0.2"], "裁切必须满足"),
        ]:
            with self.subTest(options=options):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "render-script", "unused.mp4",
                     "--script", "unused.json", "--out", "unused.jpg", *options],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)


class CliIntegrationTests(unittest.TestCase):
    def test_sample_band_and_render_with_synthetic_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "synthetic.mp4"
            subprocess.run(
                [
                    MODULE.FFMPEG,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=640x360:rate=10",
                    "-t",
                    "3",
                    "-c:v",
                    "mpeg4",
                    "-pix_fmt",
                    "yuv420p",
                    str(video),
                ],
                check=True,
                capture_output=True,
            )

            sample = tmp_path / "candidate.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sample",
                    str(video),
                    "--start",
                    "0.5",
                    "--end",
                    "2.5",
                    "--interval",
                    "1",
                    "--out",
                    str(sample),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(sample.is_file())

            default_sample = tmp_path / "default-candidate.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sample",
                    str(video),
                    "--out",
                    str(default_sample),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(default_sample.is_file())

            focused_sample = tmp_path / "focused-candidate.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sample",
                    str(video),
                    "-t",
                    "1",
                    "-t",
                    "2",
                    "--around",
                    "0.2",
                    "--out",
                    str(focused_sample),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(focused_sample.is_file())

            band = tmp_path / "band.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "band",
                    str(video),
                    "-t",
                    "1",
                    "--out",
                    str(band),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(band.is_file())

            manifest = tmp_path / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {"images": [{"title": "合成测试", "times": [0.5, 1, 1.5, 2, 2.5]}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out_dir = tmp_path / "output"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render",
                    str(video),
                    "--manifest",
                    str(manifest),
                    "--out-dir",
                    str(out_dir),
                    "--width",
                    "300",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            output = out_dir / "01_合成测试.jpg"
            self.assertTrue(output.is_file())
            self.assertTrue((out_dir / "final_contact_sheet.jpg").is_file())
            self.assertTrue((out_dir / "原生字幕时间点.json").is_file())
            with Image.open(output) as rendered:
                self.assertEqual(rendered.size, (300, 400))

            script = tmp_path / "script.json"
            script.write_text(
                json.dumps(
                    {
                        "lines": [
                            {"t": 0.5, "text": "First point"},
                            {"t": 1.0, "text": "Second point"},
                            {"t": 1.5, "text": "Third point"},
                            {"t": 2.0, "text": "Fourth point"},
                            {"t": 2.5, "text": "Fifth point"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            scripted_output = tmp_path / "scripted.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render-script",
                    str(video),
                    "--script",
                    str(script),
                    "--out",
                    str(scripted_output),
                    "--width",
                    "300",
                    "--font-size",
                    "18",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            with Image.open(scripted_output) as rendered:
                self.assertEqual(rendered.size, (300, 400))

            for command, inputs, expected in [
                ("render", ["--manifest", str(manifest), "--out-dir", str(tmp_path / "natural")], (640, 605)),
                ("render-script", ["--script", str(script), "--out", str(tmp_path / "natural-script.jpg"),
                                   "--frame-bottom", "0.72"], (640, 403)),
            ]:
                subprocess.run(
                    [sys.executable, str(SCRIPT), command, str(video), *inputs, "--layout", "natural"],
                    check=True, capture_output=True, text=True,
                )
                natural_path = (tmp_path / "natural" / "01_合成测试.jpg" if command == "render"
                                else tmp_path / "natural-script.jpg")
                with Image.open(natural_path) as rendered:
                    self.assertEqual(rendered.size, expected)

            repeated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render",
                    str(video),
                    "--manifest",
                    str(manifest),
                    "--out-dir",
                    str(out_dir),
                    "--width",
                    "300",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("--overwrite", repeated.stderr)


if __name__ == "__main__":
    unittest.main()
