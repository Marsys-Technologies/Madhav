"""SR-OD1 P1a — P1's dignity / combustion / maitrī operand sources, step-boundary providers and L0 loaders + digests (plan §3.3).

P1a adds NO doctrine value: every category → value table below is a test stub; the rules under test are the owner's ruled ladder
(P1-MAPPING-DECISION = ANSWERS.md v2.1 §B.2, "the order matters") and L1's own rules (CLAUDE.md §N.5), over the LITERAL L0 tables read
from production 2026-10-02 (`tests/l3/gochara_rules/fixtures`). The sky is an analytic ephemeris with closed-form crossings.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  P-1 the effective rung follows the owner's order COMB > EX > MT > OWN > DEB > FR/NEU/INI, one golden case per rung and the cases the
      ruling names (revert: test friendship before debility, so Jupiter in Capricorn reads NEU);
  P-2 exaltation outranks mūlatrikoṇa inside one sign — the Moon's Taurus and Mercury's Virgo read EX throughout (revert: L1's order,
      mūlatrikoṇa first);
  P-3 friendship is the PERIOD LORD's own table (L0 `graha = period lord`), never the sign lord's (revert: swap the two columns);
  P-4 combustion is L1's state: the retrograde orb of Mercury / Venus applies when the stored stations say retrograde (revert: always
      direct); the Sun and the nodes are a DECLARED non-applicability, an `na` outcome in the sweep — not a 1.0;
  P-5 the dignity boundaries are COMPLETE: sign ingress, the in-sign mūlatrikoṇa edge (N-2) and the combustion crossings — a dense scan of
      the factor's value finds no change that is not listed (revert: no mūlatrikoṇa edge);
  P-6 the combustion boundaries are complete over a station-flipped orb regime and exact to a millisecond (revert: no microsecond
      refinement — the 1-second device alone);
  P-7 a node in a sign the verse reserves for it (not in L0) is UNQUALIFIED, never classified by friendship; the variant own signs and
      the disputed friendships are disclosed (revert: classify by friendship);
  P-8 a delivery form (Sun / Jupiter through another lord's sign) is judged by the period ANCHOR's sky, not the transiting agent's
      (revert: read the agent);
  P-9 a Mercury / Venus source is complete only with the stored stations (revert: ignore the stations in `complete`);
  P-10 the L0 digest covers every consumed cell and no surrogate (revert: leave `relation` out of the naisargika preimage), and the
       loaders refuse an incomplete / duplicated / L0-L1-divergent table by name;
  P-11 the three tables are bound into the input vector through those loaders, and only when the build binds the P1 sources (revert:
       `l0_identities` does not know the P1 assets);
  P-13 the pañcadhā maitrī source (retired from the new rule version by Q7 b, kept for the factor sets that still carry it) is cut at
       the lord's AND its sign lord's ingress and reads naisargika + tatkālika (revert: the sign lord's ingress is not a boundary);
  P-12 the store hands the sources to P1 records, from the record's anchor and the stored stations, and refuses an applied schema
       without the anchor column (revert: build the sources from `rec.agent`).
"""
from __future__ import annotations

import contextlib
import copy
import dataclasses
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import p1_operands as P
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.window_sweep import OperandSource
from services.gochara_rules import p1_inputs as p1

from .test_a53_window_sweep import _rec

UTC = timezone.utc
T0 = datetime(2010, 1, 1, tzinfo=UTC)              # = test_a53_window_sweep.T0: `_rec`'s supports and this sky share one clock
FIX = Path(__file__).resolve().parents[1] / "gochara_rules" / "fixtures"
DIG = json.loads((FIX / "l0_dignity_reference_2026_10_02.json").read_text())
COMB = json.loads((FIX / "l0_combustion_orbs_2026_10_02.json").read_text())
NAIS = json.loads((FIX / "l0_naisargika_2026_10_02.json").read_text())
SIGNS = p1.SIGNS


def d(days: float) -> datetime:
    return T0 + timedelta(days=days)


def l0(dig=DIG, comb=COMB, nais=NAIS) -> P.P1L0:
    return P.P1L0(P.dignity_reference_from_rows(dig), P.combustion_orbs_from_rows(comb), P.naisargika_from_rows(nais))


def sky(**bodies):
    """An analytic ephemeris: each body is `days -> longitude`."""
    def position_at(body, t):
        return bodies[body]((t - T0).total_seconds() / 86400.0)
    return position_at


def line(lon0, rate=0.0):
    return lambda days: (lon0 + rate * days) % 360.0


#: distinct values per rung so a scan sees every change (a TEST table, not doctrine)
RUNG_VALUE = {"COMB": 0.9, "EX": 1.0, "MT": 0.8, "OWN": 0.7, "DEB": 0.6, "FR": 0.5, "NEU": 0.4, "INI": 0.3}
RUNG_RULE = P.category_rule(RUNG_VALUE)
COMBUST_RULE = P.category_rule({True: 1.0, False: 0.5}, key=lambda s: s.combust)
RULES = {P.FACTOR_DIGNITY: RUNG_RULE, P.FACTOR_COMBUSTION: COMBUST_RULE}


