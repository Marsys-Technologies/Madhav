"""SR-OD1 D2 — the owner-confirmed P1 values (Form B) bound under the new rule version P1@1.3.0.

Doctrine: OWNER-DOCTRINE-CONFIRMED-20261021 / P1-MAPPING-DECISION (ANSWERS.md v2.1 §B.2-B.3, Form B), SR-Q6-L1, SR-SOLVER-PLAN-1. The owner's
table below is typed from ANSWERS.md §B.3 and its golden cases from §B.2 — a LITERAL copy that shares nothing with the registry, so a changed
registry cell, a changed precedence or a swapped friendship column fails here. The classical dignity tables (BPHS 3.x; Bṛhat Jātaka II.16-17
for natural friendship) are re-typed in `classical_rung` as a third, independent derivation of the effective rung.

Claims, each with ONE oracle (the single planted reversion that must fail it is named):

  D-1 the registry rows P1@1.3.0 carry exactly the owner's 14 dignity cells + the combust cell + the default side per nature, each with its
      evidence tag, `ruling_ref` and `uncalibrated_default` (revert: any one cell value/side/tag changed);
  D-2 the version plan: P1@1.3.0 = dignity + combustion + agent_nature (maitrī RETIRED, Q7 b), the 1.0.0 rows are not edited and are marked
      superseded, and nothing binds or selects 1.3.0 yet (revert: `maitri_compound@1.3.0` in the soft factors / a 1.3.0 ref in BOUND_PATH_REFS);
  D-3 the three rows are ONE table: the builder's adapter reads the same 2 x 8 the verifier parses, refuses a neutral element that is not
      1.0, and a 1.0.0 grain declares no table (revert: the adapter drops the combust cell);
  D-4 the owner's golden cases hold in the BUILDER (P1a state + P1b valence) and in the independent VERIFIER (P1c), side AND value, for a gain
      and an adverse class (revert: the sweep reads the sign lord's friendship row — Jupiter in Gemini reads NEU favourable 0.125);
  D-5 precedence COMB > EX > MT > OWN > DEB > FR/NEU/INI (revert: debility after friendship — Jupiter in Capricorn reads NEU);
  D-6 the whole zodiac: for every classical lord, sign and degree the builder and the verifier equal the owner's table at the rung
      re-derived from the classical tables, for both natures of the Moon and of Mercury (revert: any rung rule changed);
  D-7 the nodes: a reserved sign is unnumbered with its named reason, a classified sign takes the malefic column, combustion is `na`
      (revert: classify the reserved sign by friendship);
  D-8 builder and verifier agree on a whole window drawn from the registry rows: the side flips at the sign ingress, the peak is the flip
      instant, the independent verifier reproduces the numbers (revert: the verifier's value table read from a different cell);
  D-9 the writer follows the registry: the L0 tables are consumed iff a bound P1 version declares the table, and the persisted rows are read
      back WITH the authored table (revert: `bound_factor_rows` drops `category_mapping`).
"""
from __future__ import annotations

import json
import pathlib
from datetime import timedelta

import pytest

from services.gochara_kernel import p1_operands as P
from services.gochara_kernel import p1_operands_check as chk
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import p1_inputs as p1
from services.gochara_rules import p1_valence as pv
from services.gochara_rules import registry as reg

from .test_a53_window_sweep import _d, _draft, _rec
from .test_od1_w0_interface import _Conn, _stored

FIX = pathlib.Path(__file__).parent.parent / "gochara_rules" / "fixtures"
DIG = json.loads((FIX / "l0_dignity_reference_2026_10_02.json").read_text())
COMB = json.loads((FIX / "l0_combustion_orbs_2026_10_02.json").read_text())
NAIS = json.loads((FIX / "l0_naisargika_2026_10_02.json").read_text())
pytest.importorskip("ga_writers.ga_condition_writer")
FOR, AGAINST = ws.CHANNEL_FOR, ws.CHANNEL_AGAINST
GAIN, ADVERSE = "marriage", "bereavement"
F, A = "favourable", "adverse"

