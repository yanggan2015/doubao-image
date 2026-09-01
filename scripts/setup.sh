#!/usr/bin/env bash
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${DOUBAO_WORK:-$SKILL}"
mkdir -p "$WORK/downloads" "$WORK/output" "$WORK/.chrome-profile"
if [[ ! -d "$WORK/.venv" ]]; then
  python3 -m venv "$WORK/.venv"
fi
# shellcheck disable=SC1091
source "$WORK/.venv/bin/activate"
pip install -U pip -q
pip install -r "$SKILL/requirements.txt" -q
python -m playwright install chromium
echo "OK skill=$SKILL work=$WORK"
