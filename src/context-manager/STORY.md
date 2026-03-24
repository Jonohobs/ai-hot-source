# How We Built the Context Manager
> A conversation between Jonathan Hobman and Claude Code (Opus 4.6), 2026-03-18

---

## The Problem

We were deep in a Frankenstengine session — reverse engineering game architectures, writing design docs, spawning parallel research agents — when we hit the familiar wall. Context getting heavy. `/compact` looming on the horizon.

The feeling is specific: you can sense the conversation getting sluggish, the model starting to lose threads it was holding ten messages ago. It's not a hard failure. It's a slow bleed. And the usual response — `/compact` and hope the distillation keeps what matters — always felt like a gamble.

Jonathan put it plainly: *"I feel like every session I'm either losing context or paying for it."*

The question wasn't new. But this time we stopped to actually solve it.

---

## The Iteration

### "Could we just not compact?"

The first idea was almost embarrassingly simple: skip `/compact` entirely.

Write a session summary to disk manually, clear the conversation, and inject the summary back in via the `SessionStart` hook at the top of the next session. No magic. Just structured memory.

The appeal was obvious. Full control. No lossy compression. You decide what gets saved.

The problem: it's manual. It requires Jonathan to remember to do it, to do it well, to do it consistently. That's friction that compounds over time. Good systems don't depend on the user being disciplined.

So we pushed further.

---

### "What if a daemon watched context size?"

What if something *automatically* detected when context was getting full? A background process — not an agent, just a file watcher — monitoring transcript size and triggering a summarize-and-clear cycle before things got critical.

No LLM needed for the detection. Just file size thresholds. Simple, reliable, zero cost.

This was a better shape. The summarization step could still involve an LLM, but the *trigger* was mechanical. That separation mattered: keep the cheap part cheap, spend intelligence only where it adds value.

---

### "Could an LLM summarize it?"

Here's where it got interesting. If we're going to summarize a session before archiving it, what does the summarizer look like?

Options on the table:

- **Claude subagent** — best quality, uses the `PreCompact` hook natively (`type: "agent"`). But it costs tokens. You're spending context to save context.
- **Gemini CLI** — free tier, surprisingly good quality, 60 requests per minute, 1000 per day. Calls out to Google's infrastructure but costs nothing.
- **Ollama / llama3** — fully local, zero network, zero cost. Quality is "good enough" for session summaries, which don't need to be literary.
- **No LLM at all** — structured extraction from the observation JSONL: tool call counts, files touched, key actions taken. Rough, but deterministic and free.

The debate wasn't really about quality. It was about what happens when your preferred option isn't available.

The answer: **tiered fallback**. Try Gemini (free + good). If Gemini isn't reachable, fall back to Ollama (free + local). If Ollama isn't running, fall back to structured extraction (zero cost, always available).

Best of all worlds. Graceful degradation built in by design, not bolted on after.

---

### "But where does the context go on injection?"

The summarizer problem solved, a harder question emerged: when the next session starts, what does it actually need?

Not just the session summary. The full picture:

1. The previous session's summary (what we were doing, where we left off)
2. Standing orders (security rules, workflow rules — things that must always be active)
3. CLAUDE.md reference data (key paths, project overviews)
4. Recent activity timeline (what files changed, what tools ran, when)

These were already split across different mechanisms. CLAUDE.md loads automatically on every session. The `UserPromptSubmit` hook fires before every message. The `SessionStart` hook fires once at the top of a new session.

The context manager slots into `SessionStart` naturally — inject the session buffer once, at the top, before any conversation starts. That's the right moment. Not every message (too much noise), not never (defeats the purpose).

---

### "I feel like this already exists"

Jonathan had a half-memory of someone describing a similar system. So we researched it properly.

The closest match: **MemGPT** (now Letta). It does the general concept — virtual memory paging for LLMs, moving context in and out of a fixed window. Smart work.

But our approach is different in every dimension that matters for this use case:

- **Native to Claude Code's hook system** — no external framework, no daemon process, no dependencies to manage
- **Zero mandatory dependencies** beyond Python 3
- **Free LLM summarization** — Gemini or Ollama, no API cost
- **~100 lines of code** — readable, auditable, modifiable
- **Designed for one workflow** — the specific Claude Code session loop, not a general-purpose agent architecture

MemGPT is a framework you adopt. This is a tool you own.

---

### The Standing Orders Migration

A parallel insight emerged mid-session that turned into its own small innovation.

CLAUDE.md — the global config file that defines behavior, security rules, workflow preferences — gets loaded at session start. But in long conversations, it drifts. The model holds it less firmly as context fills. Security-critical rules that were emphatic at message 1 become background noise by message 80.

The fix: move the most important rules out of CLAUDE.md and into a `UserPromptSubmit` hook. Inject them *fresh* before every single message.

This does two things:

1. Security rules become impossible to forget — they're literally prepended to every prompt
2. CLAUDE.md gets lighter — down from 137 lines to 85 — making the remaining content easier to absorb

It's a small architectural shift. But it changes the *category* of guarantee. "It was in the config file" becomes "it was injected into every message." Meaningfully harder to override, even unintentionally.

---

## The Architecture We Landed On

```
Every message:
  UserPromptSubmit → inject standing orders (security + workflow)

During session:
  PostToolUse → log observations to JSONL

Before compaction:
  PreCompact → summarize session (Gemini → Ollama → fallback)
             → archive permanently with tags
             → write session-buffer.md for next session

On new session:
  SessionStart → inject previous session summary + recent activity

On stop:
  Stop → generate basic session digest
```

Clean. Each hook does one thing. Each step is independently useful even if the others fail.

---

## What Makes It Novel

**Hook-native.** Claude Code has an event system — `SessionStart`, `PreCompact`, `PostToolUse`, `Stop`. Most people treat these as optional extensions. We treated them as the architecture. Everything else follows from that.

**Free.** Gemini CLI's free tier handles the summarization. Ollama handles the fallback. The only time you spend money is if you choose to. That matters for a system running on every session.

**Tiered quality.** Graceful degradation isn't a feature added later — it's the structure. Best available LLM wins. If nothing's available, structured extraction still gives you something useful.

**Permanent archival.** Every session summary gets tagged and stored. Search works. You can ask "what were we doing with DTR in early March" and get an answer without reconstructing it from memory.

**Standing orders pattern.** The insight that security rules belong in pre-message injection, not static config, is reusable. Any rule that must *always* be active belongs in `UserPromptSubmit`, not in a file that gets read once and diluted.

---

## The Real Lesson

The system didn't emerge from a spec document.

It emerged from a complaint ("I'm losing context every session"), a naive first idea ("just save a summary manually"), a follow-up question ("what if it was automatic?"), a debate about LLM options, a half-remembered MemGPT reference, a research tangent, and a side observation about CLAUDE.md drift that turned into its own solution.

That's how good systems get built. Not from a clean requirements list, but from following the actual problem until the shape of the solution becomes obvious.

The context manager is small — a handful of Python scripts, some shell wrappers, a JSON hook config. But it solves a real problem, it degrades gracefully, and it fits exactly into the workflow it was built for.

That's enough.

---

## Credits

- **Jonathan Hobman** ([@Jonohobs](https://github.com/Jonohobs)) — architecture, requirements, the key insight that security rules belong in hooks not config
- **AI Hot Sauce** — model routing / tiered fallback pattern
- **Claude Code** (Anthropic, Opus 4.6) — implementation, hook system knowledge, the MemGPT comparison

MIT License. 2026-03-18.
