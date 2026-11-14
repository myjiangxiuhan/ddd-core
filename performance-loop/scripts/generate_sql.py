#!/usr/bin/env python3
"""Generate a bounded, parameterized SQL operation from a database profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from performance_gate import PerformanceGateError, require_database_profile_gate, selected_profile_path
from profile_loader import PROFILE_DIR, ProfileError, load_yaml


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SqlGenerationError(ValueError):
    pass


def required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SqlGenerationError(f"{label} must be a non-empty string")
    return value.strip()


def identifier(value: Any, label: str) -> str:
    name = required_string(value, label)
    if not IDENTIFIER.fullmatch(name):
        raise SqlGenerationError(f"{label} contains an unsafe identifier")
    return name


def identifier_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise SqlGenerationError(f"{label} must be a non-empty array")
    return [identifier(item, f"{label}[{index}]") for index, item in enumerate(value)]


def quote(profile: dict[str, Any], name: str) -> str:
    if profile["engine"] == "sqlserver":
        return f"{profile['identifier_quote_left']}{name}{profile['identifier_quote_right']}"
    token = profile["identifier_quote"]
    return f"{token}{name}{token}"


def placeholder(profile: dict[str, Any], index: int) -> str:
    style = profile["parameter_style"]
    if style == "numbered_dollar":
        return f"${index}"
    if style == "question":
        return "?"
    if style == "named_at":
        return f"@p{index}"
    raise SqlGenerationError(f"unsupported parameter style: {style}")


def load_spec(path: Path) -> dict[str, Any]:
    value = load_yaml(path)
    operation = required_string(value.get("operation"), "operation")
    if operation not in {"list", "upsert"}:
        raise SqlGenerationError("operation must be list or upsert")
    return value


def filter_sql(profile: dict[str, Any], filters: Any, start_index: int) -> tuple[list[str], list[str], int]:
    if not isinstance(filters, list):
        raise SqlGenerationError("filters must be an array")
    clauses: list[str] = []
    parameters: list[str] = []
    index = start_index
    allowed = {"=", "is_null", "is_not_null"}
    for item_index, item in enumerate(filters):
        if not isinstance(item, dict):
            raise SqlGenerationError(f"filters[{item_index}] must be an object")
        column = identifier(item.get("column"), f"filters[{item_index}].column")
        operator = required_string(item.get("operator"), f"filters[{item_index}].operator").lower()
        if operator not in allowed:
            raise SqlGenerationError(f"filters[{item_index}].operator is not supported: {operator}")
        if operator == "is_null":
            clauses.append(f"{quote(profile, column)} IS NULL")
        elif operator == "is_not_null":
            clauses.append(f"{quote(profile, column)} IS NOT NULL")
        else:
            clauses.append(f"{quote(profile, column)} = {placeholder(profile, index)}")
            parameters.append(f"filter:{column}")
            index += 1
    return clauses, parameters, index


def order_spec(profile: dict[str, Any], value: Any) -> tuple[list[str], list[str]]:
    if not isinstance(value, list) or not value:
        raise SqlGenerationError("order_by must be a non-empty array")
    columns: list[str] = []
    directions: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise SqlGenerationError(f"order_by[{index}] must be an object")
        column = identifier(item.get("column"), f"order_by[{index}].column")
        direction = required_string(item.get("direction", "asc"), f"order_by[{index}].direction").lower()
        if direction not in {"asc", "desc"}:
            raise SqlGenerationError(f"order_by[{index}].direction must be asc or desc")
        columns.append(column)
        directions.append(direction)
    return columns, directions


def keyset_predicate(
    profile: dict[str, Any],
    columns: list[str],
    directions: list[str],
    start_index: int,
) -> tuple[str, list[str], int]:
    if len(columns) < 1:
        raise SqlGenerationError("keyset cursor must contain at least one column")
    if profile["pagination_style"] == "tuple":
        if len(set(directions)) != 1:
            raise SqlGenerationError("tuple keyset pagination requires one direction for all cursor columns")
        operator = ">" if directions[0] == "asc" else "<"
        left = ", ".join(quote(profile, column) for column in columns)
        right = ", ".join(placeholder(profile, start_index + offset) for offset in range(len(columns)))
        return f"({left}) {operator} ({right})", [f"cursor:{column}" for column in columns], start_index + len(columns)

    terms: list[str] = []
    parameters = [f"cursor:{column}" for column in columns]
    for index, column in enumerate(columns):
        equalities = [
            f"{quote(profile, previous)} = {placeholder(profile, start_index + previous_index)}"
            for previous_index, previous in enumerate(columns[:index])
        ]
        operator = ">" if directions[index] == "asc" else "<"
        comparison = f"{quote(profile, column)} {operator} {placeholder(profile, start_index + index)}"
        terms.append("(" + " AND ".join(equalities + [comparison]) + ")")
    return "(" + " OR ".join(terms) + ")", parameters, start_index + len(columns)


def generate_list(profile: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    table = identifier(spec.get("table"), "table")
    columns = identifier_list(spec.get("columns"), "columns")
    joins = spec.get("joins", [])
    if joins:
        raise SqlGenerationError("joins are not supported by this bounded generator; define an explicit join profile first")
    filter_clauses, parameters, next_index = filter_sql(profile, spec.get("filters", []), 1)
    order_columns, directions = order_spec(profile, spec.get("order_by"))
    pagination = spec.get("pagination")
    if not isinstance(pagination, dict):
        raise SqlGenerationError("pagination must be an object")
    kind = required_string(pagination.get("kind"), "pagination.kind")
    expected = profile["sql_generation"]["list"]["pagination"]
    if kind != expected:
        raise SqlGenerationError(f"pagination.kind must be {expected} for profile {profile['id']}")
    cursor_columns = identifier_list(pagination.get("cursor_columns"), "pagination.cursor_columns")
    if cursor_columns != order_columns:
        raise SqlGenerationError("pagination.cursor_columns must match order_by columns")
    predicate, cursor_parameters, next_index = keyset_predicate(profile, cursor_columns, directions, next_index)
    clauses = filter_clauses + [predicate]
    parameters.extend(cursor_parameters)
    limit = pagination.get("limit")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise SqlGenerationError("pagination.limit must be a positive integer")
    limit_parameter = placeholder(profile, next_index)
    parameters.append("limit")
    table_sql = quote(profile, table)
    projection = ", ".join(quote(profile, column) for column in columns)
    where_sql = " AND ".join(clauses)
    order_sql = ", ".join(f"{quote(profile, column)} {direction.upper()}" for column, direction in zip(order_columns, directions))
    if profile["sql_generation"]["list"]["limit_style"] == "offset_fetch":
        sql = (
            f"SELECT {projection} FROM {table_sql} WHERE {where_sql} ORDER BY {order_sql} "
            f"OFFSET 0 ROWS FETCH NEXT {limit_parameter} ROWS ONLY;"
        )
    else:
        sql = f"SELECT {projection} FROM {table_sql} WHERE {where_sql} ORDER BY {order_sql} LIMIT {limit_parameter};"
    plan_command = profile["sql_generation"]["list"]["plan_command"].format(sql=sql.rstrip(";"))
    return {
        "profile": profile["id"],
        "operation": "list",
        "sql": sql,
        "parameters": parameters,
        "plan_command": plan_command,
        "limit_value": limit,
    }


def generate_upsert(profile: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    table = identifier(spec.get("table"), "table")
    insert_columns = identifier_list(spec.get("insert_columns"), "insert_columns")
    conflict_columns = identifier_list(spec.get("conflict_columns"), "conflict_columns")
    update_columns = identifier_list(spec.get("update_columns"), "update_columns")
    returning_columns = identifier_list(spec.get("returning_columns", []), "returning_columns", allow_empty=True)
    if not set(conflict_columns).issubset(insert_columns):
        raise SqlGenerationError("conflict_columns must be included in insert_columns")
    if not set(update_columns).issubset(insert_columns):
        raise SqlGenerationError("update_columns must be included in insert_columns")
    returning_supported = profile["sql_generation"]["upsert"]["returning"] == "supported"
    if returning_columns and not returning_supported:
        raise SqlGenerationError(f"profile {profile['id']} does not support atomic upsert returning")
    table_sql = quote(profile, table)
    columns_sql = ", ".join(quote(profile, column) for column in insert_columns)
    values = [placeholder(profile, index + 1) for index in range(len(insert_columns))]
    parameters = [f"value:{column}" for column in insert_columns]
    strategy = profile["sql_generation"]["upsert"]["strategy"]
    returning_sql = ", ".join(quote(profile, column) for column in returning_columns)
    if strategy == "on_conflict":
        reference = profile["sql_generation"]["upsert"]["conflict_reference"]
        updates = ", ".join(f"{quote(profile, column)} = {reference}.{quote(profile, column)}" for column in update_columns)
        sql = (
            f"INSERT INTO {table_sql} ({columns_sql}) VALUES ({', '.join(values)}) "
            f"ON CONFLICT ({', '.join(quote(profile, column) for column in conflict_columns)}) DO UPDATE SET {updates}"
        )
        if returning_columns:
            sql += f" RETURNING {returning_sql}"
        sql += ";"
    elif strategy == "on_duplicate_key":
        updates = ", ".join(f"{quote(profile, column)} = new.{quote(profile, column)}" for column in update_columns)
        sql = (
            f"INSERT INTO {table_sql} ({columns_sql}) VALUES ({', '.join(values)}) AS new "
            f"ON DUPLICATE KEY UPDATE {updates};"
        )
    elif strategy == "update_insert_transaction":
        concurrency_required = profile["sql_generation"]["upsert"].get("concurrency_required", False)
        concurrency_strategy = spec.get("concurrency_strategy")
        if concurrency_required:
            concurrency_strategy = required_string(concurrency_strategy, "concurrency_strategy")
            options = profile["sql_generation"]["upsert"].get("concurrency_options", [])
            if concurrency_strategy not in options:
                raise SqlGenerationError(
                    f"concurrency_strategy must be one of {', '.join(options)} for profile {profile['id']}"
                )
        if concurrency_strategy == "serializable":
            transaction_prefix = "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;\n"
            update_target = table_sql
        elif concurrency_strategy == "updlock_holdlock":
            transaction_prefix = ""
            update_target = f"{table_sql} WITH (UPDLOCK, HOLDLOCK)"
        else:
            transaction_prefix = ""
            update_target = table_sql
        output = f" OUTPUT {', '.join('inserted.' + quote(profile, column) for column in returning_columns)}" if returning_columns else ""
        assignments = ", ".join(
            f"{quote(profile, column)} = {placeholder(profile, insert_columns.index(column) + 1)}" for column in update_columns
        )
        predicates = " AND ".join(
            f"{quote(profile, column)} = {placeholder(profile, insert_columns.index(column) + 1)}" for column in conflict_columns
        )
        sql = (
            f"{transaction_prefix}"
            "SET XACT_ABORT ON;\n"
            "BEGIN TRANSACTION;\n"
            f"UPDATE {update_target} SET {assignments}{output} WHERE {predicates};\n"
            "IF @@ROWCOUNT = 0\n"
            "BEGIN\n"
            f"  INSERT INTO {table_sql} ({columns_sql}){output} VALUES ({', '.join(values)});\n"
            "END;\n"
            "COMMIT TRANSACTION;"
        )
    else:
        raise SqlGenerationError(f"unsupported upsert strategy: {strategy}")
    return {
        "profile": profile["id"],
        "operation": "upsert",
        "sql": sql,
        "parameters": parameters,
        "plan_command": profile["capabilities"]["plan"]["syntax_or_api"],
    }


def generate(profile: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    if spec["operation"] == "list":
        return generate_list(profile, spec)
    return generate_upsert(profile, spec)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", help="profile id or YAML path")
    parser.add_argument("spec", type=Path, help="bounded SQL operation spec")
    parser.add_argument("--state", type=Path, required=True, help="project workflow ledger")
    parser.add_argument("--trusted-public-key", required=True, help="external trusted user public key")
    parser.add_argument("--profiles-dir", type=Path, default=PROFILE_DIR)
    args = parser.parse_args()
    try:
        _, database_record, profile, _ = require_database_profile_gate(
            args.state,
            args.trusted_public_key,
            require_performance=False,
        )
        requested_profile = Path(args.profile).stem if Path(args.profile).suffix in {".yaml", ".yml"} else args.profile
        if requested_profile != database_record["id"]:
            raise SqlGenerationError("requested SQL profile does not match the signed workflow database_profile")
        selected_path = selected_profile_path(args.state, database_record)
        if args.profiles_dir.resolve() not in {selected_path.parent.resolve(), PROFILE_DIR.resolve()}:
            raise SqlGenerationError("--profiles-dir must be the selected database profile directory")
        spec = load_spec(args.spec)
        print(json.dumps(generate(profile, spec), ensure_ascii=False, indent=2))
        return 0
    except (PerformanceGateError, ProfileError, SqlGenerationError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
