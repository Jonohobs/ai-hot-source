# AI Hot Source

Useful public metadata for builders.

New here? Start with [START_HERE.md](./START_HERE.md).

This is an unofficial, community-maintained project for open source builders and adjacent agent tooling communities. It collects small, regularly updated snapshots of public AI and computer-useful sources.

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

- Recent AI/CS papers from arXiv
- Popular public Hugging Face models
- Curated YouTube videos with lightweight public metadata and links back to the original videos

Outputs land in `data/<source>/latest.json`.
`data/index.md` provides a quick browseable catalog of the latest snapshots.
`data/index.json` remains available for tools and scripts.

## Update the data

Only needed if you want to refresh the snapshots or add new sources.

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

## Contribute a Source

If you know a source that belongs here, open an issue or PR with:

- what it is
- why it is worth including
- the source URL
- how you would collect the metadata

The best additions are easy to browse, genuinely useful, and a good fit for `COMPLIANCE.md`.

## Project context

This project is independent and unofficial. It is meant to be useful to open source builders without implying endorsement or ownership by any upstream project or maintainer.

Maintained by Jonathan Hobman / DTR Labs Ltd.
