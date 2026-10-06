"""TI-ga-node-retro-readers-001 -- ga_structural must agree with ga_positions on the mean-node retrograde flag.

Context: TI-ga-positions-node-retro-001 (#3205) makes ga_positions store `retrograde_flag = retrograde` for the
MEAN nodes Rahu/Ketu. ga_structural takes the flag from a SEPARATE channel (the engine's `chart_output`, whose
`planets_in_retrograde` list excludes the mean nodes), so without this follow-up its
`graha_special_state_rollup.is_retrograde` stays `false` for the nodes and disagrees with the stored
graha_position fact, and the two other retrograde-reading families (graha_avastha_deepta, graha_composite_state_
classification) are computed from the wrong state.

Single fix point: ga_structural normalises the engine's chart_output right where it obtains it (both
`compute_chart` call sites), with the SAME helper ga_positions uses (`_is_retrograde`). Consequence: the
`retrograde_aspect_modification` family (which its own tests always expected to emit Rahu/Ketu rows) now does:
30 new rows per chart (3 aspects x 2 nodes x 5 ayanamshas); every existing fact_id is unchanged.

No database. The real-engine test needs the pinned .se1 files (SE_EPHE_PATH) and skips visibly without them.
"""
from __future__ import annotations

import copy
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ga_writers import ga_positions_writer as gpw
from ga_writers import ga_structural_writer as gsw

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AY = "lahiri_chitrapaksha"

# name, sign, sign_id, house, longitude, retro(engine channel), dignity
_ROWS = [
    ("Sun", "Capricorn", 10, 9, 291.0, False, "neutral"),
    ("Moon", "Aquarius", 11, 10, 324.0, False, "neutral"),
    ("Mars", "Scorpio", 8, 7, 220.0, True, "own_sign"),      # retrograde classical graha (control)
    ("Mercury", "Sagittarius", 9, 8, 255.0, False, "neutral"),
    ("Jupiter", "Libra", 7, 6, 190.0, False, "neutral"),
    ("Venus", "Sagittarius", 9, 8, 262.0, False, "neutral"),
    ("Saturn", "Libra", 7, 6, 195.0, False, "exalted"),
    ("Rahu", "Taurus", 2, 2, 40.0, False, "neutral"),         # engine channel says direct: the defect
    ("Ketu", "Scorpio", 8, 8, 220.0, False, "neutral"),
]


def _chart_output() -> dict:
    return {
        "ascendant": {"sign": "Aries", "sign_id": 1, "longitude_deg": 5.0},
        "grahas": [
            {"name": n, "sign": s, "sign_id": sid, "house": h, "longitude": lon, "longitude_deg": lon,
             "retrograde": r, "dignity_status": d, "combust": False}
            for (n, s, sid, h, lon, r, d) in _ROWS
        ],
    }


def _rows(fn, chart_output, *args, **kw):
    return fn(chart_output, CHART_ID, "b", AY, "2026-10-07T00:00:00+00:00", "eng", *args, **kw)


def _by_subject(rows: list[dict], category: str, key: str | None = None) -> dict[str, str]:
    return {r["fact_subject"]: r["fact_value_text"] for r in rows
            if r["fact_category"] == category and (key is None or r["fact_key"] == key)}


# ── the helper ──────────────────────────────────────────────────────────────────────────────────────────────

def test_helper_makes_exactly_the_mean_nodes_retrograde_and_does_not_mutate_its_input():
    original = _chart_output()
    snapshot = copy.deepcopy(original)
    fixed = gsw._with_mean_node_retrograde(original)
    assert original == snapshot, "the engine's chart_output must not be mutated"
    by_name = {g["name"]: g["retrograde"] for g in fixed["grahas"]}
    assert by_name["Rahu"] is True and by_name["Ketu"] is True
    assert by_name["Mars"] is True                           # unchanged adapter flag
    for n in ("Sun", "Moon", "Mercury", "Jupiter", "Venus", "Saturn"):
        assert by_name[n] is False, n                         # every other graha keeps the adapter flag
    assert fixed["ascendant"] == original["ascendant"]


def test_helper_uses_the_same_node_set_and_rule_as_ga_positions():
    assert gsw._MEAN_NODE_GRAHA_NAMES == gpw.MEAN_NODE_GRAHA_NAMES == frozenset({"Rahu", "Ketu"})
    for g in _chart_output()["grahas"]:
        fixed = gsw._with_mean_node_retrograde({"grahas": [g]})["grahas"][0]
        assert fixed["retrograde"] is gpw._is_retrograde(g), g["name"]


# ── both compute_chart call sites go through the helper (behavioural, no DB) ───────────────────────────────────

class _Stop(Exception):
    pass


