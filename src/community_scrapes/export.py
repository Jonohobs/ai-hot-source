from __future__ import annotations

from copy import deepcopy


PUBLIC_TOP_LEVEL_FIELDS = (
    "source",
    "generated_at",
    "record_count",
    "records",
)

DEFAULT_PUBLIC_RECORD_FIELDS = (
    "id",
    "title",
    "author",
    "authors",
    "url",
    "summary",
    "notes",
    "published",
    "last_modified",
    "pipeline_tag",
    "downloads",
    "likes",
    "stars",
    "forks",
    "watchers",
    "language",
    "license",
    "primary_category",
    "categories",
    "tags",
    "topics",
)

PRIVATE_ONLY_RECORD_FIELDS = (
    "private_notes",
    "private_tags",
    "internal_notes",
    "internal_tags",
    "risk_notes",
    "trust_notes",
    "routing_notes",
    "benchmark_notes",
    "local_benchmark",
    "safety_notes",
    "review_status",
    "red_flags",
)


def sanitize_snapshot(snapshot: dict, *, public_record_fields: tuple[str, ...] | None = None) -> dict:
    allowed_record_fields = tuple(public_record_fields or DEFAULT_PUBLIC_RECORD_FIELDS)
    clean = {key: deepcopy(snapshot[key]) for key in PUBLIC_TOP_LEVEL_FIELDS if key in snapshot}
    records = []

    for record in snapshot.get("records", []):
        clean_record = {
            key: deepcopy(value)
            for key, value in record.items()
            if key in allowed_record_fields and key not in PRIVATE_ONLY_RECORD_FIELDS
        }
        records.append(clean_record)

    clean["records"] = records
    clean["record_count"] = len(records)
    return clean
