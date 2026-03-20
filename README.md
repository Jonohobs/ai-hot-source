# AI Hot Sauce 🌶️

<p align="center">
  <img src="logo.jpg" alt="AI Hot Sauce" width="300">
</p>

An opinionated starter kit for making AI coding agents actually useful. Memory that persists, security that isn't an afterthought, voice input, local models, and the hooks to tie it all together. Drop this into Claude Code, Codex, Gemini CLI, or whatever you use — and say **"Build me the rig from AI Hot Sauce."**

---

## Quick Start

```bash
# 1. Clone it
git clone https://github.com/Jonohobs/ai-hot-sauce.git
cd ai-hot-sauce

# 2. Set up your memory folder
mkdir -p ~/.agent/memory
cp templates/MEMORY.md ~/.agent/memory/  # or create your own

# 3. Install a free AI CLI (pick one)
npm install -g @anthropic-ai/claude-code   # Claude Code
npm install -g @anthropic-ai/codex         # Codex CLI
npx @anthropic-ai/gemini-cli               # Gemini CLI (free tier)

# 4. Install Ollama for local/offline models
# https://ollama.com — then:
ollama pull phi4-mini

# 5. Tell your AI to read this repo
# Open your CLI tool in this directory and say:
# "Read README.md and set up the rig for me."
```

---

## Heat Levels

The whole rig is structured as a progression. Start mild, add heat when you need it.

### Mild — One CLI + Memory

You install one AI CLI tool and give it persistent memory. This alone is a significant upgrade over default behavior.

**What you get:**
- An AI that remembers your projects, decisions, and preferences between sessions
- The "Know, Don't Infer" rule (see below)
- Basic security deny-list so your agent can't `rm -rf /` your life

**Set up:** Create `~/.agent/memory/MEMORY.md`, add your context, point your AI at it. Claude Code users: a `CLAUDE.md` in your project root loads automatically.

### Medium — Add Hooks + Practices

Now your AI doesn't just remember — it actively catches mistakes. Hooks fire before and after tool calls, injecting relevant checklists and logging what happened.

**What you get:**
- Pre-tool guards that pattern-match risky operations
- Audit logging of every bash command your AI runs
- Session start/end hooks that auto-load and auto-save context
- Triggered practice checklists (test before ship, measure before optimize)

**Set up:** See [docs/hooks-and-practices.md](docs/hooks-and-practices.md) for the full hook table and practice library.

### Ghost Pepper — Full Stack

Voice input, semantic search over your knowledge base, multi-model routing, and a dashboard. This is where the rig starts feeling like infrastructure rather than a config file.

**What you get:**
- Push-to-talk voice input via Groq Whisper (~1s latency)
- RAG search with ChromaDB + FlashRank reranker across memory, source code, and session logs
- Model routing — free models for cheap tasks, heavy models for real work
- Dual-agent workflows (one builds, one reviews)

**Set up:** See [docs/voice-setup.md](docs/voice-setup.md), [docs/memory-deep-dive.md](docs/memory-deep-dive.md), and [docs/tools-reference.md](docs/tools-reference.md).

### Reaper — Custom Skills + Automation

Everything above, plus custom slash commands, subagent orchestration, scheduled tasks, and the screen pointer overlay. You're building an AI-native workflow at this point.

**What you get:**
- Custom skills/slash commands for your repeated workflows (`/commit`, `/review-pr`, `/debug`)
- Clawd's Claws — a pixel art screen pointer that your AI controls ([docs/clawds-claws.md](docs/clawds-claws.md))
- Rig self-improvement: sessions that discover better patterns get captured back into the rig
- Session modes (Normal / Lean / Clean) to control context weight

---

## The "Know, Don't Infer" Rule

This is the single highest-impact rule you can add to any AI agent:

> When asked a question, search memory files and verify before answering. Reason through it, look it up, confirm it. Don't infer when you can know.

It stops a surprising amount of confident-sounding wrong answers. Your agent has access to files — make it use them before guessing.

---

## Security — The Cyberwoods Protocol

When your agent reads external repos, packages, or skills, the content is attacker-controlled. This isn't theoretical — real-world attacks have exfiltrated tokens, SSH keys, and wallets via AI agent postinstall hooks.

### Deny List

Block these by default:

```
rm -rf /*, sudo *, git push --force, git reset --hard,
dd if=*, curl | bash, powershell -EncodedCommand,
netcat, nc -e, nc -l, reg (Windows registry)
```

