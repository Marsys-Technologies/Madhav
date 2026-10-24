"""SR-OD1 R2 (SR-PLAN-REVIEW-RECONCILED, ruling R-2 / SR-H2-1S) — boundary completeness of the P1 state providers.

The window solver maximises a step factor EXACTLY, so a state island of a few seconds (a graha sitting on a sign edge through a
station dips across it and back) is a real part of the objective. `contact_reconstruct._core` cannot exclude an excursion shorter
than its floor, and the contact geometry's floor is 60 s: the independent review's probe (GPT-6.1 B3, `review_probes.py`) saw an
empty cut list for a 10 s island. R-2: the P1 state providers search at a 1 s floor (`STATE_MIN_EXCURSION_SECONDS` = the bisection
resolution, matching the owner's "to the second", Q12), the named limit says so, and a change instant belongs to the NEW state
(half-open `[change, next change)`).

The analytic sky is a V-shaped longitude with a closed form: the body is on the far side of an edge for exactly `|s - s0| < 5` seconds
(a 10 s island) and its speed stays below `VMAX_DPS` — the device's own smooth-motion assumption. Each oracle names its single
planted reversion; every one was run (R-2's fail-on-revert proof, see the job result).

  R2-1 a 10 s sign-ingress island is FOUND by the builder's dignity provider (revert: `P1Operands._exact` at the default 60 s floor)
  R2-2 the same island is found by the verifier's independent provider (revert: `P1Check._search` at the default floor)
  R2-3 a 10 s Moon-pakṣa island is found by the nature provider (revert: the pakṣa search at the default floor)
  R2-4 a change instant belongs to the NEW state: the builder's microsecond, the verifier's located instant (revert: `_refine` returns
       the last OLD microsecond)
  R2-5 the named limit says 1 s and the ownership rule, and the P1 modules publish it (revert: the P1 modules publish the 60 s text)
  R2-6 the 1 s floor stays affordable: only cells the speed bound cannot clear are bisected (revert: the pruning removed)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.gochara_kernel import contact_reconstruct as cr
from services.gochara_kernel import p1_nature_operands as nat
from services.gochara_kernel import p1_operands as P
from services.gochara_kernel import p1_operands_check as p1c

from .test_od1_p1c_operands_check import Sky, _check
from .test_p1a_operands import RULES, T0, d, l0

UTC = timezone.utc
S0 = 3 * 86400.0 + 1234.567                         # the island's centre, seconds after T0 (off every sampling grid)
HALF = 5.0                                          # half-width: a 10 s island
SLOPE = 3.9e-6                                      # deg/s, just under VMAX_DPS["jupiter"] = 0.35 deg/day = 4.05e-6 deg/s
MOON_SLOPE = 1.8e-4                                 # deg/s, just under VMAX_DPS["moon"] = 16 deg/day = 1.85e-4 deg/s
LO, HI = T0, T0 + timedelta(days=6)


def _secs(t: datetime) -> float:
    return (t - T0).total_seconds()


def _island_jupiter(t: datetime) -> float:
    """Jupiter at 240° (the Scorpio / Sagittarius edge) + SLOPE·(|s − s0| − 5): in Scorpio for exactly the 10 s |s − s0| < 5."""
    return 240.0 + SLOPE * (abs(_secs(t) - S0) - HALF)


def _expected() -> tuple[datetime, datetime]:
    return T0 + timedelta(seconds=S0 - HALF), T0 + timedelta(seconds=S0 + HALF)


def _sign_of(lon: float) -> int:
    return int((lon % 360.0) // 30.0)


def test_r2_1_the_builders_dignity_provider_finds_a_ten_second_sign_ingress_island():
    """GPT-6.1 B3, reproduced on the REAL provider (`P1Operands`): Jupiter is in Scorpio for 10 s and in Sagittarius either side. The
    dignity source lists BOTH change instants, located to a millisecond, and the rung read just inside the island differs from the one
    outside (Sagittarius Jupiter is mūlatrikoṇa, Scorpio is not). Control: the contact geometry's own 60 s floor returns NO cut for the
    same state function — the probe — so the oracle can read false. Planted reversion: `_exact` calls `_core` at its default floor."""
    ops = P.P1Operands(l0(), lambda body, t: _island_jupiter(t) if body == "Jupiter" else 340.0, rules=RULES)
    want_in, want_out = _expected()
    found = ops.ingress("Jupiter", LO, HI)
    assert len(found) == 2, found
    for got, want in zip(found, (want_in, want_out)):
        assert abs((got - want).total_seconds()) < 1e-3, (got, want)
    src = ops.sources_for("Jupiter", complete=True)[P.FACTOR_DIGNITY]
    bounds = src.boundaries(LO, HI)
    for want in (want_in, want_out):
        assert any(abs((b - want).total_seconds()) < 1e-3 for b in bounds), (bounds, want)
    mid = T0 + timedelta(seconds=S0)
    assert src.value_at(mid) != src.value_at(mid - timedelta(seconds=30))
    # the control: the SAME state at the contact geometry's default floor (60 s) sees nothing
    state = lambda t: _sign_of(_island_jupiter(t))                                                    # noqa: E731
    edge = lambda t: min(_island_jupiter(t) % 30.0, 30.0 - _island_jupiter(t) % 30.0)                 # noqa: E731
    vmax = cr.VMAX_DPS["jupiter"]
    assert cr._core(state, edge, vmax, LO, HI) == []
    assert len(cr._core(state, edge, vmax, LO, HI, min_excursion_seconds=cr.STATE_MIN_EXCURSION_SECONDS)) == 2


def _verifier_sky(jupiter_fn):
    base = Sky()

    def pos(body, t):
        return jupiter_fn(t) if body == "jupiter" else base(body, t)
    return pos


def test_r2_2_the_verifiers_independent_provider_finds_the_same_island():
    """The verifier derives its own change instants (`P1Check`, no builder import). The same 10 s island: both instants are found
    within the checker's stated location tolerance (`PEAK_TOLERANCE_SECONDS`), so the builder and the verifier cannot agree on a
    list that is missing it. Planted reversion: `P1Check._search` at the default 60 s floor — the list is empty."""
    chk = _check(_verifier_sky(_island_jupiter))
    found = chk.dignity_boundaries("Jupiter", LO, HI)
    # the dignity list can hold both the ingress and the mūlatrikoṇa edge at one instant; each expected instant must be there
    for want in _expected():
        assert any(abs((b - want).total_seconds()) <= p1c.PEAK_TOLERANCE_SECONDS for b in found), (found, want)


def _moon_island_sky():
    """Sun fixed at 100°; the Moon's elongation is 180° + MOON_SLOPE·(5 − |s − s0|): waning (≥ 180°) for exactly 10 s."""
    base = Sky()

    def pos(body, t):
        b = body.lower()
        if b == "moon":
            return (100.0 + 180.0 + MOON_SLOPE * (HALF - abs(_secs(t) - S0))) % 360.0
        if b == "sun":
            return 100.0
        return base(b, t)
    return pos


