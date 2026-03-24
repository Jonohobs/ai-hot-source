#!/usr/bin/env python3
"""
Context Manager for Claude Code
Session summarization, archival, and context injection.

Session digest generator — reads today's observation JSONL and appends
a compact structured summary to session-log.md.
Called by the Stop hook (session-digest.sh).

Copyright (c) 2026 Jonathan Hobman (Jonohobs), AI Hot Sauce, Claude Code (Anthropic)
License: MIT
Repository: https://github.com/Jonohobs/ai-hot-sauce
Created: 2026-03-18
"""

import json
import sys
from collections import Counter

obs_file = sys.argv[1]
session_log = sys.argv[2]
today = sys.argv[3]

lines = []
with open(obs_file, "r") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                lines.append(json.loads(line))
            except Exception:
                pass

if not lines:
    sys.exit(0)

# Count tools used
tools = Counter(o.get("tool", "?") for o in lines)
tool_summary = ", ".join(f"{t}({c})" for t, c in tools.most_common(8))

# Get unique files touched
files = set()
for o in lines:
    s = o.get("summary", "")
    if "/" in s or "\\" in s:
        parts = s.replace("\\", "/").split("/")
        fname = parts[-1][:40] if parts[-1] else ""
        if fname and len(fname) > 2:
            files.add(fname)

files_str = ", ".join(sorted(files)[:10]) if files else "n/a"

# Time range
first = lines[0].get("time", "?")
last = lines[-1].get("time", "?")

# Key actions (write-like tools)
actions = [
    o
    for o in lines
    if o.get("tool") in ("Bash", "Write", "Edit", "Agent", "WebSearch", "WebFetch")
]
action_lines = []
for a in actions[-8:]:
    s = a.get("summary", "")[:80]
    if s:
        action_lines.append(f"  - {a.get('tool')}: {s}")

digest = f"### {today} {first}\u2013{last} ({len(lines)} tool uses)\n"
digest += f"**Tools:** {tool_summary}\n"
digest += f"**Files:** {files_str}\n"
if action_lines:
    digest += "**Key actions:**\n" + "\n".join(action_lines) + "\n"

with open(session_log, "a") as f:
    f.write(digest + "\n")

print(f"Session digest: {len(lines)} observations", file=sys.stderr)
