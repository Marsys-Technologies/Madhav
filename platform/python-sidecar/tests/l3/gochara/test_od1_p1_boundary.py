"""SR-OD1 P1 self-check — the period lord's state-change instants are located to the MICROSECOND, on the builder and on the verifier.

`contact_reconstruct._core` answers with the UPPER bracket of an interval of up to `BISECT_SECONDS` (1 s): up to a second AFTER the real
change. The window solver probes every step factor 1 microsecond before each piece end (`window_solver.QUANT`) and refuses the window as
`state_boundaries_incomplete` when a listed change is later than that (its H2 contract: a listed instant is exact to ~1 microsecond), and the
verifier's pieces keep only cuts that fall strictly inside a support (`window_verifier._pieces`: `lo < c < hi`), so a cut located late past a
support end is lost. The nature list (`p1_nature_operands`) and the verifier's list (`p1_operands_check._search`) had the 1 s resolution; the
rung list (`p1_operands.P1Operands._exact`) already refined. Seven windows of each of three real classes went blank and one window per class
disagreed (0.25 against 0.125) because of it. The two refinements are independent code (K12).

The oracle is the sky itself, not the code under test: the real Sun ingress / Mercury company change / full moon is found HERE by a plain
bisect of the pinned Swiss ephemeris to 1 microsecond, and the doctrine for the state is BPHS 3.11 (`gochara_rules.nature.agent_nature`:
Mercury is malefic iff it shares a sign with a malefic; the waning Moon is a malefic). No database, no personal data.

Distinct production claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  B1  every change instant of the lord's NATURE the builder lists is the first microsecond of the new state
      (revert: `p1_nature_operands._microsecond` is the identity — the 1 s bracket returns);
  B2  a window whose support starts 21 microseconds after such a change is NUMBERED by the production solver, not blank
      (revert: as B1, observed through `solver=PRODUCTION_SOLVER`);
  V1  every change instant the verifier derives is the first microsecond of the new state
      (revert: `P1Check._search` returns `contact_reconstruct._core`'s answer unrefined);
  V2  builder and verifier produce the SAME objective on a window whose maximum is the sliver between a lord's sign change and the stored
      support end of a record 19 microseconds later (revert: as V1 — the verifier loses the cut and re-derives 0.125 for the builder's 0.25).
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import p1_nature_operands as ops
from services.gochara_kernel import window_sweep as ws

from .conftest import requires_swieph
from .test_od1_p1b_nature import MAPPING, _p1_record, _p1_rows, _swiss_position_at, rules, world
from .test_od1_p1c_operands_check import DIGNITY_ROWS, NAIS_ROWS, ORB_ROWS, P1Check, Sky, _check, p1_rows
from .test_od1_w0_interface import GRAIN, _Conn

UTC = timezone.utc
US = timedelta(microseconds=1)
#: the Sun leaves sidereal Leo (Mercury, still in Leo, stops sharing a sign with a malefic: malefic -> benefic); a public ephemeris event
SUN_LEAVES_LEO = (datetime(2010, 9, 15, tzinfo=UTC), datetime(2010, 9, 18, tzinfo=UTC))
#: USNO: full moon 2000-01-21 04:40 UTC (to the minute) — the waxing Moon turns waning (benefic -> malefic)
FULL_MOON = (datetime(2000, 1, 21, 0, 0, tzinfo=UTC), datetime(2000, 1, 21, 12, 0, tzinfo=UTC))


@pytest.fixture(autouse=True)
def _fresh_memo():
    """The chunked boundary memo is keyed by the sky's `cache_key`: a result computed under one test (or one planted reversion) must not
    answer another."""
    ops._MEMO.clear()
    yield
    ops._MEMO.clear()


def _first_true(pred, lo: datetime, hi: datetime) -> datetime:
    """The first microsecond at which `pred` holds, `pred(lo)` False and `pred(hi)` True — a plain bisect, independent of the code under test."""
    assert not pred(lo) and pred(hi)
    while hi - lo > US:
        mid = lo + (hi - lo) / 2
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return hi


def _sun_sign(pos, t):
    return int(pos("Sun", t) // 30.0)


def _sun_ingress(pos) -> datetime:
    """The first microsecond at which the Sun is no longer in the sign it holds at the start of `SUN_LEAVES_LEO`."""
    lo, hi = SUN_LEAVES_LEO
    start = _sun_sign(pos, lo)
    assert _sun_sign(pos, hi) != start
    return _first_true(lambda t: _sun_sign(pos, t) != start, lo, hi)


def _full_moon(pos) -> datetime:
    lo, hi = FULL_MOON
    waning = lambda t: (pos("Moon", t) - pos("Sun", t)) % 360.0 >= 180.0          # noqa: E731
    return _first_true(waning, lo, hi)


def _assert_first_microsecond(cuts, nature_at, expected: datetime, lo: datetime, hi: datetime):
    assert any(abs((c - expected) / US) <= 2 for c in cuts), (
        f"no listed change within 2 microseconds of the real one: nearest {min(abs((c - expected).total_seconds()) for c in cuts):.6f} s")
    for c in cuts:
        if lo < c < hi:
            assert nature_at(c - US) != nature_at(c), f"{c.isoformat()}: the new state is already in force a microsecond earlier"


# ── B1 / V1: the lists ───────────────────────────────────────────────────────────────────────────────────────────────

@requires_swieph
@pytest.mark.parametrize("graha, window, found", [("Mercury", SUN_LEAVES_LEO, _sun_ingress), ("Moon", FULL_MOON, _full_moon)])
def test_b1_the_builders_nature_change_instants_are_the_first_microsecond_of_the_new_state(graha, window, found):
    """BPHS 3.11: Mercury turns benefic the instant the Sun (a malefic) leaves its sign; the Moon turns malefic at the full moon. The
    builder's list holds that instant to within 2 microseconds, and for EVERY listed instant the new state is not yet in force a microsecond
    earlier. Planted reversion: `_microsecond` is the identity ⇒ the listed instant is up to a second late."""
    pos = _swiss_position_at()
    n = ops.NatureOperands(graha, pos)
    lo, hi = window
    _assert_first_microsecond(n.boundaries(lo, hi), n.nature_at, found(pos), lo, hi)


@requires_swieph
@pytest.mark.parametrize("graha, window, found", [("Mercury", SUN_LEAVES_LEO, _sun_ingress), ("Moon", FULL_MOON, _full_moon)])
def test_v1_the_verifiers_change_instants_are_the_first_microsecond_of_the_new_state(graha, window, found):
    """The same sky, the verifier's own derivation (`P1Check.nature_boundaries`, written without the builder's code). Planted reversion:
    `_search` hands back `_core`'s answer unrefined ⇒ the instant is up to a second late."""
    pos = _swiss_position_at()
    chk = P1Check(pos, dignity_rows=DIGNITY_ROWS, orb_rows=ORB_ROWS, naisargika_rows=NAIS_ROWS)
    lo, hi = window
    _assert_first_microsecond(chk.nature_boundaries(graha, lo, hi), lambda t: chk.nature_at(graha, t), found(pos), lo, hi)


