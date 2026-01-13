from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from semioc.cli import main as cli_main


REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "fixtures" / "biomed_io_v1" / "levelc" / "intervention_manifest.json"
EXPECTED = REPO / "expected" / "biomed_levelc_v1" / "audit" / "tool_subject_01.audit.json"
SCHEMA_PATH = REPO / "schemas" / "audit_v1" / "tool_audit_report.schema.json"


def _load_json(p: Path) -> object:
    return json.loads(p.read_text(encoding="utf-8"))


def _c14n_sha256(obj: object) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _run_cli(argv: list[str], *, monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.chdir(REPO)
    try:
        return int(cli_main(argv))
    except SystemExit as e:
        raise AssertionError(f"CLI raised SystemExit({e.code}) for argv={argv}")


def test_cli_audit_run_matches_golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    schema = _load_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)

    assert MANIFEST.is_file(), f"Missing manifest fixture: {MANIFEST}"
    assert EXPECTED.is_file(), f"Missing audit golden: {EXPECTED}"

    got_path = tmp_path / "tool_subject_01.audit.json"
    rc = _run_cli(
        [
            "audit",
            "run",
            "--tool",
            "fixture_tool",
            "--manifest",
            str(MANIFEST.relative_to(REPO)),
            "--contracts",
            "biomed_v1",
            "--tolerance-abs",
            "0.0",
            "--emit-report",
            str(got_path),
        ],
        monkeypatch=monkeypatch,
    )
    assert rc == 0

    got = _load_json(got_path)
    exp = _load_json(EXPECTED)

    jsonschema.validate(instance=got, schema=schema)
    jsonschema.validate(instance=exp, schema=schema)

    assert _c14n_sha256(got) == _c14n_sha256(exp)


def test_cli_audit_alias_form_matches_golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    schema = _load_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)

    got_path = tmp_path / "tool_subject_01.alias.audit.json"
    rc = _run_cli(
        [
            "audit",
            "--tool",
            "fixture_tool",
            "--manifest",
            str(MANIFEST.relative_to(REPO)),
            "--contracts",
            "biomed_v1",
            "--tolerance-abs",
            "0.0",
            "--emit-report",
            str(got_path),
        ],
        monkeypatch=monkeypatch,
    )
    assert rc == 0

    got = _load_json(got_path)
    exp = _load_json(EXPECTED)

    jsonschema.validate(instance=got, schema=schema)
    assert _c14n_sha256(got) == _c14n_sha256(exp)
