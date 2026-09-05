"""
NIRMĀṆA L3-W3 — `c_panchanga_quality` was a computed zero that had never been computed.

THE DEFECT (§N.8, §N.7 item 6). `_c_panchanga_quality` is called with `event='general'`, which
is **not** in `muhurat.finder.EVENTS_MVP` — a curated eight-event set settled D2 2026-05-19. So
`muhurta_service.score()` raises on every call, a bare `except` swallowed it at DEBUG, and the
function returned **0.0 on 4,729 of 4,729 Mode A/B rows** — every row that carries the key.

Two silent consequences:
  * `constituent_factors.currents.panchanga` is derived as `c_panchanga_quality > 0.0`, so every
    row asserted "pāñcāṅga did not support this window" when the truth was "pāñcāṅga was never
    consulted";
  * that current feeds `independent_current_count` (the I-22 coupling discount), so independence
    was systematically understated by a term nothing had evaluated.

WHAT THIS FIX DOES AND DOES NOT DO. It does **not** recover the 0.070 weight budget — that needs a
general-purpose pāñcāṅga quality `ka_muhurta_seva` deliberately does not expose, and substituting
one of the eight curated events as a proxy would invent a semantic. It makes the absence
**reportable** instead of indistinguishable from a real zero score.
"""
from __future__ import annotations

import datetime as dt

import pytest

from services.ka_sangam import engine as eng


class _RaisingService:
    """What the real service does with event='general': it refuses."""

    def score(self, *_a, **_k):
        raise ValueError("unsupported event 'general'; supported: EVENTS_MVP")


class _ScoringService:
    def __init__(self, value): self.value = value
    def score(self, *_a, **_k): return self.value


LOC = {"lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330}
WHEN = dt.date(2026, 9, 5)


def test_unsupported_event_returns_None_not_zero() -> None:
    """The whole defect in one assertion: a term that cannot be evaluated is None, not 0.0."""
    got = eng._c_panchanga_quality(WHEN, _RaisingService(), LOC)
    assert got is None, "an unevaluatable term must be None — 0.0 is indistinguishable from a real score"


def test_missing_service_or_location_is_also_None() -> None:
    assert eng._c_panchanga_quality(WHEN, None, LOC) is None
    assert eng._c_panchanga_quality(WHEN, _ScoringService(80.0), None) is None


def test_a_real_score_still_comes_through_normalised() -> None:
    """The guard must be selective: a service that answers is still believed."""
    assert eng._c_panchanga_quality(WHEN, _ScoringService(80.0), LOC) == pytest.approx(0.8)
    assert eng._c_panchanga_quality(WHEN, _ScoringService(0.0), LOC) == pytest.approx(0.0), (
        "a genuine zero must survive as 0.0 — that is exactly the value the fix protects"
    )
    # And clamped.
    assert eng._c_panchanga_quality(WHEN, _ScoringService(250.0), LOC) == pytest.approx(1.0)


def test_the_failure_is_loud_once_not_silent_per_row(caplog: pytest.LogCaptureFixture) -> None:
    """A per-row DEBUG line is how this stayed invisible; it warns once per process instead."""
    eng._PANCHANGA_UNAVAILABLE_WARNED = False
    with caplog.at_level("WARNING"):
        eng._c_panchanga_quality(WHEN, _RaisingService(), LOC)
        eng._c_panchanga_quality(WHEN, _RaisingService(), LOC)
    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1, "must warn exactly once per process, not per row"
    assert "NOT COMPUTABLE" in warnings[0].getMessage()


def test_an_absent_supporting_key_contributes_nothing_and_a_zero_is_different() -> None:
    """
    Why omission is the correct encoding: the combiner is saturating,
    `1 - Π(1 - w_i * s_i)`, and does `sup.get(key, 0.0)`. So an ABSENT key already means
    "contributes nothing" — identical arithmetic to an explicit 0.0, but distinguishable in the
    record. This test pins that equivalence so the omission cannot be mistaken for a score change.
    """
    with_zero = eng.convergence_score([], {"panchanga_quality": 0.0, "tara_bala": 0.5})
    omitted = eng.convergence_score([], {"tara_bala": 0.5})
    assert with_zero == pytest.approx(omitted), (
        "omitting the key must be arithmetically identical to passing 0.0 — the fix changes the "
        "record, not the score"
    )


# ── C7 ashtakavarga: the same shape, with a second defect that makes a naive fix dangerous ──


class _Ctx:
    def __init__(self, bindu): self.ashtakavarga_bindu = bindu


def test_c7_returns_None_when_the_planet_key_does_not_match() -> None:
    """
    The live case: the map is keyed by the stored L1 vocabulary (JUP/MAR/MER/...), the caller
    passes Title-case ("Jupiter"), so the lookup never matches. Measured: 0.0 on 4,729 of 4,729
    rows carrying the key. It must now report not-evaluated, not a zero score.
    """
    ctx = _Ctx({"JUP": {5: 6}})
    assert eng._c7_ashtakavarga_potency("Jupiter", 5, ctx) is None


def test_c7_returns_None_rather_than_a_repaired_number() -> None:
    """
    Deliberately NOT fixed here, and this test pins that decision so a later reader does not
    'complete' it by accident.

    The stored facts are keyed `<GRAHA>-HOUSE_<N>`; this function looks up by `transit_sign`
    (rāśi). Those are different frames. **Both canonical charts have Āries lagna**, where
    house N ≡ sign N — so a vocabulary-only fix would look perfectly correct on every chart the
    campaign builds and be silently wrong for any non-Āries-lagna chart. The frame question is an
    adjudication, not an inference.
    """
    ctx = _Ctx({"JUP": {5: 6}})
    # Even with the canonical key spelled exactly as stored, the term stays unevaluated.
    assert eng._c7_ashtakavarga_potency("JUP", 5, ctx) is None, (
        "c7 must remain held until the HOUSE-vs-SIGN frame is ruled; producing a number here "
        "would be plausible on both Āries-lagna charts and wrong elsewhere"
    )


def test_c7_is_None_when_there_is_nothing_to_look_up() -> None:
    assert eng._c7_ashtakavarga_potency("JUP", None, _Ctx({"JUP": {5: 6}})) is None
    assert eng._c7_ashtakavarga_potency("JUP", 5, _Ctx({})) is None
