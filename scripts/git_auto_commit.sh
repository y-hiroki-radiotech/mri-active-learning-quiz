#!/bin/bash
# MRI教材の日次 Drive同期 -> 検証 -> 限定commit -> push パイプライン。
#
# GitHub自動コミット設定要件.md の3節(13ステップ)・6節(安全条件)に厳密に従う。
# 対象は DIR1/DIR2 の2ディレクトリのみ。それ以外の変更は一切commitしない。
#
# 使い方:
#   bash scripts/git_auto_commit.sh            # 本実行
#   bash scripts/git_auto_commit.sh --dry-run  # ステージまで実行し、commit/pushはしない
#
# テストから上書きできるよう、主要パスは環境変数で差し替え可能にしてある
# (本番launchdでは既定値をそのまま使う)。

set -uo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

REPO_DIR="${GIT_AUTO_COMMIT_REPO_DIR:-/Users/yanagisawahiroki/Desktop/MRIプロトコール}"
DIR1_NAME="${GIT_AUTO_COMMIT_DIR1:-MRI撮像シーケンスのアクティブラーニングの解説}"
DIR2_NAME="${GIT_AUTO_COMMIT_DIR2:-シーケンス解説}"
LOG="${GIT_AUTO_COMMIT_LOG:-$HOME/Library/Logs/mri-git-auto-commit.log}"
LOCKDIR="${GIT_AUTO_COMMIT_LOCKDIR:-/tmp/mri-git-auto-commit.lock}"
MAIN_BRANCH="${GIT_AUTO_COMMIT_MAIN_BRANCH:-main}"
REMOTE="${GIT_AUTO_COMMIT_REMOTE:-origin}"

log() {
  echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S %Z')] $*" >> "$LOG"
}

abort() {
  log "中断: $*"
  log "=== end (aborted) ==="
  exit 0
}

fail() {
  log "エラー: $*"
  log "=== end (error) ==="
  exit 1
}

log "=== start (dry_run=$DRY_RUN) ==="

# --- ステップ1: 多重実行防止ロック ---
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  log "他の実行が進行中のためスキップ"
  exit 0
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

# --- リポジトリ絶対パスの検証 ---
if [[ ! -d "$REPO_DIR/.git" ]]; then
  fail "リポジトリが見つかりません: $REPO_DIR"
fi
cd "$REPO_DIR" || fail "リポジトリへ移動できません: $REPO_DIR"

DIR1="$DIR1_NAME"
DIR2="$DIR2_NAME"
if [[ ! -d "$DIR1" ]]; then
  fail "対象ディレクトリが見つかりません: $DIR1"
fi
if [[ ! -d "$DIR2" ]]; then
  fail "対象ディレクトリが見つかりません: $DIR2"
fi

# --- ステップ2: リポジトリとoriginへのアクセス確認 ---
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "gitワークツリーではありません: $REPO_DIR"
fi
if ! git ls-remote --exit-code "$REMOTE" >/dev/null 2>&1; then
  abort "$REMOTE に到達できません"
fi

# --- ステップ3: 現在のブランチがmainであることの確認 ---
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "$MAIN_BRANCH" ]]; then
  abort "現在のブランチが $MAIN_BRANCH ではありません(現在: $current_branch)"
fi

# --- ステップ4: 対象ディレクトリ外に未commitの変更がないことを確認 ---
outside_changes="$(git status --porcelain -- . ":(exclude)$DIR1" ":(exclude)$DIR2")"
if [[ -n "$outside_changes" ]]; then
  abort "対象ディレクトリ外に未commitの変更があります(stash/破棄は行いません)"
fi

# --- ステップ5: リモートの変更を取得 ---
if ! git pull --ff-only "$REMOTE" "$MAIN_BRANCH" >>"$LOG" 2>&1; then
  abort "git pull --ff-only に失敗しました(rebase等は行いません)"
fi

# --- ステップ6: 既存のGoogle Drive同期スクリプトを実行 ---
if ! bash "$REPO_DIR/scripts/drive_sync.sh" >>"$LOG" 2>&1; then
  abort "drive_sync.sh の実行に失敗しました"
fi

# --- ステップ7: サイトビルドの検証 ---
if [[ -f "$REPO_DIR/scripts/build_site.py" ]]; then
  if ! python3 "$REPO_DIR/scripts/build_site.py" --check >>"$LOG" 2>&1; then
    abort "build_site.py --check が失敗しました(教材検証エラー)"
  fi
else
  log "警告: scripts/build_site.py が見つからないため検証をスキップします"
fi

# --- ステップ8: テスト実行 ---
if [[ -d "$REPO_DIR/tests" ]]; then
  if ! python3 -m unittest discover -s tests -v >>"$LOG" 2>&1; then
    abort "テストが失敗しました"
  fi
else
  log "警告: tests/ が見つからないためテストをスキップします"
fi

# --- ステップ9: 対象2ディレクトリだけをステージ ---
git add -- "$DIR1" "$DIR2"

# --- ステップ10: 差分なしなら正常終了 ---
if git diff --cached --quiet -- "$DIR1" "$DIR2"; then
  log "変更なし、commitしません"
  git reset -- "$DIR1" "$DIR2" >/dev/null 2>&1
  log "=== end (no changes) ==="
  exit 0
fi

changed_count="$(git diff --cached --name-only -- "$DIR1" "$DIR2" | wc -l | tr -d ' ')"
log "ステージされた変更ファイル数: $changed_count"

if [[ "$DRY_RUN" == true ]]; then
  log "--dry-run: 以下をステージしましたが commit/push は行いません"
  git diff --cached --stat -- "$DIR1" "$DIR2" >>"$LOG" 2>&1
  git diff --cached --stat -- "$DIR1" "$DIR2"
  git reset -- "$DIR1" "$DIR2" >/dev/null 2>&1
  log "=== end (dry-run) ==="
  exit 0
fi

# --- ステップ11: commitメッセージを決定してcommit ---
today="$(TZ=Asia/Tokyo date '+%Y-%m-%d')"
base_message="chore(materials): sync MRI lessons $today"
if git log --oneline -1 --grep="^chore(materials): sync MRI lessons $today" >/dev/null 2>&1 \
   && [[ -n "$(git log --oneline -1 --grep="^chore(materials): sync MRI lessons $today")" ]]; then
  now_time="$(TZ=Asia/Tokyo date '+%H:%M')"
  commit_message="chore(materials): sync MRI lessons $today $now_time JST"
else
  commit_message="$base_message"
fi

if ! git commit -m "$commit_message" >>"$LOG" 2>&1; then
  fail "git commit に失敗しました"
fi
commit_sha="$(git rev-parse --short HEAD)"
log "commit作成: $commit_sha ($commit_message)"

# --- ステップ12: push ---
if git push "$REMOTE" "$MAIN_BRANCH" >>"$LOG" 2>&1; then
  log "push成功: $REMOTE/$MAIN_BRANCH"
else
  log "push失敗(non-fast-forward等の可能性): ローカルcommit $commit_sha は残しています。force/rebaseは行いません"
  log "=== end (push failed) ==="
  exit 1
fi

# --- ステップ13: 完了 ---
log "=== end (success) ==="
exit 0
