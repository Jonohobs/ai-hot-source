# Compliance Notes

This repo is intended to stay on the conservative side of scraping and data collection.

## Rules

1. Prefer official APIs, feeds, exports, or clearly public machine-readable endpoints.
2. Prefer metadata over full-content replication.
3. Treat this repo as an index that points back to sources, not a mirror of the sources themselves.
4. Do not bypass auth walls, paywalls, CAPTCHAs, rate limits, or access controls.
5. Do not scrape private communities, logged-in surfaces, or anything that reasonably expects membership-only access.
6. Check site terms before adding a new source. If the terms are unclear, do not automate it until reviewed.
7. Keep request volume low and send a clear user agent.
8. Revisit a source if its access rules, terms, or practical fit appear to have changed.

## Current v1 sources

- `arxiv_cs_ai_recent`
  - Access path: arXiv public API feed.
  - Risk profile: low.
  - Data shape: paper metadata only, with source summary and canonical paper link.

- `huggingface_trending_models`
  - Access path: Hugging Face public models API.
  - Risk profile: low.
  - Data shape: repository metadata only, with tags and canonical model link.

## Out of scope

- Discord scraping without explicit permission or an official compliant export path.
- Republishing full article bodies, paid content, or gated model artifacts.
- Building a shadow archive of full source content when source links and short blurbs would do.
- Aggressive crawling of HTML pages when a public feed or API exists.

## Review checklist for new sources

- Is there an official API/feed/export?
- Are we collecting only what we need?
- Are we linking back to the canonical source instead of mirroring it?
- Would a reasonable site operator expect this access pattern?
- Does the source require login, membership, or circumvention?
- Is the update cadence polite for the target service?

If any answer is uncomfortable, do not add the source yet.
