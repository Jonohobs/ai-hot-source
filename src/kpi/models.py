"""KPI data models — Pydantic v2."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DataType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    RATIO = "ratio"
    BOOLEAN = "boolean"
    DURATION = "duration"
    SCORE = "score"


class Direction(str, Enum):
    HIGHER_BETTER = "higher_is_better"
    LOWER_BETTER = "lower_is_better"
    TARGET = "target_based"


class FormulaDefinition(BaseModel):
    expression: str
    variables: dict[str, str]
    unit: Optional[str] = None
    example: Optional[dict[str, float]] = None


class Benchmark(BaseModel):
    poor: Optional[float] = None
    acceptable: Optional[float] = None
    good: Optional[float] = None
    excellent: Optional[float] = None
    source: Optional[str] = None
    industry: Optional[str] = None


class KPIDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str
    name: str
    description: str
    domain: str
    subdomain: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    data_type: DataType
    direction: Direction
    formula: Optional[FormulaDefinition] = None
    benchmark: Optional[Benchmark] = None

    aliases: list[str] = Field(default_factory=list)
    related_kpis: list[str] = Field(default_factory=list)
    data_sources: list[str] = Field(default_factory=list)
    owner: Optional[str] = None
    cadence: Optional[str] = None  # daily, weekly, monthly, quarterly

    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=__import__("datetime").timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=__import__("datetime").timezone.utc))
    is_custom: bool = False

    @field_validator("slug")
    @classmethod
    def slug_must_be_snake_case(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("slug must be lowercase snake_case")
        return v

    @model_validator(mode="after")
    def formula_required_for_ratio_types(self) -> "KPIDefinition":
        if self.data_type in (DataType.RATIO, DataType.PERCENTAGE) and not self.formula:
            raise ValueError(f"{self.data_type} KPIs must have a formula")
        return self
