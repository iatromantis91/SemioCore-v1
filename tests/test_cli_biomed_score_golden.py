# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from semioc.cli import main as cli_main


REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "fixtures" / "biomed_io_v1" / "levelc"
EXP = REPO / "expected" / "biomed_levelc_v1" / "score"
SCORE_SCHEMA_PATH = REPO / "schemas" / "biomed_io_v1" / "score.schema.json"


def _load_json(p: Path) -> object:
    return json.loads(p.read_text(encoding="utf-8"))


def _c14n_sha256(obj: object) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _run_cli(argv: list[str], *, monkeypatch: pytest.MonkeyPatch) -> int:
    # Ensure repo-root relative behaviours are stable.
    monkeypatch.chdir(REPO)
    try:
        return int(cli_main(argv))
    except SystemExit as e:
        raise AssertionError(f"CLI raised SystemExit({e.code}) for argv={argv}")


def test_cli_biomed_score_matches_golden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    schema = _load_json(SCORE_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)

    # 3 recipes x 4 timepoints
    cases: list[tuple[str, Path, Path]] = []
    for t in ("t0", "t24", "t72", "t168"):
        cases.append(("inflammation_score_v1", FIX / f"labs_{t}.json", EXP / "inflammation_score_v1" / f"{t}.score.json"))
        cases.append(("metabolic_score_v1", FIX / f"labs_{t}.json", EXP / "metabolic_score_v1" / f"{t}.score.json"))
        cases.append(("circadian_score_v1", FIX / f"wearable_{t}.json", EXP / "circadian_score_v1" / f"{t}.score.json"))

    out_root = tmp_path / "levelc" / "score"
    out_root.mkdir(parents=True, exist_ok=True)

    for recipe, input_path, expected_path in cases:
        assert input_path.is_file(), f"Missing fixture: {input_path}"
        assert expected_path.is_file(), f"Missing golden: {expected_path}"

        out_path = out_root / recipe / expected_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        rc = _run_cli(
            [
                "biomed",
                "score",
                "--recipe",
                recipe,
                "--input",
                str(input_path),
                "--emit-score",
                str(out_path),
                "--repo-root",
                str(REPO),
            ],
            monkeypatch=monkeypatch,
        )
        assert rc == 0

        got = _load_json(out_path)
        exp = _load_json(expected_path)

        jsonschema.validate(instance=got, schema=schema)
        jsonschema.validate(instance=exp, schema=schema)

        assert _c14n_sha256(got) == _c14n_sha256(exp), f"Score mismatch for {recipe} {expected_path.name}"
