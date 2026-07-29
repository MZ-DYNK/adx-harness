from __future__ import annotations

import importlib.util
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
SPEC = importlib.util.spec_from_file_location(
    "personal_harness_runtime",
    PLUGIN / "scripts" / "harness.py",
)
assert SPEC and SPEC.loader
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class HarnessRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.data = self.root / "plugin-data"
        self.project.mkdir()
        self.templates = PLUGIN / "templates"
        self.now = datetime(
            2026,
            7,
            29,
            14,
            32,
            10,
            tzinfo=timezone(timedelta(hours=9)),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prompt_event(self, prompt: str = "질문입니다") -> dict[str, str]:
        return {
            "session_id": "session-1",
            "prompt_id": "prompt-1",
            "hook_event_name": "UserPromptSubmit",
            "prompt": prompt,
        }

    def stop_event(self, answer: str = "답변입니다") -> dict[str, str]:
        return {
            "session_id": "session-1",
            "prompt_id": "prompt-1",
            "hook_event_name": "Stop",
            "last_assistant_message": answer,
        }

    def test_initializes_project_and_global_knowledge(self) -> None:
        project_root = HARNESS.initialize_project(self.project, self.templates)
        global_root = HARNESS.initialize_global(self.data, self.templates)

        self.assertTrue((project_root / "PROJECT.md").is_file())
        self.assertTrue((project_root / "NOW.md").is_file())
        self.assertTrue((project_root / "wiki").is_dir())
        self.assertTrue((project_root / "logs" / "INDEX.md").is_file())
        self.assertIn("logs/", (project_root / ".gitignore").read_text(encoding="utf-8"))
        self.assertTrue((global_root / "PROFILE.md").is_file())
        self.assertTrue((global_root / "DESIGN-TASTE.md").is_file())
        self.assertEqual(0o700, stat.S_IMODE(self.data.stat().st_mode))
        self.assertEqual(0o700, stat.S_IMODE(global_root.stat().st_mode))
        self.assertEqual(
            0o600,
            stat.S_IMODE((global_root / "PROFILE.md").stat().st_mode),
        )

    def test_archives_question_answer_progress_and_redacts_secrets(self) -> None:
        prompt = (
            "분석해줘 api_key=supersecretvalue123456 "
            "META_ACCESS_TOKEN=metasecretvalue123456 "
            "담당자 owner@example.com 010-1234-5678 "
            "https://files.example.com/report.xlsx?X-Amz-Signature=signedvalue123&part=1"
        )
        HARNESS.record_prompt(
            self.prompt_event(prompt),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        HARNESS.record_tool(
            {
                "session_id": "session-1",
                "prompt_id": "prompt-1",
                "tool_name": "Bash",
                "tool_input": {
                    "command": "curl -H 'Authorization: Bearer abcdefghijklmnop' https://example.com"
                },
            },
            self.project,
            self.data,
            self.now,
        )
        HARNESS.record_tool(
            {
                "session_id": "session-1",
                "prompt_id": "prompt-1",
                "tool_name": "WebFetch",
                "tool_input": {
                    "url": "https://files.example.com/report.xlsx?token=privatevalue&part=1"
                },
            },
            self.project,
            self.data,
            self.now,
        )
        answer = "완료했습니다. ghp_abcdefghijklmnopqrstuvwxyz123456"
        log_path = HARNESS.archive_stop(
            self.stop_event(answer),
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        self.assertIsNotNone(log_path)
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("### 질문", content)
        self.assertIn("### 답변", content)
        self.assertIn("### 라우팅", content)
        self.assertIn("- 관측된 호출: 없음", content)
        self.assertIn("### 진행", content)
        self.assertIn("[REDACTED]", content)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", content)
        self.assertNotIn("supersecretvalue123456", content)
        self.assertNotIn("metasecretvalue123456", content)
        self.assertNotIn("abcdefghijklmnop", content)
        self.assertNotIn("owner@example.com", content)
        self.assertNotIn("010-1234-5678", content)
        self.assertNotIn("signedvalue123", content)
        self.assertNotIn("privatevalue", content)
        self.assertNotIn("?token=", content)
        self.assertIn("[REDACTED_EMAIL]", content)
        self.assertIn("010-****-****", content)
        self.assertIn("Bash:", content)
        self.assertIn("WebFetch: https://files.example.com/report.xlsx", content)

        duplicate = HARNESS.archive_stop(
            self.stop_event(answer),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        self.assertEqual(log_path, duplicate)
        self.assertEqual(1, log_path.read_text(encoding="utf-8").count("### 질문"))

    def test_rolls_over_a_full_daily_log(self) -> None:
        HARNESS.initialize_project(self.project, self.templates)
        directory = self.project / ".harness" / "logs" / "2026" / "07"
        directory.mkdir(parents=True, exist_ok=True)
        base = directory / "29.md"
        base.write_text(
            HARNESS.log_header(self.now, 1) + ("x" * HARNESS.MAX_LOG_BYTES),
            encoding="utf-8",
        )

        HARNESS.record_prompt(
            self.prompt_event(),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        log_path = HARNESS.archive_stop(
            self.stop_event(),
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        self.assertEqual("29.part-02.md", log_path.name)
        self.assertIn(
            "part 02",
            log_path.read_text(encoding="utf-8").splitlines()[0],
        )

    def test_moves_long_answer_to_a_companion_file(self) -> None:
        HARNESS.record_prompt(
            self.prompt_event(),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        answer = "가" * (HARNESS.INLINE_ANSWER_CHARS + 1)
        log_path = HARNESS.archive_stop(
            self.stop_event(answer),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("별도 파일로 분리", content)

        companion_files = list(log_path.parent.glob("29.turn-*-answer.md"))
        self.assertEqual(1, len(companion_files))
        companion = companion_files[0].read_text(encoding="utf-8")
        self.assertIn("가" * 100, companion)

    def test_archives_multiple_turns_without_prompt_ids(self) -> None:
        first_prompt = self.prompt_event("첫 질문")
        first_prompt.pop("prompt_id")
        first_stop = self.stop_event("첫 답변")
        first_stop.pop("prompt_id")
        first_path = HARNESS.record_prompt(
            first_prompt,
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        first_log = HARNESS.archive_stop(
            first_stop,
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        duplicate = HARNESS.archive_stop(
            first_stop,
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        self.assertEqual(first_log, duplicate)

        second_prompt = self.prompt_event("둘째 질문")
        second_prompt.pop("prompt_id")
        second_stop = self.stop_event("둘째 답변")
        second_stop.pop("prompt_id")
        second_path = HARNESS.record_prompt(
            second_prompt,
            self.project,
            self.data,
            self.templates,
            self.now + timedelta(minutes=1),
        )
        second_log = HARNESS.archive_stop(
            second_stop,
            self.project,
            self.data,
            self.templates,
            self.now + timedelta(minutes=1),
        )

        self.assertEqual(first_path, second_path)
        self.assertEqual(first_log, second_log)
        content = second_log.read_text(encoding="utf-8")
        self.assertEqual(2, content.count("### 질문"))
        self.assertIn("첫 질문", content)
        self.assertIn("둘째 질문", content)

    def test_session_context_is_bounded_and_points_to_canonical_files(self) -> None:
        context = HARNESS.build_context(
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        self.assertLessEqual(len(context), HARNESS.MAX_CONTEXT_CHARS + 30)
        self.assertIn("Global user profile", context)
        self.assertIn("Project knowledge root", context)
        self.assertIn("## Current state", context)
        self.assertIn("whole logs directory", context)

    def test_session_context_falls_back_to_latest_previous_log(self) -> None:
        HARNESS.initialize_project(self.project, self.templates)
        previous = self.project / ".harness" / "logs" / "2026" / "07" / "28.md"
        previous.parent.mkdir(parents=True, exist_ok=True)
        previous.write_text(
            "# 2026-07-28 작업 기록\n\n전날 이어갈 핵심 작업\n",
            encoding="utf-8",
        )

        context = HARNESS.build_context(
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        self.assertIn(str(previous), context)
        self.assertIn("Path only", context)
        self.assertNotIn("전날 이어갈 핵심 작업", context)

    def test_marketing_prompt_routes_report_terms(self) -> None:
        context = HARNESS.prompt_context(
            "CPA와 소재 기준으로 데일리 리포트 분석해줘",
            self.project,
            self.data,
        )

        self.assertIn("audit-marketing-report", context)
        self.assertIn("routing hint", context)
        self.assertNotIn("restricted summary", context)

    def test_local_skill_catalog_lists_bundled_skills(self) -> None:
        catalog = HARNESS.local_skill_catalog(PLUGIN)
        names = {item["name"] for item in catalog}

        self.assertIn("find-skills", names)
        self.assertIn("audit-marketing-report", names)
        self.assertEqual(len(names), len(catalog))
        self.assertTrue(
            all(item["path"].startswith("skills/") for item in catalog)
        )

    def test_routing_report_compares_recommended_and_observed_skill(self) -> None:
        HARNESS.record_prompt(
            self.prompt_event("CPA 기준으로 데일리 리포트를 분석해줘"),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        HARNESS.record_tool(
            {
                "session_id": "session-1",
                "prompt_id": "prompt-1",
                "tool_name": "Skill",
                "tool_input": {
                    "skill": "personal-harness:audit-marketing-report"
                },
            },
            self.project,
            self.data,
            self.now,
        )
        for index in range(HARNESS.MAX_ACTIONS + 1):
            HARNESS.record_tool(
                {
                    "session_id": "session-1",
                    "prompt_id": "prompt-1",
                    "tool_name": "Bash",
                    "tool_input": {"command": f"echo routing-check-{index}"},
                },
                self.project,
                self.data,
                self.now,
            )
        HARNESS.archive_stop(
            self.stop_event("분석을 완료했습니다."),
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        report = HARNESS.routing_report(self.project)

        self.assertEqual(1, report["turns"]["total"])
        self.assertEqual(1, report["turns"]["instrumented"])
        self.assertEqual(1.0, report["rates"]["candidate_adoption"])
        self.assertEqual(1.0, report["rates"]["routable_call_capture"])
        self.assertEqual(1.0, report["rates"]["exact_set_match"])
        self.assertEqual(1, report["recommended"]["audit-marketing-report"])
        self.assertEqual(1, report["observed"]["audit-marketing-report"])
        self.assertEqual(1, report["outcomes"]["추천 후보 사용"])

    def test_routing_report_measures_partial_candidate_adoption(self) -> None:
        HARNESS.record_prompt(
            self.prompt_event(
                "데일리 리포트 CPA를 분석하고 CRM 시나리오를 설계해줘"
            ),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        HARNESS.record_tool(
            {
                "session_id": "session-1",
                "prompt_id": "prompt-1",
                "tool_name": "Skill",
                "tool_input": {"skill": "audit-marketing-report"},
            },
            self.project,
            self.data,
            self.now,
        )
        HARNESS.archive_stop(
            self.stop_event(),
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        report = HARNESS.routing_report(self.project)

        self.assertEqual(0.5, report["rates"]["candidate_adoption"])
        self.assertEqual(1.0, report["rates"]["routable_call_capture"])
        self.assertEqual(0.0, report["rates"]["exact_set_match"])

    def test_routing_report_excludes_explicit_skill_from_auto_metrics(self) -> None:
        HARNESS.record_prompt(
            self.prompt_event("$adaptive-writing 이 문서를 다듬어줘"),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        HARNESS.record_tool(
            {
                "session_id": "session-1",
                "prompt_id": "prompt-1",
                "tool_name": "Skill",
                "tool_input": {"skill": "adaptive-writing"},
            },
            self.project,
            self.data,
            self.now,
        )
        HARNESS.archive_stop(
            self.stop_event(),
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        report = HARNESS.routing_report(self.project)

        self.assertEqual(1, report["turns"]["explicit"])
        self.assertEqual(0, report["turns"]["automatic"])
        self.assertIsNone(report["rates"]["candidate_adoption"])
        self.assertEqual(
            1,
            report["by_skill"]["adaptive-writing"]["explicit_used"],
        )

    def test_routing_report_counts_review_candidate_use_without_prompt_text(self) -> None:
        private_marker = "PRIVATE_ROUTING_REPORT_MARKER"
        state_path = HARNESS.record_prompt(
            self.prompt_event(f"{private_marker} 문서를 검토해줘"),
            self.project,
            self.data,
            self.templates,
            self.now,
        )
        state = HARNESS.read_json_file(state_path)
        state["routing"] = {
            "selected": [],
            "review": [{"skill": "adaptive-writing", "score": 0.70}],
            "explicit": False,
        }
        HARNESS.atomic_write_json(state_path, state)
        HARNESS.record_tool(
            {
                "session_id": "session-1",
                "prompt_id": "prompt-1",
                "tool_name": "Skill",
                "tool_input": {"skill": "adaptive-writing"},
            },
            self.project,
            self.data,
            self.now,
        )
        HARNESS.archive_stop(
            self.stop_event(f"{private_marker} 답변"),
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        report = HARNESS.routing_report(self.project)

        self.assertEqual(1.0, report["rates"]["review_promotion"])
        self.assertEqual(
            1,
            report["by_skill"]["adaptive-writing"]["review_used"],
        )
        self.assertEqual(
            0,
            report["by_skill"]["adaptive-writing"]["unexpected"],
        )
        self.assertNotIn(private_marker, str(report))

    def test_prompt_context_points_to_latest_log_without_loading_it(self) -> None:
        HARNESS.initialize_project(self.project, self.templates)
        previous = self.project / ".harness" / "logs" / "2026" / "07" / "28.md"
        previous.parent.mkdir(parents=True, exist_ok=True)
        previous.write_text(
            "# 2026-07-28 작업 기록\n\nDO_NOT_INJECT_THIS_LOG_BODY\n",
            encoding="utf-8",
        )

        context = HARNESS.prompt_context("이어서 작업해줘", self.project, self.data)

        self.assertIn(str(previous), context)
        self.assertIn("path hint only", context)
        self.assertNotIn("DO_NOT_INJECT_THIS_LOG_BODY", context)

    def test_context_exposes_import_index_path_without_loading_content(self) -> None:
        harness = HARNESS.initialize_project(self.project, self.templates)
        imports_index = harness / "imports" / "INDEX.md"
        imports_index.parent.mkdir(parents=True, exist_ok=True)
        imports_index.write_text(
            "# 조사 인덱스\n\nAUTO_LOAD_FORBIDDEN_SENTINEL\n",
            encoding="utf-8",
        )

        context = HARNESS.build_context(
            self.project,
            self.data,
            self.templates,
            self.now,
        )

        self.assertIn(str(imports_index), context)
        self.assertNotIn("AUTO_LOAD_FORBIDDEN_SENTINEL", context)

    def test_non_development_tool_summaries_are_bounded(self) -> None:
        read = HARNESS.summarize_tool(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": str(self.project / "brief.md")},
            },
            self.project,
        )
        glob = HARNESS.summarize_tool(
            {
                "tool_name": "Glob",
                "tool_input": {"path": str(self.project), "pattern": "**/*.xlsx"},
            },
            self.project,
        )
        grep = HARNESS.summarize_tool(
            {
                "tool_name": "Grep",
                "tool_input": {
                    "path": str(self.project),
                    "pattern": "private search phrase",
                },
            },
            self.project,
        )
        mcp = HARNESS.summarize_tool(
            {
                "tool_name": "mcp__slack__search",
                "tool_input": {"query": "private conversation"},
            },
            self.project,
        )

        self.assertEqual("Read: brief.md", read)
        self.assertIn("**/*.xlsx", glob)
        self.assertNotIn("private search phrase", grep)
        self.assertEqual("MCP: mcp__slack__search", mcp)
        self.assertNotIn("private conversation", mcp)

    def test_wiki_structure_reports_orphan_and_broken_pages(self) -> None:
        harness = HARNESS.initialize_project(self.project, self.templates)
        orphan = harness / "wiki" / "decisions" / "orphan.md"
        orphan.parent.mkdir(parents=True)
        orphan.write_text("# 고아 결정\n", encoding="utf-8")

        _, orphan_errors = HARNESS.validate_knowledge_structure(self.project)
        self.assertIn(
            "Orphan wiki page missing from WIKI.md: wiki/decisions/orphan.md",
            orphan_errors,
        )

        wiki = harness / "WIKI.md"
        wiki.write_text(
            wiki.read_text(encoding="utf-8")
            + "\n- [고아 결정](wiki/decisions/orphan.md)\n"
            + "- [없는 결정](wiki/decisions/missing.md)\n",
            encoding="utf-8",
        )
        _, linked_errors = HARNESS.validate_knowledge_structure(self.project)

        self.assertNotIn(
            "Orphan wiki page missing from WIKI.md: wiki/decisions/orphan.md",
            linked_errors,
        )
        self.assertIn(
            "Broken wiki link: wiki/decisions/missing.md",
            linked_errors,
        )


if __name__ == "__main__":
    unittest.main()
