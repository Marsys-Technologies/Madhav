"""SR-OD1 P1B — P1 nature (Moon / Mercury / nodes), the per-instant side, and the (nature, rung) valence.

The oracle for every VALUE below is the owner's confirmed doctrine (OWNER-DOCTRINE-CONFIRMED-20261021, P1-MAPPING-DECISION,
Form B; ANSWERS.md v2.1 §B.2-B.5): the cell table `FORM_B` is the owner's table, written out here as the registry row's
`category_mapping` will carry it (the D2 binding) — the production code holds no cell value. The sky is an analytic stub
(linear motion) except in the last block, whose oracle is the published new/full-moon instants of 2000-01.

Distinct production claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  P-1  the Moon is benefic while waxing, malefic while waning (Sun-Moon elongation past 180 degrees; BPHS 3.11)
       (revert: `nature_at` hands the elongation operands to `agent_nature` swapped);
  P-2  the Moon's side flips at exactly the elongation-0/180 instants, and those instants are the change instants
       (revert: the pakṣa state function flips at 200 degrees);
  P-3  Mercury is malefic iff it shares a SIGN with the Sun, Mars, Saturn, Rāhu, Ketu or the WANING Moon (not the waxing one) —
       not within an orb (Q4 "joined" = x) (revert: join by a 10-degree orb);
  P-4  every instant at which Mercury's nature changes is a change instant, for each of the six companions
       (revert: the boundary search forgets Saturn);
  P-5  the nodes carry the malefic column (BPHS 3.11) (revert: a node is a benefic);
  P-6  the effective rung: combustion overrides every rung (revert: the combustion check moves last);
  P-7  exaltation is tested before mūlatrikoṇa inside one sign (revert: mūlatrikoṇa first, L1's natal order);
  P-8  debility is tested before the sign-lord's friendship (revert: the debility test is unreachable);
  P-9  friendship is the period lord's OWN table toward the sign lord, never the reverse (revert: the columns swapped);
  P-10 the side and value are the declared cell for (nature, rung), and rung boundaries follow `[from, to)`
       (revert: a malefic reads the benefic column);
  P-11 a side becomes a channel by the CLASS's polarity (revert: favourable is always the evidence-for channel);
  P-12 a mapping is exactly the closed 2 x 8 cells, every value in (0, 1] (spec §2.3 inv 3) (revert: a 0 value is accepted);
  P-13 a node in a sign the served verse reserves for its mūlatrikoṇa / own (not in L0) has NO rung, with a named reason
       (revert: those signs are classified by friendship);
  P-14 the disputed node friendships and the variant own signs are disclosed on the result (revert: no disclosure);
  P-15 an undeterminable combustion state is never "not combust", and a combustible lord with no combustion operand is refused
       (revert: `None` becomes `False`);
  P-16 the per-instant side reaches the WINDOW: the flip instant is the peak, with the Form B value in the flipped channel
       (revert: the side is read once, at the support start);
  P-17 a node's unclassified sign blanks its window with THAT reason (revert as P-13, observed through the sweep);
  P-18 the memoised, chunked boundary search equals the direct search (revert: the first chunk of a range is skipped);
  P-19 on the real ephemeris the Moon's change instants are the published new/full moons of January 2000 and Mercury's list
       contains every change a fine scan sees (revert as P-2, observed on the Swiss ephemeris);
  P-21 once P1 records are placed per instant, the window's evidence-AGAINST is a number (the valence three-field is then
       defined), and the independent verifier agrees on the same world (revert: the verifier keeps P1's against channel NULL);
  P-20 the owner's rung precedence differs from L1's natal classifier in exactly two placements and nowhere else (revert:
       the test's expected set is not met when any precedence step is changed).
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import contact_reconstruct as cr
from services.gochara_kernel import p1_nature_operands as ops
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import p1_valence as pv
from services.gochara_rules import registry as reg
from services.gochara_rules.p1_inputs import StrictInputError

from .conftest import EPHE_PATH, requires_swieph
from .test_a53_window_sweep import _d, _draft, _rec
from .test_od1_w0_interface import _Conn, _stored

FIX = pathlib.Path(__file__).parent.parent / "gochara_rules" / "fixtures"
DIG = json.loads((FIX / "l0_dignity_reference_2026_10_02.json").read_text())
NAIS = json.loads((FIX / "l0_naisargika_2026_10_02.json").read_text())
L1 = pytest.importorskip("ga_writers.ga_condition_writer")
FOR, AGAINST = ws.CHANNEL_FOR, ws.CHANNEL_AGAINST


def _cell(side, value):
    return {"side": side, "value": value}


F, A = "favourable", "adverse"
#: The owner's Form B table (ANSWERS §B.3), as the registry row's `category_mapping` will declare it
FORM_B = {
    "benefic": {"EX": _cell(F, 1.0), "MT": _cell(F, 0.75), "OWN": _cell(F, 0.5), "FR": _cell(F, 0.25),
                "NEU": _cell(F, 0.125), "INI": _cell(A, 0.75), "DEB": _cell(A, 1.0), "COMB": _cell(A, 1.0)},
    "malefic": {"EX": _cell(F, 1.0), "MT": _cell(F, 0.75), "OWN": _cell(F, 0.5), "FR": _cell(A, 0.5),
                "NEU": _cell(A, 0.625), "INI": _cell(A, 0.75), "DEB": _cell(A, 1.0), "COMB": _cell(A, 1.0)},
}
MAPPING = pv.validate_mapping(FORM_B, ref="test:form_b")


@pytest.fixture(autouse=True)
def _restore_factor_registry():
    saved = dict(reg.FACTORS)
    yield
    reg.FACTORS.clear()
    reg.FACTORS.update(saved)


# ── the analytic sky ─────────────────────────────────────────────────────────────────────────────────────────────────

def world(**bodies):
    """position_at over linear motion: body -> (longitude at day 0, degrees per day). Bodies not named sit at 200 deg (Libra)
    — far from anything a test moves, and a different sign from every companion position used here. The Moon alone sits 90° behind
    (a waning 270° elongation, in Cancer): a Moon exactly on the Sun is exactly ON the pakṣa edge, a degenerate world in which the
    search's speed bound can prune nothing (SR-OD1 R2: its 1 s floor then bisects every cell to the floor)."""
    def position_at(body, t):
        lon0, rate = bodies.get(body, (110.0 if body == "Moon" else 200.0, 0.0))
        return (lon0 + rate * (t - _d(0)).total_seconds() / 86400.0) % 360.0
    return position_at


