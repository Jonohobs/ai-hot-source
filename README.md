# Jono's AI Hot Sauce 🌶️

A practical guide to setting up an AI-powered dev rig. Feed this to your AI assistant and it'll help you set up whatever applies to you.

---

## The Stack

You don't nessissarily need all of this, go through it with your AI and see what fits, I like to run claudecode straight from the CLI (Powershell for Windows,). Pick what fits.

### AI CLI Tools

| Tool | What it does | Cost |
|------|-------------|------|
| **Claude Code** | Anthropic's CLI. Reads/writes files, runs commands, has subagents and hooks. Best multi-file editor. | Included in Claude Pro (~£17/mo) |
| **Codex CLI** | OpenAI's agentic CLI. Sharp coder, fast. | Included in ChatGPT Pro (~£20/mo) |
| **GitHub Copilot Chat** | VS Code chat with multiple models (Sonnet, GPT-4). Included in Copilot subscription. | Free tier (limited) or ~£10/mo |
| **Gemini CLI** | Google's CLI. Free tier is generous (1000 req/day, 1M token context). Great for research and vision. | Free |
| **Ollama** | Run models locally. No internet needed, no cost, your data stays on your machine. | Free |

> ⚠️ **Watch your billing:** Check what your subscription includes before using CLI tools. Some plans cover CLI access, others may charge separately via API billing (pay-per-token). Don't assume — check your plan details.

**If you only get one:** Gemini CLI (free) or GitHub Copilot (if you use VS Code). Add Ollama for offline.

### Editor Chat vs CLI — Know the Tradeoff

VS Code Chat / Cursor chat is convenient and often included in your subscription, but it has real limitations:
- **No persistent memory** — forgets everything between sessions
- **No hooks or automation** — can't auto-load context or run scripts
- **Limited context** — doesn't know your project setup, preferences, or history
- **Auto model routing** — you often don't know which model you're talking to
- **Less capable** — may lack web access, file system awareness, or tool access depending on setup

CLI tools (Claude Code, Codex) give you:
- Memory systems, hooks, subagents
- Full file system and terminal access
- Web access via tools and MCP servers
- You choose the model explicitly

**Use editor chat for quick questions. Use CLI for real work.**

### Model Routing — Don't Overpay

The biggest mistake people make is using one expensive model for everything. Route tasks to the cheapest thing that can handle them:

```
Quick question / summary    → Gemini Flash (free)
Image analysis / screenshots → Gemini (free, best vision)
Coding / debugging          → Codex or Claude Code
Research / web search       → Grok or Gemini
Offline / private data      → Ollama (local)
Multi-file refactoring      → Claude Code (needs file access)
```

### ask.py — One Command, Multiple Models

A Python script that routes queries to different models from one interface:
```bash
python ask.py @gemini "explain this error"        # free
python ask.py @gemini "describe this" --image screenshot.png  # free vision
python ask.py @ollama "summarise this file"        # local, free
```
Build your own or find one — the point is: don't open 4 different apps. One CLI, multiple backends.

---

## Memory System

Your AI forgets everything between sessions. Fix that.

