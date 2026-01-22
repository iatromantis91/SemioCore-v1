# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_semio(args: list[str]) -> None:
    cmd = [PYTHON, "-m", "semioc", *args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO, check=True)


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    # You can tune this if needed:
    # os.environ["SEMIOC_JSON_FLOAT_NDIGITS"] = "12"

    fix = REPO / "fixtures" / "biomed_io_v1" / "levelc"
    exp_root = REPO / "expected" / "biomed_levelc_v1"
    exp_score = exp_root / "score"
    exp_rec = exp_root / "recovery"
    exp_pl = exp_root / "plasticity2"
    exp_audit = exp_root / "audit"

    recipes = ["inflammation_score_v1", "metabolic_score_v1", "circadian_score_v1"]
    times = ["t0", "t24", "t72", "t168"]

    # 1) Scores (12 files)
    for recipe in recipes:
        for t in times:
            if recipe == "circadian_score_v1":
                inp = fix / f"wearable_{t}.json"
            else:
                inp = fix / f"labs_{t}.json"
            out = exp_score / recipe / f"{t}.score.json"
            ensure_parent(out)
            run_semio(
                [
                    "biomed",
                    "score",
                    "--recipe",
                    recipe,
                    "--input",
                    str(inp),
                    "--emit-score",
                    str(out),
                    "--repo-root",
                    str(REPO),
                ]
            )

    # 2) Recovery + plasticity2 (3 + 3)
    for recipe in recipes:
        baseline = exp_score / recipe / "t0.score.json"
        t24 = exp_score / recipe / "t24.score.json"
        t72 = exp_score / recipe / "t72.score.json"
        t168 = exp_score / recipe / "t168.score.json"

        out_rec = exp_rec / f"{recipe}.recovery.json"
        out_pl = exp_pl / f"{recipe}.plasticity2.json"
        ensure_parent(out_rec)
        ensure_parent(out_pl)

        run_semio(
            [
                "biomed",
                "compare",
                "--baseline-label",
                "t0",
                "--baseline-score",
                str(baseline),
                "--post",
                f"t24={t24}",
                "--post",
                f"t72={t72}",
                "--post",
                f"t168={t168}",
                "--emit-report",
                str(out_rec),
            ]
        )
        run_semio(
            [
                "biomed",
                "plasticity2",
                "--recovery-report",
                str(out_rec),
                "--emit-report",
                str(out_pl),
            ]
        )

    # 3) Audit score-compare goldens (3)
    for recipe in recipes:
        baseline = exp_score / recipe / "t0.score.json"
        candidate = exp_score / recipe / "t0.score.json"
        out = exp_audit / f"{recipe}.audit.json"
        ensure_parent(out)
        run_semio(
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
                str(out),
            ]
        )

    # 4) Tool audit golden (1)
    manifest = fix / "intervention_manifest.json"
    manifest_ref = str(manifest.relative_to(REPO))
    out_tool = exp_audit / "tool_subject_01.audit.json"
    ensure_parent(out_tool)
    run_semio(
        [
            "audit",
            "run",
            "--tool",
            "fixture_tool",
            "--manifest",
            manifest_ref,
            "--contracts",
            "biomed_v1",
            "--tolerance-abs",
            "0.0",
            "--emit-report",
            str(out_tool),
        ]
    )

    print("OK: regenerated goldens under expected/biomed_levelc_v1/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
