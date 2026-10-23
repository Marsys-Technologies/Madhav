"""SR-B1-Q3C-JOB — the P1 SIDE follows Q3(c) / Form B, in the builder (P1b) AND in the independent verifier (P1c), under rule version 1.3.0 only.

Doctrine: OWNER-DOCTRINE-CONFIRMED-20261021 / P1-MAPPING-DECISION, ANSWERS.md v2.1 §B.4 (Q3 c): the natural nature sets the DEFAULT side; dignity and
combustion override it at the extremes the texts name and only there — a BENEFIC lord goes ADVERSE when combust, debilitated or in an inimical sign
(Phaladīpikā XX.37, Muhūrta Cintāmaṇi 47, Saravali 26-27, XX.30 tail); a MALEFIC lord goes FAVOURABLE when exalted, in mūlatrikoṇa or in its own sign
(Saravali 25-26, 28, Phaladīpikā XXVI.31). Precedence COMB > EX > MT > OWN > DEB > FR/NEU/INI (§B.2). The literal tables below are typed from §B.3,
sharing nothing with the code under test.

The audit (what was found): P1b's channel and P1c's derivation already took the side from the Form B table cells, i.e. per (nature, rung), not from
nature alone; but the side rule existed only as DATA — nothing in either module decided it, and the verifier read the same data the builder was bound
to, so a wrong (e.g. Q3(a), nature-only) table would have been accepted by both. This job makes the side rule CODE in both (`p1_valence.q3c_side`,
`p1_operands_check.spec_side` — the latter written from the spec text, importing nothing from the builder) and makes each refuse a table that
contradicts it. Claims, each with ONE oracle (its single planted reversion is named):

  S1  the builder's side rule equals the spec's 16-cell side table                    (revert: Q3(a) — the nature's side everywhere)
  S2  the verifier's side rule equals the same table, derived independently          (revert: Q3(a))
  S3  a Q3(a) table is refused by name, by the builder and by the verifier            (revert: the contradiction check removed -> accepted)
  S4  both columns, every cell: side AND value in the builder and the verifier        (revert: any one side/value of a cell)
  S5  the owner's golden cases (the job's list) in both derivations, both classes     (revert: Q3(a))
  S6  the Moon's side flips AT the pakṣa change, per instant, in the builder           (revert: the nature read once per window)
  S7  nodes: Rāhu exalted -> favourable 1.0; migration-1401 shapes: Aquarius own -> favourable 0.5, Gemini / Ketu Sagittarius whole-sign MT -> favourable 0.75
      (SR-1401-VERIFIED); no stored sign -> honest null; a node row with a degree range refused   (revert: the reader forces the nodes' MT sign to None)
  S8  independence: the verifier loads nothing of the builder's side rule at runtime    (revert: an import of p1_valence)
  S9  rule version: a table is read only under 1.3.0; 1.0.0 declares none, so nothing moves  (revert: any version accepted)
  S10 the trial flag selects 1.3.0 explicitly and only inside its profile                (revert: the flag ignored / default flipped)
"""
from __future__ import annotations

import ast
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from services.gochara_kernel import p1_operands as P
from services.gochara_kernel import p1_operands_check as chk
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import window_sweep as ws
from services.gochara_rules import p1_inputs as p1
from services.gochara_rules import p1_valence as pv

from .test_a53_window_sweep import _d
from .test_a53_window_sweep_pg import pg  # noqa: F401  (fresh DB per test, 1081 + 1152-1157 applied)
from .test_od1_d2_form_b import (ADVERSE, BY_ID, COMB, DIG, GAIN, MAPPING, NAIS, ROWS, STATIONS, T, A, F, builder, expected_channel, l0, lon, sky,
                                 verifier)

SIDECAR = Path(__file__).resolve().parents[3]
FOR, AGAINST = ws.CHANNEL_FOR, ws.CHANNEL_AGAINST

# ── the spec's side table, typed from ANSWERS.md v2.1 §B.3 (the SIDE of each cell) ───────────────────────────────────
SPEC_SIDE = {
    "benefic": {"EX": F, "MT": F, "OWN": F, "FR": F, "NEU": F, "INI": A, "DEB": A, "COMB": A},
    "malefic": {"EX": F, "MT": F, "OWN": F, "FR": A, "NEU": A, "INI": A, "DEB": A, "COMB": A},
}
# ... and the VALUE of each cell (§B.3): both columns
SPEC_VALUE = {
    "benefic": {"EX": 1.0, "MT": 0.75, "OWN": 0.5, "FR": 0.25, "NEU": 0.125, "INI": 0.75, "DEB": 1.0, "COMB": 1.0},
    "malefic": {"EX": 1.0, "MT": 0.75, "OWN": 0.5, "FR": 0.5, "NEU": 0.625, "INI": 0.75, "DEB": 1.0, "COMB": 1.0},
}
Q3A = {"benefic": F, "malefic": A}                 # the plan's Q3(a): the nature alone decides the side


