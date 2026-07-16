"""
Tests for bo_special_lagna / bodha_writers.special_lagna_emitter (D-2 Lane
V-5, CR-76).

TYPE SPECIMENS independently reproduced against chart 482012f1's real
lahiri_chitrapaksha facts (verified live via mcp__postgres__query before
writing this test):
  - INDU_LAGNA: house_d1=8, sign=Scorpio, sign_lord=Mars, nakshatra=Jyeshtha.
  - GHATI_LAGNA: house_d1=9, sign=Sagittarius, sign_lord=Jupiter.
"""
from __future__ import annotations

import json

from bodha_writers.special_lagna_emitter import (
    _TARGET_LAGNAS,
    SPECIAL_LAGNA_CLASS_PRIOR,
    SPECIAL_LAGNA_SUBSYSTEM,
    SIGNAL_TYPE_CLASS,
    build_signal_row,
)


def _fact(text=None, num=None, fact_id="f0"):
    return {"text": text, "num": num, "fact_id": fact_id}


def test_indu_lagna_type_specimen():
    facts = {
        "house_d1": _fact(num=8, fact_id="fh"),
        "sign": _fact(text="Scorpio", fact_id="fs"),
        "sign_lord": _fact(text="Mars", fact_id="fsl"),
        "nakshatra": _fact(text="Jyeshtha", fact_id="fn"),
        "nakshatra_lord": _fact(text="Mercury", fact_id="fnl"),
        "pada": _fact(num=4, fact_id="fp"),
    }
    row = build_signal_row(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        lagna_key="INDU_LAGNA", facts=facts, now="2026-07-16T00:00:00+00:00",
    )
    assert row is not None
    cfg = json.loads(row["configuration_jsonb"])
    assert cfg["house_d1"] == 8
    assert cfg["sign"] == "Scorpio"
    assert cfg["sign_lord"] == "Mars"
    assert cfg["governs_domains"] == ["wealth"]
    assert row["signal_type_class"] == SIGNAL_TYPE_CLASS == "special_lagna"
    domain_sal = json.loads(row["domain_salience_jsonb"])
    assert "wealth" in domain_sal
    assert domain_sal["wealth"] > 0


def test_ghati_lagna_governs_career():
    facts = {"house_d1": _fact(num=9, fact_id="fh"), "sign": _fact(text="Sagittarius", fact_id="fs")}
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        lagna_key="GHATI_LAGNA", facts=facts, now="2026-07-16T00:00:00+00:00",
    )
    assert row is not None
    assert row["domains_affected_array"] == ["career"]


def test_returns_none_without_house_fact():
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        lagna_key="SREE_LAGNA", facts={}, now="2026-07-16T00:00:00+00:00",
    )
    assert row is None


def test_domain_boost_undoes_class_prior_discount():
    """domain_salience must read at parity with the underlying (pre-discount)
    salience — DR-6's explicit instruction that domain_salience carries
    in-domain rank despite the chart-wide 0.90 discount."""
    facts = {"house_d1": _fact(num=1, fact_id="fh"), "sign": _fact(text="Aries", fact_id="fs")}
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        lagna_key="HORA_LAGNA", facts=facts, now="2026-07-16T00:00:00+00:00",
    )
    domain_sal = json.loads(row["domain_salience_jsonb"])
    assert domain_sal["wealth"] == round(row["computed_salience"] / SPECIAL_LAGNA_CLASS_PRIOR, 6)


def test_target_lagnas_are_exactly_indu_sree_ghati_hora():
    assert set(_TARGET_LAGNAS.keys()) == {"INDU_LAGNA", "SREE_LAGNA", "GHATI_LAGNA", "HORA_LAGNA"}


def test_class_prior_ratified():
    assert SPECIAL_LAGNA_CLASS_PRIOR == 0.90
    assert SPECIAL_LAGNA_SUBSYSTEM == "special_lagna"


def test_not_null_columns_populated():
    facts = {"house_d1": _fact(num=7, fact_id="fh"), "sign": _fact(text="Libra", fact_id="fs")}
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        lagna_key="SREE_LAGNA", facts=facts, now="2026-07-16T00:00:00+00:00",
    )
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
        assert row[col] is not None, f"{col} must not be None (NOT NULL column)"


# ── L0 class_priors seed: special_lagna row (append-only, DIS.019) ───────

def test_l0_class_priors_has_special_lagna_row():
    from brahmagyan.l0_class_priors import CLASS_ROWS

    matches = [r for r in CLASS_ROWS if r[0] == "special_lagna"]
    assert len(matches) == 1, "exactly one special_lagna row expected (append-only)"
    _, prior, _ = matches[0]
    assert prior == 0.90  # DIS.019/DR-6 ratified value


def test_bo_special_lagna_writer_is_registered():
    from pipeline.orchestrator.writers.bo_special_lagna import BoSpecialLagnaWriter
    from pipeline.orchestrator.writers import get_writer

    assert BoSpecialLagnaWriter.asset_id == "bo_special_lagna"
    assert get_writer("bo_special_lagna") is BoSpecialLagnaWriter
