"""
test_ir6_activity_primitives.py — PK-R-9 IR-6 detectors (2026-08-11).

IR-6: Keep `nakshatra_ingress_tara` in `_ACTIVITY_PRIMITIVES`; REMOVE
`sarvatobhadra_vedha` from it (uncited_extension=True unconditional +
`bg_sarvatobhadra_grid` empty by design + a future admission ruling is
required before an algorithmic-approximation primitive with no populated
corpus should move a served, bounded intensity score).

Two detectors, per the ruling's own wording:
  1. "membership test both directions" -- nakshatra_ingress_tara IS in
     _ACTIVITY_PRIMITIVES; sarvatobhadra_vedha is NOT.
  2. "a GENERAL invariant test: no sentence carrying uncited_extension=True
     contributes to activity (the class, not the instance)" -- proven here
     by running the REAL `sarvatobhadra.find_sarvatobhadra_vedha_states`
     primitive (not one hand-built fixture sentence) across a spread of
     targets/dates and confirming (a) EVERY sentence it can ever emit
     carries uncited_extension=True unconditionally (the CLASS property,
     not one instance), and (b) none of those real sentences contribute to
     `_compute_activity_v3`'s activity term or term_breakdown, even when
     mixed into a pool alongside sentences from primitives that DO
     contribute.

INTERPRETATION NOTE (recorded here, not silently assumed): this test suite
does NOT extend the "uncited_extension=True never contributes" property to
`degree_contact` / `eclipse_degree` — both of those primitives ALSO
unconditionally set uncited_extension=True (per gochara_grammar/
primitives.py's own module docstring, families #1 and #10), but for a
DIFFERENT reason than sarvatobhadra_vedha's ("no codebase-attested
classical citation names the technique itself", not "the corpus this
primitive would need to be verified is empty by design"). A literal
class-wide "any uncited_extension=True sentence is excluded from activity"
filter would ALSO zero those two families' entire contribution to v3's
activity term — a large, currently-load-bearing behavior change with no
explicit instruction to make it, and one that the existing v3 test suite's
own `_make_sentence` fixture helpers (which set uncited_extension=True
unconditionally just to satisfy ConfigurationSentence's citation-discipline
constructor invariant, not to model real primitive behavior) would NOT have
caught, since they do not represent real primitive output. This
interpretation is disclosed prominently in the PR body for the ADJUDICATOR
to confirm or correct in a follow-on ruling if this reading is too narrow.
"""
from __future__ import annotations

import swisseph as swe

from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import sarvatobhadra as SBC
from services.gochara_grammar.models import ResonanceTarget
from services.gochara_v3.engine import (
    _ACTIVITY_PRIMITIVES,
    _compute_activity_v3,
    _compute_signed_channels_v3,
)

CHART_ID = RM.CANONICAL_CHART_ID


def _jd(y, m, d, h=12.0):
    return swe.julday(y, m, d, h)


# ── Detector 1: membership test both directions ────────────────────────────

def test_nakshatra_ingress_tara_is_in_activity_primitives():
    assert "nakshatra_ingress_tara" in _ACTIVITY_PRIMITIVES


def test_sarvatobhadra_vedha_is_not_in_activity_primitives():
    assert "sarvatobhadra_vedha" not in _ACTIVITY_PRIMITIVES


# ── Detector 2: general invariant, proven against the REAL primitive's
#    entire sentence class, not one hand-built instance ──────────────────

def test_every_real_sarvatobhadra_vedha_sentence_is_unconditionally_uncited():
    """The CLASS property IR-6's reason cites ('uncited_extension=True
    unconditional') proven against the REAL primitive, not a fixture:
    every sentence `find_sarvatobhadra_vedha_states` emits, across a spread
    of natal-nakshatra anchors and transiting planets, carries
    uncited_extension=True and classical_citation=None. No conn is passed,
    so `_vedha_pairs_from_db` always degrades to the algorithmic
    opposition-nakshatra approximation -- exactly the live production
    shape (v3's `_gather_sentences_no_db` also always calls this with
    conn=None)."""
    all_sentences = []
    start_jd, end_jd = _jd(2024, 1, 1), _jd(2026, 12, 31)
    for nak_id in (1, 7, 14, 20, 25, 27):  # spread across the 27-nakshatra wheel
        target = ResonanceTarget(
            chart_id=CHART_ID, event_class="marriage", target_type="karaka",
            target_ref=f"test_nak_{nak_id}", weight=0.9, classical_citation="TEST FIXTURE",
            target_nakshatra_id=nak_id,
        )
        all_sentences.extend(
            SBC.find_sarvatobhadra_vedha_states(
                swe, CHART_ID, target, start_jd, end_jd,
                transit_planets=["Saturn", "Jupiter", "Rahu", "Ketu"], conn=None,
            )
        )
    assert len(all_sentences) >= 1, "expected >=1 real sarvatobhadra_vedha sentence across this spread"
    for s in all_sentences:
        assert s.primitive == "sarvatobhadra_vedha"
        assert s.uncited_extension is True
        assert s.classical_citation is None


