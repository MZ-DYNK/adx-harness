from __future__ import annotations

import importlib.util
import sqlite3
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
SCRIPT_ROOT = PLUGIN / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

SPEC = importlib.util.spec_from_file_location(
    "personal_harness_knowledge",
    SCRIPT_ROOT / "knowledge.py",
)
assert SPEC and SPEC.loader
KNOWLEDGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = KNOWLEDGE
SPEC.loader.exec_module(KNOWLEDGE)


class KnowledgeIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.data = self.root / "plugin-data"
        (self.project / ".harness").mkdir(parents=True)
        (self.data / "global").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_project(self, relative: str, content: str) -> Path:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read_index_bodies(self) -> str:
        path = KNOWLEDGE.ensure_index(self.project, self.data)
        self.assertIsNotNone(path)
        connection = sqlite3.connect(path)
        try:
            rows = connection.execute("SELECT body FROM chunks").fetchall()
        finally:
            connection.close()
        return "\n".join(str(row[0]) for row in rows)

    def indexed_paths(self) -> set[str]:
        path = KNOWLEDGE.ensure_index(self.project, self.data)
        self.assertIsNotNone(path)
        connection = sqlite3.connect(path)
        try:
            rows = connection.execute("SELECT rel_path FROM documents").fetchall()
        finally:
            connection.close()
        return {str(row[0]) for row in rows}

    def test_default_search_stays_in_canonical_tiers(self) -> None:
        self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\nsharedneedle 정본 지식입니다.\n",
        )
        self.write_project(
            ".harness/logs/2026/07/29.md",
            "# 작업 기록\n\nsharedneedle 과거 기록입니다.\n",
        )
        self.write_project(
            ".harness/imports/reports/summary.md",
            "# 조사 요약\n\nsharedneedle 제한 근거입니다.\n",
        )

        results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "sharedneedle",
            limit=8,
        )

        self.assertTrue(results)
        self.assertEqual({"canonical"}, {result["tier"] for result in results})
        self.assertEqual(
            {".harness/WIKI.md"},
            {result["path"] for result in results},
        )

    def test_continuity_query_opts_into_history(self) -> None:
        self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\n현재 정본에는 다른 내용만 있습니다.\n",
        )
        self.write_project(
            ".harness/logs/2026/07/29.md",
            "# 작업 기록\n\nhistoryneedle 후속 작업을 남겼습니다.\n",
        )

        default_results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "historyneedle",
        )
        continuity_results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "지난번 historyneedle 이어서 해줘",
        )

        self.assertEqual([], default_results)
        self.assertTrue(continuity_results)
        self.assertIn("history", {result["tier"] for result in continuity_results})
        self.assertIn(
            ".harness/logs/2026/07/29.md",
            {result["path"] for result in continuity_results},
        )

    def test_explicit_evidence_query_hides_restricted_snippets(self) -> None:
        restricted_text = "restrictedneedle 광고주 내부 판단 근거"
        self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\n일반 정본입니다.\n",
        )
        self.write_project(
            ".harness/imports/reports/summary.md",
            f"# 조사 요약\n\n{restricted_text}\n",
        )

        default_results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "restrictedneedle",
        )
        evidence_results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "원문 restrictedneedle 근거 확인",
        )
        context = KNOWLEDGE.format_knowledge_context(evidence_results)

        self.assertEqual([], default_results)
        self.assertTrue(evidence_results)
        self.assertEqual(
            {"evidence-summary"},
            {result["tier"] for result in evidence_results},
        )
        self.assertTrue(
            all(result["privacy"] == "restricted" for result in evidence_results)
        )
        self.assertTrue(all(result["snippet"] == "" for result in evidence_results))
        self.assertIn("restricted summary", context)
        self.assertNotIn(restricted_text, context)

    def test_evidence_terms_come_from_the_project_not_from_shipped_code(self) -> None:
        source = (PLUGIN / "scripts" / "knowledge.py").read_text(encoding="utf-8")
        for name in ("원더", "wonder", "티젠", "teazen"):
            with self.subTest(name=name):
                self.assertNotIn(name, source)

    def test_import_bundle_names_open_the_evidence_tier(self) -> None:
        self.write_project(
            ".harness/imports/reports/2026-07-29/acmecorp/notes.md",
            "# 조사 요약\n\nbundleneedle 확인했습니다.\n",
        )

        self.assertNotIn(
            "evidence-summary",
            KNOWLEDGE.infer_tiers("bundleneedle 정리해줘", self.project),
        )
        self.assertIn(
            "evidence-summary",
            KNOWLEDGE.infer_tiers("acmecorp bundleneedle 확인해줘", self.project),
        )
        self.assertNotIn(
            "evidence-summary",
            KNOWLEDGE.infer_tiers("acmecorp bundleneedle 확인해줘"),
        )

    def test_generic_evidence_words_still_open_the_tier(self) -> None:
        for query in ("원문 근거 확인", "slack 첨부 확인", "메일 원본 확인"):
            with self.subTest(query=query):
                self.assertIn(
                    "evidence-summary",
                    KNOWLEDGE.infer_tiers(query, self.project),
                )

    def test_bundle_scan_ignores_dates_and_storage_buckets(self) -> None:
        self.write_project(
            ".harness/imports/reports/2026-07-29/acmecorp/originals/x.md",
            "# x\n",
        )

        for query in ("2026-07-29 확인", "originals 확인", "reports 확인"):
            with self.subTest(query=query):
                self.assertNotIn(
                    "evidence-summary",
                    KNOWLEDGE.infer_tiers(query, self.project),
                )

    def test_source_change_rebuilds_search_index(self) -> None:
        wiki = self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\noldneedle 이전 결정입니다.\n",
        )

        self.assertTrue(
            KNOWLEDGE.search_knowledge(self.project, self.data, "oldneedle")
        )

        wiki.write_text(
            "# 위키\n\nnewneedle 새 결정으로 교체했습니다. 내용 길이도 달라졌습니다.\n",
            encoding="utf-8",
        )

        self.assertEqual(
            [],
            KNOWLEDGE.search_knowledge(self.project, self.data, "oldneedle"),
        )
        updated = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "newneedle",
        )
        self.assertTrue(updated)
        self.assertEqual(".harness/WIKI.md", updated[0]["path"])

    def test_korean_particles_resolve_to_canonical_terms(self) -> None:
        self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\n고객 세그먼트 결정은 구매 주기를 기준으로 합니다.\n",
        )

        results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "지난번 고객의 세그먼트를 불러와줘",
        )

        self.assertTrue(results)
        self.assertIn("고객", results[0]["matched"])
        self.assertIn("세그먼트", results[0]["matched"])

    def test_generic_single_word_does_not_enter_prompt_context(self) -> None:
        self.write_project(
            ".harness/WIKI.md",
            "# 일반 정보\n\n정보만 포함된 무관한 문서입니다.\n",
        )

        results = KNOWLEDGE.search_knowledge(
            self.project,
            self.data,
            "대시보드 정보 위계를 설계해줘",
        )
        context = KNOWLEDGE.format_knowledge_context(results)

        self.assertEqual([], results)
        self.assertEqual("", context)

    def test_index_redacts_pii_and_secrets(self) -> None:
        email = "owner@example.com"
        phone = "010-1234-5678"
        api_secret = "supersecretvalue123456"
        github_token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
        self.write_project(
            ".harness/WIKI.md",
            (
                "# 위키\n\n"
                "privacyneedle 민감정보 테스트\n"
                f"- 담당자: {email}\n"
                f"- 전화: {phone}\n"
                f"- api_key={api_secret}\n"
                f"- token: {github_token}\n"
            ),
        )

        bodies = self.read_index_bodies()
        database_bytes = KNOWLEDGE.index_path(self.project).read_bytes()

        for raw_value in (email, phone, api_secret, github_token):
            self.assertNotIn(raw_value, bodies)
            self.assertNotIn(raw_value.encode("utf-8"), database_bytes)
        self.assertIn("[REDACTED_EMAIL]", bodies)
        self.assertIn("010-****-****", bodies)
        self.assertIn("[REDACTED]", bodies)

    def test_originals_attachments_and_binary_files_are_not_indexed(self) -> None:
        self.write_project(
            ".harness/imports/reports/summary.md",
            "# 조사 요약\n\nsummaryneedle 검토된 요약입니다.\n",
        )
        self.write_project(
            ".harness/imports/reports/originals/raw.md",
            "# 원문\n\nrawneedle 원본 Markdown입니다.\n",
        )
        self.write_project(
            ".harness/imports/slack/attachments/transcript.md",
            "# 첨부\n\nattachmentneedle 첨부 변환본입니다.\n",
        )
        self.write_project(
            ".harness/imports/reports/email-originals/mail.md",
            "# 메일 원문\n\nmailneedle 메일 원본입니다.\n",
        )
        binary = self.project / ".harness/imports/reports/originals/report.pdf"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(b"%PDF-1.7 binaryneedle")

        paths = self.indexed_paths()

        self.assertIn(".harness/imports/reports/summary.md", paths)
        self.assertNotIn(".harness/imports/reports/originals/raw.md", paths)
        self.assertNotIn(".harness/imports/slack/attachments/transcript.md", paths)
        self.assertNotIn(".harness/imports/reports/email-originals/mail.md", paths)
        self.assertNotIn(".harness/imports/reports/originals/report.pdf", paths)

    def test_index_permissions_are_owner_only(self) -> None:
        self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\npermissionneedle 권한 검사입니다.\n",
        )

        path = KNOWLEDGE.ensure_index(self.project, self.data)
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(0o700, stat.S_IMODE(path.parent.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))

        path.parent.chmod(0o755)
        path.chmod(0o644)
        refreshed = KNOWLEDGE.ensure_index(self.project, self.data)

        self.assertEqual(path, refreshed)
        self.assertEqual(0o700, stat.S_IMODE(path.parent.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))

    def test_symlinked_index_directory_is_rejected(self) -> None:
        self.write_project(
            ".harness/WIKI.md",
            "# 위키\n\nsymlinkneedle 안전성 검사입니다.\n",
        )
        outside = self.root / "outside-index"
        outside.mkdir()
        KNOWLEDGE.index_dir(self.project).symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "symlinked knowledge index"):
            KNOWLEDGE.rebuild_index(self.project, self.data)
        self.assertEqual([], list(outside.iterdir()))


if __name__ == "__main__":
    unittest.main()
