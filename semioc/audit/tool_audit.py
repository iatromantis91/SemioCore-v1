# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import VERSION
from ..biomed.artifacts import SCORE_SCHEMA_V1, make_score_artifact
from ..biomed.levelc import PLASTICITY2_SCHEMA_V1, RECOVERY_SCHEMA_V1, compare_v2, plasticity_v2
from ..io.load import LoadError, RepoPaths, find_repo_root, load_and_validate, labs_units_view, wearable_units_view, assert_units
from ..recipes.registry import get_recipe
from ..util import normalize_json, sha256_c14n_json, stable_utc_now_iso
from .score_compare import score_compare


TOOL_AUDIT_SCHEMA_V1 = "semiocore.audit.tool_audit_report.v1"


@dataclass(frozen=True)
class TimepointRef:
    label: str
    labs_ref: str
    wearable_ref: str
    external_scores: Dict[str, str]


def _resolve_ref(repo_root: Path, ref: str) -> Path:
    p = Path(ref)
    return p if p.is_absolute() else (repo_root / p)


def _load_score_artifact(path: Path) -> Dict[str, Any]:
    obj = load_and_validate(path)  # validates against its declared schema
    if obj.get("schema") != SCORE_SCHEMA_V1:
        raise LoadError(f"Expected score artifact schema '{SCORE_SCHEMA_V1}', got '{obj.get('schema')}' ({path})")
    return obj


def _oracle_score_from_payload(
    *,
    recipe_id: str,
    payload_path: Path,
    repo: RepoPaths,
    use_realtime: bool,
) -> Dict[str, Any]:
    payload = load_and_validate(payload_path, repo=repo)
    recipe = get_recipe(recipe_id)

    # Units gate (fail-fast, no conversions)
    if recipe.kind == "labs":
        assert_units(labs_units_view(payload), recipe.expected_units, context=f"{recipe_id} ({payload_path})")
    elif recipe.kind == "wearable":
        assert_units(wearable_units_view(payload), recipe.expected_units, context=f"{recipe_id} ({payload_path})")

    result_obj = recipe.runner(payload)
    if hasattr(result_obj, "to_dict"):
        result = result_obj.to_dict()  # type: ignore[attr-defined]
    elif isinstance(result_obj, dict):
        result = result_obj
    else:
        raise LoadError(f"Unsupported recipe result type for {recipe_id}: {type(result_obj)}")
    return make_score_artifact(
        tool_version=VERSION,
        input_payload=payload,
        result=result,
        use_realtime=use_realtime,
    )


def _tp_from_manifest_row(row: Dict[str, Any]) -> TimepointRef:
    label = str(row.get("label") or "").strip()
    if not label:
        raise LoadError("intervention_manifest: each timepoint requires non-empty 'label'")

    labs_ref = str(row.get("labs_ref") or "").strip()
    wearable_ref = str(row.get("wearable_ref") or "").strip()
    if not labs_ref or not wearable_ref:
        raise LoadError(f"intervention_manifest[{label}]: requires both labs_ref and wearable_ref")

    ext = row.get("external_scores")
    if not isinstance(ext, dict) or not ext:
        raise LoadError(f"intervention_manifest[{label}]: requires external_scores map")

    external_scores: Dict[str, str] = {}
    for k, v in ext.items():
        if isinstance(k, str) and isinstance(v, str) and k and v:
            external_scores[k] = v
    if not external_scores:
        raise LoadError(f"intervention_manifest[{label}]: external_scores must contain recipe->path entries")

    return TimepointRef(label=label, labs_ref=labs_ref, wearable_ref=wearable_ref, external_scores=external_scores)


def _suite_recipes(contracts: str) -> List[str]:
    """Resolve a contract suite name into recipe ids.

    v1.3 ships a single built-in suite:
      - biomed_v1: inflammation_score_v1, metabolic_score_v1, circadian_score_v1
    """

    name = (contracts or "").strip()
    if name in ("biomed_v1", "biomed_levelc_v1"):
        return ["inflammation_score_v1", "metabolic_score_v1", "circadian_score_v1"]
    raise LoadError(f"Unknown contracts suite '{contracts}'. Supported: biomed_v1")


def _metric_abs_diff(a: Any, b: Any) -> Optional[float]:
    try:
        if a is None or b is None:
            return None
        return abs(float(a) - float(b))
    except Exception:
        return None