def rules(graha):
    return pv.LordRungRules(graha, DIG, NAIS)


def side_value(graha, nature, sign, degree, combust=False):
    r = rules(graha).rung(sign, degree, combust)
    assert r.rung is not None, (graha, sign, degree, r)
    side, value = MAPPING.side_and_value(nature, r.rung)
    return r.rung, side, value


# ── P-1, P-2: the Moon ───────────────────────────────────────────────────────────────────────────────────────────────

def test_p1_the_moon_is_benefic_waxing_and_malefic_waning():
    """Elongation 170 (the Moon 170 ahead of the Sun) is waxing; 190 is waning (BPHS 3.11 "decreasing Moon" is a malefic).
    Planted reversion: the operands handed to `agent_nature` swapped."""
    for elong, expect in ((170.0, "benefic"), (190.0, "malefic"), (10.0, "benefic"), (350.0, "malefic")):
        n = ops.NatureOperands("Moon", world(Sun=(100.0, 0.0), Moon=((100.0 + elong) % 360.0, 0.0)))
        assert n.nature_at(_d(0)) == expect, elong


def test_p2_the_moons_side_flips_at_elongation_0_and_180_and_those_are_the_change_instants():
    """Elongation e(t) = 170 + 12 t. It reaches 180 at t = 10/12 d (waxing -> waning), 360 at t = 190/12 d (-> waxing), and 180
    again at 370/12 d. Planted reversion: the pakṣa state flips at 200 degrees instead of 180."""
    n = ops.NatureOperands("Moon", world(Sun=(100.0, 1.0), Moon=(270.0, 13.0)))
    got = n.boundaries(_d(0), _d(40))
    want = [_d(10 / 12), _d(190 / 12), _d(370 / 12)]
    assert len(got) == 3
    for g, w in zip(got, want):
        assert abs((g - w).total_seconds()) <= 1.0, (g, w)
    for g, before, after in zip(got, ("benefic", "malefic", "benefic"), ("malefic", "benefic", "malefic")):
        assert n.nature_at(g - timedelta(seconds=2)) == before and n.nature_at(g + timedelta(seconds=1)) == after


# ── P-3, P-4: Mercury ────────────────────────────────────────────────────────────────────────────────────────────────

MALEFIC_COMPANIONS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")


@pytest.mark.parametrize("body", MALEFIC_COMPANIONS)
def test_p3_mercury_is_malefic_with_each_malefic_in_its_sign(body):
    n = ops.NatureOperands("Mercury", world(Mercury=(45.0, 0.0), **{body: (50.0, 0.0)}))
    assert n.nature_at(_d(0)) == "malefic"


