from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
SPEC = importlib.util.spec_from_file_location(
    "personal_harness_promotion_runtime",
    PLUGIN / "scripts" / "harness.py",
)
assert SPEC and SPEC.loader
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

KST = timezone(timedelta(hours=9))
HEADER = "# 승격 후보\n\n<!-- 후보 시작 -->\n\n"


class PromotionGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.data = Path(self.temporary.name) / "data"
        (self.data / "global").mkdir(parents=True)
        self.now = datetime(2026, 7, 30, 10, 0, 0, tzinfo=KST)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, body: str) -> Path:
        path = self.data / "global" / "CANDIDATES.md"
        path.write_text(HEADER + body, encoding="utf-8")
        return path

    def only(self, body: str) -> dict:
        payload = HARNESS.promotion_candidates(self.data, self.now)
        self.assertEqual(1, len(payload["candidates"]))
        return payload["candidates"][0]

    def test_missing_file_is_not_an_error(self) -> None:
        payload = HARNESS.promotion_candidates(self.data, self.now)

        self.assertFalse(payload["available"])
        self.assertEqual([], payload["ready"])

    def test_user_stated_preference_passes_with_one_observation(self) -> None:
        self.write(
            "### 커밋 푸시는 확인 없이 실행\n"
            "- 분류: 프로필\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 예\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-07-30 / ECC / 확인 질문을 불필요하다고 직접 말함\n"
        )

        candidate = self.only("")

        self.assertEqual([], candidate["blocks"])
        self.assertTrue(candidate["ready"])

    def test_three_observations_in_one_session_do_not_pass(self) -> None:
        self.write(
            "### 표를 선호한다\n"
            "- 분류: 취향\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 아니오\n"
            "- 목표: DESIGN-TASTE.md\n"
            "- 관찰: 2026-07-30 / ECC / 표로 달라고 함\n"
            "- 관찰: 2026-07-30 / ECC / 또 표를 요청\n"
            "- 관찰: 2026-07-30 / ECC / 세 번째 요청\n"
        )

        candidate = self.only("")

        self.assertFalse(candidate["ready"])
        self.assertTrue(any("프로젝트" in reason for reason in candidate["blocks"]))
        self.assertTrue(any("간격" in reason for reason in candidate["blocks"]))

    def test_repeated_across_projects_and_time_passes(self) -> None:
        self.write(
            "### 결론을 먼저 본다\n"
            "- 분류: 프로필\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 아니오\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-06-01 / ECC / 결론부터 요구\n"
            "- 관찰: 2026-06-20 / other-repo / 같은 요구 반복\n"
            "- 관찰: 2026-07-15 / third / 다시 확인\n"
        )

        candidate = self.only("")

        self.assertEqual([], candidate["blocks"])
        self.assertTrue(candidate["ready"])

    def test_two_observations_are_not_enough(self) -> None:
        self.write(
            "### 아직 이른 관찰\n"
            "- 분류: 프로필\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 아니오\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-06-01 / ECC / 한 번\n"
            "- 관찰: 2026-07-01 / other / 두 번\n"
        )

        candidate = self.only("")

        self.assertFalse(candidate["ready"])
        self.assertTrue(any("관찰 2회" in reason for reason in candidate["blocks"]))

    def test_personal_data_and_money_are_blocked(self) -> None:
        cases = {
            "이메일": "- 관찰: 2026-06-01 / ECC / dynk@example.com 이 그렇게 말함\n",
            "금액": "- 관찰: 2026-06-01 / ECC / CPA 360,019원 기준을 선호\n",
            "URL": "- 관찰: 2026-06-01 / ECC / https://example.com 참고\n",
            "휴대전화": "- 관찰: 2026-06-01 / ECC / 010-1234-5678 로 확인\n",
        }
        for label, observation in cases.items():
            with self.subTest(label=label):
                self.write(
                    "### 민감값 포함\n"
                    "- 분류: 프로필\n"
                    "- 상태: 대기\n"
                    "- 사용자 명시: 예\n"
                    "- 목표: PROFILE.md\n" + observation
                )
                candidate = self.only("")
                self.assertFalse(candidate["ready"])
                self.assertTrue(
                    any(label in reason for reason in candidate["blocks"]),
                    candidate["blocks"],
                )

    def test_unknown_class_is_blocked(self) -> None:
        self.write(
            "### 분류가 이상함\n"
            "- 분류: 프로젝트\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 예\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-07-30 / ECC / 근거\n"
        )

        candidate = self.only("")

        self.assertFalse(candidate["ready"])
        self.assertTrue(any("분류" in reason for reason in candidate["blocks"]))

    def test_full_target_file_blocks_promotion(self) -> None:
        target = self.data / "global" / "PROFILE.md"
        target.write_text("\n".join(f"line {n}" for n in range(200)), encoding="utf-8")
        self.write(
            "### 목표 파일이 꽉 찼다\n"
            "- 분류: 프로필\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 예\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-07-30 / ECC / 근거\n"
        )

        candidate = self.only("")

        self.assertFalse(candidate["ready"])
        self.assertTrue(any("상한" in reason for reason in candidate["blocks"]))

    def test_already_promoted_candidate_is_not_offered_again(self) -> None:
        self.write(
            "### 이미 올린 것\n"
            "- 분류: 프로필\n"
            "- 상태: 승격\n"
            "- 사용자 명시: 예\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-07-30 / ECC / 근거\n"
        )

        payload = HARNESS.promotion_candidates(self.data, self.now)

        self.assertEqual([], payload["ready"])
        self.assertEqual([], payload["waiting"])

    def test_review_output_separates_ready_and_blocked(self) -> None:
        self.write(
            "### 통과하는 것\n"
            "- 분류: 프로필\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 예\n"
            "- 목표: PROFILE.md\n"
            "- 관찰: 2026-07-30 / ECC / 직접 말함\n\n"
            "### 막히는 것\n"
            "- 분류: 취향\n"
            "- 상태: 대기\n"
            "- 사용자 명시: 아니오\n"
            "- 목표: DESIGN-TASTE.md\n"
            "- 관찰: 2026-07-30 / ECC / 한 번만 봄\n"
        )

        text = HARNESS.format_promotion_review(
            HARNESS.promotion_candidates(self.data, self.now)
        )

        self.assertIn("올릴 수 있는 것", text)
        self.assertIn("아직 안 되는 것", text)
        self.assertIn("사용자 승인", text)

    def test_template_ships_with_the_plugin(self) -> None:
        self.assertIn("CANDIDATES.md", HARNESS.GLOBAL_TEMPLATES)
        self.assertTrue((PLUGIN / "templates" / "global" / "CANDIDATES.md").is_file())


if __name__ == "__main__":
    unittest.main()
