from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"

# 규칙 자체를 서술하는 파일은 금지 표현을 예시로 인용해야 한다.
RULE_FILES = {
    PLUGIN / "agents" / "personal-copilot.md",
    PLUGIN / "skills" / "ux-writing" / "SKILL.md",
    PLUGIN / "skills" / "ux-writing" / "references" / "korean-voice.md",
    PLUGIN / "skills" / "ux-writing" / "references" / "component-copy.md",
    PLUGIN / "skills" / "adaptive-writing" / "references" / "markdown-rules.md",
}

INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
HANGUL_RE = re.compile(r"[가-힣]")

BANNED = {
    "—": "한국어 문장부호가 아닙니다. 문장을 나누거나 쉼표·콜론으로 바꾸세요",
    "하실 수 있습니다": "과공대입니다. `할 수 있습니다`로 바꾸세요",
    "주시기 바랍니다": "과공대입니다. `해 주세요`로 바꾸세요",
    "성공적으로 완료": "상투구입니다. 무엇이 끝났는지 쓰세요",
    "잠시만 기다려": "상투구입니다. 무엇을 하는 중인지 쓰세요",
    "당신의": "한국어는 주어를 생략합니다",
    "에 있어서": "번역투입니다. `~에서`로 바꾸세요",
    "보여지": "이중 피동입니다. `보이다`로 바꾸세요",
    "잊혀지": "이중 피동입니다. `잊히다`로 바꾸세요",
}


def korean_prose(path: Path) -> str:
    """코드 펜스와 인라인 코드를 걷어낸 본문만 검사 대상으로 남긴다."""
    text = path.read_text(encoding="utf-8")
    text = FENCE_RE.sub(" ", text)
    return INLINE_CODE_RE.sub(" ", text)


def shipped_markdown() -> list[Path]:
    return [
        path
        for path in sorted(PLUGIN.rglob("*.md"))
        if path not in RULE_FILES and HANGUL_RE.search(path.read_text(encoding="utf-8"))
    ]


class KoreanVoiceTests(unittest.TestCase):
    def test_shipped_korean_text_avoids_banned_patterns(self) -> None:
        for path in shipped_markdown():
            prose = korean_prose(path)
            for pattern, reason in BANNED.items():
                with self.subTest(file=path.relative_to(ROOT), pattern=pattern):
                    self.assertNotIn(
                        pattern,
                        prose,
                        f"{path.relative_to(ROOT)}: `{pattern}` — {reason}",
                    )

    def test_rule_files_actually_state_the_rules(self) -> None:
        voice = (
            PLUGIN / "skills" / "ux-writing" / "references" / "korean-voice.md"
        ).read_text(encoding="utf-8")
        for pattern in ("—", "당신", "에 대해", "를 통해", "하실 수 있습니다"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, voice)

    def test_copilot_forbids_the_em_dash_in_korean(self) -> None:
        copilot = (PLUGIN / "agents" / "personal-copilot.md").read_text(encoding="utf-8")
        self.assertIn("em dash", copilot)
        self.assertIn("ux-writing", copilot)

    def test_ux_writing_skill_is_routed_and_bounded(self) -> None:
        import json

        config = json.loads(
            (PLUGIN / "config" / "skill-routing.json").read_text(encoding="utf-8")
        )
        route = next(
            (r for r in config["routes"] if r["skill"] == "ux-writing"), None
        )
        self.assertIsNotNone(route)
        assert route is not None
        # 개발 쪽 에러 처리와 이력서·제안서 문구로 새지 않아야 한다.
        for term in ("에러 로그", "예외 처리", "이력서", "제안서", "커밋 메시지"):
            with self.subTest(term=term):
                self.assertIn(term, route["negative"])


if __name__ == "__main__":
    unittest.main()
