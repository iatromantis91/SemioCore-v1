# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema
from jsonschema.validators import Draft202012Validator


class LoadError(RuntimeError):
    """Raised when a payload cannot be loaded or validated."""


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    schemas_dir: Path


def find_repo_root(start: Optional[Path] = None) -> RepoPaths:
    """Locate SemioCore repository root.

    The intent is to keep the toolchain runnable in-place from a cloned repo.
    A repo root is defined as a directory containing:
      - pyproject.toml
      - schemas/
      - semioc/
    """

    cur = (start or Path.cwd()).resolve()
    for _ in range(20):
        if (cur / "pyproject.toml").is_file() and (cur / "schemas").is_dir() and (cur / "semioc").is_dir():
            return RepoPaths(repo_root=cur, schemas_dir=cur / "schemas")
        if cur.parent == cur:
            break
        cur = cur.parent
    raise LoadError("Unable to locate repository root (pyproject.toml + schemas/ + semioc/).")


def _index_schemas_by_id(schemas_dir: Path) -> Dict[str, Path]:
    idx: Dict[str, Path] = {}
    for p in schemas_dir.rglob("*.schema.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        schema_id = obj.get("$id")
        if isinstance(schema_id, str) and schema_id:
            idx[schema_id] = p
    return idx


def load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise LoadError(f"Invalid JSON: {path} ({e})")


def load_and_validate(path: Path, repo: Optional[RepoPaths] = None) -> Dict[str, Any]:
    """Load a JSON payload and validate against its declared schema.

    Payloads are required to carry a top-level field:
      - schema: <schema $id>
    """

    repo = repo or find_repo_root(path.parent)
    payload = load_json(path)
    schema_id = payload.get("schema")
    if not isinstance(schema_id, str) or not schema_id:
        raise LoadError(f"Missing required field 'schema' in payload: {path}")

    schemas = _index_schemas_by_id(repo.schemas_dir)
    schema_path = schemas.get(schema_id)
    if schema_path is None:
        raise LoadError(f"Unknown schema id '{schema_id}' (no matching *.schema.json under schemas/)")

    schema_obj = load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema_obj)
    except Exception as e:
        raise LoadError(f"Invalid JSON Schema: {schema_path} ({e})")

    try:
        jsonschema.validate(instance=payload, schema=schema_obj)
    except Exception as e:
        raise LoadError(f"Schema validation failed for {path} against {schema_id}: {e}")

    return payload


def labs_units_view(labs_panel: Dict[str, Any]) -> Dict[str, str]:
    units: Dict[str, str] = {}
    for row in labs_panel.get("labs", []) or []:
        k = row.get("name")
        u = row.get("unit")
        if isinstance(k, str) and isinstance(u, str):
            units[k] = u
    return units


def wearable_units_view(wearable_ts: Dict[str, Any]) -> Dict[str, str]:
    """Extract a name->unit view from a wearable payload.

    The wearable schema admits two equivalent encodings:
      1) list-of-series: [{name, unit, values}, ...]
      2) dict-of-series: {"hr": {unit, values}, ...}

    For units gating we normalize both shapes into the same map.
    """

    units: Dict[str, str] = {}
    series = wearable_ts.get("series")

    if isinstance(series, list):
        for row in series or []:
            if not isinstance(row, dict):
                continue
            k = row.get("name")
            u = row.get("unit")
            if isinstance(k, str) and isinstance(u, str):
                units[k] = u
        return units

    if isinstance(series, dict):
        for k, row in series.items():
            if not isinstance(k, str) or not isinstance(row, dict):
                continue
            u = row.get("unit")
            if isinstance(u, str):
                units[k] = u
        return units

    return units


def assert_units(actual: Dict[str, str], expected: Dict[str, str], *, context: str) -> None:
    """Fail-fast units gate.

    The policy is strict by design: SemioCore does not attempt conversions at
    this layer. Recipes declare their expected units; inputs must match.
    """

    missing = sorted(set(expected) - set(actual))
    mismatched = sorted(k for k in expected if k in actual and actual[k] != expected[k])

    if missing or mismatched:
        lines = [f"Units gate failed: {context}"]
        if missing:
            lines.append(f"- missing: {missing}")
        if mismatched:
            lines.append("- mismatched:")
            for k in mismatched:
                lines.append(f"  - {k}: expected '{expected[k]}', got '{actual[k]}'")
        raise LoadError("\n".join(lines))