def state_of(graha, sign, deg, *, l0_=None, sun=None):
    """The lord's state at T0 standing at `deg` of `sign`, the Sun 100° away (no combustion unless `sun` says so)."""
    lon = SIGNS.index(sign) * 30.0 + deg
    sun_lon = (lon + 100.0) % 360.0 if sun is None else sun
    bodies = {"Sun": line(sun_lon), graha: line(lon, 0.01)}                 # the lord wins when it IS the Sun
    ops = P.P1Operands(l0_ or l0(), sky(**bodies))
    stations = (d(-30),) if graha in ("Mercury", "Venus") else None      # direct motion since a station 30 days earlier
    return ops.view(graha, stations).state(T0)


def scan(source: OperandSource, lo, hi, step=timedelta(minutes=15)):
    """Every change of the source's value over a dense grid must sit in a listed boundary (the H2 detector)."""
    bounds = source.boundaries(lo, hi)
    t, prev, missed, changes = lo, source.value_at(lo), [], 0
    while t < hi:
        t2 = min(t + step, hi)
        cur = source.value_at(t2)
        if cur != prev:
            changes += 1
            if not any(t < b <= t2 for b in bounds):
                missed.append((t, t2, prev, cur))
        t, prev = t2, cur
    return bounds, missed, changes


# ── P-1 / P-2 / P-3: the effective rung ───────────────────────────────────────────────────────────────────────────────

LADDER = [   # ANSWERS.md v2.1 §B.2 "golden cases, one per rung" — (graha, sign, degree, rung)
    ("Jupiter", "Cancer", 10, "EX"), ("Saturn", "Libra", 10, "EX"),
    ("Sun", "Leo", 10, "MT"), ("Jupiter", "Sagittarius", 5, "MT"),
    ("Sun", "Leo", 25, "OWN"), ("Venus", "Taurus", 15, "OWN"),
    ("Jupiter", "Capricorn", 10, "DEB"), ("Sun", "Libra", 10, "DEB"), ("Venus", "Virgo", 10, "DEB"), ("Mercury", "Pisces", 10, "DEB"),
    ("Jupiter", "Aries", 10, "FR"), ("Saturn", "Taurus", 10, "FR"),
    ("Jupiter", "Aquarius", 10, "NEU"), ("Mars", "Taurus", 10, "NEU"),
    ("Jupiter", "Gemini", 10, "INI"), ("Mars", "Virgo", 10, "INI"),
]


@pytest.mark.parametrize("graha,sign,deg,rung", LADDER)
def test_p1_the_effective_rung_follows_the_owners_ladder_one_golden_case_per_rung(graha, sign, deg, rung):
    """Debility is tested BEFORE friendship — Jupiter in Capricorn is DEB although Saturn is neutral to Jupiter, Sun in Libra is DEB not
    INI (ANSWERS §B.2 step 5/6). Planted reversion: friendship first ⇒ Jupiter in Capricorn reads NEU and this fails."""
    s = state_of(graha, sign, deg)
    assert (s.rung, s.unknown_reason) == (rung, None)


def test_p1_combustion_overrides_every_rung_below_it():
    """L1 'combust' = COMB, whatever the sign (ANSWERS §B.2 step 1; XX.30 tail: combustion is 'similar to that in depression')."""
    for graha, sign, deg, below in (("Mars", "Scorpio", 5, "OWN"), ("Jupiter", "Cancer", 10, "EX"), ("Mars", "Capricorn", 10, "EX")):
        lon = SIGNS.index(sign) * 30.0 + deg
        s = state_of(graha, sign, deg, sun=lon + 5.0)
        assert (s.rung, s.combust, s.dignity_rung) == ("COMB", True, below)
    outside = state_of("Mars", "Scorpio", 5, sun=SIGNS.index("Scorpio") * 30.0 + 5 + 18.0)       # arc 18 > the Mars orb 17
    assert (outside.rung, outside.combust) == ("OWN", False)


def test_p2_exaltation_outranks_moolatrikona_inside_one_sign():
    """The Moon's Taurus and Mercury's Virgo read EX throughout; their mūlatrikoṇa portions are absorbed (ANSWERS §B.2). L1 tests the
    mūlatrikoṇa range first (`dignity_d1_from_sign`), so the owner's order needs the remap. Planted reversion: return L1's category as is."""
    assert state_of("Moon", "Taurus", 10).rung == "EX"                   # L0 Moon mūlatrikoṇa is Taurus 4°-30°
    assert state_of("Mercury", "Virgo", 17).rung == "EX"                 # L0 Mercury mūlatrikoṇa is Virgo 16°-20°
    assert state_of("Sun", "Leo", 10).rung == "MT"                       # where the two signs differ, mūlatrikoṇa is still its own rung


def test_p3_friendship_is_the_period_lords_own_table_not_the_sign_lords():
    """BJ II.16-17 translator's note (brihat_jataka:PG69:C1): 'the particular planet's table and not the table of the ruler of the house where
    he is in'. The three pairs are asymmetric in L0: Jupiter→Mercury enemy (Mercury→Jupiter neutral), Mars→Mercury enemy
    (Mercury→Mars neutral), Moon→Saturn neutral (Saturn→Moon enemy). Planted reversion: look the pair up as (sign lord, period lord)."""
    j = state_of("Jupiter", "Gemini", 10)
    assert (j.rung, j.friendship, j.sign_lord) == ("INI", "enemy", "Mercury")
    assert state_of("Mars", "Virgo", 10).rung == "INI"
    assert state_of("Moon", "Capricorn", 10).rung == "NEU"
    nais = {(r["graha"], r["other_graha"]): r["relation"] for r in NAIS}
    assert nais[("Mercury", "Jupiter")] == "neutral" and nais[("Saturn", "Moon")] == "enemy"       # the swapped answers differ


