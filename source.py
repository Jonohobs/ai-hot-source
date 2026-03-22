#!/usr/bin/env python3
"""sauce.py — CLI entry point for the Hot Source engine.

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

from src.engine import HotSourceEngine
from src.mcpmarket.fetcher import CachedHttpClient
from src.mcpmarket.parser import extract_server_links, parse_detail_page
from src.mcpmarket.storage import MCPMarketArchive
from src.routing.scorer import classify_task


def _build_engine(db_path: str | None = None) -> HotSourceEngine:
    """Build engine with available providers based on env vars."""
    engine = HotSourceEngine(db_path=db_path)

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


def cmd_scrape_mcpmarket(args):
    archive = MCPMarketArchive(args.out)
    client = CachedHttpClient(
        cache_dir=args.cache_dir,
        min_delay_seconds=args.delay,
        timeout_seconds=args.timeout,
    )
    links: set[str] = set()

    if args.detail_url:
        links.update(args.detail_url)
    else:
        for page in range(1, args.pages + 1):
            url = args.list_url.format(page=page)
            try:
                html_text = client.fetch_text(url, force=args.force)
            except Exception as exc:
                print(f"warning: failed to fetch listing page {url}: {exc}", file=sys.stderr)
                break
            page_links = extract_server_links(html_text)
            if not page_links:
                print(f"warning: no server links found on {url}", file=sys.stderr)
                break
            links.update(page_links)

    records = []
    ordered_links = sorted(links)[: args.limit] if args.limit else sorted(links)
    for url in ordered_links:
        try:
            html_text = client.fetch_text(url, force=args.force)
            records.append(parse_detail_page(html_text, url))
        except Exception as exc:
            print(f"warning: failed to parse detail page {url}: {exc}", file=sys.stderr)

    total = archive.upsert_records(records)
    print(json.dumps({
        "scraped": len(records),
        "archive_total": total,
        "output": str(Path(args.out).resolve()),
    }, indent=2))


def cmd_import_mcpmarket_capture(args):
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = [payload]
    archive = MCPMarketArchive(args.out)
    total = archive.upsert_records(payload)
    print(json.dumps({
        "imported": len(payload),
        "archive_total": total,
        "output": str(Path(args.out).resolve()),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Hot Source — AI model router + engine")
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

    # MCP Market scrape/import
    scrape_p = sub.add_parser("scrape-mcpmarket", help="Scrape MCP Market into normalized JSONL")
    scrape_p.add_argument("--out", default="data/mcpmarket/servers.jsonl", help="Output JSONL archive path")
    scrape_p.add_argument("--cache-dir", default=".cache/mcpmarket", help="Optional cache directory")
    scrape_p.add_argument("--list-url", default="https://mcpmarket.com/server?page={page}", help="Listing URL template")
    scrape_p.add_argument("--pages", type=int, default=1, help="Number of listing pages to crawl")
    scrape_p.add_argument("--limit", type=int, default=25, help="Maximum number of detail pages to fetch")
    scrape_p.add_argument("--detail-url", action="append", help="Fetch only these detail URLs (repeatable)")
    scrape_p.add_argument("--delay", type=float, default=2.5, help="Delay between HTTP requests")
    scrape_p.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")
    scrape_p.add_argument("--force", action="store_true", help="Ignore cached responses")
    scrape_p.set_defaults(func=cmd_scrape_mcpmarket)

    import_p = sub.add_parser("import-mcpmarket-capture", help="Import extension-exported JSON into normalized JSONL")
    import_p.add_argument("input", help="Path to exported JSON capture")
    import_p.add_argument("--out", default="data/mcpmarket/servers.jsonl", help="Output JSONL archive path")
    import_p.set_defaults(func=cmd_import_mcpmarket_capture)

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