@pytest.mark.parametrize("body", ("Venus", "Jupiter"))
def test_p3_mercury_stays_benefic_with_a_benefic_in_its_sign(body):
    assert ops.NatureOperands("Mercury", world(Mercury=(45.0, 0.0), **{body: (50.0, 0.0)})).nature_at(_d(0)) == "benefic"


def test_p3_the_moon_makes_mercury_malefic_only_while_waning():
    sun = (100.0, 0.0)
    waning = world(Mercury=(45.0, 0.0), Sun=sun, Moon=(50.0, 0.0))        # Moon - Sun = 310: waning
    waxing = world(Mercury=(45.0, 0.0), Sun=(340.0, 0.0), Moon=(50.0, 0.0))   # 70: waxing
    assert ops.NatureOperands("Mercury", waning).nature_at(_d(0)) == "malefic"
    assert ops.NatureOperands("Mercury", waxing).nature_at(_d(0)) == "benefic"


def test_p3_joined_is_the_same_sign_not_an_orb():
    """Mercury 29.5 Aries and Mars 0.5 Taurus are 1 degree apart in DIFFERENT signs: not joined (Q4 x, BPHS yuti is
    sign-conjunction). Mercury 0.5 and Mars 29.5 in the same sign are 29 degrees apart: joined.
    Planted reversion: join by a 10-degree orb."""
    apart = world(Mercury=(29.5, 0.0), Mars=(30.5, 0.0))
    same = world(Mercury=(0.5, 0.0), Mars=(29.5, 0.0))
    assert ops.NatureOperands("Mercury", apart).nature_at(_d(0)) == "benefic"
    assert ops.NatureOperands("Mercury", same).nature_at(_d(0)) == "malefic"


def _scan_flips(n, lo, hi, step=timedelta(minutes=15)):
    """Brute force: (previous, current) sample pairs between which the nature differs."""
    out, prev, t = [], n.nature_at(lo), lo
    while t < hi:
        t += step
        cur = n.nature_at(t)
        if cur != prev:
            out.append((t - step, t))
        prev = cur
    return out


MERCURY_WORLDS = {
    # Mercury sits at 45 (Taurus); ONE companion walks into Taurus at 10 d (15 degrees at 1.5/d for the quick Sun-free cases)
    "Sun": dict(Sun=(25.0, 0.5)),
    "Mars": dict(Mars=(25.0, 0.5)),
    "Saturn": dict(Saturn=(25.0, 0.5)),
    "Rahu": dict(Rahu=(25.0, 0.5)),
    "Ketu": dict(Ketu=(25.0, 0.5)),
    # the Moon (waning: Moon - Sun = 280) crosses into Taurus at 0.77 d and out at 3.08 d
    "Moon": dict(Sun=(100.0, 0.0), Moon=(20.0, 13.0)),
}


@pytest.mark.parametrize("who", sorted(MERCURY_WORLDS))
def test_p4_every_change_of_mercurys_nature_is_a_change_instant(who):
    """For each companion alone, a brute-force 15-minute scan finds the changes of Mercury's nature; the boundary list must name
    exactly those changes (one boundary inside each flip's sample pair, located to a second). Planted reversion: the boundary
    search's companion list forgets Saturn (the Saturn case is the one that fails)."""
    n = ops.NatureOperands("Mercury", world(Mercury=(45.0, 0.0), **MERCURY_WORLDS[who]))
    lo, hi = _d(0), _d(40)
    flips = _scan_flips(n, lo, hi)
    cuts = n.boundaries(lo, hi)
    assert flips, "the world must move Mercury's nature"
    assert len(cuts) == len(flips), (who, cuts, flips)
    for c, (a, b) in zip(cuts, flips):
        assert a < c <= b, (who, c, a, b)
        assert n.nature_at(c - timedelta(seconds=2)) != n.nature_at(c + timedelta(seconds=1))


# ── P-5: the nodes ───────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("node", ("Rahu", "Ketu"))
def test_p5_a_node_reads_the_malefic_column(node):
    """The node in Libra (lord Venus, a friend of both nodes in L0): rung FR; the MALEFIC FR cell is adverse 0.5 (the benefic
    one would be favourable 0.25). Planted reversion: a node is a benefic."""
    lv = _lord(node, "bereavement", **{node: (200.0 + 5.0, 0.0)})
    s = lv.state_at(_d(0))
    assert (s.nature, s.rung, s.side, s.value) == ("malefic", "FR", A, 0.5)


def _lord(graha, event_class, *, combust=None, rung_boundaries=lambda lo, hi: [], mapping=MAPPING, **bodies):
    pos = world(**bodies)
    return ops.P1LordValence(graha=graha, event_class=event_class, mapping=mapping, rules=rules(graha),
                             nature=ops.NatureOperands(graha, pos), position_at=pos,
                             combust_at=combust if combust is not None else (lambda t: False),
                             rung_boundaries=rung_boundaries)