### Persistent Memory Files
Create a `~/.agent/memory/` folder (or wherever you like) with markdown files:
- **MEMORY.md** — critical rules and quick references (always loaded)
- **decisions.md** — why you chose X over Y (you'll forget, your AI will forget)
- **learnings.md** — what worked, what didn't
- **inbox.md** — dump thoughts here, curate later

**Key rule:** Keep MEMORY.md short (<200 lines). Link to topic files for details. Your AI loads this every session — bloat kills it.

### RAG Search (optional, powerful)
- **ChromaDB** + **FlashRank** reranker = semantic search over all your notes
- Index your memory files, search by meaning not just keywords
- FlashRank is CPU-only, tiny, and dramatically improves search quality
- `pip install chromadb flashrank`

---

## Hooks — Make Your AI Smarter Automatically

Hooks are scripts that run before/after your AI does things. Claude Code has native hook support. For other tools, you can script similar behaviour.

### What hooks are worth having:
| Hook | When it fires | What it does |
|------|--------------|-------------|
| **Session start** | New conversation | Loads your memory, shows inbox items, reminds you where you left off |
| **Pre-tool guard** | Before file edits | Backs up files before AI modifies them. Catches bad patterns. |
| **Post-tool memory** | After file writes | Auto-indexes new files into your search system |
| **Pre-compact** | Before context compression | Saves conversation state so you don't lose context |
| **Audit log** | After bash commands | Logs what commands your AI ran (security + debugging) |
| **Context monitor** | After any action | Warns you when context window is getting full |

### Example: Session Start Hook
Your AI starts every session by reading your memory files and giving you a "since last time" briefing. No more repeating yourself.

---

## Voice — Push to Talk

Talk to your AI instead of typing. The setup:

1. **ffmpeg** captures audio from your mic (DirectShow on Windows)
2. **Groq API** transcribes it with Whisper (~1 second, free tier available)
3. Script pastes the text into your terminal and hits Enter

**Hotkey:** Hold Ctrl+Alt to record, release to transcribe and send.

Key details:
- `pip install groq numpy python-dotenv`
- ffmpeg must be on PATH
- Run as a background daemon on startup (VBS script on Windows, systemd on Linux)
- Singleton lock prevents duplicates
- Set process priority to HIGH for real-time audio
- Add a corrections dictionary for words it always gets wrong

**Cheaper alternative:** `whisper.cpp` with Vulkan for fully offline STT. Slightly slower but zero API calls.

---

## Security — Don't Be Stupid

### Deny List
Block your AI from running dangerous commands. These should be denied by default:
```
rm -rf /*, sudo *, git push --force, git reset --hard,
dd if=*, curl | bash, powershell -EncodedCommand,
netcat, nc -e, nc -l, reg (Windows registry)
```

Also block reading `~/.ssh/*` and any curl POST commands (prevents data exfiltration).

### Audit Logging
Log every bash command your AI runs to a CSV. Costs nothing, saves you when something goes wrong.

### File Backups
Before your AI edits any file, copy the original to a backup folder. Cheap insurance.

### Model Safety
- **US/EU models only** if you care about data sovereignty (Meta, Google, Anthropic, OpenAI, Mistral)
- **Local models** (Ollama) for anything sensitive — financials, personal data, credentials
- **Never pipe untrusted URLs** through `curl | bash`

---

## MCP Servers — Give Your AI Superpowers

Model Context Protocol lets your AI talk to external services. Useful ones:

| Server | What it does |
|--------|-------------|
| **Puppeteer** | Browser automation — screenshots, form filling, scraping |
| **Google Drive** | Read/search your Drive files from the CLI |
| **Filesystem** | Controlled file access (safer than raw bash) |

Install: `npx -y @modelcontextprotocol/server-puppeteer` (etc.)

---

## Skills / Slash Commands

Pre-written prompts for common workflows. Instead of explaining what you want every time, you type `/commit` or `/review-pr` and it runs the full workflow.

Worth building skills for:
- **Committing** — consistent commit messages, runs tests first
- **PR review** — security-focused diff analysis
- **Debugging** — systematic root cause analysis before guessing
- **Planning** — explore approaches before writing code
- **Verification** — prove it works before claiming it's done

---

## Local Models That Actually Fit on Consumer GPUs

If you have 4-8GB VRAM:

| Model | Size | Good for |
|-------|------|----------|
| **Phi-4-mini** (Microsoft) | ~2GB | Best local coder for small GPUs |
| **Llama 3.2** (Meta) | ~2GB | General chat, summaries |
| **Mistral 7B** (Mistral AI) | ~4GB | Reasoning |
| **CodeLlama** (Meta) | ~4GB | Code generation |

Install via Ollama: `ollama pull phi4-mini`

---

## The Dashboard (optional)

A self-contained HTML file that shows:
- Context window usage (how full is your AI's memory)
- Token pools and daily usage
- Active projects and infrastructure status

No server needed — just a Python script that generates static HTML. Open in browser.

---

## Quick Setup Checklist

1. [ ] Install at least one AI CLI tool (Gemini CLI is free)
2. [ ] Create `~/.agent/memory/` with MEMORY.md
3. [ ] Add your first decision to decisions.md
4. [ ] Set up deny rules (block dangerous commands)
5. [ ] Install Ollama + one small model for offline use
6. [ ] (Optional) Set up push-to-talk if you prefer voice
7. [ ] (Optional) Add hooks for session start + audit logging
8. [ ] (Optional) Set up ChromaDB + FlashRank for memory search

---

## Links

- [Claude Code](https://claude.ai/download) — Anthropic CLI
- [Codex CLI](https://github.com/openai/codex) — OpenAI CLI
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) — Google CLI
- [Ollama](https://ollama.ai) — Local model runner
- [Groq](https://groq.com) — Fast free STT API
- [ChromaDB](https://www.trychroma.com) — Vector database
- [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) — CPU reranker
- [MCP Servers](https://github.com/modelcontextprotocol) — Tool servers for AI

---

*Built by trial, error, and a lot of tokens. Feed this to your AI and tell it to help you set up whatever looks useful.*
