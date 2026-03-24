---
name: context-manager
description: Session summarization, archival, and context injection for Claude Code. Use when discussing context management, session continuity, or memory architecture.
trigger: context management, session summary, compact alternatives, session continuity, memory architecture
---

# Context Manager Skill

This skill provides a hook-based context management pipeline for Claude Code.

## Architecture

```
PreCompact  →  summarize session (Gemini CLI → Ollama → structured fallback)  →  archive
SessionStart  →  inject previous session summary into context
PostToolUse  →  log observations to daily JSONL
Stop  →  generate compact session digest → append to session-log.md
```

## Key Files

| File | Path |
|------|------|
| Main summarizer | `~/.claude/hooks/pre-compact-summary.py` |
| Summarizer wrapper | `~/.claude/hooks/pre-compact-summary.sh` |
| Session injection | `~/.claude/hooks/activity-timeline.sh` |
| Observation logger | `~/.claude/hooks/observation-logger.sh` / `obs-log.py` |
| Digest generator | `~/.claude/hooks/session-digest.sh` / `digest-gen.py` |
| Observation logs | `~/.claude/memory-log/observations-YYYY-MM-DD.jsonl` |
| Session log | `~/.claude/memory-log/session-log.md` |
| Session buffer | `~/.claude/memory-log/session-buffer.md` |
| Archive | `~/.claude/memory-log/archive/` |

## Summary Quality Tiers

1. **Gemini CLI** — free, semantic, best quality
2. **Ollama llama3** — local, free, zero network
3. **Structured fallback** — pure Python, no LLM, tool counts + files touched

## Usage

The system runs automatically via hooks. No manual intervention needed.

To verify it's working:
1. Run `/compact` (or wait for auto-compact)
2. Check `~/.claude/memory-log/archive/` for the saved summary
3. Start a new session — previous summary will be injected automatically

To search archived sessions:
```bash
grep -r "#feature-name" ~/.claude/memory-log/archive/
```

## Installation

See `README.md` in `~/ai-hot-sauce/src/context-manager/` for full installation steps.

Quick install:
```bash
cp ~/ai-hot-sauce/src/context-manager/*.sh ~/.claude/hooks/
cp ~/ai-hot-sauce/src/context-manager/*.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
mkdir -p ~/.claude/memory-log/archive
```
Then merge `settings-hooks.json` into `~/.claude/settings.json`.

## Credits

Jonohobs + AI Hot Sauce + Claude Code (Anthropic) — 2026-03-18. MIT License.
Repository: https://github.com/Jonohobs/ai-hot-sauce
