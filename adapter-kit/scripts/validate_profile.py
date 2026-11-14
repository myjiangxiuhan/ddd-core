#!/usr/bin/env python3
"""Validate one Rust backend adapter profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from profile_loader import PROFILE_DIR, ProfileError, load_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", help="profile id or YAML path")
    parser.add_argument("--profiles-dir", type=Path, default=PROFILE_DIR)
    args = parser.parse_args()
    try:
        profile = load_profile(args.profile, profiles_dir=args.profiles_dir)
        print(
            json.dumps(
                {
                    "ok": True,
                    "id": profile["id"],
                    "version": profile["version"],
                    "framework": profile["framework"],
                    "runtime": profile["runtime"],
                    "driver": profile["driver"],
                    "migration": profile["migration"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (ProfileError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
