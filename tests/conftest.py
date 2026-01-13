"""Pytest configuration.

This repository is usually exercised as an installed package.
For repository-local test runs (e.g. `pytest`), ensure the repository root
is on sys.path.

This file is intentionally minimal.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
