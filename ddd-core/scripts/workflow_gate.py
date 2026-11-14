#!/usr/bin/env python3
"""Check and apply one explicit transition in a DDD workflow ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from approval import (
    ApprovalError,
    consume_approval,
    digest_bytes,
    digest_file,
    digest_json,
    domain_design_digest,
    verify_credential,
)


REQUIRED_KEYS = {
    "business": ("gates", "decisions"),
    "domain-design": ("gates", "decisions"),
    "slice-approval": ("gates", "active_slice"),
    "technology": ("gates", "active_slice"),
    "database-profile": ("gates", "active_slice", "technology_profile"),
    "performance": ("gates", "active_slice", "technology_profile"),
    "ui-system": ("gates",),
    "ui-practices": ("gates",),
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
    "select-database-profile",
    "confirm-performance",
    "draft-ui-system",
    "confirm-ui-system",
    "draft-ui-practices",
    "confirm-ui-practices",
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

USER_TRANSITIONS = {
    "confirm-mainline",
    "record-decision",
    "confirm-design",
    "approve-slice",
    "select-profile",
    "select-database-profile",
    "confirm-performance",
    "confirm-ui-system",
    "confirm-ui-practices",
    "confirm-ui",
    "reset-slice",
}


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
    if value.get("control_mode") != "human_led":
        raise ValueError("control_mode must be human_led; changing the working agreement requires an explicit workflow rule")
    return value


def project_root_from_state(path: Path) -> Path:
    resolved = path.resolve()
    return resolved.parent.parent if resolved.parent.name == ".ddd" else resolved.parent


def project_path(root: Path, raw: str, label: str) -> Path:
    candidate = Path(raw)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes project root: {raw}") from exc
    return resolved


def project_yaml(root: Path, relative: str, label: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ValueError("PyYAML is required to validate project UI records") from exc
    path = project_path(root, relative, label)
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} not found: {path}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"{label} is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    return value


def performance_profile_loader() -> Any:
    scripts = Path(__file__).resolve().parents[2] / "performance-loop" / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from profile_loader import load_profile  # type: ignore

    return load_profile


def database_profile_from_file(root: Path, relative: str, expected_id: str, expected_version: str) -> dict[str, Any]:
    path = project_path(root, relative, "database profile")
    if not path.is_file():
        raise ValueError(f"database profile not found: {relative}")
    try:
        profile = performance_profile_loader()(path)
    except Exception as exc:  # profile_loader exposes a stable validation error, but preserve a gate-level message.
        raise ValueError(f"database profile is invalid: {exc}") from exc
    if profile.get("id") != expected_id:
        raise ValueError("database profile id does not match the selected profile")
    if str(profile.get("version")) != str(expected_version):
        raise ValueError("database profile version does not match the selected profile")
    return {
        "id": profile["id"],
        "version": str(profile["version"]),
        "profile_version": str(profile.get("profile_version", "")),
        "path": Path(relative).as_posix(),
        "digest": digest_file(path),
    }


def database_profile_path(state: dict[str, Any]) -> str | None:
    record = state.get("database_profile")
    if not isinstance(record, dict):
        return None
    value = record.get("path")
    return value.strip() if isinstance(value, str) and value.strip() else None


def performance_record_path(state: dict[str, Any]) -> str | None:
    record = state.get("performance_contract")
    if not isinstance(record, dict):
        return None
    value = record.get("path")
    return value.strip() if isinstance(value, str) and value.strip() else None


def performance_contract_from_file(root: Path, relative: str, state: dict[str, Any]) -> dict[str, Any]:
    path = project_path(root, relative, "performance contract")
    if not path.is_file():
        raise ValueError(f"performance contract not found: {relative}")
    try:
        scripts = Path(__file__).resolve().parents[2] / "performance-loop" / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from validate_contract import validate  # type: ignore
        profile_record = state.get("database_profile")
        if not isinstance(profile_record, dict):
            raise ValueError("database_profile must be selected before confirming performance")
        profile_path = project_path(root, str(profile_record.get("path")), "database profile")
        result = validate(path, profiles_dir=profile_path.parent)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"performance contract is invalid: {exc}") from exc
    if result.get("status") != "confirmed":
        raise ValueError("performance contract must be confirmed before this gate")
    current_slice = active_slice(state)
    if result.get("slice_id") != current_slice.get("id"):
        raise ValueError("performance contract slice_id does not match active_slice")
    contract = project_yaml(root, relative, "performance contract")
    database = contract.get("profile", {}).get("database", {}) if isinstance(contract.get("profile"), dict) else {}
    profile_record = state.get("database_profile")
    if not isinstance(profile_record, dict) or database.get("adapter_profile") != profile_record.get("id"):
        raise ValueError("performance contract database profile does not match the selected database profile")
    if str(database.get("version")) != str(profile_record.get("version")):
        raise ValueError("performance contract database version does not match the selected database profile")
    return {
        "path": Path(relative).as_posix(),
        "digest": digest_file(path),
        "slice_id": result["slice_id"],
        "database_profile": profile_record["id"],
    }


def database_workflow_required(state: dict[str, Any]) -> bool:
    active = state.get("active_slice")
    gates = state.get("gates")
    return (
        isinstance(active, dict)
        and active.get("requires_database") is True
    ) or (
        isinstance(gates, dict)
        and ("database_profile" in gates or "performance_contract" in gates)
    )


def require_project_record(
    root: Path,
    relative: str,
    expected_status: str,
    label: str,
    require_user_decision: bool = False,
) -> dict[str, Any]:
    record = project_yaml(root, relative, label)
    if record.get("schema_version") != "1":
        raise ValueError(f"{label} schema_version must be \"1\"")
    if record.get("status") != expected_status:
        raise ValueError(f"{label} must have status: {expected_status}")
    if require_user_decision:
        decisions = record.get("decisions")
        if not isinstance(decisions, list) or not any(
            isinstance(item, dict)
            and item.get("source") == "user_decision"
            and isinstance(item.get("evidence"), str)
            and item["evidence"].strip()
            for item in decisions
        ):
            raise ValueError(f"{label} needs a user_decision with evidence before confirmation")
    return record


def require_record_profile(record: dict[str, Any], state: dict[str, Any], label: str) -> None:
    technology = state.get("technology_profile")
    if not isinstance(technology, dict):
        raise ValueError("technology_profile must be selected before confirming UI records")
    if record.get("profile") != technology.get("id") or str(record.get("profile_version")) != str(technology.get("version")):
        raise ValueError(f"{label} profile does not match selected technology_profile")


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


def check(state: dict[str, Any], target: str, root: Path | None = None) -> str | None:
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

    if target in {"ui-system", "ui-practices"}:
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        return None

    if not isinstance(current_slice, dict) or not current_slice.get("id"):
        return "active_slice must contain an id"
    if gates.get("domain_design") != "confirmed":
        return "domain_design must be confirmed"
    if gates.get("slice_approval") != "approved":
        return "slice_approval must be approved"

    if target in {"slice-approval", "technology"}:
        return None
    if target == "database-profile":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected before database profile selection"
        if gates.get("database_profile", "pending") == "selected":
            return "database_profile is already selected"
        return None
    if target == "performance":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected before performance confirmation"
        if gates.get("database_profile") != "selected":
            return "database_profile must be selected before performance confirmation"
        if gates.get("performance_contract") != "confirmed":
            return "performance_contract must be confirmed before performance verification"
        if root is not None:
            try:
                performance_contract_from_file(root, str(performance_record_path(state)), state)
            except ValueError as exc:
                return str(exc)
        return None
    if target == "ui-design":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if gates.get("ui_system", "not_started") != "confirmed":
            return "ui_system must be confirmed"
        if gates.get("ui_practices", "not_started") != "confirmed":
            return "ui_practices must be confirmed"
        if gates.get("ui_design", "not_started") not in {"not_started", "draft"}:
            return "ui_design must be not_started or draft"
        return None
    if target == "scaffold":
        if gates.get("phase") != "delivery":
            return "phase must be delivery before scaffold"
        if gates.get("business_discovery") != "confirmed":
            return "business_discovery must be confirmed before scaffold"
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if gates.get("ui_system", "not_started") != "confirmed":
            return "ui_system must be confirmed"
        if gates.get("ui_practices", "not_started") != "confirmed":
            return "ui_practices must be confirmed"
        if gates.get("ui_design", "not_started") != "confirmed":
            return "ui_design must be confirmed"
        if gates.get("delivery") != "not_started":
            return "delivery must be not_started before scaffold"
        decisions = state.get("decisions")
        if not isinstance(decisions, list) or not any(
            isinstance(item, dict)
            and item.get("status") == "answered"
            and item.get("source") == "user_decision"
            and isinstance(item.get("evidence"), str)
            and item["evidence"].strip()
            for item in decisions
        ):
            return "domain design needs an answered user_decision before scaffold"
        return None
    if target == "delivery" and gates.get("technology_profile") != "selected":
        return "technology_profile must be selected"
    if target == "delivery" and database_workflow_required(state):
        if gates.get("database_profile") != "selected":
            return "database_profile must be selected before delivery"
        if gates.get("performance_contract") != "confirmed":
            return "performance_contract must be confirmed before delivery"
        if root is not None:
            try:
                database_record = state.get("database_profile")
                if not isinstance(database_record, dict):
                    return "database_profile record is missing"
                database_profile_from_file(root, str(database_record.get("path")), str(database_record.get("id")), str(database_record.get("version")))
                performance_contract_from_file(root, str(performance_record_path(state)), state)
            except ValueError as exc:
                return str(exc)
    if target == "delivery" and gates.get("ui_design", "not_started") == "draft":
        return "ui_design must be confirmed or not_started"
    if target == "delivery" and gates.get("ui_design", "not_started") == "confirmed":
        if gates.get("ui_system", "not_started") != "confirmed":
            return "ui_system must be confirmed for a UI delivery"
        if gates.get("ui_practices", "not_started") != "confirmed":
            return "ui_practices must be confirmed for a UI delivery"
    if target == "repair":
        if gates.get("delivery") in {"in_progress", "blocked"}:
            return None
        if gates.get("delivery") == "verified" and gates.get("review", "not_started") == "blocked":
            return None
        return "delivery must be in_progress or blocked, or verified with a blocked review"
    if target == "review":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if gates.get("ui_design", "not_started") == "confirmed":
            if gates.get("ui_system", "not_started") != "confirmed":
                return "ui_system must be confirmed for a UI review"
            if gates.get("ui_practices", "not_started") != "confirmed":
                return "ui_practices must be confirmed for a UI review"
        if gates.get("delivery") != "verified":
            return "delivery must be verified before review"
        if database_workflow_required(state):
            if gates.get("database_profile") != "selected":
                return "database_profile must be selected before review"
            if gates.get("performance_contract") != "confirmed":
                return "performance_contract must be confirmed before review"
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


def serialized_state(state: dict[str, Any]) -> bytes:
    return (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def state_digest(state: dict[str, Any]) -> str:
    return digest_bytes(serialized_state(state))


def approval_arguments(state: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Return the canonical, user-visible arguments covered by a signature."""
    transition = args.transition
    result: dict[str, Any] = {
        "transition": transition,
        "evidence": (args.evidence or "").strip(),
    }
    if transition == "record-decision":
        decision = next(
            (
                item
                for item in state.get("decisions", [])
                if isinstance(item, dict) and item.get("id") == (args.decision_id or "").strip()
            ),
            None,
        )
        result.update({
            "decision_id": (args.decision_id or "").strip(),
            "answer": (args.answer or "").strip(),
        })
        if isinstance(decision, dict):
            proposed = dict(decision)
            proposed.update({"status": "answered", "source": "user_decision", "answer": (args.answer or "").strip(), "evidence": result["evidence"]})
            result["decision_digest"] = digest_json(proposed)
    elif transition == "confirm-mainline":
        result["artifact"] = state.get("business_artifact")
    elif transition == "confirm-design":
        result["domain_design_digest"] = domain_design_digest(state)
    elif transition == "approve-slice":
        result.update({
            "slice_id": (args.slice_id or "").strip(),
            "slice_name": (args.slice_name or args.slice_id or "").strip(),
        })
        slice_payload: dict[str, Any] = {"id": result["slice_id"], "name": result["slice_name"]}
        requires_database = getattr(args, "requires_database", None)
        if requires_database is not None:
            slice_payload["requires_database"] = bool(requires_database)
            result["requires_database"] = bool(requires_database)
        result["slice_digest"] = digest_json(slice_payload)
    elif transition == "select-profile":
        result.update({
            "profile_id": (args.profile_id or "").strip(),
            "profile_version": (args.profile_version or "").strip(),
        })
        result["profile_digest"] = digest_json({"id": result["profile_id"], "version": result["profile_version"]})
    elif transition == "select-database-profile":
        database_id = (args.database_profile_id or "").strip()
        result.update({
            "database_profile_id": database_id,
            "database_profile_version": (args.database_profile_version or "").strip(),
            "database_profile_path": (args.database_profile_path or f".ddd/performance-profiles/{database_id}.yaml").strip(),
        })
    elif transition == "confirm-performance":
        record_path = (args.performance_record or "").strip()
        if not record_path:
            current = state.get("active_slice")
            record_path = f".ddd/performance/{current.get('id')}.yaml" if isinstance(current, dict) else ""
        result.update({
            "performance_record": record_path,
            "database_profile_id": (state.get("database_profile") or {}).get("id", ""),
        })
    return result


