"""CLI for the KPI library — query, validate, evaluate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .catalog import KPICatalog
from .formula_engine import evaluate_formula
from .models import KPIDefinition
from .taxonomy import list_domains
from .validation import validate_kpi

BUILTIN_PATH = Path(__file__).parent / "builtin"
USER_PATH = Path.home() / ".kpicatalog" / "user"


def _load_catalog() -> KPICatalog:
    catalog = KPICatalog.from_directory(BUILTIN_PATH)
    if USER_PATH.exists():
        try:
            catalog.merge(KPICatalog.from_directory(USER_PATH))
        except Exception as e:
            print(f"[warn] Error loading user KPIs: {e}", file=sys.stderr)
    return catalog


def _print_table(kpis: list[KPIDefinition]) -> None:
    if not kpis:
        print("No KPIs found.")
        return
    # Header
    print(f"{'SLUG':<30} {'NAME':<35} {'DOMAIN':<20} {'TYPE':<12} {'DIRECTION'}")
    print("-" * 110)
    for k in kpis:
        dom = f"{k.domain}/{k.subdomain}" if k.subdomain else k.domain
        print(f"{k.slug:<30} {k.name:<35} {dom:<20} {k.data_type.value:<12} {k.direction.value}")
    print(f"\n{len(kpis)} KPI(s) found.")


def cmd_list(args: list[str]) -> None:
    catalog = _load_catalog()
    domain = ""
    subdomain = ""
    query = ""
    tags: list[str] = []
    output_json = False

    i = 0
    while i < len(args):
        if args[i] in ("-d", "--domain") and i + 1 < len(args):
            domain = args[i + 1]; i += 2
        elif args[i] in ("-s", "--subdomain") and i + 1 < len(args):
            subdomain = args[i + 1]; i += 2
        elif args[i] in ("-q", "--query") and i + 1 < len(args):
            query = args[i + 1]; i += 2
        elif args[i] in ("-t", "--tag") and i + 1 < len(args):
            tags.append(args[i + 1]); i += 2
        elif args[i] == "--json":
            output_json = True; i += 1
        else:
            query = args[i]; i += 1

    results = list(catalog.search(query=query, domain=domain, subdomain=subdomain, tags=tags or None))

    if output_json:
        print(json.dumps([k.model_dump(mode="json") for k in results], indent=2, default=str))
    else:
        _print_table(results)


def cmd_show(args: list[str]) -> None:
    if not args:
        print("Usage: kpi show <slug>", file=sys.stderr)
        return
    catalog = _load_catalog()
    kpi = catalog.get(args[0])
    if not kpi:
        print(f"KPI '{args[0]}' not found.", file=sys.stderr)
        return
    print(kpi.model_dump_json(indent=2))


def cmd_calc(args: list[str]) -> None:
    if len(args) < 2:
        print("Usage: kpi calc <slug> var1=val1 var2=val2 ...", file=sys.stderr)
        return
    catalog = _load_catalog()
    kpi = catalog.get(args[0])
    if not kpi or not kpi.formula:
        print(f"KPI '{args[0]}' not found or has no formula.", file=sys.stderr)
        return

    values: dict[str, float] = {}
    for pair in args[1:]:
        if "=" not in pair:
            print(f"Invalid value pair: {pair} (expected key=value)", file=sys.stderr)
            return
        k, v = pair.split("=", 1)
        values[k] = float(v)

    result = evaluate_formula(kpi.formula, values)
    unit = kpi.formula.unit or ""
    print(f"{kpi.name}: {result:.4f} {unit}")

    # Show benchmark comparison if available
    if kpi.benchmark:
        b = kpi.benchmark
        thresholds = []
        if b.excellent is not None:
            thresholds.append(("excellent", b.excellent))
        if b.good is not None:
            thresholds.append(("good", b.good))
        if b.acceptable is not None:
            thresholds.append(("acceptable", b.acceptable))
        if b.poor is not None:
            thresholds.append(("poor", b.poor))
        if thresholds:
            print(f"Benchmarks: {', '.join(f'{n}={v}' for n, v in thresholds)}")


def cmd_domains(args: list[str]) -> None:
    for d in list_domains():
        subs = ", ".join(d["subdomains"])
        print(f"  {d['key']:<15} {d['label']:<15} [{subs}]")


def cmd_validate(args: list[str]) -> None:
    if not args:
        print("Usage: kpi validate <json_file>", file=sys.stderr)
        return
    path = Path(args[0])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return

    catalog = _load_catalog()
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        kpi = KPIDefinition.model_validate(data)
    except Exception as e:
        print(f"FAIL (schema): {e}", file=sys.stderr)
        return

    errors = validate_kpi(kpi, catalog)
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
    else:
        print(f"OK: {kpi.slug} is valid")


def cmd_add(args: list[str]) -> None:
    if not args:
        print("Usage: kpi add <json_file>", file=sys.stderr)
        return
    path = Path(args[0])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return

    catalog = _load_catalog()
    data = json.loads(path.read_text(encoding="utf-8"))
    kpi = KPIDefinition.model_validate(data)

    errors = validate_kpi(kpi, catalog)
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return

    USER_PATH.mkdir(parents=True, exist_ok=True)
    dest = USER_PATH / f"{kpi.slug}.json"
    dest.write_text(kpi.model_dump_json(indent=2), encoding="utf-8")
    print(f"Added: {kpi.slug} -> {dest}")


def cmd_stats(args: list[str]) -> None:
    catalog = _load_catalog()
    print(f"Total KPIs: {catalog.count()}")
    print(f"Domains: {', '.join(catalog.domains())}")
    for domain in catalog.domains():
        count = len(list(catalog.search(domain=domain)))
        print(f"  {domain}: {count}")


COMMANDS = {
    "list": cmd_list,
    "ls": cmd_list,
    "show": cmd_show,
    "calc": cmd_calc,
    "domains": cmd_domains,
    "validate": cmd_validate,
    "add": cmd_add,
    "stats": cmd_stats,
}


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("KPI Library — structured KPI catalog")
        print()
        print("Commands:")
        print("  list [--domain X] [--query X] [--json]  List/filter KPIs")
        print("  show <slug>                              Show full KPI definition")
        print("  calc <slug> var=val ...                  Evaluate a formula")
        print("  domains                                  List all domains")
        print("  validate <file.json>                     Validate a KPI file")
        print("  add <file.json>                          Add custom KPI")
        print("  stats                                    Catalog statistics")
        return

    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}. Try --help", file=sys.stderr)
        sys.exit(1)

    COMMANDS[cmd](args[1:])


if __name__ == "__main__":
    main()