# ── P-4: combustion is L1's state ─────────────────────────────────────────────────────────────────────────────────────

def test_p4_the_retrograde_orb_of_mercury_applies_when_the_stored_stations_say_retrograde():
    """L1 `check_combustion` (M-19): Mercury combusts within its DEEP orb (12°) while retrograde, 14° while direct. Arc 13°: combust direct,
    not combust retrograde. Planted reversion: the retrograde flag is always False."""
    direct = P.P1Operands(l0(), sky(Mercury=line(113.0, 0.5), Sun=line(100.0))).view("Mercury", (d(-30),)).state(T0)
    retro = P.P1Operands(l0(), sky(Mercury=line(113.0, -0.5), Sun=line(100.0))).view("Mercury", (d(-30),)).state(T0)
    assert (direct.combust, direct.rung) == (True, "COMB")
    assert (retro.combust, retro.rung) == (False, "INI")             # not combust ⇒ the dignity rung decides (Cancer: Mercury→Moon is enemy)


def test_p4_the_sun_and_the_nodes_are_a_declared_non_applicability_in_the_sweep():
    """L1 M-19 / bphs:PG99:C1 ('Rahu and Ketu should not be treated as combust … they are only mathematical points'): combustion is `na` —
    takes no part in the product — which is a different statement from 'contributes 1.0'. Planted reversion: the source carries no
    `not_applicable` and the node's combustion reads the neutral element 1.0."""
    row = {"factor_id": "combustion", "rule_version": "9.0.0", "null_state": "unqualified", "function": "step"}
    ops = P.P1Operands(l0(), sky(Rahu=line(10.0, -0.05), Sun=line(200.0), Jupiter=line(50.0, 0.1)), rules=RULES)
    for lord, expect_na in (("Rahu", True), ("Jupiter", False)):
        rec = ops.attach(_rec("r", path="P1", agent=lord.lower(), kind="house_span", supports=((0, 5),)), complete=True)
        out = ws.categorical_factor(row, rec)
        assert (out.kind == "na") is expect_na, (lord, out)
    sun = P.P1Operands(l0(), sky(Sun=line(10.0, 1.0)), rules=RULES).sources_for("Sun", complete=True)[P.FACTOR_COMBUSTION]
    assert sun.not_applicable is True


def test_p4_the_retrograde_state_is_the_parity_of_the_stored_stations_even_at_a_station():
    """At a station the speed is ~0, so the regime is read from a probe a safe distance from it, never by a finite difference AT the instant
    (the piece that starts exactly at a station is evaluated there). Direct to day 0, retrograde days 0-25, direct again after.
    Planted reversion: probe the direction at `t` itself — undeterminable at the station instants."""
    def mercury(days):
        return 200.0 + 0.5 * days if days <= 0 else (200.0 - 0.5 * days if days <= 25 else 187.5 + 0.5 * (days - 25))
    v = P.P1Operands(l0(), sky(Mercury=mercury, Sun=line(20.0))).view("Mercury", [d(0), d(25)])
    got = {x: v.retrograde_at(d(x)) for x in (-5, 0, 5, 24, 25, 30)}
    assert got == {-5: False, 0: True, 5: True, 24: True, 25: False, 30: False}


# ── P-5 / P-6: the boundary providers ─────────────────────────────────────────────────────────────────────────────────

def test_p5_dignity_boundaries_are_complete_ingress_and_the_in_sign_moolatrikona_edge():
    """Jupiter 237.97° + 0.2°/d crosses 240° (ingress into Sagittarius) at day 10.15, the mūlatrikoṇa edge 250° (L0 Sagittarius 0°-10°) at
    day 60.15 and 270° at day 160.15; the Sun, 100° + 1°/d, closes to Jupiter's orb (arc 137.97 − 0.8 d ≤ 11°) at day 158.7125. A dense scan
    of the factor's value finds no change that is not listed (the H2 detector), and the listed instants are the closed-form ones. Planted
    reversion: the provider lists ingress only (`DESIGN.md` §F-C 'constant over a residence', refuted by N-2) — the day-60.15 MT→OWN change
    and the combustion entry are missed. (The day-160.15 ingress changes the dignity rung but not the effective one, COMB: listed, a superset.)"""
    ops = P.P1Operands(l0(), sky(Jupiter=line(237.97, 0.2), Sun=line(100.0, 1.0)), rules=RULES)
    src = ops.sources_for("Jupiter", complete=True)[P.FACTOR_DIGNITY]
    bounds, missed, changes = scan(src, d(0), d(165))
    assert missed == [] and changes == 3
    assert len(bounds) == 4
    for got, want in zip(bounds, (d(10.15), d(60.15), d(158.7125), d(160.15))):
        assert abs((got - want).total_seconds()) < 1e-3, (got, want)


