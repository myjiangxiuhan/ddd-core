#!/usr/bin/env python3
"""Enforce workflow approvals before project SQL generation or baseline comparison."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


DDD_SCRIPTS = Path(__file__).resolve().parents[2] / "ddd-core" / "scripts"
if str(DDD_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DDD_SCRIPTS))

from workflow_gate import (  # type: ignore  # noqa: E402
    database_profile_from_file,
    performance_contract_from_file,
    project_root_from_state,
    read_state,
    validate_history_approvals,
)


class PerformanceGateError(ValueError):
    pass


def require_database_profile_gate(
    state_path: Path,
    trusted_public_key: str,
    *,
    require_performance: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not trusted_public_key.strip():
        raise PerformanceGateError("project SQL and performance tools require --trusted-public-key")
    state = read_state(state_path)
    try:
        validate_history_approvals(state, state_path, trusted_public_key)
    except ValueError as exc:
        raise PerformanceGateError(str(exc)) from exc
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
    if gates.get("database_profile") != "selected":
        raise PerformanceGateError("database_profile must be selected by a signed user transition before project SQL")
    database_record = state.get("database_profile")
    if not isinstance(database_record, dict):
        raise PerformanceGateError("database_profile record is missing")
    root = project_root_from_state(state_path)
    try:
        database_profile_from_file(
            root,
            str(database_record.get("path")),
            str(database_record.get("id")),
            str(database_record.get("version")),
        )
    except ValueError as exc:
        raise PerformanceGateError(str(exc)) from exc
    if require_performance:
        if gates.get("performance_contract") != "confirmed":
            raise PerformanceGateError("performance_contract must be confirmed by a signed user transition before baseline verification")
        try:
            performance_contract_from_file(root, str(state.get("performance_contract", {}).get("path")), state)
        except ValueError as exc:
            raise PerformanceGateError(str(exc)) from exc
    return state, database_record
