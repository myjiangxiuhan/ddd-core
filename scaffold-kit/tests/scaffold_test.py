"""Regression tests for UI and backend scaffold boundaries."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

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
    validate_project_gate,
    validate_generator_surface,
)


CONFIG = ROOT / "examples" / "scaffold.yaml"
FORMAL_PROJECT = ROOT.parent / "template-kit" / "examples" / "formal-flow-project"


class ScaffoldBoundaryTest(unittest.TestCase):
    def test_backend_profiles_are_registered_without_changing_ui_default(self) -> None:
        config = load_yaml(CONFIG)
        self.assertEqual(config["default_profile"], "react-antd-pro")
        for profile_id in ("rust-axum-sqlx", "rust-axum-tokio-postgres", "rust-axum-toasty"):
            selected, profile = choose_profile(config, profile_id)
            self.assertEqual(selected, profile_id)
            self.assertEqual(profile["surface"], "backend")
            self.assertIn("backend", profile["generators"])

    def test_go_scaffold_profile_declares_composable_components(self) -> None:
        config = load_yaml(CONFIG)
        selected, profile = choose_profile(config, "go-echo-pgx-sqlc")
        self.assertEqual(selected, "go-echo-pgx-sqlc")
        self.assertEqual(
            [(item["kind"], item["id"]) for item in profile["components"]],
            [("language", "go"), ("framework", "echo"), ("data_access", "pgx"), ("data_access", "sqlc")],
        )
        self.assertEqual(profile["generators"]["backend"]["service"]["validation_commands"]["check"], "go test ./...")

    def test_component_matching_accepts_go_pgx_and_sqlc_and_rejects_wrong_query_layer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scaffold-go-components-", dir=ROOT.parent) as directory:
            root = Path(directory)
            ddd = root / ".ddd"
            ddd.mkdir()
            (ddd / "mainline.md").write_text("A reviewed Go mainline.\n", encoding="utf-8")
            state = {
                "schema_version": "1",
                "control_mode": "human_led",
                "business_artifact": ".ddd/mainline.md",
                "decisions": [{"id": "d1", "status": "answered", "source": "user_decision", "evidence": "user"}],
                "active_slice": {"id": "slice-1", "name": "first slice"},
                "technology_profile": {
                    "id": "project-components",
                    "version": "1",
                    "components": [
                        {"kind": "language", "id": "go", "version": "1.25"},
                        {"kind": "framework", "id": "echo", "version": "4.13"},
                        {"kind": "data_access", "id": "pgx", "version": "5.7"},
                        {"kind": "data_access", "id": "sqlc", "version": "1.29"},
                    ],
                },
                "gates": {
                    "phase": "delivery",
                    "business_discovery": "confirmed",
                    "domain_design": "confirmed",
                    "slice_approval": "approved",
                    "technology_profile": "selected",
                    "delivery": "not_started",
                },
            }
            state_path = ddd / "workflow-state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            config = load_yaml(CONFIG)
            _, profile = choose_profile(config, "go-echo-pgx-sqlc")
            validate_project_gate(
                root,
                "go-echo-pgx-sqlc",
                "1",
                True,
                requires_ui=False,
                profile=profile,
            )
            state["technology_profile"]["components"][3]["id"] = "sqlx"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "technology components"):
                validate_project_gate(
                    root,
                    "go-echo-pgx-sqlc",
                    "1",
                    True,
                    requires_ui=False,
                    profile=profile,
                )

    def test_cli_dry_run_uses_component_matched_go_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scaffold-go-cli-", dir=ROOT.parent) as directory:
            root = Path(directory)
            ddd = root / ".ddd"
            ddd.mkdir()
            (ddd / "mainline.md").write_text("A reviewed Go mainline.\n", encoding="utf-8")
            shutil.copyfile(CONFIG, ddd / "scaffold.yaml")
            state = {
                "schema_version": "1",
                "control_mode": "human_led",
                "business_artifact": ".ddd/mainline.md",
                "decisions": [{"id": "d1", "status": "answered", "source": "user_decision", "evidence": "user"}],
                "active_slice": {"id": "slice-1", "name": "first slice"},
                "technology_profile": {
                    "id": "project-components",
                    "version": "1",
                    "components": [
                        {"kind": "language", "id": "go", "version": "1.25"},
                        {"kind": "framework", "id": "echo", "version": "4.13"},
                        {"kind": "data_access", "id": "pgx", "version": "5.7"},
                        {"kind": "data_access", "id": "sqlc", "version": "1.29"},
                    ],
                },
                "gates": {
                    "phase": "delivery",
                    "business_discovery": "confirmed",
                    "domain_design": "confirmed",
                    "slice_approval": "approved",
                    "technology_profile": "selected",
                    "delivery": "not_started",
                },
            }
            (ddd / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
            result = subprocess.run(
                (
                    "python",
                    str(ROOT / "scripts" / "scaffold.py"),
                    "generate",
                    "backend",
                    "service",
                    "--profile",
                    "go-echo-pgx-sqlc",
                    "--name",
                    "FileEntry",
                    "--slice-id",
                    "slice-1",
                    "--target",
                    "src/features/files",
                    "--config",
                    str(ddd / "scaffold.yaml"),
                ),
                cwd=ROOT.parent,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual(plan["mode"], "dry-run")
            self.assertEqual(plan["profile"], "go-echo-pgx-sqlc")
            self.assertEqual(plan["components"][2]["id"], "pgx")
            self.assertIn("go test ./...", plan["contract"]["validation_commands"]["check"])
            self.assertEqual(plan["actions"][0]["path"], "src/features/files/file-entry/handler.go")
            self.assertIn("package fileEntry", plan["actions"][0]["content"])

    def test_component_matching_accepts_react_antd_pro_for_ui_scaffold(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scaffold-react-components-", dir=ROOT.parent) as directory:
            root = Path(directory) / "project"
            shutil.copytree(FORMAL_PROJECT, root)
            state_path = root / ".ddd" / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["technology_profile"] = {
                "id": "project-components",
                "version": "1",
                "components": [
                    {"kind": "language", "id": "typescript", "version": "5.9"},
                    {"kind": "framework", "id": "react", "version": "19.1"},
                    {"kind": "ui_library", "id": "antd-pro", "version": "2.8"},
                ],
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")
            config = load_yaml(CONFIG)
            _, profile = choose_profile(config, "react-antd-pro")
            validate_project_gate(
                root,
                "react-antd-pro",
                "1",
                True,
                requires_ui=True,
                profile=profile,
            )
            state["technology_profile"]["components"][2]["id"] = "antd"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "technology components"):
                validate_project_gate(
                    root,
                    "react-antd-pro",
                    "1",
                    True,
                    requires_ui=True,
                    profile=profile,
                )

    def test_component_matching_rejects_exact_version_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scaffold-rust-version-", dir=ROOT.parent) as directory:
            root = Path(directory)
            ddd = root / ".ddd"
            ddd.mkdir()
            (ddd / "mainline.md").write_text("A reviewed Rust mainline.\n", encoding="utf-8")
            state = {
                "schema_version": "1",
                "control_mode": "human_led",
                "business_artifact": ".ddd/mainline.md",
                "decisions": [{"id": "d1", "status": "answered", "source": "user_decision", "evidence": "user"}],
                "active_slice": {"id": "slice-1", "name": "first slice"},
                "technology_profile": {
                    "id": "project-components",
                    "version": "1",
                    "components": [
                        {"kind": "language", "id": "rust", "version": "1.94"},
                        {"kind": "framework", "id": "axum", "version": "0.8.9"},
                        {"kind": "runtime", "id": "tokio", "version": "1.54.1"},
                        {"kind": "data_access", "id": "sqlx", "version": "0.9.0"},
                        {"kind": "migration", "id": "sqlx-cli", "version": "0.9.0"},
                    ],
                },
                "gates": {
                    "phase": "delivery",
                    "business_discovery": "confirmed",
                    "domain_design": "confirmed",
                    "slice_approval": "approved",
                    "technology_profile": "selected",
                    "delivery": "not_started",
                },
            }
            state_path = ddd / "workflow-state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            config = load_yaml(CONFIG)
            _, profile = choose_profile(config, "rust-axum-sqlx")
            with self.assertRaisesRegex(ConfigError, "technology components"):
                validate_project_gate(
                    root,
                    "rust-axum-sqlx",
                    "1",
                    True,
                    requires_ui=False,
                    profile=profile,
                )

    def test_backend_gate_does_not_require_ui_records(self) -> None:
        fields = required_gate_fields()
        self.assertNotIn("ui_system", fields)
        self.assertNotIn("ui_practices", fields)
        self.assertNotIn("ui_design", fields)
        self.assertIn("technology_profile", fields)
        self.assertIn("delivery", fields)

    def test_ui_records_are_validated_from_files_not_mirror_gate_fields(self) -> None:
        fields = required_gate_fields()
        self.assertNotIn("ui_system", fields)
        self.assertNotIn("ui_practices", fields)
        self.assertNotIn("ui_design", fields)

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

    def test_database_backend_generator_requires_a_profile_record(self) -> None:
        with self.assertRaisesRegex(ConfigError, "database_profile record"):
            require_backend_database_gate({}, {})
        with self.assertRaisesRegex(ConfigError, "selected id and digest"):
            require_backend_database_gate({}, {"database_profile": {"id": "postgresql-16"}})

    def test_ui_generator_still_declares_ui_context_requirement(self) -> None:
        config = load_yaml(CONFIG)
        _, profile = choose_profile(config, "react-antd-pro")
        args = argparse.Namespace(command="generate", kind="component", generator="file-entry-table")
        self.assertEqual(gate_requirements(args, profile), (True, False))

    def test_list_and_describe_are_read_only_profile_inspection(self) -> None:
        list_result = subprocess.run(
            ("python", str(ROOT / "scripts" / "scaffold.py"), "list", "--config", str(CONFIG)),
            cwd=ROOT.parent,
            text=True,
            capture_output=True,
        )
        self.assertEqual(list_result.returncode, 0, list_result.stdout + list_result.stderr)
        describe_result = subprocess.run(
            (
                "python",
                str(ROOT / "scripts" / "scaffold.py"),
                "describe",
                "component:file-entry-table",
                "--config",
                str(CONFIG),
            ),
            cwd=ROOT.parent,
            text=True,
            capture_output=True,
        )
        self.assertEqual(describe_result.returncode, 0, describe_result.stdout + describe_result.stderr)
        self.assertIn('"generator": "component:file-entry-table"', describe_result.stdout)

    def test_ui_scaffold_uses_confirmed_records_without_mirror_gate_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scaffold-ui-records-", dir=ROOT.parent) as directory:
            root = Path(directory) / "project"
            shutil.copytree(FORMAL_PROJECT, root)
            state_path = root / ".ddd" / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            for field in ("ui_system", "ui_practices", "ui_design"):
                state["gates"].pop(field, None)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            ui_system_path = root / ".ddd" / "ui-system.yaml"
            ui_system = yaml.safe_load(ui_system_path.read_text(encoding="utf-8"))
            ui_system["profile"] = None
            ui_system["profile_version"] = None
            ui_system_path.write_text(yaml.safe_dump(ui_system, sort_keys=False), encoding="utf-8")
            validate_project_gate(root, "react-antd-pro", "1", True, requires_ui=True)

    def test_plain_managed_scaffold_uses_project_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scaffold-plain-", dir=ROOT.parent) as directory:
            root = Path(directory)
            ddd = root / ".ddd"
            ddd.mkdir()
            (ddd / "mainline.md").write_text("A reviewed mainline.\n", encoding="utf-8")
            state = {
                "schema_version": "1",
                "control_mode": "human_led",
                "business_artifact": ".ddd/mainline.md",
                "decisions": [{"id": "d1", "status": "answered", "source": "user_decision", "evidence": "user"}],
                "active_slice": {"id": "slice-1", "name": "first slice"},
                "technology_profile": {"id": "rust-axum-sqlx", "version": "1"},
                "gates": {
                    "phase": "delivery",
                    "business_discovery": "confirmed",
                    "domain_design": "confirmed",
                    "slice_approval": "approved",
                    "technology_profile": "selected",
                    "delivery": "not_started",
                    "ui_design": "draft",
                },
            }
            state_path = ddd / "workflow-state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            validate_project_gate(root, "rust-axum-sqlx", "1", True, requires_ui=False)

    def test_backend_generator_cannot_run_from_a_ui_profile(self) -> None:
        config = load_yaml(CONFIG)
        _, profile = choose_profile(config, "react-antd-pro")
        profile["generators"]["backend"] = {"service": {"surface": "backend", "files": [{"path": "x", "template": ""}]}}
        args = argparse.Namespace(command="generate", kind="backend", generator="service")
        with self.assertRaisesRegex(ConfigError, "does not match profile surface"):
            gate_requirements(args, profile)


if __name__ == "__main__":
    unittest.main()