def test_p6_combustion_boundaries_are_exact_to_a_millisecond_and_complete_over_a_station_flipped_regime():
    """Mercury direct (113° + 1°/d) until a station at day 10, then retrograde (123° − 0.5°/d (d−10)); Sun 100° + 1°/d. Arc 13° until the
    station: combust under the direct orb 14°. After it the arc is 28 − 1.5·d: the retrograde orb is 12°, so the lord stops being combust AT
    the station (regime flip) and re-enters at day 10.6667, leaving at 26.6667. Closed forms; a dense scan finds no unlisted change.
    Planted reversion: no microsecond refinement of the device's 1-second bracket (each listed instant is then off by up to a second)."""
    def mercury(days):
        return 113.0 + days if days <= 10 else 123.0 - 0.5 * (days - 10)
    ops = P.P1Operands(l0(), sky(Mercury=mercury, Sun=line(100.0, 1.0)), rules=RULES)
    src = ops.sources_for("Mercury", complete=True, stations=[d(10)])[P.FACTOR_COMBUSTION]
    bounds, missed, changes = scan(src, d(0), d(40))
    assert missed == [] and changes == 3
    for got, want in zip(bounds, (d(10), d(10 + 2.0 / 3.0), d(80.0 / 3.0))):
        assert abs((got - want).total_seconds()) < 1e-3, (got, want)
    assert len(bounds) == 3


def test_p6_a_direct_orb_crossing_is_located_to_a_millisecond_off_the_devices_grid():
    """Venus-style single crossing: Mercury 120.123° + 0.5°/d against the Sun at 100° + 1°/d: arc 20.123 − 0.5 d reaches the direct orb 14° at
    day 12.246 — off the 6-hour grid — and leaves it at day 68.246. Planted reversion: the 1-second bracket of `contact_reconstruct._core`
    unrefined (the error is then up to a second)."""
    ops = P.P1Operands(l0(), sky(Mercury=line(120.123, 0.5), Sun=line(100.0, 1.0)), rules=RULES)
    got = ops.sources_for("Mercury", complete=True, stations=[d(-30)])[P.FACTOR_COMBUSTION].boundaries(d(0), d(80))
    assert len(got) == 2
    for g, want in zip(got, (d(12.246), d(68.246))):
        assert abs((g - want).total_seconds()) < 1e-3, (g, want)


# ── P-7: the nodes ────────────────────────────────────────────────────────────────────────────────────────────────────

def test_p7_a_node_in_a_verse_reserved_sign_is_unqualified_and_the_variants_and_disputes_are_disclosed():
    """ANSWERS §B.5 (BPHS 47.34-39, bphs:PG573:C2-PG574:C1): the verse gives Rāhu Gemini (mūlatrikoṇa) and Aquarius (own); L0 holds neither, so a
    Rāhu record there is `node_dignity_unclassified` — and the moment L0 carries own signs for it the reservation is lifted. Virgo
    (variant own) is classified by friendship with a disclosure; a rung resting on one of the five disputed pairs (Ketu→Sun: L0 neutral, the
    translator's note enemy) carries `node_friendship_source_disputed`. Planted reversion: classify the reserved signs by friendship."""
    s = state_of("Rahu", "Aquarius", 10)
    assert (s.rung, s.unknown_reason) == (None, "node_dignity_unclassified")
    assert state_of("Rahu", "Gemini", 10).unknown_reason == "node_dignity_unclassified"
    assert state_of("Ketu", "Sagittarius", 10).unknown_reason == "node_dignity_unclassified"
    assert state_of("Rahu", "Taurus", 10).rung == "EX" and state_of("Ketu", "Scorpio", 10).rung == "EX"       # L0 exaltation, ahead of the verse's own sign
    assert state_of("Ketu", "Taurus", 10).rung == "DEB"
    virgo = state_of("Rahu", "Virgo", 10)
    assert (virgo.rung, virgo.friendship) == ("FR", "friend")
    assert set(virgo.disclosures) == {"node_own_sign_variant_unresolved", "node_friendship_source_disputed"}      # Rāhu→Mercury is a disputed pair
    leo = state_of("Ketu", "Leo", 10)
    assert (leo.rung, leo.disclosures) == ("NEU", ("node_friendship_source_disputed",))
    assert state_of("Rahu", "Cancer", 10).disclosures == ()                       # Rāhu→Moon is not disputed
    lifted = copy.deepcopy(DIG)
    for r in lifted:
        if r["graha"] == "Rahu":
            r["own_signs"] = ["Aquarius"]
    assert state_of("Rahu", "Aquarius", 10, l0_=l0(dig=lifted)).rung == "OWN"


def test_p7_the_window_of_a_reserved_node_record_carries_the_named_reason_not_the_generic_one():
    """A P1 record is a lord's residence in ONE sign, so a Rāhu record in Aquarius is undeterminable over its whole support: its window is
    unqualified with the factor's own reason (the ruling's `node_dignity_unclassified`). Planted reversion: the generic
    `operand_undeterminable_over_support` — the seal brief would then count a named gap as an anonymous one."""
    ops = P.P1Operands(l0(), sky(Rahu=line(310.0), Sun=line(100.0)), rules=RULES)
    rec = ops.attach(_rec("r", path="P1", agent="rahu", kind="house_span", supports=((0, 30),)), complete=True)
    (w,), _ = ws.draft_windows("marriage", [rec], lambda p, v: P1_ROWS, allow_dynamic=True)
    assert w.score is None and w.peak_instant is None
    assert w.unresolved == {"node_dignity_unclassified": 1}


