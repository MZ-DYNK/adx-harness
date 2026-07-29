from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
SPEC = importlib.util.spec_from_file_location(
    "personal_harness_skill_router",
    PLUGIN / "scripts" / "skill_router.py",
)
assert SPEC and SPEC.loader
ROUTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROUTER)


class SkillRouterTests(unittest.TestCase):
    def selected_names(self, prompt: str) -> list[str]:
        routing = ROUTER.route_prompt(prompt, PLUGIN)
        return [item["skill"] for item in routing["selected"]]

    def test_routes_clear_single_skill_prompts(self) -> None:
        cases = (
            (
                "find 스킬도 추가해두고 반복 업무에 맞는 스킬을 찾아줘",
                "find-skills",
            ),
            (
                "find-skills로 필요한 스킬 검색해줘",
                "find-skills",
            ),
            (
                "어떤 skill을 써야 할지 찾아줘",
                "find-skills",
            ),
            (
                "이 하네스에 빠진 스킬이 뭐야?",
                "find-skills",
            ),
            (
                "Is there an existing skill for database migrations?",
                "find-skills",
            ),
            (
                "Search the skill catalog for PDF extraction",
                "find-skills",
            ),
            (
                "원더 데일리 리포트를 CPA와 ROAS 기준으로 분석하고 "
                "예산을 재배분해줘",
                "audit-marketing-report",
            ),
            (
                "Create a decision from this daily marketing report: platform CPA "
                "improved, but first-party conversions are stale and cost basis is unknown.",
                "audit-marketing-report",
            ),
            (
                "광고 소재 성과를 분석하고 다음 A/B 테스트를 설계해줘",
                "plan-marketing-experiment",
            ),
            (
                "가입 후 전환을 높이는 CRM 시나리오와 suppression 기준을 설계해줘",
                "design-crm-lifecycle",
            ),
            (
                "리텐션 저하 원인을 분석하고 CRM 세그먼트를 진단해줘",
                "design-crm-lifecycle",
            ),
            (
                "Slack과 메일의 광고주 피드백을 정리하고 담당자와 기한을 결정해줘",
                "reconcile-marketing-decision",
            ),
            (
                "Reconcile conflicting advertiser and in-house Slack decisions; "
                "no owner has been assigned.",
                "reconcile-marketing-decision",
            ),
            (
                "한국 시장 진출을 위한 브랜드 포지셔닝과 GTM 전략을 기획해줘",
                "korea-marketing",
            ),
            (
                "대시보드의 정보 위계와 컴포넌트 구성을 제안해줘",
                "frontend-ideation",
            ),
            (
                "Polish this README without changing its technical meaning.",
                "adaptive-writing",
            ),
            (
                "지난번에 확정한 결정을 불러와 위키에 승격해줘",
                "project-knowledge",
            ),
            (
                "이 프로젝트의 지식 위키와 지식베이스를 구축해줘",
                "project-knowledge",
            ),
            (
                "이 ROAS가 왜 떨어졌는지 알려줘",
                "audit-marketing-report",
            ),
            (
                "회의록을 요약하고 액션 아이템을 정리해줘",
                "reconcile-marketing-decision",
            ),
            (
                "다음에 어떤 광고 소재를 만들어야 할까?",
                "plan-marketing-experiment",
            ),
        )

        for prompt, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual([expected], self.selected_names(prompt))

    def test_critical_false_positive_prompts_abstain(self) -> None:
        prompts = (
            "Build a CLI for this API.",
            "고객 API timeout 원인을 찾아서 고쳐줘.",
            "Explain PostgreSQL data retention settings.",
            "건축 마감 소재의 내구성을 비교해줘.",
            "The GitHub Actions test report is failing. Fix the workflow.",
            "React component unit test가 깨졌어. 고쳐줘.",
            "The UI test suite is flaky after the dependency upgrade.",
            "예산 승인 워크플로우 API를 구현해줘.",
            "Create a branded TypeScript type for UserId.",
            "한글 입력 버그를 재현하고 수정해줘.",
            "Review this pull request for race conditions.",
            "리포트 PDF 파일명을 날짜순으로 바꿔줘.",
            "Slack 메일을 요약해줘.",
            "고객 데이터 retention policy를 설계해줘.",
            "RPG 게임 스킬 트리에 포인트를 추가해줘.",
            "이력서의 직무 스킬을 보기 좋게 정리해줘.",
            "이력서에 넣을 스킬을 추천해줘.",
            "This bug is just a skill issue in the game.",
            "이 스킬에 예시를 추가해줘.",
            "이 스킬에 내용을 추가해줘.",
            "이 스킬에 섹션을 추가해줘.",
            "Add examples to this skill.",
            "Add a section to the skill.",
        )

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                routing = ROUTER.route_prompt(prompt, PLUGIN)
                self.assertEqual([], routing["selected"])
                self.assertEqual([], routing["review"])

    def test_explicit_dollar_skill_invocation_wins(self) -> None:
        routing = ROUTER.route_prompt(
            "일반적인 질문이지만 $adaptive-writing 을 사용해 답변해줘.",
            PLUGIN,
        )

        self.assertTrue(routing["explicit"])
        self.assertEqual(["adaptive-writing"], self.selected_names(
            "일반적인 질문이지만 $adaptive-writing 을 사용해 답변해줘."
        ))
        self.assertEqual(1.0, routing["selected"][0]["score"])
        self.assertEqual(["explicit invocation"], routing["selected"][0]["matched"])

    def test_non_explicit_compound_prompt_is_capped_at_two_skills(self) -> None:
        prompt = (
            "데일리 리포트 CPA를 분석하고 CRM 시나리오를 설계하고 "
            "대시보드 디자인 방향을 제안해줘"
        )
        config = ROUTER.load_config()
        text = ROUTER.normalize_text(prompt)
        threshold = float(config["selected_threshold"])
        scores = [
            ROUTER.score_route(text, route)
            for route in config["routes"]
        ]
        eligible = [result for result in scores if result["score"] >= threshold]

        self.assertGreaterEqual(len(eligible), 3)
        routing = ROUTER.route_prompt(prompt, PLUGIN)
        self.assertFalse(routing["explicit"])
        self.assertEqual(int(config["max_skills"]), len(routing["selected"]))

    def test_registry_matches_installed_skills(self) -> None:
        self.assertEqual([], ROUTER.validate_registry(PLUGIN))

        config = ROUTER.load_config()
        route_names = [
            route["skill"]
            for route in config["routes"]
            if isinstance(route, dict) and route.get("skill")
        ]
        installed_names = set(ROUTER.installed_skills(PLUGIN))

        self.assertEqual(len(route_names), len(set(route_names)))
        self.assertEqual(installed_names, set(route_names))

    def test_registry_reports_an_installed_skill_without_route(self) -> None:
        config = ROUTER.load_config()
        config["routes"] = [
            route
            for route in config["routes"]
            if route.get("skill") != "find-skills"
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routing.json"
            path.write_text(
                json.dumps(config, ensure_ascii=False),
                encoding="utf-8",
            )
            errors = ROUTER.validate_registry(PLUGIN, path)

        self.assertIn("Installed skill has no route: find-skills", errors)


if __name__ == "__main__":
    unittest.main()
