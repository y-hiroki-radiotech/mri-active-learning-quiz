"""MRIプロトコール専用: Google Drive の file ID でファイルを追跡する同期ラッパー。

~/.claude/skills/drive-sync/scripts/drive_sync.py はプロジェクト非依存の
共有エンジン(他プロジェクトも使う)なので、ここでは改修せずに import して
gws呼び出し・一覧取得・ダウンロードのプリミティブだけ再利用する。

共有エンジンの `sync` はローカル側の「Drive上の名前と同じパスにファイルが
存在するか」だけで既存/新規を判定するため、ダウンロード先でファイル名を
変更(リネーム)すると、次回同期時に「ローカルに無い」と誤判定されて元の
名前で再ダウンロードされ、重複が発生する。

このラッパーは `<dest>/.drive_sync_manifest.json` に file ID -> {ローカル
相対パス, md5} を記録し、Drive側の名前ではなく file ID を主キーにする:

- manifestに記録済みのfile IDについて、記録されたパスにファイルが無ければ、
  同じ内容(md5)のファイルをdest配下から探し、見つかればリネームとみなして
  manifestのパスを更新するだけで再ダウンロードしない。
- 見つからなければ(削除されたとみなし)Drive上の名前で新規取得する。
- manifest未登録のfile ID(初回実行時の既存ファイルを含む)は、Drive上の名前
  のパスに一致するファイルがあり中身も一致すれば、ダウンロードせずmanifestに
  登録するだけ(初回移行時に重複が発生しないようにするため)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GLOBAL_SCRIPTS_DIR = Path.home() / ".claude" / "skills" / "drive-sync" / "scripts"
sys.path.insert(0, str(GLOBAL_SCRIPTS_DIR))
import drive_sync as engine  # noqa: E402  (共有エンジンを再利用)

MANIFEST_NAME = ".drive_sync_manifest.json"


def _load_manifest(dest_dir: Path) -> dict:
    path = dest_dir / MANIFEST_NAME
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_manifest(dest_dir: Path, manifest: dict) -> None:
    path = dest_dir / MANIFEST_NAME
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _find_local_by_md5(dest_dir: Path, target_md5: str, exclude: set[Path]) -> Path | None:
    for path in dest_dir.rglob("*"):
        if not path.is_file() or path.name == MANIFEST_NAME or path in exclude:
            continue
        try:
            if engine._local_md5(path) == target_md5:
                return path
        except OSError:
            continue
    return None


def sync(folder_id: str, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(dest_dir)
    entries = engine.list_folder_tree(folder_id)
    if not entries:
        print("[sync] Drive フォルダにファイルが見つかりませんでした")
        return

    claimed: set[Path] = set()

    for entry in entries:
        file_id = entry["id"]
        remote_md5 = entry.get("md5Checksum")
        drive_rel_path = Path(entry["rel_path"])
        record = manifest.get(file_id)

        if record is None:
            # manifest未登録: 初回実行、またはDrive上の新規ファイル
            local_path = dest_dir / drive_rel_path
            if local_path.exists() and remote_md5 and engine._local_md5(local_path) == remote_md5:
                print(f"[sync] 既存ファイルを追跡対象に登録: {drive_rel_path}")
            else:
                print(f"[sync] 新規取得: {drive_rel_path}")
                engine.download_file(file_id, local_path)
            manifest[file_id] = {"path": str(drive_rel_path), "md5": remote_md5}
            claimed.add(local_path)
            continue

        local_path = dest_dir / record["path"]
        if local_path.exists():
            if remote_md5 and engine._local_md5(local_path) == remote_md5:
                print(f"[sync] skip (差分なし): {record['path']}")
            else:
                print(f"[sync] 更新を取得: {record['path']}")
                engine.download_file(file_id, local_path)
            manifest[file_id] = {"path": record["path"], "md5": remote_md5}
            claimed.add(local_path)
            continue

        # 記録されたパスに無い -> ローカルでリネーム/移動された可能性を探す
        old_md5 = record.get("md5")
        found = _find_local_by_md5(dest_dir, old_md5, claimed) if old_md5 else None
        if found is not None:
            rel = found.relative_to(dest_dir)
            print(f"[sync] ローカルでの名前変更を検知 (再取得せず追跡継続): {record['path']} -> {rel}")
            if remote_md5 and engine._local_md5(found) != remote_md5:
                print(f"[sync] 更新を取得: {rel}")
                engine.download_file(file_id, found)
            manifest[file_id] = {"path": str(rel), "md5": remote_md5}
            claimed.add(found)
            continue

        # リネーム先が見つからない -> ローカルで削除されたとみなしDrive上の名前で再取得
        new_path = dest_dir / drive_rel_path
        print(f"[sync] ローカルで見つからないため再取得: {drive_rel_path}")
        engine.download_file(file_id, new_path)
        manifest[file_id] = {"path": str(drive_rel_path), "md5": remote_md5}
        claimed.add(new_path)

    _save_manifest(dest_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="file IDでリネームを追跡するGoogle Drive同期(MRIプロトコール専用)"
    )
    parser.add_argument("--folder-id", required=True)
    parser.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    sync(args.folder_id, args.dest)


if __name__ == "__main__":
    main()
