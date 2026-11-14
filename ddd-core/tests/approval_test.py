#!/usr/bin/env python3
"""Regression tests for detached user approvals and scaffold gate validation."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization


REPO = Path(__file__).resolve().parents[2]
TRUST_TEMP_ROOT = Path(r"C:/Users/myjia/.codex/visualizations/2026/11/11/01a1c936-5506-76f0-bcc6-ff91630f78de")
APPROVAL = REPO / "ddd-core" / "scripts" / "approval.py"
WORKFLOW = REPO / "ddd-core" / "scripts" / "workflow_gate.py"
SCAFFOLD = REPO / "scaffold-kit" / "scripts" / "scaffold.py"
TEST_RUNNER = REPO / "ddd-core" / "tests" / "run_script_with_trust.py"
FORMAL_FIXTURE = REPO / "template-kit" / "examples" / "formal-flow-project"
RECEIPT_GENESIS_DIGEST = "0" * 64


def canonical_digest(value: dict[str, object]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fixed_trust_paths(project: Path, trust_home: Path) -> dict[str, Path]:
    token = hashlib.sha256(os.path.normcase(str(project.resolve())).encode("utf-8")).hexdigest()
    directory = trust_home / ".ddd-approval" / "projects" / token
    return {
        "directory": directory,
        "manifest": directory / "trust-manifest.json",
        "public_key": directory / "user-public.pem",
        "receipt_store": directory / "receipts.log",
        "receipt_anchor": directory / "receipts.anchor",
    }


def provision_receipt_chain(paths: dict[str, Path]) -> None:
    paths["receipt_store"].parent.mkdir(parents=True, exist_ok=True)
    paths["receipt_store"].write_text("", encoding="utf-8")
    body = {
        "schema_version": "1",
        "receipt_sequence": 0,
        "receipt_head_digest": RECEIPT_GENESIS_DIGEST,
        "previous_anchor_digest": RECEIPT_GENESIS_DIGEST,
    }
    anchor = {**body, "anchor_digest": canonical_digest(body)}
    paths["receipt_anchor"].write_text(json.dumps(anchor, sort_keys=True) + "\n", encoding="utf-8")


class ApprovalRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.run_root = Path(tempfile.mkdtemp(prefix="ddd-approval-test-", dir=REPO))
        self.project = self.run_root / "project"
        self.project.mkdir()
        (self.project / ".ddd").mkdir()
        self.trust = Path(tempfile.mkdtemp(prefix="ddd-approval-trust-", dir=TRUST_TEMP_ROOT))
        self.trust_paths = fixed_trust_paths(self.project, self.trust)
        self.private_key = self.trust / "private.pem"
        self.public_key = self.trust_paths["public_key"]
        self.receipt_store = self.trust_paths["receipt_store"]
        self.receipt_anchor = self.trust_paths["receipt_anchor"]
        self.trust_manifest = self.trust_paths["manifest"]
        self.state = self.project / ".ddd" / "workflow-state.json"
        (self.project / ".ddd" / "mainline.md").write_text("A narrow mainline.\n", encoding="utf-8")
        self.state.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "control_mode": "human_led",
                    "project": {"goal": "approval regression"},
                    "decisions": [],
                    "gates": {
                        "phase": "business_discovery",
                        "business_discovery": "draft",
                        "domain_design": "draft",
                        "slice_approval": "pending",
                        "technology_profile": "pending",
                        "ui_system": "not_started",
                        "ui_practices": "not_started",
                        "ui_design": "not_started",
                        "delivery": "not_started",
                        "review": "not_started",
                    },
                    "business_artifact": ".ddd/mainline.md",
                    "history": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        generated = self.exec_cmd(
            "python", str(APPROVAL), "keygen", "--private-key", str(self.private_key), "--public-key", str(self.public_key), check=True
        )
        generated_info = json.loads(generated.stdout)
        self.trust_manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "algorithm": "Ed25519",
                    "project_root": str(self.project),
                    "public_key": str(self.public_key),
                    "public_key_fingerprint": generated_info["public_key_fingerprint"],
                    "receipt_store": str(self.receipt_store),
                    "receipt_anchor": str(self.receipt_anchor),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        provision_receipt_chain(self.trust_paths)

    def tearDown(self) -> None:
        shutil.rmtree(self.run_root, ignore_errors=True)
        shutil.rmtree(self.trust, ignore_errors=True)

    def exec_cmd(
        self,
        *command: str,
        check: bool = False,
        manifest: Path | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        # Deliberately point the environment at a different directory.  The
        # production resolver must ignore both variables; the test runner
        # injects the writable trust root directly into the imported module.
        environment["USERPROFILE"] = str(self.run_root / "attacker-profile")
        environment["HOME"] = str(self.run_root / "attacker-home")
        environment.pop("DDD_APPROVAL_TRUST_MANIFEST", None)
        if env_overrides:
            environment.update(env_overrides)
        command_line = command
        if len(command) >= 2 and command[0] == "python" and Path(command[1]).resolve() in {APPROVAL, WORKFLOW, SCAFFOLD}:
            command_line = ("python", str(TEST_RUNNER), command[1], str(self.trust), *command[2:])
        result = subprocess.run(command_line, cwd=REPO, text=True, capture_output=True, env=environment)
        if check and result.returncode:
            self.fail(f"command failed ({result.returncode}): {' '.join(command_line)}\n{result.stdout}\n{result.stderr}")
        return result

    def create_approval(self, evidence: str = "User reviewed the mainline.", ttl: int = 1800) -> Path:
        arguments = {
            "transition": "confirm-mainline",
            "evidence": evidence,
            "artifact": ".ddd/mainline.md",
        }
        request_result = self.exec_cmd(
            "python",
            str(APPROVAL),
            "request",
            "--state",
            str(self.state),
            "--action",
            "workflow:confirm-mainline",
            "--arguments-json",
            json.dumps(arguments, separators=(",", ":")),
            "--record",
            ".ddd/mainline.md",
            "--ttl-seconds",
            str(ttl),
            "--output",
            ".ddd/approvals/requests",
            check=True,
        )
        request_info = json.loads(request_result.stdout)
        request_path = self.project / request_info["path"]
        credential_path = self.project / ".ddd" / "approvals" / "credentials" / "confirm-mainline.json"
        self.exec_cmd(
            "python",
            str(APPROVAL),
            "sign",
            "--request",
            str(request_path),
            "--private-key",
            str(self.private_key),
            "--expected-payload-digest",
            request_info["payload_digest"],
            "--output",
            str(credential_path),
            check=True,
        )
        return credential_path

    def apply_confirmation(self, credential: Path, evidence: str = "User reviewed the mainline.") -> subprocess.CompletedProcess[str]:
        return self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "confirm-mainline",
            "--evidence",
            evidence,
            "--approval",
            str(credential),
            "--trusted-public-key",
            str(self.public_key),
        )

    def test_generated_key_cannot_replace_pinned_trust(self) -> None:
        credential = self.create_approval()
        attacker_private = self.trust / "attacker-private.pem"
        attacker_public = self.trust / "attacker-public.pem"
        self.exec_cmd(
            "python", str(APPROVAL), "keygen", "--private-key", str(attacker_private), "--public-key", str(attacker_public), check=True
        )
        bypass = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "confirm-mainline",
            "--evidence",
            "User reviewed the mainline.",
            "--approval",
            str(credential),
            "--trusted-public-key",
            str(attacker_public),
        )
        self.assertNotEqual(bypass.returncode, 0)
        self.assertIn("does not match the user-managed trust manifest", bypass.stdout)

    def test_environment_cannot_replace_fixed_manifest(self) -> None:
        credential = self.create_approval()
        attacker_manifest = self.trust / "attacker-manifest.json"
        blocked = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "confirm-mainline",
            "--evidence",
            "User reviewed the mainline.",
            "--approval",
            str(credential),
            "--trusted-public-key",
            str(self.public_key),
            env_overrides={"DDD_APPROVAL_TRUST_MANIFEST": str(attacker_manifest)},
        )
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("is forbidden", blocked.stdout)
        trust_path = self.exec_cmd("python", str(APPROVAL), "trust-path", "--state", str(self.state))
        self.assertEqual(trust_path.returncode, 0, trust_path.stdout)
        self.assertEqual(json.loads(trust_path.stdout)["manifest"], str(self.trust_manifest))

    def test_system_user_directory_ignores_home_variables(self) -> None:
        sys.path.insert(0, str(APPROVAL.parent))
        import approval as approval_module  # type: ignore  # noqa: PLC0415

        original_home = os.environ.get("HOME")
        original_profile = os.environ.get("USERPROFILE")
        fake_home = self.run_root / "forged-user-profile"
        try:
            os.environ["HOME"] = str(fake_home)
            os.environ["USERPROFILE"] = str(fake_home)
            resolved = approval_module.system_user_directory()
        finally:
            if original_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = original_home
            if original_profile is None:
                os.environ.pop("USERPROFILE", None)
            else:
                os.environ["USERPROFILE"] = original_profile
        self.assertNotEqual(resolved, fake_home.resolve())
        self.assertTrue(resolved.is_absolute())

    def test_keygen_refuses_to_overwrite_an_existing_key(self) -> None:
        original_private = self.private_key.read_bytes()
        original_public = self.public_key.read_bytes()
        refused = self.exec_cmd(
            "python", str(APPROVAL), "keygen", "--private-key", str(self.private_key), "--public-key", str(self.public_key)
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("refusing to overwrite", refused.stdout)
        self.assertEqual(original_private, self.private_key.read_bytes())
        self.assertEqual(original_public, self.public_key.read_bytes())
        local = self.exec_cmd(
            "python",
            str(APPROVAL),
            "keygen",
            "--private-key",
            str(self.project / "private.pem"),
            "--public-key",
            str(self.project / "public.pem"),
        )
        self.assertNotEqual(local.returncode, 0)
        self.assertIn("outside a project root", local.stdout)

    def test_sign_refuses_a_request_changed_after_review(self) -> None:
        arguments = {
            "transition": "confirm-mainline",
            "evidence": "User reviewed the mainline.",
            "artifact": ".ddd/mainline.md",
        }
        request_result = self.exec_cmd(
            "python",
            str(APPROVAL),
            "request",
            "--state",
            str(self.state),
            "--action",
            "workflow:confirm-mainline",
            "--arguments-json",
            json.dumps(arguments, separators=(",", ":")),
            "--record",
            ".ddd/mainline.md",
            "--output",
            ".ddd/approvals/requests",
            check=True,
        )
        info = json.loads(request_result.stdout)
        request_path = self.project / info["path"]
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["payload"]["arguments"]["evidence"] = "A different request was substituted."
        request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
        credential_path = self.project / ".ddd" / "approvals" / "credentials" / "tampered.json"
        refused = self.exec_cmd(
            "python",
            str(APPROVAL),
            "sign",
            "--request",
            str(request_path),
            "--expected-payload-digest",
            info["payload_digest"],
            "--private-key",
            str(self.private_key),
            "--output",
            str(credential_path),
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("digest does not match the user-reviewed digest", refused.stdout)

    def test_missing_or_tampered_approval_cannot_advance_user_gate(self) -> None:
        before = self.state.read_bytes()
        missing = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "confirm-mainline",
            "--evidence",
            "User reviewed the mainline.",
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("requires --approval", missing.stdout)
        self.assertEqual(before, self.state.read_bytes())

        credential = self.create_approval()
        env_only = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "confirm-mainline",
            "--evidence",
            "User reviewed the mainline.",
            "--approval",
            str(credential),
        )
        self.assertNotEqual(env_only.returncode, 0)
        self.assertIn("explicit --trusted-public-key", env_only.stdout)
        self.state.write_text(self.state.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        changed_state = self.apply_confirmation(credential)
        self.assertNotEqual(changed_state.returncode, 0)
        self.assertIn("different workflow state", changed_state.stdout)

    def test_valid_approval_is_consumed_and_replay_is_rejected(self) -> None:
        before = self.state.read_bytes()
        credential = self.create_approval()
        accepted = self.apply_confirmation(credential)
        self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        entry = state["history"][-1]
        self.assertEqual(entry["actor"], "user")
        self.assertIn("approval", entry)
        self.assertEqual(entry["approval"]["action"], "workflow:confirm-mainline")

        # Roll the project ledger back to the exact pre-transition bytes.  The
        # user-managed receipt chain still rejects the credential, so mutable
        # project history cannot make a signed request reusable.
        self.state.write_bytes(before)
        replay = self.apply_confirmation(credential)
        self.assertNotEqual(replay.returncode, 0)
        self.assertIn("already been consumed", replay.stdout)

    def test_receipt_chain_rejects_rollback_and_tampering(self) -> None:
        before = self.state.read_bytes()
        credential = self.create_approval()
        accepted = self.apply_confirmation(credential)
        self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
        consumed_receipts = self.receipt_store.read_bytes()
        consumed_anchor = self.receipt_anchor.read_bytes()
        self.assertTrue(consumed_receipts)
        self.assertGreater(len(consumed_anchor.splitlines()), 1)

        self.state.write_bytes(before)
        self.receipt_store.write_bytes(b"")
        rolled_back = self.apply_confirmation(credential)
        self.assertNotEqual(rolled_back.returncode, 0)
        self.assertIn("does not match its immutable anchor", rolled_back.stdout)

        self.receipt_store.write_bytes(consumed_receipts)
        self.receipt_anchor.write_bytes(consumed_anchor)
        tampered = json.loads(consumed_receipts.splitlines()[0].decode("utf-8"))
        tampered["request_id"] = "rewritten-request-id"
        self.receipt_store.write_bytes((json.dumps(tampered, sort_keys=True) + "\n").encode("utf-8"))
        tamper_result = self.apply_confirmation(credential)
        self.assertNotEqual(tamper_result.returncode, 0)
        self.assertIn("entry digest is invalid", tamper_result.stdout)

        self.receipt_store.write_bytes(consumed_receipts)
        tampered_anchor = json.loads(consumed_anchor.splitlines()[1].decode("utf-8"))
        tampered_anchor["receipt_head_digest"] = RECEIPT_GENESIS_DIGEST
        self.receipt_anchor.write_bytes(
            consumed_anchor.splitlines()[0] + b"\n" + (json.dumps(tampered_anchor, sort_keys=True) + "\n").encode("utf-8")
        )
        anchor_tamper = self.apply_confirmation(credential)
        self.assertNotEqual(anchor_tamper.returncode, 0)
        self.assertIn("anchor digest is invalid", anchor_tamper.stdout)

    def test_credential_binds_trusted_key_and_record_digest(self) -> None:
        credential = self.create_approval()
        other_private = self.trust / "other-private.pem"
        other_public = self.trust / "other-public.pem"
        self.exec_cmd(
            "python",
            str(APPROVAL),
            "keygen",
            "--private-key",
            str(other_private),
            "--public-key",
            str(other_public),
            check=True,
        )
        wrong_key = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(self.state),
            "--transition",
            "confirm-mainline",
            "--evidence",
            "User reviewed the mainline.",
            "--approval",
            str(credential),
            "--trusted-public-key",
            str(other_public),
        )
        self.assertNotEqual(wrong_key.returncode, 0)
        self.assertIn("does not match the user-managed trust manifest", wrong_key.stdout)

        (self.project / ".ddd" / "mainline.md").write_text("A changed mainline.\n", encoding="utf-8")
        changed_record = self.apply_confirmation(credential)
        self.assertNotEqual(changed_record.returncode, 0)
        self.assertIn("evidence records", changed_record.stdout)

    def test_scaffold_rejects_file_only_actor_user_forgery(self) -> None:
        project = self.run_root / "formal"
        shutil.copytree(FORMAL_FIXTURE, project)
        formal_paths = fixed_trust_paths(project, self.trust)
        trust_key = formal_paths["public_key"]
        trust_key.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / ".ddd" / "approvals" / "example-public-key.pem", trust_key)
        formal_receipts = formal_paths["receipt_store"]
        formal_anchor = formal_paths["receipt_anchor"]
        formal_manifest = formal_paths["manifest"]
        public = serialization.load_pem_public_key(trust_key.read_bytes())
        der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        formal_manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "algorithm": "Ed25519",
                    "project_root": str(project),
                    "public_key": str(trust_key),
                    "public_key_fingerprint": hashlib.sha256(der).hexdigest(),
                    "receipt_store": str(formal_receipts),
                    "receipt_anchor": str(formal_anchor),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        provision_receipt_chain(formal_paths)
        valid = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        apply_missing = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "generate",
            "template",
            "vben-ant-design-pro-admin-shell",
            "--name",
            "AdminShell",
            "--slice-id",
            "admin-shell-template",
            "--target",
            "src/app/shell",
            "--apply",
            manifest=formal_manifest,
        )
        self.assertNotEqual(apply_missing.returncode, 0)
        self.assertIn("requires a signed scaffold:apply approval", apply_missing.stdout)

        template_file = project / ".ddd" / "templates" / "vben-ant-design-pro-admin-shell" / "admin-shell.tsx.template"
        template_original = template_file.read_bytes()
        template_file.write_bytes(template_original + b"\n// tampered after confirmation\n")
        changed_template = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(changed_template.returncode, 0)
        self.assertIn("file_digests", changed_template.stdout)
        template_file.write_bytes(template_original)

        source_evidence = project / ".ddd" / "template-sources" / "vben-admin-v5.7.0.md"
        source_original = source_evidence.read_bytes()
        source_evidence.write_bytes(source_original + b"\nTampered provenance note.\n")
        changed_source = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(changed_source.returncode, 0)
        self.assertIn("source_evidence_digests", changed_source.stdout)
        source_evidence.write_bytes(source_original)

        state_path = project / ".ddd" / "workflow-state.json"
        state_original = state_path.read_bytes()
        state = json.loads(state_original)
        state["gates"]["phase"] = "forged"
        state["decisions"] = []
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        stale_state = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(stale_state.returncode, 0)
        self.assertIn("phase must be delivery", stale_state.stdout)
        state["gates"]["phase"] = "delivery"
        state["gates"]["business_discovery"] = "draft"
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        downgraded_mainline = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(downgraded_mainline.returncode, 0)
        self.assertIn("business_discovery", downgraded_mainline.stdout)
        state = json.loads(state_original)
        state["history"] = [item for item in state["history"] if item.get("transition") != "record-decision"]
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        missing_decision_approval = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(missing_decision_approval.returncode, 0)
        self.assertIn("record-decision", missing_decision_approval.stdout)
        state = json.loads(state_original)
        state["decisions"][0]["question"] = "A question the user never reviewed"
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        changed_decision = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(changed_decision.returncode, 0)
        self.assertIn("domain design snapshot", changed_decision.stdout)
        state_path.write_bytes(state_original)

        state = json.loads(state_original)
        state["scope"]["current_slice_candidate"]["name"] = "Unreviewed scope substitution"
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        changed_scope = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(changed_scope.returncode, 0)
        self.assertIn("domain design snapshot", changed_scope.stdout)
        state_path.write_bytes(state_original)

        clone = self.run_root / "formal-clone"
        shutil.copytree(project, clone)
        clone_paths = fixed_trust_paths(clone, self.trust)
        clone_paths["public_key"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(trust_key, clone_paths["public_key"])
        clone_paths["manifest"].write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "algorithm": "Ed25519",
                    "project_root": str(project),
                    "public_key": str(clone_paths["public_key"]),
                    "public_key_fingerprint": hashlib.sha256(der).hexdigest(),
                    "receipt_store": str(clone_paths["receipt_store"]),
                    "receipt_anchor": str(clone_paths["receipt_anchor"]),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        provision_receipt_chain(clone_paths)
        clone_reuse = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(clone / ".ddd" / "scaffold.yaml"),
            "--root",
            str(clone),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(clone_reuse.returncode, 0)
        self.assertIn("different project root", clone_reuse.stdout)

        mutable_key = project / ".ddd" / "approvals" / "example-public-key.pem"
        mutable_anchor = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(mutable_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(mutable_anchor.returncode, 0)
        self.assertIn("outside the project root", mutable_anchor.stdout)

        state = json.loads(state_path.read_text(encoding="utf-8"))
        first_user = next(item for item in state["history"] if item.get("actor") == "user")
        first_user.pop("approval", None)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        forged = self.exec_cmd(
            "python",
            str(SCAFFOLD),
            "--config",
            str(project / ".ddd" / "scaffold.yaml"),
            "--root",
            str(project),
            "--trusted-public-key",
            str(trust_key),
            "check",
            manifest=formal_manifest,
        )
        self.assertNotEqual(forged.returncode, 0)
        self.assertIn("lacks a signed approval", forged.stdout)
        gate_forged = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(state_path),
            "--require",
            "scaffold",
            "--trusted-public-key",
            str(trust_key),
            manifest=formal_manifest,
        )
        self.assertNotEqual(gate_forged.returncode, 0)
        self.assertIn("lacks a signed approval", gate_forged.stdout)

    def test_workflow_require_rejects_final_gates_without_user_history(self) -> None:
        project = self.run_root / "empty-history"
        shutil.copytree(FORMAL_FIXTURE, project)
        state_path = project / ".ddd" / "workflow-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["history"] = []
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        empty_paths = fixed_trust_paths(project, self.trust)
        trust_key = empty_paths["public_key"]
        trust_key.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / ".ddd" / "approvals" / "example-public-key.pem", trust_key)
        manifest = empty_paths["manifest"]
        public = serialization.load_pem_public_key(trust_key.read_bytes())
        der = public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1",
                    "algorithm": "Ed25519",
                    "project_root": str(project),
                    "public_key": str(trust_key),
                    "public_key_fingerprint": hashlib.sha256(der).hexdigest(),
                    "receipt_store": str(empty_paths["receipt_store"]),
                    "receipt_anchor": str(empty_paths["receipt_anchor"]),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        provision_receipt_chain(empty_paths)
        result = self.exec_cmd(
            "python",
            str(WORKFLOW),
            "--state",
            str(state_path),
            "--require",
            "scaffold",
            "--trusted-public-key",
            str(trust_key),
            manifest=manifest,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lacks user confirmations", result.stdout)


if __name__ == "__main__":
    unittest.main()
