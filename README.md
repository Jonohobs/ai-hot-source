# AI Hot Source

Useful public metadata for builders.

This is an unofficial, community-maintained project for OpenClaw builders and adjacent agent tooling communities. It collects small, regularly updated snapshots of public AI and computer-useful sources.

This project is an index and discovery layer, not a content mirror. The goal is to provide useful blurbs and metadata that point back to the original source.

Compliance matters here. The project should prefer official APIs and public metadata, not brittle or adversarial scraping. Read `COMPLIANCE.md` before adding sources.

Code in this repo is MIT licensed. Upstream data and source content remain subject to source-specific terms.

## Just browsing?

You do not need to run any code to use this repo.

If you just want to explore:

- start with [START_HERE.md](./START_HERE.md)
- open [data/index.md](./data/index.md) to see the latest source list
- click through to the text snapshots you want to read

The `src/` folder is only there to generate and update the data.

## V1 scope

- `arxiv_cs_ai_recent`: recent papers from arXiv categories commonly useful for AI/computer-use work.
- `huggingface_trending_models`: popular public Hugging Face models with core metadata.

Outputs land in `data/<source>/latest.json`.
`data/index.md` provides a quick browseable catalog of the latest snapshots.
`data/index.json` remains available for tools and scripts.

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

- `data/index.md`: browseable summary for people reading on GitHub.
- `data/index.json`: machine-friendly summary for tools.
- `data/<source>/latest.md`: human-readable snapshot for each source.
- `data/<source>/latest.json`: full current snapshot for that source.

## Automation

`.github/workflows/update-data.yml` refreshes the data on a schedule and can commit updated snapshots back to the repo.

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

Maintained by Jonathan Hobman / DTR Labs Ltd.
