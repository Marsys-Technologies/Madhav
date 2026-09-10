"""
test_ir6_activity_primitives.py — PK-R-9 / PK-R-9a IR-6 detectors
(2026-08-11).

IR-6: Keep `nakshatra_ingress_tara` in `_ACTIVITY_PRIMITIVES`; REMOVE
`sarvatobhadra_vedha` from it (uncited_extension=True unconditional +
`bg_sarvatobhadra_grid` empty by design + a future admission ruling is
required before an algorithmic-approximation primitive with no populated
corpus should move a served, bounded intensity score).

PK-R-9a (ADJUDICATOR amendment, 2026-08-11): the builder (this file's first
pass) flagged that IR-6's literal "no sentence carrying uncited_extension=
True contributes to activity" wording, read as a blanket class-wide filter,
would also zero degree_contact/eclipse_degree's currently-load-bearing
contribution -- an unrequested, unadjudicated scoring change. The
ADJUDICATOR confirmed this narrowing was CORRECT ("That was my error, and
the builder was right to stop") and amended IR-6 to the more precise
concept below: an ABSENT-SOURCE-SUBSTITUTION marker (a detail field naming
that a real classical/DB source was unreachable and an algorithmic
approximation stood in for it), not the uncited_extension flag itself
(which degree_contact/eclipse_degree also carry, unconditionally, for an
unrelated reason -- no codebase-attested citation names the technique, not
"the corpus is empty by design").

Three detectors:
  (i) membership test both directions -- nakshatra_ingress_tara IS in
      _ACTIVITY_PRIMITIVES; sarvatobhadra_vedha is NOT.
  (ii) absent-source-substitution marker: ENFORCED for sarvatobhadra_vedha
       (detail['vedha_pair_source']=='algorithmic_opposition_approximation')
       -- proven via the real primitive's entire sentence class, not one
       hand-built instance. REPORTING-ONLY for kakshya_cell_crossing's
       equal-eighths fallback (detail['source']==
       'equal_eighths_fixture_approximation') -- this primitive remains an
       _ACTIVITY_PRIMITIVES member and DOES currently contribute; per
       PK-R-9a, zeroing that live behavior here would itself be an
       unadjudicated scoring change (the same mistake IR-6's narrower
       reading avoided for degree_contact/eclipse_degree), so this test
       DETECTS and REPORTS the participation without failing on it -- a
       named, disclosed register residual for a future ruling.
  (iii) regression guard: degree_contact and eclipse_degree DO contribute
        nonzero activity in a fixture where they fire, so any FUTURE
        blanket uncited_extension filter (re-introducing the mistake
        PK-R-9a corrected) fails this test loudly instead of silently
        deflating lambda.
"""
from __future__ import annotations

import warnings

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


# ── Detector (i): membership test both directions ──────────────────────────

def test_nakshatra_ingress_tara_is_in_activity_primitives():
    assert "nakshatra_ingress_tara" in _ACTIVITY_PRIMITIVES


def test_sarvatobhadra_vedha_is_not_in_activity_primitives():
    assert "sarvatobhadra_vedha" not in _ACTIVITY_PRIMITIVES


# ── Detector (ii), ENFORCED half: absent-source-substitution marker for
#    sarvatobhadra_vedha, proven against the REAL primitive's entire
#    sentence class, not one hand-built instance ──────────────────────────

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
        # PARĪKṢAKA F-1: this test's docstring advertises the SBC
        # enforcement as MARKER-keyed (the PK-R-9a absent-source-
        # substitution concept), not merely uncited_extension-keyed -- the
        # marker itself must actually be asserted, or this test only
        # proves the (necessary but insufficient) uncited_extension flag.
        assert s.detail.get("vedha_pair_source") == "algorithmic_opposition_approximation"


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


# ── Detector (ii), REPORTING-ONLY half: kakshya_cell_crossing's
#    equal-eighths-fallback absent-source-substitution marker ────────────

