#!/usr/bin/env bash
# Context Manager for Claude Code
# Stop hook — generates a compact session digest from today's observations.
# Appends a structured summary to session-log.md for future session injection.
#
# Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
# License: MIT | Repository: https://github.com/Jonohobs/ai-hot-sauce
# Created: 2026-03-18

LOG_DIR="$HOME/.claude/memory-log"
TODAY=$(date +%Y-%m-%d)
OBS_FILE="$LOG_DIR/observations-${TODAY}.jsonl"
SESSION_LOG="$LOG_DIR/session-log.md"

# If no observations today, skip silently
if [ ! -f "$OBS_FILE" ] || [ ! -s "$OBS_FILE" ]; then
  echo '{"continue": true}'
  exit 0
fi

# Generate compact digest from observations
python3 "$HOME/.claude/hooks/digest-gen.py" "$OBS_FILE" "$SESSION_LOG" "$TODAY" 2>/dev/null

echo '{"continue": true}'
