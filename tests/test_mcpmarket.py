"""Tests for MCP Market capture tooling."""

import json
import unittest
from pathlib import Path

from src.mcpmarket.models import MCPServerRecord
from src.mcpmarket.parser import extract_server_links, parse_detail_page
from src.mcpmarket.storage import MCPMarketArchive


FIXTURES = Path(__file__).parent / "fixtures"


class TestMCPMarketParser(unittest.TestCase):
    def test_extract_server_links(self):
        html = (FIXTURES / "mcpmarket_listing.html").read_text(encoding="utf-8")
        links = extract_server_links(html)
        self.assertEqual(
            links,
            [
                "https://mcpmarket.com/server/browserbase",
                "https://mcpmarket.com/server/firecrawl",
            ],
        )

    def test_parse_detail_page(self):
        html = (FIXTURES / "mcpmarket_detail.html").read_text(encoding="utf-8")
        record = parse_detail_page(html, "https://mcpmarket.com/server/firecrawl")
        self.assertEqual(record.slug, "firecrawl")
        self.assertEqual(record.title, "Firecrawl")
        self.assertIn("Web Scraping & Data Collection", record.categories)
        self.assertEqual(record.github_url, "https://github.com/firecrawl/firecrawl")
        self.assertEqual(record.website_url, "https://firecrawl.dev")


class TestMCPMarketArchive(unittest.TestCase):
    def test_upsert_records(self):
        tmp_path = Path(__file__).parent / ".tmp-mcpmarket-archive.jsonl"
        try:
            if tmp_path.exists():
                tmp_path.unlink()
            archive = MCPMarketArchive(tmp_path)
            count = archive.upsert_records([
                MCPServerRecord(
                    source="mcpmarket",
                    source_url="https://mcpmarket.com/server/firecrawl",
                    slug="firecrawl",
                    title="Firecrawl",
                )
            ])
            self.assertEqual(count, 1)

            count = archive.upsert_records([
                {
                    "source": "mcpmarket",
                    "source_url": "https://mcpmarket.com/server/firecrawl",
                    "slug": "firecrawl",
                    "title": "Firecrawl Updated",
                }
            ])
            self.assertEqual(count, 1)
            rows = archive.load_records()
            self.assertEqual(rows[0]["title"], "Firecrawl Updated")
            stored = archive.path.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(json.loads(stored)["slug"], "firecrawl")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
