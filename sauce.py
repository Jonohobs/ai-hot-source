#!/usr/bin/env python3
"""sauce.py — CLI entry point for the Hot Sauce engine.

Usage:
  python sauce.py "explain this error"           # auto-route to best model
  python sauce.py "@gemini describe this image"   # explicit model override
  python sauce.py --stats                         # show model health + breaker states
  python sauce.py --rank "fix this bug"           # show how models would be ranked
  python sauce.py --session abc123 "continue..."  # resume a session
  python sauce.py --reset-breaker gemini-2.5-flash  # manually reset a tripped breaker
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.engine import HotSauceEngine
from src.routing.scorer import classify_task


def _build_engine(db_path: str | None = None) -> HotSauceEngine:
    """Build engine with available providers based on env vars."""
    engine = HotSauceEngine(db_path=db_path)

    # Only add providers we have keys for
    if os.environ.get("OPENAI_API_KEY"):
        from src.providers.openai_provider import OpenAIProvider
        engine.add_provider(OpenAIProvider())

    if os.environ.get("ANTHROPIC_API_KEY"):
        from src.providers.anthropic_provider import AnthropicProvider
        engine.add_provider(AnthropicProvider())

    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        from src.providers.google_provider import GoogleProvider
        key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        engine.add_provider(GoogleProvider(api_key=key))

    # Always try Ollama (local, no key needed)
    try:
        from src.providers.ollama_provider import OllamaProvider
        p = OllamaProvider()
        if p._is_available():
            engine.add_provider(p)
    except Exception:
        pass

    return engine


def cmd_chat(args):
    engine = _build_engine(args.db)
    sid = engine.session(args.session)
    result = engine.chat(args.message, session_id=sid, system=args.system)
    print(result.content)
    print(f"\n--- [{result.model}] {result.tokens_in}→{result.tokens_out} tokens, "
          f"{result.latency_ms:.0f}ms, ${result.cost_usd:.6f} ---", file=sys.stderr)


def cmd_stats(args):
    engine = _build_engine(args.db)
    stats = engine.stats()
    print(json.dumps(stats, indent=2, default=str))


def cmd_rank(args):
    engine = _build_engine(args.db)
    task = classify_task(args.message)
    ranked = engine.router.rank(task)
    print(f"Task: {task.task_type} | vision={task.needs_vision} | tools={task.needs_tools}")
    print(f"{'Model':<35} {'Score':>8}")
    print("-" * 45)
    for name, score in ranked:
        breaker_state = engine.breaker.state(name)
        flag = f" [{breaker_state.upper()}]" if breaker_state != "closed" else ""
        print(f"{name:<35} {score:>8.4f}{flag}")


def cmd_reset_breaker(args):
    engine = _build_engine(args.db)
    engine.breaker.reset(args.model)
    print(f"Breaker reset for {args.model}")


def main():
    parser = argparse.ArgumentParser(description="Hot Sauce — AI model router + engine")
    parser.add_argument("--db", help="SQLite database path", default=None)
    sub = parser.add_subparsers(dest="command")

    # Default: chat
    chat_p = sub.add_parser("chat", help="Send a message (default)")
    chat_p.add_argument("message", help="Your message")
    chat_p.add_argument("--session", "-s", help="Session ID to resume")
    chat_p.add_argument("--system", help="System prompt")
    chat_p.set_defaults(func=cmd_chat)

    # Stats
    stats_p = sub.add_parser("stats", help="Show model health and breaker states")
    stats_p.set_defaults(func=cmd_stats)

    # Rank
    rank_p = sub.add_parser("rank", help="Show model ranking for a message")
    rank_p.add_argument("message", help="Message to classify and rank")
    rank_p.set_defaults(func=cmd_rank)

    # Reset breaker
    reset_p = sub.add_parser("reset-breaker", help="Reset a circuit breaker")
    reset_p.add_argument("model", help="Model name to reset")
    reset_p.set_defaults(func=cmd_reset_breaker)

    args = parser.parse_args()

    # Default to chat if bare message given
    if args.command is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            args.message = " ".join(sys.argv[1:])
            args.session = None
            args.system = None
            cmd_chat(args)
        else:
            parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
