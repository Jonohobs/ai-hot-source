# AI Hot Sauce Community Scrapes

Lightweight, regularly updated datasets for AI and computer-useful public sources.

This is an unofficial, community-maintained repo for OpenClaw builders and adjacent agent tooling communities. It focuses on practical metadata feeds that are easy to plug into agents, dashboards, and local tooling. The emphasis is on structured, timestamped outputs rather than raw dumps.

DTR Labs Ltd

This project is an index and discovery layer, not a content mirror. The goal is to provide useful blurbs and metadata that point back to the original source.

Compliance matters here. The project should prefer official APIs and public metadata, not brittle or adversarial scraping. Read `COMPLIANCE.md` before adding sources.

Code in this repo is MIT licensed. Upstream data and source content remain subject to source-specific terms.

## V1 scope

- `arxiv_cs_ai_recent`: recent papers from arXiv categories commonly useful for AI/computer-use work.
- `huggingface_trending_models`: popular public Hugging Face models with core metadata.

Outputs land in `data/<source>/latest.json`.
`data/index.json` provides a quick top-level catalog of the latest snapshots.

## Why this shape

- Public metadata only.
- Index, not mirror.
- Cheap to run on GitHub Actions.
- Easy to inspect and diff in git.
- Safe enough to link from a community server without shipping opaque binaries or heavy infra.
- Unofficial by design: useful to OpenClaw users without implying endorsement or ownership by OpenClaw maintainers.

## Tagline

Spicy public metadata for builders.

## Quick start

```bash
python -m community_scrapes --list
python -m community_scrapes --source arxiv_cs_ai_recent
python -m community_scrapes --all
```

If Python cannot find the package before installation, run with:

```bash
PYTHONPATH=src python -m community_scrapes --all
```

If you prefer editable installs:

```bash
pip install -e .
community-scrapes --all
```

## Output format

Each source writes a JSON document with:

- `source`
- `generated_at`
- `record_count`
- `records`

`records` are normalized per source, but remain source-aware instead of forcing an awkward universal schema.

Typical record fields should look like:

- title or identifier
- short source-provided summary or blurb
- tags/categories
- timestamps
- basic popularity metadata where available
- canonical link back to the original source

Top-level files:

- `data/index.json`: one-line-per-source summary for quick consumption.
- `data/<source>/latest.json`: full current snapshot for that source.

## Automation

`.github/workflows/update-data.yml` runs the scrapers on a schedule and can commit refreshed outputs back to the repo.

## Release

`RELEASE.md` contains a simple v1 send checklist plus suggested DM copy for the OpenClaw mod.

## Next candidates

- GitHub AI/dev repo discovery
- Papers With Code trending tasks or benchmarks
- Hacker News AI/dev stories
- curated benchmark snapshots

Candidates should pass the `COMPLIANCE.md` checklist first. In practice that means official feeds and public metadata are preferred; login-gated communities and full-content scraping are not.

## OpenClaw fit

Based on the public context available on March 11, 2026, the OpenClaw ecosystem appears to reward community-maintained resources more than centrally owned maintenance work. That makes this repo a good fit if it stays simple, useful, consistently updated, and clearly unofficial.

One concrete public signal: the maintainer response on `openclaw/community#10` was effectively "we won't own this, but we'd promote a community-maintained version." That points toward a lightweight external repo with steady updates, not a heavy platform.

Public OpenClaw repo/community signals also point in a similar direction:

- The main repo describes OpenClaw as a personal AI assistant and points builders toward Discord, docs, and ecosystem tools.
- `CONTRIBUTING.md` says small fixes can go straight to PRs, but new features should usually be discussed first.
- `CONTRIBUTING.md` points skill contributions to ClawHub, which suggests external community resources are normal as long as they are clear about scope and ownership.
