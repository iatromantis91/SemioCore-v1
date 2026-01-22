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
EXP_RECOVERY_DIR = REPO / "expected" / "biomed_levelc_v1" / "recovery"
EXP_PLASTICITY2_DIR = REPO / "expected" / "biomed_levelc_v1" / "plasticity2"
RECOVERY_SCHEMA_PATH = REPO / "schemas" / "biomed_levelc_v1" / "recovery_report.schema.json"
PLASTICITY2_SCHEMA_PATH = REPO / "schemas" / "biomed_levelc_v1" / "plasticity2_report.schema.json"


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


def test_cli_biomed_compare_and_plasticity2_match_golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    schema_recovery = _load_json(RECOVERY_SCHEMA_PATH)
    schema_pl = _load_json(PLASTICITY2_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema_recovery)
    jsonschema.Draft202012Validator.check_schema(schema_pl)

    recipes = ["inflammation_score_v1", "metabolic_score_v1", "circadian_score_v1"]

    out_root = tmp_path / "levelc"
    out_root.mkdir(parents=True, exist_ok=True)

    for recipe in recipes:
        baseline = SCORE_DIR / recipe / "t0.score.json"
        exp_rec = EXP_RECOVERY_DIR / f"{recipe}.recovery.json"
        exp_pl = EXP_PLASTICITY2_DIR / f"{recipe}.plasticity2.json"
        assert baseline.is_file(), f"Missing baseline score: {baseline}"
        assert exp_rec.is_file(), f"Missing recovery golden: {exp_rec}"
        assert exp_pl.is_file(), f"Missing plasticity2 golden: {exp_pl}"

        got_rec = out_root / "recovery" / f"{recipe}.recovery.json"
        got_pl = out_root / "plasticity2" / f"{recipe}.plasticity2.json"
        got_rec.parent.mkdir(parents=True, exist_ok=True)
        got_pl.parent.mkdir(parents=True, exist_ok=True)

        rc = _run_cli(
            [
                "biomed",
                "compare",
                "--baseline-label",
                "t0",
                "--baseline-score",
                str(baseline),
                "--post",
                f"t24={SCORE_DIR / recipe / 't24.score.json'}",
                "--post",
                f"t72={SCORE_DIR / recipe / 't72.score.json'}",
                "--post",
                f"t168={SCORE_DIR / recipe / 't168.score.json'}",
                "--emit-report",
                str(got_rec),
            ],
            monkeypatch=monkeypatch,
        )
        assert rc == 0

        rc = _run_cli(
            [
                "biomed",
                "plasticity2",
                "--recovery-report",
                str(got_rec),
                "--emit-report",
                str(got_pl),
            ],
            monkeypatch=monkeypatch,
        )
        assert rc == 0

        rec_got = _load_json(got_rec)
        rec_exp = _load_json(exp_rec)
        pl_got = _load_json(got_pl)
        pl_exp = _load_json(exp_pl)

        jsonschema.validate(instance=rec_got, schema=schema_recovery)
        jsonschema.validate(instance=rec_exp, schema=schema_recovery)
        jsonschema.validate(instance=pl_got, schema=schema_pl)
        jsonschema.validate(instance=pl_exp, schema=schema_pl)

        assert _c14n_sha256(rec_got) == _c14n_sha256(rec_exp), f"Recovery mismatch for {recipe}"
        assert _c14n_sha256(pl_got) == _c14n_sha256(pl_exp), f"Plasticity2 mismatch for {recipe}"
