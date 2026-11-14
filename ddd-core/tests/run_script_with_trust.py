"""Run one approval-related CLI with a test-only trust-root injection."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: run_script_with_trust.py SCRIPT TRUST_ROOT [ARGS...]", file=sys.stderr)
        return 2
    script = Path(sys.argv[1]).resolve()
    trust_root = Path(sys.argv[2]).resolve()
    approval_dir = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(approval_dir))
    sys.path.insert(0, str(script.parent))
    import approval  # type: ignore  # noqa: PLC0415

    approval.system_user_directory = lambda: trust_root  # type: ignore[assignment]
    target = importlib.import_module(script.stem)
    sys.argv = [str(script), *sys.argv[3:]]
    result = target.main()
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
