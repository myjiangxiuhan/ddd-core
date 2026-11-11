#!/usr/bin/env python3
"""Check whether a workflow ledger permits one gated skill to proceed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "domain-design": ("gates", "decisions"),
    "slice-approval": ("gates", "active_slice"),
    "technology": ("gates", "active_slice"),
    "delivery": ("gates", "active_slice"),
    "repair": ("gates", "active_slice"),
}


def fail(message: str) -> int:
    print(json.dumps({"allowed": False, "reason": message}, ensure_ascii=False))
    return 1


def read_state(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"workflow ledger not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"workflow ledger is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("workflow ledger root must be an object")
    if value.get("schema_version") != "1":
        raise ValueError("workflow ledger schema_version must be \"1\"")
    return value


def require_object(state: dict[str, Any], key: str) -> dict[str, Any]:
    value = state.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing object: {key}")
    return value


def check(state: dict[str, Any], target: str) -> str | None:
    for key in REQUIRED_KEYS[target]:
        if key not in state:
            return f"missing field: {key}"

    gates = require_object(state, "gates")
    active_slice = state.get("active_slice")

    if target == "domain-design":
        if not isinstance(state.get("decisions"), list):
            return "decisions must be an array"
        return None

    if not isinstance(active_slice, dict) or not active_slice.get("id"):
        return "active_slice must contain an id"
    if gates.get("domain_design") != "confirmed":
        return "domain_design must be confirmed"
    if gates.get("slice_approval") != "approved":
        return "slice_approval must be approved"

    if target == "slice-approval":
        return None
    if target == "technology":
        return None
    if target == "delivery" and gates.get("technology_profile") != "selected":
        return "technology_profile must be selected"
    if target == "repair" and gates.get("delivery") not in {"in_progress", "blocked"}:
        return "delivery must be in_progress or blocked"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument(
        "--require",
        choices=sorted(REQUIRED_KEYS),
        required=True,
        help="the next gated operation to check",
    )
    args = parser.parse_args()

    try:
        state = read_state(args.state)
        reason = check(state, args.require)
    except ValueError as exc:
        return fail(str(exc))

    if reason:
        return fail(reason)
    print(json.dumps({"allowed": True, "require": args.require}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
