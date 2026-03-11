from __future__ import annotations

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from ..http import fetch_text


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
QUERY = "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.CV"
URL = (
    "https://export.arxiv.org/api/query"
    f"?search_query={QUERY}&sortBy=submittedDate&sortOrder=descending&start=0&max_results=30"
)


def _text(element: ET.Element | None, path: str) -> str:
    if element is None:
        return ""
    node = element.find(path, ATOM_NS)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def run() -> dict:
    root = ET.fromstring(fetch_text(URL))
    records = []

    for entry in root.findall("atom:entry", ATOM_NS):
        records.append(
            {
                "id": _text(entry, "atom:id"),
                "title": _text(entry, "atom:title"),
                "summary": _text(entry, "atom:summary"),
                "published": _text(entry, "atom:published"),
                "updated": _text(entry, "atom:updated"),
                "authors": [
                    _text(author, "atom:name") for author in entry.findall("atom:author", ATOM_NS)
                ],
                "categories": [
                    category.attrib.get("term", "")
                    for category in entry.findall("atom:category", ATOM_NS)
                    if category.attrib.get("term")
                ],
                "primary_category": next(
                    (
                        category.attrib.get("term", "")
                        for category in entry.findall("atom:category", ATOM_NS)
                        if category.attrib.get("term", "").startswith("cs.")
                    ),
                    "",
                ),
            }
        )

    return {
        "source": "arxiv_cs_ai_recent",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": records,
    }