# ── P-8: the anchor ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_p8_a_delivery_form_is_judged_by_the_anchors_sky_not_the_agents():
    """AM-21 part 2: the Sun transiting Aries (exalted) is the AGENT of a record anchored at Mars's period; the factor judges the PERIOD LORD —
    Mars, here in Cancer, its debility sign. Planted reversion: the sources are built from `rec.agent`."""
    ops = P.P1Operands(l0(), sky(Sun=line(10.0, 0.01), Mars=line(100.0, 0.01), Jupiter=line(40.0, 0.01)), rules=RULES)
    base = _rec("r", path="P1", agent="sun", kind="house_span", supports=((0, 5),))
    delivery = ops.attach(dataclasses.replace(base, period_anchor_lord="mars"), complete=True)
    own = ops.attach(base, complete=True)
    at = d(1)
    assert delivery.operand_sources[P.FACTOR_DIGNITY].value_at(at) == RUNG_VALUE["DEB"]          # Mars in Cancer
    assert own.operand_sources[P.FACTOR_DIGNITY].value_at(at) == RUNG_VALUE["EX"]                # the Sun's own transit: Aries
    assert ops.attach(dataclasses.replace(base, path_id="P3"), complete=True).operand_sources == {}      # P1 only


# ── P-9: completeness needs the stored stations ───────────────────────────────────────────────────────────────────────

def test_p9_a_mercury_or_venus_source_is_complete_only_with_the_stored_stations():
    """The orb regime of those two flips at stations (N-8); without the stored list the retrograde state is unestablished — a named blank,
    never 'direct' — and the boundary list is not asserted complete. Planted reversion: `complete` ignores the stations."""
    ops = P.P1Operands(l0(), sky(Mercury=line(150.0, 0.5), Sun=line(100.0, 1.0), Jupiter=line(150.0, 0.1)), rules=RULES)
    no = ops.sources_for("Mercury", complete=True, stations=None)
    assert no[P.FACTOR_COMBUSTION].complete is False and no[P.FACTOR_DIGNITY].complete is False
    assert no[P.FACTOR_COMBUSTION].value_at(d(1)) is None
    assert no[P.FACTOR_COMBUSTION].unknown_reason(d(1)) == "retrograde_state_unestablished"
    assert no[P.FACTOR_DIGNITY].unknown_reason(d(1)) == "retrograde_state_unestablished"
    yes = ops.sources_for("Mercury", complete=True, stations=[d(-30)])
    assert yes[P.FACTOR_COMBUSTION].complete is True and yes[P.FACTOR_COMBUSTION].value_at(d(1)) is not None
    assert ops.sources_for("Mercury", complete=False, stations=[d(-30)])[P.FACTOR_DIGNITY].complete is False       # the store's own claim stands
    assert ops.sources_for("Jupiter", complete=True)[P.FACTOR_DIGNITY].complete is True                            # no regime to flip


def test_p9_without_a_value_rule_the_source_carries_no_value_and_the_sweep_keeps_its_named_blank():
    """D2 supplies the owner's tables; until then `value_mapping_undeclared` stays the honest answer (nothing here decides a number)."""
    ops = P.P1Operands(l0(), sky(Jupiter=line(150.0, 0.1), Sun=line(10.0, 1.0)))
    rec = ops.attach(_rec("r", path="P1", agent="jupiter", kind="house_span", supports=((0, 5),)), complete=True)
    row = {"factor_id": P.FACTOR_DIGNITY, "rule_version": "9.0.0", "null_state": "unqualified", "function": "categorical_ordered"}
    out = ws.categorical_factor(row, rec)
    assert (out.kind, out.reason) == ("missing", "value_mapping_undeclared")


def test_p9_a_value_rule_refuses_a_value_outside_the_declared_unit_range_and_never_defaults_an_unmapped_state():
    with pytest.raises(ValueError):
        P.category_rule({"EX": 1.5})
    with pytest.raises(ValueError):
        P.category_rule({"EX": True})
    assert P.category_rule({"EX": 1.0})(state_of("Jupiter", "Aries", 10)) is None            # FR is not in the table: None, not a default


def test_p9_a_state_the_value_table_does_not_name_is_a_named_blank_not_a_default():
    ops = P.P1Operands(l0(), sky(Jupiter=line(10.0, 0.01), Sun=line(200.0)), rules={P.FACTOR_DIGNITY: P.category_rule({"EX": 1.0})})
    src = ops.sources_for("Jupiter", complete=True)[P.FACTOR_DIGNITY]            # Jupiter in Aries: friendship FR, not in the table
    assert src.value_at(d(1)) is None and src.unknown_reason(d(1)) == "dignity_of_transit_sign_category_unmapped"


# ── P-13: the pañcadhā maitrī source ──────────────────────────────────────────────────────────────────────────────────

