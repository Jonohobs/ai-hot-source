#!/usr/bin/env python3
"""
Context Manager for Claude Code
Session summarization, archival, and context injection.

Observation logger — reads PostToolUse hook data from stdin,
extracts a useful summary per tool type, and appends to the daily JSONL log.

Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
License: MIT
Repository: https://github.com/Jonohobs/ai-hot-sauce
Created: 2026-03-18
"""

import json
import sys
from datetime import datetime

log_file = sys.argv[1]

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "unknown")
params = data.get("tool_params", {})
ts = datetime.now().strftime("%H:%M:%S")

# Extract useful summary based on tool type
summary = ""
if tool == "Bash":
    summary = (params.get("command") or "")[:200]
elif tool in ("Read", "Write", "Edit"):
    summary = params.get("file_path", "")
elif tool == "Glob":
    summary = params.get("pattern", "")
elif tool == "Grep":
    summary = (params.get("pattern", "") + " in " + params.get("path", "."))[:200]
elif tool == "Agent":
    summary = params.get("description", "")
elif tool == "WebSearch":
    summary = params.get("query", "")
elif tool == "WebFetch":
    summary = (params.get("url") or "")[:200]
else:
    summary = str(params)[:200]

obs = {"time": ts, "tool": tool, "summary": summary}

with open(log_file, "a") as f:
    f.write(json.dumps(obs) + "\n")
