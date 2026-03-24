# Sentinels — Trigger-Based Agent Daemon System

> Design doc. Not code yet. Target: buildable in 1-2 sessions.
> Author: Claude Code / Opus | Date: 2026-03-22

## Problem

We have agents, hooks, cron, n8n, git — but they're disconnected. No unified way to say "when X happens, spawn agent Y with context Z." We need a lightweight trigger router that ties these together without introducing a new daemon or framework.

## Name: Sentinels

A sentinel watches. When it sees something, it acts. No polling loops, no heavy process — just event-to-agent wiring.

---

## Architecture

```
                        ┌─────────────────────────────────┐
                        │        sentinels.yaml           │
                        │   (trigger → agent definitions)  │
                        └──────────────┬──────────────────┘
                                       │ read by
                                       ▼
┌──────────────┐   ┌──────────────────────────────────────────┐
│ Event Sources │   │           sentinel-dispatch.py            │
│              │   │  - Parses config                          │
│ ┌──────────┐ │   │  - Receives trigger events via stdin/arg  │
│ │ Hooks    │─┼──▶│  - Resolves agent template + context      │
│ │(PostTool)│ │   │  - Spawns claude/codex/gemini session     │
│ └──────────┘ │   │  - Logs to ~/.claude/sentinels/log/       │
│ ┌──────────┐ │   └──────────────┬───────────────────────────┘
│ │ Chokidar │─┼──▶               │
│ │(fswatch) │ │                  │ spawns
│ └──────────┘ │                  ▼
│ ┌──────────┐ │   ┌──────────────────────────────────────────┐
│ │ Git hooks│─┼──▶│         Agent Execution                   │
│ └──────────┘ │   │                                           │
│ ┌──────────┐ │   │  claude --dangerously-skip-permissions \  │
│ │ Cron     │─┼──▶│    -p "$(cat prompt.md)" \               │
│ │(schtasks)│ │   │    --model sonnet                         │
│ └──────────┘ │   │                                           │
│ ┌──────────┐ │   │  Output → ~/.claude/sentinels/results/    │
│ │ n8n      │─┼──▶│  Handoff → optional next trigger          │
│ │(webhook) │ │   └──────────────────────────────────────────┘
│ ┌──────────┐ │
│ │ Manual   │─┼──▶  sentinel-dispatch.py --trigger <name>
│ └──────────┘ │
└──────────────┘

State & Logs:
  ~/.claude/sentinels/
  ├── sentinels.yaml        ← config
  ├── prompts/              ← prompt templates (Jinja2 or simple {{var}})
  ├── results/              ← agent output artifacts
  ├── log/                  ← JSONL execution log
  └── lock/                 ← PID lockfiles (prevent duplicate runs)
```

---

## Config Format: sentinels.yaml

