"""Validation for KPI definitions beyond schema checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Direction
from .taxonomy import ALL_DOMAINS, ALL_SUBDOMAINS

if TYPE_CHECKING:
    from .catalog import KPICatalog
    from .models import KPIDefinition


def validate_kpi(kpi: "KPIDefinition", catalog: "KPICatalog") -> list[str]:
    errors: list[str] = []

    # Taxonomy
    if kpi.domain not in ALL_DOMAINS:
        errors.append(f"Unknown domain: {kpi.domain}")
    if kpi.subdomain and kpi.subdomain not in ALL_SUBDOMAINS:
        errors.append(f"Unknown subdomain: {kpi.subdomain}")

    # Referential integrity
    for slug in kpi.related_kpis:
        if not catalog.get(slug):
            errors.append(f"related_kpi '{slug}' not found in catalog")

    # Formula variable completeness
    if kpi.formula and kpi.formula.example:
        missing = set(kpi.formula.variables) - set(kpi.formula.example)
        if missing:
            errors.append(f"Formula example missing variables: {missing}")

    # Benchmark consistency
    if kpi.benchmark:
        vals = [
            v
            for v in [
                kpi.benchmark.poor,
                kpi.benchmark.acceptable,
                kpi.benchmark.good,
                kpi.benchmark.excellent,
            ]
            if v is not None
        ]
        if len(vals) >= 2:
            if kpi.direction == Direction.HIGHER_BETTER and vals != sorted(vals):
                errors.append("Benchmarks must be ascending for higher_is_better")
            if kpi.direction == Direction.LOWER_BETTER and vals != sorted(vals, reverse=True):
                errors.append("Benchmarks must be descending for lower_is_better")

    return errors
