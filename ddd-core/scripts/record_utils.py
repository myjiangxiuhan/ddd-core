#!/usr/bin/env python3
"""Small, project-local helpers for stable evidence records.

These helpers intentionally do not establish identity or trust.  They only
make file and JSON records comparable across machines and collaborators.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())
