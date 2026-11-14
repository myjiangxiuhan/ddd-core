"""Regression tests for database profiles and dialect-specific SQL generation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_sql import SqlGenerationError, generate  # type: ignore  # noqa: E402
from profile_loader import load_profile  # type: ignore  # noqa: E402
from validate_contract import validate  # type: ignore  # noqa: E402


LIST_SPEC = {
    "operation": "list",
    "table": "file_entries",
    "columns": ["id", "name", "created_at"],
    "filters": [
        {"column": "owner_id", "operator": "="},
        {"column": "deleted_at", "operator": "is_null"},
    ],
    "order_by": [
        {"column": "created_at", "direction": "asc"},
        {"column": "id", "direction": "asc"},
    ],
    "pagination": {"kind": "keyset", "cursor_columns": ["created_at", "id"], "limit": 50},
}


UPSERT_SPEC = {
    "operation": "upsert",
    "table": "file_entries",
    "insert_columns": ["owner_id", "name", "size_bytes"],
    "conflict_columns": ["owner_id", "name"],
    "update_columns": ["size_bytes"],
    "returning_columns": ["id"],
    "concurrency_strategy": "serializable",
}


class DatabaseProfileTest(unittest.TestCase):
    def test_all_bundled_profiles_validate(self) -> None:
        for profile_id in ("postgresql-16", "mysql-8.4", "sqlite-3.45", "sqlserver-2022"):
            profile = load_profile(profile_id)
            self.assertEqual(profile["id"], profile_id)
            self.assertIn("upsert", profile["capabilities"])
            self.assertIn("keyset_pagination", profile["capabilities"])
            self.assertIn("plan", profile["capabilities"])

    def test_list_generation_uses_each_database_dialect(self) -> None:
        expected = {
            "postgresql-16": ('"file_entries"', "$1", "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)"),
            "mysql-8.4": ("`file_entries`", "?", "EXPLAIN ANALYZE"),
            "sqlite-3.45": ('"file_entries"', "?", "EXPLAIN QUERY PLAN"),
            "sqlserver-2022": ("[file_entries]", "@p1", "SET STATISTICS IO, TIME ON"),
        }
        for profile_id, (table_marker, parameter_marker, plan_marker) in expected.items():
            result = generate(load_profile(profile_id), LIST_SPEC)
            self.assertIn(table_marker, result["sql"])
            self.assertIn(parameter_marker, result["sql"])
            self.assertIn(plan_marker, result["plan_command"])
            self.assertNotIn("SELECT *", result["sql"])

    def test_postgresql_sql_uses_native_upsert_and_returning(self) -> None:
        result = generate(load_profile("postgresql-16"), UPSERT_SPEC)
        self.assertIn("ON CONFLICT", result["sql"])
        self.assertIn("EXCLUDED", result["sql"])
        self.assertIn("RETURNING", result["sql"])

    def test_sqlite_sql_uses_native_upsert_and_returning(self) -> None:
        result = generate(load_profile("sqlite-3.45"), UPSERT_SPEC)
        self.assertIn("ON CONFLICT", result["sql"])
        self.assertIn("excluded", result["sql"])
        self.assertIn("RETURNING", result["sql"])

    def test_mysql_rejects_unsupported_atomic_returning(self) -> None:
        with self.assertRaisesRegex(SqlGenerationError, "does not support atomic upsert returning"):
            generate(load_profile("mysql-8.4"), UPSERT_SPEC)
        spec = dict(UPSERT_SPEC)
        spec["returning_columns"] = []
        result = generate(load_profile("mysql-8.4"), spec)
        self.assertIn("ON DUPLICATE KEY UPDATE", result["sql"])
        self.assertIn("AS new", result["sql"])

    def test_sqlserver_uses_transactional_update_insert_and_never_merge(self) -> None:
        result = generate(load_profile("sqlserver-2022"), UPSERT_SPEC)
        self.assertIn("BEGIN TRANSACTION", result["sql"])
        self.assertIn("OUTPUT inserted.[id]", result["sql"])
        self.assertIn("SERIALIZABLE", result["sql"])
        self.assertNotIn("MERGE", result["sql"])

    def test_sqlserver_upsert_requires_concurrency_strategy(self) -> None:
        spec = dict(UPSERT_SPEC)
        spec.pop("concurrency_strategy")
        with self.assertRaisesRegex(SqlGenerationError, "concurrency_strategy"):
            generate(load_profile("sqlserver-2022"), spec)

    def test_raw_identifiers_are_rejected(self) -> None:
        spec = dict(LIST_SPEC)
        spec["table"] = "file_entries; DROP TABLE users"
        with self.assertRaisesRegex(SqlGenerationError, "unsafe identifier"):
            generate(load_profile("postgresql-16"), spec)

    def test_joins_do_not_get_silently_dropped(self) -> None:
        spec = dict(LIST_SPEC)
        spec["joins"] = [{"table": "file_contents"}]
        with self.assertRaisesRegex(SqlGenerationError, "joins are not supported"):
            generate(load_profile("postgresql-16"), spec)

    def test_profile_directory_can_be_project_configured(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="database-profiles-") as directory:
            configured = Path(directory)
            source = (ROOT / "profiles" / "postgresql-16.yaml").read_text(encoding="utf-8")
            (configured / "team-postgresql.yaml").write_text(
                source.replace("id: postgresql-16", "id: team-postgresql", 1),
                encoding="utf-8",
            )
            profile = load_profile("team-postgresql", profiles_dir=configured)
            self.assertEqual(profile["engine"], "postgresql")
            self.assertEqual(profile["version"], "16")

    def test_each_database_profile_validates_a_matching_performance_contract(self) -> None:
        cases = {
            "postgresql-16": ("postgresql", "16"),
            "mysql-8.4": ("mysql", "8.4"),
            "sqlite-3.45": ("sqlite", "3.45"),
            "sqlserver-2022": ("sqlserver", "2022"),
        }
        for profile_id, (engine, version) in cases.items():
            contract = {
                "schema_version": "1",
                "id": f"{profile_id}-contract",
                "status": "confirmed",
                "slice_id": "list-entries",
                "seam": "HTTP list entries",
                "decisions": [
                    {
                        "id": "budget",
                        "source": "user_decision",
                        "question": "What is the p95 budget?",
                        "answer": "200 ms",
                        "evidence": "User supplied the target.",
                    }
                ],
                "profile": {
                    "id": "runtime",
                    "version": "1",
                    "database": {
                        "adapter_profile": profile_id,
                        "engine": engine,
                        "version": version,
                        "driver": "test-driver",
                        "query_layer": "raw-sql",
                    },
                },
                "workload": {
                    "dataset": {"rows": 100000, "distribution": "skewed"},
                    "warmup_seconds": 1,
                    "measurement_seconds": 2,
                    "scenarios": [
                        {
                            "id": "list",
                            "operation": "read",
                            "concurrency": 2,
                            "target_rps": 10,
                            "budget": {"p95_ms": 200, "p99_ms": 500, "error_rate_percent": 0},
                        }
                    ],
                },
                "sql": [
                    {
                        "id": "list-query",
                        "scenario_id": "list",
                        "operation": "list",
                        "filters": ["owner_id"],
                        "joins": [],
                        "order": ["created_at", "id"],
                        "selected_columns": ["id", "name"],
                        "pagination": "keyset",
                        "index": "idx_entries_owner_created_id",
                        "access_path": "index_range_scan",
                        "n_plus_one": False,
                        "batch_size": None,
                        "transaction": "none",
                        "lock_scope": "none",
                        "timeout_ms": 500,
                        "plan_evidence": ".ddd/performance/plans/list.json",
                        "database_mapping": {
                            "profile": profile_id,
                            "capabilities": ["keyset_pagination", "plan"],
                            "native_features": [f"{engine}: keyset and plan evidence"],
                            "fallback_or_incompatibility": [],
                            "evidence": [f"isolated {engine} plan capture"],
                        },
                    }
                ],
            }
            with tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="database-contract-") as directory:
                path = Path(directory) / "contract.yaml"
                path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
                self.assertEqual(validate(path)["status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