```yaml
# ~/.claude/sentinels/sentinels.yaml

version: 1

defaults:
  model: sonnet
  max_concurrent: 2
  timeout_minutes: 10
  output_dir: ~/.claude/sentinels/results
  log_dir: ~/.claude/sentinels/log

triggers:

  # ── File Watchers ──────────────────────────────────────────
  - name: dtr-glb-quality-check
    type: file_watch
    watch: ~/dreams-to-reality/results/**/*.glb
    events: [create, modify]
    debounce_seconds: 30
    agent:
      model: sonnet
      prompt: prompts/glb-quality-check.md
      context:
        - ~/dreams-to-reality/AGENTS.md
        - ~/dreams-to-reality/.track_results.json
      vars:
        file_path: "{{trigger.file}}"
      working_dir: ~/dreams-to-reality
    cooldown_minutes: 5

  - name: slag-heap-auto-categorize
    type: file_watch
    watch: ~/scrape-depot/slag-heap/*.md
    events: [create]
    debounce_seconds: 10
    agent:
      model: sonnet
      prompt: prompts/categorize-scrape.md
      vars:
        file_path: "{{trigger.file}}"
      working_dir: ~/scrape-depot

  - name: memory-consolidation
    type: file_watch
    watch: ~/.claude/projects/C--Users-jonat/memory/MEMORY.md
    events: [modify]
    debounce_seconds: 300
    agent:
      model: sonnet
      prompt: prompts/memory-lint.md
      context:
        - ~/.claude/projects/C--Users-jonat/memory/MEMORY.md
    cooldown_minutes: 60

  # ── Git Events ─────────────────────────────────────────────
  - name: post-push-lint
    type: git_hook
    hook: post-push
    repos:
      - ~/rabble
      - ~/dreams-to-reality
    agent:
      model: sonnet
      prompt: prompts/lint-and-test.md
      vars:
        repo: "{{trigger.repo}}"
        branch: "{{trigger.branch}}"
        commits: "{{trigger.commits}}"
      working_dir: "{{trigger.repo}}"

  - name: pre-push-secret-scan
    type: git_hook
    hook: pre-push
    repos: ["*"]
    agent:
      model: haiku
      prompt: prompts/secret-scan.md
      vars:
        repo: "{{trigger.repo}}"
        diff: "{{trigger.diff}}"
      blocking: true  # blocks push if agent returns non-zero

  # ── Scheduled (Cron) ──────────────────────────────────────
  - name: morning-project-status
    type: cron
    schedule: "0 9 * * *"  # daily 9am
    agent:
      model: sonnet
      prompt: prompts/project-status.md
      context:
        - ~/.claude/projects/C--Users-jonat/memory/MEMORY.md
      output: results/daily-status-{{date}}.md

  - name: weekly-memory-digest
    type: cron
    schedule: "0 10 * * 0"  # Sunday 10am
    agent:
      model: opus
      prompt: prompts/memory-digest.md
      context:
        - ~/.claude/projects/C--Users-jonat/memory/MEMORY.md
      output: results/weekly-digest-{{date}}.md

  # ── n8n Webhooks ───────────────────────────────────────────
  - name: github-issue-triage
    type: webhook
    endpoint: /sentinel/github-issue
    secret_env: SENTINEL_WEBHOOK_SECRET
    agent:
      model: sonnet
      prompt: prompts/issue-triage.md
      vars:
        title: "{{trigger.body.issue.title}}"
        body: "{{trigger.body.issue.body}}"
        repo: "{{trigger.body.repository.full_name}}"

  # ── Manual ─────────────────────────────────────────────────
  - name: full-codebase-review
    type: manual
    agent:
      model: opus
      prompt: prompts/codebase-review.md
      vars:
        target: "{{args.target}}"
      timeout_minutes: 30
      working_dir: "{{args.target}}"

  - name: research-topic
    type: manual
    agent:
      model: sonnet
      prompt: prompts/research-fan-out.md
      vars:
        topic: "{{args.topic}}"
      output: results/research-{{args.topic}}-{{date}}.md
```

---

## Prompt Templates

Simple `{{var}}` interpolation. No Jinja2 dependency — just Python `str.replace()` or `string.Template`.

Example `prompts/glb-quality-check.md`:
```markdown
You are a 3D asset quality checker.

Analyze the GLB file at: {{file_path}}

Check:
1. File size (flag if >50MB)
2. Triangle count (flag if >500K)
3. Texture resolution (flag if >4096px)
4. Missing normals or UVs

Write a quality report to the results directory.
If quality is poor, add a note to the handoffs folder.
```

---

## Component Breakdown

### 1. sentinel-dispatch.py (~150 lines)
The core router. Single Python script, no dependencies beyond stdlib + PyYAML.

```
sentinel-dispatch.py --trigger <name> [--var key=value ...]
sentinel-dispatch.py --event <json>   # piped from hooks/watchers
```

Responsibilities:
- Load `sentinels.yaml`
- Match trigger name or event to config
- Interpolate prompt template with variables
- Check lockfile (prevent duplicate runs of same trigger)
- Spawn agent process (background, detached)
- Log execution to JSONL

### 2. sentinel-watch.py (~80 lines)
File watcher using `watchdog` (pip package, cross-platform). Runs as a background process.

```
sentinel-watch.py  # reads sentinels.yaml, watches all file_watch triggers
```

On match: calls `sentinel-dispatch.py --trigger <name> --var file=<path>`.

**Alternative (no daemon):** Skip this entirely. Use existing PostToolUse hooks to detect file creation during Claude Code sessions. For outside-session file changes, use Windows Task Scheduler to run a quick check every 5 minutes. No persistent watcher needed.

### 3. Git hook installer (~30 lines)
Shell script that symlinks into `.git/hooks/` for configured repos.

```bash
sentinel-install-hooks.sh  # reads sentinels.yaml, installs git hooks
```

Each git hook calls: `sentinel-dispatch.py --trigger <name> --var repo=$PWD --var branch=$(git branch --show-current)`

### 4. Cron installer (~20 lines)
Reads cron triggers from config, writes Windows Task Scheduler entries (or cron on Linux/Hetzner).