# ── the owner's table, typed from ANSWERS.md v2.1 §B.3 (side, value, evidence tag) ───────────────────────────────────
OWNER = {
    "benefic": {"EX": (F, 1.0, "V"), "MT": (F, 0.75, "V"), "OWN": (F, 0.5, "V"), "FR": (F, 0.25, "V"), "NEU": (F, 0.125, "B"),
                "INI": (A, 0.75, "Vs/I"), "DEB": (A, 1.0, "V")},
    "malefic": {"EX": (F, 1.0, "V"), "MT": (F, 0.75, "I"), "OWN": (F, 0.5, "I"), "FR": (A, 0.5, "Vs/I"), "NEU": (A, 0.625, "I"),
                "INI": (A, 0.75, "V"), "DEB": (A, 1.0, "V")},
}
OWNER_COMB = (A, 1.0, "V")


def owner_cell(nature, rung):
    return OWNER_COMB if rung == "COMB" else OWNER[nature][rung]


def expected_channel(side, event_class):
    """Spec §3.1 as ANSWERS §B.3 states it: 'favourable' feeds the channel a benefic lord feeds — evidence FOR for a gain class,
    evidence AGAINST for an adverse class; 'adverse' the reverse."""
    gain_side = FOR if event_class == GAIN else AGAINST
    other = AGAINST if gain_side == FOR else FOR
    return gain_side if side == F else other


# ── the registry rows ────────────────────────────────────────────────────────────────────────────────────────────────
ROWS = ws.registry_factor_rows("P1", "1.3.0")
BY_ID = {r["factor_id"]: r for r in ROWS}
MAPPING = P.form_b_mapping(ROWS)


def test_d1_the_registry_rows_carry_exactly_the_owners_cells_with_their_evidence_tags():
    """Planted reversion: any one cell's value, side or tag changed."""
    dig = BY_ID["dignity_of_transit_sign"]["category_mapping"]
    assert set(dig) == {f"{n}/{r}" for n in OWNER for r in OWNER[n]}
    for nature in OWNER:
        for rung, (side, value, tag) in OWNER[nature].items():
            assert dig[f"{nature}/{rung}"] == {"side": side, "value": value, "evidence": tag}, (nature, rung)
    assert BY_ID["combustion"]["category_mapping"] == {"combust": {"side": OWNER_COMB[0], "value": OWNER_COMB[1], "evidence": OWNER_COMB[2]},
                                                       "not_combust": {"value": 1.0}}
    assert BY_ID["agent_nature"]["category_mapping"] == {"benefic": {"side": F, "value": 1.0}, "malefic": {"side": A, "value": 1.0}}
    for row in ROWS:
        assert row["rule_version"] == "1.3.0" and row["calibration_status"] == "uncalibrated_default"
        assert row["ruling_ref"] == "P1-MAPPING-DECISION"
        assert "OWNER-DOCTRINE-CONFIRMED-20261021" in row["effect"] or row["factor_id"] != "dignity_of_transit_sign"
    assert "SR-Q6-L1" in BY_ID["combustion"]["effect"]
    # the tags are in the registry notes too, cell by cell (the owner's request)
    for nature in OWNER:
        for rung, (side, value, tag) in OWNER[nature].items():
            assert f"{nature}/{rung} {side} {value:g} [{tag}]" in BY_ID["dignity_of_transit_sign"]["effect"]