def approval_records_for_transition(
    state: dict[str, Any],
    transition: str,
    args: argparse.Namespace | None = None,
) -> list[str]:
    if transition == "confirm-mainline":
        artifact = state.get("business_artifact")
        return [artifact] if isinstance(artifact, str) and artifact.strip() else []
    if transition == "confirm-ui-system":
        return [".ddd/ui-system.yaml"]
    if transition == "confirm-ui-practices":
        return [".ddd/ui-practices.yaml"]
    if transition == "confirm-ui":
        return [".ddd/ui-plan.yaml"]
    if transition == "select-database-profile":
        default_path = None
        if args is not None and isinstance(args.database_profile_id, str) and args.database_profile_id.strip():
            default_path = f".ddd/performance-profiles/{args.database_profile_id.strip()}.yaml"
        path = (args.database_profile_path if args is not None else None) or default_path or database_profile_path(state)
        return [path] if isinstance(path, str) and path.strip() else []
    if transition == "confirm-performance":
        default_path = None
        if args is not None and not (args.performance_record or "").strip():
            current = state.get("active_slice")
            if isinstance(current, dict) and current.get("id"):
                default_path = f".ddd/performance/{current['id']}.yaml"
        path = (args.performance_record if args is not None else None) or default_path or performance_record_path(state)
        return [path] if isinstance(path, str) and path.strip() else []
    return []


