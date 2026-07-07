"""test_ga_condition_jl026_graha_yuddha.py — JL-026 (2026-07-07).

ga_condition must NOT emit the `graha_yuddha` chart_facts category. ga_structural
(_build_graha_yuddha_rows, two_pass_verified) is its sole authoritative writer.
Emitting it here too was the third ga_structural↔ga_condition dual-write: identical
delete scope (chart_id, 'graha_yuddha', ayanamsha_id) → parallel clobber/deadlock,
which the migration-416 edge papered over. This guard mirrors the JL-022 structural-
side test (test_ga8_writer.test_lajjitadi_and_sayanadi_owned_by_ga_condition_not_emitted_here).

DB-free: monkeypatch _load_graha_positions to inject a genuine graha-yuddha pair
(Mars + Saturn within 1° in the same sign) and assert _build_d1_avastha_rows emits
avastha rows but NO 'graha_yuddha' category row.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_writer as sut  # noqa: E402

CHART_ID = "test-chart"
BUILD_ID = "test-build"
AY_ID = "lahiri"
COMPUTED_AT = "2026-07-07T00:00:00Z"
ENG_VER = "test-eng"

# Mars + Saturn: same sign, 0.5° apart → graha yuddha pair. Sun elsewhere.
_MOCK_POSITIONS = [
    {"graha": "Mars",   "sign": "Aries", "degree_in_sign": 10.0, "longitude": 10.0,  "house": 1, "is_retrograde": False, "speed": 0.5},
    {"graha": "Saturn", "sign": "Aries", "degree_in_sign": 10.5, "longitude": 10.5,  "house": 1, "is_retrograde": False, "speed": 0.1},
    {"graha": "Sun",    "sign": "Leo",   "degree_in_sign": 15.0, "longitude": 135.0, "house": 5, "is_retrograde": False, "speed": 1.0},
]


def test_ga_condition_does_not_emit_graha_yuddha_category(monkeypatch):
    monkeypatch.setattr(sut, "_load_graha_positions", lambda conn, cid, ay: _MOCK_POSITIONS)

    rows = sut._build_d1_avastha_rows(
        None, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER
    )
    cats = {r["fact_category"] for r in rows}

    # The dual-write is gone:
    assert "graha_yuddha" not in cats, (
        "ga_condition must not emit the graha_yuddha category (JL-026) — "
        "ga_structural is its sole authoritative writer."
    )
    # Sanity: it still does its real job (avastha rows present):
    assert "graha_avastha_sayanadi" in cats
    assert "graha_avastha_lajjitadi" in cats
