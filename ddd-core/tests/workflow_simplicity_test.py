#!/usr/bin/env python3
"""Regression tests for the lightweight workflow ledger boundaries."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "ddd-core" / "scripts" / "workflow_gate.py"
FORMAL_PROJECT = ROOT / "template-kit" / "examples" / "formal-flow-project"


class WorkflowSimplicityTest(unittest.TestCase):
    def run_require(self, state: Path, target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("python", str(WORKFLOW), "--state", str(state), "--require", target),
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_ui_records_are_authoritative_without_mirror_gate_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-light-", dir=ROOT) as directory:
            project = Path(directory) / "project"
            shutil.copytree(FORMAL_PROJECT, project)
            state_path = project / ".ddd" / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            for field in ("ui_system", "ui_practices", "ui_design"):
                state["gates"].pop(field, None)
            state["gates"]["delivery"] = "verified"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            ui_design = self.run_require(state_path, "ui-design")
            self.assertEqual(ui_design.returncode, 0, ui_design.stdout + ui_design.stderr)
            review = self.run_require(state_path, "review")
            self.assertEqual(review.returncode, 0, review.stdout + review.stderr)

    def test_draft_ui_transitions_are_not_public_user_tasks(self) -> None:
        state = FORMAL_PROJECT / ".ddd" / "workflow-state.json"
        for transition in (
            "draft-ui-system",
            "draft-ui-practices",
            "draft-ui",
            "confirm-ui-system",
            "confirm-ui-practices",
            "confirm-ui",
            "confirm-performance",
        ):
            result = subprocess.run(
                ("python", str(WORKFLOW), "--state", str(state), "--transition", transition),
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0, transition)

    def test_reset_removes_legacy_ui_gate_summaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-reset-", dir=ROOT) as directory:
            project = Path(directory) / "project"
            shutil.copytree(FORMAL_PROJECT, project)
            state_path = project / ".ddd" / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["gates"].update({
                "delivery": "verified",
                "review": "passed",
                "ui_system": "confirmed",
                "ui_practices": "confirmed",
                "ui_design": "confirmed",
            })
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = subprocess.run(
                (
                    "python",
                    str(WORKFLOW),
                    "--state",
                    str(state_path),
                    "--transition",
                    "reset-slice",
                    "--evidence",
                    "user reset the completed slice",
                ),
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = json.loads(state_path.read_text(encoding="utf-8"))
            for field in ("ui_system", "ui_practices", "ui_design"):
                self.assertNotIn(field, updated["gates"])

    def test_select_profile_can_record_independent_components(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-components-", dir=ROOT) as directory:
            project = Path(directory) / "project"
            shutil.copytree(FORMAL_PROJECT, project)
            state_path = project / ".ddd" / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["gates"]["technology_profile"] = "pending"
            state["gates"]["phase"] = "technology"
            state.pop("technology_profile", None)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = subprocess.run(
                (
                    "python",
                    str(WORKFLOW),
                    "--state",
                    str(state_path),
                    "--transition",
                    "select-profile",
                    "--component",
                    "language:rust:1.95",
                    "--component",
                    "framework:axum:0.8.9",
                    "--component",
                    "runtime:tokio:1.54.1",
                    "--component",
                    "data_access:sqlx:0.9.0",
                    "--evidence",
                    "user selected independent application components",
                ),
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["technology_profile"]["id"], "project-components")
            self.assertEqual(
                [item["id"] for item in updated["technology_profile"]["components"]],
                ["rust", "axum", "tokio", "sqlx"],
            )

    def test_select_profile_allows_composable_go_data_access_components(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-go-components-", dir=ROOT) as directory:
            project = Path(directory) / "project"
            shutil.copytree(FORMAL_PROJECT, project)
            state_path = project / ".ddd" / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["gates"]["technology_profile"] = "pending"
            state["gates"]["phase"] = "technology"
            state.pop("technology_profile", None)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            result = subprocess.run(
                (
                    "python",
                    str(WORKFLOW),
                    "--state",
                    str(state_path),
                    "--transition",
                    "select-profile",
                    "--component",
                    "language:go:project-selected",
                    "--component",
                    "framework:echo:project-selected",
                    "--component",
                    "data_access:pgx:project-selected",
                    "--component",
                    "data_access:sqlc:project-selected",
                    "--evidence",
                    "user selected pgx and sqlc as separate data-access components",
                ),
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [item["id"] for item in updated["technology_profile"]["components"]],
                ["go", "echo", "pgx", "sqlc"],
            )


if __name__ == "__main__":
    unittest.main()
