#!/usr/bin/env python3
"""Compare a recorded performance baseline with a confirmed contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from performance_gate import PerformanceGateError, project_root_from_state, require_database_profile_gate
from profile_loader import PROFILE_DIR
from validate_contract import ContractError, load_yaml, validate


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read baseline JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ContractError("baseline root must be an object")
    return value


def compare(contract_path: Path, baseline_path: Path, *, profiles_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    summary = validate(contract_path, profiles_dir=profiles_dir)
    contract = load_yaml(contract_path)
    if summary["status"] != "confirmed":
        raise ContractError("performance contract must be confirmed before budget comparison")
    baseline = load_json(baseline_path)
    if baseline.get("schema_version") != "1":
        raise ContractError('baseline schema_version must be "1"')
    if baseline.get("contract_id") != summary["id"]:
        raise ContractError("baseline contract_id does not match the contract")
    if baseline.get("slice_id") != summary["slice_id"]:
        raise ContractError("baseline slice_id does not match the contract")
    profile = baseline.get("profile")
    contract_profile = contract.get("profile", {})
    if not isinstance(profile, dict):
        raise ContractError("baseline.profile must be an object")
    if profile.get("id") != contract_profile.get("id") or profile.get("version") != contract_profile.get("version"):
        raise ContractError("baseline profile does not match the contract")
    expected_database_profile = contract_profile.get("database", {}).get("adapter_profile")
    if baseline.get("database_profile") != expected_database_profile:
        raise ContractError("baseline database_profile does not match the contract")
    for field in ("commit", "dataset_digest"):
        value = baseline.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContractError(f"baseline.{field} must be a non-empty string")
    dataset_rows = baseline.get("dataset_rows")
    expected_rows = contract["workload"]["dataset"]["rows"]
    if isinstance(dataset_rows, bool) or not isinstance(dataset_rows, int) or dataset_rows != expected_rows:
        raise ContractError("baseline.dataset_rows does not match the contract")
    environment = baseline.get("environment")
    if not isinstance(environment, dict) or not environment:
        raise ContractError("baseline.environment must be a non-empty object")
    workload = contract["workload"]
    for field in ("warmup_seconds", "measurement_seconds"):
        actual = baseline.get(field)
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            raise ContractError(f"baseline.{field} must be numeric")
        if actual != workload[field]:
            raise ContractError(f"baseline.{field} does not match the contract")
    results = baseline.get("scenarios")
    if not isinstance(results, dict):
        raise ContractError("baseline.scenarios must be an object keyed by scenario id")

    failures: list[dict[str, Any]] = []
    checked = 0
    for scenario in contract["workload"]["scenarios"]:
        scenario_id = scenario["id"]
        result = results.get(scenario_id)
        if not isinstance(result, dict):
            failures.append({"scenario": scenario_id, "reason": "missing baseline result"})
            continue
        budget = scenario["budget"]
        checked += 1
        concurrency = result.get("concurrency")
        if isinstance(concurrency, bool) or not isinstance(concurrency, (int, float)):
            failures.append({"scenario": scenario_id, "metric": "concurrency", "reason": "missing numeric result"})
        elif concurrency != scenario["concurrency"]:
            failures.append({
                "scenario": scenario_id,
                "metric": "concurrency",
                "actual": concurrency,
                "expected": scenario["concurrency"],
            })
        for metric in ("p95_ms", "p99_ms", "error_rate_percent"):
            actual = result.get(metric)
            limit = budget[metric]
            if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                failures.append({"scenario": scenario_id, "metric": metric, "reason": "missing numeric result"})
            elif actual > limit:
                failures.append({"scenario": scenario_id, "metric": metric, "actual": actual, "limit": limit})
        for metric in ("db_cpu_percent", "db_connections", "lock_wait_ms", "pool_wait_ms", "memory_mb"):
            if metric not in budget:
                continue
            actual = result.get(metric)
            limit = budget[metric]
            if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                failures.append({"scenario": scenario_id, "metric": metric, "reason": "missing numeric result"})
            elif actual > limit:
                failures.append({"scenario": scenario_id, "metric": metric, "actual": actual, "limit": limit})
        if "target_rps" in scenario:
            actual = result.get("throughput_rps")
            target = scenario["target_rps"]
            if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                failures.append({"scenario": scenario_id, "metric": "throughput_rps", "reason": "missing numeric result"})
            elif actual < target:
                failures.append({"scenario": scenario_id, "metric": "throughput_rps", "actual": actual, "target": target})

    return {
        "ok": not failures,
        "contract_id": summary["id"],
        "checked_scenarios": checked,
        "status": "passed" if not failures else "failed",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--state", type=Path, required=True, help="project workflow ledger")
    parser.add_argument("--trusted-public-key", required=True, help="external trusted user public key")
    parser.add_argument("--profiles-dir", type=Path, default=PROFILE_DIR)
    args = parser.parse_args()
    try:
        state, _ = require_database_profile_gate(
            args.state,
            args.trusted_public_key,
            require_performance=True,
        )
        state_record = state.get("performance_contract")
        if not isinstance(state_record, dict):
            raise PerformanceGateError("performance_contract record is missing")
        root = project_root_from_state(args.state)
        if args.contract.resolve() != (root / state_record["path"]).resolve():
            raise PerformanceGateError("baseline contract path does not match the signed performance_contract")
        result = compare(args.contract, args.baseline, profiles_dir=args.profiles_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    except (PerformanceGateError, ContractError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
