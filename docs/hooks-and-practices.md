# Hooks & Practices

Hooks are scripts that run before/after your AI does things. Claude Code has native hook support. For other tools, you can script similar behaviour.

## Hooks Worth Having

| Hook | When it fires | What it does |
|------|--------------|-------------|
| **Session start** | New conversation | Loads memory, shows inbox, surfaces what changed since last session |
| **Pre-tool guard** | Before file edits | Pattern-matches for known gotchas (CSS centering, SDK bias, dangerous commands) and injects the relevant practice checklist |
| **Post-tool memory** | After file writes | Auto-indexes new/changed files into your search system |
| **Pre-compact** | Before context compression | Saves conversation state (decisions, learnings, task progress) to memory files |
| **Audit log** | After bash commands | Logs what commands your AI ran (security + debugging) |
| **Pause-save** | User signals pause/close/save | Writes compact handoff + artifact metadata, and adds one focused section if the user flagged something important |

Pre-tool hooks pattern-match tool calls (e.g. CSS edits -> centering checklist, `git push` -> verify checklist) and inject the relevant practice. No match = no overhead. Note: hook injections add tokens — use lean mode (see Session Modes) for simple tasks.

## Session Modes

Not every task needs your full rig context. Session modes let you control how much gets loaded.

| Mode | What loads | Good for |
|------|-----------|----------|
| **Normal** | Everything — practices, inbox, memory reading, full hooks | Regular development work |
| **Lean** | Just your config rules. No practices, no inbox, no memory injection. | Quick one-off tasks, simple fixes |
| **Clean** | Bare skeleton. No personal context. Just file structure pointers. | Sharing the rig, fresh starts, onboarding |

Say "lean mode" or "clean mode", your AI writes it to `~/.agent/state/session-mode`, then `/clear`. The session-start hook adjusts what gets loaded. Your full startup context is ~3-5K tokens — lean mode gives that back on simple tasks.

## Practices — Triggered Checklists

Practices are checklists that fire when specific conditions are met. They catch mistakes before they happen.

| ID | Name | When it fires | What it checks |
|----|------|--------------|----------------|
| P000 | CSS Centering | Writing layout classes in frontend files | mx-auto needs explicit width, copy full class sets from reference |
| P001 | Build Rails First | Starting a new feature | Test after each layer, don't add complexity before the foundation works |
| P002 | Test Harness First | Creating a new project | Install test framework, write 1 trivial test before any real code |
| P003 | Verify Before Done | About to claim something is complete | Run tests, lint, manual check. Prove it works. |
| P004 | Measure First | Performance optimisation | Profile before changing. Measure the delta. Gut feelings are hypotheses. |
| P005 | Session Start | New session | Load context, check inbox, note where you left off |
| P006 | Session End | Wrapping up or high context % | Save decisions, learnings, task state to memory |
| P007 | Track Measure Optimise | Every task | Baseline, work, measure, learn |
| P008 | OSS Security | Ingesting any GitHub/OSS code | Read-only first, verify legitimacy, scan for injection, no blind execution |

These live in `~/.agent/memory/practices.md`. Your hooks can pattern-match tool calls and inject the relevant checklist before execution.

## Dual-Agent Pattern

If you're running two AI tools (e.g. Claude Code + Codex), use them together instead of separately:

1. Primary agent implements.
2. Secondary agent reviews only (bugs, regressions, missing tests).
3. Resolve findings once.
4. When agents disagree, trust runnable evidence (tests/logs).

Switch roles daily if you want freshness.

### Fast Handoff Template

For quick tasks (<= 1 hour), use this to keep agents aligned:

```md
## Assignment
- Primary agent:
- Secondary agent:
- Goal:

## Changes
- Files touched:
- What changed:

## Verify
- Commands:
- Result: `pass` | `fail`

## Review
- Top findings (max 3):
- Fixes applied:

## Ship
- Status: `ready` | `needs work` | `blocked`
- Next step:
```

## Rig Upgrade Capture Rule

If a session discovers a reusable improvement to agent behavior, memory hygiene, hooks, handoffs, routing, review workflow, or safety policy, treat it as a Hot Source upgrade candidate.

Default rule:
- Add the improvement to this repo when it is generalisable beyond one project
- Keep the write-up short and operational
- Prefer updating existing guidance over scattering new files everywhere
- If the idea is still unproven, mark it clearly as experimental

Good candidates:
- Better save / handoff triggers
- New hook ideas that reduce repeated mistakes
- Better subagent coordination rules
- Lightweight logging patterns that improve recovery
- Safety or review practices that clearly prevented risk

Not good candidates:
- One-off project trivia
- Long transcripts
- Preferences that only matter in a single repo
