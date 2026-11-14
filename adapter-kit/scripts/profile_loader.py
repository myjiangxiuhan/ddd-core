#!/usr/bin/env python3
"""Load and validate a version-pinned application technology profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parents[1] / "profiles"
BACKEND_DRIVERS = {"sqlx", "tokio-postgres", "toasty"}
REQUIRED_VALIDATION_COMMANDS = {"format", "check", "lint", "test", "audit"}


class ProfileError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ProfileError("PyYAML is required to load adapter profiles") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ProfileError(f"adapter profile not found: {path}") from exc
    except OSError as exc:
        raise ProfileError(f"cannot read adapter profile: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ProfileError(f"adapter profile is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileError("adapter profile root must be an object")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{label} must be a non-empty string")
    return value.strip()


def mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ProfileError(f"{label} must be a non-empty object")
    return value


def string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ProfileError(f"{label} must be a non-empty string array")
    return value


def validate_profile(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != "1":
        raise ProfileError('schema_version must be "1"')
    profile_id = text(value.get("id"), "id")
    text(value.get("version"), "version")
    if value.get("type") != "technology":
        raise ProfileError("type must be technology")
    if value.get("surface") != "backend":
        raise ProfileError("backend adapter profiles must declare surface: backend")
    if value.get("language") != "rust":
        raise ProfileError("backend Rust profiles must declare language: rust")

    rust = mapping(value.get("rust"), "rust")
    text(rust.get("edition"), "rust.edition")
    text(rust.get("msrv"), "rust.msrv")

    framework = mapping(value.get("framework"), "framework")
    if text(framework.get("name"), "framework.name") != "axum":
        raise ProfileError("framework.name must be axum")
    text(framework.get("version"), "framework.version")
    runtime = mapping(value.get("runtime"), "runtime")
    if text(runtime.get("name"), "runtime.name") != "tokio":
        raise ProfileError("runtime.name must be tokio")
    text(runtime.get("version"), "runtime.version")
    http = mapping(value.get("http"), "http")
    for field in ("hyper", "tower", "tower-http"):
        text(http.get(field), f"http.{field}")
    serialization = mapping(value.get("serialization"), "serialization")
    text(serialization.get("serde"), "serialization.serde")

    database = mapping(value.get("database"), "database")
    if text(database.get("engine"), "database.engine") != "postgresql":
        raise ProfileError("the Rust comparison profiles must use the same postgresql engine")
    text(database.get("version"), "database.version")
    text(database.get("performance_profile"), "database.performance_profile")

    driver = mapping(value.get("driver"), "driver")
    driver_name = text(driver.get("name"), "driver.name")
    if driver_name not in BACKEND_DRIVERS:
        raise ProfileError(f"driver.name is not supported: {driver_name}")
    text(driver.get("version"), "driver.version")
    text(driver.get("package"), "driver.package")
    if driver_name == "toasty":
        text(driver.get("package_version"), "driver.package_version")
    text(driver.get("query_model"), "driver.query_model")
    string_list(driver.get("features"), "driver.features")
    if driver_name == "toasty" and text(driver.get("maturity"), "driver.maturity") != "experimental":
        raise ProfileError("Toasty must remain explicitly marked experimental")

    migration = mapping(value.get("migration"), "migration")
    migration_tool = text(migration.get("tool"), "migration.tool")
    if migration_tool not in {"sqlx-cli", "refinery"}:
        raise ProfileError(f"migration.tool is not supported: {migration_tool}")
    text(migration.get("version"), "migration.version")
    text(migration.get("mode"), "migration.mode")
    text(migration.get("status"), "migration.status")
    commands = mapping(migration.get("commands"), "migration.commands")
    for command, value_text in commands.items():
        text(value_text, f"migration.commands.{command}")
    if driver_name == "toasty":
        native_tool = mapping(migration.get("native_tool"), "migration.native_tool")
        text(native_tool.get("name"), "migration.native_tool.name")
        text(native_tool.get("version"), "migration.native_tool.version")
        if text(native_tool.get("migrations"), "migration.native_tool.migrations") != "unavailable":
            raise ProfileError("Toasty must declare native migrations unavailable until its migration work lands")

    validation = mapping(value.get("validation"), "validation")
    validation_commands = mapping(validation.get("commands"), "validation.commands")
    missing = sorted(REQUIRED_VALIDATION_COMMANDS - set(validation_commands))
    if missing:
        raise ProfileError(f"validation.commands is missing: {', '.join(missing)}")
    for command in REQUIRED_VALIDATION_COMMANDS:
        command_text = text(validation_commands.get(command), f"validation.commands.{command}")
        if not command_text.startswith("cargo "):
            raise ProfileError(f"validation.commands.{command} must be a Cargo command")

    scaffold = mapping(value.get("scaffold"), "scaffold")
    if text(scaffold.get("profile"), "scaffold.profile") != profile_id:
        raise ProfileError("scaffold.profile must match id")
    kinds = string_list(scaffold.get("generator_kinds"), "scaffold.generator_kinds")
    if "backend" not in kinds:
        raise ProfileError("scaffold.generator_kinds must include backend")
    if scaffold.get("requires_ui") is not False:
        raise ProfileError("backend scaffold profiles must set scaffold.requires_ui: false")

    evidence = mapping(value.get("evidence"), "evidence")
    for field in ("framework", "runtime", "driver", "migration"):
        source = text(evidence.get(field), f"evidence.{field}")
        if not source.startswith("https://"):
            raise ProfileError(f"evidence.{field} must be an HTTPS URL")
    if driver_name == "toasty":
        source = text(evidence.get("driver_package"), "evidence.driver_package")
        if not source.startswith("https://"):
            raise ProfileError("evidence.driver_package must be an HTTPS URL")

    serialized = json.dumps(value, ensure_ascii=False).lower()
    if "diesel" in serialized:
        raise ProfileError("Diesel is intentionally not part of the Rust adapter profiles")
    return value


def resolve_profile_path(profile: str | Path, profiles_dir: Path = PROFILE_DIR) -> Path:
    requested = Path(profile)
    if requested.is_absolute() or requested.suffix in {".yaml", ".yml"} or len(requested.parts) > 1:
        return requested
    return profiles_dir / f"{requested}.yaml"


def load_profile(profile: str | Path, profiles_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    path = resolve_profile_path(profile, profiles_dir)
    value = validate_profile(load_yaml(path))
    requested = str(profile)
    if not Path(requested).suffix and Path(requested).name != value["id"]:
        raise ProfileError(f"adapter profile id does not match requested profile: {requested}")
    return value
