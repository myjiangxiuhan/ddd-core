"""Regression tests for the repository-wide skill contract."""

from __future__ import annotations

import sys
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ddd-core" / "scripts"))

from skill_lint import SkillContractError, validate_skill  # type: ignore  # noqa: E402


class SkillContractTest(unittest.TestCase):
    def test_every_skill_has_matching_metadata_and_stop_boundary(self) -> None:
        skills = sorted(ROOT.rglob("SKILL.md"))
        self.assertGreaterEqual(len(skills), 1)
        for path in skills:
            metadata = validate_skill(path)
            self.assertEqual(metadata.name, path.parent.name)

    def test_grilling_and_feedback_loop_are_model_invoked(self) -> None:
        for name in ("grilling", "feedback-loop"):
            metadata = validate_skill(ROOT / name / "SKILL.md")
            self.assertTrue(metadata.allow_implicit_invocation)

    def test_compact_delegating_wrapper_does_not_need_a_full_stop_section(self) -> None:
        root = ROOT / ".tmp-skill-wrapper" / "thin-wrapper"
        shutil.rmtree(root.parent, ignore_errors=True)
        try:
            (root / "agents").mkdir(parents=True)
            (root / "SKILL.md").write_text(
                "---\nname: thin-wrapper\ndescription: Delegate one focused workflow\n---\n"
                "# thin-wrapper\n\nThis is a user-invoked wrapper.\n\n"
                "## Delegates\n\nCall the Skill tool for `grilling`, then return the result.\n",
                encoding="utf-8",
            )
            (root / "agents" / "openai.yaml").write_text(
                "interface:\n  default_prompt: Use the thin wrapper\n"
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            metadata = validate_skill(root / "SKILL.md")
            self.assertFalse(metadata.allow_implicit_invocation)
        finally:
            shutil.rmtree(root.parent, ignore_errors=True)

    def test_invalid_openai_metadata_is_rejected_instead_of_passing_regex_checks(self) -> None:
        root = ROOT / ".tmp-invalid-metadata" / "broken-skill"
        shutil.rmtree(root.parent, ignore_errors=True)
        try:
            (root / "agents").mkdir(parents=True)
            (root / "SKILL.md").write_text(
                "---\nname: broken-skill\ndescription: Catch malformed metadata\n---\n"
                "# broken-skill\n\nThis is a user-invoked skill.\n\n## Hard stops\n\n- Stop.\n",
                encoding="utf-8",
            )
            (root / "agents" / "openai.yaml").write_text(
                "interface:\n  default_prompt: broken\n    bad_indent: true\n"
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            with self.assertRaises(SkillContractError):
                validate_skill(root / "SKILL.md")
        finally:
            shutil.rmtree(root.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
