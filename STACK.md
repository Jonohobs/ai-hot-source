# AI Stack Manifest
> Auto-referenced by the dispatcher skill. Last updated: 2026-03-22.
> Health: ✅ working | ⚠️ degraded | ❌ broken | 💤 not installed/inactive

---

## Models

| Model | Access | Cost | Best For | Limits | Health |
|-------|--------|------|----------|--------|--------|
| Claude Opus 4.6 | Claude Code (self) | Paid (primary) | Architecture, complex reasoning, code review | Rate limits apply | ✅ |
| Claude Sonnet 4.5 | Claude Code (subagent) | Paid | Fast code gen, web research, parallel tasks | Rate limits apply | ✅ |
| Claude Haiku | API | Cheap | Classification, triage, routing | Lower capability | ✅ |
| Gemini 2.5 Pro | CLI (`gemini`) / API | Free tier (250K TPM, 1K RPD) | Best quality free, multimodal, 1M context | 5-15 RPM | ⚠️ (reinstalled 2026-03-22) |
| Grok (xAI) | API / Web | $175/mo free credits | Contrarian takes, general tasks | Requires data-sharing opt-in | ⚠️ (verify key) |
| Perplexity | Web | Free/Pro | Search-grounded research, citations | No code execution | ✅ |
| Ollama (llama3) | Local (`ollama`) | Free ($0) | Offline inference, privacy-sensitive tasks | 4.7GB, GPU-bound | ✅ |
| SambaNova | API (DevLoop) | Free (20M tok/day) | Highest-volume batching, R&D | OpenAI-compat | ✅ |
| Mistral Large | API (DevLoop) | Free (1B tok/month) | Code (Codestral), queued batch | 2 RPM | ✅ |
| Cerebras | API (DevLoop) | Free (1M tok/day) | Speed-critical tasks | 2,600 tok/s | ✅ |
| Groq | API (DevLoop) | Free (~14K req/day) | Real-time lint/review, whisper | 30-60 RPM | ✅ |
| Mercury 2 | API | 10M free tokens (one-time) | Fast diffusion inference | OpenAI-compat | ✅ |
| OpenRouter | API (DevLoop) | 29 free models, 1K RPD | Aggregator/fallback router | Varies by model | ⚠️ (verify key) |

**Token budget routing:**
```
TIER 0 (local):     Ollama — $0, your GPU
TIER 1 (free API):  SambaNova → Mistral → Cerebras → Groq → Gemini
TIER 2 (cheap):     OpenRouter, Grok credits, Mercury 2
TIER 3 (expensive): Claude Code — supervised work only
```

**NO Chinese models** (ban in effect — MiniMax correlation, spam risk). DeepSeek/Kimi via OpenRouter allowed for non-sensitive summarization only when explicitly noted.

---

## 3D Reconstruction

| Tool | Access | Cost | Quality | Speed | Health |
|------|--------|------|---------|-------|--------|
| VGGT (Meta) | Local (5GB weights needed) | Free | High (multi-view, not hallucination) | Sub-second | ⚠️ (weights not yet downloaded) |
| Trellis | HuggingFace Space / API | Free (quota) | Good | Moderate | ✅ (DTR pipeline, 1st fallback) |
| Hunyuan3D-2.1 (Tencent) | HuggingFace Space / Gradio API | Free | Good (4-view support) | 95-120s | ✅ (tested in DTR) |
| Rodin / Hyper3D | fal.ai API | ~$0.40/job | High (quad-mesh, 4K PBR, 21K verts) | Moderate | ✅ (tested, in api_reconstruct_v2.py) |
| Tripo AI | fal.ai API | ~$0.40/job | Good | Moderate | ✅ (DTR pipeline, 4th fallback) |
| RealityScan (Epic) | Desktop / REST+gRPC API | Free under $1M revenue | Best-in-class (photogrammetry) | Slow (batch) | ✅ |
| COLMAP | Local (no-CUDA build) | Free | High (photogrammetry) | Slow | ⚠️ (failed at 360p; untested at 1080p — use with U2Net masking) |
| Blender | Local | Free | N/A (mesh cleanup/import) | Manual | ✅ |
| RunPod Serverless | Cloud API | ~$0.10/job | Good (Trellis) | Moderate | ✅ (DTR pipeline, 2nd fallback) |
| GCP Spot L4 | Cloud API | ~$0.12/job | Good (Trellis) | Moderate | ✅ (DTR pipeline, 3rd fallback) |

**DTR fallback chain:** `Trellis (free HF) → RunPod ($0.10) → GCP ($0.12) → Tripo ($0.40)`
**Rule:** All photogrammetry must use U2Net masking.

---

## Voice / Audio

| Tool | Access | Cost | Notes | Health |
|------|--------|------|-------|--------|
| ElevenLabs | API | Paid (105K token budget noted) | TTS, voice cloning, MC scripts, ad breaks | ✅ |
| Groq Whisper | API (DevLoop / OpenWhispr) | Free | ~440ms latency, real-time STT | ✅ |
| OpenWhispr | Local Electron app (`~/openwhispr/`) | Free | Push-to-talk, Groq-backed, RCtrl+RAlt PTT | ✅ |
| Claude Code /voice | Built-in | Free | Improved 2026-03-15, needs headset mic | ✅ |
| openai-whisper | Local pip (v20250625) | Free | Offline STT, slower | ✅ |

---

## Code / Dev