def test_p13_maitri_is_cut_at_the_sign_lords_ingress_and_reads_naisargika_plus_tatkalika():
    """Mars stands in Gemini (lord Mercury) throughout; Mercury, 40° + 1°/d, enters Gemini at day 20 and Cancer at day 50. Mars→Mercury is
    an enemy in L0; Mercury in Taurus is the 12th from Mars (a temporary friend: offsets 2,3,4,10,11,12) ⇒ enemy + friend = neutral, in
    Gemini the 1st (a temporary enemy) ⇒ enemy + enemy = extreme enemy (adhiśatru), in Cancer the 2nd ⇒ neutral again (BPHS 3.55-58, Jātaka
    Pārijāta II.45). Mars never moves, so only the sign lord's ingress changes the category. Planted reversion: the sign lord's ingress is
    not a boundary — the scan finds both changes unlisted."""
    table = {"neutral": 0.4, "extreme_enemy": 0.1, "enemy": 0.2, "friend": 0.6, "extreme_friend": 0.8, "own_sign": 0.9}
    rule = {P.FACTOR_MAITRI: P.category_rule(table, key=lambda s: s.maitri)}
    ops = P.P1Operands(l0(), sky(Mars=line(70.0), Mercury=line(40.0, 1.0), Sun=line(250.0)), rules=rule)
    src = ops.sources_for("Mars", complete=True)[P.FACTOR_MAITRI]
    assert [src.value_at(d(x)) for x in (10, 30, 60)] == [0.4, 0.1, 0.4]
    bounds, missed, changes = scan(src, d(0), d(70))
    assert missed == [] and changes == 2
    for got, want in zip(bounds, (d(20), d(50))):
        assert abs((got - want).total_seconds()) < 1e-3, (got, want)
    own = P.P1Operands(l0(), sky(Mars=line(10.0), Mercury=line(40.0), Sun=line(250.0)), rules=rule)
    assert own.sources_for("Mars", complete=True)[P.FACTOR_MAITRI].value_at(d(1)) == 0.9            # in its own sign: no maitrī, declared
    node = P.P1Operands(l0(), sky(Rahu=line(10.0), Sun=line(250.0)), rules=rule).sources_for("Rahu", complete=True)[P.FACTOR_MAITRI]
    assert node.value_at(d(1)) is None and node.unknown_reason(d(1)) == "node_maitri_unqualified"


# ── the sources inside the sweep ──────────────────────────────────────────────────────────────────────────────────────

P1_ROWS = [{"factor_id": P.FACTOR_DIGNITY, "rule_version": "9.0.0", "null_state": "unqualified", "function": "categorical_ordered"},
           {"factor_id": P.FACTOR_COMBUSTION, "rule_version": "9.0.0", "null_state": "unqualified", "function": "step"}]


def test_the_sources_cut_the_sweeps_pieces_at_their_boundaries_and_an_incomplete_list_blanks_the_record():
    ops = P.P1Operands(l0(), sky(Jupiter=line(237.97, 0.2), Sun=line(100.0, 1.0)), rules=RULES)
    rec = ops.attach(_rec("r", path="P1", agent="jupiter", kind="house_span", supports=((0, 100),)), complete=True)
    prog = ws.build_program(rec, P1_ROWS)
    assert prog.qualified and all(o.kind == "fn" for o in prog.outcomes)
    cuts = [a for a, _, _ in ws._pieces(d(0), d(100), [prog])]
    assert any(abs((c - d(10.15)).total_seconds()) < 1e-3 for c in cuts) and any(abs((c - d(60.15)).total_seconds()) < 1e-3 for c in cuts)
    assert prog.value_at(d(30)) == pytest.approx(RUNG_VALUE["MT"] * 0.5)              # the product of the two factors (MT, not combust)
    incomplete = ops.attach(_rec("r", path="P1", agent="jupiter", kind="house_span", supports=((0, 100),)), complete=False)
    blank = ws.build_program(incomplete, P1_ROWS)
    assert not blank.qualified and ("state_boundaries", ws.STATE_BOUNDARIES_REASON) in blank.reasons


# ── P-10: the L0 loaders and digests ──────────────────────────────────────────────────────────────────────────────────

def test_p10_the_digest_covers_every_consumed_cell_and_no_surrogate_and_ignores_row_order():
    base = l0()
    assert l0(dig=list(reversed(DIG))).digests() == base.digests()                       # order is not content
    noisy = [dict(r, id=900 + i, classical_citation="x", notes="y") for i, r in enumerate(NAIS)]
    assert P.naisargika_from_rows(noisy).content_digest == base.naisargika.content_digest       # surrogate ids, citations, notes: not consumed
    from decimal import Decimal
    as_decimal = [dict(r, orb_degrees=Decimal(str(float(r["orb_degrees"]))) , deep_orb_degrees=Decimal(r["deep_orb_degrees"]).quantize(Decimal("0.00")))
                  for r in COMB]
    assert P.combustion_orbs_from_rows(as_decimal).content_digest == base.combustion.content_digest      # 15, 15.0, Decimal('12.00'): one value
    changed = {
        "naisargika relation": (l0(nais=[dict(r, relation="friend" if (r["graha"], r["other_graha"]) == ("Jupiter", "Mercury") else r["relation"])
                                         for r in NAIS]), "bg_graha_naisargika_friendship"),
        "combustion orb": (l0(comb=[dict(r, orb_degrees=r["orb_degrees"] + 1) if r["graha"] == "Mars" else r for r in COMB]), "bg_combustion_orbs"),
        "combustion deep orb": (l0(comb=[dict(r, deep_orb_degrees=r["deep_orb_degrees"] - 1) if r["graha"] == "Mars" else r for r in COMB]),
                                "bg_combustion_orbs"),
        "dignity own sign": (l0(dig=[dict(r, own_signs=r["own_signs"] + ["Pisces"]) if r["graha"] == "Rahu" else r for r in DIG]),
                             "bg_dignity_reference"),
        "dignity exaltation": (l0(dig=[dict(r, exaltation_sign="Gemini") if r["graha"] == "Rahu" else r for r in DIG]), "bg_dignity_reference"),
    }
    for what, (other, asset) in changed.items():
        assert other.digests()[asset] != base.digests()[asset], what
        assert {a: x for a, x in other.digests().items() if a != asset} == {a: x for a, x in base.digests().items() if a != asset}, what


