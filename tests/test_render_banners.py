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
    def test_every_language_and_theme_builds(self):
        for lang, copy in MODULE.COPY.items():
            for theme, colors in MODULE.THEMES.items():
                with self.subTest(lang=lang, theme=theme):
                    html = MODULE.build_html(lang, theme)
                    self.assertIn(copy["title"], html)
                    self.assertIn(copy["tagline"], html)
                    for pill in copy["pills"]:
                        self.assertIn(pill, html)
                    self.assertIn(colors["fg"], html)

    def test_committed_banners_exist(self):
        for lang in MODULE.COPY:
            for theme in MODULE.THEMES:
                path = ROOT / "assets" / f"banner-{lang}-{theme}.png"
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
