import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.build_site import SOURCES, build, discover, is_html, parse_material

ROOT = Path(__file__).resolve().parents[1]

class BuildTests(unittest.TestCase):
    def test_current_two_directories_build(self):
        items = discover(ROOT)
        self.assertGreater(len(items), 0)
        self.assertEqual(len(items), len({item["id"] for item in items}))
        self.assertTrue(all(item["_source"].split("/", 1)[0] in SOURCES for item in items))

    def test_build_outputs_every_catalog_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "site"
            build(ROOT, output)
            data = json.loads((output / "materials.json").read_text(encoding="utf-8"))
            self.assertEqual(data["schemaVersion"], 2)
            self.assertTrue(all((output / item["path"]).is_file() for item in data["materials"]))
            self.assertFalse(any(any(key.startswith("_") for key in item) for item in data["materials"]))
            self.assertTrue((output / "review.html").is_file())

    def test_extensionless_html_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lesson-without-extension"
            path.write_text("<!doctype html><title>Lesson</title>", encoding="utf-8")
            self.assertTrue(is_html(path))

    def test_new_material_uses_first_git_commit_for_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / next(iter(SOURCES))
            source.mkdir()
            path = source / "new.html"
            path.write_text("<!doctype html><title>New lesson</title>", encoding="utf-8")
            history = "2026-09-20T10:00:00+09:00\n2026-09-13T08:00:00+09:00\n"
            completed = subprocess.CompletedProcess([], 0, stdout=history, stderr="")
            with patch("scripts.build_site.subprocess.run", return_value=completed) as git_log:
                item = parse_material(path, root)
            self.assertEqual(item["addedAt"], "2026-09-13")
            self.assertEqual(item["updated"], "2026-09-20")
            self.assertTrue(item["reviewEligible"])
            self.assertTrue(item["reviewKey"].startswith("path-"))
            self.assertIn("--follow", git_log.call_args.args[0])

            baseline_history = "2026-09-12T19:23:11+09:00\n"
            baseline_commit = subprocess.CompletedProcess([], 0, stdout=baseline_history, stderr="")
            with patch("scripts.build_site.subprocess.run", return_value=baseline_commit):
                baseline_item = parse_material(path, root)
            self.assertFalse(baseline_item["reviewEligible"])

if __name__ == "__main__": unittest.main()
