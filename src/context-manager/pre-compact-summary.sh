#!/usr/bin/env bash
# Context Manager for Claude Code
# PreCompact hook — generates and archives session summary before compaction.
# Runs pre-compact-summary.py with Gemini/Ollama/fallback quality tiers.
#
# Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
# License: MIT | Repository: https://github.com/Jonohobs/ai-hot-sauce
# Created: 2026-03-18

set -euo pipefail

SCRIPT_DIR="$HOME/.claude/hooks"
SUMMARIZER="$SCRIPT_DIR/pre-compact-summary.py"

# Ensure log dirs exist
mkdir -p "$HOME/.claude/memory-log/archive"

if [ ! -f "$SUMMARIZER" ]; then
  echo '{"continue": true}' >&1
  echo "pre-compact-summary.py not found at $SUMMARIZER" >&2
  exit 0
fi

# Pass stdin through to python (hook data arrives on stdin)
python3 "$SUMMARIZER" < /dev/stdin

exit 0
