"""Golden-value narration fidelity tests for bo_upaya.

(1) the gemstone maraka-contraindication verdict's `reason` sentence;
(2) the `citation_human` strings the writer composes for resonance, prescription,
    chart-summary, dosha-bundle and pattern-remedy rows.
Every expected sentence is stated by hand from the f-string templates.
"""
from __future__ import annotations

from pipeline.orchestrator.writers import bo_upaya as W


def test_upaya_maraka_verdict_reason_golden():
    facts = {"second_lord": "Mercury", "seventh_lord": "Jupiter", "_source_fact_id": "f1"}
    both = {"second_lord": "Saturn", "seventh_lord": "Saturn", "_source_fact_id": "f2"}
    second = W._compute_gemstone_maraka_verdict("Mercury", facts)
    seventh = W._compute_gemstone_maraka_verdict("Jupiter", facts)
    neither = W._compute_gemstone_maraka_verdict("Venus", facts)
    double = W._compute_gemstone_maraka_verdict("Saturn", both)
    reasons = [second["reason"], seventh["reason"], neither["reason"], double["reason"]]
    assert reasons == [
        "Mercury rules the 2nd house (BPHS: \"the 2nd is a powerful Maraka house\") from lagna — "
        "a maraka lord. Per BPHS Ch.44/47, wearing Mercury's gemstone is classically "
        "contraindicated for this chart unless a qualified acharya review finds a redeeming "
        "yoga; gemstones strengthen the planet they represent, and strengthening a maraka is "
        "the opposite of the intended effect.",
        "Jupiter rules the 7th house from lagna — a maraka lord. Per BPHS Ch.44/47, wearing "
        "Jupiter's gemstone is classically contraindicated for this chart unless a qualified "
        "acharya review finds a redeeming yoga; gemstones strengthen the planet they represent, "
        "and strengthening a maraka is the opposite of the intended effect.",
        "Venus is neither the 2nd-house lord (Mercury) nor the 7th-house lord (Jupiter) from "
        "lagna in this chart — no maraka-lordship contraindication under the v1 rule.",
        "Saturn rules both the 2nd and 7th houses (maximal maraka lordship) from lagna — a "
        "maraka lord. Per BPHS Ch.44/47, wearing Saturn's gemstone is classically "
        "contraindicated for this chart unless a qualified acharya review finds a redeeming "
        "yoga; gemstones strengthen the planet they represent, and strengthening a maraka is "
        "the opposite of the intended effect.",
    ]


def test_upaya_citation_human_golden(monkeypatch):
    def _remedies(conn, graha, limit=5):
        if graha != "Jupiter":
            return []
        return [
            {"remedy_id": "R-J1", "remedy_type": "mantra", "prescription_text": "Chant the mantra",
             "confidence": 0.9},
            {"remedy_id": "R-J2", "remedy_type": "charity", "prescription_text": "Offer yellow grain",
             "confidence": 0.8},
        ]

    monkeypatch.setattr(W, "_fetch_shadbala", lambda conn, c, a: {"Jupiter": 0.4237, "Sun": 1.1})
    monkeypatch.setattr(W, "_fetch_bhava_bala", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_special_states", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_graha_house_placements", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_yoga_karaka_flags", lambda conn, c, a: set())
    monkeypatch.setattr(W, "_fetch_chara_roles", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_msr_dosha_sigs_by_graha",
                        lambda conn, c, a: {"Jupiter": ["guru_chandala", "kemadruma"]})
    monkeypatch.setattr(W, "_fetch_active_doshas_by_graha", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_maraka_facts", lambda conn, c, a: None)
    monkeypatch.setattr(W, "_fetch_chart_typology", lambda conn, c, a: "balanced")
    monkeypatch.setattr(W, "_fetch_dispositor_terminal_strength", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_cgm_motif_weakest_node_burden", lambda conn, c, a, s: {})
    monkeypatch.setattr(W, "_fetch_graha_cdlm_cells", lambda conn, c, a: {})
    monkeypatch.setattr(W, "_fetch_msr_contradiction_burden", lambda conn, c, a: ({}, False))
    monkeypatch.setattr(W, "_fetch_remedies_for_graha", _remedies)

    resonances, prescriptions = W._build_resonances_and_prescriptions(
        "chart", "lahiri_chitrapaksha", "build", None, "2026-10-05T00:00:00+00:00"
    )
    by_graha = {r["graha"]: r for r in resonances}
    summary = W._build_rm_summary(
        "chart", "lahiri_chitrapaksha", "build", resonances, prescriptions, "balanced",
        "2026-10-05T00:00:00+00:00",
    )
    bundles = W._build_dosha_bundles(
        "chart", "lahiri_chitrapaksha", "build", prescriptions, "2026-10-05T00:00:00+00:00",
    )
    patterns = W._build_pattern_remedies(
        "chart", "lahiri_chitrapaksha", "build", resonances, prescriptions,
        "2026-10-05T00:00:00+00:00",
    )
    citations = [
        by_graha["Jupiter"]["citation_human"],
        by_graha["Rahu"]["citation_human"],
        prescriptions[0]["citation_human"],
        summary["citation_human"],
        bundles[0]["citation_human"],
        patterns[0]["citation_human"],
    ]
    assert citations == [
        "Resonance: Jupiter | sha=0.42 dosha_count=2",
        "Resonance: Rahu | sha=n/a (no classical shadbala for this graha) dosha_count=0",
        "G27 remedy R-J1 for Jupiter",
        "RM chart summary — 9 resonances, 2 prescriptions",
        "Dosha remedy bundle for guru_chandala — 2 prescriptions",
        "Pattern remedy theme strengthen_Jupiter — 2 prescriptions",
    ]
