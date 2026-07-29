from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
sys.path.insert(0, str(PLUGIN / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "personal_harness_eval_routing",
    PLUGIN / "scripts" / "eval_routing.py",
)
assert SPEC and SPEC.loader
EVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVAL)


SCENARIOS = ROOT / "evals" / "real-usage" / "scenarios.json"


@unittest.skipUnless(
    SCENARIOS.is_file(),
    "실사용 라벨에는 프로젝트·클라이언트 이름이 있어 배포본에는 포함하지 않습니다",
)
class RoutingEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = EVAL.load_scenarios()

    def test_scenarios_are_well_formed(self) -> None:
        skills = set(EVAL.installed_skills(PLUGIN))
        self.assertEqual([], EVAL.validate_scenarios(self.payload, skills))

    def test_scenario_set_covers_every_skill_and_abstains(self) -> None:
        routed = [
            scenario
            for scenario in self.payload["scenarios"]
            if scenario.get("mode", "route") == "route"
        ]
        abstained = [
            scenario
            for scenario in self.payload["scenarios"]
            if scenario.get("mode") == "abstain"
        ]
        expected = {
            name
            for scenario in routed
            for name in scenario.get("expect", [])
        }

        self.assertEqual(set(EVAL.installed_skills(PLUGIN)), expected)
        self.assertGreaterEqual(len(abstained), 8)
        self.assertGreaterEqual(len(routed), 30)

    def test_real_usage_routing_scores_full_marks(self) -> None:
        report = EVAL.evaluate(self.payload)
        self.assertEqual(
            [],
            [failure["id"] for failure in report["failures"]],
            EVAL.format_report(report),
        )
        self.assertEqual(100.0, report["score"])

    def test_eval_detects_a_regressed_route(self) -> None:
        payload = {
            "scenarios": [
                {
                    "id": "guard",
                    "source": "regression guard",
                    "prompt": "점심 뭐 먹을지 골라줘.",
                    "expect": ["audit-marketing-report"],
                }
            ]
        }
        report = EVAL.evaluate(payload)

        self.assertEqual(1, report["scenarios"]["failed"])
        self.assertLess(report["score"], 100.0)

    def test_scenario_file_rejects_unknown_skill_labels(self) -> None:
        payload = json.loads(json.dumps(self.payload))
        payload["scenarios"][0]["expect"] = ["no-such-skill"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenarios.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            errors = EVAL.validate_scenarios(
                EVAL.load_scenarios(path),
                set(EVAL.installed_skills(PLUGIN)),
            )

        self.assertTrue(any("no-such-skill" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
