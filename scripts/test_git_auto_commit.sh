#!/bin/bash
# scripts/git_auto_commit.sh の簡易自動テスト。
# 1) シェル構文検査 (bash -n)
# 2) 使い捨てのbare origin + 作業リポジトリを用意し、主要シナリオを検証する。
#
# 実リポジトリやGoogle Driveには一切アクセスしない
# (scripts/drive_sync.sh はテスト用のスタブに差し替える)。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/git_auto_commit.sh"

FAILURES=0
pass() { echo "  OK: $1"; }
failcase() { echo "  NG: $1"; FAILURES=$((FAILURES + 1)); }

echo "=== 1) シェル構文検査 ==="
if bash -n "$TARGET_SCRIPT"; then
  pass "bash -n 構文チェック"
else
  failcase "bash -n 構文チェック"
fi

echo ""
echo "=== 2) パイプラインの動作検証(使い捨てリポジトリ) ==="

WORKDIR="$(mktemp -d /tmp/mri-git-auto-commit-test.XXXXXX)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

ORIGIN="$WORKDIR/origin.git"
REPO="$WORKDIR/repo"
DIR1="MRI撮像シーケンスのアクティブラーニングの解説"
DIR2="シーケンス解説"

setup_repo() {
  rm -rf "$ORIGIN" "$REPO"
  git init --bare -q "$ORIGIN"

  git init -q "$REPO"
  git -C "$REPO" config user.name "test"
  git -C "$REPO" config user.email "test@example.com"
  git -C "$REPO" checkout -q -b main
  git -C "$REPO" remote add origin "$ORIGIN"

  mkdir -p "$REPO/$DIR1" "$REPO/$DIR2" "$REPO/scripts"
  echo "<html>initial</html>" > "$REPO/$DIR1/sample1.html"
  echo "<html>initial</html>" > "$REPO/$DIR2/sample2.html"
  echo "readme" > "$REPO/README.md"
  # drive_sync.sh はネットワークアクセスしないスタブに差し替える(呼ばれたことだけ記録)
  cat > "$REPO/scripts/drive_sync.sh" <<'EOS'
#!/bin/bash
echo "stub drive_sync.sh called" >> "$(dirname "$0")/../.drive_sync_stub_called"
exit 0
EOS
  chmod +x "$REPO/scripts/drive_sync.sh"

  git -C "$REPO" add -A
  git -C "$REPO" commit -q -m "initial"
  git -C "$REPO" push -q origin main
}

run_target() {
  GIT_AUTO_COMMIT_REPO_DIR="$REPO" \
  GIT_AUTO_COMMIT_DIR1="$DIR1" \
  GIT_AUTO_COMMIT_DIR2="$DIR2" \
  GIT_AUTO_COMMIT_LOG="$WORKDIR/test.log" \
  GIT_AUTO_COMMIT_LOCKDIR="$WORKDIR/lock.$$" \
  GIT_AUTO_COMMIT_MAIN_BRANCH="main" \
  GIT_AUTO_COMMIT_REMOTE="origin" \
  bash "$TARGET_SCRIPT" "$@"
}

commit_count() {
  git -C "$REPO" rev-list --count HEAD
}

# --- テストA: 変更が無ければcommitが作られない ---
setup_repo
before="$(commit_count)"
run_target >/dev/null 2>&1
after="$(commit_count)"
if [[ "$before" == "$after" ]]; then
  pass "テストA: 変更なし時はcommitされない"
else
  failcase "テストA: 変更なし時はcommitされない (commit数が変化: $before -> $after)"
fi

# --- テストB: 対象ディレクトリに新規ファイル -> commit・push される ---
setup_repo
echo "<html>new</html>" > "$REPO/$DIR1/new-material.html"
before="$(commit_count)"
run_target >/dev/null 2>&1
after="$(commit_count)"
origin_head="$(git -C "$REPO" ls-remote origin main | cut -f1)"
local_head="$(git -C "$REPO" rev-parse HEAD)"
if [[ "$after" -gt "$before" ]] && [[ "$origin_head" == "$local_head" ]]; then
  pass "テストB: 新規ファイル追加でcommit・pushされる"
else
  failcase "テストB: 新規ファイル追加でcommit・pushされる (commit: $before->$after, origin一致: $([[ "$origin_head" == "$local_head" ]] && echo yes || echo no))"
fi

# --- テストC: mainでないブランチでは中断する ---
setup_repo
git -C "$REPO" checkout -q -b feature/tmp
echo "<html>new</html>" > "$REPO/$DIR1/new-material.html"
before="$(commit_count)"
run_target >/dev/null 2>&1
after="$(commit_count)"
if [[ "$before" == "$after" ]]; then
  pass "テストC: main以外のブランチでは中断される"
else
  failcase "テストC: main以外のブランチでは中断される (commit数が変化)"
fi

# --- テストD: 対象外ファイルに未commit変更があると中断する ---
setup_repo
echo "unrelated local edit" >> "$REPO/README.md"
before="$(commit_count)"
run_target >/dev/null 2>&1
after="$(commit_count)"
readme_content="$(cat "$REPO/README.md")"
if [[ "$before" == "$after" ]] && grep -q "unrelated local edit" <<<"$readme_content"; then
  pass "テストD: 対象外の未commit変更があると中断され、破棄もされない"
else
  failcase "テストD: 対象外の未commit変更があると中断される"
fi

# --- テストE: git pull --ff-only が失敗する状況では中断しローカルを破壊しない ---
setup_repo
# origin側だけ別クローンで進める(local historyに無いコミット)
OTHER_CLONE="$WORKDIR/other_clone"
git clone -q "$ORIGIN" "$OTHER_CLONE"
git -C "$OTHER_CLONE" config user.name "test"
git -C "$OTHER_CLONE" config user.email "test@example.com"
echo "origin only change" >> "$OTHER_CLONE/README.md"
git -C "$OTHER_CLONE" commit -q -am "origin-only commit"
git -C "$OTHER_CLONE" push -q origin main
# local側にもorigin未反映のローカルコミットを作り、履歴を分岐させる
echo "<html>local only</html>" > "$REPO/$DIR2/local-only.html"
git -C "$REPO" add "$DIR2/local-only.html"
git -C "$REPO" commit -q -m "local-only commit"
before_head="$(git -C "$REPO" rev-parse HEAD)"
run_target >/dev/null 2>&1
after_head="$(git -C "$REPO" rev-parse HEAD)"
if [[ "$before_head" == "$after_head" ]]; then
  pass "テストE: ff-only pull失敗時は中断しローカルを変更しない"
else
  failcase "テストE: ff-only pull失敗時は中断しローカルを変更しない (HEADが変化)"
fi

echo ""
if [[ "$FAILURES" -eq 0 ]]; then
  echo "全テスト成功"
  exit 0
else
  echo "$FAILURES 件のテストが失敗しました"
  exit 1
fi