def _q3a(nature, rung):
    return Q3A[nature]


# ── S1, S2: the two side rules equal the spec ────────────────────────────────────────────────────────────────────────
def test_s1_the_builders_side_rule_is_the_specs_for_every_cell():
    """Planted reversion: `q3c_side` returns the nature's side (Q3(a)) — benefic INI/DEB/COMB and malefic EX/MT/OWN then differ."""
    got = {n: {r: pv.q3c_side(n, r) for r in pv.RUNGS} for n in pv.NATURES}
    assert got == SPEC_SIDE
    # the overrides, and ONLY the overrides, differ from the nature's default (Q3(c): "at the extremes the texts name")
    differs = {(n, r) for n in SPEC_SIDE for r, s in SPEC_SIDE[n].items() if s != Q3A[n]}
    assert differs == {("benefic", "INI"), ("benefic", "DEB"), ("benefic", "COMB"), ("malefic", "EX"), ("malefic", "MT"), ("malefic", "OWN")}


def test_s2_the_verifiers_side_rule_is_the_specs_for_every_cell_derived_independently():
    """Planted reversion: `spec_side` returns the nature's side (Q3(a))."""
    got = {n: {r: chk.spec_side(n, r) for r in chk.RUNGS + ("COMB",)} for n in chk.NATURES}
    assert got == SPEC_SIDE
    with pytest.raises(p1.StrictInputError):
        chk.spec_side("benefic", "XX")


# ── S3: a Q3(a) table is refused, by name, in both ───────────────────────────────────────────────────────────────────
def _q3a_rows():
    """The registry's rows with every side replaced by the nature's (what a table built for Q3(a) would declare)."""
    rows = copy.deepcopy(ROWS)
    for r in rows:
        m = r["category_mapping"]
        if r["factor_id"] == "dignity_of_transit_sign":
            for k, cell in m.items():
                cell["side"] = Q3A[k.split("/")[0]]
        elif r["factor_id"] == "combustion":
            m["combust"]["side"] = F                    # a Q3(a) table lets a benefic's combustion stay favourable
    return rows


def test_s3_a_table_that_declares_q3a_sides_is_refused_by_the_builder_and_by_the_verifier():
    """Planted reversion: the contradiction checks removed — the Q3(a) table would then bind and score."""
    with pytest.raises(p1.StrictInputError) as e:
        pv.mapping_from_rows(_q3a_rows())
    assert e.value.reason == "mapping_side_contradicts_q3c"
    raw = {n: {r: {"side": _q3a(n, r), "value": SPEC_VALUE[n][r]} for r in pv.RUNGS} for n in pv.NATURES}
    with pytest.raises(p1.StrictInputError) as e:
        pv.validate_mapping(raw)
    assert e.value.reason == "mapping_side_contradicts_q3c"
    bad_default = copy.deepcopy(ROWS)
    for r in bad_default:
        if r["factor_id"] == "agent_nature":
            r["category_mapping"]["benefic"]["side"] = A
    with pytest.raises(p1.StrictInputError) as e:
        pv.mapping_from_rows(bad_default)
    assert e.value.reason == "mapping_side_contradicts_q3c"
    # the verifier: the rows are unreadable as one table — every factor of the record carries the named reason, never a number
    check = chk.P1Check(sky("Jupiter", lon("Capricorn")), dignity_rows=DIG, orb_rows=COMB, naisargika_rows=NAIS)
    binding = check.bind(_q3a_rows(), GAIN)
    for fid in ("dignity_of_transit_sign", "combustion", "agent_nature"):
        assert binding.record_problem(fid, {"agent": "jupiter"}) == "category_mapping_side_contradicts_q3c"
    assert not isinstance(check.bind(ROWS, GAIN).evaluate({"agent": "jupiter"}, T), chk.P1Unknown)