def test_kakshya_equal_eighths_fallback_absent_source_marker_is_reported_not_silently_zeroed():
    """PK-R-9a REPORTING-ONLY detector: `kakshya_cell_crossing`'s equal-
    eighths fallback (detail['source']=='equal_eighths_fixture_
    approximation', fired whenever no live `ashtakavarga_kakshya_boundary`
    chart_facts rows are reachable -- e.g. conn=None, exactly what v3's
    `_gather_sentences_no_db` always passes) is ANOTHER absent-source-
    substitution marker of the same KIND as sarvatobhadra_vedha's
    `vedha_pair_source`. Unlike sarvatobhadra_vedha, `kakshya_cell_crossing`
    remains an `_ACTIVITY_PRIMITIVES` member (IR-6 never touched it) and
    `_compute_activity_v3` has no marker-aware exclusion for this fallback
    -- so a fallback sentence DOES currently contribute nonzero activity.

    Per PK-R-9a, silently zeroing this here (e.g. by adding an ad hoc
    detail['source'] check) would itself be an unadjudicated scoring
    change -- the same category of mistake IR-6's narrower reading avoided
    for degree_contact/eclipse_degree, just discovered from the opposite
    direction (an admission that SHOULD arguably be reviewed, left alone
    instead of unilaterally "fixed"). This test's job is to DETECT and
    REPORT the participation loudly (a warning naming it a register
    residual) without failing the suite on it -- it neither asserts the
    contribution must be zero (that would silently mandate an unauthorized
    fix) nor that it must be nonzero (that would freeze an unadjudicated
    behavior as a permanent contract). A future ruling on this residual
    can change the underlying behavior without this test needing to change
    first."""
    from services.gochara_grammar import primitives as P

    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="wealth", target_type="bhava",
        target_ref="2", weight=0.9, classical_citation="TEST FIXTURE",
        target_sign="Taurus",
    )
    start_jd, end_jd = _jd(2019, 1, 1), _jd(2021, 1, 1)
    # conn=None forces the equal-eighths fallback unconditionally (no live
    # boundary rows are ever fetched when conn is None) -- exactly the
    # shape v3's _gather_sentences_no_db always calls this primitive with.
    kakshya_sentences = P.kakshya_cell_crossing(
        swe, CHART_ID, target, start_jd, end_jd, conn=None, planets=["Moon"],
    )
    assert len(kakshya_sentences) >= 1, "expected >=1 real kakshya_cell_crossing fallback sentence"
    for s in kakshya_sentences:
        assert s.detail.get("source") == "equal_eighths_fixture_approximation"
        assert s.uncited_extension is True  # same "extension, not verified" shape as sarvatobhadra_vedha

    assert "kakshya_cell_crossing" in _ACTIVITY_PRIMITIVES  # unchanged by IR-6 -- the precondition for this residual

    weight_by_target_ref = {"2": 1.0}
    activity_k, detail_k, term_breakdown_k = _compute_activity_v3(kakshya_sentences, weight_by_target_ref)

    # Sanity only -- never a pass/fail gate on the specific value (see
    # docstring: this detector must not fail regardless of which way the
    # residual eventually resolves).
    assert 0.0 <= activity_k <= 1.0

    participates = activity_k > 0.0 or "kakshya_cell_crossing" in term_breakdown_k
    if participates:
        warnings.warn(
            "PK-R-9a register residual: kakshya_cell_crossing's equal-eighths "
            "fallback (detail['source']=='equal_eighths_fixture_approximation') "
            f"contributes nonzero v3 activity (activity={activity_k!r}, "
            f"term_breakdown={term_breakdown_k!r}) -- an unadjudicated absent-"
            "source-substitution admission, the same KIND of gap sarvatobhadra_"
            "vedha had before IR-6 excluded it. NOT fixed here per PK-R-9a "
            "(zeroing it would itself be an unadjudicated scoring change); "
            "flagged for a future ruling, not silently patched.",
            stacklevel=2,
        )
    # DETECTED and REPORTED above (via the warning, when true). Deliberately
    # NOT `assert participates` (would freeze the residual as a required
    # contract) nor `assert not participates` (would silently mandate an
    # unauthorized fix) -- this test's contract is detection+reporting, not
    # a specific pass/fail outcome on the residual's direction.
    print(
        f"[PK-R-9a residual detector] kakshya_cell_crossing fallback participates in "
        f"v3 activity: {participates} (activity={activity_k!r})"
    )


