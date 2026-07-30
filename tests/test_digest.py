from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin" if (ROOT / "plugin" / "scripts").is_dir() else ROOT
SPEC = importlib.util.spec_from_file_location(
    "personal_harness_digest_runtime",
    PLUGIN / "scripts" / "harness.py",
)
assert SPEC and SPEC.loader
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

KST = timezone(timedelta(hours=9))


class DigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.data = self.root / "plugin-data"
        self.project.mkdir()
        self.templates = PLUGIN / "templates"
        self.now = datetime(2026, 7, 29, 14, 32, 10, tzinfo=KST)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_log(self, body: str) -> Path:
        directory = self.project / ".harness" / "logs" / "2026" / "07"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "29.md"
        path.write_text(body, encoding="utf-8")
        return path

    def sample_log(self) -> str:
        return (
            "# 2026-07-29 작업 기록\n\n"
            "## 09:10:00 · 20260729-091000-aaa\n\n"
            "<!-- session: s1 -->\n\n"
            "### 질문\n\n"
            "> 원더 데일리 리포트 CPA를 분석해줘\n\n"
            "### 답변\n\n"
            "> 판정은 Investigate입니다\n\n"
            "### 라우팅\n\n"
            "- 추천 스킬: `audit-marketing-report` (0.90)\n"
            "- 검토 후보: 없음\n"
            "- 호출 방식: 자동 후보\n"
            "- 관측된 호출: `audit-marketing-report`\n"
            "- 비교: 추천 후보 사용\n\n"
            "### 진행\n\n"
            "- `09:10:05` Read: .harness/NOW.md\n"
            "- `09:10:20` Bash: python3 audit.py ×3\n\n"
            "## 11:00:00 · 20260729-110000-bbb\n\n"
            "### 질문\n\n"
            "> 랜딩 화면 구성 제안해줘\n\n"
            "### 답변\n\n"
            "> 세 가지 방향입니다\n\n"
            "### 라우팅\n\n"
            "- 추천 스킬: `frontend-ideation` (0.86)\n"
            "- 검토 후보: 없음\n"
            "- 호출 방식: 자동 후보\n"
            "- 관측된 호출: `adaptive-writing`\n"
            "- 비교: 추천과 다른 스킬 사용\n\n"
            "### 진행\n\n"
            "- `11:00:10` Read: README.md\n\n"
        )

    def test_digest_summarizes_turns_skills_and_activity(self) -> None:
        self.write_log(self.sample_log())

        payload = HARNESS.digest(self.project, self.now)

        self.assertEqual("2026-07-29", payload["date"])
        self.assertEqual(2, payload["totals"]["turns"])
        self.assertEqual(5, payload["totals"]["actions"])
        self.assertEqual(
            {"audit-marketing-report": 1, "adaptive-writing": 1},
            payload["skills_observed"],
        )
        self.assertEqual({"Read": 2, "Bash": 3}, payload["tools"])
        self.assertEqual(
            "원더 데일리 리포트 CPA를 분석해줘",
            payload["turns"][0]["question"],
        )

    def test_digest_flags_routing_mismatch_for_review(self) -> None:
        self.write_log(self.sample_log())

        payload = HARNESS.digest(self.project, self.now)

        self.assertEqual(1, len(payload["needs_review"]))
        self.assertEqual("추천과 다른 스킬 사용", payload["needs_review"][0]["comparison"])
        self.assertIn("확인할 것", HARNESS.format_digest(payload))

    def test_digest_ignores_externalized_turn_files(self) -> None:
        self.write_log(self.sample_log())
        directory = self.project / ".harness" / "logs" / "2026" / "07"
        (directory / "29.turn-20260729-091000-aaa-answer.md").write_text(
            "# 답변\n\n## 09:10:00 · fake\n\n", encoding="utf-8"
        )

        payload = HARNESS.digest(self.project, self.now)

        self.assertEqual(2, payload["totals"]["turns"])

    def test_written_digest_is_private_and_not_a_turn_log(self) -> None:
        self.write_log(self.sample_log())

        path = HARNESS.write_digest(self.project, self.now)

        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual("summary-29.md", path.name)
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        log_root = self.project / ".harness" / "logs"
        turn_logs = [
            item.name
            for item in log_root.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]*.md")
        ]
        self.assertNotIn(path.name, turn_logs)

    def test_digest_without_turns_writes_nothing(self) -> None:
        payload = HARNESS.digest(self.project, self.now)

        self.assertEqual(0, payload["totals"]["turns"])
        self.assertIsNone(HARNESS.write_digest(self.project, self.now))
        self.assertIn("기록된 턴이 없습니다", HARNESS.format_digest(payload))

    def test_session_end_hook_writes_the_digest(self) -> None:
        self.write_log(self.sample_log())

        HARNESS.write_digest(self.project, self.now)

        path = self.project / ".harness" / "logs" / "2026" / "07" / "summary-29.md"
        self.assertTrue(path.is_file())
        self.assertIn("audit-marketing-report", path.read_text(encoding="utf-8"))

    def test_status_reports_without_raising_on_a_fresh_project(self) -> None:
        HARNESS.initialize_project(self.project, self.templates)
        HARNESS.initialize_global(self.data, self.templates)

        text, code = HARNESS.status(self.project, self.data, self.templates)

        installed = len(list((PLUGIN / "skills").glob("*/SKILL.md")))
        self.assertIn("ADX Harness · 상태", text)
        self.assertIn(f"스킬       {installed}개", text)
        self.assertIn(0, (code, 0))

    def test_plugin_install_state_never_raises(self) -> None:
        state = HARNESS.plugin_install_state()

        self.assertIn("installed", state)
        self.assertIsInstance(state["leaks"], list)

    def test_read_event_returns_empty_dict_on_a_terminal(self) -> None:
        class FakeStdin:
            def isatty(self) -> bool:
                return True

            def read(self) -> str:  # pragma: no cover - must never be reached
                raise AssertionError("read_event must not block on a terminal")

        original = HARNESS.sys.stdin
        HARNESS.sys.stdin = FakeStdin()
        try:
            self.assertEqual({}, HARNESS.read_event())
        finally:
            HARNESS.sys.stdin = original


if __name__ == "__main__":
    unittest.main()
