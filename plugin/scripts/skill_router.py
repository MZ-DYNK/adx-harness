#!/usr/bin/env python3
"""Deterministic, precision-first skill suggestions for ADX Harness."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "skill-routing.json"
WORD_CHAR_RE = re.compile(r"[a-z0-9_]")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FIELD_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$")


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).lower()


def contains_term(text: str, term: str) -> bool:
    normalized = normalize_text(term).strip()
    if not normalized:
        return False
    pattern = re.escape(normalized).replace(r"\ ", r"\s+")
    prefix = r"(?<![a-z0-9_])" if WORD_CHAR_RE.match(normalized[0]) else ""
    suffix = r"(?![a-z0-9_])" if WORD_CHAR_RE.match(normalized[-1]) else ""
    return re.search(prefix + pattern + suffix, text) is not None


def matching_terms(text: str, terms: Any) -> list[str]:
    if not isinstance(terms, list):
        return []
    return [str(term) for term in terms if contains_term(text, str(term))]


def matching_pairs(text: str, pairs: Any) -> list[str]:
    if not isinstance(pairs, list):
        return []
    matches: list[str] = []
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) < 2:
            continue
        if all(contains_term(text, str(term)) for term in pair):
            matches.append(" + ".join(str(term) for term in pair))
    return matches


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("routes"), list):
        raise ValueError(f"Invalid routing config: {path}")
    return payload


def skill_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        field = FIELD_RE.match(line)
        if field:
            result[field.group(1)] = field.group(2).strip("\"'")
    return result


def installed_skills(plugin_root: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return result
    for path in sorted(skills_root.glob("*/SKILL.md")):
        metadata = skill_frontmatter(path)
        name = metadata.get("name")
        if name:
            result[name] = {
                "name": name,
                "description": metadata.get("description", ""),
                "path": str(path),
            }
    return result


def explicit_skills(prompt: str, names: set[str]) -> list[str]:
    text = normalize_text(prompt)
    selected = []
    for name in sorted(names):
        if contains_term(text, f"/{name}") or contains_term(text, f"${name}"):
            selected.append(name)
    return selected


def score_route(text: str, route: dict[str, Any]) -> dict[str, Any]:
    actions = matching_terms(text, route.get("actions"))
    objects = matching_terms(text, route.get("objects"))
    strong = matching_terms(text, route.get("strong_phrases"))
    unique = matching_terms(text, route.get("unique"))
    pairs = matching_pairs(text, route.get("pairs"))
    negatives = matching_terms(text, route.get("negative"))

    # A strong or unique term usually contains its own action or object token
    # ("캠페인 전략" contains "전략", "roas" is also an object). Counting both
    # would let a single signal confirm itself, so only independent action and
    # object matches count as surrounding context.
    covered = [normalize_text(value) for value in strong + unique]
    context = bool(
        [
            term
            for term in actions + objects
            if not any(normalize_text(term) in value for value in covered)
        ]
    )

    score = 0.0
    if strong:
        score = max(score, 0.72 + min(0.08, 0.04 * (len(strong) - 1)))
    if actions and objects:
        score = max(score, 0.62)
    if pairs:
        score = max(score, 0.70 + min(0.10, 0.05 * (len(pairs) - 1)))
    if unique:
        # More evidence must never score lower than the unique term alone.
        score = max(score, 0.68)
        if context or strong or pairs:
            score += 0.22
    if strong and (context or pairs or len(strong) > 1):
        score += 0.10
    if pairs and actions and objects:
        score += 0.12
    if len(actions) > 1 and len(objects) > 1:
        score += 0.05
    if negatives:
        score -= min(0.85, 0.60 + (len(negatives) - 1) * 0.10)

    score = max(0.0, min(1.0, score))
    matched = [
        *(f"phrase:{value}" for value in strong[:2]),
        *(f"pair:{value}" for value in pairs[:2]),
        *(f"unique:{value}" for value in unique[:2]),
        *(f"action:{value}" for value in actions[:2]),
        *(f"object:{value}" for value in objects[:2]),
        *(f"negative:{value}" for value in negatives[:2]),
    ]
    return {
        "skill": str(route.get("skill") or ""),
        "score": round(score, 3),
        "priority": int(route.get("priority") or 0),
        "matched": matched,
    }


def route_prompt(
    prompt: Any,
    plugin_root: Path,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    config = load_config(config_path)
    skills = installed_skills(plugin_root)
    explicit = explicit_skills(str(prompt or ""), set(skills))
    if explicit:
        return {
            "selected": [
                {
                    "skill": name,
                    "score": 1.0,
                    "priority": 10_000,
                    "matched": ["explicit invocation"],
                    "description": skills[name]["description"],
                }
                for name in explicit
            ],
            "review": [],
            "explicit": True,
        }

    text = normalize_text(prompt)
    candidates = []
    for route in config["routes"]:
        if not isinstance(route, dict):
            continue
        name = str(route.get("skill") or "")
        if name not in skills:
            continue
        result = score_route(text, route)
        result["description"] = skills[name]["description"]
        candidates.append(result)

    candidates.sort(key=lambda item: (-item["score"], -item["priority"], item["skill"]))
    selected_threshold = float(config.get("selected_threshold", 0.82))
    review_threshold = float(config.get("review_threshold", 0.65))
    selected = [item for item in candidates if item["score"] >= selected_threshold]
    review = [
        item
        for item in candidates
        if review_threshold <= item["score"] < selected_threshold
    ]

    max_skills = int(config.get("max_skills", 2))
    absolute_max = int(config.get("absolute_max_skills", 3))
    compound_markers = (
        "한 뒤",
        "그리고",
        "그 다음",
        "then",
        " and ",
        " afterwards",
    )
    allow_three = (
        len(selected) >= 3
        and sum(1 for marker in compound_markers if marker in text) >= 2
        and all(item["score"] >= 0.90 for item in selected[:3])
    )
    limit = absolute_max if allow_three else max_skills
    return {
        "selected": selected[:limit],
        "review": review[:2],
        "explicit": False,
    }


def format_route_context(routing: dict[str, Any]) -> str:
    selected = routing.get("selected")
    if not isinstance(selected, list) or not selected:
        return ""
    labels = ", ".join(
        f"`{item['skill']}` ({float(item['score']):.2f})"
        for item in selected
        if isinstance(item, dict) and item.get("skill")
    )
    return (
        f"High-confidence skill candidates for this turn: {labels}. "
        "Use the smallest fitting set through the Skill tool before substantive "
        "work. This is a routing hint, not evidence; ignore a candidate that does "
        "not match the user's actual intent."
    )


def validate_registry(
    plugin_root: Path,
    config_path: Path = DEFAULT_CONFIG,
) -> list[str]:
    config = load_config(config_path)
    skills = installed_skills(plugin_root)
    errors: list[str] = []
    seen: set[str] = set()
    for route in config["routes"]:
        if not isinstance(route, dict):
            errors.append("Route is not an object")
            continue
        name = str(route.get("skill") or "")
        if name in seen:
            errors.append(f"Duplicate route: {name}")
        seen.add(name)
        if name not in skills:
            errors.append(f"Route points to missing skill: {name}")
        if not route.get("actions") and not route.get("strong_phrases"):
            errors.append(f"Route has no action or strong phrase: {name}")
        for key in ("actions", "objects", "strong_phrases", "unique", "negative"):
            values = route.get(key, [])
            if not isinstance(values, list):
                errors.append(f"Route field must be a list: {name}.{key}")
    for name in sorted(set(skills) - seen):
        errors.append(f"Installed skill has no route: {name}")
    return errors


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("prompt")
    result.add_argument(
        "--plugin-root",
        default=str(Path(__file__).resolve().parent.parent),
    )
    result.add_argument("--config", default=str(DEFAULT_CONFIG))
    return result


def main() -> int:
    args = parser().parse_args()
    result = route_prompt(
        args.prompt,
        Path(args.plugin_root).expanduser().resolve(),
        Path(args.config).expanduser().resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