def run_tool_audit(
    *,
    tool_name: str,
    manifest_path: Path,
    contracts: str,
    tolerance_abs: float,
    emit_report: Path,
    repo_root: Optional[Path] = None,
    use_realtime: bool = False,
) -> Dict[str, Any]:
    """Audit an external tool against SemioCore oracles using an intervention manifest.

    The current v1.3 implementation consumes `external_scores` from the manifest
    (score artifacts produced by the external tool) and compares them to
    SemioCore's own deterministic scores computed from the referenced raw inputs.
    Recovery + plasticity2 summaries are derived from each score set and compared
    at the metric level.
    """

    if tolerance_abs < 0:
        raise LoadError("tolerance_abs must be >= 0")
    if not tool_name:
        raise LoadError("tool_name must be non-empty")

    repo = RepoPaths(repo_root=repo_root, schemas_dir=(repo_root / "schemas")) if repo_root else find_repo_root(manifest_path.parent)

    manifest_obj = load_and_validate(manifest_path, repo=repo)
    if manifest_obj.get("schema") != "semiocore.biomed.intervention_manifest.v1":
        raise LoadError("manifest schema mismatch: expected semiocore.biomed.intervention_manifest.v1")

    baseline_row = manifest_obj.get("baseline")
    posts_rows = manifest_obj.get("posts")
    if not isinstance(baseline_row, dict) or not isinstance(posts_rows, list):
        raise LoadError("intervention_manifest requires 'baseline' object and 'posts' array")

    baseline = _tp_from_manifest_row(baseline_row)
    posts = [_tp_from_manifest_row(r) for r in posts_rows if isinstance(r, dict)]

    suite = _suite_recipes(contracts)

    # Preload all candidate score artifacts referenced by the manifest.
    # We keep them as evidence for hashing.
    cand_scores: Dict[str, Dict[str, Dict[str, Any]]] = {rid: {} for rid in suite}
    oracle_scores: Dict[str, Dict[str, Dict[str, Any]]] = {rid: {} for rid in suite}

    timepoints: List[TimepointRef] = [baseline, *posts]

    for rid in suite:
        recipe = get_recipe(rid)
        for tp in timepoints:
            # Select raw input by recipe kind.
            raw_ref = tp.labs_ref if recipe.kind == "labs" else tp.wearable_ref
            raw_path = _resolve_ref(repo.repo_root, raw_ref)
            oracle = _oracle_score_from_payload(recipe_id=rid, payload_path=raw_path, repo=repo, use_realtime=use_realtime)
            oracle_scores[rid][tp.label] = oracle

            cand_ref = tp.external_scores.get(rid)
            if not isinstance(cand_ref, str) or not cand_ref:
                raise LoadError(f"manifest[{tp.label}]: external_scores missing entry for recipe '{rid}'")
            cand_path = _resolve_ref(repo.repo_root, cand_ref)
            cand = _load_score_artifact(cand_path)
            if cand.get("recipe") != rid:
                raise LoadError(f"Candidate score recipe mismatch at {tp.label}: expected '{rid}', got '{cand.get('recipe')}'")
            cand_scores[rid][tp.label] = cand

    # Build report per recipe.
    recipes_out: List[Dict[str, Any]] = []
    ok_count = 0

    for rid in suite:
        recipe = get_recipe(rid)

        # Score-level comparisons
        tps_out: List[Dict[str, Any]] = []
        score_ok = True

        for tp in timepoints:
            oracle = oracle_scores[rid][tp.label]
            cand = cand_scores[rid][tp.label]
            cmp = score_compare(
                tool_version=VERSION,
                baseline=oracle,
                candidate=cand,
                tolerance_abs=float(tolerance_abs),
                use_realtime=use_realtime,
            )
            if not cmp.get("within_tolerance"):
                score_ok = False

            tps_out.append(
                {
                    "label": tp.label,
                    "raw_ref": tp.labs_ref if recipe.kind == "labs" else tp.wearable_ref,
                    "candidate_ref": tp.external_scores.get(rid),
                    "score_compare": cmp,
                }
            )

        # Recovery + plasticity2 (derive from scores)
        def _mk_posts(scores_map: Dict[str, Dict[str, Any]]) -> List[Tuple[str, Dict[str, Any]]]:
            return [(tp.label, scores_map[tp.label]) for tp in posts]

        rec_oracle = compare_v2(
            tool_version=VERSION,
            baseline_label=baseline.label,
            baseline_score=oracle_scores[rid][baseline.label],
            posts=_mk_posts(oracle_scores[rid]),
            use_realtime=use_realtime,
        )
        rec_cand = compare_v2(
            tool_version=VERSION,
            baseline_label=baseline.label,
            baseline_score=cand_scores[rid][baseline.label],
            posts=_mk_posts(cand_scores[rid]),
            use_realtime=use_realtime,
        )
        if rec_oracle.get("schema") != RECOVERY_SCHEMA_V1 or rec_cand.get("schema") != RECOVERY_SCHEMA_V1:
            raise LoadError("Unexpected recovery report schema")

        pl_oracle = plasticity_v2(tool_version=VERSION, recovery_report=rec_oracle, use_realtime=use_realtime)
        pl_cand = plasticity_v2(tool_version=VERSION, recovery_report=rec_cand, use_realtime=use_realtime)
        if pl_oracle.get("schema") != PLASTICITY2_SCHEMA_V1 or pl_cand.get("schema") != PLASTICITY2_SCHEMA_V1:
            raise LoadError("Unexpected plasticity2 report schema")

        # Metric diffs under the same absolute tolerance (conservative default)
        rec_mo = rec_oracle.get("metrics", {}) if isinstance(rec_oracle.get("metrics"), dict) else {}
        rec_mc = rec_cand.get("metrics", {}) if isinstance(rec_cand.get("metrics"), dict) else {}

        rec_diffs = {
            "D_peak_abs": _metric_abs_diff(rec_mo.get("D_peak"), rec_mc.get("D_peak")),
            "t_peak_hours_abs": _metric_abs_diff(rec_mo.get("t_peak_hours"), rec_mc.get("t_peak_hours")),
            "t_recover_80_hours_abs": _metric_abs_diff(rec_mo.get("t_recover_80_hours"), rec_mc.get("t_recover_80_hours")),
        }
        rec_ok = all((d is None or d <= float(tolerance_abs)) for d in rec_diffs.values())

        pl_mo = pl_oracle.get("metrics", {}) if isinstance(pl_oracle.get("metrics"), dict) else {}
        pl_mc = pl_cand.get("metrics", {}) if isinstance(pl_cand.get("metrics"), dict) else {}
        pl_diffs = {
            "auc_D_abs": _metric_abs_diff(pl_mo.get("auc_D"), pl_mc.get("auc_D")),
            "mean_R_abs": _metric_abs_diff(pl_mo.get("mean_R"), pl_mc.get("mean_R")),
            "mean_C_abs": _metric_abs_diff(pl_mo.get("mean_C"), pl_mc.get("mean_C")),
        }
        pl_ok = all((d is None or d <= float(tolerance_abs)) for d in pl_diffs.values())

        within = bool(score_ok and rec_ok and pl_ok)
        if within:
            ok_count += 1

        recipes_out.append(
            {
                "recipe": rid,
                "kind": recipe.kind,
                "timepoints": tps_out,
                "recovery": {
                    "oracle": {
                        "schema": rec_oracle.get("schema"),
                        "evidence_hash": rec_oracle.get("provenance", {}).get("evidence_hash"),
                        "metrics": rec_mo,
                    },
                    "candidate": {
                        "schema": rec_cand.get("schema"),
                        "evidence_hash": rec_cand.get("provenance", {}).get("evidence_hash"),
                        "metrics": rec_mc,
                    },
                    "metric_diffs": rec_diffs,
                    "within_tolerance": bool(rec_ok),
                },
                "plasticity2": {
                    "oracle": {
                        "schema": pl_oracle.get("schema"),
                        "evidence_hash": pl_oracle.get("provenance", {}).get("evidence_hash"),
                        "metrics": pl_mo,
                    },
                    "candidate": {
                        "schema": pl_cand.get("schema"),
                        "evidence_hash": pl_cand.get("provenance", {}).get("evidence_hash"),
                        "metrics": pl_mc,
                    },
                    "metric_diffs": pl_diffs,
                    "within_tolerance": bool(pl_ok),
                },
                "within_tolerance": within,
            }
        )

    evidence_hash = sha256_c14n_json(
        {
            "manifest": manifest_obj,
            "oracle_scores": oracle_scores,
            "candidate_scores": cand_scores,
            "contracts": contracts,
            "tolerance_abs": float(tolerance_abs),
            "tool": tool_name,
        }
    )

    report: Dict[str, Any] = {
        "schema": TOOL_AUDIT_SCHEMA_V1,
        "provenance": {
            "tool_version": VERSION,
            "created_utc": stable_utc_now_iso(use_realtime=use_realtime),
            "evidence_hash": evidence_hash,
        },
        "tool": {"name": tool_name},
        "contracts": {"suite": contracts, "recipes": suite},
        "manifest": {
            "ref": str(manifest_path).replace("\\", "/"),
            "subject_id": manifest_obj.get("subject_id"),
            "baseline_label": baseline.label,
            "post_labels": [tp.label for tp in posts],
            "hash": sha256_c14n_json(manifest_obj),
        },
        "tolerance_abs": float(tolerance_abs),
        "recipes": recipes_out,
        "summary": {
            "recipes_total": len(suite),
            "recipes_within_tolerance": int(ok_count),
            "within_tolerance": bool(ok_count == len(suite)),
        },
    }

    # Normalize for cross-platform golden stability (float quantization + -0.0 collapse).
    report = normalize_json(report)

    emit_report.parent.mkdir(parents=True, exist_ok=True)
    emit_report.write_text(
        __import__("json").dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
