#!/usr/bin/env bash
# Context Manager for Claude Code
# PostToolUse hook — logs tool usage to a daily JSONL observation file.
# Local-only, no dependencies beyond python3 standard library.
#
# Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
# License: MIT | Repository: https://github.com/Jonohobs/ai-hot-sauce
# Created: 2026-03-18

LOG_DIR="$HOME/.claude/memory-log"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/observations-${TODAY}.jsonl"

mkdir -p "$LOG_DIR"

# Read hook input from stdin and pass to python logger
python3 "$HOME/.claude/hooks/obs-log.py" "$LOG_FILE" 2>/dev/null

# Always pass through — never block tool execution
echo '{"continue": true}'
