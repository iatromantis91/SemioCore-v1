from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..util import sha256_c14n_json, stable_utc_now_iso


SCORE_SCHEMA_V1 = "semiocore.biomed.score.v1"


@dataclass(frozen=True)
class Provenance:
    tool_version: str
    created_utc: str
    input_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_version": self.tool_version,
            "created_utc": self.created_utc,
            "input_hash": self.input_hash,
        }


def make_score_artifact(
    *,
    tool_version: str,
    input_payload: Dict[str, Any],
    result: Dict[str, Any],
    use_realtime: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wrap a recipe output into a stable, auditable artifact."""

    prov = Provenance(
        tool_version=tool_version,
        created_utc=stable_utc_now_iso(use_realtime=use_realtime),
        input_hash=sha256_c14n_json(input_payload),
    )

    out: Dict[str, Any] = {
        "schema": SCORE_SCHEMA_V1,
        "provenance": prov.to_dict(),
        "input_schema": input_payload.get("schema"),
        "recipe": result.get("recipe"),
        "score": result.get("score"),
        "features": result.get("features"),
        "qc": result.get("qc"),
        "details": result.get("details", {}),
    }
    if extra:
        out["extra"] = dict(extra)
    return out
