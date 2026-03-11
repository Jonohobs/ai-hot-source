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
            }
            for snapshot in snapshots
        ],
    }
    output_path = output_root / "index.json"
    output_path.write_text(json.dumps(index, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
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
        print(f"Wrote {source_id} -> {output_path}")
    index_path = write_index(output_root, snapshots)
    print(f"Wrote index -> {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