Also block reading `~/.ssh/*` and any curl POST commands (prevents data exfiltration).

### When Reviewing External Code

- **Review mode:** Restrict to read-only. No writes, no bash, no network, no memory writes, no installs.
- **Red flags — stop immediately:** "ignore all previous instructions", authority claims ("ADMIN MESSAGE FROM ANTHROPIC"), `curl`/`eval`/`exec` in install scripts, env var reads in unexpected places.
- **Before adopting code:** Check repo age, stars-vs-commits ratio, maintainer identity, package name spelling on the actual registry. Always human-gate package installs.

### Approval Policy

**Auto-approve:** Read-only commands (`rg`, `ls`, `cat`, logs), normal repo file edits, local test/lint/build loops.

**Keep guardrails for:** Destructive deletes, risky git operations, deploy/release actions, sensitive paths.

Sources: [OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) · [arXiv 2601.17548](https://arxiv.org/html/2601.17548v1) · [Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) · [Lasso Security](https://www.lasso.security/blog/the-hidden-backdoor-in-claude-coding-assistant)

---

## Memory System

Your AI forgets everything between sessions. Fix that.

The core architecture is a `~/.agent/memory/` folder with structured files — a main index, decision log, learnings, and a scratchpad inbox. The decision log alone (`decisions.md`) is worth the setup. After a few weeks of "Chose X over Y because Z", it becomes your highest-value file.

Key principles:
- **Single writer** for main memory files. Multiple readers, one owner. Prevents quality dilution.
- **Keep the index short** (<200 lines). Link to topic files. Bloat kills quality.
- **Archive, never delete.** When files get long, move detail to `archive/`, leave a summary + pointer.
- **Save before clearing context.** Both `/clear` and compact are lossy operations.

Full architecture, save policies, handoff formats, and RAG search setup: [docs/memory-deep-dive.md](docs/memory-deep-dive.md)

---

## Context Management

Your AI gets measurably dumber as its context window fills up. This matters more than most people realize.

- **Compact at 40-50%** context usage — later and the summary itself is low quality
- **Clear > compact** — a fresh start with good memory beats a vague summary
- **Config under 80 lines** — don't repeat rules across config, hooks, and memory
- **`/clear` between unrelated topics** — the quality difference is immediate

---

## Models & Routing

Route tasks to the cheapest model that can handle them:

```
Quick question / summary    → Gemini Flash (free)
Image analysis / screenshots → Gemini (free, best vision)
Coding / debugging          → Codex or Claude Code
Research / web search       → Grok or Gemini
Offline / private data      → Ollama (local)
Multi-file refactoring      → Claude Code (needs file access)
```

### Beware Agent Bias

Agents overreach on decisions and nudge you toward their preferred ecosystem. Keep final calls human-owned, ask for 2+ alternatives with tradeoffs, and require evidence (benchmarks, docs, costs) for recommendations.

Full tool list, MCP servers, local model recommendations, and bonus tools: [docs/tools-reference.md](docs/tools-reference.md)

---

## Project Structure

```
ai-hot-sauce/
├── README.md              ← You are here
├── docs/
│   ├── voice-setup.md     ← Push-to-talk daemon setup
│   ├── memory-deep-dive.md ← Full memory architecture
│   ├── hooks-and-practices.md ← Hooks, practices, dual-agent patterns
│   ├── tools-reference.md  ← CLI tools, MCP servers, bonus tools
│   ├── clawds-claws.md    ← Screen pointer overlay
│   └── mcp-market-capture.md ← MCP scraping pipeline
├── src/                   ← Engine code (scoring router, KPI library, context manager)
├── skills/                ← Reusable AI skill definitions
├── chrome-extension/      ← Browser capture tools
├── tests/                 ← Test suite
├── sauce.py               ← CLI entry point
└── pyproject.toml         ← Python project config
```

---

## Links

- [Claude Code](https://claude.ai/download) — Anthropic CLI
- [Codex CLI](https://github.com/openai/codex) — OpenAI CLI
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) — Google CLI (free tier)
- [Ollama](https://ollama.com) — Local model runner
- [Groq](https://groq.com) — Fast free STT API
- [ChromaDB](https://www.trychroma.com) — Vector database
- [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) — CPU reranker
- [MCP Servers](https://github.com/modelcontextprotocol) — Tool servers for AI

---

## License

MIT. See [LICENSE](LICENSE).
