#!/usr/bin/env python3
"""Inspect and render a safe, declarative scaffold configuration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

APPROVAL_SCRIPTS = Path(__file__).resolve().parents[2] / "ddd-core" / "scripts"
if str(APPROVAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(APPROVAL_SCRIPTS))
from approval import ApprovalError, consume_approval, digest_file, digest_json, domain_design_digest, verify_credential  # type: ignore  # noqa: E402


PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")
VALID_AXES = {"standards", "spec", "ddd", "ui", "custom"}
TEMPLATE_SOURCE_KINDS = {"oss", "local", "design-reference", "user"}


class ConfigError(ValueError):
    pass


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(message: str) -> int:
    emit({"ok": False, "error": message})
    return 1


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ConfigError("PyYAML is required to read scaffold configuration") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration not found: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read configuration: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"configuration is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError("configuration root must be an object")
    if value.get("schema_version") != "1":
        raise ConfigError('schema_version must be "1"')
    if not isinstance(value.get("profiles"), dict) or not value["profiles"]:
        raise ConfigError("profiles must be a non-empty object")
    return value


def load_yaml_record(path: Path, label: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ConfigError("PyYAML is required to read scaffold records") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ConfigError(f"{label} not found: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read {label}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{label} is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{label} root must be an object")
    return value


def load_json_record(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ConfigError(f"{label} not found: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read {label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{label} is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{label} root must be an object")
    return value


def choose_profile(config: dict[str, Any], profile_id: str | None) -> tuple[str, dict[str, Any]]:
    selected = profile_id or config.get("default_profile")
    if not isinstance(selected, str) or not selected.strip():
        raise ConfigError("profile is required when default_profile is absent")
    profile = config["profiles"].get(selected)
    if not isinstance(profile, dict):
        raise ConfigError(f"profile not found: {selected}")
    if not isinstance(profile.get("version"), str) or not profile["version"].strip():
        raise ConfigError(f"profile {selected} must declare a version")
    if not isinstance(profile.get("generators"), dict) or not profile["generators"]:
        raise ConfigError(f"profile {selected} must declare generators")
    return selected, profile


def project_root(config_path: Path, explicit_root: str | None) -> Path:
    if explicit_root:
        root = Path(explicit_root).resolve()
    elif config_path.parent.name == ".ddd":
        root = config_path.parent.parent.resolve()
    else:
        root = Path.cwd().resolve()
    if not root.exists() or not root.is_dir():
        raise ConfigError(f"project root is not a directory: {root}")
    return root


def managed_project_config(config_path: Path, root: Path) -> bool:
    ddd = root / ".ddd"
    managed = (
        config_path.resolve() == (ddd / "scaffold.yaml").resolve()
        or (ddd / "workflow-state.json").exists()
        or (ddd / "ui-system.yaml").exists()
        or (ddd / "ui-practices.yaml").exists()
    )
    if managed and config_path.resolve() != (ddd / "scaffold.yaml").resolve():
        raise ConfigError("managed projects must use the project-owned .ddd/scaffold.yaml")
    return managed


def resolve_generator(
    profile: dict[str, Any],
    kind: str,
    generator_id: str,
    root: Path | None = None,
    profile_id: str | None = None,
    trusted_public_key: str | None = None,
) -> dict[str, Any]:
    generators = profile["generators"].get(kind)
    if not isinstance(generators, dict):
        raise ConfigError(f"generator kind not found: {kind}")
    generator = generators.get(generator_id)
    if not isinstance(generator, dict):
        raise ConfigError(f"generator not found: {kind}:{generator_id}")
    validate_generator_surface(generator, kind, generator_id)
    if kind == "template":
        validate_template(generator, generator_id)
        if root is not None:
            if not isinstance(profile_id, str) or not profile_id.strip():
                raise ConfigError("profile id is required to validate a project template registration")
            validate_project_gate(root, profile_id, str(profile.get("version")), True, trusted_public_key, requires_ui=True)
            validate_template_registration(
                generator,
                generator_id,
                root,
                profile_id,
                str(profile.get("version")),
                trusted_public_key,
            )
    files = generator.get("files")
    if not isinstance(files, list) or not files:
        raise ConfigError(f"generator {kind}:{generator_id} must declare files")
    for index, item in enumerate(files):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"].strip():
            raise ConfigError(f"generator {kind}:{generator_id} file {index} needs a path")
        has_template = isinstance(item.get("template"), str)
        has_template_file = isinstance(item.get("template_file"), str)
        if has_template == has_template_file:
            raise ConfigError(f"generator {kind}:{generator_id} file {index} needs exactly one template source")
    return generator


def validate_generator_surface(generator: dict[str, Any], kind: str, generator_id: str) -> None:
    surface = generator.get("surface", "backend" if kind in {"backend", "service", "repository"} else "ui")
    if surface not in {"ui", "backend"}:
        raise ConfigError(f"generator {kind}:{generator_id} surface must be ui or backend")
    requires_ui = generator.get("requires_ui", surface == "ui")
    if not isinstance(requires_ui, bool):
        raise ConfigError(f"generator {kind}:{generator_id} requires_ui must be boolean")
    if surface == "backend" and requires_ui:
        raise ConfigError(f"backend generator {kind}:{generator_id} cannot require UI records")
    requires_database = generator.get("requires_database", False)
    if not isinstance(requires_database, bool):
        raise ConfigError(f"generator {kind}:{generator_id} requires_database must be boolean")


def required_gate_fields(requires_ui: bool) -> dict[str, str]:
    fields = {
        "business_discovery": "confirmed",
        "domain_design": "confirmed",
        "slice_approval": "approved",
        "technology_profile": "selected",
        "delivery": "not_started",
    }
    if requires_ui:
        fields.update({
            "ui_system": "confirmed",
            "ui_practices": "confirmed",
            "ui_design": "confirmed",
        })
    return fields


def require_backend_database_gate(gates: dict[str, Any], state: dict[str, Any]) -> None:
    if gates.get("database_profile") != "selected":
        raise ConfigError("database_profile must be selected before a database backend scaffold")
    database_record = state.get("database_profile")
    if not isinstance(database_record, dict) or not database_record.get("id") or not database_record.get("digest"):
        raise ConfigError("database_profile must contain the signed id and digest before backend scaffold")


def template_sources(template: dict[str, Any]) -> list[Any]:
    sources = template.get("sources")
    if sources is None:
        source = template.get("source")
        return [source] if source is not None else []
    return sources if isinstance(sources, list) else []


def validate_template(template: dict[str, Any], template_id: str) -> None:
    if template.get("status") != "confirmed":
        raise ConfigError(f"template {template_id} must have status: confirmed")
    if not isinstance(template.get("version"), str) or not template["version"].strip():
        raise ConfigError(f"template {template_id} must declare a version")
    sources = template.get("sources")
    if sources is None:
        source = template.get("source")
        sources = [source] if source is not None else []
    if not isinstance(sources, list) or not sources:
        raise ConfigError(f"template {template_id} must declare source or sources provenance")
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ConfigError(f"template {template_id} sources[{index}] must be an object")
        source_kind = source.get("kind")
        if source_kind not in TEMPLATE_SOURCE_KINDS:
            raise ConfigError(f"template {template_id} sources[{index}].kind must be one of {sorted(TEMPLATE_SOURCE_KINDS)}")
        for field in ("locator", "ref", "license", "attribution", "evidence"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ConfigError(f"template {template_id} sources[{index}].{field} is required")
        extraction = source.get("extraction", "pattern_only")
        if extraction not in {"pattern_only", "licensed_copy"}:
            raise ConfigError(f"template {template_id} sources[{index}].extraction must be pattern_only or licensed_copy")
    mapping = template.get("mapping")
    if not isinstance(mapping, dict):
        raise ConfigError(f"template {template_id} must declare mapping")
    for field in ("ui_system", "ui_practices"):
        if not isinstance(mapping.get(field), str) or not mapping[field].strip():
            raise ConfigError(f"template {template_id} mapping.{field} is required")
    for field in ("theme_roles", "layout_regions", "primitives"):
        if not isinstance(mapping.get(field), list) or not mapping[field]:
            raise ConfigError(f"template {template_id} mapping.{field} is required")
    adaptation = mapping.get("adaptation")
    if not isinstance(adaptation, dict):
        raise ConfigError(f"template {template_id} mapping.adaptation is required")
    for field in ("source_framework", "source_library", "target_framework", "target_library"):
        if not isinstance(adaptation.get(field), str) or not adaptation[field].strip():
            raise ConfigError(f"template {template_id} mapping.adaptation.{field} is required")
    if not isinstance(adaptation.get("primitive_map"), list) or not adaptation["primitive_map"]:
        raise ConfigError(f"template {template_id} mapping.adaptation.primitive_map is required")
    if not isinstance(adaptation.get("target_invariants"), list) or not adaptation["target_invariants"]:
        raise ConfigError(f"template {template_id} mapping.adaptation.target_invariants is required")
    slots = template.get("slots", [])
    public_seams = template.get("public_seams", [])
    if not isinstance(slots, list) or not isinstance(public_seams, list) or not (slots or public_seams):
        raise ConfigError(f"template {template_id} needs slots or public_seams")
    if not isinstance(template.get("variables"), list) or not template["variables"]:
        raise ConfigError(f"template {template_id} must declare variables")
    if not isinstance(template.get("review_checks"), list) or not template["review_checks"]:
        raise ConfigError(f"template {template_id} must declare review_checks")
    if template.get("status") == "confirmed":
        source_evidence_digests = template.get("source_evidence_digests")
        if not isinstance(source_evidence_digests, dict) or not source_evidence_digests:
            raise ConfigError(f"template {template_id} must declare source_evidence_digests")
        confirmation = template.get("confirmation")
        if not isinstance(confirmation, dict):
            raise ConfigError(f"template {template_id} needs a confirmation record")
        if confirmation.get("status") != "confirmed":
            raise ConfigError(f"template {template_id} confirmation must have status: confirmed")
        if confirmation.get("source") != "user_decision":
            raise ConfigError(f"template {template_id} confirmation.source must be user_decision")
        if not isinstance(confirmation.get("evidence"), str) or not confirmation["evidence"].strip():
            raise ConfigError(f"template {template_id} confirmation.evidence is required")


def validate_template_registration(
    template: dict[str, Any],
    template_id: str,
    root: Path,
    profile_id: str,
    profile_version: str,
    trusted_public_key: str | None = None,
) -> None:
    record_ref = template.get("record")
    if not isinstance(record_ref, str) or not record_ref.strip():
        raise ConfigError(f"template {template_id} must declare record")
    record_path = safe_relative(root, record_ref)
    record = load_yaml_record(record_path, f"template record {template_id}")
    validate_template(record, template_id)
    if record.get("schema_version") != "1":
        raise ConfigError(f"template record {template_id} schema_version must be \"1\"")
    if record.get("id") != template_id:
        raise ConfigError(f"template record id does not match registered id: {record.get('id')!r}")
    if record.get("version") != template.get("version"):
        raise ConfigError(f"template {template_id} record version does not match scaffold registration")
    if record.get("profile") != profile_id or record.get("profile_version") != profile_version:
        raise ConfigError(f"template {template_id} record profile does not match scaffold profile")
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        raise ConfigError(f"template record {template_id} mapping is required")
    for field in ("ui_system", "ui_practices"):
        expected_path = (root / ".ddd" / f"{field.replace('_', '-')}.yaml").resolve()
        mapped_path = safe_relative(root, mapping.get(field, ""))
        if mapped_path != expected_path:
            raise ConfigError(f"template {template_id} mapping.{field} must point to .ddd/{field.replace('_', '-')}.yaml")
    expected_file_digests = template_file_digests(record, root)
    declared_file_digests = record.get("file_digests")
    if expected_file_digests != declared_file_digests:
        raise ConfigError(f"template {template_id} file_digests do not match its template files")
    expected_source_evidence_digests: dict[str, str] = {}
    for source in template_sources(record):
        if isinstance(source, dict) and isinstance(source.get("evidence"), str):
            evidence = source["evidence"]
            evidence_path = safe_relative(root, evidence)
            if not evidence_path.is_file():
                raise ConfigError(f"template {template_id} source evidence not found: {evidence}")
            expected_source_evidence_digests[evidence] = digest_file(evidence_path)
    expected_source_evidence_digests = dict(sorted(expected_source_evidence_digests.items()))
    if expected_source_evidence_digests != record.get("source_evidence_digests"):
        raise ConfigError(f"template {template_id} source_evidence_digests do not match its evidence files")
    confirmation_evidence = record["confirmation"].get("evidence")
    confirmation_path = safe_relative(root, confirmation_evidence)
    if not confirmation_path.exists():
        raise ConfigError(f"template {template_id} confirmation evidence not found: {confirmation_evidence}")
    state_path = root / ".ddd" / "workflow-state.json"
    if not state_path.is_file():
        raise ConfigError(f"template {template_id} needs a workflow ledger for signed confirmation")
    try:
        verify_credential(
            state_path,
            confirmation_path,
            trusted_public_key,
            expected_action="template:confirm",
            expected_arguments={"template_id": template_id, "record": record_ref},
            expected_records=[record_ref],
            # Template confirmation is a separate artifact approval.  Its
            # signed record digest is the binding; the workflow ledger may
            # legitimately advance after the template was confirmed.
            check_state=False,
        )
    except ApprovalError as exc:
        raise ConfigError(f"template {template_id} confirmation credential is invalid: {exc}") from exc
    ui_plan_path = root / ".ddd" / "ui-plan.yaml"
    if ui_plan_path.exists():
        ui_plan = load_yaml_record(ui_plan_path, "ui-plan.yaml")
        if ui_plan.get("template") != record_ref:
            raise ConfigError(f"template {template_id} record is not the template approved by ui-plan.yaml")
    comparable_fields = (
        "description",
        "required_components",
        "mapping",
        "slots",
        "public_seams",
        "variables",
        "review_checks",
        "files",
        "file_digests",
        "source_evidence_digests",
        "confirmation",
    )
    for field in comparable_fields:
        if record.get(field, [] if field in {"required_components", "slots", "public_seams", "variables", "review_checks", "files"} else None) != template.get(field, [] if field in {"required_components", "slots", "public_seams", "variables", "review_checks", "files"} else None):
            raise ConfigError(f"template {template_id} registration drift in {field}")
    if template_sources(record) != template_sources(template):
        raise ConfigError(f"template {template_id} registration drift in sources")
    for source in template_sources(record):
        if isinstance(source, dict) and isinstance(source.get("evidence"), str):
            safe_relative(root, source["evidence"])
    for item in record.get("files", []):
        if isinstance(item, dict) and isinstance(item.get("template_file"), str):
            template_text(item, root)


def words(raw: str) -> list[str]:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw)
    return [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]


def names(raw: str) -> dict[str, str]:
    parts = words(raw)
    if not parts:
        raise ConfigError("name must contain letters or digits")
    pascal = "".join(part[:1].upper() + part[1:] for part in parts)
    camel = pascal[:1].lower() + pascal[1:]
    kebab = "-".join(part.lower() for part in parts)
    return {"name": raw, "pascal_name": pascal, "camel_name": camel, "kebab_name": kebab}


def render(value: str, context: dict[str, str]) -> str:
    unknown = sorted({match.group(1) for match in PLACEHOLDER_RE.finditer(value) if match.group(1) not in context})
    if unknown:
        raise ConfigError(f"unknown template placeholders: {', '.join(unknown)}")
    return PLACEHOLDER_RE.sub(lambda match: context[match.group(1)], value)


def safe_relative(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ConfigError(f"output path must be relative: {relative}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ConfigError(f"output path escapes project root: {relative}") from exc
    return resolved


def safe_generated_output(root: Path, path: Path) -> Path:
    """Keep a generator from overwriting the workflow ledger or approvals."""
    ddd = (root / ".ddd").resolve()
    try:
        path.resolve().relative_to(ddd)
    except ValueError:
        return path
    raise ConfigError("scaffold output may not write inside the project .ddd directory")


def template_text(item: dict[str, Any], root: Path) -> str:
    if isinstance(item.get("template"), str):
        return item["template"]
    template_path = (root / item["template_file"]).resolve()
    try:
        template_path.relative_to(root)
    except ValueError as exc:
        raise ConfigError(f"template_file escapes project root: {item['template_file']}") from exc
    try:
        template_path.relative_to((root / ".ddd").resolve())
    except ValueError:
        pass
    else:
        try:
            template_path.relative_to((root / ".ddd" / "templates").resolve())
        except ValueError as exc:
            raise ConfigError("template_file may only read from .ddd/templates inside a managed project") from exc
    try:
        return template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read template_file {template_path}: {exc}") from exc


def template_file_digests(template: dict[str, Any], root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    files = template.get("files", [])
    if not isinstance(files, list):
        raise ConfigError("template files must be an array")
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("template_file"), str):
            continue
        relative = item["template_file"]
        path = safe_relative(root, relative)
        result[relative] = digest_file(path)
    return dict(sorted(result.items()))


def history_records(state: dict[str, Any], transition: str) -> list[str]:
    if transition == "confirm-mainline":
        artifact = state.get("business_artifact")
        return [artifact] if isinstance(artifact, str) and artifact.strip() else []
    if transition == "confirm-ui-system":
        return [".ddd/ui-system.yaml"]
    if transition == "confirm-ui-practices":
        return [".ddd/ui-practices.yaml"]
    if transition == "confirm-ui":
        return [".ddd/ui-plan.yaml"]
    return []


def validate_signed_history_result(state: dict[str, Any], item: dict[str, Any], payload: dict[str, Any]) -> None:
    transition = item.get("transition")
    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        raise ConfigError(f"history approval for {transition} has no signed arguments")
    if arguments.get("transition") != transition:
        raise ConfigError(f"history approval action arguments do not match {transition}")
    if arguments.get("evidence") != item.get("evidence"):
        raise ConfigError(f"history approval evidence does not match {transition}")
    if transition == "record-decision":
        decision_id = arguments.get("decision_id")
        decision = next((entry for entry in state.get("decisions", []) if isinstance(entry, dict) and entry.get("id") == decision_id), None)
        if decision is None or decision.get("status") != "answered" or decision.get("source") != "user_decision":
            raise ConfigError("signed record-decision no longer matches an answered user decision")
        if (
            decision.get("answer") != arguments.get("answer")
            or decision.get("evidence") != item.get("evidence")
            or arguments.get("decision_digest") != digest_json(decision)
        ):
            raise ConfigError("signed record-decision no longer matches the decision record")
    elif transition == "confirm-mainline":
        if state.get("business_artifact") != arguments.get("artifact"):
            raise ConfigError("signed confirm-mainline no longer matches business_artifact")
    elif transition == "confirm-design":
        if arguments.get("domain_design_digest") != domain_design_digest(state):
            raise ConfigError("signed confirm-design no longer matches the domain design snapshot")
    elif transition == "approve-slice":
        current = state.get("active_slice")
        if (
            not isinstance(current, dict)
            or current.get("id") != arguments.get("slice_id")
            or current.get("name") != arguments.get("slice_name")
            or arguments.get("slice_digest") != digest_json(current)
        ):
            raise ConfigError("signed approve-slice no longer matches active_slice")
    elif transition == "select-profile":
        current = state.get("technology_profile")
        if (
            not isinstance(current, dict)
            or current.get("id") != arguments.get("profile_id")
            or str(current.get("version")) != str(arguments.get("profile_version"))
            or arguments.get("profile_digest") != digest_json(current)
        ):
            raise ConfigError("signed select-profile no longer matches technology_profile")


def validate_project_gate(
    root: Path,
    profile_id: str,
    profile_version: str,
    managed_project: bool,
    trusted_public_key: str | None = None,
    *,
    requires_ui: bool = True,
    requires_database: bool = False,
) -> None:
    if not managed_project:
        return
    if not (trusted_public_key or "").strip():
        raise ConfigError("managed scaffold checks require an explicit --trusted-public-key assertion")
    ddd = root / ".ddd"
    if not ddd.is_dir():
        raise ConfigError(f"managed project root has no .ddd directory: {root}")
    state = load_json_record(ddd / "workflow-state.json", "workflow ledger")
    if state.get("schema_version") != "1":
        raise ConfigError('workflow ledger schema_version must be "1"')
    if state.get("control_mode") != "human_led":
        raise ConfigError("workflow ledger control_mode must be human_led")
    gates = state.get("gates")
    if not isinstance(gates, dict):
        raise ConfigError("workflow ledger gates must be an object")
    required_gates = required_gate_fields(requires_ui)
    for field, expected in required_gates.items():
        if gates.get(field) != expected:
            raise ConfigError(f"workflow gate {field} must be {expected}")
    if gates.get("phase") != "delivery":
        raise ConfigError("workflow gate phase must be delivery")
    if not requires_ui and gates.get("ui_design", "not_started") == "draft":
        raise ConfigError("a draft ui_design must be confirmed or removed before backend scaffold")
    if requires_database:
        require_backend_database_gate(gates, state)
    decisions = state.get("decisions")
    if not isinstance(decisions, list) or not any(
        isinstance(item, dict)
        and item.get("status") == "answered"
        and item.get("source") == "user_decision"
        and isinstance(item.get("evidence"), str)
        and item["evidence"].strip()
        for item in decisions
    ):
        raise ConfigError("domain design needs an answered user_decision before scaffold")
    active_slice = state.get("active_slice")
    if not isinstance(active_slice, dict) or not isinstance(active_slice.get("id"), str) or not active_slice["id"].strip():
        raise ConfigError("workflow ledger active_slice must contain an id")
    technology = state.get("technology_profile")
    if not isinstance(technology, dict) or technology.get("id") != profile_id or str(technology.get("version")) != profile_version:
        raise ConfigError("workflow ledger technology_profile does not match scaffold profile")
    history = state.get("history")
    if not isinstance(history, list):
        raise ConfigError("workflow ledger history must be an array")
    required_user_transitions = {
        "confirm-mainline",
        "confirm-design",
        "approve-slice",
        "select-profile",
    }
    if requires_ui:
        required_user_transitions.update({"confirm-ui-system", "confirm-ui-practices", "confirm-ui"})
    observed_user_transitions: set[str] = set()
    seen_request_ids: set[str] = set()
    recorded_decisions: set[str] = set()
    for item in history:
        if not isinstance(item, dict):
            continue
        if item.get("actor") != "user":
            if "approval" in item:
                raise ConfigError(f"agent history entry {item.get('transition')} cannot carry a user approval")
            continue
        transition = item.get("transition")
        if not isinstance(transition, str) or not transition:
            raise ConfigError("user history entry must name a transition")
        observed_user_transitions.add(transition)
        approval = item.get("approval")
        if not isinstance(approval, dict):
            raise ConfigError(f"user history entry {transition} lacks a signed approval")
        request_id = approval.get("request_id")
        credential_ref = approval.get("credential")
        if not isinstance(request_id, str) or not request_id.strip() or not isinstance(credential_ref, str) or not credential_ref.strip():
            raise ConfigError(f"user history entry {transition} has incomplete approval metadata")
        if request_id in seen_request_ids:
            raise ConfigError(f"approval request was replayed in history: {request_id}")
        seen_request_ids.add(request_id)
        credential_path = safe_relative(root, credential_ref)
        try:
            verified = verify_credential(
                ddd / "workflow-state.json",
                credential_path,
                trusted_public_key,
                expected_action=f"workflow:{transition}",
                expected_records=history_records(state, transition),
                check_state=False,
                allow_consumed=True,
            )
        except ApprovalError as exc:
            raise ConfigError(f"user history approval for {transition} is invalid: {exc}") from exc
        if verified["request_id"] != request_id or verified["payload_digest"] != approval.get("payload_digest"):
            raise ConfigError(f"user history approval metadata does not match its credential: {transition}")
        if verified["public_key_fingerprint"] != approval.get("public_key_fingerprint"):
            raise ConfigError(f"user history approval key metadata does not match its credential: {transition}")
        payload = verified["payload"]
        validate_signed_history_result(state, item, payload)
        if transition == "record-decision":
            arguments = payload.get("arguments")
            if isinstance(arguments, dict) and isinstance(arguments.get("decision_id"), str):
                recorded_decisions.add(arguments["decision_id"])
    missing_user_transitions = sorted(required_user_transitions - observed_user_transitions)
    if missing_user_transitions:
        raise ConfigError(f"workflow ledger lacks user confirmations: {', '.join(missing_user_transitions)}")
    required_decisions = {
        item.get("id")
        for item in state.get("decisions", [])
        if isinstance(item, dict)
        and item.get("status") == "answered"
        and item.get("source") == "user_decision"
        and isinstance(item.get("id"), str)
        and item.get("id").strip()
    }
    missing_decisions = sorted(required_decisions - recorded_decisions)
    if missing_decisions:
        raise ConfigError(f"answered decisions lack signed record-decision approvals: {', '.join(missing_decisions)}")
    business_artifact = state.get("business_artifact")
    if not isinstance(business_artifact, str) or not business_artifact.strip() or not safe_relative(root, business_artifact).is_file():
        raise ConfigError("workflow ledger business_artifact must point to an existing file")

    records: dict[str, dict[str, Any]] = {}
    if not requires_ui:
        return
    for filename in ("ui-system.yaml", "ui-practices.yaml", "ui-plan.yaml"):
        record = load_yaml_record(ddd / filename, filename)
        if record.get("schema_version") != "1":
            raise ConfigError(f"{filename} schema_version must be \"1\"")
        if record.get("status") != "confirmed":
            raise ConfigError(f"{filename} must have status: confirmed")
        if record.get("profile") != profile_id or str(record.get("profile_version")) != profile_version:
            raise ConfigError(f"{filename} profile does not match scaffold profile")
        decisions = record.get("decisions")
        if not isinstance(decisions, list) or not any(
            isinstance(item, dict)
            and item.get("source") == "user_decision"
            and isinstance(item.get("evidence"), str)
            and item["evidence"].strip()
            for item in decisions
        ):
            raise ConfigError(f"{filename} needs a user_decision with evidence")
        records[filename] = record
    ui_plan = records["ui-plan.yaml"]
    if ui_plan.get("active_slice") != active_slice["id"]:
        raise ConfigError("ui-plan active_slice does not match workflow active_slice")


def list_generators(profile_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for kind, generators in profile["generators"].items():
        if not isinstance(generators, dict):
            raise ConfigError(f"generators.{kind} must be an object")
        for generator_id, generator in generators.items():
            if not isinstance(generator, dict):
                raise ConfigError(f"generator {kind}:{generator_id} must be an object")
            row = {
                "kind": kind,
                "id": generator_id,
                "description": generator.get("description", ""),
                "public_seam": generator.get("public_seam"),
                "surface": generator.get("surface", "backend" if kind in {"backend", "service", "repository"} else "ui"),
                "requires_ui": generator.get("requires_ui"),
                "requires_database": generator.get("requires_database", False),
            }
            if kind == "template":
                source = generator.get("source") or {}
                sources = generator.get("sources") or []
                row.update({
                    "status": generator.get("status"),
                    "version": generator.get("version"),
                    "source_kind": source.get("kind") if source else None,
                    "source_kinds": [item.get("kind") for item in sources] if sources else [],
                })
            rows.append(row)
    return {"ok": True, "profile": profile_id, "profile_version": profile["version"], "generators": rows}


def validate_generators(
    profile: dict[str, Any],
    profile_id: str,
    root: Path | None = None,
    trusted_public_key: str | None = None,
) -> None:
    for kind, generators in profile["generators"].items():
        if not isinstance(generators, dict):
            raise ConfigError(f"generators.{kind} must be an object")
        for generator_id in generators:
            generator = resolve_generator(
                profile,
                kind,
                generator_id,
                root=root,
                profile_id=profile_id,
                trusted_public_key=trusted_public_key,
            )
            if root is not None:
                for item in generator["files"]:
                    if isinstance(item.get("template_file"), str):
                        template_text(item, root)


def build_plan(args: argparse.Namespace, config_path: Path, profile_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    root = project_root(config_path, args.root)
    generator = resolve_generator(
        profile,
        args.kind,
        args.generator,
        root=root,
        profile_id=profile_id,
        trusted_public_key=args.trusted_public_key,
    )
    if managed_project_config(config_path, root):
        state = load_json_record(root / ".ddd" / "workflow-state.json", "workflow ledger")
        active_slice = state.get("active_slice")
        if not isinstance(active_slice, dict) or not isinstance(active_slice.get("id"), str):
            raise ConfigError("workflow ledger active_slice must contain an id")
        if args.slice_id != active_slice["id"]:
            raise ConfigError(f"--slice-id must equal the approved active slice: {active_slice['id']}")
    context = names(args.name)
    context.update({
        "slice_id": args.slice_id or "",
        "profile_id": profile_id,
        "target": args.target,
    })
    target = safe_relative(root, args.target)
    safe_generated_output(root, target)
    actions = []
    for item in generator["files"]:
        relative_path = render(item["path"], context)
        output = safe_relative(target, relative_path)
        safe_generated_output(root, output)
        content = render(template_text(item, root), context)
        exists = output.exists()
        action = "overwrite" if exists and args.force else "skip" if exists else "create"
        actions.append({
            "path": str(output.relative_to(root)).replace("\\", "/"),
            "action": action,
            "bytes": len(content.encode("utf-8")),
            "content": content,
        })
    contract = {
        "description": generator.get("description", ""),
        "required_components": generator.get("required_components", []),
        "public_seam": render(generator["public_seam"], context) if isinstance(generator.get("public_seam"), str) else generator.get("public_seam"),
        "review_checks": generator.get("review_checks", []),
        "surface": generator.get("surface", "backend" if args.kind in {"backend", "service", "repository"} else "ui"),
        "requires_ui": generator.get("requires_ui"),
        "requires_database": generator.get("requires_database", False),
        "validation_commands": generator.get("validation_commands", {}),
    }
    if args.kind == "template":
        contract.update({
            "source": generator.get("source"),
            "sources": generator.get("sources", []),
            "record": generator.get("record"),
            "confirmation": generator.get("confirmation"),
            "mapping": generator.get("mapping"),
            "slots": generator.get("slots", []),
            "variables": generator.get("variables", []),
            "public_seams": generator.get("public_seams", []),
        })
    plan = {
        "ok": True,
        "profile": profile_id,
        "profile_version": profile["version"],
        "generator": f"{args.kind}:{args.generator}",
        "name": args.name,
        "target": str(target.relative_to(root)).replace("\\", "/") or ".",
        "contract": contract,
        "actions": actions,
        "root": str(root),
    }
    plan["approval"] = {
        "action": "scaffold:apply",
        "arguments": scaffold_approval_arguments(plan, profile_id, profile, args),
    }
    plan["approval"]["arguments"]["plan_digest"] = plan_digest(plan)
    return plan


def plan_digest(plan: dict[str, Any]) -> str:
    value = dict(plan)
    value.pop("root", None)
    value.pop("approval", None)
    return digest_json(value)


def scaffold_approval_arguments(
    plan: dict[str, Any],
    profile_id: str,
    profile: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "profile_id": profile_id,
        "profile_version": str(profile["version"]),
        "generator": plan["generator"],
        "name": args.name,
        "target": args.target,
        "slice_id": args.slice_id or "",
        "force": bool(args.force),
    }


def verify_scaffold_approval(
    args: argparse.Namespace,
    plan: dict[str, Any],
    root: Path,
    config_path: Path,
    trusted_public_key: str | None,
) -> dict[str, Any]:
    approval_path = (args.approval or "").strip()
    if not approval_path:
        raise ConfigError("managed scaffold apply requires a signed scaffold:apply approval")
    if not trusted_public_key:
        raise ConfigError("managed scaffold apply requires --trusted-public-key")
    state_path = root / ".ddd" / "workflow-state.json"
    expected = dict(plan["approval"]["arguments"])
    expected["plan_digest"] = plan_digest(plan)
    try:
        record_ref = config_path.resolve().relative_to(root.resolve()).as_posix()
        return verify_credential(
            state_path,
            safe_relative(root, approval_path),
            trusted_public_key,
            expected_action="scaffold:apply",
            expected_arguments=expected,
            expected_records=[record_ref],
        )
    except (ApprovalError, ValueError) as exc:
        raise ConfigError(f"scaffold apply approval is invalid: {exc}") from exc


def apply_plan(plan: dict[str, Any], root: Path, force: bool) -> dict[str, Any]:
    applied = []
    for action in plan["actions"]:
        # Re-resolve at apply time. A plan may have been displayed for a
        # while; a replaced symlink/reparse point must not redirect the write.
        output = safe_relative(root, action["path"])
        safe_generated_output(root, output)
        if action["action"] == "skip":
            applied.append({"path": action["path"], "action": "skip"})
            continue
        if action["action"] == "overwrite" and not force:
            raise ConfigError(f"refusing to overwrite existing file without --force: {action['path']}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(action["content"], encoding="utf-8")
        applied.append({"path": action["path"], "action": action["action"]})
    result = dict(plan)
    result.pop("root", None)
    result["mode"] = "apply"
    result["actions"] = applied
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".ddd/scaffold.yaml"))
    parser.add_argument("--profile")
    parser.add_argument("--root")
    parser.add_argument("--trusted-public-key")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--config", type=Path, default=argparse.SUPPRESS)
        subparser.add_argument("--profile", default=argparse.SUPPRESS)
        subparser.add_argument("--root", default=argparse.SUPPRESS)
        subparser.add_argument("--trusted-public-key", default=argparse.SUPPRESS)

    list_parser = sub.add_parser("list")
    add_common(list_parser)
    describe = sub.add_parser("describe")
    add_common(describe)
    describe.add_argument("target", help="kind:generator-id")

    generate = sub.add_parser("generate")
    add_common(generate)
    generate.add_argument("kind")
    generate.add_argument("generator")
    generate.add_argument("--name", required=True)
    generate.add_argument("--target", default=".")
    generate.add_argument("--slice-id")
    generate.add_argument("--apply", action="store_true")
    generate.add_argument("--force", action="store_true")
    generate.add_argument("--approval")

    check_parser = sub.add_parser("check")
    add_common(check_parser)
    return parser


def gate_requirements(args: argparse.Namespace, profile: dict[str, Any]) -> tuple[bool, bool]:
    """Return (requires_ui, requires_database) for the requested generator."""
    profile_surface = profile.get("surface", "ui")
    if args.command == "generate":
        generator = resolve_generator(profile, args.kind, args.generator)
        surface = generator.get("surface", "backend" if args.kind in {"backend", "service", "repository"} else "ui")
        if surface != profile_surface:
            raise ConfigError(f"generator surface {surface} does not match profile surface {profile_surface}")
        return bool(generator.get("requires_ui", surface == "ui")), bool(generator.get("requires_database", False))
    if args.command == "describe":
        if ":" not in args.target:
            raise ConfigError("describe target must be kind:generator-id")
        kind, generator_id = args.target.split(":", 1)
        generator = resolve_generator(profile, kind, generator_id)
        surface = generator.get("surface", "backend" if kind in {"backend", "service", "repository"} else "ui")
        if surface != profile_surface:
            raise ConfigError(f"generator surface {surface} does not match profile surface {profile_surface}")
        return bool(generator.get("requires_ui", surface == "ui")), bool(generator.get("requires_database", False))
    surface = profile.get("surface", "ui")
    return surface != "backend", False


def main() -> int:
    args = build_parser().parse_args()
    try:
        config_path = args.config.resolve()
        config = load_yaml(config_path)
        profile_id, profile = choose_profile(config, args.profile)
        root = project_root(config_path, getattr(args, "root", None))
        managed_project = managed_project_config(config_path, root)
        requires_ui, requires_database = gate_requirements(args, profile)
        validate_project_gate(
            root,
            profile_id,
            str(profile["version"]),
            managed_project,
            args.trusted_public_key,
            requires_ui=requires_ui,
            requires_database=requires_database,
        )
        if args.command == "list":
            validate_generators(profile, profile_id, root, args.trusted_public_key)
            emit(list_generators(profile_id, profile))
            return 0
        if args.command == "check":
            validate_generators(profile, profile_id, root, args.trusted_public_key)
            emit(list_generators(profile_id, profile))
            return 0
        if args.command == "describe":
            if ":" not in args.target:
                raise ConfigError("describe target must be kind:generator-id")
            kind, generator_id = args.target.split(":", 1)
            generator = resolve_generator(
                profile,
                kind,
                generator_id,
                root=root,
                profile_id=profile_id,
                trusted_public_key=args.trusted_public_key,
            )
            emit({"ok": True, "profile": profile_id, "profile_version": profile["version"], "generator": f"{kind}:{generator_id}", "definition": generator})
            return 0
        if args.force and not args.apply:
            raise ConfigError("--force requires --apply")
        plan = build_plan(args, config_path, profile_id, profile)
        if not args.apply:
            result = dict(plan)
            result.pop("root", None)
            result["mode"] = "dry-run"
            emit(result)
            return 0
        if managed_project:
            approval = verify_scaffold_approval(args, plan, root, config_path, args.trusted_public_key)
            state_path = root / ".ddd" / "workflow-state.json"
            state_digest = digest_file(state_path)
            consume_approval(
                state_path,
                approval,
                args.trusted_public_key,
                pre_state_digest=state_digest,
                post_state_digest=state_digest,
            )
        emit(apply_plan(plan, Path(plan["root"]), args.force))
        return 0
    except (ConfigError, OSError) as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
