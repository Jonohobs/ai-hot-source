from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .arxiv import run as run_arxiv
from .huggingface import run as run_huggingface
from .youtube import run as run_youtube


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    description: str
    run: Callable[[], dict]


SOURCES = {
    "arxiv_cs_ai_recent": Source(
        id="arxiv_cs_ai_recent",
        title="Recent AI/CS papers from arXiv",
        description="Recent arXiv metadata for selected CS/AI categories.",
        run=run_arxiv,
    ),
    "huggingface_trending_models": Source(
        id="huggingface_trending_models",
        title="Popular public Hugging Face models",
        description="Popular public Hugging Face model metadata.",
        run=run_huggingface,
    ),
    "youtube_watch_videos": Source(
        id="youtube_watch_videos",
        title="Curated YouTube videos",
        description="Curated YouTube video metadata from public oEmbed responses.",
        run=run_youtube,
    ),
}
