#!/usr/bin/env python3
"""Check and apply one explicit transition in a DDD workflow ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "business": ("gates", "decisions"),
    "domain-design": ("gates", "decisions"),
    "slice-approval": ("gates", "active_slice"),
    "technology": ("gates", "active_slice"),
    "ui-design": ("gates", "active_slice"),
    "scaffold": ("gates", "active_slice"),
    "delivery": ("gates", "active_slice"),
    "repair": ("gates", "active_slice"),
    "review": ("gates", "active_slice"),
}

TRANSITIONS = (
    "start-business-lab",
    "record-mainline",
    "confirm-mainline",
    "record-decision",
    "confirm-design",
    "approve-slice",
    "select-profile",
    "draft-ui",
    "confirm-ui",
    "start-delivery",
    "verify",
    "block",
    "start-repair",
    "pass-review",
    "block-review",
    "reset-slice",
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(message: str) -> int:
    emit({"allowed": False, "reason": message})
    return 1


def read_state(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"workflow ledger not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"workflow ledger is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("workflow ledger root must be an object")
    if value.get("schema_version") != "1":
        raise ValueError('workflow ledger schema_version must be "1"')
    return value


def require_object(state: dict[str, Any], key: str) -> dict[str, Any]:
    value = state.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing object: {key}")
    return value


def active_slice(state: dict[str, Any]) -> dict[str, Any]:
    value = state.get("active_slice")
    if not isinstance(value, dict) or not value.get("id"):
        raise ValueError("active_slice must contain an id")
    return value


def check(state: dict[str, Any], target: str) -> str | None:
    for key in REQUIRED_KEYS[target]:
        if key not in state:
            return f"missing field: {key}"

    gates = require_object(state, "gates")
    current_slice = state.get("active_slice")

    if target == "domain-design":
        if not isinstance(state.get("decisions"), list):
            return "decisions must be an array"
        if state.get("control_mode", "human_led") == "human_led" and gates.get("business_discovery", "not_started") != "confirmed":
            return "business_discovery must be confirmed in human_led mode"
        return None

    if target == "business":
        if not isinstance(state.get("decisions"), list):
            return "decisions must be an array"
        return None

    if not isinstance(current_slice, dict) or not current_slice.get("id"):
        return "active_slice must contain an id"
    if gates.get("domain_design") != "confirmed":
        return "domain_design must be confirmed"
    if gates.get("slice_approval") != "approved":
        return "slice_approval must be approved"

    if target in {"slice-approval", "technology"}:
        return None
    if target == "ui-design":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if gates.get("ui_design", "not_started") not in {"not_started", "draft"}:
            return "ui_design must be not_started or draft"
        return None
    if target == "scaffold":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if gates.get("ui_design", "not_started") != "confirmed":
            return "ui_design must be confirmed"
        if gates.get("delivery") != "not_started":
            return "delivery must be not_started before scaffold"
        return None
    if target == "delivery" and gates.get("technology_profile") != "selected":
        return "technology_profile must be selected"
    if target == "delivery" and gates.get("ui_design", "not_started") == "draft":
        return "ui_design must be confirmed or not_started"
    if target == "repair":
        if gates.get("delivery") in {"in_progress", "blocked"}:
            return None
        if gates.get("delivery") == "verified" and gates.get("review", "not_started") == "blocked":
            return None
        return "delivery must be in_progress or blocked, or verified with a blocked review"
    if target == "review":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if gates.get("delivery") != "verified":
            return "delivery must be verified before review"
        if gates.get("review", "not_started") not in {"not_started", "blocked"}:
            return "review must be not_started or blocked"
    return None


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    try:
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(path)
    except OSError as exc:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        raise ValueError(f"cannot write workflow ledger: {exc}") from exc


def add_history(state: dict[str, Any], transition: str, evidence: str) -> None:
    history = state.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("history must be an array when present")
    user_transitions = {
        "confirm-mainline",
        "record-decision",
        "confirm-design",
        "approve-slice",
        "select-profile",
        "confirm-ui",
        "reset-slice",
    }
    history.append({"transition": transition, "actor": "user" if transition in user_transitions else "agent", "evidence": evidence})


def require_evidence(args: argparse.Namespace) -> str:
    evidence = (args.evidence or "").strip()
    if not evidence:
        raise ValueError("--evidence is required for an explicit transition")
    return evidence


def apply_transition(state: dict[str, Any], args: argparse.Namespace) -> str:
    transition = args.transition
    gates = require_object(state, "gates")
    evidence = require_evidence(args)

    if transition == "record-decision":
        decisions = state.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError("decisions must be an array")
        decision = next((item for item in decisions if isinstance(item, dict) and item.get("id") == args.decision_id), None)
        if decision is None:
            raise ValueError(f"decision not found: {args.decision_id}")
        if not (args.answer or "").strip():
            raise ValueError("--answer is required for record-decision")
        decision.update({"status": "answered", "source": "user_decision", "answer": args.answer.strip(), "evidence": evidence})
        add_history(state, transition, evidence)
        return f"recorded decision {args.decision_id}"

    if transition == "start-business-lab":
        if gates.get("business_discovery", "not_started") != "not_started":
            raise ValueError("business_discovery must be not_started before start-business-lab")
        gates.update({"business_discovery": "in_progress", "phase": "business_discovery"})
    elif transition == "record-mainline":
        if gates.get("business_discovery", "not_started") != "in_progress":
            raise ValueError("business_discovery must be in_progress before record-mainline")
        if not (args.artifact or "").strip():
            raise ValueError("--artifact is required for record-mainline")
        state["business_artifact"] = args.artifact.strip()
        gates.update({"business_discovery": "draft", "phase": "business_discovery"})
    elif transition == "confirm-mainline":
        if gates.get("business_discovery", "not_started") != "draft":
            raise ValueError("business_discovery must be draft before confirm-mainline")
        if not (state.get("business_artifact") or "").strip():
            raise ValueError("business_artifact is required before confirm-mainline")
        gates.update({"business_discovery": "confirmed", "phase": "domain_design"})
    elif transition == "confirm-design":
        if gates.get("domain_design") != "draft":
            raise ValueError("domain_design must be draft before confirm-design")
        if state.get("control_mode", "human_led") == "human_led" and gates.get("business_discovery", "not_started") != "confirmed":
            raise ValueError("business_discovery must be confirmed in human_led mode before confirm-design")
        gates.update({"domain_design": "confirmed", "phase": "slice_approval"})
    elif transition == "approve-slice":
        if gates.get("domain_design") != "confirmed":
            raise ValueError("domain_design must be confirmed before approve-slice")
        if gates.get("slice_approval") != "pending":
            raise ValueError("slice_approval must be pending before approve-slice")
        if not (args.slice_id or "").strip():
            raise ValueError("--slice-id is required for approve-slice")
        state["active_slice"] = {"id": args.slice_id.strip(), "name": (args.slice_name or args.slice_id).strip()}
        gates.update({"slice_approval": "approved", "phase": "technology"})
    elif transition == "select-profile":
        active_slice(state)
        if gates.get("domain_design") != "confirmed" or gates.get("slice_approval") != "approved":
            raise ValueError("domain design and slice approval must be complete before select-profile")
        if gates.get("technology_profile") != "pending":
            raise ValueError("technology_profile must be pending before select-profile")
        if not (args.profile_id or "").strip() or not (args.profile_version or "").strip():
            raise ValueError("--profile-id and --profile-version are required for select-profile")
        state["technology_profile"] = {"id": args.profile_id.strip(), "version": args.profile_version.strip()}
        gates.update({"technology_profile": "selected", "phase": "delivery"})
    elif transition == "draft-ui":
        reason = check(state, "ui-design")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_design", "not_started") != "not_started":
            raise ValueError("ui_design must be not_started before draft-ui")
        gates.update({"ui_design": "draft", "phase": "ui_design"})
    elif transition == "confirm-ui":
        reason = check(state, "ui-design")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_design", "not_started") != "draft":
            raise ValueError("ui_design must be draft before confirm-ui")
        gates.update({"ui_design": "confirmed", "phase": "delivery"})
    elif transition == "start-delivery":
        if check(state, "delivery"):
            raise ValueError(check(state, "delivery"))
        if gates.get("delivery") != "not_started":
            raise ValueError("delivery must be not_started before start-delivery")
        gates.update({"delivery": "in_progress", "review": "not_started", "phase": "delivery"})
    elif transition == "verify":
        if gates.get("delivery") not in {"in_progress", "blocked"}:
            raise ValueError("delivery must be in_progress or blocked before verify")
        gates.update({"delivery": "verified", "review": "not_started", "phase": "verification"})
    elif transition == "block":
        if gates.get("delivery") not in {"in_progress", "blocked"}:
            raise ValueError("delivery must be in_progress or blocked before block")
        gates.update({"delivery": "blocked", "review": "not_started", "phase": "verification"})
    elif transition == "start-repair":
        if check(state, "repair"):
            raise ValueError(check(state, "repair"))
        gates.update({"delivery": "in_progress", "review": "not_started", "phase": "repair"})
    elif transition == "pass-review":
        reason = check(state, "review")
        if reason:
            raise ValueError(reason)
        gates.update({"review": "passed", "phase": "verification"})
    elif transition == "block-review":
        reason = check(state, "review")
        if reason:
            raise ValueError(reason)
        gates.update({"review": "blocked", "phase": "verification"})
    elif transition == "reset-slice":
        if gates.get("delivery") != "verified":
            raise ValueError("delivery must be verified before reset-slice")
        if gates.get("review", "not_started") != "passed":
            raise ValueError("review must be passed before reset-slice")
        gates.update({"phase": "discovery", "domain_design": "draft", "slice_approval": "pending", "technology_profile": "pending", "ui_design": "not_started", "delivery": "not_started", "review": "not_started"})
        state["active_slice"] = None
        state.pop("technology_profile", None)
    else:
        raise ValueError(f"unknown transition: {transition}")

    add_history(state, transition, evidence)
    return transition


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--require", choices=sorted(REQUIRED_KEYS), help="read-only check for the next operation")
    mode.add_argument("--transition", choices=TRANSITIONS, help="apply one explicit state transition")
    parser.add_argument("--evidence", help="user message, test result, or record supporting the transition")
    parser.add_argument("--decision-id")
    parser.add_argument("--answer")
    parser.add_argument("--artifact")
    parser.add_argument("--slice-id")
    parser.add_argument("--slice-name")
    parser.add_argument("--profile-id")
    parser.add_argument("--profile-version")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        state = read_state(args.state)
        if args.require:
            reason = check(state, args.require)
            if reason:
                return fail(reason)
            emit({"allowed": True, "require": args.require})
            return 0
        if args.transition == "record-decision" and not (args.decision_id or "").strip():
            return fail("--decision-id is required for record-decision")
        result = apply_transition(state, args)
        write_state(args.state, state)
        emit({"allowed": True, "transition": result})
        return 0
    except ValueError as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
