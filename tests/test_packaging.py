from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

# Installing a plugin copies its source directory verbatim; there is no ignore
# list. So the plugin source must never contain project state or evidence.
FORBIDDEN_IN_PLUGIN_SOURCE = (".harness", "evals", "tests", "tmp", "site")


def plugin_source_dirs() -> list[Path]:
    payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    sources = []
    for plugin in payload.get("plugins", []):
        source = str(plugin.get("source") or "./")
        sources.append((ROOT / source).resolve())
    return sources


# Organization distribution (Team/Enterprise) has its own source rules:
# npm sources are not supported, and private plugins must live inside the
# marketplace repository and be referenced by a relative path.
ORG_SAFE_SOURCE_KINDS = {"github", "url", "git-subdir"}
PLUGIN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganizationDistributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MARKETPLACE.read_text(encoding="utf-8"))

    def test_marketplace_has_the_fields_organization_sync_reads(self) -> None:
        self.assertTrue(self.manifest.get("name"))
        self.assertTrue(self.manifest.get("owner", {}).get("name"))
        self.assertTrue(self.manifest.get("plugins"))

    def test_plugin_sources_are_relative_or_org_safe(self) -> None:
        for plugin in self.manifest["plugins"]:
            with self.subTest(plugin=plugin.get("name")):
                source = plugin.get("source")
                if isinstance(source, str):
                    self.assertTrue(
                        source.startswith("./"),
                        "조직 배포에서 비공개 플러그인은 저장소 안 상대 경로여야 합니다",
                    )
                    continue
                self.assertIn(source.get("source"), ORG_SAFE_SOURCE_KINDS)
                self.assertNotEqual(
                    "npm",
                    source.get("source"),
                    "조직 배포는 npm 소스를 지원하지 않습니다",
                )

    def test_plugin_names_follow_the_organization_naming_rule(self) -> None:
        for plugin in self.manifest["plugins"]:
            name = plugin.get("name", "")
            with self.subTest(plugin=name):
                self.assertRegex(name, PLUGIN_NAME_RE)
                self.assertLessEqual(len(name), 64)

    def test_plugin_manifest_agrees_with_the_marketplace_entry(self) -> None:
        plugin = json.loads(
            (ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn(
            plugin["name"],
            {entry["name"] for entry in self.manifest["plugins"]},
        )

    def test_packaged_plugin_stays_well_under_the_upload_limit(self) -> None:
        total = sum(
            path.stat().st_size
            for path in (ROOT / "plugin").rglob("*")
            if path.is_file() and "__pycache__" not in str(path)
        )
        self.assertLess(total, 50 * 1024 * 1024)


class PackagingBoundaryTests(unittest.TestCase):
    def test_marketplace_declares_at_least_one_plugin(self) -> None:
        self.assertTrue(plugin_source_dirs())

    def test_plugin_source_ships_no_project_state_or_evidence(self) -> None:
        for source in plugin_source_dirs():
            for name in FORBIDDEN_IN_PLUGIN_SOURCE:
                with self.subTest(source=source.name, entry=name):
                    self.assertFalse(
                        (source / name).exists(),
                        f"{source / name} would be copied into the plugin cache",
                    )

    def test_plugin_source_holds_the_runtime_it_needs(self) -> None:
        for source in plugin_source_dirs():
            for name in (
                ".claude-plugin/plugin.json",
                "hooks/hooks.json",
                "scripts/harness.py",
                "scripts/skill_router.py",
                "config/skill-routing.json",
                "templates",
                "skills",
                "agents",
                "commands",
            ):
                with self.subTest(source=source.name, entry=name):
                    self.assertTrue(
                        (source / name).exists(),
                        f"{source / name} is missing from the plugin source",
                    )

    def test_hooks_reference_only_plugin_relative_paths(self) -> None:
        for source in plugin_source_dirs():
            hooks = json.loads((source / "hooks" / "hooks.json").read_text(encoding="utf-8"))
            events = hooks.get("hooks", {})
            self.assertIn("SessionEnd", events)
            for entries in events.values():
                for entry in entries:
                    for hook in entry.get("hooks", []):
                        command = str(hook.get("command") or "")
                        self.assertTrue(
                            command.startswith("${CLAUDE_PLUGIN_ROOT}/"),
                            f"hook command is not plugin-relative: {command}",
                        )
                        relative = command.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
                        self.assertTrue((source / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
