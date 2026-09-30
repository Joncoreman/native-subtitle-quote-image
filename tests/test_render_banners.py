import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BANNER_SCRIPT = ROOT / "scripts" / "render_banners.py"
SPEC = importlib.util.spec_from_file_location("render_banners", BANNER_SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BannerHtmlTests(unittest.TestCase):
    def test_every_language_builds(self):
        for lang, copy in MODULE.COPY.items():
            with self.subTest(lang=lang):
                html = MODULE.build_html(lang)
                for key in ("kicker", "title", "tagline", "rule"):
                    self.assertIn(copy[key], html)
                for src in ("s1.jpg", "s2.jpg", "s3.jpg"):
                    self.assertIn(f'src="{src}"', html)

    def test_showcase_images_exist(self):
        self.assertEqual(len(MODULE.SHOWCASE), 3)
        for path in MODULE.SHOWCASE:
            self.assertTrue(path.is_file(), path)

    def test_committed_banners_exist(self):
        for lang in MODULE.COPY:
            path = ROOT / "assets" / f"banner-{lang}.webp"
            self.assertTrue(path.is_file(), path)


class FindChromeTests(unittest.TestCase):
    def test_explicit_path_wins(self):
        with mock.patch.dict(os.environ, {"CHROME": "/from/env"}):
            self.assertEqual(MODULE.find_chrome("/explicit"), "/explicit")

    def test_env_used_when_no_explicit_path(self):
        with mock.patch.dict(os.environ, {"CHROME": "/from/env"}):
            self.assertEqual(MODULE.find_chrome(), "/from/env")

    def test_returns_none_when_nothing_found(self):
        env = {k: v for k, v in os.environ.items() if k != "CHROME"}
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(MODULE, "CHROME_CANDIDATES", []), \
             mock.patch.object(MODULE.shutil, "which", return_value=None):
            self.assertIsNone(MODULE.find_chrome())


if __name__ == "__main__":
    unittest.main()
