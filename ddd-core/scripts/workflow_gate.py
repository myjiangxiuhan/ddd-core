#!/usr/bin/env python3
"""Check and apply one explicit transition in a DDD workflow ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from record_utils import digest_bytes


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
    "scaffold-backend": ("gates", "active_slice"),
    "delivery": ("gates", "active_slice"),
    "repair": ("gates", "active_slice"),
    "review": ("gates", "active_slice"),
}

TRANSITIONS = (
    "record-mainline",
    "confirm-mainline",
    "record-decision",
    "confirm-design",
    "approve-slice",
    "select-profile",
    "select-database-profile",
    "record-performance",
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


def database_profile_from_file(root: Path, relative: str, expected_id: str, expected_version: str) -> dict[str, Any]:
    path = project_path(root, relative, "database profile")
    try:
        raw = path.read_bytes()
        current_digest = digest_bytes(raw)
        import yaml  # type: ignore
        scripts = Path(__file__).resolve().parents[2] / "performance-loop" / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from profile_loader import validate_profile  # type: ignore

        profile_value = yaml.safe_load(raw.decode("utf-8-sig"))
        if not isinstance(profile_value, dict):
            raise ValueError("database profile root must be an object")
        profile = validate_profile(profile_value)
    except FileNotFoundError as exc:
        raise ValueError(f"database profile not found: {relative}") from exc
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
        "digest": current_digest,
    }


def _performance_contract_snapshot(
    root: Path,
    relative: str,
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = project_path(root, relative, "performance contract")
    if not path.is_file():
        raise ValueError(f"performance contract not found: {relative}")
    try:
        raw = path.read_bytes()
        current_digest = digest_bytes(raw)
    except OSError as exc:
        raise ValueError(f"cannot read performance contract: {relative}") from exc
    try:
        scripts = Path(__file__).resolve().parents[2] / "performance-loop" / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from validate_contract import validate  # type: ignore
        import yaml  # type: ignore
        profile_record = state.get("database_profile")
        if not isinstance(profile_record, dict):
            raise ValueError("database_profile must be selected before recording performance evidence")
        profile_path = project_path(root, str(profile_record.get("path")), "database profile")
        contract = yaml.safe_load(raw.decode("utf-8-sig"))
        if not isinstance(contract, dict):
            raise ValueError("performance contract root must be an object")
        result = validate(path, profiles_dir=profile_path.parent, document=contract)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"performance contract is invalid: {exc}") from exc
    if result.get("status") != "confirmed":
        raise ValueError("performance contract must be confirmed before recording performance evidence")
    current_slice = active_slice(state)
    if result.get("slice_id") != current_slice.get("id"):
        raise ValueError("performance contract slice_id does not match active_slice")
    database = contract.get("profile", {}).get("database", {}) if isinstance(contract.get("profile"), dict) else {}
    profile_record = state.get("database_profile")
    if not isinstance(profile_record, dict) or database.get("adapter_profile") != profile_record.get("id"):
        raise ValueError("performance contract database profile does not match the selected database profile")
    if str(database.get("version")) != str(profile_record.get("version")):
        raise ValueError("performance contract database version does not match the selected database profile")
    existing_record = state.get("performance_contract")
    if isinstance(existing_record, dict) and existing_record.get("digest") != current_digest:
        raise ValueError("performance contract digest does not match the selected workflow record")
    result_record = {
        "path": Path(relative).as_posix(),
        "digest": current_digest,
        "slice_id": result["slice_id"],
        "database_profile": profile_record["id"],
    }
    baseline_spec = contract.get("baseline")
    if isinstance(baseline_spec, dict) and isinstance(baseline_spec.get("result"), str):
        result_record["baseline_result"] = Path(baseline_spec["result"]).as_posix()
    return result_record, contract


def performance_contract_from_file(root: Path, relative: str, state: dict[str, Any]) -> dict[str, Any]:
    return _performance_contract_snapshot(root, relative, state)[0]


def baseline_record_from_file(root: Path, relative: str, state: dict[str, Any]) -> dict[str, Any]:
    """Read the exact baseline bytes and derive its project evidence record."""
    path = project_path(root, relative, "baseline result")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"baseline result not found: {relative}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"baseline result is not valid JSON: {relative}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1":
        raise ValueError("baseline result must use schema_version 1")

    active = active_slice(state)
    if value.get("slice_id") != active.get("id"):
        raise ValueError("baseline slice_id does not match active_slice")
    commit = value.get("commit")
    dataset_digest = value.get("dataset_digest")
    if not isinstance(commit, str) or not commit.strip():
        raise ValueError("baseline.commit must be a non-empty string")
    if not isinstance(dataset_digest, str) or not dataset_digest.strip():
        raise ValueError("baseline.dataset_digest must be a non-empty string")
    if not isinstance(value.get("environment"), dict) or not value["environment"]:
        raise ValueError("baseline.environment must be a non-empty object")

    database_record = state.get("database_profile")
    if not isinstance(database_record, dict):
        raise ValueError("database_profile must be selected before reading the baseline record")
    current_profile = database_profile_from_file(
        root,
        str(database_record.get("path")),
        str(database_record.get("id")),
        str(database_record.get("version")),
    )
    if current_profile.get("digest") != database_record.get("digest"):
        raise ValueError("database profile digest does not match the selected workflow record")
    if value.get("database_profile") != database_record.get("id"):
        raise ValueError("baseline database_profile does not match the selected database profile")

    performance_record = state.get("performance_contract")
    if not isinstance(performance_record, dict):
        raise ValueError("performance_contract must be recorded before reading the baseline record")
    contract_record, contract = _performance_contract_snapshot(root, str(performance_record.get("path")), state)
    if contract_record.get("digest") != performance_record.get("digest"):
        raise ValueError("performance contract digest does not match the selected workflow record")
    if value.get("contract_id") != contract.get("id"):
        raise ValueError("baseline contract_id does not match the performance contract")
    contract_profile = contract.get("profile")
    if not isinstance(contract_profile, dict):
        raise ValueError("performance contract profile is missing")
    contract_database = contract_profile.get("database")
    if not isinstance(contract_database, dict):
        raise ValueError("performance contract database profile is missing")
    expected_databases = {f"{contract_database.get('engine')}:{contract_database.get('version')}"}
    release = current_profile.get("release")
    if isinstance(release, dict) and isinstance(release.get("tested_minor"), str) and release["tested_minor"].strip():
        expected_databases.add(f"{contract_database.get('engine')}:{release['tested_minor']}")
    if value["environment"].get("database") not in expected_databases:
        raise ValueError("baseline.environment.database does not match the performance contract database")
    baseline_profile = value.get("profile")
    if (
        not isinstance(baseline_profile, dict)
        or baseline_profile.get("id") != contract_profile.get("id")
        or str(baseline_profile.get("version")) != str(contract_profile.get("version"))
    ):
        raise ValueError("baseline profile does not match the performance contract")
    if contract_database.get("adapter_profile") != database_record.get("id"):
        raise ValueError("performance contract database profile does not match the selected database profile")
    baseline_spec = contract.get("baseline")
    if not isinstance(baseline_spec, dict) or not isinstance(baseline_spec.get("result"), str):
        raise ValueError("performance contract must bind a baseline.result path")
    if project_path(root, baseline_spec["result"], "baseline result") != path:
        raise ValueError("baseline path does not match the performance contract")
    workload = contract.get("workload")
    dataset = workload.get("dataset") if isinstance(workload, dict) else None
    if not isinstance(dataset, dict) or value.get("dataset_rows") != dataset.get("rows"):
        raise ValueError("baseline.dataset_rows does not match the performance contract")

    return {
        "path": Path(relative).as_posix(),
        "digest": digest_bytes(raw),
        "contract_path": performance_record["path"],
        "contract_digest": performance_record["digest"],
        "database_profile": database_record["id"],
        "database_profile_version": str(database_record.get("version")),
        "database_profile_path": database_record["path"],
        "database_profile_digest": database_record["digest"],
        "dataset_digest": dataset_digest,
        "dataset_rows": value["dataset_rows"],
        "commit": commit,
        "slice_id": active["id"],
    }


def require_record_profile(record: dict[str, Any], state: dict[str, Any], label: str, *, optional: bool = False) -> None:
    technology = state.get("technology_profile")
    if not isinstance(technology, dict):
        if optional and not record.get("profile") and not record.get("profile_version"):
            return
        raise ValueError("technology_profile must be selected before confirming UI records")
    if record.get("profile") != technology.get("id") or str(record.get("profile_version")) != str(technology.get("version")):
        raise ValueError(f"{label} profile does not match selected technology_profile")


def confirmed_ui_record_reason(root: Path | None, relative: str, state: dict[str, Any], *, optional_profile: bool = False) -> str | None:
    """Use the UI record as the source of truth instead of a mirrored gate field."""
    if root is None:
        return None
    label = Path(relative).name
    try:
        record = project_yaml(root, relative, label)
        if record.get("status") != "confirmed":
            return f"{label} must be confirmed"
        decisions = record.get("decisions")
        if not isinstance(decisions, list) or not any(
            isinstance(item, dict)
            and item.get("source") == "user_decision"
            and isinstance(item.get("evidence"), str)
            and item["evidence"].strip()
            for item in decisions
        ):
            return f"{label} needs a user_decision with evidence"
        require_record_profile(record, state, label, optional=optional_profile)
    except ValueError as exc:
        return str(exc)
    return None


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


def check(
    state: dict[str, Any],
    target: str,
    root: Path | None = None,
) -> str | None:
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

    if target == "ui-system":
        return None

    if target == "ui-practices":
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
        if isinstance(state.get("database_profile"), dict):
            return "database_profile is already selected"
        return None
    if target == "performance":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected before recording performance evidence"
        return None
    if target == "ui-design":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        if root is not None:
            for relative, optional_profile in ((".ddd/ui-system.yaml", True), (".ddd/ui-practices.yaml", False)):
                reason = confirmed_ui_record_reason(root, relative, state, optional_profile=optional_profile)
                if reason:
                    return reason
        else:
            if gates.get("ui_system", "not_started") != "confirmed":
                return "ui_system must be confirmed"
            if gates.get("ui_practices", "not_started") != "confirmed":
                return "ui_practices must be confirmed"
        if gates.get("ui_design", "not_started") not in {"not_started", "draft", "confirmed"}:
            return "ui_design must be not_started, draft, or confirmed"
        return None
    if target in {"scaffold", "scaffold-backend"}:
        if gates.get("phase") != "delivery":
            return "phase must be delivery before scaffold"
        if gates.get("business_discovery") != "confirmed":
            return "business_discovery must be confirmed before scaffold"
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
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
    if target == "delivery" and root is not None:
        ui_plan_path = root / ".ddd" / "ui-plan.yaml"
        ui_plan = project_yaml(root, ".ddd/ui-plan.yaml", "ui-plan.yaml") if ui_plan_path.exists() else None
        if isinstance(ui_plan, dict) and ui_plan.get("status") != "confirmed":
            return "ui-plan.yaml must be confirmed before delivery"
    if target == "repair":
        if gates.get("delivery") in {"in_progress", "blocked"}:
            return None
        if gates.get("delivery") == "verified" and gates.get("review", "not_started") == "blocked":
            return None
        return "delivery must be in_progress or blocked, or verified with a blocked review"
    if target == "review":
        if gates.get("technology_profile") != "selected":
            return "technology_profile must be selected"
        ui_design_confirmed = gates.get("ui_design", "not_started") == "confirmed"
        if root is not None:
            ui_plan_path = root / ".ddd" / "ui-plan.yaml"
            if ui_plan_path.exists():
                try:
                    ui_plan = project_yaml(root, ".ddd/ui-plan.yaml", "ui-plan.yaml")
                except ValueError as exc:
                    return str(exc)
                ui_design_confirmed = ui_plan.get("status") == "confirmed"
        if ui_design_confirmed:
            for relative, optional_profile in ((".ddd/ui-system.yaml", True), (".ddd/ui-practices.yaml", False)):
                reason = confirmed_ui_record_reason(root, relative, state, optional_profile=optional_profile)
                if reason:
                    return f"{reason} for a UI review"
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


def add_history(
    state: dict[str, Any],
    transition: str,
    evidence: str,
) -> None:
    history = state.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("history must be an array when present")
    entry: dict[str, Any] = {
        "transition": transition,
        "actor": "user" if transition in USER_TRANSITIONS else "agent",
        "evidence": evidence,
    }
    history.append(entry)


def require_evidence(args: argparse.Namespace) -> str:
    evidence = (args.evidence or "").strip()
    if evidence:
        return evidence
    if args.transition in USER_TRANSITIONS:
        raise ValueError("--evidence is required for a user decision transition")
    return f"mechanical transition: {args.transition}"


def parse_components(raw_values: list[str] | None) -> list[dict[str, str]]:
    if not raw_values:
        return []
    components: list[dict[str, str]] = []
    singleton_kinds = {"language", "framework", "runtime", "ui_library"}
    seen_kinds: set[str] = set()
    for raw in raw_values:
        parts = raw.split(":", 2)
        if len(parts) != 3 or any(not part.strip() for part in parts):
            raise ValueError("--component must use kind:id:version")
        kind, component_id, version = (part.strip() for part in parts)
        if kind in singleton_kinds and kind in seen_kinds:
            raise ValueError(f"only one component may be selected for kind: {kind}")
        if kind in singleton_kinds:
            seen_kinds.add(kind)
        components.append({"kind": kind, "id": component_id, "version": version})
    return components


def apply_transition(state: dict[str, Any], args: argparse.Namespace, state_path: Path | None = None) -> str:
    transition = args.transition
    gates = require_object(state, "gates")
    evidence = require_evidence(args)
    root = project_root_from_state(state_path) if state_path is not None else None

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
        add_history(state, transition, evidence)
        return f"recorded decision {args.decision_id}"

    if transition == "record-mainline":
        if gates.get("business_discovery", "not_started") not in {"not_started", "in_progress", "draft"}:
            raise ValueError("business_discovery must be not_started, in_progress, or draft before record-mainline")
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
        components = parse_components(args.component)
        if components:
            profile_id = (args.profile_id or "project-components").strip()
            profile_version = (args.profile_version or "1").strip()
        else:
            if not (args.profile_id or "").strip() or not (args.profile_version or "").strip():
                raise ValueError("--profile-id and --profile-version are required unless --component is used")
            profile_id = args.profile_id.strip()
            profile_version = args.profile_version.strip()
        state["technology_profile"] = {"id": profile_id, "version": profile_version}
        if components:
            state["technology_profile"]["components"] = components
        gates.update({"technology_profile": "selected", "phase": "delivery"})
    elif transition == "select-database-profile":
        reason = check(state, "database-profile")
        if reason:
            raise ValueError(reason)
        if not (args.database_profile_id or "").strip() or not (args.database_profile_version or "").strip():
            raise ValueError("--database-profile-id and --database-profile-version are required for select-database-profile")
        if isinstance(state.get("database_profile"), dict):
            raise ValueError("database_profile must not already be selected")
        root = project_root_from_state(state_path) if state_path is not None else None
        if root is None:
            raise ValueError("select-database-profile requires a workflow ledger path")
        relative = (args.database_profile_path or f".ddd/performance-profiles/{args.database_profile_id.strip()}.yaml").strip()
        record = database_profile_from_file(root, relative, args.database_profile_id.strip(), args.database_profile_version.strip())
        state["database_profile"] = record
        state.pop("performance_contract", None)
    elif transition == "record-performance":
        reason = check(state, "performance", root)
        if reason:
            raise ValueError(reason)
        if not isinstance(state.get("database_profile"), dict):
            raise ValueError("database_profile must be selected before record-performance")
        if isinstance(state.get("performance_contract"), dict):
            raise ValueError("performance_contract must not already be recorded")
        root = project_root_from_state(state_path) if state_path is not None else None
        if root is None:
            raise ValueError("record-performance requires a workflow ledger path")
        relative = (args.performance_record or f".ddd/performance/{active_slice(state)['id']}.yaml").strip()
        record = performance_contract_from_file(root, relative, state)
        state["performance_contract"] = record
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
        reason = check(state, "review", project_root_from_state(state_path) if state_path is not None else None)
        if reason:
            raise ValueError(reason)
        gates.update({"review": "blocked", "phase": "verification"})
    elif transition == "reset-slice":
        if gates.get("delivery") != "verified":
            raise ValueError("delivery must be verified before reset-slice")
        if gates.get("review", "not_started") != "passed":
            raise ValueError("review must be passed before reset-slice")
        gates.update({"phase": "discovery", "domain_design": "draft", "slice_approval": "pending", "technology_profile": "pending", "delivery": "not_started", "review": "not_started"})
        for field in ("ui_system", "ui_practices", "ui_design"):
            gates.pop(field, None)
        state["active_slice"] = None
        state.pop("technology_profile", None)
        state.pop("database_profile", None)
        state.pop("performance_contract", None)
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
    parser.add_argument("--requires-database", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--profile-id")
    parser.add_argument("--profile-version")
    parser.add_argument("--component", action="append", help="independent technology component kind:id:version; repeat per kind")
    parser.add_argument("--database-profile-id")
    parser.add_argument("--database-profile-version")
    parser.add_argument("--database-profile-path")
    parser.add_argument("--performance-record")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        state = read_state(args.state)
        if args.require:
            reason = check(state, args.require, project_root_from_state(args.state))
            if reason:
                return fail(reason)
            emit({"allowed": True, "require": args.require})
            return 0
        if args.transition == "record-decision" and not (args.decision_id or "").strip():
            return fail("--decision-id is required for record-decision")
        result = apply_transition(state, args, args.state)
        write_state(args.state, state)
        emit({"allowed": True, "transition": result})
        return 0
    except ValueError as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
