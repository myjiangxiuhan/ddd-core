"""Regression tests for performance-contract validation and budget comparison."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_budget import ContractError, compare  # type: ignore  # noqa: E402
from validate_contract import validate  # type: ignore  # noqa: E402


@contextmanager
def workspace_temp():
    path = Path(tempfile.mkdtemp(prefix="performance-contract-", dir=ROOT / "tests"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def contract() -> dict[str, object]:
    return {
        "schema_version": "1",
        "id": "file-entry-crud-performance",
        "status": "confirmed",
        "slice_id": "file-entry-crud",
        "seam": "HTTP file-entry list",
        "decisions": [
            {
                "id": "list-budget",
                "source": "user_decision",
                "question": "What is the p95 budget?",
                "answer": "200 ms",
                "evidence": "User confirmed the first-release list budget.",
            }
        ],
        "profile": {
            "id": "go-echo-pgx",
            "version": "1",
            "database": {
                "adapter_profile": "postgresql-16",
                "engine": "postgresql",
                "version": "16",
                "driver": "pgx",
                "query_layer": "sqlc",
            },
        },
        "workload": {
            "dataset": {"rows": 100000, "tenants": 100, "distribution": "skewed"},
            "warmup_seconds": 30,
            "measurement_seconds": 60,
            "scenarios": [
                {
                    "id": "list-root-entries",
                    "operation": "read",
                    "concurrency": 20,
                    "target_rps": 100,
                    "budget": {"p95_ms": 200, "p99_ms": 500, "error_rate_percent": 0.1},
                }
            ],
        },
        "sql": [
            {
                "id": "list-root-entries-query",
                "scenario_id": "list-root-entries",
                "operation": "list",
                "filters": ["owner_id", "parent_id"],
                "joins": [],
                "order": ["created_at", "id"],
                "selected_columns": ["id", "name"],
                "pagination": "keyset",
                "index": "idx_entries_owner_parent_created_id",
                "access_path": "index_range_scan",
                "n_plus_one": False,
                "batch_size": None,
                "transaction": "none",
                "lock_scope": "none",
                "timeout_ms": 500,
                "plan_evidence": ".ddd/performance/plans/list.json",
                "database_mapping": {
                    "profile": "postgresql-16",
                    "capabilities": ["keyset_pagination", "plan"],
                    "native_features": ["PostgreSQL: composite index"],
                    "fallback_or_incompatibility": [],
                    "evidence": ["isolated PostgreSQL 16 plan capture"],
                },
            }
        ],
    }


class PerformanceContractTest(unittest.TestCase):
    def test_confirmed_contract_validates(self) -> None:
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(contract(), sort_keys=False), encoding="utf-8")
            result = validate(path)
            self.assertTrue(result["ok"])
            self.assertEqual(result["sql_entries"], 1)

    def test_confirmed_contract_needs_user_decision(self) -> None:
        value = contract()
        value["decisions"] = []
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "user_decision"):
                validate(path)

    def test_draft_contract_can_keep_a_pending_decision(self) -> None:
        value = contract()
        value["status"] = "draft"
        value["decisions"] = [{"id": "database-version", "source": "pending", "question": "Which version is deployed?"}]
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            self.assertEqual(validate(path)["status"], "draft")

    def test_contract_cannot_claim_the_wrong_database_profile(self) -> None:
        value = contract()
        value["profile"]["database"]["adapter_profile"] = "mysql-8.4"  # type: ignore[index]
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "profile engine"):
                validate(path)

    def test_database_profile_rejects_offset_pagination(self) -> None:
        value = contract()
        value["sql"][0]["pagination"] = "offset"  # type: ignore[index]
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "must follow database profile"):
                validate(path)

    def test_sql_n_plus_one_is_rejected(self) -> None:
        value = contract()
        value["sql"][0]["n_plus_one"] = True  # type: ignore[index]
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "n_plus_one"):
                validate(path)

    def test_confirmed_sql_needs_database_mapping_evidence(self) -> None:
        value = contract()
        value["sql"][0]["database_mapping"]["evidence"] = []  # type: ignore[index]
        with workspace_temp() as root:
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "database_mapping.evidence"):
                validate(path)

    def test_baseline_passes_and_fails_against_fixed_budget(self) -> None:
        with workspace_temp() as root:
            contract_path = root / "contract.yaml"
            baseline_path = root / "baseline.json"
            contract_path.write_text(yaml.safe_dump(contract(), sort_keys=False), encoding="utf-8")
            baseline = {
                "schema_version": "1",
                "contract_id": "file-entry-crud-performance",
                "slice_id": "file-entry-crud",
                "profile": {"id": "go-echo-pgx", "version": "1"},
                "database_profile": "postgresql-16",
                "commit": "abc123",
                "dataset_digest": "seed-1",
                "dataset_rows": 100000,
                "environment": {"database": "postgresql:16"},
                "warmup_seconds": 30,
                "measurement_seconds": 60,
                "concurrency": 20,
                "scenarios": {
                    "list-root-entries": {
                        "concurrency": 20,
                        "p50_ms": 50,
                        "p95_ms": 150,
                        "p99_ms": 300,
                        "throughput_rps": 120,
                        "error_rate_percent": 0,
                    }
                },
            }
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            self.assertEqual(compare(contract_path, baseline_path)["status"], "passed")
            baseline["scenarios"]["list-root-entries"]["p95_ms"] = 201
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            self.assertEqual(compare(contract_path, baseline_path)["status"], "failed")

    def test_baseline_metadata_must_match_contract(self) -> None:
        with workspace_temp() as root:
            contract_path = root / "contract.yaml"
            baseline_path = root / "baseline.json"
            contract_path.write_text(yaml.safe_dump(contract(), sort_keys=False), encoding="utf-8")
            baseline = {
                "schema_version": "1",
                "contract_id": "file-entry-crud-performance",
                "slice_id": "file-entry-crud",
                "profile": {"id": "go-echo-pgx", "version": "1"},
                "database_profile": "postgresql-16",
                "commit": "abc123",
                "dataset_digest": "seed-1",
                "dataset_rows": 100000,
                "environment": {"database": "postgresql:16"},
                "warmup_seconds": 30,
                "measurement_seconds": 60,
                "scenarios": {
                    "list-root-entries": {
                        "concurrency": 19,
                        "p95_ms": 150,
                        "p99_ms": 300,
                        "throughput_rps": 120,
                        "error_rate_percent": 0,
                    }
                },
            }
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            result = compare(contract_path, baseline_path)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["failures"][0]["metric"], "concurrency")

    def test_baseline_cannot_change_database_profile_or_dataset_size(self) -> None:
        with workspace_temp() as root:
            contract_path = root / "contract.yaml"
            baseline_path = root / "baseline.json"
            contract_path.write_text(yaml.safe_dump(contract(), sort_keys=False), encoding="utf-8")
            baseline = {
                "schema_version": "1",
                "contract_id": "file-entry-crud-performance",
                "slice_id": "file-entry-crud",
                "profile": {"id": "go-echo-pgx", "version": "1"},
                "database_profile": "mysql-8.4",
                "commit": "abc123",
                "dataset_digest": "seed-1",
                "dataset_rows": 99999,
                "environment": {"database": "mysql:8.4"},
                "warmup_seconds": 30,
                "measurement_seconds": 60,
                "scenarios": {},
            }
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "database_profile"):
                compare(contract_path, baseline_path)


if __name__ == "__main__":
    unittest.main()
