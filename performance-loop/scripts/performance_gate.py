#!/usr/bin/env python3
"""Validate the selected database profile and performance evidence."""

from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Any


DDD_SCRIPTS = Path(__file__).resolve().parents[2] / "ddd-core" / "scripts"
if str(DDD_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DDD_SCRIPTS))

from workflow_gate import (  # type: ignore  # noqa: E402
    baseline_record_from_file,
    project_path,
    project_root_from_state,
    read_state,
)
from record_utils import digest_bytes  # type: ignore  # noqa: E402


class PerformanceGateError(ValueError):
    pass


def selected_profile_path(state_path: Path, database_record: dict[str, Any]) -> Path:
    raw_path = database_record.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise PerformanceGateError("database_profile.path is missing")
    return project_path(project_root_from_state(state_path), raw_path, "database profile")


def load_selected_profile(state_path: Path, database_record: dict[str, Any]) -> dict[str, Any]:
    """Read and validate the selected profile bytes once for an operation."""
    path = selected_profile_path(state_path, database_record)
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise PerformanceGateError(f"database profile not found: {path}") from exc
    except OSError as exc:
        raise PerformanceGateError(f"cannot read database profile: {exc}") from exc
    if digest_bytes(raw) != database_record.get("digest"):
        raise PerformanceGateError("database profile digest does not match the workflow record")
    try:
        import yaml  # type: ignore
        from profile_loader import validate_profile  # type: ignore

        value = yaml.safe_load(raw.decode("utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("database profile root must be an object")
        profile = validate_profile(value)
    except Exception as exc:
        raise PerformanceGateError(f"database profile is invalid: {exc}") from exc
    if profile.get("id") != database_record.get("id") or str(profile.get("version")) != str(database_record.get("version")):
        raise PerformanceGateError("database profile no longer matches the workflow record")
    return profile


def load_selected_contract(
    state_path: Path,
    state: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Read and validate the confirmed contract bytes once for an operation."""
    record = state.get("performance_contract")
    if not isinstance(record, dict):
        raise PerformanceGateError("performance_contract record is missing")
    raw_path = record.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise PerformanceGateError("performance_contract.path is missing")
    path = project_path(project_root_from_state(state_path), raw_path, "performance contract")
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise PerformanceGateError(f"performance contract not found: {path}") from exc
    except OSError as exc:
        raise PerformanceGateError(f"cannot read performance contract: {exc}") from exc
    if digest_bytes(raw) != record.get("digest"):
        raise PerformanceGateError("performance contract digest does not match the workflow record")
    try:
        import yaml  # type: ignore
        from validate_contract import validate  # type: ignore

        document = yaml.safe_load(raw.decode("utf-8-sig"))
        if not isinstance(document, dict):
            raise ValueError("performance contract root must be an object")
        summary = validate(
            path,
            profiles_dir=selected_profile_path(state_path, state["database_profile"]).parent,
            profile_override=profile,
            document=document,
        )
    except Exception as exc:
        raise PerformanceGateError(f"performance contract is invalid: {exc}") from exc
    if summary.get("status") != "confirmed":
        raise PerformanceGateError("performance contract must be confirmed before baseline verification")
    active = state.get("active_slice")
    if not isinstance(active, dict) or summary.get("slice_id") != active.get("id"):
        raise PerformanceGateError("performance contract slice_id does not match active_slice")
    return document


def load_baseline(
    state_path: Path,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Read the baseline bound to the active performance contract."""
    root = project_root_from_state(state_path)
    performance = state.get("performance_contract")
    if not isinstance(performance, dict) or not isinstance(performance.get("baseline_result"), str):
        raise PerformanceGateError("performance contract must name a baseline result")
    try:
        record = baseline_record_from_file(root, performance["baseline_result"], state)
    except ValueError as exc:
        raise PerformanceGateError(str(exc)) from exc
    path = project_path(root, record["path"], "baseline result")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8-sig"))
    except PerformanceGateError:
        raise
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PerformanceGateError(f"baseline result is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PerformanceGateError("baseline root must be an object")
    return value


def require_database_profile_context(
    state_path: Path,
    *,
    require_performance: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    state = read_state(state_path)
    gates = state.get("gates")
    active = state.get("active_slice")
    if not isinstance(gates, dict) or not isinstance(active, dict) or not active.get("id"):
        raise PerformanceGateError("workflow ledger must contain gates and active_slice before project SQL")
    if gates.get("domain_design") != "confirmed":
        raise PerformanceGateError("domain_design must be confirmed before project SQL")
    if gates.get("slice_approval") != "approved":
        raise PerformanceGateError("slice_approval must be approved before project SQL")
    if gates.get("technology_profile") != "selected" or not isinstance(state.get("technology_profile"), dict):
        raise PerformanceGateError("technology_profile must be selected before project SQL")
    database_record = state.get("database_profile")
    if not isinstance(database_record, dict):
        raise PerformanceGateError("database_profile record is missing; select one before project SQL")
    profile = load_selected_profile(state_path, database_record)
    contract: dict[str, Any] | None = None
    if require_performance:
        if not isinstance(state.get("performance_contract"), dict):
            raise PerformanceGateError("performance_contract record is missing before baseline verification")
        contract = load_selected_contract(state_path, state, profile)
    return state, database_record, profile, contract