```bash
sentinel-install-cron.sh
```

### 5. n8n webhook bridge
An n8n workflow that:
1. Receives webhook (GitHub, custom, etc.)
2. POSTs to local machine via Tailscale or SSH tunnel
3. Local receiver calls `sentinel-dispatch.py --event <json>`

No new code on n8n side — just a webhook → HTTP request node workflow.

### 6. Hook integration (0 new files)
Add one line to existing `observation-logger.sh` or create a thin wrapper:

```bash
# In PostToolUse hook, after logging:
python3 ~/.claude/sentinels/sentinel-dispatch.py --event "$HOOK_INPUT" 2>/dev/null &
```

This makes every Claude Code tool use a potential trigger event. The dispatcher checks if any trigger matches and ignores 99% of them (fast path: ~5ms).

---

## Execution Model

### Agent Spawning

```python
import subprocess

def spawn_agent(config, prompt_text, working_dir):
    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "-p", prompt_text,
        "--model", config.get("model", "sonnet"),
        "--output-format", "text"
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=working_dir,
        stdout=open(output_path, "w"),
        stderr=open(log_path, "a"),
        start_new_session=True  # detach from parent
    )
    return proc.pid
```

For non-Claude agents (Codex, Gemini):
```python
if agent_type == "codex":
    cmd = ["codex", "-q", prompt_text]
elif agent_type == "gemini":
    cmd = ["gemini", "-p", prompt_text]
```

### Concurrency Control

- Global `max_concurrent` (default: 2) — check active PIDs in `lock/` before spawning
- Per-trigger `cooldown_minutes` — skip if last run was too recent
- Lockfile per trigger name: `lock/{trigger_name}.pid`
- Stale lock detection: if PID doesn't exist, remove lockfile

### Logging

JSONL to `log/sentinel-YYYY-MM-DD.jsonl`:
```json
{
  "ts": "2026-03-22T09:00:01Z",
  "trigger": "morning-project-status",
  "type": "cron",
  "agent_model": "sonnet",
  "pid": 12345,
  "status": "spawned",
  "prompt_hash": "abc123"
}
```

Completion logged by wrapper that waits for PID:
```json
{
  "ts": "2026-03-22T09:02:15Z",
  "trigger": "morning-project-status",
  "status": "completed",
  "pid": 12345,
  "exit_code": 0,
  "duration_seconds": 134,
  "output_file": "results/daily-status-2026-03-22.md"
}
```

---

## What We Leverage vs What's New

### Existing (no work needed)
| Component | Status |
|-----------|--------|
| Claude Code hooks (Pre/PostToolUse) | Active, 4 hooks running |
| `observation-logger.sh` | Active, logs all tool use |
| n8n on Hetzner | Running, webhook-capable |
| Git installed on all repos | Ready |
| `claude` CLI with `--dangerously-skip-permissions` | Available |
| DTR swarm board patterns | Reference for task schema |
| Windows Task Scheduler | Available for cron |
| Tailscale | Installed (Hetzner ↔ local) |

### New (must build)
| Component | Effort | Priority |
|-----------|--------|----------|
| `sentinel-dispatch.py` | 2-3 hours | P0 — core router |
| `sentinels.yaml` config | 30 min | P0 — with 3-4 real triggers |
| 3-4 prompt templates | 1 hour | P0 — GLB check, lint, status |
| `sentinel-watch.py` | 1-2 hours | P1 — file watcher |
| Git hook installer | 30 min | P1 — shell script |
| Cron installer | 30 min | P2 — Task Scheduler entries |
| n8n webhook workflow | 1 hour | P2 — optional |
| Hook integration (1 line) | 5 min | P0 — wire into existing hooks |

---

## Implementation Plan

### Session 1: Core (3-4 hours)

1. **Create directory structure**
   ```
   ~/.claude/sentinels/
   ├── sentinel-dispatch.py
   ├── sentinels.yaml
   ├── prompts/
   │   ├── glb-quality-check.md
   │   ├── lint-and-test.md
   │   └── project-status.md
   ├── results/
   ├── log/
   └── lock/
   ```

2. **Build `sentinel-dispatch.py`** — the core router
   - YAML config parser
   - Template interpolation
   - Agent spawner (claude CLI)
   - Lockfile management
   - JSONL logging
   - CLI: `--trigger <name>`, `--event <json>`, `--list`, `--status`

