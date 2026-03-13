from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "catalog.json"
POLICY_PATH = ROOT / "routing-policy.json"


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def route_for_task(task: str) -> list[dict]:
    catalog = load_catalog()
    policy = load_policy()
    task_route = next((item for item in policy["task_routes"] if item["task"] == task), None)
    if not task_route:
        return []

    model_map = {model["id"]: model for model in catalog["models"]}
    results = []
    for model_id in task_route["preferred_models"]:
        model = model_map.get(model_id)
        if model:
            results.append(model)
    return results


if __name__ == "__main__":
    for task_name in ("bulk_classification", "planning", "coding", "sensitive_reasoning", "experimental_local"):
        print(f"[{task_name}]")
        for model in route_for_task(task_name):
            print(f"- {model['id']} ({model['provider']}, {model['ops']['status']})")