# ── B2: the solver's H2 contract, end to end ─────────────────────────────────────────────────────────────────────────

@requires_swieph
def test_b2_a_window_whose_support_starts_microseconds_before_a_nature_change_is_numbered_by_the_production_solver():
    """Mercury in Leo, the stored support of its record starting 21 microseconds BEFORE the Sun leaves Leo (a stored contact edge is Swiss-bisected at
    1e-9 d, so it sits some 20 microseconds off the real sky event: the Sun's ingress both ends the Sun's residence and changes Mercury's company).
    The first piece [start, E) is malefic (Form B friend sign: adverse 0.5, the against channel), the second benefic (favourable 0.25, the for channel
    of the gain class "marriage"): the window is NUMBERED, 0.25 at E. Listed 0.6 s late, the change sat inside the first piece, the solver's
    1-microsecond probe before the piece end saw the new state there and the window went blank `state_boundaries_incomplete`.
    Planted reversion: as B1."""
    pos = _swiss_position_at()
    E = _sun_ingress(pos)
    lv = ops.P1LordValence(graha="Mercury", event_class="marriage", mapping=MAPPING, rules=rules("Mercury"), nature=ops.NatureOperands("Mercury", pos),
                           position_at=pos, combust_at=lambda t: False, rung_boundaries=lambda lo, hi: [])
    rec = dataclasses.replace(_p1_record(lv, "mercury"), supports=((E - 21 * US, E + timedelta(days=2)),))
    (draft,), _ = ws.draft_windows("marriage", [rec], _p1_rows, solver=ws.PRODUCTION_SOLVER)
    assert draft.unqualified_reason is None, draft.unqualified_reason
    assert draft.objective_value == pytest.approx(0.25)
    assert abs((draft.peak_instant - E) / US) <= 2


