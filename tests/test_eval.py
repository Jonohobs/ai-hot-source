"""Self-eval tests — verify routing classification against test vectors."""

import unittest
from pathlib import Path

import yaml

from src.routing.scorer import classify_task

EVAL_DIR = Path(__file__).parent / "eval_cases"


class TestRoutingEval(unittest.TestCase):
    """Parameterised tests from YAML eval cases."""

    @classmethod
    def setUpClass(cls):
        cls.cases = []
        for yaml_file in EVAL_DIR.glob("*.yaml"):
            with open(yaml_file) as f:
                cls.cases.extend(yaml.safe_load(f))

    def test_eval_cases_loaded(self):
        self.assertGreater(len(self.cases), 0, "No eval cases found")

    def test_routing_classification(self):
        failures = []
        for case in self.cases:
            task = classify_task(case["input"])

            if task.task_type != case["expect_type"]:
                failures.append(
                    f"  {case['name']}: expected type={case['expect_type']}, got={task.task_type}"
                )
            if task.needs_vision != case["expect_vision"]:
                failures.append(
                    f"  {case['name']}: expected vision={case['expect_vision']}, got={task.needs_vision}"
                )
            if task.needs_tools != case["expect_tools"]:
                failures.append(
                    f"  {case['name']}: expected tools={case['expect_tools']}, got={task.needs_tools}"
                )

        if failures:
            pass_count = len(self.cases) * 3 - len(failures)
            total = len(self.cases) * 3
            msg = f"\n{len(failures)}/{total} assertions failed:\n" + "\n".join(failures)
            self.fail(msg)


if __name__ == "__main__":
    unittest.main()