# ── P-6..P-10: the effective rung and the table (the owner's golden cases, ANSWERS §B.2) ─────────────────────────────

def test_p6_combustion_overrides_every_rung():
    """Any lord with the L1 state "combust" is COMB, adverse 1.00, whatever the sign — here Jupiter in its exaltation sign.
    Planted reversion: the combustion check moves to the end of the precedence."""
    assert side_value("Jupiter", "benefic", "Cancer", 5.0, combust=True) == ("COMB", A, 1.0)
    assert side_value("Saturn", "malefic", "Libra", 5.0, combust=True) == ("COMB", A, 1.0)
    assert side_value("Jupiter", "benefic", "Cancer", 5.0, combust=False) == ("EX", F, 1.0)


def test_p7_exaltation_is_tested_before_moolatrikona():
    """The Moon's Taurus (mūlatrikoṇa 4-30 in L0) and Mercury's Virgo (16-20) read as exaltation throughout.
    Planted reversion: mūlatrikoṇa first — L1's natal order."""
    assert side_value("Moon", "benefic", "Taurus", 10.0) == ("EX", F, 1.0)
    assert side_value("Mercury", "benefic", "Virgo", 18.0) == ("EX", F, 1.0)


def test_p8_debility_is_tested_before_the_sign_lords_friendship():
    """Jupiter in Capricorn: Saturn is NEUTRAL to Jupiter, but debility is reached first -> adverse 1.00 (not NEU 0.125). Likewise
    Sun in Libra (not INI), Venus in Virgo, Mercury in Pisces. Planted reversion: the debility test is unreachable."""
    assert side_value("Jupiter", "benefic", "Capricorn", 5.0) == ("DEB", A, 1.0)
    assert side_value("Sun", "malefic", "Libra", 5.0) == ("DEB", A, 1.0)
    assert side_value("Venus", "benefic", "Virgo", 5.0) == ("DEB", A, 1.0)
    assert side_value("Mercury", "benefic", "Pisces", 5.0) == ("DEB", A, 1.0)


def test_p9_friendship_is_the_period_lords_own_table_toward_the_sign_lord():
    """Jupiter in Gemini: Jupiter -> Mercury is ENEMY (Mercury -> Jupiter would read neutral) -> INI adverse 0.75, not NEU
    0.125. Mars in Virgo likewise. Moon in Capricorn: Moon -> Saturn is NEUTRAL (Saturn -> Moon is enemy) -> NEU: favourable
    0.125 waxing, adverse 0.625 waning. Planted reversion: the lookup columns swapped."""
    assert side_value("Jupiter", "benefic", "Gemini", 5.0) == ("INI", A, 0.75)
    assert side_value("Mars", "malefic", "Virgo", 5.0) == ("INI", A, 0.75)
    assert side_value("Moon", "benefic", "Capricorn", 5.0) == ("NEU", F, 0.125)
    assert side_value("Moon", "malefic", "Capricorn", 5.0) == ("NEU", A, 0.625)


def test_p10_every_rung_reads_its_declared_cell_and_the_degree_edges_are_half_open():
    """One golden case per remaining rung (ANSWERS §B.2): EX, MT, OWN, FR, NEU, INI on both natures; the mūlatrikoṇa range is
    [from, to): Sun in Leo 19.999 is MT, 20.0 is OWN. Planted reversion: a malefic reads the benefic column."""
    cases = [
        ("Jupiter", "benefic", "Cancer", 5, ("EX", F, 1.0)), ("Saturn", "malefic", "Libra", 5, ("EX", F, 1.0)),
        ("Sun", "malefic", "Leo", 10, ("MT", F, 0.75)), ("Jupiter", "benefic", "Sagittarius", 5, ("MT", F, 0.75)),
        ("Sun", "malefic", "Leo", 25, ("OWN", F, 0.5)), ("Venus", "benefic", "Taurus", 5, ("OWN", F, 0.5)),
        ("Jupiter", "benefic", "Aries", 5, ("FR", F, 0.25)), ("Saturn", "malefic", "Taurus", 5, ("FR", A, 0.5)),
        ("Jupiter", "benefic", "Aquarius", 5, ("NEU", F, 0.125)), ("Mars", "malefic", "Taurus", 5, ("NEU", A, 0.625)),
        ("Sun", "malefic", "Leo", 19.999, ("MT", F, 0.75)), ("Sun", "malefic", "Leo", 20.0, ("OWN", F, 0.5)),
    ]
    for graha, nature, sign, deg, want in cases:
        assert side_value(graha, nature, sign, deg) == want, (graha, sign, deg)