3. **Write 3 prompt templates** — GLB quality, lint-and-test, project status

4. **Wire into hooks** — add sentinel dispatch call to `observation-logger.sh`

5. **Test manually** — `sentinel-dispatch.py --trigger morning-project-status`

### Session 2: Automation (2-3 hours)

6. **Build `sentinel-watch.py`** — watchdog-based file watcher, or poll-based fallback

7. **Git hook installer** — read YAML, symlink hooks into repos

8. **Cron installer** — Windows Task Scheduler for scheduled triggers

9. **n8n webhook bridge** — if time permits

10. **Dashboard** — `sentinel-dispatch.py --status` shows last 20 runs, active agents, next scheduled

---

## Design Decisions

### Why not a persistent daemon?
Daemons crash, leak memory, need restarts. Instead:
- File watchers: lightweight `watchdog` process OR 5-min poll via Task Scheduler
- Hooks: fire-and-forget from existing hook pipeline
- Cron: OS-native scheduling
- The dispatcher itself runs, spawns, exits. Stateless.

### Why YAML not JSON?
Comments. Triggers need inline documentation. YAML supports comments, JSON doesn't.

### Why not use Claude Code's native CronCreate?
CronCreate runs inside a Claude Code session. Sentinels should work without an active session — that's the whole point. OS-level cron/Task Scheduler is more reliable.

### Why single dispatch script, not per-trigger scripts?
One config file to rule them all. Adding a new trigger = add YAML block + prompt template. No new scripts, no new wiring.

### Agent model selection
- **haiku**: fast checks (secret scan, simple lint) — cheap, <10s
- **sonnet**: most triggers — good balance of speed/quality
- **opus**: weekly digests, architecture reviews — quality matters, cost acceptable

### Security considerations
- Agents spawned with `--dangerously-skip-permissions` — contained by working_dir and prompt scope
- Webhook secret validation for n8n triggers
- No credential files read by agents (enforced by prompt + pre-tool-guard hook)
- Lockfiles prevent runaway duplicate spawns
- `max_concurrent` hard cap prevents cost explosion

---

## Future Extensions (not now)

- **Chaining**: trigger A's output → trigger B's input (DAG-style pipelines)
- **Agent teams**: spawn multiple agents for one trigger (fan-out)
- **Hetzner remote sentinels**: same config, runs on VPS for always-on triggers
- **Notification**: Slack/Discord/email on sentinel completion or failure
- **Cost tracking**: parse Claude CLI output for token usage, aggregate by trigger
- **Web dashboard**: simple HTML page showing sentinel status (read from JSONL)

---

## CLI Interface

```bash
# Run a trigger manually
sentinel --trigger morning-project-status

# Run with custom vars
sentinel --trigger full-codebase-review --var target=~/rabble

# List all triggers
sentinel --list

# Show recent runs
sentinel --status

# Show runs for a specific trigger
sentinel --status --trigger dtr-glb-quality-check

# Install git hooks for configured repos
sentinel --install-git-hooks

# Install cron/scheduled tasks
sentinel --install-cron

# Start file watcher (foreground, or background with &)
sentinel --watch

# Dry run — show what would happen without spawning
sentinel --trigger morning-project-status --dry-run
```

Alias in `.bashrc`: `alias sentinel='python3 ~/.claude/sentinels/sentinel-dispatch.py'`

---

## Success Metrics

| Metric | Target | How to measure |
|--------|--------|----------------|
| Triggers configured | 5+ | Count in sentinels.yaml |
| Auto-runs per day | 3-10 | JSONL log count |
| False triggers | <1/day | Manual review of log |
| Agent spawn time | <3s | Log timestamps |
| Config change to live | <1 min | Edit YAML, done |
| Maintenance burden | ~0 | No daemon to babysit |

---

## Comparison with Always-On Agents

Sentinels complement, not replace, the Always-On Agent plan:

| Aspect | Always-On Agents | Sentinels |
|--------|-----------------|-----------|
| Location | Hetzner VPS | Local machine |
| Trigger | Poll-based (60s) | Event-driven |
| Duration | Long-running containers | Short-lived sessions |
| Cost | ~$17-24/mo | ~$0 (uses existing infra) |
| Use case | Background R&D, pipeline work | Reactive: file changes, git events |
| Dependency | Hetzner access (blocked) | Nothing — works now |

**Key advantage of Sentinels**: buildable today with zero new infrastructure. The Always-On system needs Hetzner access (currently blocked). Sentinels use what's already running.
