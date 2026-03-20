# MCP Market Capture

This repo includes a small MCP Market capture pipeline with two entry points that write the same record format.

```bash
python sauce.py scrape-mcpmarket --pages 1 --limit 10
python sauce.py import-mcpmarket-capture path/to/mcpmarket-server_firecrawl.json
```

Normalized output lands in `data/mcpmarket/servers.jsonl` by default.

## Chrome Extension

- Path: `chrome-extension/mcpmarket-capture/`
- Load it via `chrome://extensions` -> Developer mode -> Load unpacked
- Open `mcpmarket.com`, browse normally so network captures fire, then use the popup to export JSON
- Import that export back into the archive with `import-mcpmarket-capture`

Use this as a starting point. Then keep the parts that are useful for your setup.