# ── S4: both columns, every cell, in both derivations ───────────────────────────────────────────────────────────────
# a sky that realises each (nature, rung): benefic = Jupiter, malefic = Saturn (natural friendship from the period lord's OWN row)
CELL_SKY = {
    ("benefic", "EX"): ("Jupiter", lon("Cancer"), {}), ("benefic", "MT"): ("Jupiter", lon("Sagittarius", 5), {}),
    ("benefic", "OWN"): ("Jupiter", lon("Pisces"), {}), ("benefic", "FR"): ("Jupiter", lon("Aries"), {}),
    ("benefic", "NEU"): ("Jupiter", lon("Aquarius"), {}), ("benefic", "INI"): ("Jupiter", lon("Gemini"), {}),
    ("benefic", "DEB"): ("Jupiter", lon("Capricorn"), {}), ("benefic", "COMB"): ("Jupiter", lon("Cancer", 20), {"sun": lon("Cancer", 23)}),
    ("malefic", "EX"): ("Saturn", lon("Libra"), {}), ("malefic", "MT"): ("Saturn", lon("Aquarius", 5), {}),
    ("malefic", "OWN"): ("Saturn", lon("Capricorn"), {}), ("malefic", "FR"): ("Saturn", lon("Taurus"), {}),
    ("malefic", "NEU"): ("Saturn", lon("Sagittarius"), {}), ("malefic", "INI"): ("Saturn", lon("Leo"), {}),
    ("malefic", "DEB"): ("Saturn", lon("Aries"), {}), ("malefic", "COMB"): ("Saturn", lon("Capricorn", 20), {"sun": lon("Capricorn", 23)}),
}


@pytest.mark.parametrize("event_class", [GAIN, ADVERSE])
@pytest.mark.parametrize("nature,rung", [(n, r) for n in ("benefic", "malefic") for r in pv.RUNGS])
def test_s4_every_cell_of_both_columns_side_and_value_in_the_builder_and_in_the_verifier(nature, rung, event_class):
    """Planted reversion: any one cell's side or value changed in the declared table or the rule (the literals above are the spec's)."""
    lord, longitude, extra = CELL_SKY[(nature, rung)]
    position_at = sky(lord, longitude, **extra)
    side, value = SPEC_SIDE[nature][rung], SPEC_VALUE[nature][rung]
    _src, channel, val = builder(lord, position_at, event_class)
    assert channel == expected_channel(side, event_class), ("builder side", nature, rung)
    assert val == pytest.approx(value), ("builder value", nature, rung)
    ev = verifier(lord, position_at, event_class)
    assert (ev.nature, ev.rung, ev.side, ev.value) == (nature, rung, side, pytest.approx(value)), ("verifier", nature, rung)
    state = _lord_state(lord, position_at, event_class)
    assert (state.nature, state.rung, state.side, state.value) == (nature, rung, side, pytest.approx(value))


def _lord_state(lord, position_at, event_class):
    """P1b's own `LordValence` for the lord at T (the object that decides the side), built from the same L0 rows."""
    ops = P.P1Operands(l0(), position_at, form_b=MAPPING)
    v = ops.view(lord, STATIONS if lord in ("Mercury", "Venus") else None)
    from services.gochara_kernel import p1_nature_operands as nat
    rules = pv.LordRungRules(lord, DIG, NAIS)
    return nat.P1LordValence(graha=lord, event_class=event_class, mapping=MAPPING, rules=rules,
                             nature=nat.NatureOperands(lord, lambda b, t: position_at(b, t)), position_at=lambda b, t: position_at(b, t),
                             combust_at=None if lord in p1.NEVER_COMBUST else v._combust_flag).state_at(T)


# ── S5: the job's golden cases ───────────────────────────────────────────────────────────────────────────────────────
VENUS_COMBUST = ("Venus", lon("Libra", 10), {"sun": lon("Libra", 13)})       # in its own sign, 3 degrees from the Sun: the combustion rung wins
GOLDEN = [
    ("Jupiter in Capricorn: debility -> adverse 1.00", ("Jupiter", lon("Capricorn"), {}), "DEB", A, 1.0),
    ("Venus combust: the depression rung -> adverse 1.00", VENUS_COMBUST, "COMB", A, 1.0),
    ("Saturn in Libra: exaltation -> favourable 1.00", ("Saturn", lon("Libra"), {}), "EX", F, 1.0),
    ("Mars in Scorpio: own -> favourable 0.50", ("Mars", lon("Scorpio"), {}), "OWN", F, 0.5),
    ("Mercury in Virgo: exalted benefic -> unchanged, favourable 1.00", ("Mercury", lon("Virgo", 10), {}), "EX", F, 1.0),
    ("Jupiter in Gemini: inimical (Jupiter->Mercury) -> adverse 0.75", ("Jupiter", lon("Gemini"), {}), "INI", A, 0.75),
    ("Moon in Capricorn, waxing: NEU -> favourable 0.125", ("Moon", lon("Capricorn"), {"sun": lon("Capricorn") - 150.0}), "NEU", F, 0.125),
    ("Moon in Capricorn, waning: NEU -> adverse 0.625", ("Moon", lon("Capricorn"), {"sun": lon("Capricorn") + 150.0}), "NEU", A, 0.625),
]


