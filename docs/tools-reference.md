# Tools Reference

## Core Tools

Scripts that live in `~/.agent/tools/` and get used regularly:

| Tool | What it does |
|------|-------------|
| `ask.py` | Multi-model CLI router. Gemini (free), Ollama (local), Groq. Text + vision. |
| `memory-search.py` | Tiered ChromaDB search — memory, docs, source code, session logs. FlashRank reranker. |
| `dashboard.py` | Generates HTML dashboard — context %, tokens, projects, status. |
| `rig-doctor.py` | Infrastructure audit — checks hooks, tasks, paths, state files. |
| `package-rig.py` | Generates sanitized, shareable version of your rig (strips personal data). |
| `mine-conversations.py` | Extracts learnings from past session logs. |
| `integrity-check.py` | Verifies file hashes against expected state. Catches unexpected changes. |

You don't need all of these. `ask.py` and `memory-search.py` are the highest-value. Build the rest as you need them.

## MCP Servers

Model Context Protocol lets your AI talk to external services. Useful ones:

| Server | What it does |
|--------|-------------|
| **Puppeteer** | Browser automation — screenshots, form filling, scraping |
| **Google Drive** | Read/search your Drive files from the CLI |
| **Filesystem** | Controlled file access (safer than raw bash) |

Install: `npx -y @modelcontextprotocol/server-puppeteer` (etc.)

## The Dashboard (Optional)

A self-contained HTML file that shows:
- Context window usage (how full is your AI's memory)
- Token pools and daily usage
- Active projects and infrastructure status

No server needed — just a Python script that generates static HTML. Open in browser.

## Extra Toppings — Bonus Tools

These are optional, but worth knowing about. All are free or self-hostable.

| Tool | What it does | Install |
|------|-------------|---------|
| **Langfuse** | Open-source observability for AI calls. Traces agent actions, RAG retrieval, latency, cost. Self-hostable. | `pip install langfuse` |
| **OpenWebUI** | Full ChatGPT-style web UI for Ollama. Voice, vision, RAG, model switching. | `docker run -d -p 3000:8080 ghcr.io/open-webui/open-webui:main` |
| **Mem0** | Entity memory — remembers facts about people and things across sessions. | `pip install mem0ai` |
| **OpenCode** | Provider-agnostic coding agent. 75+ LLM providers through one terminal UI. | `npm i -g opencode-ai@latest` |
| **LiteLLM** | API proxy — lets Claude-compatible tools talk to Gemini/Ollama instead. | `pip install litellm` |
| **OpenRouter** | Multi-model gateway. 200+ models, pay-per-token, no subscriptions. | API key from openrouter.ai |
| **Godot** | Open-source game engine. AI agents can write GDScript and scene files directly. | Free, [godotengine.org](https://godotengine.org) |

## AI CLI Tools

| Tool | What it does |
|------|-------------|
| **Claude Code** | Anthropic's CLI. Reads/writes files, runs commands, has subagents and hooks. Best multi-file editor. |
| **Codex CLI** | OpenAI's agentic CLI. Sharp coder, fast. |
| **GitHub Copilot Chat** | VS Code chat with multiple models (Sonnet, GPT-4o). Included in Copilot subscription. |
| **Gemini CLI** | Google's CLI. Free tier is generous (1000 req/day, 1M token context). Great for research and vision. |
| **Ollama** | Run models locally. No internet needed, no cost, your data stays on your machine. |

> **Watch your billing:** Check what your subscription includes before using CLI tools. Some plans cover CLI access, others may charge separately via API billing (pay-per-token). Don't assume — check your plan details.

## Local Models — 2-4GB GPU Friendly

| Model | Size | Good for |
|-------|------|----------|
| **Phi-4-mini** (Microsoft) | ~2GB | Best local coder for small GPUs |
| **Llama 3.2** (Meta) | ~2GB | General chat, summaries |
| **Mistral 7B** (Mistral AI) | ~4GB | Reasoning |
| **CodeLlama** (Meta) | ~4GB | Code generation |

Install via Ollama: `ollama pull phi4-mini`

## Cross-Platform CLI Setup

| | Windows | Mac | Linux |
|---|---|---|---|
| **Shell** | PowerShell 7 | Zsh | Bash |
| **Terminal** | Windows Terminal | iTerm2 or Warp | Alacritty or Kitty |
| **Packages** | Winget or Chocolatey | Homebrew | apt / dnf / pacman |
