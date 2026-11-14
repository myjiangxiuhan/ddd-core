"""Regression tests for the Rust backend adapter profiles."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from profile_loader import ProfileError, load_profile, validate_profile  # type: ignore  # noqa: E402


PROFILES = (
    "rust-axum-sqlx",
    "rust-axum-tokio-postgres",
    "rust-axum-toasty",
)


class RustAdapterProfileTest(unittest.TestCase):
    def test_three_profiles_pin_the_same_http_runtime_and_database(self) -> None:
        values = [load_profile(profile_id) for profile_id in PROFILES]
        self.assertEqual({value["framework"]["name"] for value in values}, {"axum"})
        self.assertEqual({value["framework"]["version"] for value in values}, {"0.8.9"})
        self.assertEqual({value["runtime"]["name"] for value in values}, {"tokio"})
        self.assertEqual({value["runtime"]["version"] for value in values}, {"1.54.1"})
        self.assertEqual({value["database"]["performance_profile"] for value in values}, {"postgresql-16"})

    def test_profiles_are_three_distinct_database_layers_and_have_no_diesel(self) -> None:
        values = [load_profile(profile_id) for profile_id in PROFILES]
        self.assertEqual({value["driver"]["name"] for value in values}, {"sqlx", "tokio-postgres", "toasty"})
        self.assertNotIn("diesel", " ".join(PROFILES).lower())
        for value in values:
            self.assertNotIn("diesel", str(value).lower())

    def test_every_profile_has_cargo_validation_and_migration_commands(self) -> None:
        for profile_id in PROFILES:
            value = load_profile(profile_id)
            self.assertEqual({"format", "check", "lint", "test", "audit"}, set(value["validation"]["commands"]))
            self.assertTrue(value["migration"]["commands"])
            self.assertTrue(value["migration"]["version"])

    def test_toasty_exposes_its_migration_boundary(self) -> None:
        value = load_profile("rust-axum-toasty")
        self.assertEqual(value["driver"]["maturity"], "experimental")
        self.assertEqual(value["driver"]["package_version"], "0.8.0")
        self.assertEqual(value["migration"]["native_tool"]["migrations"], "unavailable")
        self.assertEqual(value["migration"]["status"], "external_required")

    def test_missing_migration_tool_is_rejected(self) -> None:
        value = copy.deepcopy(load_profile("rust-axum-sqlx"))
        value["migration"].pop("tool")
        with self.assertRaisesRegex(ProfileError, "migration.tool"):
            validate_profile(value)

    def test_diesel_cannot_be_added_as_a_hidden_dependency(self) -> None:
        value = copy.deepcopy(load_profile("rust-axum-sqlx"))
        value["driver"]["features"].append("diesel-compat")
        with self.assertRaisesRegex(ProfileError, "Diesel"):
            validate_profile(value)


if __name__ == "__main__":
    unittest.main()
