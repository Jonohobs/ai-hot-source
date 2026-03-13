from __future__ import annotations

from datetime import datetime, timezone

from ..http import fetch_json


REPOS = [
    {
        "full_name": "openbestof/awesome-ai",
        "notes": "Auto-ranked AI repository collection.",
    },
    {
        "full_name": "mahseema/awesome-ai-tools",
        "notes": "Curated AI tools list.",
    },
    {
        "full_name": "youssefHosni/Awesome-AI-Data-GitHub-Repos",
        "notes": "AI data repository collection.",
    },
]


def _repo_url(full_name: str) -> str:
    return f"https://api.github.com/repos/{full_name}"


def run() -> dict:
    records = []

    for item in REPOS:
        payload = fetch_json(_repo_url(item["full_name"]))
        license_info = payload.get("license") or {}
        records.append(
            {
                "id": payload.get("full_name"),
                "title": payload.get("full_name"),
                "url": payload.get("html_url"),
                "summary": payload.get("description"),
                "author": (payload.get("owner") or {}).get("login"),
                "stars": payload.get("stargazers_count"),
                "forks": payload.get("forks_count"),
                "watchers": payload.get("subscribers_count"),
                "language": payload.get("language"),
                "topics": payload.get("topics", []),
                "license": license_info.get("spdx_id") or license_info.get("name"),
                "last_modified": payload.get("updated_at"),
                "created_at": payload.get("created_at"),
                "notes": item.get("notes"),
            }
        )

    return {
        "source": "github_curated_ai_repos",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": records,
    }
