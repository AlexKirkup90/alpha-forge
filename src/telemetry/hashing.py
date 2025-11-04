"""Utilities for hashing configs and capturing code revisions."""
from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any


def hash_config(cfg: dict[str, Any]) -> str:
    """Return a deterministic SHA256 hash of a configuration dictionary."""
    payload = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def code_sha() -> str:
    """Return the current Git revision short SHA, or "unknown" on failure."""
    try:
        output = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return output.decode("utf-8").strip()
    except Exception:
        return "unknown"
