#!/usr/bin/env python3
"""Load and validate a version-pinned performance database profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parents[1] / "profiles"
SUPPORTED_ENGINES = {"postgresql", "mysql", "sqlite", "sqlserver", "none", "in-memory"}
PARAMETER_STYLES = {"numbered_dollar", "question", "named_at"}
PAGINATION_STYLES = {"tuple", "lexicographic"}


class ProfileError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ProfileError("PyYAML is required to load database profiles") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ProfileError(f"database profile not found: {path}") from exc
    except OSError as exc:
        raise ProfileError(f"cannot read database profile: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ProfileError(f"database profile is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileError("database profile root must be an object")
    return value


def non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{label} must be a non-empty string")
    return value.strip()


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ProfileError(f"{label} must be boolean")
    return value


def positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProfileError(f"{label} must be a positive integer")
    return value


def validate_profile(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != "1":
        raise ProfileError('schema_version must be "1"')
    non_empty_string(value.get("id"), "id")
    engine = non_empty_string(value.get("engine"), "engine")
    if engine not in SUPPORTED_ENGINES:
        raise ProfileError(f"engine is not supported: {engine}")
    non_empty_string(value.get("version"), "version")
    non_empty_string(value.get("profile_version"), "profile_version")
    parameter_style = non_empty_string(value.get("parameter_style"), "parameter_style")
    if parameter_style not in PARAMETER_STYLES:
        raise ProfileError(f"parameter_style is not supported: {parameter_style}")
    pagination_style = non_empty_string(value.get("pagination_style"), "pagination_style")
    if pagination_style not in PAGINATION_STYLES:
        raise ProfileError(f"pagination_style is not supported: {pagination_style}")
    if engine == "sqlserver":
        non_empty_string(value.get("identifier_quote_left"), "identifier_quote_left")
        non_empty_string(value.get("identifier_quote_right"), "identifier_quote_right")
    else:
        non_empty_string(value.get("identifier_quote"), "identifier_quote")

    capabilities = value.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        raise ProfileError("capabilities must be a non-empty object")
    for capability_name, capability in capabilities.items():
        if not isinstance(capability_name, str) or not capability_name.strip():
            raise ProfileError("capability names must be non-empty strings")
        if not isinstance(capability, dict):
            raise ProfileError(f"capabilities.{capability_name} must be an object")
        boolean(capability.get("supported"), f"capabilities.{capability_name}.supported")
        non_empty_string(capability.get("syntax_or_api"), f"capabilities.{capability_name}.syntax_or_api")
        non_empty_string(
            capability.get("fallback_or_incompatibility"),
            f"capabilities.{capability_name}.fallback_or_incompatibility",
        )
    for required in ("upsert", "returning", "plan", "keyset_pagination"):
        if required not in capabilities:
            raise ProfileError(f"capabilities must declare {required}")

    rules = value.get("rules")
    if not isinstance(rules, dict):
        raise ProfileError("rules must be an object")
    boolean(rules.get("require_parameterized"), "rules.require_parameterized")
    boolean(rules.get("forbid_select_star"), "rules.forbid_select_star")
    non_empty_string(rules.get("preferred_pagination"), "rules.preferred_pagination")
    large_dataset_offset = non_empty_string(rules.get("large_dataset_offset"), "rules.large_dataset_offset")
    if large_dataset_offset not in {"reject", "require_rationale", "allow"}:
        raise ProfileError("rules.large_dataset_offset must be reject, require_rationale, or allow")
    positive_integer(rules.get("max_batch_size"), "rules.max_batch_size")

    generation = value.get("sql_generation")
    if not isinstance(generation, dict):
        raise ProfileError("sql_generation must be an object")
    for operation in ("list", "upsert"):
        spec = generation.get(operation)
        if not isinstance(spec, dict):
            raise ProfileError(f"sql_generation.{operation} must be an object")
        non_empty_string(spec.get("pagination" if operation == "list" else "strategy"), f"sql_generation.{operation}")
        if operation == "list":
            predicate_style = non_empty_string(spec.get("predicate_style"), "sql_generation.list.predicate_style")
            if predicate_style not in PAGINATION_STYLES:
                raise ProfileError("sql_generation.list.predicate_style is not supported")
            non_empty_string(spec.get("limit_style"), "sql_generation.list.limit_style")
            non_empty_string(spec.get("plan_command"), "sql_generation.list.plan_command")
        else:
            non_empty_string(spec.get("conflict_reference"), "sql_generation.upsert.conflict_reference")
            returning = non_empty_string(spec.get("returning"), "sql_generation.upsert.returning")
            if returning not in {"supported", "unsupported"}:
                raise ProfileError("sql_generation.upsert.returning must be supported or unsupported")
            if "concurrency_required" in spec:
                boolean(spec.get("concurrency_required"), "sql_generation.upsert.concurrency_required")
            if "concurrency_options" in spec:
                options = spec.get("concurrency_options")
                if not isinstance(options, list) or not options or any(
                    not isinstance(option, str) or not option.strip() for option in options
                ):
                    raise ProfileError("sql_generation.upsert.concurrency_options must be a non-empty string array")
    if rules["preferred_pagination"] != generation["list"]["pagination"]:
        raise ProfileError("rules.preferred_pagination must match sql_generation.list.pagination")
    if generation["list"]["predicate_style"] != pagination_style:
        raise ProfileError("sql_generation.list.predicate_style must match pagination_style")
    if generation["list"]["pagination"] == "keyset" and capabilities["keyset_pagination"].get("supported") is not True:
        raise ProfileError("keyset pagination generation requires a supported keyset_pagination capability")
    returning_mode = generation["upsert"]["returning"] == "supported"
    if returning_mode != capabilities["returning"].get("supported"):
        raise ProfileError("sql_generation.upsert.returning must match capabilities.returning.supported")
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
        raise ProfileError(f"database profile id does not match requested profile: {requested}")
    return value


def load_profile_from_contract(database: dict[str, Any], profiles_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    adapter_profile = non_empty_string(database.get("adapter_profile"), "profile.database.adapter_profile")
    value = load_profile(adapter_profile, profiles_dir)
    if value["engine"] != database.get("engine"):
        raise ProfileError("database profile engine does not match the contract")
    if value["version"] != str(database.get("version")):
        raise ProfileError("database profile version does not match the contract")
    return value