def test_p10_the_loaders_refuse_an_incomplete_duplicated_or_divergent_table_by_name():
    def refused(build, reason):
        with pytest.raises(p1.StrictInputError) as e:
            build()
        assert e.value.reason == reason, e.value.reason
    refused(lambda: P.naisargika_from_rows([r for r in NAIS if (r["graha"], r["other_graha"]) != ("Sun", "Moon")]), "naisargika_table_incomplete")
    refused(lambda: P.naisargika_from_rows(NAIS + [NAIS[0]]), "naisargika_row_duplicate")
    refused(lambda: P.combustion_orbs_from_rows([r for r in COMB if r["graha"] != "Jupiter"]), "combustion_orbs_incomplete")
    refused(lambda: P.dignity_reference_from_rows([r for r in DIG if r["graha"] != "Saturn"]), "dignity_row_missing_or_duplicate")
    moved = [dict(r, moolatrikona_from=5) if r["graha"] == "Moon" else r for r in DIG]          # L0 Moon 5°-30° against L1's 4°-30°
    refused(lambda: P.dignity_reference_from_rows(moved), "dignity_boundary_authority_divergence")
    refused(lambda: P.dignity_reference_from_rows(DIG + [dict(DIG[0], graha="Pluto")]), "dignity_row_graha_unknown")


class _Cursor:
    """A DB-API cursor over the fixture tables: `execute` picks the table the SQL names; `fetchall` returns the SELECTed columns in order."""

    def __init__(self, tables):
        self.tables, self.sql, self._asset = tables, [], None

    def execute(self, sql, params=None):
        self.sql.append(sql)
        self._asset = next(a for a in self.tables if a in sql)

    def fetchall(self):
        cols = P._COLUMNS[self._asset]
        return [tuple(r[c] for c in cols) for r in self.tables[self._asset]]


def test_p10_the_loaders_read_the_three_tables_through_a_cursor_in_a_total_order():
    cur = _Cursor({"bg_dignity_reference": DIG, "bg_combustion_orbs": COMB, "bg_graha_naisargika_friendship": NAIS})
    loaded = P.load_p1_l0(cur)
    assert loaded.digests() == l0().digests()
    assert all("ORDER BY" in s and "public.bg_" in s for s in cur.sql) and len(cur.sql) == 3


# ── P-11: the input vector ────────────────────────────────────────────────────────────────────────────────────────────

class _Conn:
    """A DB-API stand-in for `l0_identities`: a savepoint context and a cursor over the fixture tables."""

    def __init__(self, tables):
        self.tables = tables

    @contextlib.contextmanager
    def transaction(self):
        yield

    def cursor(self):
        return _Cursor(self.tables)


P1_ASSETS = ("bg_dignity_reference", "bg_combustion_orbs", "bg_graha_naisargika_friendship")


def test_p11_the_p1_tables_are_bound_into_the_vector_through_the_loaders_digests():
    conn = _Conn({"bg_dignity_reference": DIG, "bg_combustion_orbs": COMB, "bg_graha_naisargika_friendship": NAIS})
    assert all(iv.L0_CONSUMED[a][0] == "P1" for a in P1_ASSETS)
    assert iv.l0_identities(conn, P1_ASSETS) == l0().digests()
    assert iv.l0_identities(conn, ()) == {}                                                   # an unconsumed authority is not an input
    broken = _Conn({"bg_dignity_reference": DIG, "bg_combustion_orbs": COMB,
                    "bg_graha_naisargika_friendship": [r for r in NAIS if r["graha"] != "Venus"]})
    with pytest.raises(iv.InputDrift, match="P1 loader"):
        iv.l0_identities(broken, P1_ASSETS)


def test_p11_the_p1_modules_sit_in_the_implementation_digest_and_the_writers_consumption_follows_the_binding(monkeypatch):
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    listed = {m for mods in iv.IMPLEMENTATION_MODULES.values() for m in mods}
    assert {"services.gochara_kernel.p1_operands", "services.gochara_rules.p1_inputs"} <= listed
    assert writer.P1_VALUE_RULES is None and writer._l0_consumed() == ()
    monkeypatch.setattr(writer, "P1_VALUE_RULES", dict(RULES))
    assert set(writer._l0_consumed()) == set(P1_ASSETS)
    monkeypatch.setattr(writer, "VEDHA_SOURCE", lambda *a: None)
    assert set(writer._l0_consumed()) == set(P1_ASSETS) | {"bg_transit_rules"}


from .test_a53_input_vector import db, ephe  # noqa: E402,F401  (the disposable-database fixtures; skip NOT_RUN when the cluster is down)

