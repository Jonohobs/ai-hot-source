# AI Hot Sauce

A collection of spicy AI tools, agents, and utilities — the secret ingredients that make agentic workflows actually work.

## What's Inside

### Sentinels
Trigger-based agent daemon system. Define "when X happens, spawn agent Y with context Z" rules. Event-to-agent wiring without a heavy framework.

- [Design Doc](SENTINELS.md)
- [Pipeline Watcher](sentinels/dtr_watcher.py) — file-system watcher that triggers 3D reconstruction pipelines

### Context Manager (`src/context-manager/`)
Tools for managing AI agent context across sessions — observation logging, session digests, pre-compaction summaries, and attention residual analysis.

### Guiding Sprite (`src/guiding-sprite/`)
AI-powered screen overlay that guides your cursor to UI elements using natural language. Describe what you're looking for ("the save button"), and an animated sprite floats to it. Supports Claude, GPT-4 Vision, and Gemini.

### AI Stack Manifest
[STACK.md](STACK.md) — living inventory of every model, API, and tool in the stack with health status and token budget routing tiers.

## Philosophy

Ship tools that solve real friction in AI-assisted development. No frameworks for frameworks' sake — just the hot sauce that makes everything better.

## License

MIT