@pytest.mark.parametrize("event_class", [GAIN, ADVERSE])
@pytest.mark.parametrize("name,case,rung,side,value", GOLDEN, ids=[g[0].split(":")[0] for g in GOLDEN])
def test_s5_the_golden_cases_in_the_builder_and_the_independent_verifier(name, case, rung, side, value, event_class):
    """Planted reversion: Q3(a) in either derivation (see `test_s5b`)."""
    lord, longitude, extra = case
    position_at = sky(lord, longitude, **extra)
    _src, channel, val = builder(lord, position_at, event_class)
    assert (channel, val) == (expected_channel(side, event_class), pytest.approx(value)), name
    ev = verifier(lord, position_at, event_class)
    assert (ev.rung, ev.side, ev.value) == (rung, side, pytest.approx(value)), name


def _golden_problems():
    """The goldens against the CURRENT code, builder and verifier: [] when every one holds (an oracle that can read false)."""
    bad = []
    for name, (lord, longitude, extra), rung, side, value in GOLDEN:
        position_at = sky(lord, longitude, **extra)
        for event_class in (GAIN, ADVERSE):
            try:
                _s, channel, _v = builder(lord, position_at, event_class)
            except p1.StrictInputError as exc:
                bad.append((name, "builder", exc.reason))
                continue
            if channel != expected_channel(side, event_class):
                bad.append((name, "builder", channel))
        if verifier(lord, position_at, GAIN).side != side:
            bad.append((name, "verifier"))
    return bad


def test_s5b_forcing_q3a_into_either_derivation_makes_the_golden_oracle_fail(monkeypatch):
    """The planted reversion of S1/S2/S5: the side rule replaced by the nature's side. Builder and verifier are forced SEPARATELY; each must be caught
    (the builder by the golden channels or by its own table cross-check, the verifier by its sides)."""
    assert _golden_problems() == []
    monkeypatch.setattr(pv, "q3c_side", _q3a)
    assert any(b[1] == "builder" for b in _golden_problems())
    monkeypatch.undo()
    assert _golden_problems() == []
    monkeypatch.setattr(chk, "spec_side", _q3a)
    assert any(b[1] == "verifier" for b in _golden_problems())


# ── S6: the per-instant flip ─────────────────────────────────────────────────────────────────────────────────────────
def test_s6_the_moons_side_flips_at_the_paksa_change_inside_one_window():
    """The Moon stays in Capricorn (Saturn's sign: NEU for the Moon, whose own table calls Saturn neutral) while the Sun-Moon elongation passes 180 degrees
    (day 5): benefic (waxing) before -> favourable 0.125, malefic (waning) after -> adverse 0.625; the nature's change instant is among the cuts.
    Planted reversion: the nature read once per window (the side would not flip)."""
    moon0 = lon("Capricorn", 10)

    def position_at(body, t):
        days = (t - _d(0)).total_seconds() / 86400.0
        body = body.title()
        if body == "Moon":
            return moon0
        if body == "Sun":
            return (moon0 - 170.0 - 2.0 * days) % 360.0                # elongation (Moon - Sun) = 170 + 2 d: crosses 180 on day 5
        return (moon0 + 100.0 + 10.0 * (len(body) % 5)) % 360.0
    ops = P.P1Operands(l0(), position_at, form_b=MAPPING)
    src = ops.sources_for("Moon", complete=True, stations=None, event_class=GAIN)
    nature_src = src["agent_nature"]
    before, after = _d(4), _d(6)
    assert nature_src.channel_at(before) == FOR and src["dignity_of_transit_sign"].value_at(before) == pytest.approx(0.125)
    assert nature_src.channel_at(after) == AGAINST and src["dignity_of_transit_sign"].value_at(after) == pytest.approx(0.625)
    cuts = nature_src.boundaries(_d(0), _d(10))
    assert any(abs((c - _d(5)).total_seconds()) < 5.0 for c in cuts), cuts
    # the independent verifier agrees on both sides of the flip
    binding = chk.P1Check(position_at, dignity_rows=DIG, orb_rows=COMB, naisargika_rows=NAIS).bind(ROWS, GAIN)
    e1, e2 = binding.evaluate({"agent": "moon"}, before), binding.evaluate({"agent": "moon"}, after)
    assert (e1.side, e1.value) == (F, pytest.approx(0.125)) and (e2.side, e2.value) == (A, pytest.approx(0.625))


