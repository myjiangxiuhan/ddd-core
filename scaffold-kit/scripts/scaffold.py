#!/usr/bin/env python3
"""Inspect and render a safe, declarative scaffold configuration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")
VALID_AXES = {"standards", "spec", "ddd", "ui", "custom"}


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


def resolve_generator(profile: dict[str, Any], kind: str, generator_id: str) -> dict[str, Any]:
    generators = profile["generators"].get(kind)
    if not isinstance(generators, dict):
        raise ConfigError(f"generator kind not found: {kind}")
    generator = generators.get(generator_id)
    if not isinstance(generator, dict):
        raise ConfigError(f"generator not found: {kind}:{generator_id}")
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


def template_text(item: dict[str, Any], config_path: Path) -> str:
    if isinstance(item.get("template"), str):
        return item["template"]
    template_path = (config_path.parent / item["template_file"]).resolve()
    try:
        template_path.relative_to(config_path.parent.resolve())
    except ValueError as exc:
        raise ConfigError(f"template_file escapes configuration directory: {item['template_file']}") from exc
    try:
        return template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read template_file {template_path}: {exc}") from exc


def list_generators(profile_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for kind, generators in profile["generators"].items():
        if not isinstance(generators, dict):
            raise ConfigError(f"generators.{kind} must be an object")
        for generator_id, generator in generators.items():
            if not isinstance(generator, dict):
                raise ConfigError(f"generator {kind}:{generator_id} must be an object")
            rows.append({
                "kind": kind,
                "id": generator_id,
                "description": generator.get("description", ""),
                "public_seam": generator.get("public_seam"),
            })
    return {"ok": True, "profile": profile_id, "profile_version": profile["version"], "generators": rows}


def build_plan(args: argparse.Namespace, config_path: Path, profile_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    generator = resolve_generator(profile, args.kind, args.generator)
    context = names(args.name)
    context.update({
        "slice_id": args.slice_id or "",
        "profile_id": profile_id,
        "target": args.target,
    })
    root = project_root(config_path, args.root)
    target = safe_relative(root, args.target)
    actions = []
    for item in generator["files"]:
        relative_path = render(item["path"], context)
        output = safe_relative(target, relative_path)
        content = render(template_text(item, config_path), context)
        exists = output.exists()
        action = "overwrite" if exists and args.force else "skip" if exists else "create"
        actions.append({
            "path": str(output.relative_to(root)).replace("\\", "/"),
            "action": action,
            "bytes": len(content.encode("utf-8")),
            "content": content,
        })
    return {
        "ok": True,
        "profile": profile_id,
        "profile_version": profile["version"],
        "generator": f"{args.kind}:{args.generator}",
        "name": args.name,
        "target": str(target.relative_to(root)).replace("\\", "/") or ".",
        "contract": {
            "description": generator.get("description", ""),
            "required_components": generator.get("required_components", []),
            "public_seam": generator.get("public_seam"),
            "review_checks": generator.get("review_checks", []),
        },
        "actions": actions,
        "root": str(root),
    }


def apply_plan(plan: dict[str, Any], root: Path, force: bool) -> dict[str, Any]:
    applied = []
    for action in plan["actions"]:
        output = root / action["path"]
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
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--config", type=Path, default=argparse.SUPPRESS)
        subparser.add_argument("--profile", default=argparse.SUPPRESS)
        subparser.add_argument("--root", default=argparse.SUPPRESS)

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

    check_parser = sub.add_parser("check")
    add_common(check_parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        config_path = args.config.resolve()
        config = load_yaml(config_path)
        profile_id, profile = choose_profile(config, args.profile)
        if args.command == "list":
            emit(list_generators(profile_id, profile))
            return 0
        if args.command == "check":
            emit(list_generators(profile_id, profile))
            return 0
        if args.command == "describe":
            if ":" not in args.target:
                raise ConfigError("describe target must be kind:generator-id")
            kind, generator_id = args.target.split(":", 1)
            generator = resolve_generator(profile, kind, generator_id)
            emit({"ok": True, "profile": profile_id, "profile_version": profile["version"], "generator": f"{kind}:{generator_id}", "definition": generator})
            return 0
        plan = build_plan(args, config_path, profile_id, profile)
        if not args.apply:
            result = dict(plan)
            result.pop("root", None)
            result["mode"] = "dry-run"
            for action in result["actions"]:
                action.pop("content", None)
            emit(result)
            return 0
        if args.force and not args.apply:
            raise ConfigError("--force requires --apply")
        emit(apply_plan(plan, Path(plan["root"]), args.force))
        return 0
    except (ConfigError, OSError) as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
