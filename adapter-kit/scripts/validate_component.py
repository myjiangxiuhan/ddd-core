#!/usr/bin/env python3
"""Validate one independent technology component."""

from __future__ import annotations

import argparse
import json

from component_loader import ComponentError, load_component


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component")
    args = parser.parse_args()
    try:
        value = load_component(args.component)
        print(
            json.dumps(
                {
                    "ok": True,
                    "id": value["id"],
                    "kind": value["kind"],
                    "version": value["version"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (ComponentError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
