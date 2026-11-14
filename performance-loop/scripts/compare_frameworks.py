#!/usr/bin/env python3
"""Compare pinned Rust database-framework results without inventing a winner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ADAPTER_SCRIPTS = Path(__file__).resolve().parents[2] / "adapter-kit" / "scripts"
if str(ADAPTER_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SCRIPTS))
from profile_loader import ProfileError, load_profile  # type: ignore  # noqa: E402

DEFAULT_ADAPTER_PROFILES_DIR = ADAPTER_SCRIPTS.parent / "profiles"


class ComparisonError(ValueError):
    pass


EXPECTED_FRAMEWORKS = {
    "rust-axum-sqlx",
    "rust-axum-tokio-postgres",
    "rust-axum-toasty",
}
REQUIRED_METRICS = {"throughput_rps", "p50_ms", "p95_ms", "p99_ms", "error_rate_percent"}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ComparisonError("PyYAML is required to read the comparison matrix") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ComparisonError(f"comparison matrix not found: {path}") from exc
    except OSError as exc:
        raise ComparisonError(f"cannot read comparison matrix: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ComparisonError(f"comparison matrix is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ComparisonError("comparison matrix root must be an object")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ComparisonError(f"result file not found: {path}") from exc
    except OSError as exc:
        raise ComparisonError(f"cannot read result file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ComparisonError(f"result file is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ComparisonError("result root must be an object")
    return value


def non_empty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComparisonError(f"{label} must be a non-empty string")
    return value.strip()


def positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
        raise ComparisonError(f"{label} must be a finite non-negative number")
    return float(value)


def validate_matrix(matrix: dict[str, Any]) -> dict[str, Any]:
    if matrix.get("schema_version") != "1":
        raise ComparisonError('matrix schema_version must be "1"')
    matrix_id = non_empty(matrix.get("id"), "matrix.id")
    controls = matrix.get("controls")
    if not isinstance(controls, dict):
        raise ComparisonError("matrix.controls must be an object")
    for section in ("framework", "runtime", "rust", "database"):
        if not isinstance(controls.get(section), dict):
            raise ComparisonError(f"matrix.controls.{section} must be an object")
    db = controls["database"]
    for field in ("engine", "version", "performance_profile", "schema_digest", "seed_digest", "environment_digest"):
        if field in db:
            non_empty(db.get(field), f"matrix.controls.database.{field}")
    non_empty(controls.get("schema_digest"), "matrix.controls.schema_digest")
    non_empty(controls.get("seed_digest"), "matrix.controls.seed_digest")
    non_empty(controls.get("environment_digest"), "matrix.controls.environment_digest")
    workload = matrix.get("workload")
    if not isinstance(workload, dict) or not isinstance(workload.get("scenarios"), list) or not workload["scenarios"]:
        raise ComparisonError("matrix.workload.scenarios must be a non-empty array")
    scenario_ids: set[str] = set()
    for scenario in workload["scenarios"]:
        if not isinstance(scenario, dict):
            raise ComparisonError("matrix workload scenarios must be objects")
        scenario_id = non_empty(scenario.get("id"), "matrix.workload.scenario.id")
        if scenario_id in scenario_ids:
            raise ComparisonError(f"duplicate scenario id: {scenario_id}")
        scenario_ids.add(scenario_id)
        non_empty(scenario.get("public_seam"), f"matrix.workload.{scenario_id}.public_seam")
        if not isinstance(scenario.get("budget"), dict):
            raise ComparisonError(f"matrix.workload.{scenario_id}.budget must be an object")

    frameworks = matrix.get("frameworks")
    if not isinstance(frameworks, list) or len(frameworks) != len(EXPECTED_FRAMEWORKS):
        raise ComparisonError("matrix must list exactly the three configured Rust frameworks")
    ids: set[str] = set()
    for framework in frameworks:
        if not isinstance(framework, dict):
            raise ComparisonError("matrix frameworks must be objects")
        framework_id = non_empty(framework.get("id"), "matrix.framework.id")
        if framework_id in ids:
            raise ComparisonError(f"duplicate framework id: {framework_id}")
        ids.add(framework_id)
        for field in (
            "adapter_profile",
            "adapter_profile_file",
            "adapter_profile_digest",
            "driver",
            "driver_version",
            "driver_package_version",
            "query_model",
            "migration_tool",
            "migration_mode",
        ):
            non_empty(framework.get(field), f"matrix.frameworks.{framework_id}.{field}")
    if ids != EXPECTED_FRAMEWORKS:
        raise ComparisonError(f"matrix frameworks must be exactly {sorted(EXPECTED_FRAMEWORKS)}")
    if "diesel" in json.dumps(matrix, ensure_ascii=False).lower():
        raise ComparisonError("Diesel is not part of this comparison")
    return {"id": matrix_id, "scenario_ids": sorted(scenario_ids), "framework_ids": sorted(ids)}


def validate_adapter_bindings(matrix: dict[str, Any], profiles_dir: Path) -> None:
    controls = matrix["controls"]
    framework_controls = controls["framework"]
    runtime_controls = controls["runtime"]
    database_controls = controls["database"]
    for framework in matrix["frameworks"]:
        framework_id = framework["id"]
        profile_file = Path(framework["adapter_profile_file"])
        if profile_file.is_absolute() or ".." in profile_file.parts or profile_file.suffix not in {".yaml", ".yml"}:
            raise ComparisonError(f"adapter profile path is unsafe: {framework_id}")
        profile_path = (profiles_dir / profile_file).resolve()
        try:
            profile_path.relative_to(profiles_dir.resolve())
        except ValueError as exc:
            raise ComparisonError(f"adapter profile path escapes the configured directory: {framework_id}") from exc
        try:
            profile_digest = "sha256:" + hashlib.sha256(profile_path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ComparisonError(f"adapter profile file is unavailable: {framework_id}") from exc
        if profile_digest != framework["adapter_profile_digest"]:
            raise ComparisonError(f"adapter profile {framework_id} digest changed")
        try:
            profile = load_profile(framework["adapter_profile"], profiles_dir=profiles_dir)
        except (ProfileError, OSError) as exc:
            raise ComparisonError(f"adapter profile {framework_id} is invalid: {exc}") from exc
        if profile["id"] != framework_id:
            raise ComparisonError(f"adapter profile id does not match matrix framework: {framework_id}")
        if profile["framework"] != framework_controls:
            raise ComparisonError(f"adapter profile {framework_id} does not match Axum controls")
        if profile["runtime"] != runtime_controls:
            raise ComparisonError(f"adapter profile {framework_id} does not match Tokio controls")
        if {
            "engine": profile["database"]["engine"],
            "version": profile["database"]["version"],
            "performance_profile": profile["database"]["performance_profile"],
        } != database_controls:
            raise ComparisonError(f"adapter profile {framework_id} does not match database controls")
        if profile["driver"]["name"] != framework["driver"] or profile["driver"]["version"] != framework["driver_version"]:
            raise ComparisonError(f"adapter profile {framework_id} driver binding changed")
        if profile["driver"].get("package_version", profile["driver"]["version"]) != framework["driver_package_version"]:
            raise ComparisonError(f"adapter profile {framework_id} package version binding changed")
        migration = f"{profile['migration']['tool']}@{profile['migration']['version']}"
        if migration != framework["migration_tool"] or profile["migration"]["mode"] != framework["migration_mode"]:
            raise ComparisonError(f"adapter profile {framework_id} migration binding changed")


def validate_results(results: dict[str, Any], matrix: dict[str, Any], matrix_meta: dict[str, Any]) -> dict[str, Any]:
    if results.get("schema_version") != "1":
        raise ComparisonError('results schema_version must be "1"')
    if results.get("matrix_id") != matrix_meta["id"]:
        raise ComparisonError("result matrix_id does not match the comparison matrix")
    for field in ("commit", "schema_digest", "dataset_digest", "environment_digest"):
        non_empty(results.get(field), f"results.{field}")
    if results.get("schema_digest") != matrix["controls"]["schema_digest"]:
        raise ComparisonError("results.schema_digest must match the matrix schema digest")
    if results.get("dataset_digest") != matrix["controls"]["seed_digest"]:
        raise ComparisonError("results.dataset_digest must match the matrix seed digest")
    if results.get("environment_digest") != matrix["controls"]["environment_digest"]:
        raise ComparisonError("results.environment_digest must match the matrix environment digest")
    if results.get("database") != matrix["controls"]["database"]:
        raise ComparisonError("results.database must match the matrix database controls")
    scenarios = results.get("scenarios")
    if not isinstance(scenarios, dict):
        raise ComparisonError("results.scenarios must be an object")
    output: dict[str, Any] = {}
    rules = matrix.get("comparison_rules")
    minimum_samples = 1
    if isinstance(rules, dict) and isinstance(rules.get("minimum_samples_per_scenario"), int):
        minimum_samples = max(1, rules["minimum_samples_per_scenario"])
    for scenario_id in matrix_meta["scenario_ids"]:
        rows = scenarios.get(scenario_id)
        if not isinstance(rows, dict) or set(rows) != set(matrix_meta["framework_ids"]):
            raise ComparisonError(f"scenario {scenario_id} must contain one result for every framework")
        ranked = []
        for framework_id in matrix_meta["framework_ids"]:
            row = rows[framework_id]
            if not isinstance(row, dict):
                raise ComparisonError(f"result {scenario_id}/{framework_id} must be an object")
            samples = row.get("samples")
            if isinstance(samples, bool) or not isinstance(samples, int) or samples < minimum_samples:
                raise ComparisonError(
                    f"result {scenario_id}/{framework_id}.samples must be at least {minimum_samples}"
                )
            metrics = {metric: positive_number(row.get(metric), f"result {scenario_id}/{framework_id}.{metric}") for metric in REQUIRED_METRICS}
            ranked.append({"framework": framework_id, **metrics, "samples": samples})
        output[scenario_id] = {
            "by_p95_ms": sorted(ranked, key=lambda row: (row["p95_ms"], row["error_rate_percent"], row["framework"])),
            "by_throughput_rps": sorted(ranked, key=lambda row: (-row["throughput_rps"], row["error_rate_percent"], row["framework"])),
            "overall_winner": None,
        }
    return output


def compare(
    matrix: dict[str, Any],
    results: dict[str, Any],
    profiles_dir: Path = DEFAULT_ADAPTER_PROFILES_DIR,
) -> dict[str, Any]:
    matrix_meta = validate_matrix(matrix)
    validate_adapter_bindings(matrix, profiles_dir)
    rankings = validate_results(results, matrix, matrix_meta)
    return {
        "ok": True,
        "matrix_id": matrix_meta["id"],
        "comparison": rankings,
        "interpretation": "p95 latency and throughput are reported separately; no overall winner is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("--adapter-profiles-dir", type=Path, default=DEFAULT_ADAPTER_PROFILES_DIR)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                compare(load_yaml(args.matrix), load_json(args.results), profiles_dir=args.adapter_profiles_dir),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (ComparisonError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
