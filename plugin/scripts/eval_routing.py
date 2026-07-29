#!/usr/bin/env python3
"""Deterministic real-usage evaluation for ADX Harness skill routing.

Scenarios are authored expectations, not hook observations. Each scenario is
scored on independent checks so a failure names the exact defect:

- ``hit``: every expected skill was selected
- ``clean``: no forbidden skill was selected
- ``tight``: no skill outside ``expect`` + ``accept`` was selected
- ``silent``: abstain scenarios select nothing
- ``quiet``: abstain scenarios keep the review list empty too

Score is the share of passed checks. Full marks means 100.0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_router import installed_skills, route_prompt  # noqa: E402


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
# The scenario set is development evidence, so it lives beside the plugin rather
# than inside it. An installed copy has no `evals/` and degrades to "no set".
DEFAULT_SCENARIOS = next(
    (
        candidate
        for candidate in (
            PLUGIN_ROOT.parent / "evals" / "real-usage" / "scenarios.json",
            PLUGIN_ROOT / "evals" / "real-usage" / "scenarios.json",
        )
        if candidate.is_file()
    ),
    PLUGIN_ROOT.parent / "evals" / "real-usage" / "scenarios.json",
)


def load_scenarios(path: Path = DEFAULT_SCENARIOS) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("scenarios"), list):
        raise ValueError(f"Invalid scenario file: {path}")
    return payload


def validate_scenarios(payload: dict[str, Any], skills: set[str]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, scenario in enumerate(payload.get("scenarios", [])):
        label = str(scenario.get("id") or f"#{index}")
        if not isinstance(scenario, dict):
            errors.append(f"Scenario is not an object: {label}")
            continue
        if not scenario.get("id"):
            errors.append(f"Scenario has no id: {label}")
        if label in seen:
            errors.append(f"Duplicate scenario id: {label}")
        seen.add(label)
        if not str(scenario.get("prompt") or "").strip():
            errors.append(f"Scenario has no prompt: {label}")
        if not str(scenario.get("source") or "").strip():
            errors.append(f"Scenario has no work source: {label}")
        mode = scenario.get("mode", "route")
        if mode not in ("route", "abstain"):
            errors.append(f"Unknown scenario mode: {label}.{mode}")
        expect = scenario.get("expect", [])
        if mode == "route" and not expect:
            errors.append(f"Route scenario has no expected skill: {label}")
        if mode == "abstain" and expect:
            errors.append(f"Abstain scenario must not expect a skill: {label}")
        for key in ("expect", "accept", "forbid"):
            values = scenario.get(key, [])
            if not isinstance(values, list):
                errors.append(f"Scenario field must be a list: {label}.{key}")
                continue
            for name in values:
                if name not in skills:
                    errors.append(f"Unknown skill in {label}.{key}: {name}")
    return errors


def evaluate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    routing = route_prompt(scenario["prompt"], PLUGIN_ROOT)
    selected = [item["skill"] for item in routing["selected"]]
    review = [item["skill"] for item in routing["review"]]
    expect = list(scenario.get("expect", []))
    accept = list(scenario.get("accept", []))
    forbid = list(scenario.get("forbid", []))
    mode = scenario.get("mode", "route")

    checks: dict[str, bool] = {}
    if mode == "abstain":
        checks["silent"] = not selected
        checks["quiet"] = not review
    else:
        checks["hit"] = all(name in selected for name in expect)
        checks["clean"] = not [name for name in selected if name in forbid]
        checks["tight"] = not [
            name for name in selected if name not in expect and name not in accept
        ]

    return {
        "id": scenario["id"],
        "mode": mode,
        "source": scenario.get("source", ""),
        "prompt": scenario["prompt"],
        "expect": expect,
        "accept": accept,
        "forbid": forbid,
        "selected": selected,
        "review": review,
        "checks": checks,
        "passed": all(checks.values()),
        "detail": {item["skill"]: item["matched"] for item in routing["selected"]},
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    results = [evaluate_scenario(scenario) for scenario in payload["scenarios"]]
    checks_total = sum(len(result["checks"]) for result in results)
    checks_passed = sum(
        sum(1 for value in result["checks"].values() if value) for result in results
    )
    by_group: dict[str, dict[str, int]] = {}
    for result in results:
        group = result["source"]
        stats = by_group.setdefault(group, {"scenarios": 0, "failed": 0})
        stats["scenarios"] += 1
        if not result["passed"]:
            stats["failed"] += 1

    failures = [result for result in results if not result["passed"]]
    return {
        "score": round(100.0 * checks_passed / checks_total, 2) if checks_total else 0.0,
        "scenarios": {
            "total": len(results),
            "passed": len(results) - len(failures),
            "failed": len(failures),
        },
        "checks": {"total": checks_total, "passed": checks_passed},
        "by_source": by_group,
        "failures": failures,
        "results": results,
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [
        f"score: {report['score']:.2f} / 100",
        (
            f"scenarios: {report['scenarios']['passed']}/"
            f"{report['scenarios']['total']} passed"
        ),
        f"checks: {report['checks']['passed']}/{report['checks']['total']} passed",
    ]
    if not report["failures"]:
        lines.append("no failing scenario")
        return "\n".join(lines)
    lines.append("")
    lines.append("failures:")
    for failure in report["failures"]:
        broken = ", ".join(
            name for name, value in failure["checks"].items() if not value
        )
        lines.append(f"- {failure['id']} [{broken}] ({failure['source']})")
        lines.append(f"  prompt:   {failure['prompt']}")
        lines.append(f"  expect:   {failure['expect'] or '(none)'}")
        lines.append(f"  selected: {failure['selected'] or '(none)'}")
        if failure["mode"] == "abstain" and failure["review"]:
            lines.append(f"  review:   {failure['review']}")
        for skill, matched in failure["detail"].items():
            lines.append(f"  why {skill}: {', '.join(matched) or '(none)'}")
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS))
    result.add_argument("--fail-under", type=float, default=100.0)
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    payload = load_scenarios(Path(args.scenarios).expanduser().resolve())
    errors = validate_scenarios(payload, set(installed_skills(PLUGIN_ROOT)))
    if errors:
        for line in errors:
            print(f"ERROR {line}")
        return 1

    report = evaluate(payload)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0 if report["score"] >= args.fail_under else 1


if __name__ == "__main__":
    raise SystemExit(main())
