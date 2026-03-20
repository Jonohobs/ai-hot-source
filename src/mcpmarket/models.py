from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class MCPServerRecord:
    source: str
    source_url: str
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    website_url: str | None = None
    github_url: str | None = None
    pricing: str | None = None
    verified: bool | None = None
    capture_method: str = "unknown"
    captured_at: str = field(default_factory=utc_now_iso)
    raw: dict = field(default_factory=dict)

    def record_key(self) -> str:
        if self.slug:
            return self.slug
        return self.source_url

    def to_dict(self) -> dict:
        return asdict(self)