# ── P-11: the channel is the class's ─────────────────────────────────────────────────────────────────────────────────

def test_p11_a_side_becomes_a_channel_by_the_classs_polarity():
    """Jupiter exalted is favourable: evidence FOR a gain class (marriage), AGAINST an adverse one (bereavement). Jupiter
    debilitated is adverse: the reverse. Planted reversion: favourable is always the for-channel."""
    ex = dict(Jupiter=(100.0 + 5.0, 0.0))        # Cancer
    deb = dict(Jupiter=(270.0 + 5.0, 0.0))       # Capricorn
    assert _lord("Jupiter", "marriage", **ex).channel_at(_d(0)) == FOR
    assert _lord("Jupiter", "bereavement", **ex).channel_at(_d(0)) == AGAINST
    assert _lord("Jupiter", "marriage", **deb).channel_at(_d(0)) == AGAINST
    assert _lord("Jupiter", "bereavement", **deb).channel_at(_d(0)) == FOR


# ── P-12: the mapping's shape ────────────────────────────────────────────────────────────────────────────────────────

def test_p12_a_mapping_is_exactly_the_closed_cells_with_values_in_zero_one_exclusive_of_zero():
    import copy
    bad = copy.deepcopy(FORM_B)
    bad["malefic"]["NEU"]["value"] = 0.0                       # a modifier never removes a window
    with pytest.raises(StrictInputError) as e:
        pv.validate_mapping(bad)
    assert e.value.reason == "mapping_value_invalid"
    over = copy.deepcopy(FORM_B)
    over["benefic"]["EX"]["value"] = 1.01
    with pytest.raises(StrictInputError):
        pv.validate_mapping(over)
    short = copy.deepcopy(FORM_B)
    del short["benefic"]["COMB"]
    with pytest.raises(StrictInputError) as e:
        pv.validate_mapping(short)
    assert e.value.reason == "mapping_rungs_invalid"
    sided = copy.deepcopy(FORM_B)
    sided["benefic"]["EX"]["side"] = "good"
    with pytest.raises(StrictInputError) as e:
        pv.validate_mapping(sided)
    assert e.value.reason == "mapping_side_invalid"
    with pytest.raises(StrictInputError) as e:
        pv.mapping_from_row({"factor_id": "dignity_of_transit_sign", "rule_version": "1.3.0"})
    assert e.value.reason == "category_mapping_undeclared"
    ok = pv.mapping_from_row({"factor_id": "dignity_of_transit_sign", "rule_version": "1.3.0", "category_mapping": FORM_B})
    assert ok.cells == MAPPING.cells and ok.ref == "dignity_of_transit_sign@1.3.0"


# ── P-13, P-14: the nodes' rungs ─────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("node,sign", [("Rahu", "Gemini"), ("Rahu", "Aquarius"), ("Ketu", "Sagittarius")])
def test_p13_a_node_in_a_sign_the_verse_reserves_and_l0_lacks_has_no_rung(node, sign):
    """BPHS 47.34-39 (bphs:PG573:C2-PG574:C1): Rāhu's mūlatrikoṇa Gemini and own Aquarius, Ketu's mūlatrikoṇa Sagittarius — not in
    L0. No rung, the named reason, never a friendship guess. Planted reversion: those signs fall through to friendship."""
    r = rules(node).rung(sign, 10.0, False)
    assert r.rung is None and r.reason == pv.REASON_NODE_UNCLASSIFIED == "node_dignity_unclassified"


def test_p13_exaltation_and_debility_of_the_nodes_come_from_l0_and_win_over_the_reserved_set():
    assert rules("Rahu").rung("Taurus", 5.0, False).rung == "EX"
    assert rules("Rahu").rung("Scorpio", 5.0, False).rung == "DEB"
    assert rules("Ketu").rung("Scorpio", 5.0, False).rung == "EX"            # the verse's own sign, but exaltation wins
    assert rules("Ketu").rung("Taurus", 5.0, False).rung == "DEB"


def test_p13_an_own_sign_l0_later_carries_for_a_node_is_classified_by_l0():
    import copy
    rows = copy.deepcopy(DIG)
    next(r for r in rows if r["graha"] == "Rahu")["own_signs"] = ["Aquarius"]
    assert pv.LordRungRules("Rahu", rows, NAIS).rung("Aquarius", 5.0, False).rung == "OWN"
    assert pv.LordRungRules("Rahu", rows, NAIS).rung("Gemini", 5.0, False).rung is None      # mūlatrikoṇa still has no L0 carrier