def _capture_chart_output_at_validation(monkeypatch):
    seen: dict = {}

    def _validate(chart_output):
        seen["chart_output"] = chart_output
        raise _Stop

    monkeypatch.setattr(gsw, "compute_chart", lambda inputs, ayanamsha_id: _chart_output())
    monkeypatch.setattr(gsw, "_validate_chart_output_complete", _validate)
    return seen


_BP = {"datetime_iso": "1984-02-05T10:43:00", "tz_offset_hours": 5.5, "latitude_deg": 20.2961,
       "longitude_deg": 85.8245, "place_name": "Bhubaneswar", "subject_label": "native"}


def _node_flags(chart_output: dict) -> dict[str, bool]:
    return {g["name"]: g["retrograde"] for g in chart_output["grahas"] if g["name"] in ("Rahu", "Ketu")}


def test_substep_path_hands_the_corrected_flag_to_every_family(monkeypatch):
    seen = _capture_chart_output_at_validation(monkeypatch)
    with pytest.raises(_Stop):
        gsw.build_ga_structural_substep(CHART_ID, "b", "lahiri_chitrapaksha", None, birth_params=_BP)
    assert _node_flags(seen["chart_output"]) == {"Rahu": True, "Ketu": True}


def test_legacy_whole_chart_path_hands_the_corrected_flag_to_every_family(monkeypatch):
    seen = _capture_chart_output_at_validation(monkeypatch)
    monkeypatch.setattr(gsw, "_load_yoga_catalog", lambda c: [])
    monkeypatch.setattr(gsw, "_load_dosha_catalog", lambda c: [])

    class _Conn:
        def commit(self):
            pass

    with pytest.raises(_Stop):
        gsw.build_ga_structural(CHART_ID, "b", conn=_Conn(), birth_params=_BP, skip_upstream_check=True)
    assert _node_flags(seen["chart_output"]) == {"Rahu": True, "Ketu": True}


def test_no_compute_chart_call_in_ga_structural_bypasses_the_helper():
    src = Path(gsw.__file__).read_text(encoding="utf-8")
    calls = re.findall(r"^[^#\n]*\bcompute_chart\(", src, flags=re.M)
    assert calls, "expected compute_chart call sites"
    for line in calls:
        assert "_with_mean_node_retrograde(" in line, line.strip()


# ── the three families that read the flag now agree with the stored graha_position fact ───────────────────────

def test_rollup_is_retrograde_agrees_with_the_graha_position_fact_for_the_nodes():
    corrected = gsw._with_mean_node_retrograde(_chart_output())
    rows = _rows(gsw._build_special_state_rows, corrected, conn=None)
    flags = _by_subject(rows, "graha_special_state_rollup", "is_retrograde")
    assert flags["RAH_MEAN"] == "true" and flags["KET_MEAN"] == "true"
    assert flags["MAR"] == "true"                            # classical retrograde graha unchanged
    assert flags["SUN"] == "false" and flags["SAT"] == "false"
    # the stored fact the same chart_output yields through ga_positions' own builder
    pos = gpw._build_position_rows(corrected, CHART_ID, "b", AY, "lahiri", "2026-10-07T00:00:00+00:00")
    stored = {r["fact_subject"]: r["fact_value_text"] for r in pos if r["fact_key"] == "retrograde_flag"}
    for subj in ("RAH_MEAN", "KET_MEAN", "MAR", "SUN"):
        assert (flags[subj] == "true") == (stored[subj] == "retrograde"), subj


def test_without_the_helper_the_rollup_disagrees_with_the_stored_fact():
    """Documents the defect this PR closes: the raw engine channel says direct for the nodes."""
    rows = _rows(gsw._build_special_state_rows, _chart_output(), conn=None)
    flags = _by_subject(rows, "graha_special_state_rollup", "is_retrograde")
    assert flags["RAH_MEAN"] == "false" and flags["KET_MEAN"] == "false"


def test_deepta_and_composite_classification_follow_the_corrected_flag_for_nodes_only():
    raw, fixed = _chart_output(), gsw._with_mean_node_retrograde(_chart_output())
    d_raw = _by_subject(_rows(gsw._build_avastha_rows, raw), "graha_avastha_deepta", "deepta_state")
    d_fix = _by_subject(_rows(gsw._build_avastha_rows, fixed), "graha_avastha_deepta", "deepta_state")
    c_raw = _by_subject(_rows(gsw._build_structural_relationship_rows, raw, conn=None),
                        "graha_composite_state_classification", "classification")
    c_fix = _by_subject(_rows(gsw._build_structural_relationship_rows, fixed, conn=None),
                        "graha_composite_state_classification", "classification")
    # nodes: house 2 (Rahu) / 8 (Ketu), neutral dignity -> the written rules read retro
    assert (d_raw["RAH_MEAN"], d_fix["RAH_MEAN"]) == ("dina", "vikala")
    assert (d_raw["KET_MEAN"], d_fix["KET_MEAN"]) == ("dina", "vikala")
    assert (c_raw["RAH_MEAN"], c_fix["RAH_MEAN"]) == ("neutral", "weak")
    assert (c_raw["KET_MEAN"], c_fix["KET_MEAN"]) == ("neutral", "weak")
    # every other graha: identical value, identical subject set (no row added or removed)
    assert set(d_raw) == set(d_fix) and set(c_raw) == set(c_fix)
    for subj in set(d_raw) - {"RAH_MEAN", "KET_MEAN"}:
        assert d_raw[subj] == d_fix[subj], subj
    for subj in set(c_raw) - {"RAH_MEAN", "KET_MEAN"}:
        assert c_raw[subj] == c_fix[subj], subj


