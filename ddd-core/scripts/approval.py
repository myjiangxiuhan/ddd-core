#!/usr/bin/env python3
"""Create and verify detached Ed25519 approval credentials for workflow actions."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


SCHEMA_VERSION = "1"
ALGORITHM = "Ed25519"
TRUST_MANIFEST_ENV = "DDD_APPROVAL_TRUST_MANIFEST"
TRUST_ROOT_NAME = ".ddd-approval"
TRUST_PROJECTS_DIR = "projects"
TRUST_MANIFEST_NAME = "trust-manifest.json"
TRUST_PUBLIC_KEY_NAME = "user-public.pem"
TRUST_RECEIPT_STORE_NAME = "receipts.log"
TRUST_RECEIPT_ANCHOR_NAME = "receipts.anchor"
RECEIPT_GENESIS_DIGEST = "0" * 64


class ApprovalError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def system_user_directory() -> Path:
    """Resolve the current user's profile directory without consulting env vars."""
    if os.name == "nt":
        try:
            import ctypes

            buffer = ctypes.create_unicode_buffer(32768)
            # CSIDL_PROFILE (0x0028) is resolved by the shell from the
            # interactive Windows user token, not from HOME/USERPROFILE.
            result = ctypes.windll.shell32.SHGetFolderPathW(None, 0x0028, None, 0, buffer)
        except (AttributeError, OSError, ValueError, ctypes.ArgumentError) as exc:
            raise ApprovalError("cannot resolve the Windows user directory through the system API") from exc
        if result != 0 or not buffer.value.strip():
            raise ApprovalError("the Windows system API returned no user directory")
        return Path(buffer.value).resolve()
    try:
        import pwd

        return Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    except (ImportError, KeyError, OSError, AttributeError) as exc:
        raise ApprovalError("cannot resolve the system user directory from the OS account source") from exc


def fixed_trust_directory(project_root: Path) -> Path:
    """Return the system-user path reserved for this exact project root."""
    canonical_root = os.path.normcase(str(project_root.resolve()))
    project_token = digest_bytes(canonical_root.encode("utf-8"))
    return system_user_directory() / TRUST_ROOT_NAME / TRUST_PROJECTS_DIR / project_token


def fixed_trust_paths(project_root: Path) -> dict[str, Path]:
    directory = fixed_trust_directory(project_root)
    return {
        "directory": directory,
        "manifest": directory / TRUST_MANIFEST_NAME,
        "public_key": directory / TRUST_PUBLIC_KEY_NAME,
        "receipt_store": directory / TRUST_RECEIPT_STORE_NAME,
        "receipt_anchor": directory / TRUST_RECEIPT_ANCHOR_NAME,
    }


def domain_design_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    """Return the state covered by a domain-design confirmation."""
    return {
        "project": state.get("project"),
        "scope": state.get("scope"),
        "decisions": state.get("decisions"),
        "business_artifact": state.get("business_artifact"),
        "domain_design": state.get("domain_design"),
    }


def domain_design_digest(state: dict[str, Any]) -> str:
    return digest_json(domain_design_snapshot(state))