def test_r2_3_the_nature_provider_finds_a_ten_second_moon_paksa_island():
    """P1b's Moon-pakṣa list (`NatureOperands`, BPHS 3.11: the Moon is benefic waxing, malefic waning) over a 10 s waning island across
    the 180° elongation: both flips are listed, within a second. Planted reversion: the pakṣa search at the default 60 s floor."""
    found = nat.NatureOperands("Moon", _moon_island_sky()).boundaries(LO, HI)
    for want in _expected():
        assert any(abs((b - want).total_seconds()) <= 1.001 for b in found), (found, want)
    assert len(found) == 2, found


def test_r2_4_a_change_instant_belongs_to_the_new_state_half_open():
    """Jupiter 237.97° + 0.2°/d crosses 240° (Scorpio → Sagittarius) on day 10.15. The builder lists the FIRST microsecond of
    Sagittarius: the state AT the instant is the new one and the state one microsecond earlier is the old one; the dignity source's
    value flips exactly there. The verifier's located instant is the first sample already in the new state (within its tolerance of the
    closed form). Planted reversion: the microsecond refinement returns the last OLD microsecond (`a`, not `b`)."""
    ops = P.P1Operands(l0(), lambda body, t: (237.97 + 0.2 * _secs(t) / 86400.0) if body == "Jupiter" else 340.0, rules=RULES)
    (b,) = ops.ingress("Jupiter", d(0), d(20))
    assert abs((b - d(10.15)).total_seconds()) < 1e-3
    us = timedelta(microseconds=1)
    assert ops.lon("Jupiter", b - us) < 240.0 <= ops.lon("Jupiter", b)
    src = ops.sources_for("Jupiter", complete=True)[P.FACTOR_DIGNITY]
    assert src.value_at(b - us) != src.value_at(b)
    chk = _check(Sky(jupiter=(237.97, 0.2)))
    (c,) = [x for x in chk.dignity_boundaries("Jupiter", d(0), d(20)) if abs((x - d(10.15)).total_seconds()) <= 2.0]
    assert chk.sign_of("jupiter", c)[0] == "Sagittarius"
    assert chk.sign_of("jupiter", c - timedelta(seconds=p1c.PEAK_TOLERANCE_SECONDS + 0.001))[0] == "Scorpio"


def test_r2_5_the_named_limit_states_one_second_and_the_ownership_rule_and_the_p1_modules_publish_it():
    """The owner's "to the second" (Q12): the P1 floor IS the bisection resolution and the text says so, with the ownership rule. The
    P1 builder and the P1 verifier publish that text; the contact geometry (no solver on top of it) keeps its own 60 s statement.
    Planted reversion: the P1 modules publish `contact_reconstruct.NAMED_LIMIT` (the 60 s text)."""
    assert cr.STATE_MIN_EXCURSION_SECONDS == cr.BISECT_SECONDS == 1.0
    text = cr.STATE_NAMED_LIMIT
    assert "excursions shorter than 1 s are not excluded" in text and "60" not in text
    assert "belongs to the NEW state" in text and "half-open" in text
    assert P.NAMED_LIMIT == p1c.NAMED_LIMIT == text
    assert cr.MIN_EXCURSION_SECONDS == 60 and "shorter than 60 s are not excluded" in cr.NAMED_LIMIT


def test_r2_6_the_one_second_floor_only_bisects_cells_the_speed_bound_cannot_clear():
    """A graha with ONE sign ingress in 30 days is sampled every 6 hours (121 steps) plus the bisection of the cells the speed bound
    cannot clear: the cost is bounded by the number of edges, not by the floor. A floor applied to every cell (2**15 leaves per
    6-hour step) would be a hundred thousand evaluations. Planted reversion: the VMAX pruning removed (`refine` never returns early)."""
    calls = {"n": 0}

    def pos(body, t):
        calls["n"] += 1
        return 237.97 + 0.2 * _secs(t) / 86400.0 if body == "Jupiter" else 340.0
    ops = P.P1Operands(l0(), pos)
    assert len(ops.ingress("Jupiter", d(0), d(30))) == 1
    assert calls["n"] < 1500, calls["n"]
