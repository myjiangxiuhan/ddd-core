#!/usr/bin/env python3
"""Regression tests for the signed database-profile and performance gates."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from approval_test import (  # type: ignore
    APPROVAL,
    REPO,
    TEST_RUNNER,
    TRUST_TEMP_ROOT,
    WORKFLOW,
    fixed_trust_paths,
    provision_receipt_chain,
)

PERFORMANCE = REPO / "performance-loop"
PROFILE_SOURCE = PERFORMANCE / "profiles" / "postgresql-16.yaml"
SQL_SPEC_SOURCE = PERFORMANCE / "examples" / "file-entry-crud.sql.yaml"


class DatabaseGateRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.run_root = Path(tempfile.mkdtemp(prefix="database-gate-test-", dir=REPO))
        self.project = self.run_root / "project"
        (self.project / ".ddd" / "approvals" / "requests").mkdir(parents=True)
        (self.project / ".ddd" / "approvals" / "credentials").mkdir(parents=True)
        (self.project / ".ddd" / "performance-profiles").mkdir(parents=True)
        (self.project / ".ddd" / "performance").mkdir(parents=True)
        self.trust = Path(tempfile.mkdtemp(prefix="database-gate-trust-", dir=TRUST_TEMP_ROOT))
        self.trust_paths = fixed_trust_paths(self.project, self.trust)
        self.private_key = self.trust / "private.pem"
        self.public_key = self.trust_paths["public_key"]
        self.state = self.project / ".ddd" / "workflow-state.json"
        (self.project / ".ddd" / "mainline.md").write_text("A database-backed slice mainline.\n", encoding="utf-8")
        self.profile_path = self.project / ".ddd" / "performance-profiles" / "postgresql-16.yaml"
        shutil.copyfile(PROFILE_SOURCE, self.profile_path)
        self.contract_path = self.project / ".ddd" / "performance" / "admin-shell-template.yaml"
        contract = yaml.safe_load((PERFORMANCE / "examples" / "file-entry-crud.yaml").read_text(encoding="utf-8"))
        contract["status"] = "confirmed"
        contract["slice_id"] = "admin-shell-template"
        contract["decisions"][0].update({
            "source": "user_decision",
            "answer": "p95 <= 200 ms, p99 <= 500 ms",
            "evidence": "The user confirmed the first-release performance budget.",
        })
        self.contract_path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
        self.sql_spec_path = self.project / ".ddd" / "performance" / "list.sql.yaml"
        shutil.copyfile(SQL_SPEC_SOURCE, self.sql_spec_path)
        self.baseline_path = self.project / ".ddd" / "performance" / "admin-shell-template.baseline.json"
        self.baseline_path.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "contract_id": contract["id"],
                    "slice_id": "admin-shell-template",
                    "profile": {"id": "go-echo-pgx", "version": "1"},
                    "database_profile": "postgresql-16",
                    "commit": "test-commit",
                    "dataset_digest": "test-dataset",
                    "dataset_rows": 100000,
                    "environment": {"database": "postgresql:16", "host": "isolated"},
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
        self.state.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "control_mode": "human_led",
                    "project": {"goal": "database gate regression"},
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
        self.exec_cmd("python", str(APPROVAL), "keygen", "--private-key", str(self.private_key), "--public-key", str(self.public_key), check=True)
        from cryptography.hazmat.primitives import serialization

        public = serialization.load_pem_public_key(self.public_key.read_bytes())
        der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.trust_paths["manifest"].write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "algorithm": "Ed25519",
                    "project_root": str(self.project),
                    "public_key": str(self.public_key),
                    "public_key_fingerprint": __import__("hashlib").sha256(der).hexdigest(),
                    "receipt_store": str(self.trust_paths["receipt_store"]),
                    "receipt_anchor": str(self.trust_paths["receipt_anchor"]),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        provision_receipt_chain(self.trust_paths)

    def tearDown(self) -> None:
        shutil.rmtree(self.run_root, ignore_errors=True)
        shutil.rmtree(self.trust, ignore_errors=True)

    def exec_cmd(self, *command: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(self.run_root / "forged-home")
        env["USERPROFILE"] = str(self.run_root / "forged-profile")
        result = subprocess.run(
            ("python", str(TEST_RUNNER), command[1], str(self.trust), *command[2:]) if len(command) > 1 and command[0] == "python" else command,
            cwd=REPO,
            text=True,
            capture_output=True,
            env=env,
        )
        if check and result.returncode:
            self.fail(result.stdout + result.stderr)
        return result

    def signed_transition(self, transition: str, evidence: str, extra: dict[str, object], records: list[str] = None) -> None:
        state = json.loads(self.state.read_text(encoding="utf-8"))
        namespace = argparse.Namespace(
            transition=transition,
            evidence=evidence,
            decision_id=None,
            answer=None,
            artifact=None,
            slice_id=None,
            slice_name=None,
            requires_database=None,
            profile_id=None,
            profile_version=None,
            database_profile_id=None,
            database_profile_version=None,
            database_profile_path=None,
            performance_record=None,
        )
        for key, value in extra.items():
            setattr(namespace, key, value)
        import sys

        sys.path.insert(0, str(REPO / "ddd-core" / "scripts"))
        from workflow_gate import approval_arguments  # type: ignore

        arguments = approval_arguments(state, namespace)
        request_args = [
            "python",
            str(APPROVAL),
            "request",
            "--state",
            str(self.state),
            "--action",
            f"workflow:{transition}",
            "--arguments-json",
            json.dumps(arguments, separators=(",", ":")),
            "--output",
            ".ddd/approvals/requests",
        ]
        for record in records or []:
            request_args.extend(["--record", record])
        requested = self.exec_cmd(*request_args, check=True)
        info = json.loads(requested.stdout)
        request_path = self.project / info["path"]
        credential = self.project / ".ddd" / "approvals" / "credentials" / f"{transition}.json"
        self.exec_cmd(
            "python",
            str(APPROVAL),
            "sign",
            "--request",
            str(request_path),
            "--private-key",
            str(self.private_key),
            "--expected-payload-digest",
            info["payload_digest"],
            "--output",
            str(credential),
            check=True,
        )
        command = [
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            transition,
            "--evidence",
            evidence,
            "--approval",
            str(credential),
            "--trusted-public-key",
            str(self.public_key),
        ]
        for key, value in extra.items():
            flag = "--" + key.replace("_", "-")
            if isinstance(value, bool):
                if value:
                    command.append(flag)
            else:
                command.extend([flag, str(value)])
        result = self.exec_cmd(*command)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def advance_to_database_profile(self) -> None:
        self.advance_to_technology()
        self.signed_transition(
            "select-database-profile",
            "User selected PostgreSQL 16 for this slice.",
            {
                "database_profile_id": "postgresql-16",
                "database_profile_version": "16",
                "database_profile_path": ".ddd/performance-profiles/postgresql-16.yaml",
            },
            [".ddd/performance-profiles/postgresql-16.yaml"],
        )

    def advance_to_technology(self) -> None:
        self.signed_transition("confirm-mainline", "User confirmed the mainline.", {"artifact": ".ddd/mainline.md"}, [".ddd/mainline.md"])
        self.signed_transition("confirm-design", "User confirmed the design.", {})
        self.signed_transition(
            "approve-slice",
            "User approved the database-backed slice.",
            {"slice_id": "admin-shell-template", "slice_name": "Database-backed slice", "requires_database": True},
        )
        self.signed_transition("select-profile", "User selected the application profile.", {"profile_id": "go-echo-pgx", "profile_version": "1"})

    def test_database_profile_is_required_before_sql_or_baseline(self) -> None:
        self.advance_to_technology()
        generated = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            "postgresql-16",
            str(self.sql_spec_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertNotEqual(generated.returncode, 0)
        self.assertIn("database_profile", generated.stdout)
        baseline = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "compare_budget.py"),
            str(self.contract_path),
            str(self.baseline_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertNotEqual(baseline.returncode, 0)
        self.assertIn("database_profile", baseline.stdout)

    def test_profile_and_performance_approvals_gate_generation_delivery_and_baseline(self) -> None:
        self.advance_to_database_profile()
        before_confirm = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--require",
            "delivery",
            "--trusted-public-key",
            str(self.public_key),
        )
        self.assertNotEqual(before_confirm.returncode, 0)
        self.assertIn("performance_contract", before_confirm.stdout)
        blocked_baseline = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "compare_budget.py"),
            str(self.contract_path),
            str(self.baseline_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertNotEqual(blocked_baseline.returncode, 0)
        self.assertIn("performance_contract", blocked_baseline.stdout)
        generated_before_confirmation = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            "postgresql-16",
            str(self.sql_spec_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertEqual(generated_before_confirmation.returncode, 0, generated_before_confirmation.stdout)
        self.signed_transition(
            "confirm-performance",
            "User confirmed the performance contract and database mapping.",
            {"performance_record": ".ddd/performance/admin-shell-template.yaml"},
            [".ddd/performance/admin-shell-template.yaml"],
        )
        performance_allowed = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--require",
            "performance",
            "--trusted-public-key",
            str(self.public_key),
        )
        self.assertEqual(performance_allowed.returncode, 0, performance_allowed.stdout)
        wrong_profile = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            "mysql-8.4",
            str(self.sql_spec_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertNotEqual(wrong_profile.returncode, 0)
        self.assertIn("does not match", wrong_profile.stdout)
        generated = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            "postgresql-16",
            str(self.sql_spec_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertEqual(generated.returncode, 0, generated.stdout)
        self.assertIn("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)", generated.stdout)
        passed = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "compare_budget.py"),
            str(self.contract_path),
            str(self.baseline_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertEqual(passed.returncode, 0, passed.stdout)
        self.assertIn('"status": "passed"', passed.stdout)
        allowed = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--require",
            "delivery",
            "--trusted-public-key",
            str(self.public_key),
        )
        self.assertEqual(allowed.returncode, 0, allowed.stdout)

    def test_forged_database_gate_without_signed_history_is_rejected(self) -> None:
        self.advance_to_database_profile()
        state = json.loads(self.state.read_text(encoding="utf-8"))
        state["gates"]["performance_contract"] = "confirmed"
        state["performance_contract"] = {
            "path": ".ddd/performance/admin-shell-template.yaml",
            "digest": __import__("hashlib").sha256(self.contract_path.read_bytes()).hexdigest(),
            "slice_id": "admin-shell-template",
            "database_profile": "postgresql-16",
        }
        state["history"] = [item for item in state["history"] if item.get("transition") != "select-database-profile"]
        self.state.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        forged = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            "postgresql-16",
            str(self.sql_spec_path),
            "--state",
            str(self.state),
            "--trusted-public-key",
            str(self.public_key),
            "--profiles-dir",
            str(self.project / ".ddd" / "performance-profiles"),
        )
        self.assertNotEqual(forged.returncode, 0)
        self.assertIn("select-database-profile", forged.stdout)

    def test_sql_generator_requires_workflow_and_trusted_key(self) -> None:
        result = self.exec_cmd(
            "python",
            str(PERFORMANCE / "scripts" / "generate_sql.py"),
            "postgresql-16",
            str(SQL_SPEC_SOURCE),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--state", result.stderr)


if __name__ == "__main__":
    unittest.main()