def test_p14_the_disputed_node_friendships_and_the_variant_own_signs_are_disclosed():
    """L0 and the translator's note disagree on Rāhu->Mercury / Mars / Jupiter and Ketu->Sun / Moon: a node rung that rests on one
    carries `node_friendship_source_disputed`. Rāhu in Virgo / Ketu in Pisces (the variant own signs) carry
    `node_own_sign_variant_unresolved`. Planted reversion: the disclosures are dropped."""
    virgo = rules("Rahu").rung("Virgo", 5.0, False)                 # lord Mercury: a disputed pair AND the variant own sign
    assert virgo.rung == "FR" and set(virgo.disclosures) == {pv.DISCLOSE_FRIENDSHIP, pv.DISCLOSE_VARIANT_OWN}
    pisces = rules("Ketu").rung("Pisces", 5.0, False)               # lord Jupiter: Ketu->Jupiter is not a disputed pair
    assert pisces.rung == "NEU" and pisces.disclosures == (pv.DISCLOSE_VARIANT_OWN,)
    ketu_leo = rules("Ketu").rung("Leo", 5.0, False)                # lord Sun: Ketu->Sun is disputed
    assert ketu_leo.disclosures == (pv.DISCLOSE_FRIENDSHIP,)
    assert rules("Rahu").rung("Libra", 5.0, False).disclosures == ()          # Rāhu->Venus: undisputed
    assert rules("Jupiter").rung("Gemini", 5.0, False).disclosures == ()      # a classical lord never carries them


# ── P-15: combustion is never defaulted ──────────────────────────────────────────────────────────────────────────────

def test_p15_an_undeterminable_combustion_state_is_never_not_combust():
    """Planted reversion: `None` is coerced to `False` ⇒ the lord reads as an ordinary exalted Jupiter."""
    lv = _lord("Jupiter", "marriage", combust=lambda t: None, Jupiter=(105.0, 0.0))
    assert lv.state_at(_d(0)) == ops.REASON_COMBUSTION_UNAVAILABLE
    assert lv.channel_at(_d(0)) is None and lv.value_at(_d(0)) is None
    assert lv.unknown_reason(_d(0)) == "p1_combustion_state_undeterminable"
    pos = world(Jupiter=(105.0, 0.0))
    with pytest.raises(ValueError, match="combustion operand"):
        ops.P1LordValence(graha="Jupiter", event_class="marriage", mapping=MAPPING, rules=rules("Jupiter"),
                          nature=ops.NatureOperands("Jupiter", pos), position_at=pos)
    # the Sun and the nodes are a DECLARED non-applicability: no operand needed
    sun = world(Sun=(130.0, 0.0))
    ops.P1LordValence(graha="Sun", event_class="marriage", mapping=MAPPING, rules=rules("Sun"),
                      nature=ops.NatureOperands("Sun", sun), position_at=sun).state_at(_d(0))


# ── P-16, P-17: through the sweep ────────────────────────────────────────────────────────────────────────────────────

P1_FACTORS = ("agent_nature", "dignity_of_transit_sign", "combustion")


def _p1_rows(path, version):
    return [r for r in ws.registry_factor_rows("P1", "1.0.0") if r["factor_id"] in P1_FACTORS]


def _p1_record(lord_valence, agent, supports=((0, 10),)):
    return _rec("lord", path="P1", agent=agent, root="R-lord", supports=supports, state_boundaries=None,
                state_boundaries_complete=False,
                operand_sources={"agent_nature": lord_valence.agent_nature_source(),
                                 "dignity_of_transit_sign": lord_valence.dignity_value_source(),
                                 "combustion": ops.declared_neutral_source()})


def test_p16_the_flip_of_the_moons_side_is_the_peak_with_the_form_b_value_in_the_flipped_channel():
    """The Moon lord stays in Aries (neutral sign to the Moon: NEU) while its elongation goes 175 -> 185: benefic until day 5,
    malefic after. For the ADVERSE class bereavement a benefic's NEU is favourable 0.125 -> evidence AGAINST; the waning
    Moon's NEU is adverse 0.625 -> evidence FOR. So the for-channel objective is 0 until day 5 and 0.625 after: the window's peak
    is the flip instant, evidence_for 0.625, evidence_against 0. Planted reversion: the side is read once, at the support start
    (the objective is then 0 throughout and the window has no peak value)."""
    lv = _lord("Moon", "bereavement", Sun=(190.0, -0.5), Moon=(5.0, 0.5))
    (w,), _ = _draft([_p1_record(lv, "moon")], _p1_rows, cls="bereavement")
    assert w.unqualified_reason is None, w.unqualified_reason
    assert abs((w.peak_instant - _d(5)).total_seconds()) <= 1.0
    assert w.objective_value == pytest.approx(0.625)
    assert (w.evidence_for, w.evidence_against) == (pytest.approx(0.625), pytest.approx(0.0))


