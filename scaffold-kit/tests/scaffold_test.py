"""Regression tests for UI and backend scaffold boundaries."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scaffold import (  # type: ignore  # noqa: E402
    ConfigError,
    choose_profile,
    gate_requirements,
    load_yaml,
    required_gate_fields,
    resolve_generator,
    require_backend_database_gate,
    validate_generator_surface,
)


CONFIG = ROOT / "examples" / "scaffold.yaml"


class ScaffoldBoundaryTest(unittest.TestCase):
    def test_backend_profiles_are_registered_without_changing_ui_default(self) -> None:
        config = load_yaml(CONFIG)
        self.assertEqual(config["default_profile"], "react-antd-pro")
        for profile_id in ("rust-axum-sqlx", "rust-axum-tokio-postgres", "rust-axum-toasty"):
            selected, profile = choose_profile(config, profile_id)
            self.assertEqual(selected, profile_id)
            self.assertEqual(profile["surface"], "backend")
            self.assertIn("backend", profile["generators"])

    def test_backend_gate_does_not_require_ui_records(self) -> None:
        fields = required_gate_fields(False)
        self.assertNotIn("ui_system", fields)
        self.assertNotIn("ui_practices", fields)
        self.assertNotIn("ui_design", fields)
        self.assertIn("technology_profile", fields)
        self.assertIn("delivery", fields)

    def test_generator_requirements_are_explicit(self) -> None:
        config = load_yaml(CONFIG)
        _, profile = choose_profile(config, "rust-axum-sqlx")
        service = resolve_generator(profile, "backend", "service")
        repository = resolve_generator(profile, "backend", "repository")
        service_args = argparse.Namespace(command="generate", kind="backend", generator="service")
        repository_args = argparse.Namespace(command="generate", kind="backend", generator="repository")
        self.assertEqual(gate_requirements(service_args, profile), (False, False))
        self.assertEqual(gate_requirements(repository_args, profile), (False, True))
        self.assertFalse(service["requires_ui"])
        self.assertTrue(repository["requires_database"])

    def test_backend_generator_cannot_reintroduce_ui_dependency(self) -> None:
        with self.assertRaisesRegex(ConfigError, "cannot require UI"):
            validate_generator_surface({"surface": "backend", "requires_ui": True}, "backend", "bad")

    def test_database_backend_generator_cannot_skip_database_profile(self) -> None:
        with self.assertRaisesRegex(ConfigError, "database_profile must be selected"):
            require_backend_database_gate({}, {})
        with self.assertRaisesRegex(ConfigError, "signed id and digest"):
            require_backend_database_gate({"database_profile": "selected"}, {"database_profile": {"id": "postgresql-16"}})

    def test_ui_generator_still_requires_ui_gate(self) -> None:
        config = load_yaml(CONFIG)
        _, profile = choose_profile(config, "react-antd-pro")
        args = argparse.Namespace(command="generate", kind="component", generator="file-entry-table")
        self.assertEqual(gate_requirements(args, profile), (True, False))

    def test_backend_generator_cannot_run_from_a_ui_profile(self) -> None:
        config = load_yaml(CONFIG)
        _, profile = choose_profile(config, "react-antd-pro")
        profile["generators"]["backend"] = {"service": {"surface": "backend", "files": [{"path": "x", "template": ""}]}}
        args = argparse.Namespace(command="generate", kind="backend", generator="service")
        with self.assertRaisesRegex(ConfigError, "does not match profile surface"):
            gate_requirements(args, profile)


if __name__ == "__main__":
    unittest.main()