# ── Detector (iii): regression guard -- degree_contact/eclipse_degree DO
#    contribute nonzero activity despite being unconditionally
#    uncited_extension=True ─────────────────────────────────────────────

def test_degree_contact_and_eclipse_degree_contribute_nonzero_activity_regression_guard():
    """PK-R-9a regression guard: `degree_contact` and `eclipse_degree` are
    BOTH unconditionally `uncited_extension=True` (gochara_grammar/
    primitives.py module docstring, families #1 and #10) -- exactly the
    flag IR-6's literal wording could have been misread as a blanket
    exclusion key. They are NOT absent-source-substitution markers (no
    detail field on either claims a real source was unreachable and
    something else substituted for it -- their uncited status is about the
    TECHNIQUE itself, not a degraded/approximated computation), so IR-6/
    PK-R-9a does not touch them, and they remain full, currently-load-
    bearing `_ACTIVITY_PRIMITIVES` members.

    This test proves they DO contribute nonzero activity in a realistic
    fixture where they fire -- a HARD assertion (unlike detector (ii)'s
    kakshya reporting-only check), so that if a future change re-introduces
    a blanket "any uncited_extension=True sentence contributes nothing"
    filter (the exact mistake PK-R-9a corrected), this test FAILS LOUDLY
    instead of silently deflating every v3 lambda_v3 evaluation that relies
    on these two primitive families."""
    from services.gochara_grammar import primitives as P
    from pipeline.transit_search import _get_planet_pos, SIGNS

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd0 = _jd(2020, 6, 15)
    lon, _ = _get_planet_pos(swe, "Saturn", jd0)
    target = ResonanceTarget(
        chart_id=CHART_ID, event_class="career_advancement", target_type="karaka",
        target_ref="Saturn", weight=0.9, classical_citation="TEST FIXTURE",
        target_longitude_deg=lon, target_sign=SIGNS[int(lon // 30.0) % 12],
    )
    start_jd, end_jd = _jd(2015, 1, 1), _jd(2025, 1, 1)
    weight_by_target_ref = {"Saturn": 1.0}

    degree_contact_sentences = P.degree_contact(swe, CHART_ID, target, start_jd, end_jd)
    assert len(degree_contact_sentences) >= 1, "expected >=1 real degree_contact sentence in this fixture"
    for s in degree_contact_sentences:
        assert s.uncited_extension is True  # confirms the precondition this guard is about

    eclipse_sentences = P.eclipse_degree(swe, CHART_ID, target, start_jd, end_jd)
    assert len(eclipse_sentences) >= 1, "expected >=1 real eclipse_degree sentence in this fixture"
    for s in eclipse_sentences:
        assert s.uncited_extension is True  # confirms the precondition this guard is about

    activity_dc, _, term_breakdown_dc = _compute_activity_v3(degree_contact_sentences, weight_by_target_ref)
    assert activity_dc > 0.0, (
        "degree_contact must contribute NONZERO v3 activity despite being "
        "unconditionally uncited_extension=True (PK-R-9a: it is not an "
        "absent-source-substitution marker) -- a blanket uncited_extension "
        "filter would wrongly zero this."
    )
    assert "degree_contact" in term_breakdown_dc

    activity_ec, _, term_breakdown_ec = _compute_activity_v3(eclipse_sentences, weight_by_target_ref)
    assert activity_ec > 0.0, (
        "eclipse_degree must contribute NONZERO v3 activity despite being "
        "unconditionally uncited_extension=True (PK-R-9a: it is not an "
        "absent-source-substitution marker) -- a blanket uncited_extension "
        "filter would wrongly zero this."
    )
    assert "eclipse_degree" in term_breakdown_ec
