import json
import tempfile
import unittest
from pathlib import Path
from scripts.build_site import SOURCES, build, discover, is_html

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
            self.assertTrue(all((output / item["path"]).is_file() for item in data["materials"]))
            self.assertFalse(any(any(key.startswith("_") for key in item) for item in data["materials"]))

    def test_extensionless_html_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lesson-without-extension"
            path.write_text("<!doctype html><title>Lesson</title>", encoding="utf-8")
            self.assertTrue(is_html(path))

if __name__ == "__main__": unittest.main()