| Tool | Access | Notes | Health |
|------|--------|-------|--------|
| Claude Code | Terminal / IDE | Primary coding agent (this system) | ✅ |
| Codex CLI | Terminal (`codex`) | OpenAI agent, different model perspective | ✅ |
| Cursor | IDE | Code-aware second opinion, inline edits | ✅ |
| Gemini CLI | Terminal (`gemini`) | Google agent, 1M context, free tier | ⚠️ (reinstalled 2026-03-22, was broken) |
| LangGraph | Python (`langgraph` 1.1.3) | Graph-based agent workflows | ✅ |
| LiteLLM | Python (`litellm` 1.81.6) | Model gateway / provider abstraction | ✅ |
| LlamaIndex | Python (`llama-index` 0.14.18) | RAG / data indexing (activate per-project) | ✅ (dormant) |
| ChromaDB | Python (`chromadb` 1.5.1) | Vector database | ✅ |
| E2B Sandbox | — | Safe agent code execution | 💤 (pip install pending, $100 credit) |
| Arize Phoenix | — | Agent tracing + cost dashboard | 💤 (Docker deploy pending) |
| Context7 MCP | — | Live API docs, kills hallucinated API calls | 💤 (install pending) |

---

## Automation

| Tool | Access | Notes | Health |
|------|--------|-------|--------|
| n8n | Hetzner VPS (SSH tunnel) | Workflow automation, SQLite, 330MiB RAM | ✅ |
| DevLoop | Local (`~/devloop/`) | LLM router + 7 free providers, 50M+ tok/day | ✅ (MVP, sign-ups in progress) |
| GSD | Claude Code skills (`~/.claude/commands/gsd/`) | Execution framework v1.26.0 | ✅ |
| BMAD | `~/_bmad/` | Planning/SDLC agent framework v6.2.0 | ✅ |
| AI Hot Sauce | `~/ai-hot-sauce/` (`~/scrape-depot/ai-hot-sauce/`) | KPI library (52 KPIs), context manager, routing engine | ✅ |
| Playwright MCP | — | Browser automation, web scraping, E2E tests | 💤 (install pending) |

---

## Research

| Tool | Access | Notes | Health |
|------|--------|-------|--------|
| /recon skill | Claude Code skill | Parallel 4-agent research fan-out | ✅ |
| Perplexity | Web | Search-grounded, citation-heavy | ✅ |
| Gemini CLI | Terminal (`gemini`) | 1M context, free tier, web access | ⚠️ (auth may need refresh) |
| Web search (Claude) | Built-in (claude.ai) | General search-grounded queries | ✅ |

---

## Creative

| Tool | Access | Notes | Health |
|------|--------|-------|--------|
| Canva MCP | claude.ai MCP | Design gen + editing, 30+ tools | ✅ |
| Figma MCP | claude.ai MCP | Design context, Code Connect, FigJam diagrams | ✅ |
| Spline MCP | claude.ai MCP (`~/spline-mcp/`) | 3D code gen, WebSocket, n8n, 22 tools | ✅ |
| Remotion | npm / `~/remotion/` | Programmatic video creation | ✅ |
| Blender | Local desktop | 3D modelling, mesh cleanup, animation | ✅ |
| ElevenLabs | API | TTS for creative audio, MC scripts, ads | ✅ |

---

## Infrastructure

| Provider | Services | Cost | Health |
|----------|----------|------|--------|
| Vercel | Riffraff + DTR hosting, CI/CD | Free tier | ✅ |
| Railway | OpenClaw (Node.js agent gateway) | Free/usage | ✅ |
| Hetzner VPS | n8n, Tailscale, future OpenClaw mirror | ~€4-6/mo | ⚠️ (DDoS risk at L7 — CrowdSec/CF free tier TODO) |
| HuggingFace | Model hosting, Spaces (Trellis, VGGT, Hunyuan3D) | Free tier | ✅ |
| GitHub | Source control, Pages (agentic taxonomy viz), agent-memory repo | Free | ✅ |
| Docker | Local containerisation + production deploys | Free (local) | ✅ |
| Ollama | Local LLM inference (llama3 4.7GB) | Free | ✅ |

---

## MCP Servers (claude.ai)

| Server | Status | Tools | Notes |
|--------|--------|-------|-------|
| Spline MCP | ✅ Active | 22 | 3D code gen, asset mgmt, WebSocket, n8n |
| Figma MCP | ✅ Active | 10+ | Design context, Code Connect |
| Canva MCP | ✅ Active | 30+ | Design gen + editing |
| Slack MCP | ✅ Active | 10+ | Message/channel ops |
| Gmail MCP | ✅ Active | 7 | Email search/compose |
| Google Calendar MCP | ✅ Active | 9 | Event mgmt, availability |
| Playwright MCP | ✅ Active | 20+ | Browser automation |
| Notion MCP | 💤 Disabled | 15+ | Re-enable for wiki/database work |
| Clay MCP | 💤 Disabled | 15+ | Re-enable for freelance outbound sales |

---

## Lean Stack (Active Config — decided 2026-03-20)

Council decision: Stack A "Lean" + n8n. One tool per layer.

| Layer | Tool | Status |
|-------|------|--------|
| LLM SDK | Anthropic + OpenAI | ✅ Active |
| Orchestration | LangGraph (sole) | ✅ Active |
| RAG/Data | LlamaIndex (per-project only) | ✅ Dormant |
| Vector DB | ChromaDB | ✅ Active |
| Model Gateway | LiteLLM | ✅ Active |
| Observability | Arize Phoenix | 💤 TODO (Docker) |
| Sandbox | E2B | 💤 TODO (pip) |
| MCP Docs | Context7 | 💤 TODO |
| Automation | n8n | ✅ Live (Hetzner) |
| Local LLM | Ollama (llama3) | ✅ Active |

**Dropped (installed but unused):** CrewAI, Vellum, LangSmith, LangChain base, Composio
