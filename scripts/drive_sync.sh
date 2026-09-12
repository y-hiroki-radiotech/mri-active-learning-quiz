#!/bin/bash
set -euo pipefail

BASE="/Users/yanagisawahiroki/Desktop/MRIプロトコール"
LOG="$HOME/Library/Logs/mri-drive-sync.log"
DRIVE_SYNC_PY="$BASE/scripts/drive_sync_local.py"
PYTHON_BIN="$(command -v python3 || echo /usr/bin/python3)"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') sync start ===" >> "$LOG"

"$PYTHON_BIN" "$DRIVE_SYNC_PY" \
  --folder-id 1y3q-mfYekq7t9KMBJ_xTQv3lH9yMrR_L \
  --dest "$BASE/シーケンス解説" >> "$LOG" 2>&1

"$PYTHON_BIN" "$DRIVE_SYNC_PY" \
  --folder-id 1GwSz1vYhJjaYN0EUaJ2IxAn-FOESwPEt \
  --dest "$BASE/MRI撮像シーケンスのアクティブラーニングの解説" >> "$LOG" 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S') sync end ===" >> "$LOG"