def consumed_request_ids(state: dict[str, Any]) -> set[str]:
    history = state.get("history")
    if not isinstance(history, list):
        return set()
    result: set[str] = set()
    for item in history:
        if not isinstance(item, dict):
            continue
        approval = item.get("approval")
        if isinstance(approval, dict) and isinstance(approval.get("request_id"), str):
            result.add(approval["request_id"])
    return result


def required_user_transitions(state: dict[str, Any]) -> set[str]:
    """Derive the approvals that must exist for the ledger's current gates.

    Gate fields are useful indexes, but they are never evidence by themselves.
    A downstream read-only check must see the corresponding signed transition
    before it can accept a hand-edited ledger.
    """
    gates = state.get("gates")
    if not isinstance(gates, dict):
        return set()
    required: set[str] = set()
    if gates.get("business_discovery") == "confirmed":
        required.add("confirm-mainline")
    if gates.get("domain_design") == "confirmed":
        required.add("confirm-design")
    if gates.get("slice_approval") == "approved":
        required.add("approve-slice")
    if gates.get("technology_profile") == "selected":
        required.add("select-profile")
    if gates.get("database_profile") == "selected":
        required.add("select-database-profile")
    if gates.get("performance_contract") == "confirmed":
        required.add("confirm-performance")
    if gates.get("ui_system") == "confirmed":
        required.add("confirm-ui-system")
    if gates.get("ui_practices") == "confirmed":
        required.add("confirm-ui-practices")
    if gates.get("ui_design") == "confirmed":
        required.add("confirm-ui")
    decisions = state.get("decisions")
    if isinstance(decisions, list) and any(
        isinstance(item, dict)
        and item.get("status") == "answered"
        and item.get("source") == "user_decision"
        for item in decisions
    ):
        required.add("record-decision")
    return required