def digest_file(path: Path) -> str:
    try:
        return digest_bytes(path.read_bytes())
    except FileNotFoundError as exc:
        raise ApprovalError(f"approval evidence not found: {path}") from exc
    except OSError as exc:
        raise ApprovalError(f"cannot read approval evidence {path}: {exc}") from exc


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ApprovalError(f"{label} is required")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise ApprovalError(f"{label} is not a valid UTC timestamp") from exc


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ApprovalError(f"{label} not found: {path}") from exc
    except OSError as exc:
        raise ApprovalError(f"cannot read {label}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ApprovalError(f"{label} is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ApprovalError(f"{label} root must be an object")
    return value


def project_root_from_state(state_path: Path) -> Path:
    resolved = state_path.resolve()
    return resolved.parent.parent if resolved.parent.name == ".ddd" else resolved.parent


def project_root_from_request(request_path: Path) -> Path:
    resolved = request_path.resolve()
    for candidate in (resolved, *resolved.parents):
        if candidate.name == ".ddd":
            return candidate.parent
    return resolved.parent


def project_path(root: Path, raw: str, label: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ApprovalError(f"{label} must be relative to the project root: {raw}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ApprovalError(f"{label} escapes project root: {raw}") from exc
    return resolved


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_private_key(path: Path) -> Ed25519PrivateKey:
    try:
        value = serialization.load_pem_private_key(path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise ApprovalError(f"cannot load Ed25519 private key: {path}") from exc
    if not isinstance(value, Ed25519PrivateKey):
        raise ApprovalError("approval private key must be Ed25519")
    return value


def load_public_key(path: Path) -> Ed25519PublicKey:
    try:
        value = serialization.load_pem_public_key(path.read_bytes())
    except (OSError, ValueError, TypeError) as exc:
        raise ApprovalError(f"cannot load trusted Ed25519 public key: {path}") from exc
    if not isinstance(value, Ed25519PublicKey):
        raise ApprovalError("trusted approval key must be Ed25519")
    return value


def public_key_fingerprint(public_key: Ed25519PublicKey) -> str:
    encoded = public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(encoded).hexdigest()


def outside_project(path: Path, project_root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError:
        return resolved
    raise ApprovalError(f"{label} must be outside the project root")


def trust_manifest(project_root: Path) -> tuple[Path, dict[str, Any]]:
    paths = fixed_trust_paths(project_root)
    raw = os.environ.get(TRUST_MANIFEST_ENV)
    if raw:
        raise ApprovalError(
            f"{TRUST_MANIFEST_ENV} is forbidden; the user trust manifest has a fixed path: {paths['manifest']}"
        )
    manifest_path = paths["manifest"]
    manifest = load_json(manifest_path, "approval trust manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("algorithm") != ALGORITHM:
        raise ApprovalError("approval trust manifest has an invalid schema")
    for field in ("project_root", "public_key", "public_key_fingerprint", "receipt_store", "receipt_anchor"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ApprovalError(f"approval trust manifest {field} is required")
    project_ref = Path(manifest["project_root"])
    if not project_ref.is_absolute():
        raise ApprovalError("approval trust manifest project_root must be absolute")
    if project_ref.resolve() != project_root.resolve():
        raise ApprovalError("approval trust manifest is bound to a different project root")
    public_key_ref = Path(manifest["public_key"])
    public_key_path = public_key_ref if public_key_ref.is_absolute() else manifest_path.parent / public_key_ref
    manifest["_path"] = str(manifest_path)
    manifest["_public_key_path"] = str(outside_project(public_key_path, project_root, "trusted public key"))
    receipt_ref = Path(manifest["receipt_store"])
    receipt_path = receipt_ref if receipt_ref.is_absolute() else manifest_path.parent / receipt_ref
    manifest["_receipt_store_path"] = str(outside_project(receipt_path, project_root, "approval receipt store"))
    anchor_ref = Path(manifest["receipt_anchor"])
    anchor_path = anchor_ref if anchor_ref.is_absolute() else manifest_path.parent / anchor_ref
    manifest["_receipt_anchor_path"] = str(outside_project(anchor_path, project_root, "approval receipt anchor"))
    if Path(manifest["_public_key_path"]).resolve() != paths["public_key"].resolve():
        raise ApprovalError("approval trust manifest public key must use the fixed user trust path")
    if Path(manifest["_receipt_store_path"]).resolve() != paths["receipt_store"].resolve():
        raise ApprovalError("approval receipt store must use the fixed user trust path")
    if Path(manifest["_receipt_anchor_path"]).resolve() != paths["receipt_anchor"].resolve():
        raise ApprovalError("approval receipt anchor must use the fixed user trust path")
    if not receipt_path.is_file():
        raise ApprovalError("user-managed approval receipt store must be provisioned before verification")
    if not anchor_path.is_file():
        raise ApprovalError("user-managed approval receipt anchor must be provisioned before verification")
    return manifest_path, manifest


def trusted_context(
    explicit: str | None,
    project_root: Path,
) -> tuple[Ed25519PublicKey, Path, Path, Path, Path]:
    manifest_path, manifest = trust_manifest(project_root)
    public_key_path = Path(manifest["_public_key_path"])
    if explicit:
        explicit_path = outside_project(Path(explicit), project_root, "trusted public key")
        if explicit_path != public_key_path:
            raise ApprovalError("trusted public key does not match the user-managed trust manifest")
    public_key = load_public_key(public_key_path)
    fingerprint = public_key_fingerprint(public_key)
    if manifest.get("public_key_fingerprint") != fingerprint:
        raise ApprovalError("trust manifest fingerprint does not match its public key")
    return (
        public_key,
        public_key_path,
        Path(manifest["_receipt_store_path"]),
        Path(manifest["_receipt_anchor_path"]),
        manifest_path,
    )


def trusted_public_key(explicit: str | None, project_root: Path | None = None) -> tuple[Ed25519PublicKey, Path]:
    if project_root is None:
        raise ApprovalError("project root is required to resolve the user-managed trust manifest")
    public_key, public_key_path, _, _, _ = trusted_context(explicit, project_root)
    return public_key, public_key_path


def approval_records(root: Path, paths: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in paths:
        path = project_path(root, raw, "approval record")
        result[relative_path(root, path)] = digest_file(path)
    return dict(sorted(result.items()))


def _json_lines(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ApprovalError(f"{label} not found: {path}") from exc
    except OSError as exc:
        raise ApprovalError(f"cannot read {label}: {exc}") from exc
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_lines, start=1):
        if not raw.strip():
            raise ApprovalError(f"{label} contains a blank line at entry {index}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApprovalError(f"{label} entry {index} is not valid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ApprovalError(f"{label} entry {index} must be an object")
        result.append(value)
    return result


def _append_json_line(path: Path, value: dict[str, Any], label: str) -> None:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with path.open("ab") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ApprovalError(f"cannot append {label}: {exc}") from exc


def _entry_digest(value: dict[str, Any], digest_field: str) -> str:
    body = {key: item for key, item in value.items() if key != digest_field}
    return digest_json(body)


def _genesis_anchor() -> dict[str, Any]:
    body = {
        "schema_version": SCHEMA_VERSION,
        "receipt_sequence": 0,
        "receipt_head_digest": RECEIPT_GENESIS_DIGEST,
        "previous_anchor_digest": RECEIPT_GENESIS_DIGEST,
    }
    return {**body, "anchor_digest": _entry_digest(body, "anchor_digest")}


def load_receipts(receipt_path: Path, anchor_path: Path) -> dict[str, Any]:
    """Validate an append-only receipt log against its external anchor.

    The receipt log and anchor are deliberately separate.  A rollback of only
    one file fails closed because the sequence and hash-chain head no longer
    agree.  The user-owned trust directory must still enforce append-only or
    ACL protection against a writer that can rewrite both files.
    """
    receipt_entries = _json_lines(receipt_path, "approval receipt store")
    anchor_entries = _json_lines(anchor_path, "approval receipt anchor")
    if not anchor_entries or anchor_entries[0] != _genesis_anchor():
        raise ApprovalError("approval receipt anchor has an invalid genesis")
    previous_receipt_digest = RECEIPT_GENESIS_DIGEST
    previous_sequence = 0
    receipts: list[dict[str, Any]] = []
    for index, entry in enumerate(receipt_entries, start=1):
        if entry.get("schema_version") != SCHEMA_VERSION or entry.get("sequence") != index:
            raise ApprovalError("approval receipt store sequence is not append-only")
        if entry.get("previous_digest") != previous_receipt_digest:
            raise ApprovalError("approval receipt store hash chain is broken")
        if entry.get("entry_digest") != _entry_digest(entry, "entry_digest"):
            raise ApprovalError("approval receipt store entry digest is invalid")
        receipts.append(entry)
        previous_receipt_digest = entry["entry_digest"]
        previous_sequence = index
    previous_anchor_digest = RECEIPT_GENESIS_DIGEST
    anchor_sequence = 0
    for index, entry in enumerate(anchor_entries):
        expected_sequence = index
        if entry.get("schema_version") != SCHEMA_VERSION or entry.get("receipt_sequence") != expected_sequence:
            raise ApprovalError("approval receipt anchor sequence is not append-only")
        if entry.get("previous_anchor_digest") != previous_anchor_digest:
            raise ApprovalError("approval receipt anchor hash chain is broken")
        if entry.get("anchor_digest") != _entry_digest(entry, "anchor_digest"):
            raise ApprovalError("approval receipt anchor digest is invalid")
        previous_anchor_digest = entry["anchor_digest"]
        anchor_sequence = expected_sequence
    last_anchor = anchor_entries[-1]
    if anchor_sequence != previous_sequence or last_anchor.get("receipt_head_digest") != previous_receipt_digest:
        raise ApprovalError("approval receipt store does not match its immutable anchor")
    return {
        "schema_version": SCHEMA_VERSION,
        "receipts": receipts,
        "sequence": previous_sequence,
        "head_digest": previous_receipt_digest,
        "anchor_digest": previous_anchor_digest,
    }


def receipt_for_request(receipts: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    for item in receipts.get("receipts", []):
        if isinstance(item, dict) and item.get("request_id") == request_id:
            return item
    return None


def receipt_ids(receipts: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in receipts.get("receipts", []):
        if isinstance(item, dict) and isinstance(item.get("request_id"), str):
            result.add(item["request_id"])
    return result


@contextmanager
def receipt_lock(path: Path) -> Iterator[None]:
    """Serialize consumption so two concurrent invocations cannot both spend one request."""
    lock_path = path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    acquired = False
    try:
        for _ in range(500):
            try:
                descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(descriptor)
                acquired = True
                break
            except FileExistsError:
                time.sleep(0.01)
        if not acquired:
            raise ApprovalError("approval receipt store is locked")
        yield
    finally:
        if acquired:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def consume_approval(
    state_path: Path,
    approval: dict[str, Any],
    trusted_key_path: str | None,
    pre_state_digest: str | None = None,
    post_state_digest: str | None = None,
) -> None:
    """Append one verified request and its anchor checkpoint."""
    root = project_root_from_state(state_path)
    _, _, receipt_path, anchor_path, _ = trusted_context(trusted_key_path, root)
    request_id = approval.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ApprovalError("verified approval has no request_id to consume")
    with receipt_lock(receipt_path):
        receipts = load_receipts(receipt_path, anchor_path)
        if request_id in receipt_ids(receipts):
            raise ApprovalError("approval credential has already been consumed")
        payload = approval.get("payload") if isinstance(approval.get("payload"), dict) else {}
        project_id = approval.get("project_id") or payload.get("project_id")
        receipt_body = {
            "schema_version": SCHEMA_VERSION,
            "sequence": receipts["sequence"] + 1,
            "previous_digest": receipts["head_digest"],
            "request_id": request_id,
            "action": payload.get("action"),
            "payload_digest": approval.get("payload_digest"),
            "public_key_fingerprint": approval.get("public_key_fingerprint"),
            "project_id": project_id,
            "pre_state_digest": pre_state_digest or approval.get("state_digest"),
            "post_state_digest": post_state_digest,
            "consumed_at": timestamp(utc_now()),
        }
        receipt_entry = {**receipt_body, "entry_digest": _entry_digest(receipt_body, "entry_digest")}
        _append_json_line(receipt_path, receipt_entry, "approval receipt store")
        anchor_body = {
            "schema_version": SCHEMA_VERSION,
            "receipt_sequence": receipt_entry["sequence"],
            "receipt_head_digest": receipt_entry["entry_digest"],
            "previous_anchor_digest": receipts["anchor_digest"],
        }
        anchor_entry = {**anchor_body, "anchor_digest": _entry_digest(anchor_body, "anchor_digest")}
        _append_json_line(anchor_path, anchor_entry, "approval receipt anchor")


def build_request(
    state_path: Path,
    action: str,
    arguments: dict[str, Any],
    records: list[str],
    ttl_seconds: int,
) -> tuple[Path, dict[str, Any]]:
    root = project_root_from_state(state_path)
    state_path = state_path.resolve()
    state = load_json(state_path, "workflow ledger")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ApprovalError('workflow ledger schema_version must be "1"')
    if not action.strip():
        raise ApprovalError("approval action is required")
    if ttl_seconds <= 0:
        raise ApprovalError("approval TTL must be positive")
    issued = utc_now()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM,
        "request_id": uuid.uuid4().hex,
        "action": action,
        "arguments": arguments,
        "project_id": digest_json(state.get("project", {})),
        "state_file": relative_path(root, state_path),
        "state_digest": digest_file(state_path),
        "record_digests": approval_records(root, records),
        "issued_at": timestamp(issued),
        "expires_at": timestamp(issued + timedelta(seconds=ttl_seconds)),
        "nonce": uuid.uuid4().hex,
    }
    return root, {"schema_version": SCHEMA_VERSION, "payload": payload}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_request(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state).resolve()
    try:
        arguments = json.loads(args.arguments_json)
    except json.JSONDecodeError as exc:
        raise ApprovalError(f"--arguments-json is not valid JSON: {exc.msg}") from exc
    if not isinstance(arguments, dict):
        raise ApprovalError("--arguments-json must be an object")
    root, request = build_request(state_path, args.action, arguments, args.record or [], args.ttl_seconds)
    output_hint = project_path(root, args.output, "approval request output")
    request_id = request["payload"]["request_id"]
    # Requests are addressed by their signed request_id.  Accept either a
    # directory or a .json hint, but always write the canonical filename so
    # the verifier cannot be redirected to an unrelated request file.
    if output_hint.name == f"{request_id}.json":
        output = output_hint
    else:
        output_dir = output_hint if output_hint.suffix.lower() != ".json" else output_hint.parent
        output = output_dir / f"{request_id}.json"
    write_json(output, request)
    return {
        "ok": True,
        "mode": "request",
        "request_id": request["payload"]["request_id"],
        "path": relative_path(root, output),
        "payload_digest": digest_json(request["payload"]),
    }


def sign_request(args: argparse.Namespace) -> dict[str, Any]:
    request_path = Path(args.request).resolve()
    request = load_json(request_path, "approval request")
    payload = request.get("payload")
    if request.get("schema_version") != SCHEMA_VERSION or not isinstance(payload, dict):
        raise ApprovalError("approval request has an invalid schema")
    actual_payload_digest = digest_json(payload)
    if args.expected_payload_digest != actual_payload_digest:
        raise ApprovalError("approval request digest does not match the user-reviewed digest")
    private_path = Path(args.private_key).expanduser().resolve()
    # A signing key is a user-held secret.  Never accept a project-local path,
    # where an agent can create or replace it while preparing the request.
    root = project_root_from_request(request_path)
    if root in private_path.parents or private_path == root:
        raise ApprovalError("approval private key must be outside the project root")
    private_key = load_private_key(private_path)
    signature = private_key.sign(canonical_bytes(payload))
    public_key = private_key.public_key()
    credential = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM,
        "request_id": payload.get("request_id"),
        "payload_digest": actual_payload_digest,
        "signature": base64.b64encode(signature).decode("ascii"),
        "public_key_fingerprint": public_key_fingerprint(public_key),
        "signer": args.signer or "user",
        "signed_at": timestamp(utc_now()),
    }
    output = Path(args.output).expanduser().resolve()
    write_json(output, credential)
    return {
        "ok": True,
        "mode": "sign",
        "request_id": payload.get("request_id"),
        "path": str(output),
        "payload_digest": credential["payload_digest"],
        "public_key_fingerprint": credential["public_key_fingerprint"],
    }


def _load_credential_bundle(root: Path, credential_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    credential_path = credential_path.resolve()
    try:
        credential_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ApprovalError("approval credential must be inside the project root") from exc
    credential = load_json(credential_path, "approval credential")
    request_id = credential.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ApprovalError("approval credential request_id is required")
    request_path = project_path(root, f".ddd/approvals/requests/{request_id}.json", "approval request")
    request = load_json(request_path, "approval request")
    payload = request.get("payload")
    if request.get("schema_version") != SCHEMA_VERSION or not isinstance(payload, dict):
        raise ApprovalError("approval request has an invalid schema")
    if payload.get("request_id") != request_id:
        raise ApprovalError("approval request id mismatch")
    if credential.get("schema_version") != SCHEMA_VERSION or credential.get("algorithm") != ALGORITHM:
        raise ApprovalError("approval credential has an invalid schema")
    if credential.get("payload_digest") != digest_json(payload):
        raise ApprovalError("approval credential does not match the request payload")
    return credential, payload, request_path


def verify_credential(
    state_path: Path,
    credential_path: Path,
    trusted_key_path: str | None,
    expected_action: str | None = None,
    expected_arguments: dict[str, Any] | None = None,
    expected_records: list[str] | None = None,
    used_request_ids: set[str] | None = None,
    check_state: bool = True,
    allow_consumed: bool = False,
    require_consumed: bool = False,
) -> dict[str, Any]:
    state_path = state_path.resolve()
    root = project_root_from_state(state_path)
    credential, payload, request_path = _load_credential_bundle(root, credential_path)
    public_key, public_key_path, receipt_path, anchor_path, manifest_path = trusted_context(trusted_key_path, root)
    try:
        signature = base64.b64decode(credential.get("signature", ""), validate=True)
        public_key.verify(signature, canonical_bytes(payload))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise ApprovalError("approval signature is invalid") from exc
    fingerprint = public_key_fingerprint(public_key)
    if credential.get("public_key_fingerprint") != fingerprint:
        raise ApprovalError("approval credential key fingerprint does not match the trusted key")
    if expected_action is not None and payload.get("action") != expected_action:
        raise ApprovalError(f"approval action must be {expected_action}")
    if expected_arguments is not None and payload.get("arguments") != expected_arguments:
        raise ApprovalError("approval arguments do not match the requested transition")
    if payload.get("state_file") != relative_path(root, state_path):
        raise ApprovalError("approval is bound to a different workflow ledger")
    state = load_json(state_path, "workflow ledger")
    if payload.get("project_id") != digest_json(state.get("project", {})):
        raise ApprovalError("approval is bound to a different project identity")
    receipts = load_receipts(receipt_path, anchor_path)
    receipt = receipt_for_request(receipts, payload.get("request_id"))
    consumed = receipt_ids(receipts)
    if receipt is not None and receipt.get("payload_digest") != digest_json(payload):
        raise ApprovalError("approval receipt does not match the signed request payload")
    if receipt is not None and receipt.get("public_key_fingerprint") != fingerprint:
        raise ApprovalError("approval receipt does not match the trusted key")
    if not allow_consumed and receipt is not None:
        raise ApprovalError("approval credential has already been consumed")
    if require_consumed and receipt is None:
        raise ApprovalError("approval credential was not consumed by a completed workflow transition")
    if used_request_ids and payload.get("request_id") in used_request_ids:
        raise ApprovalError("approval credential has already been consumed")
    if check_state and payload.get("state_digest") != digest_file(state_path):
        raise ApprovalError("approval was created for a different workflow state")
    if expected_records is not None:
        expected = approval_records(root, expected_records)
        actual = payload.get("record_digests")
        if not isinstance(actual, dict) or actual != expected:
            raise ApprovalError("approval evidence records do not match the current files")
    if utc_now() > parse_timestamp(payload.get("expires_at"), "approval expires_at"):
        raise ApprovalError("approval credential has expired")
    return {
        "request_id": payload["request_id"],
        "payload_digest": digest_json(payload),
        "public_key_fingerprint": fingerprint,
        "credential": relative_path(root, Path(credential_path)),
        "request": relative_path(root, request_path),
        "trusted_key": str(public_key_path),
        "trust_manifest": str(manifest_path),
        "receipt_store": str(receipt_path),
        "receipt_anchor": str(anchor_path),
        "consumed": receipt is not None,
        "receipt": receipt,
        "payload": payload,
    }


def verify_command(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.state).resolve()
    try:
        arguments = json.loads(args.arguments_json) if args.arguments_json else None
    except json.JSONDecodeError as exc:
        raise ApprovalError(f"--arguments-json is not valid JSON: {exc.msg}") from exc
    result = verify_credential(
        state_path,
        Path(args.credential),
        args.trusted_public_key,
        expected_action=args.action,
        expected_arguments=arguments,
        expected_records=args.record,
    )
    return {"ok": True, "mode": "verify", **{key: result[key] for key in ("request_id", "payload_digest", "public_key_fingerprint")}}


def trust_path_command(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root_from_state(Path(args.state))
    paths = fixed_trust_paths(root)
    return {
        "ok": True,
        "mode": "trust-path",
        "project_root": str(root),
        "manifest": str(paths["manifest"]),
        "public_key": str(paths["public_key"]),
        "receipt_store": str(paths["receipt_store"]),
        "receipt_anchor": str(paths["receipt_anchor"]),
        "receipt_anchor_genesis": _genesis_anchor(),
    }


def keygen_command(args: argparse.Namespace) -> dict[str, Any]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_path = Path(args.private_key).expanduser().resolve()
    public_path = Path(args.public_key).expanduser().resolve()
    for key_path in (private_path, public_path):
        for ancestor in (key_path, *key_path.parents):
            if (ancestor / ".ddd").is_dir():
                raise ApprovalError("approval keys must be stored outside a project root")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_bytes = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public_bytes = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    created_private = False
    try:
        with private_path.open("xb") as stream:
            stream.write(private_bytes)
        created_private = True
        with public_path.open("xb") as stream:
            stream.write(public_bytes)
    except FileExistsError as exc:
        # Never rotate or replace an existing trust anchor implicitly.  A
        # deliberate key rotation must be performed by the user-managed trust
        # configuration, outside this command.
        try:
            if created_private and private_path.exists():
                private_path.unlink()
        except OSError:
            pass
        raise ApprovalError(f"refusing to overwrite an existing approval key: {exc.filename}") from exc
    return {"ok": True, "mode": "keygen", "private_key": str(private_path), "public_key": str(public_path), "public_key_fingerprint": public_key_fingerprint(public_key)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    keygen = sub.add_parser("keygen")
    keygen.add_argument("--private-key", required=True)
    keygen.add_argument("--public-key", required=True)

    request = sub.add_parser("request")
    request.add_argument("--state", required=True)
    request.add_argument("--action", required=True)
    request.add_argument("--arguments-json", required=True)
    request.add_argument("--record", action="append")
    request.add_argument("--ttl-seconds", type=int, default=1800)
    request.add_argument("--output", required=True)

    sign = sub.add_parser("sign")
    sign.add_argument("--request", required=True)
    sign.add_argument("--private-key", required=True)
    sign.add_argument("--output", required=True)
    sign.add_argument("--expected-payload-digest", required=True)
    sign.add_argument("--signer")

    verify = sub.add_parser("verify")
    verify.add_argument("--state", required=True)
    verify.add_argument("--credential", required=True)
    verify.add_argument("--trusted-public-key")
    verify.add_argument("--action")
    verify.add_argument("--arguments-json")
    verify.add_argument("--record", action="append")

    trust_path = sub.add_parser("trust-path")
    trust_path.add_argument("--state", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "keygen":
            result = keygen_command(args)
        elif args.command == "request":
            result = create_request(args)
        elif args.command == "sign":
            result = sign_request(args)
        elif args.command == "trust-path":
            result = trust_path_command(args)
        else:
            result = verify_command(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ApprovalError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
