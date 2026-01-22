# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal

from ..util import stable_utc_now_iso


RecipeKind = Literal["labs", "wearable"]


@dataclass(frozen=True)
class RecipeSpec:
    recipe_id: str
    kind: RecipeKind
    expected_units: Dict[str, str]
    runner: Callable[[Dict[str, Any]], Any]


def _load() -> Dict[str, RecipeSpec]:
    from . import inflammation_score_v1, metabolic_score_v1, circadian_score_v1

    return {
        inflammation_score_v1.RECIPE_ID: RecipeSpec(
            recipe_id=inflammation_score_v1.RECIPE_ID,
            kind="labs",
            expected_units=dict(inflammation_score_v1.EXPECTED_UNITS),
            runner=inflammation_score_v1.run,
        ),
        metabolic_score_v1.RECIPE_ID: RecipeSpec(
            recipe_id=metabolic_score_v1.RECIPE_ID,
            kind="labs",
            expected_units=dict(metabolic_score_v1.EXPECTED_UNITS),
            runner=metabolic_score_v1.run,
        ),
        circadian_score_v1.RECIPE_ID: RecipeSpec(
            recipe_id=circadian_score_v1.RECIPE_ID,
            kind="wearable",
            expected_units=dict(circadian_score_v1.EXPECTED_UNITS),
            runner=circadian_score_v1.run,
        ),
    }


_RECIPES = _load()


RECIPES_INDEX_SCHEMA_V1 = "semiocore.biomed.recipes_index.v1"


def list_recipes() -> Dict[str, RecipeSpec]:
    return dict(_RECIPES)


def get_recipe(recipe_id: str) -> RecipeSpec:
    if recipe_id not in _RECIPES:
        raise KeyError(f"Unknown recipe: {recipe_id}")
    return _RECIPES[recipe_id]


def recipe_index(*, tool_version: str, use_realtime: bool = False) -> Dict[str, Any]:
    """Build a deterministic recipes index for CLI and audits."""

    recipes = []
    for rid in sorted(_RECIPES):
        spec = _RECIPES[rid]
        recipes.append(
            {
                "recipe_id": spec.recipe_id,
                "kind": spec.kind,
                "expected_units": dict(spec.expected_units),
            }
        )

    return {
        "schema": RECIPES_INDEX_SCHEMA_V1,
        "provenance": {
            "tool_version": tool_version,
            "created_utc": stable_utc_now_iso(use_realtime=use_realtime),
        },
        "recipes": recipes,
    }
