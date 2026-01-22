# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from semioc.cli import main as cli_main


REPO = Path(__file__).resolve().parents[1]
SCORE_DIR = REPO / "expected" / "biomed_levelc_v1" / "score"
EXP_AUDIT_DIR = REPO / "expected" / "biomed_levelc_v1" / "audit"
AUDIT_SCHEMA_PATH = REPO / "schemas" / "audit_v1" / "score_compare_report.schema.json"


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


def test_cli_audit_score_compare_matches_golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    schema = _load_json(AUDIT_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)

    recipes = ["inflammation_score_v1", "metabolic_score_v1", "circadian_score_v1"]
    out_root = tmp_path / "levelc" / "audit"
    out_root.mkdir(parents=True, exist_ok=True)

    for recipe in recipes:
        baseline = SCORE_DIR / recipe / "t0.score.json"
        candidate = SCORE_DIR / recipe / "t0.score.json"
        expected = EXP_AUDIT_DIR / f"{recipe}.audit.json"
        assert baseline.is_file(), f"Missing baseline: {baseline}"
        assert expected.is_file(), f"Missing audit golden: {expected}"

        got_path = out_root / f"{recipe}.audit.json"
        got_path.parent.mkdir(parents=True, exist_ok=True)

        rc = _run_cli(
            [
                "audit",
                "score-compare",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--tolerance-abs",
                "0.0",
                "--emit-report",
                str(got_path),
            ],
            monkeypatch=monkeypatch,
        )
        assert rc == 0

        got = _load_json(got_path)
        exp = _load_json(expected)

        jsonschema.validate(instance=got, schema=schema)
        jsonschema.validate(instance=exp, schema=schema)

        assert _c14n_sha256(got) == _c14n_sha256(exp), f"Audit mismatch for {recipe}"
