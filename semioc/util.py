# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from typing import Any


# Fixed timestamp for deterministic artifacts (golden tests, reproducible reports).
# The pipeline may opt into real time explicitly when needed.
FIXED_TIMESTAMP_ISO = "1970-01-01T00:00:00+00:00"


def sha256_file(path: str) -> str:
    """Compute SHA-256 of a file, streaming for large inputs."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now_iso() -> str:
    """Current UTC time as ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def stable_utc_now_iso(use_realtime: bool = False) -> str:
    """Return a stable timestamp for reproducible artifacts.

    When `use_realtime=True`, returns the actual current time. Otherwise, returns
    a fixed epoch string.
    """
    return utc_now_iso() if use_realtime else FIXED_TIMESTAMP_ISO


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Controls float quantization for JSON emission + canonical hashing.
# Override via env var, e.g.:
#   SEMIOC_JSON_FLOAT_NDIGITS=12
# Set to -1 to disable rounding (not recommended if you want portable goldens).
DEFAULT_FLOAT_NDIGITS = _env_int("SEMIOC_JSON_FLOAT_NDIGITS", 12)


def normalize_json(obj: Any, float_ndigits: int | None = None) -> Any:
    """Normalize JSON-like structures for cross-platform reproducibility.

    - Quantize floats to N decimal digits.
    - Convert -0.0 to 0.0.
    - Recurse through dict/list/tuple.

    Notes:
    - We do not change computational precision internally; this is
      serialization/hash stability.
    - NaN/Inf are left untouched (JSON encoders may reject them, as they should).
    """

    if float_ndigits is None:
        float_ndigits = DEFAULT_FLOAT_NDIGITS

    # Order matters: bool is a subclass of int, so check float first.
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return obj
        if float_ndigits >= 0:
            obj = round(obj, float_ndigits)
        # Collapse negative zero
        if obj == 0.0:
            obj = 0.0
        return obj

    if obj is None or isinstance(obj, (str, int, bool)):
        return obj

    if isinstance(obj, list):
        return [normalize_json(v, float_ndigits) for v in obj]

    if isinstance(obj, tuple):
        # JSON doesn't have tuples; normalize to a list.
        return [normalize_json(v, float_ndigits) for v in obj]

    if isinstance(obj, dict):
        return {k: normalize_json(v, float_ndigits) for k, v in obj.items()}

    return obj


def json_c14n(obj: Any) -> str:
    """Canonical JSON string for hashing/diffing.

    - sort_keys=True for stable key order
    - separators without whitespace
    - ensure_ascii=False to preserve unicode deterministically
    - allow_nan=False to reject non-JSON floats
    """
    obj = normalize_json(obj)
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def sha256_c14n_json(obj: Any) -> str:
    """SHA-256 over canonical JSON representation."""
    h = hashlib.sha256()
    h.update(json_c14n(obj).encode("utf-8"))
    return h.hexdigest()