def test_p17_a_nodes_unclassified_sign_blanks_the_window_with_that_reason():
    """Rāhu 10 degrees into Gemini for the whole support (mūlatrikoṇa by the served verse, absent from L0): the window is blank
    and carries `node_dignity_unclassified`, not the generic reason. Planted reversion: as P-13."""
    lv = _lord("Rahu", "bereavement", Rahu=(70.0, 0.0))
    (w,), _ = _draft([_p1_record(lv, "rahu")], _p1_rows, cls="bereavement")
    assert w.peak_instant is None and w.score is None and w.evidence_for is None
    assert w.unqualified_reason == "node_dignity_unclassified"
    assert w.outcome_valence_for_native == "unqualified"


def test_p17_the_same_node_in_a_classified_sign_is_numbered():
    lv = _lord("Rahu", "bereavement", Rahu=(205.0, 0.0))            # Libra: Venus is Rāhu's friend -> malefic FR adverse 0.5
    (w,), _ = _draft([_p1_record(lv, "rahu")], _p1_rows, cls="bereavement")
    assert w.unqualified_reason is None and w.objective_value == pytest.approx(0.5)
    assert w.evidence_for == pytest.approx(0.5)


def test_p16_without_rung_boundaries_the_record_is_blank_not_numbered_on_a_guess():
    """The nature list is complete by construction, the rung list is the caller's: absent ⇒ no completeness claimed."""
    lv = _lord("Moon", "bereavement", rung_boundaries=None, Sun=(190.0, -0.5), Moon=(5.0, 0.5))
    (w,), _ = _draft([_p1_record(lv, "moon")], _p1_rows, cls="bereavement")
    assert w.peak_instant is None and w.unqualified_reason == ws.STATE_BOUNDARIES_REASON


def test_p21_evidence_against_is_numbered_for_p1_and_the_verifier_agrees(monkeypatch):
    """The P16 world, handed to the VERIFIER with only a channel derivation (the flip at day 5) and a constant record value:
    the builder's evidence_against 0.0 (a number, with the plain/adverse valence it implies) is reproduced. A P1 record the caller
    cannot place in a channel keeps the against channel NULL, and so does a registry row with a silent direction.
    Planted reversion: the verifier's `_against_evaluated` ignores the channel derivation ⇒ it expects NULL and refuses 0.0."""
    lv = _lord("Moon", "bereavement", Sun=(190.0, -0.5), Moon=(5.0, 0.5))
    rec = _p1_record(lv, "moon")
    (draft,), _ = _draft([rec], _p1_rows, cls="bereavement")
    assert draft.evidence_against == pytest.approx(0.0) and draft.outcome_valence_for_native == "adverse"
    monkeypatch.setattr(wv, "_row_state", lambda row, r, d, v: ("const", 0.625 if row["factor_id"] == "dignity_of_transit_sign" else 1.0))
    conn = _Conn([_stored(draft)], [(rec.record_id, rec.root_id, "residence", "sign_span", "moon", None, *rec.supports[0])],
                 [("w", rec.record_id)])
    grain = dict(chart_id="c", generation="g", event_class="bereavement", path_id="P1", rule_version="1.0.0")
    flip = _d(5)
    report = wv.verify_window_semantics(
        conn, factor_rows=_p1_rows("P1", "1.0.0"), policy=wv.POLICY_VERSION, **grain,
        channel_at=lambda r, t: AGAINST if t < flip else FOR, channel_boundaries=lambda r, lo, hi: [flip] if lo < flip < hi else [])
    assert report["numeric_reproduced"] == 1 and report["status"] == "VERIFIED"
    assert wv._against_evaluated("P1", _p1_rows("P1", "1.0.0")) is False
    assert wv._against_evaluated("P1", _p1_rows("P1", "1.0.0"), per_instant_channel=True) is True
    silent = _p1_rows("P1", "1.0.0") + [{"factor_id": "x", "direction": "unclear"}]
    assert wv._against_evaluated("P1", silent, per_instant_channel=True) is False
    assert ws.against_channel_state(silent) in ("ambiguous", "declared")      # the builder's own reading of the same rows


# ── P-18: the chunked search equals the direct one ───────────────────────────────────────────────────────────────────

