from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from ..http import fetch_json


VIDEOS = [
    {
        "url": "https://www.youtube.com/watch?v=Xn-gtHDsaPY",
        "notes": "Seed video added manually.",
    },
]


def _oembed_url(video_url: str) -> str:
    return (
        "https://www.youtube.com/oembed"
        f"?url={quote(video_url, safe=':/?=&')}&format=json"
    )


def run() -> dict:
    records = []

    for item in VIDEOS:
        payload = fetch_json(_oembed_url(item["url"]))
        records.append(
            {
                "id": item["url"].split("v=")[-1],
                "url": item["url"],
                "title": payload.get("title"),
                "author": payload.get("author_name"),
                "author_url": payload.get("author_url"),
                "provider_name": payload.get("provider_name"),
                "thumbnail_url": payload.get("thumbnail_url"),
                "notes": item.get("notes"),
            }
        )

    return {
        "source": "youtube_watch_videos",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": records,
    }