def test_d2_the_version_plan_maitri_retired_old_rows_unedited_and_nothing_bound_yet():
    """Planted reversion: `maitri_compound@1.3.0` among the soft factors, or ("P1", "1.3.0") in the bound catalogue."""
    path = reg.RULE_PATHS[("P1", "1.3.0")]
    assert path["soft_factors"] == [("dignity_of_transit_sign", "1.3.0"), ("combustion", "1.3.0"), ("agent_nature", "1.3.0")]
    assert ("maitri_compound", "1.3.0") not in reg.FACTORS
    assert reg.SUPERSEDED_FACTORS[("maitri_compound", "1.0.0")]["superseded_by"] is None
    assert reg.SUPERSEDED_PATHS[("P1", "1.0.0")]["superseded_by"] == ("P1", "1.3.0")
    for fid in ("dignity_of_transit_sign", "combustion", "agent_nature"):
        assert reg.SUPERSEDED_FACTORS[(fid, "1.0.0")]["superseded_by"] == (fid, "1.3.0")
    # the sealed 1.0.0 rows are as they were authored: no mapping, the 1.0.0 soft factors, maitrī still there
    assert reg.RULE_PATHS[("P1", "1.0.0")]["soft_factors"] == [
        ("dignity_of_transit_sign", "1.0.0"), ("combustion", "1.0.0"), ("agent_nature", "1.0.0"), ("maitri_compound", "1.0.0")]
    assert all("category_mapping" not in reg.FACTORS[(f, "1.0.0")] for f in ("dignity_of_transit_sign", "combustion", "agent_nature"))
    assert reg.FACTORS[("dignity_of_transit_sign", "1.0.0")]["ordering_anchor"]["own"] == 30
    # not bound, not selected, and no ND-H class runs P1 at 1.3.0 (their decision waits for the V-8 check, plan I-5)
    assert ("P1", "1.3.0") not in rr.bound_path_refs() and ("P1", "1.3.0") not in rr.SELECTED_PATH_REFS
    assert all(v != "1.3.0" for v in rr.CLASS_SELECTION_OVERRIDES.values())
    assert not any(v == "1.3.0" for _f, v in rr.BOUND_FACTOR_REFS)
    assert reg.H_TABLE_VERSIONS["1.3.0"] == "spec_2_2"


def test_d3_the_three_rows_are_one_table_and_a_1_0_0_grain_declares_none():
    """Planted reversion: the adapter drops the combust cell (COMB would then be refused as a missing cell)."""
    for nature in OWNER:
        for rung in OWNER[nature]:
            assert MAPPING.side_and_value(nature, rung) == owner_cell(nature, rung)[:2]
        assert MAPPING.side_and_value(nature, "COMB") == OWNER_COMB[:2]
    assert P.form_b_mapping(ws.registry_factor_rows("P1", "1.0.0")) is None
    assert not pv.has_form_b(ws.registry_factor_rows("P1", "1.0.0"))
    # a neutral element that is not 1.0 would make the sources' product differ from the table: refused by name
    bad = [dict(r) for r in ROWS]
    bad[[r["factor_id"] for r in bad].index("combustion")] = {**BY_ID["combustion"], "category_mapping": {
        "combust": BY_ID["combustion"]["category_mapping"]["combust"], "not_combust": {"value": 0.9}}}
    with pytest.raises(p1.StrictInputError) as e:
        pv.mapping_from_rows(bad)
    assert e.value.reason == "form_b_neutral_element_not_one"
    with pytest.raises(p1.StrictInputError) as e:
        pv.mapping_from_rows([r for r in ROWS if r["factor_id"] != "agent_nature"])
    assert e.value.reason == "category_mapping_undeclared"


