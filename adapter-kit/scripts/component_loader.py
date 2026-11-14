#!/usr/bin/env python3
"""Load and validate one independent technology component."""

from __future__ import annotations

from pathlib import Path
from typing import Any


COMPONENT_DIR = Path(__file__).resolve().parents[1] / "components"
KINDS = {"language", "framework", "runtime", "data_access", "migration", "ui_library"}


class ComponentError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ComponentError("PyYAML is required to load technology components") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ComponentError(f"technology component not found: {path}") from exc
    except OSError as exc:
        raise ComponentError(f"cannot read technology component: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ComponentError(f"technology component is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ComponentError("technology component root must be an object")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComponentError(f"{label} must be a non-empty string")
    return value.strip()


def validate_component(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != "1":
        raise ComponentError('schema_version must be "1"')
    text(value.get("id"), "id")
    kind = text(value.get("kind"), "kind")
    if kind not in KINDS:
        raise ComponentError(f"kind must be one of {sorted(KINDS)}")
    text(value.get("version"), "version")
    evidence = text(value.get("evidence"), "evidence")
    if not evidence.startswith("https://"):
        raise ComponentError("evidence must be an HTTPS URL")
    if "supported_database_engines" in value:
        engines = value["supported_database_engines"]
        if not isinstance(engines, list) or not engines or any(not isinstance(item, str) or not item.strip() for item in engines):
            raise ComponentError("supported_database_engines must be a non-empty string array")
    if kind == "data_access" and "supported_database_engines" not in value:
        raise ComponentError("data_access components must declare supported_database_engines")
    return value


def load_component(component: str | Path, components_dir: Path = COMPONENT_DIR) -> dict[str, Any]:
    requested = Path(component)
    path = requested if requested.suffix in {".yaml", ".yml"} or requested.is_absolute() else components_dir / f"{requested}.yaml"
    value = validate_component(load_yaml(path))
    if requested.suffix not in {".yaml", ".yml"} and requested.name != value["id"]:
        raise ComponentError(f"component id does not match requested component: {requested}")
    return value
