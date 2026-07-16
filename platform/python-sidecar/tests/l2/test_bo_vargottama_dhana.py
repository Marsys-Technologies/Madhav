"""
Tests for bo_vargottama_dhana / bodha_writers.vargottama_dhana_emitter
(D-2 Lane V-5, CR-36).

TYPE SPECIMENS independently reproduced against chart 482012f1's real
lahiri_chitrapaksha facts (verified live via mcp__postgres__query before
writing this test):
  - Mercury IS vargottama in D9 (is_vargottama=1); all other 8 grahas are
    NOT vargottama in D9 on this chart/ayanamsha — the anti-vacuous-test
    guarantee for this class (exactly one real fired row).
  - LAGNA sign = Aries (0-indexed 0). House 2 -> Taurus (lord Venus).
    House 11 -> Aquarius (lord Saturn, classical rulership).
  - Rahu occupies house_d1=2 (tenants the dhana house); Moon occupies
    house_d1=11 (tenants the labha house).
"""
from __future__ import annotations

import json

from bodha_writers.vargottama_dhana_emitter import (
    GRAHAS,
    VARGOTTAMA_AMPLIFICATION_CLASS_PRIOR,
    DHANA_AXIS_CLASS_PRIOR,
    VARGOTTAMA_AMPLIFICATION_SIGNAL_TYPE_CLASS,
    DHANA_AXIS_SIGNAL_TYPE_CLASS,
    _SIGN_LORD,
    build_vargottama_rows,
    build_dhana_axis_rows,
)


def _pos(house=None, sign=None, fact_id="f0"):
    d = {}
    if house is not None:
        d["house_d1"] = {"num": house, "fact_id": fact_id + "_h"}
    if sign is not None:
        d["sign"] = {"text": sign, "fact_id": fact_id + "_s"}
    return d


# ── vargottama_amplification ──────────────────────────────────────────────

def test_vargottama_fires_only_for_true_graha():
    vargottama_facts = {
        "MER": {"is_vargottama": True, "fact_id": "fmer"},
        "SUN": {"is_vargottama": False, "fact_id": "fsun"},
        "MOON": {"is_vargottama": False, "fact_id": "fmoon"},
    }
    positions = {"MER": _pos(house=10, sign="Capricorn", fact_id="mer")}
    rows = build_vargottama_rows(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        vargottama_facts=vargottama_facts, positions=positions,
        now="2026-07-16T00:00:00+00:00",
    )
    assert len(rows) == 1
    assert rows[0]["signal_type_id"] == "vargottama_amplification:MER"
    assert rows[0]["signal_type_class"] == VARGOTTAMA_AMPLIFICATION_SIGNAL_TYPE_CLASS
    cfg = json.loads(rows[0]["configuration_jsonb"])
    assert cfg["is_vargottama"] is True
    assert rows[0]["valence"] == "benefic"


def test_vargottama_no_rows_when_none_true():
    vargottama_facts = {"SUN": {"is_vargottama": False, "fact_id": "f1"}}
    rows = build_vargottama_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        vargottama_facts=vargottama_facts, positions={}, now="2026-07-16T00:00:00+00:00",
    )
    assert rows == []


def test_vargottama_class_prior_ratified():
    assert VARGOTTAMA_AMPLIFICATION_CLASS_PRIOR == 1.15


# ── dhana_axis ───────────────────────────────────────────────────────────

def test_dhana_axis_type_specimen_aries_lagna():
    positions = {
        "LAGNA": _pos(house=1, sign="Aries", fact_id="lagna"),
        "RAH_MEAN": _pos(house=2, sign="Taurus", fact_id="rah"),
        "MOON": _pos(house=11, sign="Aquarius", fact_id="moon"),
        "VEN": _pos(house=9, sign="Sagittarius", fact_id="ven"),
        "SAT": _pos(house=7, sign="Libra", fact_id="sat"),
    }
    rows = build_dhana_axis_rows(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        positions=positions, now="2026-07-16T00:00:00+00:00",
    )
    assert len(rows) == 2  # always 2 rows: H2 and H11
    h2 = next(r for r in rows if r["signal_type_id"] == "dhana_axis:H2")
    h11 = next(r for r in rows if r["signal_type_id"] == "dhana_axis:H11")

    cfg2 = json.loads(h2["configuration_jsonb"])
    assert cfg2["house_sign"] == "Taurus"
    assert cfg2["house_lord"] == "Venus"
    assert cfg2["occupants"] == ["Rahu"]
    assert cfg2["lord_own_house_placement"] == 9  # Venus itself sits in H9

    cfg11 = json.loads(h11["configuration_jsonb"])
    assert cfg11["house_sign"] == "Aquarius"
    assert cfg11["house_lord"] == "Saturn"
    assert cfg11["occupants"] == ["Moon"]
    assert cfg11["lord_own_house_placement"] == 7  # Saturn itself sits in H7

    assert h2["signal_type_class"] == DHANA_AXIS_SIGNAL_TYPE_CLASS == "dhana_axis"


