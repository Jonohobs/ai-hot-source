from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .arxiv import run as run_arxiv
from .huggingface import run as run_huggingface


@dataclass(frozen=True)
class Source:
    id: str
    description: str
    run: Callable[[], dict]


SOURCES = {
    "arxiv_cs_ai_recent": Source(
        id="arxiv_cs_ai_recent",
        description="Recent arXiv metadata for selected CS/AI categories.",
        run=run_arxiv,
    ),
    "huggingface_trending_models": Source(
        id="huggingface_trending_models",
        description="Popular public Hugging Face model metadata.",
        run=run_huggingface,
    ),
}
