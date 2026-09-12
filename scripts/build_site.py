#!/usr/bin/env python3
"""Build MRI Learning from the two Google Drive synchronized directories."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCES = {
    "MRI撮像シーケンスのアクティブラーニングの解説": ("physics", "アクティブラーニング"),
    "シーケンス解説": ("sequences", "シーケンス解説"),
}
CATEGORIES = {"physics", "sequences", "artifacts", "parameters", "coils", "anatomy", "positioning", "questions"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
JST = ZoneInfo("Asia/Tokyo")
REVIEW_BASELINE_AT = datetime.fromisoformat("2026-09-12T19:23:11+09:00")


class BuildError(ValueError):
    pass


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta: dict[str, str] = {}
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            values = {str(k).lower(): v or "" for k, v in attrs}
            name = values.get("name", "").lower()
            if name.startswith("mri-"):
                self.meta[name] = values.get("content", "").strip()

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def csv_list(value: str) -> list[str]:
    return [part.strip() for part in value.replace("、", ",").split(",") if part.strip()]


def is_html(path: Path) -> bool:
    if not path.is_file() or path.name.startswith("."):
        return False
    try:
        start = path.read_text(encoding="utf-8")[:4096].lower()
    except (UnicodeDecodeError, OSError):
        return False
    return path.suffix.lower() in {".html", ".htm"} or "<html" in start or "<!doctype html" in start


def infer_category(title: str, default: str) -> str:
    if re.search(r"ghost|ゴースト|artifact|アーチファクト|banding|バンディング|shine-through", title, re.I):
        return "artifacts"
    if re.search(r"DICOM|撮像時間|パラメータ実践", title, re.I):
        return "parameters"
    if re.search(r"Bloch|方程式|T2\s*と\s*T2\*|物理動的", title, re.I):
        return "physics"
    return default


def make_id(title: str, relative: str) -> str:
    normalized = unicodedata.normalize("NFKC", title).lower()
    base = "-".join(re.findall(r"[a-z0-9]+", normalized)[:8]) or "material"
    digest = hashlib.sha256(unicodedata.normalize("NFC", relative).encode()).hexdigest()[:8]
    return f"{base[:60].rstrip('-')}-{digest}"


def make_review_key(relative: str) -> str:
    digest = hashlib.sha256(unicodedata.normalize("NFC", relative).encode()).hexdigest()[:16]
    return f"path-{digest}"


def git_history_dates(path: Path, root: Path) -> tuple[str, str, datetime] | None:
    """Return added date, updated date and added instant from the file's Git history."""
    relative = path.relative_to(root).as_posix()
    result = subprocess.run(
        ["git", "-C", str(root), "log", "--follow", "--format=%cI", "--", relative],
        check=False,
        capture_output=True,
        text=True,
    )
    history = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if result.returncode != 0 or not history:
        return None
    try:
        updated_at = datetime.fromisoformat(history[0]).astimezone(JST)
        added_at = datetime.fromisoformat(history[-1]).astimezone(JST)
    except ValueError:
        return None
    return added_at.date().isoformat(), updated_at.date().isoformat(), added_at


def parse_material(path: Path, root: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    source = path.relative_to(root).parts[0]
    if source not in SOURCES:
        raise BuildError(f"{relative}: source directory is not allowed")
    text = path.read_text(encoding="utf-8")
    parser = HeadParser()
    parser.feed(text)
    meta = parser.meta
    title = meta.get("mri-title") or parser.title.strip() or path.stem
    category = meta.get("mri-category") or infer_category(title, SOURCES[source][0])
    if category not in CATEGORIES:
        raise BuildError(f"{relative}: unknown category '{category}'")
    material_id = meta.get("mri-id") or make_id(title, relative)
    if not ID_RE.fullmatch(material_id):
        raise BuildError(f"{relative}: mri-id must be lowercase ASCII kebab-case")
    history_dates = git_history_dates(path, root)
    file_date = date.fromtimestamp(path.stat().st_mtime).isoformat()
    added = history_dates[0] if history_dates else file_date
    updated = meta.get("mri-updated") or (history_dates[1] if history_dates else file_date)
    try:
        date.fromisoformat(updated)
    except ValueError as exc:
        raise BuildError(f"{relative}: invalid mri-updated '{updated}'") from exc
    content_type = meta.get("mri-content-type") or ("simulator" if re.search(r"simulator|シミュレータ", title, re.I) else "guide")
    if content_type not in {"guide", "simulator"}:
        raise BuildError(f"{relative}: mri-content-type must be guide or simulator")
    fingerprint = hashlib.sha256(text.strip().encode()).hexdigest()
    return {
        "id": material_id, "title": title, "category": category,
        "reviewKey": material_id if meta.get("mri-id") else make_review_key(relative),
        "subcategory": meta.get("mri-subcategory") or SOURCES[source][1],
        "keywords": csv_list(meta.get("mri-keywords", "")) or [title, source],
        "description": meta.get("mri-description") or f"{title}を学ぶMRI教材です。",
        "addedAt": added,
        "updated": updated, "contentType": content_type,
        "reviewEligible": history_dates[2] > REVIEW_BASELINE_AT if history_dates else True,
        "manufacturer": csv_list(meta.get("mri-manufacturer", "")),
        "anatomy": csv_list(meta.get("mri-anatomy", "")),
        "path": f"{category}/{material_id}.html",
        "_source": relative, "_fingerprint": fingerprint,
    }


def discover(root: Path) -> list[dict[str, object]]:
    by_content: dict[str, dict[str, object]] = {}
    for source in SOURCES:
        directory = root / source
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if is_html(path):
                item = parse_material(path, root)
                by_content.setdefault(str(item["_fingerprint"]), item)
    materials = list(by_content.values())
    ids: set[str] = set()
    for item in materials:
        if item["id"] in ids:
            item["id"] = f"{item['id']}-{str(item['_fingerprint'])[:8]}"
            item["path"] = f"{item['category']}/{item['id']}.html"
        ids.add(str(item["id"]))
    materials.sort(key=lambda m: (str(m["updated"]), str(m["title"])), reverse=True)
    return materials


def build(root: Path, output: Path) -> list[dict[str, object]]:
    materials = discover(root)
    if not materials:
        raise BuildError("no HTML materials found in the two source directories")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in ("index.html", "review.html", "manifest.webmanifest", "sw.js"):
        shutil.copy2(root / name, output / name)
    shutil.copytree(root / "assets", output / "assets")
    for item in materials:
        target = output / str(item["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / str(item["_source"]), target)
    payload = {"schemaVersion": 2, "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "materials": [{k: v for k, v in item.items() if not k.startswith("_")} for item in materials]}
    (output / "materials.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / ".nojekyll").touch()
    return materials


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("_site"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        materials = discover(args.root) if args.check else build(args.root, args.output)
        if not materials:
            raise BuildError("no HTML materials found")
    except (BuildError, OSError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(f"Validated {len(materials)} materials" if args.check else f"Built {len(materials)} materials in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