# ── the sky, the two derivations ─────────────────────────────────────────────────────────────────────────────────────
T = _d(5)
STATIONS = [_d(-300), _d(300)]
SIGNS = p1.SIGNS
SIGN_LORD = dict(zip(SIGNS, ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")))


def l0():
    return P.P1L0(P.dignity_reference_from_rows(DIG), P.combustion_orbs_from_rows(COMB), P.naisargika_from_rows(NAIS))


def sky(lord, lon, *, sun=None, moon=None, mars=None, saturn=None):
    """Every body sits far from the lord (in a different sign, >= 90 degrees away) unless a test places it; all move slowly so the retrograde
    probe of Mercury / Venus reads motion. The Sun defaults to 150 degrees from the lord (never combust)."""
    pos = {"Sun": (lon + 150.0) % 360.0, "Moon": (lon + 100.0) % 360.0, "Mars": (lon + 105.0) % 360.0, "Mercury": (lon + 120.0) % 360.0,
           "Jupiter": (lon + 130.0) % 360.0, "Venus": (lon + 140.0) % 360.0, "Saturn": (lon + 170.0) % 360.0,
           "Rahu": (lon + 190.0) % 360.0, "Ketu": (lon + 10.0 + 180.0 + 20.0) % 360.0}
    pos[lord] = lon
    for k, v in (("Sun", sun), ("Moon", moon), ("Mars", mars), ("Saturn", saturn)):
        if v is not None and k != lord:
            pos[k] = v % 360.0
    if lord == "Sun" and sun is not None:
        pos["Sun"] = sun % 360.0
    return lambda body, t: (pos[body.title()] + 0.001 * (t - _d(0)).total_seconds() / 86400.0) % 360.0


def builder(lord, position_at, event_class):
    ops = P.P1Operands(l0(), position_at, form_b=MAPPING)
    src = ops.sources_for(lord, complete=True, stations=STATIONS if lord in ("Mercury", "Venus") else None, event_class=event_class)
    return src, src["agent_nature"].channel_at(T), src["dignity_of_transit_sign"].value_at(T)


def verifier(lord, position_at, event_class):
    check = chk.P1Check(position_at, dignity_rows=DIG, orb_rows=COMB, naisargika_rows=NAIS)
    return check.bind(ROWS, event_class).evaluate({"agent": lord.lower()}, T)


def assert_cell(lord, position_at, rung, nature, event_class, why=""):
    side, value, _tag = owner_cell(nature, rung)
    src, channel, val = builder(lord, position_at, event_class)
    assert (channel, val) == (expected_channel(side, event_class), pytest.approx(value)), (why, "builder", lord, rung, nature)
    ev = verifier(lord, position_at, event_class)
    assert (ev.rung, ev.nature, ev.side, ev.value) == (rung, nature, side, pytest.approx(value)), (why, "verifier", lord, rung, nature)


# the owner's golden cases, ANSWERS.md v2.1 §B.2 — (lord, longitude, rung, nature, extra sky)
def lon(sign, degree=15.0):
    return SIGNS.index(sign) * 30.0 + degree


GOLDEN = [
    ("Jupiter", lon("Cancer"), "EX", "benefic", {}), ("Saturn", lon("Libra"), "EX", "malefic", {}),
    ("Sun", lon("Leo", 10), "MT", "malefic", {}), ("Jupiter", lon("Sagittarius", 5), "MT", "benefic", {}),
    ("Sun", lon("Leo", 25), "OWN", "malefic", {}), ("Venus", lon("Taurus"), "OWN", "benefic", {}),
    ("Jupiter", lon("Capricorn"), "DEB", "benefic", {}), ("Sun", lon("Libra"), "DEB", "malefic", {}),
    ("Venus", lon("Virgo"), "DEB", "benefic", {}), ("Mercury", lon("Pisces"), "DEB", "benefic", {}),
    ("Jupiter", lon("Aries"), "FR", "benefic", {}), ("Saturn", lon("Taurus"), "FR", "malefic", {}),
    ("Jupiter", lon("Aquarius"), "NEU", "benefic", {}), ("Mars", lon("Taurus"), "NEU", "malefic", {}),
    ("Jupiter", lon("Gemini"), "INI", "benefic", {}), ("Mars", lon("Virgo"), "INI", "malefic", {}),
    # the asymmetric pairs: the period lord's OWN table decides (Mercury->Jupiter would read neutral; Saturn->Moon would read enemy)
    ("Moon", lon("Capricorn"), "NEU", "benefic", {"sun": lon("Capricorn") - 150.0}),            # waxing: favourable 0.125
    ("Moon", lon("Capricorn"), "NEU", "malefic", {"sun": lon("Capricorn") + 150.0}),            # waning: adverse 0.625
    # EX before MT: the Moon's Taurus and Mercury's Virgo read exaltation throughout
    ("Moon", lon("Taurus", 10), "EX", "benefic", {"sun": lon("Taurus", 10) - 150.0}),
    ("Mercury", lon("Virgo", 18), "EX", "benefic", {}),
    # Mercury joined to a malefic (same sign) takes the malefic column; alone it is benefic
    ("Mercury", lon("Aries"), "NEU", "benefic", {}),
    ("Mercury", lon("Aries"), "NEU", "malefic", {"saturn": lon("Aries", 3)}),
    # COMB: any lord whose L1 state is combust, whatever the sign (Jupiter in its exaltation sign, Saturn in its own)
    ("Jupiter", lon("Cancer", 20), "COMB", "benefic", {"sun": lon("Cancer", 23)}),
    ("Saturn", lon("Capricorn", 20), "COMB", "malefic", {"sun": lon("Capricorn", 23)}),
]


@pytest.mark.parametrize("event_class", [GAIN, ADVERSE])
@pytest.mark.parametrize("lord,longitude,rung,nature,extra", GOLDEN, ids=[f"{g[0]}-{g[2]}-{g[3]}" for g in GOLDEN])
def test_d4_the_owners_golden_cases_hold_in_the_builder_and_in_the_independent_verifier(lord, longitude, rung, nature, extra, event_class):
    """Planted reversion: friendship read from the sign lord's row (Jupiter in Gemini then reads NEU favourable 0.125, Mars in Virgo NEU
    adverse 0.625, the Moon in Capricorn INI adverse 0.75) and debility tested after friendship (Jupiter in Capricorn reads NEU)."""
    position_at = sky(lord, longitude, **extra)
    assert_cell(lord, position_at, rung, nature, event_class, why="golden")


def test_d5_precedence_comb_then_ex_mt_own_deb_then_friendship():
    """The checks run in the owner's order. Jupiter in Capricorn: debility is reached only if it is tested before the sign lord's friendship
    (Saturn is neutral to Jupiter). Planted reversion: DEB moved after FR/NEU/INI."""
    for event_class in (GAIN, ADVERSE):
        assert_cell("Jupiter", sky("Jupiter", lon("Capricorn")), "DEB", "benefic", event_class)
        assert_cell("Jupiter", sky("Jupiter", lon("Cancer", 20), sun=lon("Cancer", 23)), "COMB", "benefic", event_class)   # COMB over EX
    # a combust lord NOT at the orb is an ordinary lord: Jupiter 12 degrees from the Sun (orb 11) is not combust
    assert_cell("Jupiter", sky("Jupiter", lon("Cancer", 20), sun=lon("Cancer", 8)), "EX", "benefic", GAIN)


# ── the whole zodiac against the classical tables ───────────────────────────────────────────────────────────────────
EXALT = dict(zip(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"),
                 ("Aries", "Taurus", "Capricorn", "Virgo", "Cancer", "Pisces", "Libra")))
DEBIL = {g: SIGNS[(SIGNS.index(s) + 6) % 12] for g, s in EXALT.items()}
MT_RANGE = {"Sun": ("Leo", 0, 20), "Moon": ("Taurus", 4, 20), "Mars": ("Aries", 0, 12), "Mercury": ("Virgo", 16, 20),
            "Jupiter": ("Sagittarius", 0, 10), "Venus": ("Libra", 0, 15), "Saturn": ("Aquarius", 0, 20)}
OWN = {"Sun": ("Leo",), "Moon": ("Cancer",), "Mars": ("Aries", "Scorpio"), "Mercury": ("Gemini", "Virgo"),
       "Jupiter": ("Sagittarius", "Pisces"), "Venus": ("Taurus", "Libra"), "Saturn": ("Capricorn", "Aquarius")}
# Bṛhat Jātaka II.16-17 (brihat_jataka:PG69:C1): each planet's own friends and enemies; the rest are neutral
FRIENDS = {"Sun": ("Moon", "Mars", "Jupiter"), "Moon": ("Sun", "Mercury"), "Mars": ("Sun", "Moon", "Jupiter"), "Mercury": ("Sun", "Venus"),
           "Jupiter": ("Sun", "Moon", "Mars"), "Venus": ("Mercury", "Saturn"), "Saturn": ("Mercury", "Venus")}
ENEMIES = {"Sun": ("Venus", "Saturn"), "Moon": (), "Mars": ("Mercury",), "Mercury": ("Moon",), "Jupiter": ("Mercury", "Venus"),
           "Venus": ("Sun", "Moon"), "Saturn": ("Sun", "Moon", "Mars")}


def classical_rung(lord, sign, degree):
    if sign == EXALT[lord]:
        return "EX"
    s, lo, hi = MT_RANGE[lord]
    if sign == s and lo <= degree < hi:
        return "MT"
    if sign in OWN[lord]:
        return "OWN"
    if sign == DEBIL[lord]:
        return "DEB"
    other = SIGN_LORD[sign]
    return "FR" if other in FRIENDS[lord] else "INI" if other in ENEMIES[lord] else "NEU"


DEGREES = (2.0, 9.0, 11.0, 14.0, 17.0, 25.0)


def test_d6_every_classical_lord_in_every_sign_and_degree_equals_the_owners_table_in_both_derivations():
    """The L0 friendship rows the build reads agree with Bṛhat Jātaka for the seven planets (a precondition: ANSWERS §B.2), and for every
    lord x sign x degree — both natures of the Moon (pakṣa) and of Mercury (joined / alone) — the builder's side and value and the
    verifier's (side, value, rung) equal the owner's cell at the rung the classical tables give. Planted reversion: any rung rule changed
    (e.g. mūlatrikoṇa before exaltation, own before mūlatrikoṇa, the friendship columns swapped)."""
    nais = {(r["graha"], r["other_graha"]): r["relation"] for r in NAIS}
    for g in FRIENDS:
        for o in FRIENDS:
            if g != o:
                want = "friend" if o in FRIENDS[g] else "enemy" if o in ENEMIES[g] else "neutral"
                assert nais[(g, o)] == want, ("L0 vs Bṛhat Jātaka", g, o)
    n = 0
    for lord in FRIENDS:
        for sign in SIGNS:
            for degree in DEGREES:
                rung = classical_rung(lord, sign, degree)
                longitude = lon(sign, degree)
                variants = [("benefic" if lord in ("Jupiter", "Venus") else "malefic", {})]
                if lord == "Moon":
                    variants = [("benefic", {"sun": longitude - 150.0}), ("malefic", {"sun": longitude + 150.0})]
                if lord == "Mercury":
                    variants = [("benefic", {}), ("malefic", {"saturn": (SIGNS.index(sign) * 30.0 + 1.0)})]
                for nature, extra in variants:
                    for event_class in (GAIN, ADVERSE):
                        assert_cell(lord, sky(lord, longitude, **extra), rung, nature, event_class, why=f"{lord} {sign} {degree}")
                        n += 1
    assert n == 7 * 12 * 6 * 2 + 2 * 12 * 6 * 2        # the Moon and Mercury carry two natures each


# ── the nodes ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_d7_nodes_a_reserved_sign_is_unnumbered_a_classified_one_takes_the_malefic_column_and_combustion_is_na():
    """Rāhu 10 degrees into Gemini (the verse's mūlatrikoṇa, absent from L0) is unclassified with its reason in both derivations; in Libra
    (Venus is Rāhu's friend in L0) it is a malefic FR, adverse 0.5; in Taurus it is EX, favourable 1.0. Planted reversion: classify the
    reserved sign by friendship."""
    reserved = sky("Rahu", lon("Gemini", 10))
    _src, channel, value = builder("Rahu", reserved, GAIN)
    assert channel is None and value is None
    assert _src["agent_nature"].unknown_reason(T) == "node_dignity_unclassified"
    ev = verifier("Rahu", reserved, GAIN)
    assert isinstance(ev, chk.P1Unknown) and ev.reason == "node_dignity_unclassified"
    assert_cell("Rahu", sky("Rahu", lon("Libra", 10)), "FR", "malefic", GAIN)
    assert_cell("Rahu", sky("Rahu", lon("Taurus", 10)), "EX", "malefic", ADVERSE)
    assert_cell("Ketu", sky("Ketu", lon("Taurus", 10)), "DEB", "malefic", ADVERSE)
    # combustion: the Sun and the nodes are DECLARED not applicable (`na`), never a 1.0 — and a combustible lord is the neutral element
    for node in ("Rahu", "Ketu", "Sun"):
        assert builder(node, sky(node, lon("Libra", 10)), GAIN)[0]["combustion"].not_applicable is True
    assert builder("Jupiter", sky("Jupiter", lon("Cancer")), GAIN)[0]["combustion"].value_at(T) == 1.0


# ── a whole window ──────────────────────────────────────────────────────────────────────────────────────────────────
def _jupiter_world():
    """Jupiter crosses from Gemini (the inimical sign of Mercury: INI, benefic, adverse 0.75) into Cancer (its exaltation: favourable 1.0)
    on day 5, at 0.2 degrees a day; the Sun is far. A gain class: adverse feeds evidence AGAINST, favourable evidence FOR."""
    start = lon("Gemini", 29.0)

    def position_at(body, t):
        days = (t - _d(0)).total_seconds() / 86400.0
        body = body.title()                  # the builder probes Title-case names, the independent verifier lower-case
        return {"Jupiter": start + 0.2 * days, "Sun": (start + 150.0) % 360.0 + 0.0 * days}.get(body, (start + 100.0 + 7.0 * (len(body) % 5)) % 360.0)
    return position_at


def test_d8_builder_and_independent_verifier_reproduce_one_window_drawn_from_the_registry_rows():
    """The side flips at the sign ingress (day 5); the peak is that instant with the exaltation value in the for-channel; the verifier,
    handed only the stored window and its own sky + L0 reads, reproduces it. Planted reversion: the verifier's table read from the wrong cell
    (the Cancer value is then not 1.0 and the numbers are refused)."""
    position_at = _jupiter_world()
    ops = P.P1Operands(l0(), position_at, form_b=MAPPING)
    rec = ops.attach(_rec("jup", path="P1", agent="jupiter", root="R-jup", supports=((0, 10),), state_boundaries=None,
                          state_boundaries_complete=False, period_anchor_lord="jupiter"),
                     complete=True, stations=None, event_class=GAIN)
    (draft,), _ = _draft([rec], lambda p, v: ROWS, cls=GAIN)
    assert draft.unqualified_reason is None, draft.unqualified_reason
    assert abs((draft.peak_instant - _d(5)).total_seconds()) <= 1.0
    assert draft.evidence_for == pytest.approx(1.0)
    conn = _Conn([_stored(draft)], [(rec.record_id, rec.root_id, "residence", "sign_span", "jupiter", None, *rec.supports[0])],
                 [("w", rec.record_id)])
    check = chk.P1Check(position_at, dignity_rows=DIG, orb_rows=COMB, naisargika_rows=NAIS)
    report = wv.verify_window_semantics(conn, factor_rows=ROWS, policy=wv.POLICY_VERSION, p1_check=check, dynamic_enabled=True, chart_id="c", generation="g",
                                        event_class=GAIN, path_id="P1", rule_version="1.3.0")
    assert report["numeric_reproduced"] == 1 and report["status"] == "VERIFIED", report


# ── the writer follows the registry ─────────────────────────────────────────────────────────────────────────────────
def test_d9_the_l0_tables_are_consumed_iff_a_bound_p1_version_declares_the_table(monkeypatch):
    """Planted reversion: `_p1_form_b_bound` always False — a build that numbers P1 would then not bind the three L0 tables into its vector."""
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    assets = {"bg_dignity_reference", "bg_combustion_orbs", "bg_graha_naisargika_friendship"}
    assert writer._p1_form_b_bound() is False and writer._l0_consumed() == ()
    monkeypatch.setattr(rr, "BOUND_PATH_REFS", tuple(rr.BOUND_PATH_REFS) + (("P1", "1.3.0"),))
    assert writer._p1_form_b_bound() is True and set(writer._l0_consumed()) == assets


class _Persisted:
    """The two statements `bound_factor_rows` issues, answered with what the encoder would have persisted."""

    def __init__(self, refs, skip_mapping=False):
        self.refs, self.skip_mapping = refs, skip_mapping
        self.declared = {(r["factor_id"], r["rule_version"]): r for r in rr.factor_rows()}

    def execute(self, sql, params=()):
        class R:
            def __init__(self, rows):
                self.rows = rows

            def fetchall(self):
                return self.rows

            def fetchone(self):
                return self.rows[0] if self.rows else None
        if "ka_gochara_rule_path_soft_factor" in sql:
            return R([{"factor_id": f, "factor_rule_version": v} for f, v in self.refs])
        d = self.declared[tuple(params)]
        return R([{"operand_selector": d["operand_selector"], "null_state": d["null_state"], "function": d["function"],
                   "direction": d["direction"], "category_mapping": None if self.skip_mapping else d["category_mapping"]}])


def test_d9_the_persisted_rows_are_read_back_with_the_authored_table_and_the_1_0_0_anchor_stays_private(monkeypatch):
    """The 1.0.0 dignity row's ordering anchor rides in `category_mapping` (E5) but is not a value table: it is not surfaced, so a 1.0.0
    grain reads exactly what it read. A 1.3.0 row surfaces its authored table, and a stored row that lost it diverges loudly.
    Planted reversion: `bound_factor_rows` drops `category_mapping` (the verifier and the sweep would then see no table)."""
    forms = tuple((f, "1.3.0") for f in ("dignity_of_transit_sign", "combustion", "agent_nature"))
    monkeypatch.setattr(rr, "BOUND_FACTOR_REFS", tuple(rr.BOUND_FACTOR_REFS) + forms)
    old = rr.RuleRegistryStore(_Persisted([("dignity_of_transit_sign", "1.0.0"), ("combustion", "1.0.0")]))
    assert all("category_mapping" not in r for r in old.bound_factor_rows("P1", "1.0.0"))
    new = rr.RuleRegistryStore(_Persisted(list(forms))).bound_factor_rows("P1", "1.3.0")
    assert {r["factor_id"]: r["category_mapping"] for r in new} == {f: reg.FACTORS[(f, "1.3.0")]["category_mapping"] for f, _v in forms}
    assert P.form_b_mapping(new).side_and_value("malefic", "NEU") == (A, 0.625)
    with pytest.raises(rr.RegistryDivergenceError):
        rr.RuleRegistryStore(_Persisted(list(forms), skip_mapping=True)).bound_factor_rows("P1", "1.3.0")


def test_d3_the_form_b_side_is_class_relative_so_the_store_must_hand_over_the_event_class():
    """A Form B source built without the grain's event class is refused by name, never given a default polarity."""
    ops = P.P1Operands(l0(), sky("Jupiter", lon("Cancer")), form_b=MAPPING)
    with pytest.raises(p1.StrictInputError) as e:
        ops.sources_for("Jupiter", complete=True)
    assert e.value.reason == "event_class_missing"
    with pytest.raises(ValueError):
        P.P1Operands(l0(), sky("Jupiter", lon("Cancer")), form_b=MAPPING, rules={"dignity_of_transit_sign": lambda s: 1.0})
