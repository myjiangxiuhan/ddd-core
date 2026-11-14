#!/usr/bin/env python3
"""Validate a declarative slice performance contract without executing commands."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from profile_loader import PROFILE_DIR, ProfileError, load_profile_from_contract


class ContractError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ContractError("PyYAML is required to validate performance contracts") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ContractError(f"performance contract not found: {path}") from exc
    except OSError as exc:
        raise ContractError(f"cannot read performance contract: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ContractError(f"performance contract is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("performance contract root must be an object")
    return value


def non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value <= 0:
        raise ContractError(f"{label} must be positive")
    return float(value)


def non_negative_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
        raise ContractError(f"{label} must be zero or positive")
    return float(value)


def string_list(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(non_empty_string(item, f"{label}[{index}]"))
    if not allow_empty and not result:
        raise ContractError(f"{label} must not be empty")
    return result


def validate(
    path: Path,
    *,
    profiles_dir: Path = PROFILE_DIR,
    profile_override: dict[str, Any] | None = None,
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = document if document is not None else load_yaml(path)
    if value.get("schema_version") != "1":
        raise ContractError('schema_version must be "1"')
    contract_id = non_empty_string(value.get("id"), "id")
    status = non_empty_string(value.get("status"), "status")
    if status not in {"draft", "confirmed"}:
        raise ContractError("status must be draft or confirmed")
    non_empty_string(value.get("slice_id"), "slice_id")
    non_empty_string(value.get("seam"), "seam")

    decisions = value.get("decisions")
    if not isinstance(decisions, list):
        raise ContractError("decisions must be an array")
    decision_ids: set[str] = set()
    has_user_decision = False
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            raise ContractError(f"decisions[{index}] must be an object")
        decision_id = non_empty_string(decision.get("id"), f"decisions[{index}].id")
        if decision_id in decision_ids:
            raise ContractError(f"duplicate decision id: {decision_id}")
        decision_ids.add(decision_id)
        source = non_empty_string(decision.get("source"), f"decisions[{index}].source")
        if source not in {"user_decision", "agent_recommendation", "agent_inference", "pending"}:
            raise ContractError(f"decisions[{index}].source is not a canonical decision source")
        non_empty_string(decision.get("question"), f"decisions[{index}].question")
        if source == "user_decision":
            non_empty_string(decision.get("answer"), f"decisions[{index}].answer")
            non_empty_string(decision.get("evidence"), f"decisions[{index}].evidence")
        else:
            if decision.get("answer") is not None and not isinstance(decision.get("answer"), str):
                raise ContractError(f"decisions[{index}].answer must be a string when present")
            if decision.get("evidence") is not None and not isinstance(decision.get("evidence"), str):
                raise ContractError(f"decisions[{index}].evidence must be a string when present")
        has_user_decision = has_user_decision or source == "user_decision"
    if status == "confirmed" and not has_user_decision:
        raise ContractError("confirmed contract needs at least one evidenced user_decision")

    profile = value.get("profile")
    if not isinstance(profile, dict):
        raise ContractError("profile must be an object")
    non_empty_string(profile.get("id"), "profile.id")
    non_empty_string(profile.get("version"), "profile.version")
    database = profile.get("database")
    if not isinstance(database, dict):
        raise ContractError("profile.database must be an object")
    for field in ("engine", "version", "driver", "query_layer"):
        non_empty_string(database.get(field), f"profile.database.{field}")
    database_profile: dict[str, Any] | None = None
    if database.get("engine") not in {"none", "in-memory"}:
        try:
            if profile_override is not None:
                adapter_profile = non_empty_string(database.get("adapter_profile"), "profile.database.adapter_profile")
                if profile_override.get("id") != adapter_profile:
                    raise ProfileError("database profile id does not match the contract")
                if profile_override.get("engine") != database.get("engine"):
                    raise ProfileError("database profile engine does not match the contract")
                if str(profile_override.get("version")) != str(database.get("version")):
                    raise ProfileError("database profile version does not match the contract")
                database_profile = profile_override
            else:
                database_profile = load_profile_from_contract(database, profiles_dir)
        except ProfileError as exc:
            raise ContractError(str(exc)) from exc

    workload = value.get("workload")
    if not isinstance(workload, dict):
        raise ContractError("workload must be an object")
    dataset = workload.get("dataset")
    if not isinstance(dataset, dict):
        raise ContractError("workload.dataset must be an object")
    rows_value = dataset.get("rows")
    if isinstance(rows_value, bool) or not isinstance(rows_value, int) or rows_value <= 0:
        raise ContractError("workload.dataset.rows must be a positive integer")
    rows = rows_value
    non_empty_string(dataset.get("distribution"), "workload.dataset.distribution")
    if "tenants" in dataset:
        tenants = dataset.get("tenants")
        if isinstance(tenants, bool) or not isinstance(tenants, int) or tenants <= 0:
            raise ContractError("workload.dataset.tenants must be a positive integer when present")
    non_negative_number(workload.get("warmup_seconds"), "workload.warmup_seconds")
    positive_number(workload.get("measurement_seconds"), "workload.measurement_seconds")
    scenarios = workload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ContractError("workload.scenarios must be a non-empty array")
    scenario_ids: set[str] = set()
    scenarios_by_id: dict[str, dict[str, Any]] = {}
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ContractError(f"workload.scenarios[{index}] must be an object")
        scenario_id = non_empty_string(scenario.get("id"), f"workload.scenarios[{index}].id")
        if scenario_id in scenario_ids:
            raise ContractError(f"duplicate scenario id: {scenario_id}")
        scenario_ids.add(scenario_id)
        scenarios_by_id[scenario_id] = scenario
        positive_number(scenario.get("concurrency"), f"scenario {scenario_id}.concurrency")
        budget = scenario.get("budget")
        if not isinstance(budget, dict):
            raise ContractError(f"scenario {scenario_id}.budget must be an object")
        for field in ("p95_ms", "p99_ms"):
            positive_number(budget.get(field), f"scenario {scenario_id}.budget.{field}")
        non_negative_number(budget.get("error_rate_percent"), f"scenario {scenario_id}.budget.error_rate_percent")
        if "target_rps" not in scenario and "batch_target" not in scenario:
            raise ContractError(f"scenario {scenario_id} needs target_rps or batch_target")
        if "target_rps" in scenario:
            positive_number(scenario.get("target_rps"), f"scenario {scenario_id}.target_rps")
        if "batch_target" in scenario:
            positive_number(scenario.get("batch_target"), f"scenario {scenario_id}.batch_target")

    sql_entries = value.get("sql", [])
    if not isinstance(sql_entries, list):
        raise ContractError("sql must be an array")
    sql_ids: set[str] = set()
    for index, query in enumerate(sql_entries):
        if not isinstance(query, dict):
            raise ContractError(f"sql[{index}] must be an object")
        query_id = non_empty_string(query.get("id"), f"sql[{index}].id")
        if query_id in sql_ids:
            raise ContractError(f"duplicate SQL id: {query_id}")
        sql_ids.add(query_id)
        scenario_id = non_empty_string(query.get("scenario_id"), f"sql[{index}].scenario_id")
        if scenario_id not in scenarios_by_id:
            raise ContractError(f"sql {query_id} references unknown scenario: {scenario_id}")
        operation = non_empty_string(query.get("operation"), f"sql {query_id}.operation")
        if operation not in {"list", "upsert"}:
            raise ContractError(f"sql {query_id}.operation must be list or upsert")
        for field in ("filters", "joins", "order", "selected_columns"):
            if not isinstance(query.get(field), list):
                raise ContractError(f"sql {query_id}.{field} must be an array")
        if not query["selected_columns"]:
            raise ContractError(f"sql {query_id}.selected_columns must not be empty")
        non_empty_string(query.get("index"), f"sql {query_id}.index")
        non_empty_string(query.get("pagination"), f"sql {query_id}.pagination")
        non_empty_string(query.get("access_path"), f"sql {query_id}.access_path")
        non_empty_string(query.get("transaction"), f"sql {query_id}.transaction")
        non_empty_string(query.get("lock_scope"), f"sql {query_id}.lock_scope")
        positive_number(query.get("timeout_ms"), f"sql {query_id}.timeout_ms")
        non_empty_string(query.get("plan_evidence"), f"sql {query_id}.plan_evidence")
        if Path(query["plan_evidence"]).is_absolute():
            raise ContractError(f"sql {query_id}.plan_evidence must be project-relative")
        if query.get("n_plus_one") is not False:
            raise ContractError(f"sql {query_id}.n_plus_one must be false")
        mapping = query.get("database_mapping")
        if not isinstance(mapping, dict):
            raise ContractError(f"sql {query_id}.database_mapping must be an object")
        if database_profile is not None:
            mapping_profile = non_empty_string(
                mapping.get("profile"),
                f"sql {query_id}.database_mapping.profile",
            )
            if mapping_profile != database_profile["id"]:
                raise ContractError(f"sql {query_id}.database_mapping.profile does not match the selected database profile")
            mapping_capabilities = string_list(
                mapping.get("capabilities"),
                f"sql {query_id}.database_mapping.capabilities",
            )
            for capability_name in mapping_capabilities:
                capability = database_profile["capabilities"].get(capability_name)
                if not isinstance(capability, dict):
                    raise ContractError(
                        f"sql {query_id}.database_mapping.capabilities references unknown capability: {capability_name}"
                    )
                if capability.get("supported") is not True:
                    raise ContractError(
                        f"sql {query_id}.database_mapping.capabilities references unsupported capability: {capability_name}"
                    )
            generation = database_profile["sql_generation"].get(operation, {})
            expected_pagination = generation.get("pagination")
            if operation == "list" and expected_pagination and query.get("pagination") != expected_pagination:
                raise ContractError(
                    f"sql {query_id}.pagination must follow database profile {database_profile['id']}: {expected_pagination}"
                )
        native_features = string_list(mapping.get("native_features"), f"sql {query_id}.database_mapping.native_features")
        string_list(
            mapping.get("fallback_or_incompatibility"),
            f"sql {query_id}.database_mapping.fallback_or_incompatibility",
        )
        if "evidence" in mapping:
            string_list(mapping.get("evidence"), f"sql {query_id}.database_mapping.evidence")
        if status == "confirmed":
            if database.get("engine") not in {"none", "in-memory"} and not native_features:
                raise ContractError(f"sql {query_id}.database_mapping.native_features must not be empty")
            string_list(
                mapping.get("evidence"),
                f"sql {query_id}.database_mapping.evidence",
                allow_empty=False,
            )
        if rows >= 10000 and query.get("pagination") == "offset":
            offset_rule = database_profile["rules"]["large_dataset_offset"] if database_profile else "require_rationale"
            if offset_rule == "reject":
                raise ContractError(f"sql {query_id} uses offset pagination rejected by the selected database profile")
            if offset_rule == "require_rationale" and not query.get("pagination_rationale"):
                raise ContractError(f"sql {query_id} needs a rationale for offset pagination at this dataset size")

    if status == "confirmed" and not sql_entries and database.get("engine") not in {"none", "in-memory"}:
        raise ContractError("confirmed database-backed contract needs at least one SQL entry")
    baseline = value.get("baseline")
    if baseline is not None:
        if not isinstance(baseline, dict):
            raise ContractError("baseline must be an object when present")
        baseline_status = non_empty_string(baseline.get("status"), "baseline.status")
        if baseline_status not in {"pending", "inconclusive", "passed", "failed"}:
            raise ContractError("baseline.status is invalid")
        if baseline.get("result") is not None:
            non_empty_string(baseline.get("result"), "baseline.result")
            if Path(str(baseline["result"])).is_absolute():
                raise ContractError("baseline.result must be project-relative")
    return {
        "ok": True,
        "id": contract_id,
        "status": status,
        "slice_id": value["slice_id"],
        "scenarios": len(scenarios),
        "sql_entries": len(sql_entries),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--profiles-dir", type=Path, default=PROFILE_DIR)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.contract, profiles_dir=args.profiles_dir), ensure_ascii=False, indent=2))
        return 0
    except ContractError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