# ── S7: the nodes ────────────────────────────────────────────────────────────────────────────────────────────────────
def _dig_1401(*, ketu=False):
    """The bg_dignity_reference rows as migration 1401 (PR #3840, SR-DOCTRINE-H) leaves them: Rāhu mūlatrikoṇa Gemini with NO degree range, own Aquarius.
    Typed from the migration's VALUES (moolatrikona_sign 'Gemini', moolatrikona_from/to NULL, own_signs {'Aquarius'}); it is not applied to any database.
    `ketu=True` adds the verse's Ketu mūlatrikoṇa SIGN (Sagittarius, BPHS 47.34-39, bphs:PG573:C2-PG574:C1) in the same shape — the sign only, nothing else of the row."""
    rows = copy.deepcopy(DIG)
    for r in rows:
        if r["graha"] == "Rahu":
            r.update(moolatrikona_sign="Gemini", moolatrikona_from=None, moolatrikona_to=None, own_signs=["Aquarius"])
        if ketu and r["graha"] == "Ketu":
            r.update(moolatrikona_sign="Sagittarius", moolatrikona_from=None, moolatrikona_to=None)
    return rows


def _node_both(node, dig, position, event_class):
    """(builder source, verifier evaluation) for a node over the given L0 dignity rows."""
    ops = P.P1Operands(P.P1L0(P.dignity_reference_from_rows(dig), P.combustion_orbs_from_rows(COMB), P.naisargika_from_rows(NAIS)), position, form_b=MAPPING)
    src = ops.sources_for(node, complete=True, event_class=event_class)
    ev = chk.P1Check(position, dignity_rows=dig, orb_rows=COMB, naisargika_rows=NAIS).bind(ROWS, event_class).evaluate({"agent": node.lower()}, T)
    return src, ev


def test_s7_nodes_exalted_rahu_is_favourable_and_the_1401_rows_number_own():
    """Rāhu in Taurus is exalted (L0 as seeded): malefic column, favourable 1.00, both derivations. With the 1401 rows, Rāhu in Aquarius is OWN, malefic ->
    favourable 0.50 in both. Planted reversion: classify the reserved sign by friendship."""
    for event_class in (GAIN, ADVERSE):
        _s, channel, val = builder("Rahu", sky("Rahu", lon("Taurus", 10)), event_class)
        assert (channel, val) == (expected_channel(F, event_class), pytest.approx(1.0))
        ev = verifier("Rahu", sky("Rahu", lon("Taurus", 10)), event_class)
        assert (ev.nature, ev.rung, ev.side, ev.value) == ("malefic", "EX", F, pytest.approx(1.0))
    src, ev = _node_both("Rahu", _dig_1401(), sky("Rahu", lon("Aquarius", 10)), GAIN)
    assert src["agent_nature"].channel_at(T) == FOR and src["dignity_of_transit_sign"].value_at(T) == pytest.approx(0.5)
    assert (ev.rung, ev.side, ev.value) == ("OWN", F, pytest.approx(0.5))


@pytest.mark.parametrize("node, sign, deg", [("Rahu", "Gemini", 0.5), ("Rahu", "Gemini", 15.0), ("Rahu", "Gemini", 29.9),
                                             ("Ketu", "Sagittarius", 0.5), ("Ketu", "Sagittarius", 29.9)])
def test_s7_a_node_moolatrikona_with_no_stored_degree_range_is_the_whole_sign_MT_in_both_derivations(node, sign, deg):
    """SR-1401-VERIFIED / ANSWERS.md v2.1 §B.5 + BPHS 47.34-39 (bphs:PG573:C2-PG574:C1: the verse names Gemini and Sagittarius as the nodes' mūlatrikoṇa and gives
    no degrees): migration 1401 stores the SIGN with NULL from/to, and the strict reader reads that as the WHOLE sign. Rāhu in Gemini / Ketu in Sagittarius is MT,
    malefic column: favourable 0.75 (§B.3), builder and independent verifier, at both ends of the sign. Planted reversion: the reader forces the nodes'
    `moolatrikona_sign` back to None (strict L0 reader, p1_inputs) — both derivations then answer `node_dignity_unclassified`."""
    dig = _dig_1401(ketu=True)
    position = sky(node, lon(sign, deg))
    for event_class in (GAIN, ADVERSE):
        src, ev = _node_both(node, dig, position, event_class)
        assert src["agent_nature"].channel_at(T) == expected_channel(F, event_class), (node, deg, "builder side")
        assert src["dignity_of_transit_sign"].value_at(T) == pytest.approx(0.75), (node, deg, "builder value")
        assert (ev.nature, ev.rung, ev.side, ev.value) == ("malefic", "MT", F, pytest.approx(0.75)), (node, deg, "verifier")