def verify_transition_approval(
    state: dict[str, Any],
    args: argparse.Namespace,
    state_path: Path | None,
) -> dict[str, Any] | None:
    if args.transition not in USER_TRANSITIONS:
        return None
    if state_path is None:
        raise ValueError("user transitions require a workflow ledger path and signed approval")
    approval_path = (args.approval or "").strip()
    if not approval_path:
        raise ValueError(
            "user transition requires --approval, --trusted-public-key, and the fixed user trust manifest; run approval.py trust-path to locate it"
        )
    if not (args.trusted_public_key or "").strip():
        raise ValueError("user transition requires an explicit --trusted-public-key assertion")
    root = project_root_from_state(state_path)
    candidate = Path(approval_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        return verify_credential(
            state_path,
            candidate,
            args.trusted_public_key,
            expected_action=f"workflow:{args.transition}",
            expected_arguments=approval_arguments(state, args),
            expected_records=approval_records_for_transition(state, args.transition, args),
            used_request_ids=consumed_request_ids(state),
        )
    except ApprovalError as exc:
        raise ValueError(str(exc)) from exc


def validate_history_approvals(
    state: dict[str, Any],
    state_path: Path,
    trusted_public_key: str | None,
) -> None:
    """Reject a ledger that contains hand-written or replayed user history."""
    history = state.get("history")
    if not isinstance(history, list):
        raise ValueError("workflow ledger history must be an array")
    required = required_user_transitions(state)
    has_user_history = any(isinstance(item, dict) and item.get("actor") == "user" for item in history)
    if not trusted_public_key and (required or has_user_history):
        raise ValueError(
            "a trusted public key is required to validate existing user history; "
            "pass --trusted-public-key and provision the fixed user trust manifest (approval.py trust-path)"
        )
    seen: set[str] = set()
    observed: set[str] = set()
    recorded_decisions: set[str] = set()
    root = project_root_from_state(state_path)
    for item in history:
        if not isinstance(item, dict):
            continue
        transition = item.get("transition")
        if item.get("actor") != "user":
            if "approval" in item:
                raise ValueError(f"agent history entry {transition} cannot carry a user approval")
            continue
        approval = item.get("approval")
        if not isinstance(approval, dict):
            raise ValueError(f"user history entry {transition} lacks a signed approval")
        request_id = approval.get("request_id")
        credential_ref = approval.get("credential")
        if not isinstance(transition, str) or not transition or not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("user history approval has an invalid transition or request_id")
        if transition in observed and transition != "record-decision":
            raise ValueError(f"user transition was recorded more than once: {transition}")
        observed.add(transition)
        if request_id in seen:
            raise ValueError(f"approval request was replayed in history: {request_id}")
        seen.add(request_id)
        if not isinstance(credential_ref, str) or not credential_ref.strip():
            raise ValueError(f"user history entry {transition} lacks a credential path")
        credential_path = project_path(root, credential_ref, "approval credential")
        try:
            verified = verify_credential(
                state_path,
                credential_path,
                trusted_public_key,
                expected_action=f"workflow:{transition}",
                expected_records=approval_records_for_transition(state, transition),
                check_state=False,
                allow_consumed=True,
            )
        except ApprovalError as exc:
            raise ValueError(f"user history approval for {transition} is invalid: {exc}") from exc
        if verified["request_id"] != request_id or verified["payload_digest"] != approval.get("payload_digest"):
            raise ValueError(f"user history approval metadata does not match its credential: {transition}")
        if verified["public_key_fingerprint"] != approval.get("public_key_fingerprint"):
            raise ValueError(f"user history approval key metadata does not match its credential: {transition}")
        if verified["payload"].get("state_digest") != approval.get("state_digest"):
            raise ValueError(f"user history approval state metadata does not match its credential: {transition}")
        if verified["payload"].get("project_id") != approval.get("project_id"):
            raise ValueError(f"user history approval project metadata does not match its credential: {transition}")
        payload = verified["payload"]
        arguments = payload.get("arguments")
        if not isinstance(arguments, dict) or arguments.get("transition") != transition or arguments.get("evidence") != item.get("evidence"):
            raise ValueError(f"user history approval arguments do not match {transition}")
        if transition == "record-decision":
            decision_id = arguments.get("decision_id")
            if isinstance(decision_id, str) and decision_id.strip():
                recorded_decisions.add(decision_id)
            decision = next(
                (
                    entry
                    for entry in state.get("decisions", [])
                    if isinstance(entry, dict) and entry.get("id") == arguments.get("decision_id")
                ),
                None,
            )
            if (
                not isinstance(decision, dict)
                or decision.get("status") != "answered"
                or decision.get("source") != "user_decision"
                or decision.get("answer") != arguments.get("answer")
                or decision.get("evidence") != item.get("evidence")
                or arguments.get("decision_digest") != digest_json(decision)
            ):
                raise ValueError("signed record-decision no longer matches the decision record")
        elif transition == "confirm-mainline" and state.get("business_artifact") != arguments.get("artifact"):
            raise ValueError("signed confirm-mainline no longer matches business_artifact")
        elif transition == "confirm-design" and arguments.get("domain_design_digest") != domain_design_digest(state):
            raise ValueError("signed confirm-design no longer matches the domain design snapshot")
        elif transition == "approve-slice":
            current_slice = state.get("active_slice")
            if (
                not isinstance(current_slice, dict)
                or current_slice.get("id") != arguments.get("slice_id")
                or current_slice.get("name") != arguments.get("slice_name")
                or arguments.get("slice_digest") != digest_json(current_slice)
            ):
                raise ValueError("signed approve-slice no longer matches active_slice")
        elif transition == "select-profile":
            technology = state.get("technology_profile")
            if (
                not isinstance(technology, dict)
                or technology.get("id") != arguments.get("profile_id")
                or str(technology.get("version")) != str(arguments.get("profile_version"))
                or arguments.get("profile_digest") != digest_json(technology)
            ):
                raise ValueError("signed select-profile no longer matches technology_profile")
        elif transition == "select-database-profile":
            database_record = state.get("database_profile")
            if (
                not isinstance(database_record, dict)
                or database_record.get("id") != arguments.get("database_profile_id")
                or str(database_record.get("version")) != str(arguments.get("database_profile_version"))
                or database_record.get("path") != arguments.get("database_profile_path")
                or database_record.get("digest") != digest_file(project_path(root, str(database_record.get("path")), "database profile"))
            ):
                raise ValueError("signed select-database-profile no longer matches database_profile")
        elif transition == "confirm-performance":
            performance_record = state.get("performance_contract")
            if (
                not isinstance(performance_record, dict)
                or performance_record.get("path") != arguments.get("performance_record")
                or performance_record.get("database_profile") != arguments.get("database_profile_id")
                or performance_record.get("digest") != digest_file(project_path(root, str(performance_record.get("path")), "performance contract"))
            ):
                raise ValueError("signed confirm-performance no longer matches performance_contract")
    missing = sorted(required - observed)
    if missing:
        raise ValueError(f"workflow ledger lacks user confirmations: {', '.join(missing)}")
    decisions = state.get("decisions")
    required_decisions = {
        item.get("id")
        for item in decisions
        if isinstance(item, dict)
        and item.get("status") == "answered"
        and item.get("source") == "user_decision"
        and isinstance(item.get("id"), str)
        and item.get("id").strip()
    } if isinstance(decisions, list) else set()
    missing_decisions = sorted(required_decisions - recorded_decisions)
    if missing_decisions:
        raise ValueError(f"answered decisions lack signed record-decision approvals: {', '.join(missing_decisions)}")


def add_history(
    state: dict[str, Any],
    transition: str,
    evidence: str,
    approval: dict[str, Any] | None = None,
) -> None:
    history = state.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("history must be an array when present")
    if transition in USER_TRANSITIONS and approval is None:
        raise ValueError(f"{transition} requires a verified user approval")
    entry: dict[str, Any] = {
        "transition": transition,
        "actor": "user" if transition in USER_TRANSITIONS else "agent",
        "evidence": evidence,
    }
    if approval is not None:
        payload = approval.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("verified approval is missing its signed payload")
        entry["approval"] = {
            "request_id": approval["request_id"],
            "payload_digest": approval["payload_digest"],
            "public_key_fingerprint": approval["public_key_fingerprint"],
            "credential": approval["credential"],
            "request": approval["request"],
            "action": payload.get("action"),
            "arguments": payload.get("arguments"),
            "project_id": payload.get("project_id"),
            "state_digest": payload.get("state_digest"),
            "record_digests": payload.get("record_digests", {}),
        }
    history.append(entry)


def require_evidence(args: argparse.Namespace) -> str:
    evidence = (args.evidence or "").strip()
    if not evidence:
        raise ValueError("--evidence is required for an explicit transition")
    return evidence


def apply_transition(state: dict[str, Any], args: argparse.Namespace, state_path: Path | None = None) -> str:
    transition = args.transition
    gates = require_object(state, "gates")
    evidence = require_evidence(args)
    root = project_root_from_state(state_path) if state_path is not None else None
    approval = verify_transition_approval(state, args, state_path)

    if transition == "record-decision":
        if gates.get("domain_design") != "draft":
            raise ValueError("cannot record a decision after domain design is confirmed; reset the slice first")
        decisions = state.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError("decisions must be an array")
        decision = next((item for item in decisions if isinstance(item, dict) and item.get("id") == args.decision_id), None)
        if decision is None:
            raise ValueError(f"decision not found: {args.decision_id}")
        if not (args.answer or "").strip():
            raise ValueError("--answer is required for record-decision")
        decision.update({"status": "answered", "source": "user_decision", "answer": args.answer.strip(), "evidence": evidence})
        add_history(state, transition, evidence, approval)
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
        if root is not None and not project_path(root, args.artifact.strip(), "business artifact").is_file():
            raise ValueError(f"business artifact not found: {args.artifact.strip()}")
        state["business_artifact"] = args.artifact.strip()
        gates.update({"business_discovery": "draft", "phase": "business_discovery"})
    elif transition == "confirm-mainline":
        if gates.get("business_discovery", "not_started") != "draft":
            raise ValueError("business_discovery must be draft before confirm-mainline")
        if not (state.get("business_artifact") or "").strip():
            raise ValueError("business_artifact is required before confirm-mainline")
        if root is not None and not project_path(root, state["business_artifact"], "business artifact").is_file():
            raise ValueError(f"business artifact not found: {state['business_artifact']}")
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
        if args.requires_database is not None:
            state["active_slice"]["requires_database"] = bool(args.requires_database)
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
    elif transition == "select-database-profile":
        reason = check(state, "database-profile")
        if reason:
            raise ValueError(reason)
        if not (args.database_profile_id or "").strip() or not (args.database_profile_version or "").strip():
            raise ValueError("--database-profile-id and --database-profile-version are required for select-database-profile")
        if gates.get("database_profile") == "selected":
            raise ValueError("database_profile must not already be selected")
        root = project_root_from_state(state_path) if state_path is not None else None
        if root is None:
            raise ValueError("select-database-profile requires a workflow ledger path")
        relative = (args.database_profile_path or f".ddd/performance-profiles/{args.database_profile_id.strip()}.yaml").strip()
        record = database_profile_from_file(root, relative, args.database_profile_id.strip(), args.database_profile_version.strip())
        state["database_profile"] = record
        gates.update({"database_profile": "selected", "performance_contract": "pending", "phase": "performance"})
    elif transition == "confirm-performance":
        if gates.get("database_profile") != "selected":
            raise ValueError("database_profile must be selected before confirm-performance")
        if gates.get("performance_contract", "pending") == "confirmed":
            raise ValueError("performance_contract must not already be confirmed")
        root = project_root_from_state(state_path) if state_path is not None else None
        if root is None:
            raise ValueError("confirm-performance requires a workflow ledger path")
        relative = (args.performance_record or f".ddd/performance/{active_slice(state)['id']}.yaml").strip()
        record = performance_contract_from_file(root, relative, state)
        state["performance_contract"] = record
        gates.update({"performance_contract": "confirmed", "phase": "delivery"})
    elif transition == "draft-ui-system":
        reason = check(state, "ui-system")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_system", "not_started") != "not_started":
            raise ValueError("ui_system must be not_started before draft-ui-system")
        if root is not None:
            record = require_project_record(root, ".ddd/ui-system.yaml", "draft", "ui-system.yaml")
            require_record_profile(record, state, "ui-system.yaml")
        gates.update({"ui_system": "draft", "phase": "ui_design"})
    elif transition == "confirm-ui-system":
        reason = check(state, "ui-system")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_system", "not_started") != "draft":
            raise ValueError("ui_system must be draft before confirm-ui-system")
        if root is not None:
            record = require_project_record(root, ".ddd/ui-system.yaml", "confirmed", "ui-system.yaml", require_user_decision=True)
            require_record_profile(record, state, "ui-system.yaml")
        gates.update({"ui_system": "confirmed", "phase": "ui_design"})
    elif transition == "draft-ui-practices":
        reason = check(state, "ui-practices")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_practices", "not_started") != "not_started":
            raise ValueError("ui_practices must be not_started before draft-ui-practices")
        if root is not None:
            record = require_project_record(root, ".ddd/ui-practices.yaml", "draft", "ui-practices.yaml")
            require_record_profile(record, state, "ui-practices.yaml")
        gates.update({"ui_practices": "draft", "phase": "ui_design"})
    elif transition == "confirm-ui-practices":
        reason = check(state, "ui-practices")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_practices", "not_started") != "draft":
            raise ValueError("ui_practices must be draft before confirm-ui-practices")
        if root is not None:
            record = require_project_record(root, ".ddd/ui-practices.yaml", "confirmed", "ui-practices.yaml", require_user_decision=True)
            require_record_profile(record, state, "ui-practices.yaml")
        gates.update({"ui_practices": "confirmed", "phase": "ui_design"})
    elif transition == "draft-ui":
        reason = check(state, "ui-design")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_design", "not_started") != "not_started":
            raise ValueError("ui_design must be not_started before draft-ui")
        if root is not None:
            record = require_project_record(root, ".ddd/ui-plan.yaml", "draft", "ui-plan.yaml")
            require_record_profile(record, state, "ui-plan.yaml")
        gates.update({"ui_design": "draft", "phase": "ui_design"})
    elif transition == "confirm-ui":
        reason = check(state, "ui-design")
        if reason:
            raise ValueError(reason)
        if gates.get("ui_design", "not_started") != "draft":
            raise ValueError("ui_design must be draft before confirm-ui")
        if root is not None:
            record = require_project_record(root, ".ddd/ui-plan.yaml", "confirmed", "ui-plan.yaml", require_user_decision=True)
            require_record_profile(record, state, "ui-plan.yaml")
            current_slice = active_slice(state)
            if record.get("active_slice") != current_slice["id"]:
                raise ValueError("ui-plan active_slice does not match active_slice")
        gates.update({"ui_design": "confirmed", "phase": "delivery"})
    elif transition == "start-delivery":
        reason = check(state, "delivery", project_root_from_state(state_path) if state_path is not None else None)
        if reason:
            raise ValueError(reason)
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
        reason = check(state, "review", project_root_from_state(state_path) if state_path is not None else None)
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
        gates.update({"phase": "discovery", "domain_design": "draft", "slice_approval": "pending", "technology_profile": "pending", "ui_system": "not_started", "ui_practices": "not_started", "ui_design": "not_started", "delivery": "not_started", "review": "not_started"})
        state["active_slice"] = None
        state.pop("technology_profile", None)
        state.pop("database_profile", None)
        state.pop("performance_contract", None)
        gates.pop("database_profile", None)
        gates.pop("performance_contract", None)
    else:
        raise ValueError(f"unknown transition: {transition}")

    add_history(state, transition, evidence, approval)
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
    parser.add_argument("--requires-database", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--profile-id")
    parser.add_argument("--profile-version")
    parser.add_argument("--database-profile-id")
    parser.add_argument("--database-profile-version")
    parser.add_argument("--database-profile-path")
    parser.add_argument("--performance-record")
    parser.add_argument("--approval", help="project-relative signed approval credential for a user transition")
    parser.add_argument("--trusted-public-key", help="external trusted Ed25519 public key used to verify approval")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        state = read_state(args.state)
        validate_history_approvals(state, args.state, args.trusted_public_key)
        if args.require:
            reason = check(state, args.require, project_root_from_state(args.state))
            if reason:
                return fail(reason)
            emit({"allowed": True, "require": args.require})
            return 0
        if args.transition == "record-decision" and not (args.decision_id or "").strip():
            return fail("--decision-id is required for record-decision")
        pre_state_digest = digest_file(args.state)
        result = apply_transition(state, args, args.state)
        if args.transition in USER_TRANSITIONS:
            history = state.get("history")
            approval = history[-1].get("approval") if isinstance(history, list) and history and isinstance(history[-1], dict) else None
            if not isinstance(approval, dict):
                return fail("user transition did not produce verified approval metadata")
            payload = approval.get("state_digest")
            if payload != pre_state_digest:
                return fail("workflow ledger changed while the approval was being applied")
            post_state_digest = state_digest(state)
            consume_approval(
                args.state,
                approval,
                args.trusted_public_key,
                pre_state_digest=pre_state_digest,
                post_state_digest=post_state_digest,
            )
        write_state(args.state, state)
        emit({"allowed": True, "transition": result})
        return 0
    except ValueError as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
