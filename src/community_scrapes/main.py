from __future__ import annotations

import argparse
import json
from pathlib import Path

from .sources import SOURCES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run community scrapers.")
    parser.add_argument("--list", action="store_true", help="List available sources and exit.")
    parser.add_argument("--all", action="store_true", help="Run all sources.")
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Source id to run. Repeatable.",
    )
    parser.add_argument(
        "--output-root",
        default="data",
        help="Directory where source snapshots will be written.",
    )
    return parser


def write_snapshot(output_root: Path, snapshot: dict) -> Path:
    output_dir = output_root / snapshot["source"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest.json"
    output_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return output_path


def _truncate(text: str, limit: int = 220) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def render_snapshot_markdown(snapshot: dict) -> str:
    lines = [
        f"# {snapshot['source']}",
        "",
        f"Generated at: `{snapshot['generated_at']}`",
        f"Records: `{snapshot['record_count']}`",
        "",
    ]

    for index, record in enumerate(snapshot["records"], start=1):
        title = record.get("title") or record.get("id") or f"Record {index}"
        lines.append(f"## {index}. {title}")
        lines.append("")

        if record.get("url"):
            lines.append(f"Source: {record['url']}")
        elif record.get("id", "").startswith("http"):
            lines.append(f"Source: {record['id']}")

        if record.get("author"):
            lines.append(f"Author: {record['author']}")
        if record.get("authors"):
            lines.append(f"Authors: {', '.join(record['authors'])}")
        if record.get("published"):
            lines.append(f"Published: {record['published']}")
        if record.get("last_modified"):
            lines.append(f"Last modified: {record['last_modified']}")
        if record.get("pipeline_tag"):
            lines.append(f"Type: {record['pipeline_tag']}")
        if record.get("downloads") is not None:
            lines.append(f"Downloads: {record['downloads']}")
        if record.get("likes") is not None:
            lines.append(f"Likes: {record['likes']}")
        if record.get("primary_category"):
            lines.append(f"Primary category: {record['primary_category']}")
        if record.get("categories"):
            lines.append(f"Categories: {', '.join(record['categories'])}")
        if record.get("tags"):
            lines.append(f"Tags: {', '.join(record['tags'][:12])}")
        if record.get("summary"):
            lines.append(f"Summary: {_truncate(record['summary'])}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_snapshot_markdown(output_root: Path, snapshot: dict) -> Path:
    output_dir = output_root / snapshot["source"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest.md"
    output_path.write_text(render_snapshot_markdown(snapshot), encoding="utf-8")
    return output_path


def write_index(output_root: Path, snapshots: list[dict]) -> Path:
    index = {
        "generated_at": max(snapshot["generated_at"] for snapshot in snapshots),
        "source_count": len(snapshots),
        "sources": [
            {
                "source": snapshot["source"],
                "record_count": snapshot["record_count"],
                "generated_at": snapshot["generated_at"],
                "path": f"{snapshot['source']}/latest.json",
                "browse_path": f"{snapshot['source']}/latest.md",
            }
            for snapshot in snapshots
        ],
    }
    output_path = output_root / "index.json"
    output_path.write_text(json.dumps(index, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return output_path


def write_index_markdown(output_root: Path, snapshots: list[dict]) -> Path:
    lines = [
        "# Data Index",
        "",
        "Browseable snapshot links for the current public metadata sources.",
        "",
    ]

    for snapshot in snapshots:
        lines.extend(
            [
                f"## {snapshot['source']}",
                "",
                f"- Records: `{snapshot['record_count']}`",
                f"- Generated at: `{snapshot['generated_at']}`",
                f"- Browse: [{snapshot['source']}/latest.md](./{snapshot['source']}/latest.md)",
                f"- JSON: [{snapshot['source']}/latest.json](./{snapshot['source']}/latest.json)",
                "",
            ]
        )

    output_path = output_root / "index.md"
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list:
        for source_id, source in SOURCES.items():
            print(f"{source_id}\t{source.description}")
        return 0

    requested = args.sources or []
    if args.all:
        requested = list(SOURCES.keys())

    if not requested:
        parser.error("Specify --all, --source, or --list.")

    unknown_sources = [source_id for source_id in requested if source_id not in SOURCES]
    if unknown_sources:
        parser.error(f"Unknown source(s): {', '.join(unknown_sources)}")

    output_root = Path(args.output_root)
    snapshots: list[dict] = []
    for source_id in requested:
        snapshot = SOURCES[source_id].run()
        snapshots.append(snapshot)
        output_path = write_snapshot(output_root, snapshot)
        markdown_path = write_snapshot_markdown(output_root, snapshot)
        print(f"Wrote {source_id} -> {output_path}")
        print(f"Wrote {source_id} browse view -> {markdown_path}")
    index_path = write_index(output_root, snapshots)
    index_markdown_path = write_index_markdown(output_root, snapshots)
    print(f"Wrote index -> {index_path}")
    print(f"Wrote browse index -> {index_markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
