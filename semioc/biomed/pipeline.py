# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from .. import VERSION
from ..io.load import LoadError, assert_units, find_repo_root, labs_units_view, load_and_validate, wearable_units_view
from ..util import json_c14n
from ..recipes.registry import get_recipe
from .artifacts import make_score_artifact


def score(
    *,
    recipe_id: str,
    input_path: str,
    output_path: str,
    repo_root: Optional[str] = None,
    use_realtime: bool = False,
) -> None:
    """Compute a score artifact from a raw payload.

    The units policy is strict: recipes declare expected units, and inputs must
    match exactly. No conversions are performed at this layer.
    """

    repo = find_repo_root(Path(repo_root)) if repo_root else find_repo_root(Path(input_path).resolve().parent)

    payload = load_and_validate(Path(input_path), repo=repo)
    recipe = get_recipe(recipe_id)

    if recipe.kind == "labs":
        assert_units(labs_units_view(payload), recipe.expected_units, context=f"recipe={recipe_id}")
    elif recipe.kind == "wearable":
        assert_units(wearable_units_view(payload), recipe.expected_units, context=f"recipe={recipe_id}")
    else:
        raise LoadError(f"Unsupported recipe kind: {recipe.kind}")

    result_obj = recipe.runner(payload).to_dict()  # type: ignore[attr-defined]
    artifact = make_score_artifact(
        tool_version=VERSION,
        input_payload=payload,
        result=result_obj,
        use_realtime=use_realtime,
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    Path(output_path).write_text(json_c14n(artifact) + "\n", encoding="utf-8")
