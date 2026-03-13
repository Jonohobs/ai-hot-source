from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .arxiv import run as run_arxiv
from .github_curated import run as run_github_curated
from .huggingface import run as run_huggingface
from .youtube import run as run_youtube


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    description: str
    run: Callable[[], dict]
    public_record_fields: tuple[str, ...] | None = None


SOURCES = {
    "arxiv_cs_ai_recent": Source(
        id="arxiv_cs_ai_recent",
        title="Recent AI/CS papers from arXiv",
        description="Recent arXiv metadata for selected CS/AI categories.",
        run=run_arxiv,
        public_record_fields=(
            "id",
            "title",
            "url",
            "authors",
            "published",
            "summary",
            "categories",
            "notes",
        ),
    ),
    "huggingface_trending_models": Source(
        id="huggingface_trending_models",
        title="Popular public Hugging Face models",
        description="Popular public Hugging Face model metadata.",
        run=run_huggingface,
        public_record_fields=(
            "id",
            "author",
            "url",
            "pipeline_tag",
            "last_modified",
            "downloads",
            "likes",
            "tags",
        ),
    ),
    "github_curated_ai_repos": Source(
        id="github_curated_ai_repos",
        title="Curated GitHub AI repositories",
        description="Selected GitHub repositories that curate AI tools, lists, and data resources.",
        run=run_github_curated,
        public_record_fields=(
            "id",
            "title",
            "url",
            "summary",
            "stars",
            "forks",
            "watchers",
            "language",
            "license",
            "topics",
            "notes",
        ),
    ),
    "youtube_watch_videos": Source(
        id="youtube_watch_videos",
        title="Curated YouTube videos",
        description="Curated YouTube video metadata from public oEmbed responses.",
        run=run_youtube,
        public_record_fields=(
            "id",
            "title",
            "author",
            "url",
            "published",
            "summary",
            "notes",
            "tags",
        ),
    ),
}
