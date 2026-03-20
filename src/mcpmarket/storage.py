from __future__ import annotations

import json
from pathlib import Path

from .models import MCPServerRecord


class MCPMarketArchive:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_records(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows: list[dict] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
        return rows

    def upsert_records(self, records: list[MCPServerRecord | dict]) -> int:
        by_key: dict[str, dict] = {}
        for row in self.load_records():
            key = row.get("slug") or row.get("source_url")
            if key:
                by_key[key] = row

        for record in records:
            payload = record.to_dict() if isinstance(record, MCPServerRecord) else dict(record)
            key = payload.get("slug") or payload.get("source_url")
            if not key:
                continue
            by_key[key] = payload

        ordered = [by_key[key] for key in sorted(by_key)]
        content = "\n".join(json.dumps(row, sort_keys=True) for row in ordered)
        if content:
            content += "\n"
        self.path.write_text(content, encoding="utf-8")
        return len(ordered)
