#!/usr/bin/env python3
"""Regression tests for independent technology components."""

from __future__ import annotations

import sys
import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from component_loader import COMPONENT_DIR, load_component  # type: ignore  # noqa: E402


COMPONENTS = (
    "rust",
    "axum",
    "tokio",
    "sqlx",
    "tokio-postgres",
    "toasty",
    "sqlx-cli",
    "refinery",
    "go",
    "echo",
    "pgx",
    "sqlc",
    "typescript",
    "react",
    "vue",
    "angular",
    "antd",
    "antd-pro",
    "ant-design-vue",
    "element-plus",
    "ng-zorro",
)


class TechnologyComponentTest(unittest.TestCase):
    def test_all_components_are_independently_valid(self) -> None:
        for component_id in COMPONENTS:
            value = load_component(component_id)
            self.assertEqual(value["id"], component_id)
            self.assertTrue((COMPONENT_DIR / f"{component_id}.yaml").is_file())

    def test_sqlx_component_does_not_pin_a_database_version(self) -> None:
        value = load_component("sqlx")
        self.assertEqual(value["supported_database_engines"], ["postgresql", "mysql", "sqlite"])
        self.assertNotIn("version", value.get("database", {}))

    def test_toasty_remains_explicitly_experimental(self) -> None:
        self.assertEqual(load_component("toasty")["maturity"], "experimental")


if __name__ == "__main__":
    unittest.main()
