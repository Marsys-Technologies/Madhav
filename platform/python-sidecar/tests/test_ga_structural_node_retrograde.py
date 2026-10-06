"""N-185 (TI-ga-node-retro-readers-001): the mean-node retrograde FLAG is a fact; three RULES keyed on it exclude the nodes.

Ruling: `is_retrograde = true` for Rahu/Ketu everywhere it is a stored or rolled-up fact (ga_positions
`retrograde_flag`, ga_structural `graha_special_state_rollup.is_retrograde`, ga_condition_composite via the stored
flag). The three derivations keyed on "retrograde" are defined for the five tara-grahas (Mars..Saturn):
aspect halving (`retrograde_aspect_modification`), the retrograde branch of the deepta avastha, and the composite-
state downgrade. Rahu/Ketu are EXCLUDED from those three (always retrograde: not a distinguishing condition;
rule-scope ruling on the owner's acharya-check list). Net row effect of the whole node-retrograde pass in
ga_structural: ONLY `is_retrograde` false->true for the nodes; no node rows in retrograde_aspect_modification;
node deepta/classification unchanged; the five tara-grahas unchanged.

The engine adapter now reports retrograde=True for the mean nodes at source (pyjhora_adapter/positions.py), so
ga_structural reads the corrected flag straight from chart_output (no wrapper). No database. Real-engine tests
need the pinned .se1 files (SE_EPHE_PATH) and skip visibly without them.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ga_writers import ga_positions_writer as gpw
from ga_writers import ga_structural_writer as gsw

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AY = "lahiri_chitrapaksha"

# name, sign, sign_id, house, longitude, retro (engine channel, post-adapter-fix), dignity
_BASE_ROWS = [
    ("Sun", "Capricorn", 10, 9, 291.0, False, "neutral"),
    ("Moon", "Aquarius", 11, 10, 324.0, False, "neutral"),
    ("Mars", "Scorpio", 8, 7, 220.0, False, "neutral"),
    ("Mercury", "Sagittarius", 9, 8, 255.0, False, "neutral"),
    ("Jupiter", "Libra", 7, 6, 190.0, False, "neutral"),
    ("Venus", "Sagittarius", 9, 8, 262.0, False, "neutral"),
    ("Saturn", "Libra", 7, 6, 195.0, False, "exalted"),
    ("Rahu", "Taurus", 2, 2, 40.0, False, "neutral"),
    ("Ketu", "Scorpio", 8, 8, 220.0, False, "neutral"),
]
TARA = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _chart_output(retro: dict[str, bool]) -> dict:
    return {
        "ascendant": {"sign": "Aries", "sign_id": 1, "longitude_deg": 5.0},
        "grahas": [
            {"name": n, "sign": s, "sign_id": sid, "house": h, "longitude": lon, "longitude_deg": lon,
             "retrograde": retro.get(n, r), "dignity_status": d, "combust": False}
            for (n, s, sid, h, lon, r, d) in _BASE_ROWS
        ],
    }


# the engine channel as it is AFTER the adapter fix: nodes True, plus every tara-graha retrograde in the stress case
NODES_ONLY = _chart_output({"Rahu": True, "Ketu": True})
NODES_AND_TARA = _chart_output({"Rahu": True, "Ketu": True, **{n: True for n in TARA}})
# the pre-fix engine channel (nodes False) for the 'unchanged for the nodes' comparison
PRE_FIX = _chart_output({})


def _rows(fn, chart_output, **kw):
    return fn(chart_output, CHART_ID, "b", AY, "2026-10-07T00:00:00+00:00", "eng", **kw)


def _vals(rows: list[dict], category: str, key: str) -> dict[str, str]:
    return {r["fact_subject"]: r["fact_value_text"] for r in rows
            if r["fact_category"] == category and r["fact_key"] == key}


NODE_SUBJECTS = ("RAH_MEAN", "KET_MEAN")


# ── the flag itself is a fact: rollup is_retrograde is true for the nodes ───────────────────────────────────

def test_rollup_is_retrograde_is_true_for_the_nodes_and_matches_the_stored_flag():
    rows = _rows(gsw._build_special_state_rows, NODES_AND_TARA, conn=None)
    flags = _vals(rows, "graha_special_state_rollup", "is_retrograde")
    assert flags["RAH_MEAN"] == "true" and flags["KET_MEAN"] == "true"
    assert flags["MAR"] == "true" and flags["SUN"] == "false"
    pos = gpw._build_position_rows(NODES_AND_TARA, CHART_ID, "b", AY, "lahiri", "2026-10-07T00:00:00+00:00")
    stored = {r["fact_subject"]: r["fact_value_text"] for r in pos if r["fact_key"] == "retrograde_flag"}
    for subj, v in flags.items():
        if subj in stored:
            assert (v == "true") == (stored[subj] == "retrograde"), subj


# ── the three rules exclude the nodes ───────────────────────────────────────────────────────────────────────

def test_node_deepta_state_is_unchanged_by_the_node_retrograde_flag():
    pre = _vals(_rows(gsw._build_avastha_rows, PRE_FIX), "graha_avastha_deepta", "deepta_state")
    post = _vals(_rows(gsw._build_avastha_rows, NODES_ONLY), "graha_avastha_deepta", "deepta_state")
    assert post == pre
    assert post["RAH_MEAN"] == "dina" and post["KET_MEAN"] == "dina"      # house 2 / 8, neutral, NOT vikala


def test_node_composite_classification_is_unchanged_by_the_node_retrograde_flag():
    pre = _vals(_rows(gsw._build_structural_relationship_rows, PRE_FIX, conn=None),
                "graha_composite_state_classification", "classification")
    post = _vals(_rows(gsw._build_structural_relationship_rows, NODES_ONLY, conn=None),
                 "graha_composite_state_classification", "classification")
    assert post == pre
    assert post["RAH_MEAN"] == "neutral" and post["KET_MEAN"] == "neutral"  # NOT weak


def test_nodes_are_absent_from_retrograde_aspect_modification():
    rows = _rows(gsw._build_combustion_retrograde_relationship_rows, NODES_AND_TARA)
    subjects = {r["fact_subject"] for r in rows if r["fact_category"] == "retrograde_aspect_modification"}
    assert subjects and not any(s.startswith(("RAH", "KET")) for s in subjects), subjects
    assert subjects == {"MAR_retro", "MER_retro", "JUP_retro", "VEN_retro", "SAT_retro"}


def test_the_five_tara_grahas_keep_every_retrograde_rule():
    """Control: a retrograde tara-graha still halves its aspects, reads vikala outside kendra/trikona and is downgraded."""
    out = NODES_AND_TARA
    asp = _rows(gsw._build_combustion_retrograde_relationship_rows, out)
    per_subject = {}
    for r in asp:
        if r["fact_category"] == "retrograde_aspect_modification":
            per_subject.setdefault(r["fact_subject"], []).append(r)
    from brahmagyan.aspects import get_graha_aspects
    for subj, full in {"MAR_retro": "Mars", "MER_retro": "Mercury", "JUP_retro": "Jupiter", "VEN_retro": "Venus",
                       "SAT_retro": "Saturn"}.items():
        assert len(per_subject[subj]) == len(get_graha_aspects(full)), subj      # one row per aspect, as before
    assert all(r["fact_value_jsonb"]["modified_strength"] == round(r["fact_value_jsonb"]["base_strength"] * 0.5, 4)
               for v in per_subject.values() for r in v)
    deepta = _vals(_rows(gsw._build_avastha_rows, out), "graha_avastha_deepta", "deepta_state")
    assert deepta["MER"] == "vikala" and deepta["VEN"] == "vikala"     # H8, neutral, retro
    comp = _vals(_rows(gsw._build_structural_relationship_rows, out, conn=None),
                 "graha_composite_state_classification", "classification")
    assert comp["MER"] == "weak" and comp["VEN"] == "weak" and comp["JUP"] == "weak"
    assert comp["SAT"] == "well_placed"                                # exalted wins before the retro branch


def test_only_is_retrograde_changes_for_the_nodes_and_no_fact_id_or_row_set_changes():
    for builder, kw in ((gsw._build_special_state_rows, {"conn": None}), (gsw._build_avastha_rows, {}),
                        (gsw._build_structural_relationship_rows, {"conn": None}),
                        (gsw._build_combustion_retrograde_relationship_rows, {})):
        a, b = _rows(builder, PRE_FIX, **kw), _rows(builder, NODES_ONLY, **kw)
        assert [r["fact_id"] for r in a] == [r["fact_id"] for r in b], builder.__name__
        changed = [(x["fact_category"], x["fact_subject"], x["fact_key"]) for x, y in zip(a, b)
                   if (x["fact_value_text"], x["fact_value_num"], str(x["fact_value_jsonb"]))
                   != (y["fact_value_text"], y["fact_value_num"], str(y["fact_value_jsonb"]))]
        for c in changed:
            assert c[0] == "graha_special_state_rollup" and c[2] == "is_retrograde" and c[1] in NODE_SUBJECTS, (builder.__name__, c)
        if builder is gsw._build_special_state_rows:
            assert len(changed) == 2


def test_the_exclusion_uses_one_node_set_shared_with_ga_positions():
    assert gsw._MEAN_NODE_GRAHA_NAMES == gpw.MEAN_NODE_GRAHA_NAMES == frozenset({"Rahu", "Ketu"})


def test_the_exclusion_is_commented_with_the_ruling_at_each_rule_site():
    from pathlib import Path
    src = Path(gsw.__file__).read_text(encoding="utf-8").splitlines()
    sites = [l for l in src if "_MEAN_NODE_GRAHA_NAMES" in l and ("elif retro" in l or "if not retro" in l)]
    assert len(sites) == 3, sites
    assert all("N-185" in l and "always retrograde" in l for l in sites), sites


# ── real engine: native chart, all five ayanamshas ────────────────────────────────────────────────────────────

_BP = {"datetime_iso": "1984-02-05T10:43:00", "tz_offset_hours": 5.5, "latitude_deg": 20.2961,
       "longitude_deg": 85.8245, "place_name": "Bhubaneswar", "subject_label": "native"}


def _se1_available() -> bool:
    return bool(os.environ.get("SE_EPHE_PATH")) and os.path.isdir(os.environ["SE_EPHE_PATH"])


@pytest.mark.skipif(not _se1_available(), reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_real_engine_native_rollup_true_for_nodes_rules_unchanged_all_five_ayanamshas():
    from pyjhora_adapter.compute import compute_chart

    seen = 0
    for canonical, adapter_id in gpw.CANONICAL_AYANAMSHAS.items():
        out = compute_chart(inputs=_BP, ayanamsha_id=adapter_id)
        assert {g["name"]: g["retrograde"] for g in out["grahas"] if g["name"] in ("Rahu", "Ketu")} == \
            {"Rahu": True, "Ketu": True}, canonical
        roll = _vals(_rows(gsw._build_special_state_rows, out, conn=None), "graha_special_state_rollup", "is_retrograde")
        deepta = _vals(_rows(gsw._build_avastha_rows, out), "graha_avastha_deepta", "deepta_state")
        comp = _vals(_rows(gsw._build_structural_relationship_rows, out, conn=None),
                     "graha_composite_state_classification", "classification")
        asp = {r["fact_subject"] for r in _rows(gsw._build_combustion_retrograde_relationship_rows, out)
               if r["fact_category"] == "retrograde_aspect_modification"}
        for subj in NODE_SUBJECTS:
            assert roll[subj] == "true", (canonical, subj)
            assert deepta[subj] == "dina" and comp[subj] == "neutral", (canonical, subj)   # production values today
            seen += 1
        assert not any(s.startswith(("RAH", "KET")) for s in asp), (canonical, asp)
    assert seen == 10
