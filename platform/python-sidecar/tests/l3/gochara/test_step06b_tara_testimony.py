"""ASTRA_REVIEW_A5_4 P1-6 — tārā as P6 testimony on the '4.0' projection
path (GOCHARA_DESIGN_SPECS_v1_4 §2.2 P6, S-04, O-P6-TARA, O-RR-7).

The projection must PRODUCE the tārā annotation (the pre-rework projection
passed None, None — an honest skip forever) on the intended path (day rows,
the only P6 grain) and must NEVER let it move a score: λ with the annotation
is bit-identical to λ without it. Twins fixture (O-P6-TARA): natal Moon
327.06° → nakṣatra 25 (Pūrva Bhādrapadā); transit Moon 269.14° → nakṣatra
21; inclusive count 24 → nine-fold class 6 (sādhaka).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .test_step06b_windows_projection import _open_gates  # noqa: E402
from .test_step06b_angular_m1 import _contact, T_EXACT, _load_writer  # noqa: E402

w = _load_writer()

NATAL_MOON = 327.06
TWINS_MOON = 269.14


def _ctx(natal_moon):
    return w.ClassContext(
        "childbirth", [0.8], {"vimshottari": True},
        weight_by_target_ref={"Jupiter": 0.8}, class_valence="gain",
        class_is_adverse=False, natal_moon_deg=natal_moon)


def _pos(body, jd):
    if body == "Moon":
        return TWINS_MOON
    return (100.0 + 0.5 * (jd - T_EXACT)) % 360.0  # the contact body peaks at t_exact


def _rows(natal_moon):
    c = _contact("j", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0, body="Jupiter")
    c["target_ref"] = "Jupiter"
    rows, report = w.project_class_windows(
        _ctx(natal_moon), [c], (T_EXACT - 30.0, T_EXACT + 30.0), _open_gates,
        planet_pos_fn=_pos)
    return rows, report


def test_nakshatra_index_convention_matches_the_twins_arithmetic():
    assert w.nakshatra_index_1based(NATAL_MOON) == 25
    assert w.nakshatra_index_1based(TWINS_MOON) == 21
    assert w.nakshatra_index_1based(0.0) == 1 and w.nakshatra_index_1based(359.99) == 27


def test_day_rows_carry_the_tara_annotation_with_class_six():
    rows, _ = _rows(NATAL_MOON)
    tiers = {r["resolution"]: r for r in rows}
    assert {"era", "month", "day"} <= set(tiers)
    ann = tiers["day"]["suppression_state"]["tara"]["annotation"]
    assert ann["state"] == "annotated" and ann["operator"] == "tara"
    assert ann["count"] == 24 and ann["class"] == 6 and ann["class_name"] == "sadhaka"
    assert ann["operator_role"] == "testimony" and ann["weight"] == 0.0
    assert (ann["natal_nakshatra_index"], ann["transit_nakshatra_index"]) == (25, 21)
    assert "tara:testimony(P6 day annotation; never weights)" in tiers["day"]["contributing_systems"]
    for tier in ("era", "month"):
        t = tiers[tier]["suppression_state"]["tara"]
        assert t["annotation"] is None and t["annotation_state"].startswith("not_applicable")
        assert any(s.startswith("tara:not_applicable") for s in tiers[tier]["contributing_systems"])


def test_scores_identical_with_and_without_the_testimony():
    """O-RR-7 / O-P6-TARA: the annotation present vs absent (natal Moon
    withheld) ⇒ bit-identical raw/signed intensity on every row; the product
    term is pinned to 1.0. Mutation caught: any λ delta from tārā."""
    with_rows, with_rep = _rows(NATAL_MOON)
    without_rows, without_rep = _rows(None)
    assert len(with_rows) == len(without_rows) >= 3
    for a, b in zip(with_rows, without_rows):
        assert a["raw_intensity"] == b["raw_intensity"]
        assert a["signed_intensity"] == b["signed_intensity"]
        assert a["suppression_state"]["tara"]["modifier"] == 1.0
        assert a["suppression_state"]["tara"]["operator_role"] == "testimony"
    assert with_rep["tara_modifier"] == without_rep["tara_modifier"] == 1.0
    day_without = [r for r in without_rows if r["resolution"] == "day"][0]
    ann = day_without["suppression_state"]["tara"]["annotation"]
    assert ann["state"] == "skipped" and "natal Moon" in ann["reason"]


def test_annotator_reuses_the_b51_p6_operator():
    from services.gochara_rules import p6
    ann = w.make_tara_annotator(NATAL_MOON, _pos)(T_EXACT)
    assert ann["class"] == p6.tara(25, 21)["class"] == 6
    assert ann["source"] == "MC PG67/PG79 [D]"


def test_document_chart_feeds_the_natal_moon(monkeypatch):
    doc = {"_chart": {"natal": {"Moon": NATAL_MOON}}, "marriage": {}}
    ctx = w.build_projection_class_context(
        None, "chart", "marriage", {"permission_systems": {"vimshottari": True}},
        doc, weights=[0.9], weight_by_target_ref={"Venus": 0.9},
        context_source="test", permission_factory=lambda *a, **k: None)
    assert ctx.natal_moon_deg == NATAL_MOON and ctx.tara["skipped"] is False
    # a case-mismatched key ('MOON') is NOT silently accepted as the natal Moon
    ctx2 = w.build_projection_class_context(
        None, "chart", "marriage", {"permission_systems": {"vimshottari": True}},
        {"_chart": {"natal": {"MOON": NATAL_MOON}}, "marriage": {}},
        weights=[0.9], weight_by_target_ref={"Venus": 0.9},
        context_source="test", permission_factory=lambda *a, **k: None)
    assert ctx2.natal_moon_deg is None and ctx2.tara["skipped"] is True
