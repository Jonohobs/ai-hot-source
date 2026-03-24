#!/usr/bin/env bash
# Context Manager for Claude Code
# SessionStart hook — injects previous session summary + recent activity timeline.
# Reads session-buffer.md (last PreCompact summary) and session-log.md (digest history).
#
# Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
# License: MIT | Repository: https://github.com/Jonohobs/ai-hot-sauce
# Created: 2026-03-18

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.claude/memory-log"
BUFFER_FILE="$LOG_DIR/session-buffer.md"
SESSION_LOG="$LOG_DIR/session-log.md"

# ---------------------------------------------------------------------------
# Attention Residuals mode — relevance-scored context injection
# When ATTENTION_RESIDUALS=true, the scorer replaces default injection.
# When disabled/unset, existing behavior is preserved (backward compatible).
# ---------------------------------------------------------------------------
if [ "${ATTENTION_RESIDUALS:-}" = "true" ] || [ "${ATTENTION_RESIDUALS:-}" = "1" ]; then
  # Run the attention residuals scorer.
  # Pass session-buffer content as signal (scorer also reads it as fallback).
  SCORED_CONTEXT=""
  if [ -f "$BUFFER_FILE" ] && [ -s "$BUFFER_FILE" ]; then
    SCORED_CONTEXT=$(cat "$BUFFER_FILE" | ATTENTION_RESIDUALS=true python3 "$SCRIPT_DIR/attention-residuals.py" 2>/dev/null)
  else
    SCORED_CONTEXT=$(echo "" | ATTENTION_RESIDUALS=true python3 "$SCRIPT_DIR/attention-residuals.py" 2>/dev/null)
  fi

  if [ -n "$SCORED_CONTEXT" ]; then
    # Clear buffer after successful scoring so it's not injected twice
    > "$BUFFER_FILE" 2>/dev/null
    python3 -c "
import json, sys
ctx = sys.stdin.read().strip()
if ctx:
    print(json.dumps({'additionalContext': ctx}))
else:
    print(json.dumps({'continue': True}))
" <<< "$SCORED_CONTEXT" 2>/dev/null
    exit 0
  fi
  # If scorer failed or returned empty, fall through to default behavior
fi

# ---------------------------------------------------------------------------
# Default behavior — inject session buffer + recent log equally (no scoring)
# ---------------------------------------------------------------------------

# Build context from available sources
CONTEXT=""

# Primary: inject last PreCompact summary if present
if [ -f "$BUFFER_FILE" ] && [ -s "$BUFFER_FILE" ]; then
  BUFFER=$(cat "$BUFFER_FILE")
  CONTEXT="<previous-session-summary>\n$BUFFER\n</previous-session-summary>\n\n"
  # Clear buffer after reading so it's not injected twice
  > "$BUFFER_FILE"
fi

# Secondary: inject recent session digests (last ~30 lines)
if [ -f "$SESSION_LOG" ] && [ -s "$SESSION_LOG" ]; then
  RECENT=$(tail -30 "$SESSION_LOG" 2>/dev/null)
  if [ -n "$RECENT" ]; then
    CONTEXT="${CONTEXT}<recent-activity>\n$RECENT\n</recent-activity>"
  fi
fi

if [ -n "$CONTEXT" ]; then
  python3 -c "
import json, sys
ctx = sys.stdin.read().strip()
if ctx:
    print(json.dumps({'additionalContext': ctx}))
else:
    print(json.dumps({'continue': True}))
" <<< "$CONTEXT" 2>/dev/null
else
  echo '{"continue": true}'
fi
