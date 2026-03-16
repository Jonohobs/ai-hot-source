"""Tests for the KPI library."""

import json
from pathlib import Path

import pytest

from src.kpi.models import KPIDefinition, FormulaDefinition, Benchmark, DataType, Direction
from src.kpi.catalog import KPICatalog
from src.kpi.formula_engine import evaluate_formula
from src.kpi.taxonomy import ALL_DOMAINS, ALL_SUBDOMAINS, list_domains
from src.kpi.validation import validate_kpi

BUILTIN_PATH = Path(__file__).parent.parent / "src" / "kpi" / "builtin"


# --- Models ---

def test_kpi_basic():
    kpi = KPIDefinition(
        slug="test_kpi",
        name="Test KPI",
        description="A test",
        domain="engineering",
        data_type=DataType.INTEGER,
        direction=Direction.HIGHER_BETTER,
    )
    assert kpi.slug == "test_kpi"
    assert kpi.is_custom is False


def test_slug_validation():
    with pytest.raises(ValueError, match="snake_case"):
        KPIDefinition(
            slug="BadSlug",
            name="Bad",
            description="Bad slug",
            domain="engineering",
            data_type=DataType.INTEGER,
            direction=Direction.HIGHER_BETTER,
        )


def test_percentage_requires_formula():
    with pytest.raises(ValueError, match="must have a formula"):
        KPIDefinition(
            slug="no_formula_pct",
            name="No Formula",
            description="Missing formula",
            domain="marketing",
            data_type=DataType.PERCENTAGE,
            direction=Direction.HIGHER_BETTER,
        )


def test_percentage_with_formula():
    kpi = KPIDefinition(
        slug="conv_rate",
        name="Conversion Rate",
        description="Test",
        domain="marketing",
        data_type=DataType.PERCENTAGE,
        direction=Direction.HIGHER_BETTER,
        formula=FormulaDefinition(
            expression="(conversions / visitors) * 100",
            variables={"conversions": "Number of conversions", "visitors": "Total visitors"},
            unit="%",
        ),
    )
    assert kpi.formula is not None


# --- Formula Engine ---

def test_formula_eval_simple():
    f = FormulaDefinition(
        expression="a / b",
        variables={"a": "numerator", "b": "denominator"},
    )
    assert evaluate_formula(f, {"a": 10, "b": 2}) == 5.0


def test_formula_eval_percentage():
    f = FormulaDefinition(
        expression="(conversions / visitors) * 100",
        variables={"conversions": "conv", "visitors": "vis"},
    )
    result = evaluate_formula(f, {"conversions": 50, "visitors": 1000})
    assert result == 5.0


def test_formula_missing_variable():
    f = FormulaDefinition(
        expression="a + b",
        variables={"a": "x", "b": "y"},
    )
    with pytest.raises(ValueError, match="Missing"):
        evaluate_formula(f, {"a": 1})


def test_formula_division_by_zero():
    f = FormulaDefinition(
        expression="a / b",
        variables={"a": "x", "b": "y"},
    )
    with pytest.raises(ValueError, match="division by zero"):
        evaluate_formula(f, {"a": 1, "b": 0})


def test_formula_functions():
    f = FormulaDefinition(
        expression="sqrt(a)",
        variables={"a": "input"},
    )
    assert evaluate_formula(f, {"a": 9}) == 3.0


# --- Taxonomy ---

def test_domains_exist():
    assert "engineering" in ALL_DOMAINS
    assert "saas" in ALL_DOMAINS
    assert "gaming" in ALL_DOMAINS


def test_subdomains_exist():
    assert "dora" in ALL_SUBDOMAINS
    assert "monetization" in ALL_SUBDOMAINS


def test_list_domains():
    domains = list_domains()
    assert len(domains) >= 9
    keys = [d["key"] for d in domains]
    assert "marketing" in keys


# --- Catalog ---

def test_catalog_load_builtin():
    catalog = KPICatalog.from_directory(BUILTIN_PATH)
    assert catalog.count() > 0


def test_catalog_search():
    catalog = KPICatalog.from_directory(BUILTIN_PATH)
    results = list(catalog.search(domain="engineering"))
    assert len(results) > 0
    assert all(k.domain == "engineering" for k in results)


def test_catalog_get():
    catalog = KPICatalog.from_directory(BUILTIN_PATH)
    # Try to get any KPI
    all_kpis = catalog.all()
    if all_kpis:
        slug = all_kpis[0].slug
        assert catalog.get(slug) is not None


def test_catalog_export():
    catalog = KPICatalog.from_directory(BUILTIN_PATH)
    exported = catalog.export_all()
    data = json.loads(exported)
    assert isinstance(data, list)


# --- Validation ---

def test_validate_good_kpi():
    catalog = KPICatalog()
    kpi = KPIDefinition(
        slug="test_valid",
        name="Test",
        description="Valid test KPI",
        domain="engineering",
        subdomain="quality",
        data_type=DataType.INTEGER,
        direction=Direction.HIGHER_BETTER,
    )
    errors = validate_kpi(kpi, catalog)
    assert errors == []


def test_validate_bad_domain():
    catalog = KPICatalog()
    kpi = KPIDefinition(
        slug="test_bad",
        name="Test",
        description="Bad domain",
        domain="nonexistent",
        data_type=DataType.INTEGER,
        direction=Direction.HIGHER_BETTER,
    )
    errors = validate_kpi(kpi, catalog)
    assert any("Unknown domain" in e for e in errors)


def test_validate_benchmark_order():
    catalog = KPICatalog()
    kpi = KPIDefinition(
        slug="test_bench",
        name="Test",
        description="Bad benchmarks",
        domain="engineering",
        data_type=DataType.INTEGER,
        direction=Direction.HIGHER_BETTER,
        benchmark=Benchmark(poor=90, acceptable=50, good=30, excellent=10),
    )
    errors = validate_kpi(kpi, catalog)
    assert any("ascending" in e for e in errors)


# --- Builtin KPI file validation ---

def test_all_builtin_kpis_valid():
    """Every JSON file in builtin/ must parse and validate."""
    catalog = KPICatalog.from_directory(BUILTIN_PATH)
    for kpi in catalog.all():
        errors = validate_kpi(kpi, catalog)
        assert errors == [], f"{kpi.slug} has validation errors: {errors}"
