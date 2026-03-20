# Memory System — Deep Dive

Everything about the persistent memory architecture that doesn't fit in the README.

## Memory Architecture

Create a `~/.agent/memory/` folder with these files:

| File | What it stores | Who writes |
|------|---------------|------------|
| `MEMORY.md` | Critical rules, quick references. Always loaded. Keep under 200 lines. | Your primary AI tool |
| `context.md` | Who you are — role, skills, hardware, preferences. Your AI reads this to know you. | Your primary AI tool |
| `decisions.md` | Why you chose X over Y, with dates. You'll forget, your AI will forget. | Your primary AI tool |
| `learnings.md` | What worked, what didn't. Solutions to problems you've hit. | Your primary AI tool |
| `practices.md` | Triggered checklists (see [hooks-and-practices.md](hooks-and-practices.md)). | Your primary AI tool |
| `inbox.md` | Quick-capture scratchpad. Dump thoughts here, curate later. | Any tool or manual |
| `priorities.md` | What matters now. Task ranking. | Your primary AI tool |
| `model-routing.md` | Which model for which task. Cost strategy. | Your primary AI tool |

## Key Rules

- **Single writer for main files.** One AI tool owns the main memory files. Others can read any file but only append to `inbox.md`. This prevents quality dilution.
- **Keep MEMORY.md short** (<200 lines). Link to topic files for details. Your AI loads this every session — bloat kills quality.
- **Archive at ~100 lines.** When a file gets long, move detail to `archive/`, leave a summary + pointer. Never delete — archive preserves full resolution.
- **Pointer-based references.** Store references to docs, not full copies.
- **Save before `/clear` or session end.** Context loss is painful.
- **Attribution format:** `### [YYYY-MM-DD] Title` + `**Source:** Tool / Model`

Claude Code users: drop a `CLAUDE.md` in your project root for automatic session loading. This is your behavioural config: rules, shortcuts, and references.

## Decision Log — The Most Underrated File

`decisions.md` prevents re-researching the same choice. Format: `### [date] Chose X over Y` + reasoning. After a few weeks this becomes your highest-value file.

## Learnings Log

`learnings.md` captures solutions: problem, fix, date. When your AI hits the same issue months later, it finds this instead of rediscovering it.

## Save Policy — Light by Default, Specific When Needed

Most people do not use exact trigger phrases consistently. Design your rig around intent, not perfect wording.

**Default save trigger:** If your message suggests pausing, closing, wrapping up, handing off, compacting, or saving, the agent should create a compact recovery handoff automatically.

Examples that should all count:
- `save`, `wrap up`, `before I close this`, `let's stop there`
- `handoff`, `compact and save`, `save and clear`, `I'm done for now`

**Specific save trigger:** If you call out something as especially important, the agent should keep the normal compact handoff and add one focused section for that item.

Examples:
- `save this research properly`
- `make sure the fusion logic is preserved`
- `save the exact commands`

### What Should Save Automatically

- Goal and current task state
- Decisions made and why (brief)
- Files changed
- Commands/runs that materially changed state
- Output artifacts and their paths
- Key metrics (test status, verts/faces, timings, costs) when relevant
- Distilled subagent findings (only if they changed the recommendation)
- Next recommended step
- Blockers or deferred items

### What Should Not Save by Default

- Full conversation transcripts
- Raw tool dumps
- Long reasoning traces
- Every subagent turn verbatim
- Speculative brainstorming that did not affect next-step decisions

## Compact Handoff Format

For ordinary "save before I close this" moments, keep the handoff short enough that another agent can load it fast:

```md
# Session Handoff

- Goal:
- Status:
- What changed:
- Key decisions:
- Files touched:
- Commands / runs worth knowing:
- Artifacts / outputs:
- Subagent findings:
- Next step:
- Blockers:
```

Target: 10-20 lines, no raw dumps.

## Structured Artifact Log

If the session produced concrete outputs, save a small machine-readable file alongside the handoff.

Suggested fields:

```json
{
  "timestamp": "2026-03-11T17:42:00Z",
  "goal": "short task summary",
  "artifacts": [
    {
      "path": "results/spaceship/fusion_v1/spaceship_consensus.glb",
      "kind": "mesh",
      "source_inputs": ["..."],
      "metrics": { "vertices": 17410, "faces": 36704, "watertight": false },
      "params": { "voxel_size": 0.008, "min_votes": 2 }
    }
  ],
  "next_step": "upgrade to Open3D point-cloud fusion"
}
```

Do not load these logs by default every session. Read them only when resuming related work.

## RAG Search — Tiered Semantic Index

ChromaDB + FlashRank reranker = search your knowledge by meaning, not just keywords. Organised in tiers so searches stay fast and relevant:

| Tier | What's indexed | Searched by default? |
|------|---------------|---------------------|
| **Core** | Memory files, project docs (README/DESIGN/HANDOFF) | Yes |
| **Source** | Project source code (.py/.ts/.js), depth-limited, capped at 500 files | No — opt-in with `-c source` |
| **Session** | Conversation logs (human + assistant text only, last 30 days) | No — opt-in with `-c session` |

```bash
pip install chromadb flashrank

python memory-search.py index                          # full rebuild (all tiers)
python memory-search.py update                         # incremental (changed files only)
python memory-search.py search "centering bug"         # core tier (default)
python memory-search.py search "WebSocket client" -c source   # source code only
python memory-search.py search "that auth discussion" -c session  # session logs only
```

FlashRank is CPU-only, ~22MB, and dramatically improves result ranking.

## Cross-Agent Save Rules

This rule works well across Claude Code, Codex, Gemini CLI, editor agents, and local wrappers:

> If the user message suggests pausing, closing, saving, compacting, or handing off, create a compact recovery handoff automatically. Do not require exact trigger phrases. If the user highlights a specific item as important, add one focused section for it. Save full transcripts only when explicitly requested.

Recommended behavior split:
- **Automatic:** compact handoff, artifact metadata, short subagent findings, emergency save near context or token exhaustion
- **Manual:** full archive exports, promotion into long-term memory/docs, unusually detailed research preservation
