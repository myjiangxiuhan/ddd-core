#!/usr/bin/env python3
"""Validate a declarative code-review profile without executing checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


AXES = {"standards", "spec", "ddd", "ui", "performance", "custom"}
SEVERITIES = {"blocker", "major", "minor", "info"}
FORBIDDEN_KEYS = {"command", "shell", "exec", "run", "script"}


class ProfileError(ValueError):
    pass


def validate(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ProfileError("PyYAML is required to validate review profiles") from exc
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ProfileError(f"profile not found: {path}") from exc
    except OSError as exc:
        raise ProfileError(f"cannot read profile: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ProfileError(f"profile is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileError("profile root must be an object")
    if value.get("schema_version") != "1":
        raise ProfileError('schema_version must be "1"')
    for key in ("id", "version"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ProfileError(f"{key} must be a non-empty string")
    checks = value.get("checks", [])
    if not isinstance(checks, list):
        raise ProfileError("checks must be an array")
    seen: set[str] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ProfileError(f"checks[{index}] must be an object")
        forbidden = sorted(FORBIDDEN_KEYS.intersection(check))
        if forbidden:
            raise ProfileError(f"checks[{index}] contains executable keys: {', '.join(forbidden)}")
        for key in ("id", "axis", "severity", "blocking", "rule", "evidence"):
            if key not in check:
                raise ProfileError(f"checks[{index}] missing {key}")
        check_id = check["id"]
        if not isinstance(check_id, str) or not check_id.strip():
            raise ProfileError(f"checks[{index}].id must be a non-empty string")
        if check_id in seen:
            raise ProfileError(f"duplicate check id: {check_id}")
        seen.add(check_id)
        if check["axis"] not in AXES:
            raise ProfileError(f"checks[{index}].axis must be one of {sorted(AXES)}")
        if check["severity"] not in SEVERITIES:
            raise ProfileError(f"checks[{index}].severity must be one of {sorted(SEVERITIES)}")
        if not isinstance(check["blocking"], bool):
            raise ProfileError(f"checks[{index}].blocking must be boolean")
        if not isinstance(check["rule"], str) or not check["rule"].strip():
            raise ProfileError(f"checks[{index}].rule must be a non-empty string")
        if not isinstance(check["evidence"], (str, list)):
            raise ProfileError(f"checks[{index}].evidence must be a string or array")
        applies_to = check.get("applies_to")
        if applies_to is not None and not isinstance(applies_to, list):
            raise ProfileError(f"checks[{index}].applies_to must be an array when present")
    return {"ok": True, "id": value["id"], "version": value["version"], "checks": len(checks)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.profile), ensure_ascii=False, indent=2))
        return 0
    except ProfileError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
