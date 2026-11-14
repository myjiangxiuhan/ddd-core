"""Regression tests for fair Rust database-framework comparisons."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_frameworks import ComparisonError, compare, load_yaml  # type: ignore  # noqa: E402


MATRIX = ROOT / "examples" / "rust-database-framework-comparison.yaml"


def sample_results() -> dict:
    matrix = load_yaml(MATRIX)
    return {
        "schema_version": "1",
        "matrix_id": matrix["id"],
        "database": matrix["controls"]["database"],
        "commit": "abc123",
        "schema_digest": matrix["controls"]["schema_digest"],
        "dataset_digest": matrix["controls"]["seed_digest"],
        "environment_digest": matrix["controls"]["environment_digest"],
        "scenarios": {
            scenario["id"]: {
                framework_id: {
                    "samples": 100,
                    "throughput_rps": 100.0 + index,
                    "p50_ms": 10.0 + index,
                    "p95_ms": 50.0 + index,
                    "p99_ms": 90.0 + index,
                    "error_rate_percent": 0.0,
                }
                for index, framework_id in enumerate(
                    ("rust-axum-sqlx", "rust-axum-tokio-postgres", "rust-axum-toasty")
                )
            }
            for scenario in matrix["workload"]["scenarios"]
        },
    }


class FrameworkComparisonTest(unittest.TestCase):
    def test_matrix_declares_three_layers_with_same_controls(self) -> None:
        report = compare(load_yaml(MATRIX), sample_results())
        self.assertTrue(report["ok"])
        self.assertIsNone(report["comparison"]["list-file-entries"]["overall_winner"])
        self.assertEqual(report["comparison"]["list-file-entries"]["by_p95_ms"][0]["framework"], "rust-axum-sqlx")

    def test_dataset_or_environment_mismatch_is_rejected(self) -> None:
        results = sample_results()
        results["dataset_digest"] = "sha256:other-seed"
        with self.assertRaisesRegex(ComparisonError, "dataset_digest"):
            compare(load_yaml(MATRIX), results)
        results = sample_results()
        results["environment_digest"] = "sha256:other-environment"
        with self.assertRaisesRegex(ComparisonError, "environment_digest"):
            compare(load_yaml(MATRIX), results)

        results = sample_results()
        results["schema_digest"] = "sha256:other-schema"
        with self.assertRaisesRegex(ComparisonError, "schema_digest"):
            compare(load_yaml(MATRIX), results)

    def test_adapter_profile_binding_is_part_of_the_comparison_contract(self) -> None:
        matrix = load_yaml(MATRIX)
        matrix["frameworks"][0]["driver_version"] = "0.8.0"
        with self.assertRaisesRegex(ComparisonError, "driver binding"):
            compare(matrix, sample_results())

        matrix = load_yaml(MATRIX)
        matrix["frameworks"][0]["adapter_profile_digest"] = "sha256:changed"
        with self.assertRaisesRegex(ComparisonError, "digest changed"):
            compare(matrix, sample_results())

    def test_missing_framework_result_is_rejected(self) -> None:
        results = sample_results()
        results["scenarios"]["list-file-entries"].pop("rust-axum-toasty")
        with self.assertRaisesRegex(ComparisonError, "every framework"):
            compare(load_yaml(MATRIX), results)

    def test_diesel_cannot_be_added_to_the_comparison(self) -> None:
        matrix = load_yaml(MATRIX)
        matrix["frameworks"][0]["driver"] = "diesel"
        with self.assertRaisesRegex(ComparisonError, "Diesel"):
            compare(matrix, sample_results())

    def test_result_file_can_be_round_tripped_as_json(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="framework-results-") as directory:
            path = Path(directory) / "results.json"
            path.write_text(json.dumps(sample_results()), encoding="utf-8")
            self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
