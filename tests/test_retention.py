from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
SPEC = importlib.util.spec_from_file_location(
    "personal_harness_retention_runtime",
    PLUGIN / "scripts" / "harness.py",
)
assert SPEC and SPEC.loader
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

KST = timezone(timedelta(hours=9))
TABLE_HEADER = "| 계층 | 대상 | 보존 | 재검토일 |\n|---|---|---|---|\n"


class RetentionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        (self.project / ".harness" / "imports").mkdir(parents=True)
        self.now = datetime(2026, 7, 29, 14, 0, 0, tzinfo=KST)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_policy(self, rows: str) -> Path:
        path = self.project / ".harness" / "imports" / "RETENTION.md"
        path.write_text(f"# 보존 정책\n\n{TABLE_HEADER}{rows}", encoding="utf-8")
        return path

    def test_missing_policy_is_reported_but_is_not_an_error(self) -> None:
        payload = HARNESS.retention_policy(self.project, self.now)

        self.assertFalse(payload["available"])
        self.assertEqual([], payload["overdue"])
        self.assertIsNone(payload["next_review"])

    def test_parses_tiers_and_finds_the_next_review(self) -> None:
        self.write_policy(
            "| 요약 | `**/*.md` | 영구 | - |\n"
            "| 집계 원본 | `reports/**` | 프로젝트 종료 + 마감 1회 | 2026-10-29 |\n"
            "| 첨부 원본 | `slack/**` | 프로젝트 종료 + 마감 1회 | 2026-12-01 |\n"
            "| 식별정보 RAW | 해당 파일 없음 | 즉시 집계만 | - |\n"
        )

        payload = HARNESS.retention_policy(self.project, self.now)

        self.assertTrue(payload["available"])
        self.assertEqual(4, len(payload["tiers"]))
        self.assertEqual("2026-10-29", payload["next_review"])
        self.assertEqual([], payload["overdue"])

    def test_overdue_review_is_listed(self) -> None:
        self.write_policy(
            "| 집계 원본 | `reports/**` | 프로젝트 종료 + 마감 1회 | 2026-06-30 |\n"
            "| 첨부 원본 | `slack/**` | 프로젝트 종료 + 마감 1회 | 2026-12-01 |\n"
        )

        payload = HARNESS.retention_policy(self.project, self.now)

        self.assertEqual(1, len(payload["overdue"]))
        self.assertEqual("집계 원본", payload["overdue"][0]["tier"])
        self.assertEqual("2026-06-30", payload["overdue"][0]["review"])
        self.assertEqual("2026-12-01", payload["next_review"])

    def test_permanent_and_immediate_tiers_need_no_date(self) -> None:
        self.write_policy(
            "| 요약 | `**/*.md` | 영구 | - |\n"
            "| 식별정보 RAW | 해당 파일 없음 | 즉시 집계만 | - |\n"
        )

        payload = HARNESS.retention_policy(self.project, self.now)

        self.assertEqual(2, len(payload["tiers"]))
        self.assertEqual([], payload["overdue"])
        self.assertIsNone(payload["next_review"])

    def test_malformed_date_does_not_raise(self) -> None:
        self.write_policy("| 집계 원본 | `reports/**` | 보존 | 2026-13-99 |\n")

        payload = HARNESS.retention_policy(self.project, self.now)

        self.assertEqual([], payload["overdue"])
        self.assertIsNone(payload["next_review"])

    def test_doctor_errors_only_when_a_review_is_overdue(self) -> None:
        templates = PLUGIN / "templates"
        data = Path(self.temporary.name) / "data"
        HARNESS.initialize_project(self.project, templates)
        HARNESS.initialize_global(data, templates)

        self.write_policy("| 집계 원본 | `reports/**` | 보존 | 2026-12-01 |\n")
        checks, errors = HARNESS.doctor(self.project, data, templates, self.now)
        self.assertFalse([line for line in errors if "보존" in line])
        self.assertTrue([line for line in checks if "retention policy" in line])

        self.write_policy("| 집계 원본 | `reports/**` | 보존 | 2026-06-30 |\n")
        checks, errors = HARNESS.doctor(self.project, data, templates, self.now)
        self.assertTrue([line for line in errors if "집계 원본" in line])

    def test_this_repository_declares_a_policy_with_no_overdue_review(self) -> None:
        payload = HARNESS.retention_policy(ROOT)

        self.assertTrue(payload["available"])
        self.assertEqual([], payload["overdue"])
        self.assertTrue(any(tier["tier"] for tier in payload["tiers"]))


if __name__ == "__main__":
    unittest.main()
