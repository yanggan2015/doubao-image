#!/usr/bin/env bash
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${DOUBAO_WORK:-$SKILL}"
if [[ ! -d "$WORK/.venv" ]]; then
  bash "$SKILL/scripts/setup.sh"
fi
# shellcheck disable=SC1091
source "$WORK/.venv/bin/activate"
export HEADLESS="${HEADLESS:-0}"
export DOUBAO_WORK="$WORK"
PROMPT="${*:-生成一个美女在海边散步的图片，动漫风格}"
exec python "$SKILL/scripts/two_prompt_generate.py" --keep-round1 "$PROMPT"