#: the same preimage derived a second way — Postgres' own canonical JSON + sha256 over the real tables (no loader, no Python rule code)
_SQL_DIGESTS = {
    "bg_dignity_reference": "SELECT jsonb_build_array(graha, exaltation_sign, debilitation_sign, moolatrikona_sign, trim_scale(moolatrikona_from)::text,"
                            " trim_scale(moolatrikona_to)::text, to_jsonb(COALESCE(own_signs, ARRAY[]::text[]))) AS x, graha AS k1, '' AS k2"
                            " FROM public.bg_dignity_reference",
    "bg_combustion_orbs": "SELECT jsonb_build_array(graha, trim_scale(orb_degrees)::text, trim_scale(deep_orb_degrees)::text) AS x, graha AS k1, ''"
                          " AS k2 FROM public.bg_combustion_orbs",
    "bg_graha_naisargika_friendship": "SELECT jsonb_build_array(graha, other_graha, relation) AS x, graha AS k1, other_graha AS k2"
                                      " FROM public.bg_graha_naisargika_friendship",
}


def test_p11_the_real_migration_250_tables_load_and_bind_through_a_real_connection(db, ephe):
    """The loaders' SQL, the driver's NUMERIC / TEXT[] types and the digest preimage against the REAL L0 DDL and seed (migration 250), and the
    digest re-derived in Postgres. (Deferred to CI when the local cluster is down.)"""
    db.execute((Path(__file__).resolve().parents[4] / "migrations" / "250_bg_dignity_reference.sql").read_text())
    loaded = P.load_p1_l0(db.cursor())
    bound = iv.l0_identities(db, P1_ASSETS)
    assert bound == loaded.digests()
    for asset, sql in _SQL_DIGESTS.items():
        row = db.execute(f"SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(jsonb_agg(x ORDER BY k1, k2))) FROM ({sql}) t").fetchone()
        assert row[0] == bound[asset], asset
    db.execute("DELETE FROM public.bg_graha_naisargika_friendship WHERE graha = 'Sun' AND other_graha = 'Moon'")
    with pytest.raises(iv.InputDrift, match="P1 loader"):
        iv.l0_identities(db, P1_ASSETS)


# ── P-12: the store ───────────────────────────────────────────────────────────────────────────────────────────────────

class _Range:
    def __init__(self, lower, upper):
        self.lower, self.upper = lower, upper


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class _StoreConn:
    def __init__(self, rows, *, anchor_cols=2, stations=()):
        self.rows, self.anchor_cols, self.stations, self.calls = rows, anchor_cols, stations, []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "FROM pg_attribute" in sql:
            return _Result([(self.anchor_cols,)])
        if "completed_horizon" in sql:
            return _Result([(_Range(d(-1000), d(1000)),)])
        if "event_kind = 'station'" in sql:
            return _Result([(t,) for t in self.stations])
        if "ka_gochara_relationship_record r" in sql:
            return _Result(self.rows)
        raise AssertionError(sql)


def _row(rid, agent, anchor, lo=0, hi=50):
    return (rid, f"c-{rid}", "P1", "1.3.0", "residence", "house_span", agent, "scored", "admitted", "span:1", None,
            d(lo), d(hi), True, False, None, "conv-1", anchor)


def test_p12_the_store_builds_p1_sources_from_the_anchor_and_the_stored_stations():
    """Planted reversion: the sources are built from `rec.agent` — the delivery record anchored at Mars is then judged by the Sun's sky."""
    from services.gochara_kernel.window_store import WindowStore
    conn = _StoreConn([_row("a", "sun", "mars"), _row("b", "jupiter", "mercury")], stations=[d(-30)])
    ops = P.P1Operands(l0(), sky(Sun=line(10.0, 0.01), Mars=line(100.0, 0.01), Jupiter=line(40.0, 0.01), Mercury=line(150.0, 0.5)), rules=RULES)
    recs = {r.record_id: r for r in WindowStore(conn).read_grain(
        chart_id="x", generation="5.0", event_class="marriage", path_id="P1", rule_version="1.3.0", position_at=ops._position_at, p1=ops)}
    assert recs["a"].period_anchor_lord == "mars" and recs["b"].period_anchor_lord == "mercury"
    assert recs["a"].operand_sources[P.FACTOR_DIGNITY].value_at(d(1)) == RUNG_VALUE["DEB"]       # Mars in Cancer, not the Sun in Aries
    assert recs["a"].operand_sources[P.FACTOR_DIGNITY].complete is True                          # coverage completed every support
    assert recs["b"].operand_sources[P.FACTOR_COMBUSTION].complete is True                       # stations were fetched for Mercury …
    station_queries = [p for s, p in conn.calls if "event_kind = 'station'" in s]
    assert station_queries == [("mercury", "conv-1")]                                           # … once, and only for the lord that needs them


def test_p12_without_p1_the_records_are_exactly_what_they_were_and_a_missing_anchor_column_is_refused():
    from services.gochara_kernel.window_store import WindowStore
    plain = WindowStore(_StoreConn([_row("a", "sun", None)], anchor_cols=0)).read_grain(
        chart_id="x", generation="5.0", event_class="marriage", path_id="P1", rule_version="1.3.0", position_at=lambda b, t: 0.0)
    assert plain[0].operand_sources == {} and plain[0].period_anchor_lord is None
    ops = P.P1Operands(l0(), sky(Sun=line(10.0)))
    with pytest.raises(RuntimeError, match="period-anchor column"):
        WindowStore(_StoreConn([_row("a", "sun", None)], anchor_cols=0)).read_grain(
            chart_id="x", generation="5.0", event_class="marriage", path_id="P1", rule_version="1.3.0", position_at=ops._position_at, p1=ops)
