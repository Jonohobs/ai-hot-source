from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from .models import MCPServerRecord

SERVER_PATH_RE = re.compile(r"^/server/([^/?#]+)")
JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
META_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?P<key>[^"\']+)["\'][^>]+content=["\'](?P<value>[^"\']*)["\']',
    re.IGNORECASE,
)
TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
ANCHOR_RE = re.compile(
    r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TEXT_TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = html.unescape(TEXT_TAG_RE.sub(" ", value))
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def _slug_from_url(url: str) -> str | None:
    match = SERVER_PATH_RE.match(urlparse(url).path)
    return match.group(1) if match else None


class _ServerLinkExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        parsed = urlparse(href)
        if SERVER_PATH_RE.match(parsed.path or ""):
            self.links.add(urljoin(self.base_url, href))


def extract_server_links(html_text: str, base_url: str = "https://mcpmarket.com") -> list[str]:
    parser = _ServerLinkExtractor(base_url)
    parser.feed(html_text)
    return sorted(parser.links)


def _iter_json_nodes(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _iter_json_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_json_nodes(item)


def _extract_json_ld_objects(html_text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for block in JSON_LD_RE.findall(html_text):
        try:
            data = json.loads(html.unescape(block))
        except json.JSONDecodeError:
            continue
        for node in _iter_json_nodes(data):
            objects.append(node)
    return objects


def parse_detail_page(html_text: str, source_url: str) -> MCPServerRecord:
    meta = {m.group("key").lower(): html.unescape(m.group("value")) for m in META_RE.finditer(html_text)}
    title_match = TITLE_RE.search(html_text)
    title = _clean_text(title_match.group(1)) if title_match else None
    description = _clean_text(meta.get("description") or meta.get("og:description"))
    github_url = None
    website_url = None
    slug = _slug_from_url(source_url)
    tag_values: list[str] = []

    for match in ANCHOR_RE.finditer(html_text):
        href = html.unescape(match.group("href"))
        label = (_clean_text(match.group("label")) or "").lower()
        if "github.com" in href and github_url is None:
            github_url = href
        elif href.startswith("http") and "mcpmarket.com" not in href and website_url is None:
            website_url = href
        if label and len(label) <= 32 and label not in {"github", "website", "visit", "official"}:
            tag_values.append(label)

    categories: list[str] = []
    pricing = None
    verified = None
    raw_payload: dict[str, Any] = {}

    for obj in _extract_json_ld_objects(html_text):
        raw_payload.setdefault("json_ld", []).append(obj)
        title = title or obj.get("name") or obj.get("headline")
        description = description or _clean_text(obj.get("description"))
        slug = slug or _slug_from_url(obj.get("url", "")) if isinstance(obj.get("url"), str) else slug
        same_as = obj.get("sameAs")
        if isinstance(same_as, str) and "github.com" in same_as and not github_url:
            github_url = same_as
        elif isinstance(same_as, list):
            for candidate in same_as:
                if isinstance(candidate, str) and "github.com" in candidate and not github_url:
                    github_url = candidate
        keywords = obj.get("keywords")
        if isinstance(keywords, str):
            categories.extend([part.strip() for part in keywords.split(",") if part.strip()])
        elif isinstance(keywords, list):
            categories.extend([str(part).strip() for part in keywords if str(part).strip()])

    title = title or _clean_text(meta.get("og:title")) or slug

    for key, value in meta.items():
        lowered = key.lower()
        if "category" in lowered:
            categories.extend([part.strip() for part in value.split(",") if part.strip()])
        if "price" in lowered and not pricing:
            pricing = value
        if "verified" in lowered:
            verified = value.lower() in {"true", "1", "yes"}

    categories = sorted({item for item in categories if item})
    tags = sorted({item for item in tag_values if item and item != (title or "").lower()})

    raw_payload["meta"] = meta
    return MCPServerRecord(
        source="mcpmarket",
        source_url=source_url,
        slug=slug,
        title=title,
        description=description,
        categories=categories,
        tags=tags,
        website_url=website_url,
        github_url=github_url,
        pricing=pricing,
        verified=verified,
        capture_method="html",
        raw=raw_payload,
    )
