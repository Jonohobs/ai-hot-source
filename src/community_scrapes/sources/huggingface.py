from __future__ import annotations

from datetime import datetime, timezone

from ..http import fetch_json


URL = (
    "https://huggingface.co/api/models"
    "?sort=downloads&direction=-1&limit=30&full=true"
)


def run() -> dict:
    payload = fetch_json(URL)
    records = []

    for item in payload:
        records.append(
            {
                "id": item.get("id"),
                "author": item.get("author"),
                "pipeline_tag": item.get("pipeline_tag"),
                "last_modified": item.get("lastModified"),
                "downloads": item.get("downloads"),
                "likes": item.get("likes"),
                "private": item.get("private"),
                "gated": item.get("gated"),
                "tags": item.get("tags", []),
            }
        )

    return {
        "source": "huggingface_trending_models",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": records,
    }