# ── V2: builder and verifier on the sliver ───────────────────────────────────────────────────────────────────────────

def test_v2_builder_and_verifier_agree_on_a_window_whose_maximum_is_a_sliver_at_a_support_end():
    """Mercury crosses from Pisces (debilitated, adverse) into Aries (neutral sign: favourable 0.125, owner's Form B) at an instant E that is not on
    any search lattice. Two records of Mercury, two roots: one supports until E + 19 microseconds (the stored edge of the same sky event), the other
    spans E. For the gain class "marriage" the objective is the sum over roots of the favourable value: 0 before E, 0.25 in [E, E+19us), 0.125 after.
    The builder's rung list is exact; the verifier locates the same E from the sky alone. A verifier that locates it late loses the cut (it falls past
    the first record's support end) and re-derives 0.125 for the builder's 0.25 — `objective_value 0.25 != re-derived 0.125`, the production message.
    SR-P1-SLIVER-D2 (supersedes the 0.25): the 19 us piece is shorter than one JD ulp (40.2 us), one sky event read on two paths, so it is no candidate for the
    maximum: BOTH sides number 0.125, first reached where the first record's support ends (E + 19 us), and the builder counts the excluded piece.
    Planted reversion: as V1."""
    base = datetime(2010, 1, 1, tzinfo=UTC)                           # day 0 of both analytic worlds (`_d(0)`, `T0`)
    t_cross = base + timedelta(days=1, hours=7, seconds=13, microseconds=123456)
    rate = 1.0                                                        # degrees per day
    lon0 = 360.0 - rate * (t_cross - base).total_seconds() / 86400.0
    sky = Sky(mercury=(lon0, rate))                                   # verifier's world: Sun in Libra, Moon in Gemini, nobody in Pisces / Aries
    b_pos = world(Mercury=(lon0, rate))                               # the builder's world: the same Mercury, the same defaults far from it
    E = _first_true(lambda t: _lon_sign(sky, t) == "Aries", base, base + timedelta(days=3))
    lv = ops.P1LordValence(graha="Mercury", event_class="marriage", mapping=MAPPING, rules=rules("Mercury"), nature=ops.NatureOperands("Mercury", b_pos),
                           position_at=b_pos, combust_at=lambda t: False, rung_boundaries=lambda lo, hi: [E] if lo < E < hi else [])
    r1 = dataclasses.replace(_p1_record(lv, "mercury"), record_id="r1", root_id="root1", supports=((base, E + 19 * US),))
    r2 = dataclasses.replace(_p1_record(lv, "mercury"), record_id="r2", root_id="root2", supports=((base + timedelta(hours=12), base + timedelta(days=3)),))
    (draft,), _ = ws.draft_windows("marriage", [r1, r2], lambda path, version: p1_rows(), solver=ws.PRODUCTION_SOLVER)     # the rows the verifier reads too
    assert draft.unqualified_reason is None and draft.objective_value == pytest.approx(0.125)      # D2: not 0.25 — that maximum lived on the 19 us sliver
    assert draft.sliver_pieces_excluded == 1 and abs((draft.peak_instant - (E + 19 * US)) / US) <= 2
    lo, hi = draft.interval
    stored = ("w", lo, hi, draft.peak_instant, draft.score, draft.evidence_for, draft.evidence_against, None, list(draft.null_states_used),
              draft.outcome_valence_for_native, None, None, None)
    records = [(r.record_id, r.root_id, "residence", "sign_span", "mercury", None, r.supports[0][0], r.supports[0][1]) for r in (r1, r2)]
    conn = _Conn([stored], records, [("w", "r1"), ("w", "r2")])
    report = _verify_draft(conn, sky)
    assert report["numeric_reproduced"] == 1 and report["status"] == "VERIFIED"


def _lon_sign(sky, t) -> str:
    from services.gochara_rules.p1_inputs import SIGNS
    return SIGNS[int(sky("mercury", t) // 30.0) % 12]


def _verify_draft(conn, sky):
    from services.gochara_kernel import window_verifier as wv
    return wv.verify_window_semantics(conn, factor_rows=p1_rows(), p1_check=_check(sky), dynamic_enabled=True, policy=wv.POLICY_VERSION,
                                      **{**GRAIN, "event_class": "marriage"})