def test_s7_where_no_node_moolatrikona_sign_is_stored_gemini_and_sagittarius_stay_an_honest_null():
    """The pre-1401 database (and 1401's Ketu row, which this test leaves without a sign): no stored sign -> no whole-sign MT is invented; the node in the verse's
    sign is `node_dignity_unclassified` in both derivations (B.10 / N.7.6). Planted reversion: the reader treats every node's reserved sign as MT regardless of
    what L0 stores."""
    for node, sign, dig in (("Rahu", "Gemini", DIG), ("Ketu", "Sagittarius", DIG), ("Ketu", "Sagittarius", _dig_1401())):
        src, ev = _node_both(node, dig, sky(node, lon(sign, 10)), GAIN)
        assert src["agent_nature"].channel_at(T) is None and src["agent_nature"].unknown_reason(T) == "node_dignity_unclassified", (node, "builder")
        assert isinstance(ev, chk.P1Unknown) and ev.reason == "node_dignity_unclassified", (node, "verifier")


def test_s7_a_node_row_that_gives_a_degree_range_is_refused_not_read_as_a_whole_sign():
    """The reader's whole-sign reading is for the verse's rangeless mūlatrikoṇa only: a node row carrying a partial or full degree range contradicts it and is
    refused by name (no silent widening of a stated range). Planted reversion: the check removed — the range would be ignored and the whole sign scored."""
    rows = _dig_1401()
    for r in rows:
        if r["graha"] == "Rahu":
            r.update(moolatrikona_from=0.0, moolatrikona_to=20.0)
    with pytest.raises(p1.StrictInputError) as e:
        p1.validated_dignity_row(rows, "Rahu")
    assert e.value.reason == "dignity_node_moolatrikona_range_not_whole_sign"


# ── S8: independence — an import-graph proof ────────────────────────────────────────────────────────────────────────
BUILDER_SIDE_MODULES = ("services.gochara_rules.p1_valence", "services.gochara_kernel.p1_nature_operands", "services.gochara_kernel.p1_operands",
                        "services.gochara_kernel.window_sweep", "services.gochara_kernel.window_solver")
# `-I` drops the user site and PYTHONPATH, where a CI runner's pip-installed pyswisseph can live, and the package `__init__` imports `knots` (which needs it at import time):
# hand the child the parent's own import path, and a stand-in for a runner without the binding, so what is measured is only which of OUR modules the import pulls in
# (the same two moves as `test_od1_s2_solver_check`'s checker-imports-nothing-of-the-builder probe)
_PROBE = ("import sys, json; sys.path[:0] = [sys.argv[1], *json.loads(sys.argv[3])]\n"
          "try:\n    import swisseph\nexcept ImportError:\n    from unittest import mock; sys.modules['swisseph'] = mock.MagicMock()\n"
          "import importlib; importlib.import_module(sys.argv[2]); "
          "print('\\n'.join(sorted(m for m in sys.modules if m.startswith('services.gochara'))))")


def _loaded_after_importing(module: str) -> set[str]:
    """The `services.gochara*` modules a FRESH interpreter holds after importing `module` alone (isolated: no cwd, no PYTHONPATH)."""
    out = subprocess.run([sys.executable, "-I", "-c", _PROBE, str(SIDECAR), module, json.dumps(sys.path)], capture_output=True, text=True, timeout=120, check=True)
    return set(out.stdout.split())


def test_s8_the_verifier_loads_nothing_of_the_builders_side_rule_at_runtime():
    """The real import closure (not a name list): importing the verifier's P1 module pulls in none of the builder's side-rule modules. The detector can read
    true — importing P1b's module in the same way DOES load `p1_valence`. Planted reversion: `from services.gochara_rules import p1_valence` in the verifier."""
    verifier_loaded = _loaded_after_importing("services.gochara_kernel.p1_operands_check")
    assert "services.gochara_kernel.p1_operands_check" in verifier_loaded
    assert not verifier_loaded & set(BUILDER_SIDE_MODULES), verifier_loaded & set(BUILDER_SIDE_MODULES)
    builder_loaded = _loaded_after_importing("services.gochara_kernel.p1_nature_operands")
    assert "services.gochara_rules.p1_valence" in builder_loaded            # the probe sees a real dependency when there is one
    # and no source-level mention either, at any depth (a lazy import inside a function is invisible to the runtime probe above)
    tree = ast.parse(Path(chk.__file__).read_text(encoding="utf-8"))
    mentioned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mentioned.add((node.module or "").split(".")[-1])
            mentioned.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            mentioned.update(a.name.split(".")[-1] for a in node.names)
    assert not mentioned & {"p1_valence", "p1_nature_operands", "p1_operands", "window_sweep", "window_solver", "q3c_side"}, mentioned