def test_dhana_axis_untenanted_house_still_emits():
    positions = {"LAGNA": _pos(house=1, sign="Aries", fact_id="lagna")}
    rows = build_dhana_axis_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        positions=positions, now="2026-07-16T00:00:00+00:00",
    )
    assert len(rows) == 2
    for r in rows:
        cfg = json.loads(r["configuration_jsonb"])
        assert cfg["occupants"] == []
        assert r["valence"] == "neutral"


def test_dhana_axis_no_rows_without_lagna_sign():
    rows = build_dhana_axis_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        positions={}, now="2026-07-16T00:00:00+00:00",
    )
    assert rows == []


def test_dhana_axis_class_prior_ratified():
    assert DHANA_AXIS_CLASS_PRIOR == 1.05


def test_sign_lord_table_covers_all_12_signs_classical_only():
    assert len(_SIGN_LORD) == 12
    assert "Rahu" not in _SIGN_LORD.values()
    assert "Ketu" not in _SIGN_LORD.values()
    assert _SIGN_LORD["Aries"] == "Mars"
    assert _SIGN_LORD["Aquarius"] == "Saturn"


def test_not_null_columns_populated_both_classes():
    vargottama_facts = {"MER": {"is_vargottama": True, "fact_id": "fmer"}}
    positions = {"LAGNA": _pos(house=1, sign="Aries", fact_id="lagna"),
                 "MER": _pos(house=10, sign="Capricorn", fact_id="mer")}
    rows = build_vargottama_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        vargottama_facts=vargottama_facts, positions=positions,
        now="2026-07-16T00:00:00+00:00",
    ) + build_dhana_axis_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        positions=positions, now="2026-07-16T00:00:00+00:00",
    )
    assert len(rows) == 3  # 1 vargottama + 2 dhana_axis
    not_null_cols = [
        "signal_id", "chart_id", "ayanamsha_id", "build_id",
        "signal_type_id", "signal_type_class", "signal_tradition",
        "fact_kind", "source_l1_asset", "source_subsystem", "lel_origin",
        "configuration_jsonb", "constituent_facts_array",
        "deterministic_strength", "verification_certainty",
        "computed_salience", "salience_formula_version",
        "domains_affected_array", "domain_salience_jsonb",
        "active_duration_class", "verification_pass_status",
        "citation_ref", "citation_human", "computed_at", "engine_version",
    ]
    for row in rows:
        for col in not_null_cols:
            assert row[col] is not None, f"{col} must not be None (NOT NULL column) in {row['signal_type_id']}"


# ── L0 class_priors seed: both classes (append-only, DIS.019) ────────────

def test_l0_class_priors_has_both_rows():
    from brahmagyan.l0_class_priors import CLASS_ROWS

    va_matches = [r for r in CLASS_ROWS if r[0] == "vargottama_amplification"]
    da_matches = [r for r in CLASS_ROWS if r[0] == "dhana_axis"]
    assert len(va_matches) == 1
    assert len(da_matches) == 1
    assert va_matches[0][1] == 1.15
    assert da_matches[0][1] == 1.05


def test_bo_vargottama_dhana_writer_is_registered():
    from pipeline.orchestrator.writers.bo_vargottama_dhana import BoVargottamaDhanaWriter
    from pipeline.orchestrator.writers import get_writer

    assert BoVargottamaDhanaWriter.asset_id == "bo_vargottama_dhana"
    assert get_writer("bo_vargottama_dhana") is BoVargottamaDhanaWriter