def test_p18_the_memoised_chunked_boundaries_equal_the_direct_search_across_chunk_edges():
    """Ranges that start inside a chunk, straddle a chunk edge and span several are compared with the unchunked `_changes` over
    the same range (the two step lattices differ, so equality is to the 1 s the search locates to). Planted reversion: the first
    chunk of a range is skipped."""
    pos = world(Mercury=(20.0, 1.1), Sun=(10.0, 0.97), Mars=(40.0, 0.4), Moon=(100.0, 13.1), Saturn=(60.0, 0.05))
    pos.cache_key = ("stub", "p18")
    n = ops.NatureOperands("Mercury", pos)
    for lo_d, hi_d in ((50.0, 100.0), (100.0, 150.0), (3.0, 300.0)):    # chunk edges fall at days 47, 143, 239
        lo, hi = _d(lo_d), _d(hi_d)
        direct = [c for c in n._changes(lo, hi) if lo < c < hi]
        chunked = n.boundaries(lo, hi)
        assert len(direct) == len(chunked) and direct, (lo_d, hi_d)
        for a, b in zip(direct, chunked):
            assert abs((a - b).total_seconds()) <= 2.0
    again = n.boundaries(_d(50.0), _d(300.0))                           # a memo hit returns the same list
    assert again == n.boundaries(_d(50.0), _d(300.0))


# ── P-19: the real ephemeris ─────────────────────────────────────────────────────────────────────────────────────────

def _swiss_position_at():
    from services.gochara_kernel.knots import calc_sidereal_lon

    def position_at(body, t):
        jd = t.timestamp() / 86400.0 + 2440587.5
        lon, retflag = calc_sidereal_lon(body.title(), jd, EPHE_PATH)
        assert retflag & 2
        return lon
    position_at.cache_key = ("swiss", EPHE_PATH)
    return position_at


@requires_swieph
def test_p19_the_moons_change_instants_are_the_published_new_and_full_moons_of_january_2000():
    """USNO: new moon 2000-01-06 18:14 UTC, full moon 2000-01-21 04:40 UTC, new moon 2000-02-05 13:03 UTC, full moon
    2000-02-19 16:27 UTC (to the minute). The nature after a new moon is benefic, after a full moon malefic."""
    n = ops.NatureOperands("Moon", _swiss_position_at())
    cuts = n.boundaries(datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2000, 3, 1, tzinfo=timezone.utc))
    published = [datetime(2000, 1, 6, 18, 14), datetime(2000, 1, 21, 4, 40), datetime(2000, 2, 5, 13, 3),
                 datetime(2000, 2, 19, 16, 27)]
    assert len(cuts) == 4
    for c, p in zip(cuts, published):
        assert abs((c - p.replace(tzinfo=timezone.utc)).total_seconds()) <= 90.0, (c, p)
    assert [n.nature_at(c + timedelta(seconds=1)) for c in cuts] == ["benefic", "malefic", "benefic", "malefic"]


@requires_swieph
def test_p19_every_change_of_mercurys_nature_a_fine_scan_sees_is_a_change_instant():
    n = ops.NatureOperands("Mercury", _swiss_position_at())
    lo, hi = datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2000, 4, 1, tzinfo=timezone.utc)
    flips = _scan_flips(n, lo, hi, step=timedelta(minutes=30))
    cuts = n.boundaries(lo, hi)
    assert flips and len(cuts) == len(flips)
    for c, (a, b) in zip(cuts, flips):
        assert a < c <= b


# ── P-20: the owner's order versus L1's natal classifier ─────────────────────────────────────────────────────────────

def test_p20_the_precedence_differs_from_l1s_natal_classifier_in_exactly_two_placements():
    """L1's `dignity_d1_from_sign` tests mūlatrikoṇa before exaltation. Over every classical graha x sign x half-degree, the
    owner's rung and L1's label agree on every non-friendship placement except the Moon in Taurus from 4 degrees and Mercury
    in Virgo 16-20, where the owner reads exaltation (ANSWERS §B.2). The set is pinned: a change to any precedence step moves it."""
    l1_to_rung = {"exalted": "EX", "moolatrikona": "MT", "own": "OWN", "debilitated": "DEB"}
    differ = set()
    for graha in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        r = rules(graha)
        for sign in pv.SIGNS:
            for half in range(60):
                deg = half / 2.0
                label = L1.dignity_d1_from_sign(graha, sign, deg, r.ref)
                mine = r.rung(sign, deg, False).rung
                if label in l1_to_rung:
                    if l1_to_rung[label] != mine:
                        differ.add((graha, sign, mine, l1_to_rung[label]))
                else:                                                  # a friendship class in L1: mine must be one too
                    assert mine in ("FR", "NEU", "INI"), (graha, sign, deg, label, mine)
    assert differ == {("Moon", "Taurus", "EX", "MT"), ("Mercury", "Virgo", "EX", "MT")}