# ── S9: the rule version ─────────────────────────────────────────────────────────────────────────────────────────────
def test_s9_the_side_rule_is_defined_for_1_3_0_only_and_1_0_0_declares_no_table():
    """Planted reversion: any rule_version accepted by the builder's adapter or the verifier's binding."""
    old = ws.registry_factor_rows("P1", "1.0.0")
    assert P.form_b_mapping(old) is None and not pv.has_form_b(old)            # 1.0.0: no table, the Form B path is never engaged
    wrong = [{**r, "rule_version": "1.0.0"} for r in ROWS]
    with pytest.raises(p1.StrictInputError) as e:
        pv.mapping_from_rows(wrong)
    assert e.value.reason == "side_rule_undefined_for_version"
    check = chk.P1Check(sky("Jupiter", lon("Capricorn")), dignity_rows=DIG, orb_rows=COMB, naisargika_rows=NAIS)
    binding = check.bind(wrong, GAIN)
    assert binding.record_problem("dignity_of_transit_sign", {"agent": "jupiter"}) == "side_rule_undefined_for_version"
    assert pv.SIDE_RULE_VERSION == chk.SIDE_RULE_VERSION == "1.3.0"
    # the registry's rows carry exactly the table the rule accepts (S1/S2/S3 on the real declaration)
    assert {r["rule_version"] for r in ROWS} == {"1.3.0"} and set(BY_ID) == {"dignity_of_transit_sign", "combustion", "agent_nature"}


# ── S10: the trial flag ──────────────────────────────────────────────────────────────────────────────────────────────
P1_FORM_B = ("P1", "1.3.0")


def test_s10_the_default_selection_is_1_0_0_and_the_flag_selects_1_3_0_inside_its_profile_only():
    """Planted reversion: the flag ignored (the trial would run 1.0.0) or 1.3.0 selected by default (production would move)."""
    assert P1_FORM_B not in rr.bound_path_refs() and rr.p1_form_b_selected() is False
    assert rr.selected_versions_for("marriage")["P1"] == "1.0.0"
    plain_factors = rr.bound_factor_refs()
    with rr.rule_profile(final_rules=False, p1_form_b=True):
        assert rr.p1_form_b_selected() is True and P1_FORM_B in rr.bound_path_refs()
        assert rr.selected_versions_for("marriage")["P1"] == "1.3.0" and rr.selected_path_version("business_launch", "P1") == "1.3.0"
        assert all(v == "1.0.0" for p, v in rr.selected_versions_for("marriage").items() if p != "P1")     # nothing else moves
        assert set(rr.P1_FORM_B_FACTOR_REFS) <= set(rr.bound_factor_refs())
        rr._membership_consistent()                                       # the selection is drawn from the bound catalogue
    assert P1_FORM_B not in rr.bound_path_refs() and rr.selected_versions_for("marriage")["P1"] == "1.0.0"
    assert rr.bound_factor_refs() == plain_factors                        # nothing leaks out of the profile
    # SR-OD1 merge-back: the FINAL profile selects the owner-confirmed doctrine rows by default (V1: FINAL_SELECTED_PATH_REFS, P1@1.3.0), flag or no flag; the trial
    # flag's own claim above (measuring profile: default 1.0.0, flag selects 1.3.0 inside its scope only) is unchanged
    with rr.rule_profile(final_rules=True, p1_form_b=False):
        assert P1_FORM_B in rr.bound_path_refs() and rr.selected_versions_for("marriage")["P1"] == "1.3.0"
    with rr.rule_profile(final_rules=True, p1_form_b=True):
        assert rr.selected_versions_for("marriage")["P1"] == "1.3.0"
    with pytest.raises(ValueError, match="gochara_v5_p1_form_b must be a boolean"):
        with rr.rule_profile(final_rules=False, p1_form_b="yes"):
            pass


def test_s10_an_nd_h_class_keeps_its_own_p1_version_under_the_flag():
    """The eight ND-H classes run P1 at 1.2.0 under the final rules (plan I-5: their move to 1.3.0 is a separate decision). Planted reversion: the flag
    overrides a class override."""
    from services.gochara_rules import registry as reg
    nd_h = sorted(reg.ND_H_CLASSES)[0]
    with rr.rule_profile(final_rules=True, p1_form_b=True):
        assert rr.selected_versions_for(nd_h)["P1"] == reg.ND_H_VERSION
        assert rr.selected_versions_for("marriage")["P1"] == "1.3.0"