def test_real_sarvatobhadra_vedha_sentences_never_contribute_to_v3_activity():
    """The actual IR-6 invariant: feed the REAL sarvatobhadra_vedha
    sentences gathered above into `_compute_activity_v3` (and the signed-
    channel counterpart), mixed alongside a real, member-primitive
    sentence (sign_ingress) that DOES contribute, and confirm the
    sarvatobhadra_vedha sentences contribute NOTHING -- no term_breakdown
    entry, no effect on activity beyond what the member sentence alone
    would produce."""
    from services.gochara_grammar import primitives as P

    start_jd, end_jd = _jd(2024, 1, 1), _jd(2026, 12, 31)
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="marriage", target_type="karaka",
        target_ref="test_nak_25", weight=0.9, classical_citation="TEST FIXTURE",
        target_nakshatra_id=25,
    )
    sbc_sentences = SBC.find_sarvatobhadra_vedha_states(
        swe, CHART_ID, target, start_jd, end_jd,
        transit_planets=["Saturn", "Jupiter", "Rahu", "Ketu"], conn=None,
    )
    assert len(sbc_sentences) >= 1

    weight_by_target_ref = {"test_nak_25": 1.0}

    # sarvatobhadra_vedha sentences ALONE: activity must be exactly 0.0 and
    # term_breakdown must be empty -- the primitive-membership filter in
    # _compute_activity_v3 excludes it entirely (s.primitive not in
    # _ACTIVITY_PRIMITIVES), regardless of uncited_extension.
    activity_alone, detail_alone, term_breakdown_alone = _compute_activity_v3(
        sbc_sentences, weight_by_target_ref,
    )
    assert activity_alone == 0.0
    assert term_breakdown_alone == {}
    assert detail_alone["sentence_count_active"] == 0
    assert detail_alone["sentence_count_total_gathered"] == len(sbc_sentences)

    supportive_alone, afflicting_alone, _ = _compute_signed_channels_v3(
        sbc_sentences, weight_by_target_ref,
    )
    assert supportive_alone == 0.0
    assert afflicting_alone == 0.0

    # Mixed with a real, contributing member-primitive sentence: the mixed
    # pool's activity/term_breakdown must be IDENTICAL to the member
    # sentence alone -- proving the sarvatobhadra_vedha sentences add
    # nothing, not merely that an empty pool scores zero.
    bhava_target = ResonanceTarget(
        chart_id=CHART_ID, event_class="marriage", target_type="bhava",
        target_ref="test_nak_25", weight=0.9, classical_citation="TEST FIXTURE",
        target_sign="Capricorn",
    )
    # Wide window + Moon (ingresses into every sign roughly monthly) --
    # guarantees a real sign_ingress hit regardless of the narrower
    # 2024-2026 window used for the sarvatobhadra_vedha gather above.
    wide_start_jd, wide_end_jd = _jd(2020, 1, 1), _jd(2026, 12, 31)
    ingress_sentences = P.sign_ingress(swe, CHART_ID, bhava_target, wide_start_jd, wide_end_jd, planets=["Moon"])
    assert len(ingress_sentences) >= 1, "need >=1 real sign_ingress sentence to prove non-interference"

    activity_member_only, _, term_breakdown_member_only = _compute_activity_v3(
        ingress_sentences, weight_by_target_ref,
    )
    activity_mixed, _, term_breakdown_mixed = _compute_activity_v3(
        ingress_sentences + sbc_sentences, weight_by_target_ref,
    )
    assert activity_mixed == activity_member_only
    assert term_breakdown_mixed == term_breakdown_member_only
    assert "sarvatobhadra_vedha" not in term_breakdown_mixed
