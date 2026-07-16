"""
Tests for bo_arudha / bodha_writers.arudha_emitter (D-2 Lane V-5, CR-61).

TYPE SPECIMEN independently reproduced against chart 482012f1's real
lahiri_chitrapaksha facts (verified live via mcp__postgres__query before
writing this test): ARUDHA_A1 (AL) = H9; JUP and VEN are BOTH in H9 —
i.e. AL is conjunct Jupiter AND Venus. ARUDHA_A2 = H3 (untenanted by any
graha on this chart). ARUDHA_A11 = H2 (tenanted by Rahu, house_d1=2).
"""
from __future__ import annotations

import json

from bodha_writers.arudha_emitter import (
    GRAHAS,
    ARUDHA_CLASS_PRIOR,
    ARUDHA_SUBSYSTEM,
    SIGNAL_TYPE_CLASS,
    build_signal_rows,
)


def _arudha_fact(subj_facts: dict) -> dict:
    return subj_facts


def test_al_conjunction_type_specimen_jupiter_venus_h9():
    """AL=H9; JUP and VEN both occupy H9 on 482012f1/lahiri — both must
    surface as AL_conjunction rows."""
    arudha_facts = {
        "ARUDHA_A1": {"house_d1": {"num": 9, "fact_id": "fal"}, "sign": {"text": "Sagittarius"}},
        "ARUDHA_A2": {"house_d1": {"num": 3, "fact_id": "fa2"}, "sign": {"text": "Cancer"}},
        "ARUDHA_A11": {"house_d1": {"num": 2, "fact_id": "fa11"}, "sign": {"text": "Gemini"}},
    }
    graha_houses = {
        "JUP": {"house_d1": 9, "fact_id": "fjup"},
        "VEN": {"house_d1": 9, "fact_id": "fven"},
        "RAH_MEAN": {"house_d1": 2, "fact_id": "frah"},
        "SUN": {"house_d1": 10, "fact_id": "fsun"},
        "MOON": {"house_d1": 11, "fact_id": "fmoon"},
        "MAR": {"house_d1": 7, "fact_id": "fmar"},
        "MER": {"house_d1": 10, "fact_id": "fmer"},
        "SAT": {"house_d1": 7, "fact_id": "fsat"},
        "KET_MEAN": {"house_d1": 8, "fact_id": "fket"},
    }
    rows = build_signal_rows(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        arudha_facts=arudha_facts, graha_houses=graha_houses,
        now="2026-07-16T00:00:00+00:00",
    )
    subkeys = [r["signal_type_id"] for r in rows]
    assert "arudha:AL_bhava_relation" in subkeys
    assert "arudha:AL_conjunction:JUP" in subkeys
    assert "arudha:AL_conjunction:VEN" in subkeys
    assert "arudha:AL_conjunction:SUN" not in subkeys  # Sun is in H10, not H9
    assert "arudha:ARUDHA_A2_tenancy" in subkeys
    assert "arudha:ARUDHA_A11_tenancy" in subkeys

    a11_row = next(r for r in rows if r["signal_type_id"] == "arudha:ARUDHA_A11_tenancy")
    cfg = json.loads(a11_row["configuration_jsonb"])
    assert cfg["occupants"] == ["Rahu"]

    a2_row = next(r for r in rows if r["signal_type_id"] == "arudha:ARUDHA_A2_tenancy")
    cfg2 = json.loads(a2_row["configuration_jsonb"])
    assert cfg2["occupants"] == []  # untenanted


def test_al_bhava_relation_house_9_is_trikona():
    arudha_facts = {"ARUDHA_A1": {"house_d1": {"num": 9, "fact_id": "fal"}, "sign": {"text": "Sagittarius"}}}
    rows = build_signal_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        arudha_facts=arudha_facts, graha_houses={}, now="2026-07-16T00:00:00+00:00",
    )
    al_row = next(r for r in rows if r["signal_type_id"] == "arudha:AL_bhava_relation")
    cfg = json.loads(al_row["configuration_jsonb"])
    assert cfg["al_category"] == "trikona"
    assert al_row["valence"] == "benefic"


def test_no_rows_without_al_house_fact():
    rows = build_signal_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        arudha_facts={}, graha_houses={}, now="2026-07-16T00:00:00+00:00",
    )
    assert rows == []


def test_class_prior_and_subsystem_ratified():
    assert ARUDHA_CLASS_PRIOR == 1.10
    assert ARUDHA_SUBSYSTEM == "jaimini"
    assert SIGNAL_TYPE_CLASS == "arudha"


def test_not_null_columns_populated():
    arudha_facts = {"ARUDHA_A1": {"house_d1": {"num": 1, "fact_id": "fal"}, "sign": {"text": "Aries"}}}
    rows = build_signal_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        arudha_facts=arudha_facts, graha_houses={}, now="2026-07-16T00:00:00+00:00",
    )
    assert len(rows) == 1
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
    for col in not_null_cols:
        assert rows[0][col] is not None, f"{col} must not be None (NOT NULL column)"


# ── L0 class_priors seed: arudha row (append-only, DIS.019) ──────────────

def test_l0_class_priors_has_arudha_row():
    from brahmagyan.l0_class_priors import CLASS_ROWS

    matches = [r for r in CLASS_ROWS if r[0] == "arudha"]
    assert len(matches) == 1, "exactly one arudha row expected (append-only)"
    _, prior, _ = matches[0]
    assert prior == 1.10  # DIS.019/DR-6 ratified value


def test_bo_arudha_writer_is_registered():
    from pipeline.orchestrator.writers.bo_arudha import BoArudhaWriter
    from pipeline.orchestrator.writers import get_writer

    assert BoArudhaWriter.asset_id == "bo_arudha"
    assert get_writer("bo_arudha") is BoArudhaWriter
