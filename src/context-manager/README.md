# Context Manager for Claude Code

> Automatic session summarization, archival, and context injection for Claude Code.
> No more lossy `/compact`. Sessions are summarized before compaction, archived permanently, and injected into the next session automatically.

**Created by:** [Jonohobs](https://github.com/Jonohobs) + [AI Hot Sauce](https://github.com/Jonohobs/ai-hot-sauce) + Claude Code (Anthropic)
**Date:** 2026-03-18
**License:** MIT

## How It Works

```
Session in progress
    ↓ (context getting full)
PreCompact hook fires
    ↓
Summarizer runs (Gemini CLI → Ollama → fallback)
    ↓
Summary saved to session-buffer.md + archive/
    ↓
User does /clear
    ↓
SessionStart hook injects previous session summary
    ↓
Fresh context with full continuity
```

## Components

| Component | What it does |
|-----------|-------------|
| `pre-compact-summary.py` | Reads observation logs, generates rich session summary via LLM (Gemini/Ollama) or structured fallback |
| `pre-compact-summary.sh` | Bash wrapper for the hook system |
| `activity-timeline.sh` | SessionStart hook — injects previous session summary + recent activity |
| `observation-logger.sh` | PostToolUse hook — logs tool usage to daily JSONL |
| `session-digest.sh` | Stop hook — generates compact session digest |
| `obs-log.py` | Python core for observation logging |
| `digest-gen.py` | Python core for digest generation |
| `settings-hooks.json` | Hook configuration to merge into your settings.json |

## Installation

1. Copy hook scripts to `~/.claude/hooks/`:
   ```bash
   cp pre-compact-summary.py ~/.claude/hooks/
   cp pre-compact-summary.sh ~/.claude/hooks/
   cp activity-timeline.sh ~/.claude/hooks/
   cp observation-logger.sh ~/.claude/hooks/
   cp session-digest.sh ~/.claude/hooks/
   cp obs-log.py ~/.claude/hooks/
   cp digest-gen.py ~/.claude/hooks/
   chmod +x ~/.claude/hooks/*.sh
   ```
2. Merge `settings-hooks.json` into your `~/.claude/settings.json`
3. Ensure either `gemini` CLI or `ollama` is installed (both are free)
4. Create the log directory: `mkdir -p ~/.claude/memory-log/archive`

## Requirements

- Claude Code
- Python 3 (standard library only)
- One of: Gemini CLI (free), Ollama with llama3 (free), or neither (uses structured fallback)

## Architecture

The system uses Claude Code's hook events:
- **PreCompact** — fires before context compaction, generates and archives session summary
- **SessionStart** — fires on new session or /clear, injects previous session's summary
- **PostToolUse** — logs observations to daily JSONL file
- **Stop** — generates compact session digest appended to session-log.md

### Summary Quality Tiers

1. **Gemini CLI** (best free option) — semantic understanding of what was accomplished
2. **Ollama llama3** (local, free) — good quality, zero network
3. **Structured fallback** (no LLM) — tool counts, files touched, key actions from JSONL

### Archive Format

Each session is archived permanently:
```
~/.claude/memory-log/archive/
├── 2026-03-18-14-30-session.md
├── 2026-03-18-16-45-session.md
└── ...
```

Sessions include tags (#project-name, #feature, #bugfix) for searchability.

## The Problem This Solves

Claude Code's `/compact` is lossy — it compresses the conversation but loses nuance, decisions, and context. This system:
- Captures a high-quality summary BEFORE compaction
- Archives it permanently (never lose session history)
- Injects it into the next session (seamless continuity)
- Uses free LLMs (zero API cost)
- Tags sessions for searchability

## Credits

This system emerged from a session on context engineering for Claude Code, exploring how to maintain continuity across sessions without relying on lossy compaction.

- **Jonathan Hobman** ([@Jonohobs](https://github.com/Jonohobs)) — architecture, requirements, testing
- **AI Hot Sauce** — model routing patterns, quality tier fallback
- **Claude Code** (Anthropic, Claude Sonnet 4.6) — implementation, hook system design

## License

MIT — use it, fork it, improve it.
