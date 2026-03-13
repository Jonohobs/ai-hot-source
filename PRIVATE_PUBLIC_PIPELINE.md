# Private / Public Pipeline

This repo can be used as the public layer of a two-stage scrape system:

1. `private scrape system`
2. `public export system`

## Why split them

Private scrape layer can keep:

- raw or noisy findings
- internal ranking notes
- trust/risk assessments
- benchmark notes
- routing or safety decisions
- pre-publication review status

Public export should keep only:

- neutral metadata
- public summaries
- links back to original sources
- safe, browseable records

## Current flow

Use `--output-root` for the private snapshot directory and `--public-root` for the sanitized export directory.

Example:

```bash
python -m community_scrapes --all --output-root private_data --public-root data
```

This produces:

- `private_data/`: fuller internal snapshots
- `data/`: sanitized public snapshots

## Sanitization rules

Public export keeps only allowlisted fields per source.

Examples of fields that should stay private:

- `private_notes`
- `internal_notes`
- `risk_notes`
- `trust_notes`
- `routing_notes`
- `benchmark_notes`
- `local_benchmark`
- `safety_notes`
- `review_status`
- `red_flags`

## Recommended architecture

- keep a private upstream repo or local workspace for full scrape + review
- export only approved snapshots into this public repo
- use the same source ids and normalized record shape across both layers

## Model catalog use

For model discovery:

- let the private layer hold raw model findings, benchmark notes, and trust/risk tags
- let the public layer publish cleaned catalog snapshots with neutral metadata only
