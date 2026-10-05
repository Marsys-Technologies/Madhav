"""S-L2 LAKSANA-COLLISION: post-S-L1 chart_facts carry their natural key in the
fact_subject / formula_id COLUMNS (fact_value_jsonb is NULL), so the signal config must
carry them or distinct facts collapse onto one deterministic identity (production
1c03ec17: 14,999 of 25,268 lahiri rows). Natural key, never a random row id."""
from __future__ import annotations

import json

from pipeline.orchestrator.writers import bo_laksana as bo

_NOW = "2026-10-05T00:00:00+00:00"


def _fact(fid, cat, key, subject, num=0.0, formula=None, aya="lahiri_chitrapaksha", fvj=None, text=None):
    return {"fact_id": fid, "fact_category": cat, "fact_key": key, "fact_subject": subject,
            "fact_value_text": text, "fact_value_num": num, "ayanamsha_id": aya,
            "source_calculation": "x", "formula_id": formula, "fact_value_jsonb": fvj}


def _cfg(f):
    row = bo._build_signal_row(f, "chart-1", "b1", {}, {}, {}, _NOW, valid_fact_ids={f["fact_id"]})
    return row, json.loads(row["configuration_jsonb"])


def _identity_key(row, cfg):
    return json.dumps([row["ayanamsha_id"], row["signal_type_id"], row["varga_id"], cfg], sort_keys=True)


def test_facts_distinguished_only_by_fact_subject_stay_distinct():
    a = _cfg(_fact("a", "argala_natal_matrix", "from_sign_10_offset_1", "D30_SIGN_10"))
    b = _cfg(_fact("b", "argala_natal_matrix", "from_sign_10_offset_1", "D1_SIGN_10"))
    assert _identity_key(*a) != _identity_key(*b)
    assert a[1]["fact_subject"] == "D30_SIGN_10"


def test_facts_distinguished_only_by_formula_id_stay_distinct():
    a = _cfg(_fact("a", "karaka_chara_position", "k", "SUN", formula="kn_rao_rahu_included"))
    b = _cfg(_fact("b", "karaka_chara_position", "k", "SUN", formula="parashari_rahu_excluded"))
    assert _identity_key(*a) != _identity_key(*b)


def test_no_subject_no_formula_adds_no_key():
    _, cfg = _cfg(_fact("a", "x_cat", "k", None))
    assert "fact_subject" not in cfg and "l1_formula_id" not in cfg


def test_aggregate_rollup_carries_no_arbitrary_member_subject():
    members = [_fact(f"m{i}", "ashtakavarga_bindu_per_varga", "D10", f"SAT-HOUSE_{i}") for i in range(3)]
    agg = bo._make_aggregate_fact_row(members, "D10")
    _, cfg = _cfg(agg)
    assert "fact_subject" not in cfg and cfg["aggregated"] is True


def test_invariant_twin_with_same_value_is_folded_and_still_cited():
    aya = [_fact("a1", "bhadra_flag", "active_at_birth_flag", "BHADRA_FLAG_BIRTH", num=None, text="false")]
    inv = [_fact("i1", "bhadra_flag", "active_at_birth_flag", "BHADRA_FLAG_BIRTH", num=None, text="false",
                 aya="INVARIANT")]
    out, folded = bo._merge_invariant_shadowed_duplicates(aya, inv)
    assert folded == 1 and len(out) == 1
    row, _ = _cfg(out[0])
    assert set(row["constituent_facts_array"]) >= {"a1"}
    row2 = bo._build_signal_row(out[0], "c", "b", {}, {}, {}, _NOW, valid_fact_ids={"a1", "i1"})
    assert row2["constituent_facts_array"] == ["a1", "i1"]


def test_invariant_twin_with_different_value_or_subject_is_kept():
    aya = [_fact("a1", "c", "k", "S", num=1.0)]
    out, folded = bo._merge_invariant_shadowed_duplicates(
        aya, [_fact("i1", "c", "k", "S", num=2.0, aya="INVARIANT"),
              _fact("i2", "c", "k", "OTHER", num=1.0, aya="INVARIANT")])
    assert folded == 0 and len(out) == 3
