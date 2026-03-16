"""KPI catalog — load, search, and manage KPI definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from .models import KPIDefinition


class KPICatalog:
    def __init__(self) -> None:
        self._kpis: dict[str, KPIDefinition] = {}

    @classmethod
    def from_directory(cls, path: Path) -> "KPICatalog":
        catalog = cls()
        if not path.exists():
            return catalog
        for f in sorted(path.rglob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                kpi = KPIDefinition.model_validate(data)
                catalog.add(kpi)
            except Exception as e:
                print(f"[warn] Skipping {f.name}: {e}")
        return catalog

    def merge(self, other: "KPICatalog") -> None:
        for kpi in other._kpis.values():
            if kpi.slug not in self._kpis:
                self._kpis[kpi.slug] = kpi

    def add(self, kpi: KPIDefinition) -> None:
        if kpi.slug in self._kpis:
            raise ValueError(f"Duplicate slug: {kpi.slug}")
        self._kpis[kpi.slug] = kpi

    def get(self, slug: str) -> Optional[KPIDefinition]:
        return self._kpis.get(slug)

    def all(self) -> list[KPIDefinition]:
        return list(self._kpis.values())

    def count(self) -> int:
        return len(self._kpis)

    def domains(self) -> list[str]:
        return sorted({k.domain for k in self._kpis.values()})

    def search(
        self,
        query: str = "",
        domain: str = "",
        subdomain: str = "",
        tags: Optional[list[str]] = None,
        data_type: str = "",
        direction: str = "",
    ) -> Iterator[KPIDefinition]:
        q = query.lower()
        for kpi in self._kpis.values():
            if q and q not in (kpi.name + " " + kpi.description + " " + " ".join(kpi.aliases)).lower():
                continue
            if domain and kpi.domain != domain:
                continue
            if subdomain and kpi.subdomain != subdomain:
                continue
            if tags and not set(tags).issubset(set(kpi.tags)):
                continue
            if data_type and kpi.data_type != data_type:
                continue
            if direction and kpi.direction != direction:
                continue
            yield kpi

    def to_json(self, slug: str) -> str:
        kpi = self._kpis.get(slug)
        if not kpi:
            raise KeyError(f"KPI '{slug}' not found")
        return kpi.model_dump_json(indent=2)

    def export_all(self) -> str:
        return json.dumps(
            [k.model_dump(mode="json") for k in self._kpis.values()],
            indent=2,
            default=str,
        )
