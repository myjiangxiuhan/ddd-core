#!/usr/bin/env python3
"""Regression tests for project-local database and performance evidence."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / "ddd-core" / "scripts" / "workflow_gate.py"
PERFORMANCE = REPO / "performance-loop"
PROFILE_SOURCE = PERFORMANCE / "profiles" / "postgresql-18.yaml"
SQL_SPEC_SOURCE = PERFORMANCE / "examples" / "file-entry-crud.sql.yaml"


class DatabaseGateRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.run_root = Path(tempfile.mkdtemp(prefix="database-evidence-test-", dir=REPO))
        self.project = self.run_root / "project"
        ddd = self.project / ".ddd"
        (ddd / "performance-profiles").mkdir(parents=True)
        (ddd / "performance").mkdir(parents=True)
        self.attacker_profile_dir = ddd / "attacker-profiles"
        self.attacker_profile_dir.mkdir()
        (ddd / "mainline.md").write_text("A database-backed slice mainline.\n", encoding="utf-8")
        self.profile_path = ddd / "performance-profiles" / "postgresql-18.yaml"
        shutil.copyfile(PROFILE_SOURCE, self.profile_path)
        self.contract_path = ddd / "performance" / "admin-shell-template.yaml"
        contract = yaml.safe_load((PERFORMANCE / "examples" / "file-entry-crud.yaml").read_text(encoding="utf-8"))
        contract["status"] = "confirmed"
        contract["slice_id"] = "admin-shell-template"
        contract["baseline"]["result"] = ".ddd/performance/admin-shell-template.baseline.json"
        contract["decisions"][0].update({
            "source": "user_decision",
            "answer": "p95 <= 200 ms, p99 <= 500 ms",
            "evidence": "The user confirmed the first-release performance budget.",
        })
        self.contract_path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
        self.sql_spec_path = ddd / "performance" / "list.sql.yaml"
        shutil.copyfile(SQL_SPEC_SOURCE, self.sql_spec_path)
        self.baseline_path = ddd / "performance" / "admin-shell-template.baseline.json"
        self.baseline_path.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "contract_id": contract["id"],
                    "slice_id": "admin-shell-template",
                    "profile": {"id": "go-echo-pgx", "version": "1"},
                    "database_profile": "postgresql-18",
                    "commit": "test-commit",
                    "dataset_digest": "test-dataset",
                    "dataset_rows": 100000,
                    "environment": {"database": "postgresql:18", "host": "isolated"},
                    "warmup_seconds": 30,
                    "measurement_seconds": 60,
                    "scenarios": {
                        "list-root-entries": {
                            "concurrency": 20,
                            "p50_ms": 50,
                            "p95_ms": 150,
                            "p99_ms": 300,
                            "throughput_rps": 120,
                            "error_rate_percent": 0,
                            "db_cpu_percent": 40,
                            "db_connections": 12,
                        }
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.state = ddd / "workflow-state.json"
        self.state.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "control_mode": "human_led",
                    "project": {"goal": "database evidence regression"},
                    "scope": {"current_slice_candidate": {"id": "admin-shell-template", "name": "Database-backed slice"}},
                    "decisions": [],
                    "gates": {
                        "phase": "business_discovery",
                        "business_discovery": "draft",
                        "domain_design": "draft",
                        "slice_approval": "pending",
                        "technology_profile": "pending",
                        "ui_system": "not_started",
                        "ui_practices": "not_started",
                        "ui_design": "not_started",
                        "delivery": "not_started",
                        "review": "not_started",
                    },
                    "active_slice": None,
                    "business_artifact": ".ddd/mainline.md",
                    "history": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.run_root, ignore_errors=True)

    def run_cmd(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        result = subprocess.run(("python", *args), cwd=REPO, text=True, capture_output=True, env=env)
        if check and result.returncode:
            self.fail(result.stdout + result.stderr)
        return result

    def transition(self, name: str, *extra: str) -> None:
        result = self.run_cmd(
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            name,
            "--evidence",
            f"User recorded {name}.",
            *extra,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def advance_to_technology(self) -> None:
        self.transition("confirm-mainline")
        self.transition("confirm-design")
        self.transition("approve-slice", "--slice-id", "admin-shell-template", "--slice-name", "Database-backed slice", "--requires-database")
        self.transition("select-profile", "--profile-id", "go-echo-pgx", "--profile-version", "1")

    def select_database(self) -> None:
        self.advance_to_technology()
        self.transition(
            "select-database-profile",
            "--database-profile-id",
            "postgresql-18",
            "--database-profile-version",
            "18",
            "--database-profile-path",
            ".ddd/performance-profiles/postgresql-18.yaml",
        )

    def record_performance(self) -> None:
        self.select_database()
        self.transition("record-performance", "--performance-record", ".ddd/performance/admin-shell-template.yaml")

    def sql_command(self, profile: str = "postgresql-18", *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_cmd(
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            profile,
            str(self.sql_spec_path),
            "--state",
            str(self.state),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
            *extra,
        )

    def compare_command(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_cmd(
            str(PERFORMANCE / "scripts" / "compare_budget.py"),
            str(self.contract_path),
            str(self.baseline_path),
            "--state",
            str(self.state),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
            *extra,
        )

    def test_database_profile_is_required_before_sql(self) -> None:
        self.advance_to_technology()
        result = self.sql_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("database_profile", result.stdout)

    def test_mechanical_transition_can_use_generated_history_evidence(self) -> None:
        self.advance_to_technology()
        result = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--transition", "start-delivery")
        self.assertEqual(result.returncode, 0, result.stdout)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["history"][-1]["evidence"], "mechanical transition: start-delivery")

    def test_record_performance_is_mechanical_bookkeeping(self) -> None:
        self.select_database()
        result = self.run_cmd(
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "record-performance",
            "--performance-record",
            ".ddd/performance/admin-shell-template.yaml",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["history"][-1]["evidence"], "mechanical transition: record-performance")

    def test_user_transition_still_requires_evidence(self) -> None:
        result = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--transition", "confirm-mainline")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--evidence", result.stdout)

    def test_record_mainline_does_not_need_a_start_marker(self) -> None:
        result = self.run_cmd(
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "record-mainline",
            "--artifact",
            ".ddd/mainline.md",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["gates"]["business_discovery"], "draft")

    def test_start_business_lab_is_not_a_public_transition(self) -> None:
        result = self.run_cmd(
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "start-business-lab",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_ui_system_check_can_run_before_technology_selection(self) -> None:
        result = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--require", "ui-system")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_technology_neutral_ui_system_record_can_be_confirmed_before_profile(self) -> None:
        ui_record = {
            "schema_version": "1",
            "status": "draft",
            "profile": None,
            "profile_version": None,
            "decisions": [],
        }
        ui_path = self.project / ".ddd" / "ui-system.yaml"
        ui_path.write_text(yaml.safe_dump(ui_record, sort_keys=False), encoding="utf-8")
        ui_record["status"] = "confirmed"
        ui_record["decisions"] = [{
            "source": "user_decision",
            "evidence": "The user confirmed technology-neutral visual roles.",
        }]
        ui_path.write_text(yaml.safe_dump(ui_record, sort_keys=False), encoding="utf-8")
        required = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--require", "ui-system")
        self.assertEqual(required.returncode, 0, required.stdout + required.stderr)
        self.assertEqual(yaml.safe_load(ui_path.read_text(encoding="utf-8"))["status"], "confirmed")

    def test_profile_directory_substitution_is_rejected(self) -> None:
        self.select_database()
        result = self.sql_command("postgresql-18", "--profiles-dir", str(self.attacker_profile_dir))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--profiles-dir", result.stdout)

    def test_selected_profile_replacement_is_rejected(self) -> None:
        self.select_database()
        self.profile_path.write_text(self.profile_path.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        result = self.sql_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest", result.stdout)

    def test_plain_database_and_performance_records_are_supporting_evidence(self) -> None:
        self.select_database()
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertNotIn("database_profile", state["gates"])
        generated = self.sql_command()
        self.assertEqual(generated.returncode, 0, generated.stdout)
        self.transition("record-performance", "--performance-record", ".ddd/performance/admin-shell-template.yaml")
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertNotIn("performance_contract", state["gates"])
        required = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--require", "performance")
        self.assertEqual(required.returncode, 0, required.stdout)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["gates"]["phase"], "delivery")
        compared_before_record = self.compare_command()
        self.assertEqual(compared_before_record.returncode, 0, compared_before_record.stdout)
        compared = self.compare_command()
        self.assertEqual(compared.returncode, 0, compared.stdout)

    def test_contract_replacement_is_rejected(self) -> None:
        self.record_performance()
        self.contract_path.write_text(self.contract_path.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        result = self.compare_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest", result.stdout)

    def test_baseline_budget_failure_is_reported(self) -> None:
        self.record_performance()
        baseline = json.loads(self.baseline_path.read_text(encoding="utf-8"))
        baseline["scenarios"]["list-root-entries"]["p95_ms"] = 9999
        self.baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
        result = self.compare_command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"status": "failed"', result.stdout)

    def test_sql_generator_rejects_profile_mismatch(self) -> None:
        self.select_database()
        result = self.sql_command("mysql-8.4")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match", result.stdout)

    def test_delivery_does_not_require_performance_record(self) -> None:
        self.select_database()
        result = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--require", "delivery")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_delivery_still_stops_for_an_existing_unconfirmed_ui_plan(self) -> None:
        self.select_database()
        (self.project / ".ddd" / "ui-plan.yaml").write_text("schema_version: '1'\nstatus: draft\n", encoding="utf-8")
        result = self.run_cmd(str(WORKFLOW), "--state", str(self.state), "--require", "delivery")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ui-plan.yaml", result.stdout)


if __name__ == "__main__":
    unittest.main()
