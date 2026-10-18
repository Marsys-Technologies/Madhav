"""Portable, hash-pinned 3.0 comparison oracles consumed by PR #2923's tests.

The inputs are the archived campaign artifacts, never a synthesized substitute.
Missing or modified files fail the consuming tests; CI needs no personal checkout.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

CAMPAIGN_MEASUREMENT = Path(__file__).resolve().parent / "fixtures" / "candidate_3_0"
REGISTRY_V2_3 = CAMPAIGN_MEASUREMENT / "event_registry_v2_3.json"
CONTROLS_V1_3 = CAMPAIGN_MEASUREMENT / "random_controls_v1_3.json"
EXTRACT_3_0 = CAMPAIGN_MEASUREMENT / "baseline_3_0_extract_v1_0.json"
EXTRACT_3_0_PIN = "70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff"
requires_pinned_oracles = pytest.mark.usefixtures("pinned_candidate_oracles")


@pytest.fixture(scope="module")
def pinned_candidate_oracles():
    index = json.loads((CAMPAIGN_MEASUREMENT / "SOURCE_INDEX.json").read_text())
    for entry in index["files"]:
        file = CAMPAIGN_MEASUREMENT / entry["file"]
        assert hashlib.sha256(file.read_bytes()).hexdigest() == entry["sha256"], f"candidate oracle bytes changed: {file.name}"