def test_s10_the_writer_reads_the_flag_from_its_config_and_the_harness_sets_it(monkeypatch):
    """The writer's profile wrapper and the slice harness both carry `gochara_v5_p1_form_b`; absent = off. Planted reversion: the wrapper drops the key."""
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from scripts.kala_gochara_cutover import j4d_slice_qualify as q
    seen = []

    class Ctx:
        def __init__(self, **config):
            self.config = config

    @writer._with_rule_profile
    def probe(self, ctx):
        seen.append((rr.p1_form_b_selected(), rr.selected_versions_for("marriage")["P1"], writer._p1_form_b_bound()))
    probe(None, Ctx(gochara_v5_final_rules=False))
    probe(None, Ctx(gochara_v5_final_rules=False, gochara_v5_p1_form_b=True))
    assert seen == [(False, "1.0.0", False), (True, "1.3.0", True)]
    # the harness: `build_slice(p1_form_b=True)` puts the key on the writer's config; the default leaves it out (byte-identical to before)
    configs = []

    class Writer:
        def plan_substeps(self, ctx):
            configs.append(dict(ctx.config))
            return []
    monkeypatch.setattr(writer, "GocharaV5Writer", Writer)
    monkeypatch.setattr(q, "require_lane", lambda conn: None)
    monkeypatch.setattr(q, "ensure_near_miss_layer", lambda conn: "applied")
    q.build_slice(object(), chart_id="c", horizon=(None, None), classes=["marriage"], ephe_path="/x")
    q.build_slice(object(), chart_id="c", horizon=(None, None), classes=["marriage"], ephe_path="/x", p1_form_b=True)
    assert "gochara_v5_p1_form_b" not in configs[0] and configs[1]["gochara_v5_p1_form_b"] is True


def test_s10_the_command_lines_expose_the_flag():
    """`j4d_slice_qualify qualify --p1-form-b` and `verification_job --p1-form-b` exist, default off. Planted reversion: the option removed."""
    from pipeline.orchestrator import verification_job
    from scripts.kala_gochara_cutover import j4d_slice_qualify as q
    assert "--p1-form-b" in Path(q.__file__).read_text(encoding="utf-8")
    assert "--p1-form-b" in Path(verification_job.__file__).read_text(encoding="utf-8")
    seen = []
    import argparse
    orig = argparse.ArgumentParser.parse_args

    def spy(self, args=None, namespace=None):
        ns = orig(self, args, namespace)
        seen.append(getattr(ns, "p1_form_b", None))
        raise SystemExit(0)
    argparse.ArgumentParser.parse_args = spy
    try:
        for argv in (["qualify", "--golden", "g", "--dsn", "d", "--ephe-path", "e", "--output", "o", "--p1-form-b"],
                     ["qualify", "--golden", "g", "--dsn", "d", "--ephe-path", "e", "--output", "o"]):
            with pytest.raises(SystemExit):
                q.main(argv)
    finally:
        argparse.ArgumentParser.parse_args = orig
    assert seen == [True, False]


def test_s10_verification_job_selects_1_3_0_iff_its_flag_is_given(monkeypatch):
    """B-1 (lane review of od1-q3c): the VERIFICATION half of the trial. `verification_job --p1-form-b` really runs the wrapped job under P1@1.3.0, and
    without it under 1.0.0 (acceptance (d); the build's flag must be matched or the kernel raises `VerificationDisagrees("selection", ...)`).
    Planted reversion: `main` parses the option but ignores it (`rule_profile(final_rules=args.final_rules)`) — the first selection then reads 1.0.0."""
    from pipeline.orchestrator import verification_job
    seen = []
    monkeypatch.setattr(verification_job, "_run", lambda args: seen.append(rr.selected_versions_for("marriage")["P1"]) or 0)
    assert verification_job.main(["--chart", "c", "--p1-form-b"]) == 0
    assert verification_job.main(["--chart", "c"]) == 0
    assert seen == ["1.3.0", "1.0.0"]


def test_s10_under_the_flag_the_1_3_0_rows_persist_and_read_back_with_their_table_on_the_real_schema(pg):
    """The flag is not only a selection: P1@1.3.0 and its three factors seal into the REAL registry tables under the profile, `bound_factor_rows` reads the
    authored table back, and the builder's adapter builds the same mapping from what was persisted. By default the seed is the 1.0.0 five.
    Planted reversion: `bound_factor_refs` ignoring the profile (the soft-factor members would then be unbound and the seed refused)."""
    plain = rr.RuleRegistryStore(pg).seed()
    assert plain["paths"] == 5
    with rr.rule_profile(final_rules=False, p1_form_b=True):
        store = rr.RuleRegistryStore(pg)
        counts = store.seed()
        assert counts["paths"] == 1 and counts["reused"] > 0 and (P1_FORM_B in rr.bound_path_refs())    # one NEW path; the 1.0.0 five are reused
        rows = store.bound_factor_rows("P1", "1.3.0")
    assert {r["factor_id"] for r in rows} == {"dignity_of_transit_sign", "combustion", "agent_nature"}
    assert all(r["rule_version"] == "1.3.0" for r in rows)
    persisted = P.form_b_mapping(rows)
    assert persisted is not None and persisted.cells == MAPPING.cells
    assert {n: {r: persisted.side_and_value(n, r)[0] for r in pv.RUNGS} for n in pv.NATURES} == SPEC_SIDE