def test_node_in_a_kendra_keeps_its_deepta_state_only_the_flag_changes():
    out = _chart_output()
    for g in out["grahas"]:
        if g["name"] == "Rahu":
            g["house"] = 4                                    # kendra -> 'mudita' before the retro branch
    fixed = gsw._with_mean_node_retrograde(out)
    assert _by_subject(_rows(gsw._build_avastha_rows, fixed), "graha_avastha_deepta", "deepta_state")["RAH_MEAN"] == "mudita"


def test_the_corrected_flag_changes_values_only_never_a_fact_id_or_the_row_set():
    raw, fixed = _chart_output(), gsw._with_mean_node_retrograde(_chart_output())
    for builder, kw in ((gsw._build_special_state_rows, {"conn": None}), (gsw._build_avastha_rows, {}),
                        (gsw._build_structural_relationship_rows, {"conn": None})):
        a = _rows(builder, raw, **kw)
        b = _rows(builder, fixed, **kw)
        assert [r["fact_id"] for r in a] == [r["fact_id"] for r in b], builder.__name__
        assert [(r["fact_category"], r["fact_subject"], r["fact_key"]) for r in a] == \
               [(r["fact_category"], r["fact_subject"], r["fact_key"]) for r in b], builder.__name__


# ── the retrograde aspect-modification family: node rows appear for the first time ─────────────────────────

def test_retrograde_aspect_modification_emits_the_node_rows_its_own_tests_always_expected():
    """The family halves the aspect strength of every retrograde graha (5th/7th/9th for the nodes). Its tests
    (test_ga8_writer, lane1 parity) have always expected Rahu/Ketu rows; production holds none because the engine
    flag was false for the nodes. With the corrected flag: 3 aspects x 2 nodes = 6 NEW rows per ayanamsha."""
    raw_rows = _rows(gsw._build_combustion_retrograde_relationship_rows, _chart_output())
    fixed_rows = _rows(gsw._build_combustion_retrograde_relationship_rows, gsw._with_mean_node_retrograde(_chart_output()))
    cat = "retrograde_aspect_modification"
    raw = [r for r in raw_rows if r["fact_category"] == cat]
    fixed = [r for r in fixed_rows if r["fact_category"] == cat]
    assert {r["fact_subject"] for r in raw} == {"MAR_retro"}
    assert {r["fact_subject"] for r in fixed} == {"MAR_retro", "RAH_MEAN_retro", "KET_MEAN_retro"}
    assert len(fixed) - len(raw) == 6
    assert {r["fact_id"] for r in raw} < {r["fact_id"] for r in fixed}     # existing ids untouched, new ones added
    assert [r for r in fixed_rows if r["fact_category"] != cat] == [r for r in raw_rows if r["fact_category"] != cat]


# ── real engine: native chart, all five ayanamshas ────────────────────────────────────────────────────────────

def _se1_available() -> bool:
    return bool(os.environ.get("SE_EPHE_PATH")) and os.path.isdir(os.environ["SE_EPHE_PATH"])


@pytest.mark.skipif(not _se1_available(), reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_real_engine_native_chart_rollup_agrees_with_ga_positions_for_all_ten_node_rows():
    from pyjhora_adapter.compute import compute_chart

    seen = 0
    for canonical, adapter_id in gpw.CANONICAL_AYANAMSHAS.items():
        raw = compute_chart(inputs=_BP, ayanamsha_id=adapter_id)
        fixed = gsw._with_mean_node_retrograde(raw)
        roll = _by_subject(_rows(gsw._build_special_state_rows, fixed, conn=None),
                           "graha_special_state_rollup", "is_retrograde")
        pos = gpw._build_position_rows(fixed, CHART_ID, "b", canonical, "x", "2026-10-07T00:00:00+00:00")
        stored = {r["fact_subject"]: r["fact_value_text"] for r in pos if r["fact_key"] == "retrograde_flag"}
        for subj in ("RAH_MEAN", "KET_MEAN"):
            assert roll[subj] == "true" and stored[subj] == "retrograde", (canonical, subj)
            seen += 1
        for subj in roll:                                     # every graha: rollup == stored fact
            assert (roll[subj] == "true") == (stored[subj] == "retrograde"), (canonical, subj)
    assert seen == 10
