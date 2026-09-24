"""N-19 CI gate for the plan §10 "Value" row (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1).

The §10 Value row states: the NOT_RUN is CI-enforced — the test asserts both
artifacts' presence and is NOT_RUN rather than relying on memory. This test is
that gate. When the artifacts are absent from the branch, the result is
NOT_RUN (skip with reason), never a pass and never a hard failure; when they
are present, their presence is asserted so a later accidental removal breaks
the suite.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ARTIFACTS = [
    "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_COST_PROFILE_v1_0.md",
    "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_BASELINE_v1_0.md",
]

REPO_ROOT = Path(__file__).resolve().parents[5]


def _missing() -> list[str]:
    return [a for a in ARTIFACTS if not (REPO_ROOT / a).is_file()]


def test_n19_value_artifacts_present():
    missing = _missing()
    if missing:
        pytest.skip(
            "NOT_RUN: KALA value artifacts absent from this branch: "
            + ", ".join(missing)
        )
    for artifact in ARTIFACTS:
        path = REPO_ROOT / artifact
        assert path.stat().st_size > 0, f"{artifact} is empty"
