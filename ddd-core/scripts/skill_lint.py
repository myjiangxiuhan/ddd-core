#!/usr/bin/env python3
"""Validate the repository-level contract shared by every skill."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    allow_implicit_invocation: bool


class SkillContractError(ValueError):
    pass


def parse_frontmatter(path: Path, text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillContractError(f"{path}: SKILL.md must start with YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise SkillContractError(f"{path}: frontmatter is not closed") from exc

    values: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^(name|description):\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"\'')
    name = values.get("name", "")
    description = values.get("description", "")
    if not name or not description:
        raise SkillContractError(f"{path}: frontmatter needs non-empty name and description")
    return name, description


def parse_openai_metadata(path: Path) -> bool:
    metadata_path = path.parent / "agents" / "openai.yaml"
    if not metadata_path.is_file():
        raise SkillContractError(f"{path}: missing agents/openai.yaml")
    try:
        import yaml  # type: ignore
        value = yaml.safe_load(metadata_path.read_text(encoding="utf-8-sig"))
    except ImportError as exc:
        raise SkillContractError(f"{metadata_path}: PyYAML is required to validate agents/openai.yaml") from exc
    except yaml.YAMLError as exc:  # type: ignore[name-defined]
        raise SkillContractError(f"{metadata_path}: invalid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise SkillContractError(f"{metadata_path}: root must be an object")
    interface = value.get("interface")
    if not isinstance(interface, dict) or not isinstance(interface.get("default_prompt"), str):
        raise SkillContractError(f"{metadata_path}: interface.default_prompt is required")
    policy = value.get("policy")
    if not isinstance(policy, dict) or not isinstance(policy.get("allow_implicit_invocation"), bool):
        raise SkillContractError(f"{metadata_path}: policy.allow_implicit_invocation must be boolean")
    return policy["allow_implicit_invocation"]


def validate_skill(path: Path) -> SkillMetadata:
    text = path.read_text(encoding="utf-8-sig")
    name, description = parse_frontmatter(path, text)
    allow_implicit = parse_openai_metadata(path)
    if name != path.parent.name:
        raise SkillContractError(f"{path}: frontmatter name {name!r} does not match directory {path.parent.name!r}")
    has_stop = re.search(r"(?im)^##\s+(Hard stops|Stop)\s*$", text)
    has_delegate = re.search(r"(?im)^##\s+Delegates\s*$", text) and re.search(
        r"(?i)\b(call|delegate|invoke)\b.*\b(skill|tool)\b", text
    )
    if not has_stop and not has_delegate:
        raise SkillContractError(f"{path}: add a Hard stops/Stop section or a Delegates section naming the delegated skill/tool")
    if not re.search(r"(?i)\b(user-invoked|model-invoked)\b", text):
        raise SkillContractError(f"{path}: invocation mode must be stated in the skill text")
    if allow_implicit and not re.search(r"(?i)\bmodel-invoked\b", text):
        raise SkillContractError(f"{path}: implicit skill must state that it is model-invoked")
    if not allow_implicit and not re.search(r"(?i)\buser-invoked\b", text):
        raise SkillContractError(f"{path}: explicit skill must state that it is user-invoked")
    return SkillMetadata(name, description, allow_implicit)


def iter_skills(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("SKILL.md") if ".git" not in path.parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    checked = 0
    for path in iter_skills(root):
        checked += 1
        try:
            validate_skill(path)
        except (OSError, SkillContractError) as exc:
            errors.append(str(exc))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"skill contract failed: {len(errors)} error(s) across {checked} skill(s)", file=sys.stderr)
        return 1
    print(f"skill contract passed: {checked} skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
