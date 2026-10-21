"""SR-OD1 P1c — the verifier-side, independent derivation of the P1 (period-lord strength) operands.

The oracle for every VALUE here is the owner-confirmed doctrine (OWNER-DOCTRINE-CONFIRMED-20261021, P1-MAPPING-DECISION Form B):
`ANSWERS.md` v2.1 §B.2 (the effective rung, its golden cases), §B.3 (the Form B side-and-value table), §B.5 (nodes), with the
classical sources it cites (Phaladīpikā XX.30/XX.37, Bṛhat Jātaka II.16-17 and XX.11, BPHS 3.11 / 3.55, UK PG28:C1). The L0 reference
rows are the seed of migration 250 — parsed or transcribed from it, not computed by the code under test. No test here re-implements a
rule; each reads what `p1_operands_check` derives from an ANALYTIC sky (linear motion, so every crossing instant is known in closed
form) and compares it with the doctrine's answer. No database, no personal data.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  K1 exaltation outranks mūlatrikoṇa inside one sign (B.2: EX › MT › OWN)             (revert: test MT first, as L1's classifier does)
  K2 the mūlatrikoṇa range is L0's, half-open [from, to)                              (revert: `to` inclusive)
  K3 debility is tested before the sign-lord's friendship (B.2 step 6)                 (revert: friendship first)
  K4 friendship is the PERIOD LORD's own row towards the sign lord (BJ II.16-17, PG69:C1) (revert: swap the two columns)
  K6 nodes: exaltation / debility from L0; the verse's mūlatrikoṇa / own signs are undetermined, never guessed (B.5)  (revert: friendship)
  K7 combustion: the L0 outer orb for a direct graha; the Sun and the nodes are never combust (L1 M-19)  (revert: deep orb / nodes combustible)
  K8 the retrograde flag comes from the sky: retrograde Mercury/Venus use the tighter orb (L1 M-19)    (revert: always direct)
  K9 the Moon's pakṣa: waxing while 0-180° ahead of the Sun (BPHS 3.11)                (revert: elongation reversed)
  K10 Mercury is malefic iff in the SAME SIGN as a malefic (Q4 x), not within some degrees   (revert: a degree orb)
  K11 Rāhu and Ketu are malefic companions of Mercury and malefic lords (Q4 a)          (revert: nodes dropped from the malefic list)
  B1 the dignity change instants: sign ingress AND the mūlatrikoṇa degree edge          (revert: sign edges only)
  B2 the combustion change instants are the orb entry and exit                         (revert: deep-orb edges)
  B3 the Moon's pakṣa flips at 0° and 180° elongation                                  (revert: 180° only)
  B4 Mercury's company changes when ANY malefic crosses a sign edge                    (revert: Mercury's own edges only)
  V1 Form B: the dignity rung's side overrides the nature's default (B.3)              (revert: the side is the nature's)
  V2 combustion overrides every rung — adverse 1.0 (B.2 step 1, XX.30 tail)             (revert: rung before combustion)
  V3 an unreadable value table is refused by name, never defaulted                     (revert: a missing cell defaults to neutral)
  V4 maitrī is retired from P1 (Q7 b): no derivation exists                            (revert: a mapped maitrī row becomes a step factor)
  V5 L0 is read by this module's own SQL, by column name                               (revert: columns read in the wrong order)
  W1 the verifier cuts its pieces at the DERIVED change instants (builder-independent) (revert: boundaries ignored)
  W2 an undeterminable instant blanks the window by the named reason, one count per piece   (revert: unknown pieces skipped)
  W3 a declared value table with no derivation supplied is never accepted as a number  (revert: treated as a constant)
  W4 a step-valued window follows the dynamic switch like a function-valued one         (revert: the switch ignored)
  W5 the builder's W0 hooks and the verifier agree on one world (differential, no reversion)
  W6 independence: no import from the builder modules                                  (revert: an import of window_sweep)
  W7 nothing moves for factor rows without a value table                               (revert: karaka_agent counts)
  W8 real Swiss sky: the derived change instants equal an independent dense scan (differential, no reversion)
  W9 real Swiss sky: the rung equals L1's own classifier everywhere except the two owner-ruled EX › MT cells (differential)
"""
from __future__ import annotations

import ast
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import p1_operands_check as p1c
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_kernel.p1_operands_check import P1Check, P1Unknown
from services.gochara_kernel.window_sweep import OperandSource
from services.gochara_rules import p1_inputs

from .test_a53_window_sweep import _rec
from .test_od1_w0_interface import GRAIN, _Conn, _Rows

UTC = timezone.utc
T0 = datetime(2010, 1, 1, tzinfo=UTC)
SIGNS = p1_inputs.SIGNS
MIGRATION = Path(__file__).resolve().parents[5] / "platform" / "migrations" / "250_bg_dignity_reference.sql"


def _d(days: float) -> datetime:
    return T0 + timedelta(days=days)


def _lon(sign: str, deg: float = 15.0) -> float:
    return SIGNS.index(sign) * 30.0 + deg


# ── L0: the seed of migration 250 ────────────────────────────────────────────────────────────────────────────────────
def _dig(graha, ex, deb, mt, mt_from, mt_to, own):
    return {"graha": graha, "exaltation_sign": ex, "debilitation_sign": deb, "moolatrikona_sign": mt,
            "moolatrikona_from": mt_from, "moolatrikona_to": mt_to, "own_signs": own}


DIGNITY_ROWS = [
    _dig("Sun", "Aries", "Libra", "Leo", 0, 20, ["Leo"]),
    _dig("Moon", "Taurus", "Scorpio", "Taurus", 4, 30, ["Cancer"]),
    _dig("Mars", "Capricorn", "Cancer", "Aries", 0, 12, ["Aries", "Scorpio"]),
    _dig("Mercury", "Virgo", "Pisces", "Virgo", 16, 20, ["Gemini", "Virgo"]),
    _dig("Jupiter", "Cancer", "Capricorn", "Sagittarius", 0, 10, ["Sagittarius", "Pisces"]),
    _dig("Venus", "Pisces", "Virgo", "Libra", 0, 15, ["Taurus", "Libra"]),
    _dig("Saturn", "Libra", "Aries", "Aquarius", 0, 20, ["Capricorn", "Aquarius"]),
    _dig("Rahu", "Taurus", "Scorpio", None, None, None, []),
    _dig("Ketu", "Scorpio", "Taurus", None, None, None, []),
]
ORB_ROWS = [{"graha": g, "orb_degrees": o, "deep_orb_degrees": d} for g, o, d in (
    ("Moon", 12, 10), ("Mars", 17, 15), ("Mercury", 14, 12), ("Jupiter", 11, 9), ("Venus", 10, 8), ("Saturn", 15, 12),
    ("Rahu", 9, 7), ("Ketu", 9, 7))]


def _naisargika_from_migration() -> list[dict]:
    text = MIGRATION.read_text(encoding="utf-8")
    start = text.index("INSERT INTO bg_graha_naisargika_friendship")
    section = text[start:text.index("bg_combustion_orbs", start)]
    rows = [{"graha": g, "other_graha": o, "relation": r} for g, o, r in
            re.findall(r"\('(\w+)',\s*'(\w+)',\s*'(friend|neutral|enemy)'", section)]
    assert len(rows) == 72, len(rows)
    return rows


NAIS_ROWS = _naisargika_from_migration()


# ── the Form B table of ANSWERS.md §B.3 (owner-confirmed), as the factor rows' `category_mapping` ─────────────────────
def _c(side, value):
    return {"side": side, "value": value}


FAV, ADV = "favourable", "adverse"
FORM_B = {            # rung: (benefic lord, malefic lord)
    "EX": (_c(FAV, 1.0), _c(FAV, 1.0)), "MT": (_c(FAV, 0.75), _c(FAV, 0.75)), "OWN": (_c(FAV, 0.5), _c(FAV, 0.5)),
    "FR": (_c(FAV, 0.25), _c(ADV, 0.5)), "NEU": (_c(FAV, 0.125), _c(ADV, 0.625)), "INI": (_c(ADV, 0.75), _c(ADV, 0.75)),
    "DEB": (_c(ADV, 1.0), _c(ADV, 1.0))}
NATURE_MAP = {"benefic": _c(FAV, 1.0), "malefic": _c(ADV, 1.0)}
DIGNITY_MAP = {f"{n}/{r}": cells[i] for r, cells in FORM_B.items() for i, n in enumerate(("benefic", "malefic"))}
COMB_MAP = {"combust": _c(ADV, 1.0), "not_combust": {"value": 1.0}}


def _row(fid, mapping, **kw):
    return {"factor_id": fid, "rule_version": "9.0.0", "null_state": "unqualified", "direction": "doctrine-ordered",
            "function": "step", "range": [0.0, 1.0], "units": "unitless", "category_mapping": mapping, **kw}


def p1_rows(path="P1", version="9.0.0"):
    return [_row("dignity_of_transit_sign", DIGNITY_MAP), _row("combustion", COMB_MAP), _row("agent_nature", NATURE_MAP)]


# ── an analytic sky: linear motion, so every crossing has a closed form ──────────────────────────────────────────────
_DEFAULT = {"sun": 190.0, "moon": 75.0, "mars": 300.0, "mercury": 340.0, "jupiter": 100.0, "venus": 130.0, "saturn": 250.0,
            "rahu": 80.0, "ketu": 260.0}


class Sky:
    def __init__(self, **motion):
        self.motion = {b: (v, 0.0) if isinstance(v, (int, float)) else v for b, v in {**_DEFAULT, **motion}.items()}

    def __call__(self, body, t):
        lon0, v = self.motion[body]
        return (lon0 + v * (t - T0).total_seconds() / 86400.0) % 360.0


def _check(sky=None, **kw):
    return P1Check(sky or Sky(), dignity_rows=kw.get("dignity_rows", DIGNITY_ROWS), orb_rows=kw.get("orb_rows", ORB_ROWS),
                   naisargika_rows=kw.get("nais_rows", NAIS_ROWS))


def _lord_sky(graha, sign, deg=15.0, **more):
    """`graha` fixed at sign/deg with the Sun a trine away (so combustion plays no part), the rest as `Sky` defaults."""
    lon = _lon(sign, deg)
    motion = {graha.lower(): lon, **more}
    if graha == "Rahu":
        motion["ketu"] = (lon + 180.0) % 360.0
    if graha == "Ketu":
        motion["rahu"] = (lon + 180.0) % 360.0
    if graha != "Sun":
        motion.setdefault("sun", (lon + 120.0) % 360.0)
    return Sky(**motion)


def _rung(graha, sign, deg=15.0, **kw):
    return _check(_lord_sky(graha, sign, deg), **kw).rung_at(graha, T0)


# ══ K1–K4, K6: the effective rung (ANSWERS.md §B.2 golden cases) ═════════════════════════════════════════════════════════

@pytest.mark.parametrize("graha, sign, deg, want", [
    # B.2 "golden cases, one per rung" (lagna-independent; friendship read from the period lord's own table)
    ("Jupiter", "Cancer", 10, "EX"), ("Saturn", "Libra", 10, "EX"),
    ("Sun", "Leo", 10, "MT"), ("Jupiter", "Sagittarius", 5, "MT"),
    ("Sun", "Leo", 25, "OWN"), ("Venus", "Taurus", 10, "OWN"),
    ("Jupiter", "Capricorn", 10, "DEB"), ("Sun", "Libra", 10, "DEB"), ("Venus", "Virgo", 10, "DEB"), ("Mercury", "Pisces", 10, "DEB"),
    ("Jupiter", "Aries", 10, "FR"), ("Saturn", "Taurus", 10, "FR"),
    ("Jupiter", "Aquarius", 10, "NEU"), ("Mars", "Taurus", 10, "NEU"),
    ("Jupiter", "Gemini", 10, "INI"), ("Mars", "Virgo", 10, "INI"),
])
def test_k_the_rung_ladder_follows_the_b2_golden_cases(graha, sign, deg, want):
    assert _rung(graha, sign, deg) == want


@pytest.mark.parametrize("graha, sign, deg", [("Moon", "Taurus", 10), ("Mercury", "Virgo", 18)])
def test_k1_exaltation_outranks_mulatrikona_inside_one_sign(graha, sign, deg):
    """B.2: "Precedence inside one sign is EX › MT › OWN (so the Moon's Taurus and Mercury's Virgo read as exaltation
    throughout)". L0 holds Moon MT = Taurus 4-30 and Mercury MT = Virgo 16-20. Planted reversion: the MT test before EX
    (L1's `dignity_d1_from_sign` order) ⇒ both read MT."""
    assert _rung(graha, sign, deg) == "EX"


def test_k2_the_mulatrikona_range_is_l0s_half_open():
    """Sun's MT is Leo 0° ≤ λ < 20° (L0 `moolatrikona_from/to`; Uttara Kālāmṛta PG28:C1 "Sun 0° to 20°"); at 20° it is OWN.
    Planted reversion: `to` inclusive ⇒ 20.0 reads MT."""
    assert (_rung("Sun", "Leo", 0.0), _rung("Sun", "Leo", 19.999999), _rung("Sun", "Leo", 20.0)) == ("MT", "MT", "OWN")


def test_k3_debility_is_tested_before_the_sign_lords_friendship():
    """B.2 step 6 / golden: "Jupiter in Capricorn → debilitated, adverse 1.00 (Saturn is neutral to Jupiter, but DEB is tested
    before friendship)"; "Sun in Libra → adverse 1.00 (not INI 0.75)". Planted reversion: friendship first ⇒ NEU / INI."""
    assert _rung("Jupiter", "Capricorn") == "DEB" and _rung("Sun", "Libra") == "DEB"


@pytest.mark.parametrize("graha, sign, want", [
    ("Jupiter", "Gemini", "INI"),    # Jupiter→Mercury is enemy (Mercury→Jupiter would read neutral)   — BJ II.16-17
    ("Mars", "Virgo", "INI"),        # Mars→Mercury is enemy (Mercury→Mars neutral)
    ("Moon", "Capricorn", "NEU"),    # Moon→Saturn is neutral (Saturn→Moon would read enemy)
])
def test_k4_friendship_is_the_period_lords_own_row_toward_the_sign_lord(graha, sign, want):
    """B.2 step 6: "Lookup pinned with the period lord as the first column … a planted-reversion test on an asymmetric pair".
    Planted reversion: the two columns swapped ⇒ each of these reads the other relation."""
    assert _rung(graha, sign) == want


@pytest.mark.parametrize("graha, sign, want", [
    ("Rahu", "Taurus", "EX"), ("Rahu", "Scorpio", "DEB"), ("Ketu", "Scorpio", "EX"), ("Ketu", "Taurus", "DEB"),
])
def test_k6_nodes_take_exaltation_and_debility_from_l0(graha, sign, want):
    assert _rung(graha, sign) == want


@pytest.mark.parametrize("graha, sign", [("Rahu", "Gemini"), ("Rahu", "Aquarius"), ("Ketu", "Sagittarius")])
def test_k6_a_node_in_the_signs_the_verse_reserves_is_undetermined_not_guessed(graha, sign):
    """B.5 (BPHS 47.34-39½, bphs:PG573:C2-PG574:C1): the nodes' mūlatrikoṇa / own signs are Gemini and Aquarius (Rāhu), Sagittarius
    (Ketu); L0 holds neither, so the rung is `node_dignity_unclassified`. Planted reversion: classify by friendship ⇒ a rung."""
    got = _rung(graha, sign)
    assert got == P1Unknown(p1c.NODE_DIGNITY_UNCLASSIFIED)


def test_k6_the_reservation_lifts_for_a_sign_l0_comes_to_hold():
    rows = [r if r["graha"] != "Rahu" else {**r, "own_signs": ["Aquarius"]} for r in DIGNITY_ROWS]
    assert _rung("Rahu", "Aquarius", dignity_rows=rows) == "OWN"
    assert _rung("Rahu", "Gemini", dignity_rows=rows) == P1Unknown(p1c.NODE_DIGNITY_UNCLASSIFIED)


def test_k6_a_node_elsewhere_reads_the_nodes_own_friendship_row():
    """B.5: "Node FR/NEU/INI rungs: L0 `bg_graha_naisargika_friendship` governs, read with graha = the node". Rāhu in Aries
    (lord Mars): L0 Rahu→Mars is 'neutral'."""
    assert next(r for r in NAIS_ROWS if (r["graha"], r["other_graha"]) == ("Rahu", "Mars"))["relation"] == "neutral"
    assert _rung("Rahu", "Aries") == "NEU"


# ══ K7–K11: combustion and nature ════════════════════════════════════════════════════════════════════════════════════════

def _comb_sky(graha, arc, *, speed=0.0, sun_speed=0.0):
    sun = 100.0
    return Sky(sun=(sun, sun_speed), **{graha.lower(): (sun + arc, speed)})


def test_k7_combustion_is_the_l0_outer_orb_for_a_direct_graha():
    """Jupiter's L0 orb is 11° (deep 9°; BPHS translator's table / `bg_combustion_orbs`): combust inside 11°, not outside.
    Planted reversion: the deep orb ⇒ 10.9° reads not combust."""
    inside, outside = _check(_comb_sky("Jupiter", 10.9)), _check(_comb_sky("Jupiter", 11.1))
    assert inside.combustion_at("Jupiter", T0)["is_combust"] is True
    assert outside.combustion_at("Jupiter", T0)["is_combust"] is False


@pytest.mark.parametrize("graha", ["Sun", "Rahu", "Ketu"])
def test_k7_the_sun_and_the_nodes_are_never_combust_although_l0_carries_node_rows(graha):
    """L1 M-19 / BPHS 7.28-29 translator's note (bphs:PG99:C1): "Rahu and Ketu should not be treated as combust … they are only
    mathematical points". `bg_combustion_orbs` still holds Rahu / Ketu rows (9°/7°). Planted reversion: those rows are used."""
    sky = Sky(sun=100.0, rahu=102.0, ketu=282.0)
    assert any(r["graha"] == "Rahu" for r in ORB_ROWS)
    assert _check(sky).combustion_at(graha, T0)["applicable"] is False


def test_k8_the_retrograde_flag_comes_from_the_sky():
    """L1 M-19 ("Mercury 12°R, Venus 8°R"): retrograde Mercury uses the tighter orb (12°), direct 14°. At 13° from the Sun the
    same arc is combust direct and not combust retrograde. Planted reversion: the flag is always False."""
    direct = _check(_comb_sky("Mercury", 13.0, speed=+1.0)).combustion_at("Mercury", T0)
    retro = _check(_comb_sky("Mercury", 13.0, speed=-1.0)).combustion_at("Mercury", T0)
    assert (direct["is_combust"], retro["is_combust"]) == (True, False)


@pytest.mark.parametrize("elongation, want", [(10.0, "benefic"), (90.0, "benefic"), (179.9, "benefic"),
                                              (180.1, "malefic"), (270.0, "malefic"), (359.9, "malefic")])
def test_k9_the_moon_is_benefic_while_waxing_malefic_while_waning(elongation, want):
    """BPHS 3.11 (bphs:PG26:C1): "decreasing Moon … malefic". Waxing = the Moon 0-180° ahead of the Sun. Planted reversion:
    the elongation taken the other way round ⇒ every row flips."""
    sky = Sky(sun=100.0, moon=100.0 + elongation)
    assert _check(sky).nature_at("Moon", T0) == want


@pytest.mark.parametrize("companion, merc_deg, where, want", [
    ("jupiter", 19.5, _lon("Aries", 20), "benefic"),       # Jupiter is a benefic
    ("mars", 19.5, _lon("Aries", 20), "malefic"),
    ("saturn", 19.5, _lon("Aries", 20), "malefic"),
    ("sun", 19.5, _lon("Aries", 20), "malefic"),
    ("mars", 29.5, _lon("Taurus", 0.2), "benefic"),        # 0.7° from Mercury but in the NEXT sign: not joined (Q4 x)
    ("mars", 0.3, _lon("Pisces", 29.9), "benefic"),        # 0.4° away on the other side: not joined either
])
def test_k10_mercury_is_malefic_iff_in_the_same_sign_as_a_malefic(companion, merc_deg, where, want):
    """Q4 x ("joined" = same sign; BPHS 3.56 reckons by whole houses, no served text gives a degree orb). Planted reversion: a
    degree orb (|Δλ| < 10°) ⇒ the two next-sign rows read malefic."""
    sky = Sky(mercury=_lon("Aries", merc_deg), **{companion: where})
    assert _check(sky).nature_at("Mercury", T0) == want


@pytest.mark.parametrize("node", ["rahu", "ketu"])
def test_k11_a_node_is_a_malefic_companion(node):
    """Q4 a / BPHS 3.11: "Rahu and Ketu … are malefics"; Mercury "is a malefic if he joins a malefic". Planted reversion: the
    nodes dropped from the malefic list (Q4 b)."""
    sky = Sky(mercury=_lon("Aries", 19.5), **{node: _lon("Aries", 5.0), "rahu" if node == "ketu" else "ketu": _lon("Libra", 5.0)})
    assert _check(sky).nature_at("Mercury", T0) == "malefic"


def test_k10_a_waning_moon_in_the_sign_makes_mercury_malefic_a_waxing_one_does_not():
    sun, merc = _lon("Gemini", 3.0), _lon("Aries", 19.5)
    waning = Sky(sun=sun, mercury=merc, moon=_lon("Aries", 25.0))          # Moon 55° BEHIND the Sun's… elongation = 262° ⇒ waning
    waxing = Sky(sun=_lon("Pisces", 10.0), mercury=merc, moon=_lon("Aries", 25.0))   # elongation 45° ⇒ waxing
    assert _check(waning).nature_at("Mercury", T0) == "malefic"
    assert _check(waxing).nature_at("Mercury", T0) == "benefic"


# ══ B1–B4: the change instants, against closed forms ═════════════════════════════════════════════════════════════════════

def _near(found, expected_days, tol_s=p1c.PEAK_TOLERANCE_SECONDS):
    assert len(found) == len(expected_days), (found, expected_days)
    for got, want in zip(found, expected_days):
        assert abs((got - _d(want)).total_seconds()) <= tol_s, (got, _d(want))


def test_b1_dignity_changes_at_sign_ingress_and_at_the_mulatrikona_degree():
    """The Sun at 1°/day enters Leo (120°) on day 20 from 100°, reaches Leo 20° (MT → OWN) on day 40, leaves Leo (150°) on day 50.
    L0 Sun MT = Leo 0-20. Planted reversion: sign edges only ⇒ the day-40 instant is missing."""
    chk = _check(Sky(sun=(100.0, 1.0)))
    _near(chk.dignity_boundaries("Sun", _d(0), _d(60)), [20.0, 40.0, 50.0])


def test_b2_combustion_changes_at_orb_entry_and_exit():
    """Jupiter (orb 11°) sits 20° ahead of the Sun and the Sun gains 1°/day: the arc is 11° on day 9, and Jupiter leaves the
    orb on the far side on day 31. Planted reversion: the deep-orb (9°) edges ⇒ days 11 and 29."""
    chk = _check(Sky(sun=(100.0, 1.0), jupiter=(120.0, 0.0)))
    _near(chk.combustion_boundaries("Jupiter", _d(0), _d(60)), [9.0, 31.0])


def test_b3_the_moons_paksa_flips_at_zero_and_one_eighty_degrees_elongation():
    """Sun 1°/day, Moon 13°/day from 90° ahead: relative 12°/day. Elongation reaches 180° on day 7.5 and 360° (=0°) on day 22.5.
    Planted reversion: only 180°."""
    chk = _check(Sky(sun=(100.0, 1.0), moon=(190.0, 13.0)))
    _near(chk.nature_boundaries("Moon", _d(0), _d(25)), [7.5, 22.5])


def test_b4_mercurys_company_changes_when_any_malefic_crosses_a_sign_edge():
    """Mercury sits still in Aries 19.5°; Mars at 0.5°/day enters Aries from Pisces 29° (day 2) and leaves it 30 days later…
    (Aries is 30° wide ⇒ 60 days). The company changes on day 2 and day 62. Planted reversion: only Mercury's own edges."""
    chk = _check(Sky(mercury=_lon("Aries", 19.5), mars=(_lon("Pisces", 29.0), 0.5)))
    _near(chk.nature_boundaries("Mercury", _d(0), _d(70)), [2.0, 62.0])


# ══ V1–V5: the value table and the L0 reads ══════════════════════════════════════════════════════════════════════════════

def _bound(sky, event_class="marriage"):
    return _check(sky).bind(p1_rows(), event_class)


def _eval(graha, sky, **kw):
    return _bound(sky, **kw).evaluate({"agent": graha.lower()}, T0)


@pytest.mark.parametrize("graha, sign, deg, side, value", [
    ("Jupiter", "Cancer", 10, FAV, 1.0), ("Saturn", "Libra", 10, FAV, 1.0), ("Sun", "Leo", 10, FAV, 0.75),
    ("Sun", "Leo", 25, FAV, 0.5), ("Saturn", "Taurus", 10, ADV, 0.5), ("Mars", "Taurus", 10, ADV, 0.625),
    ("Jupiter", "Aquarius", 10, FAV, 0.125), ("Jupiter", "Gemini", 10, ADV, 0.75), ("Mars", "Virgo", 10, ADV, 0.75),
    ("Jupiter", "Capricorn", 10, ADV, 1.0), ("Sun", "Libra", 10, ADV, 1.0),
])
def test_v1_form_b_the_rung_decides_the_side_and_the_value(graha, sign, deg, side, value):
    """ANSWERS.md §B.2 golden cases × §B.3 Form B: a benefic lord in debility / an inimical sign turns ADVERSE, a malefic lord in
    exaltation / mūlatrikoṇa / own sign is FAVOURABLE (Phaladīpikā XX.37, XX.34; Saravali 25-28). Planted reversion: the side is
    the nature's default ⇒ Jupiter in Capricorn reads favourable."""
    e = _eval(graha, _lord_sky(graha, sign, deg))
    assert (e.side, e.value) == (side, value)


def test_v1_the_moons_neutral_rung_follows_its_paksa():
    """B.2 asymmetric golden: Moon in Capricorn (Moon→Saturn neutral): a waxing Moon favourable 0.125, a waning one adverse 0.625."""
    cap = _lon("Capricorn", 10.0)
    waxing = _eval("Moon", Sky(moon=cap, sun=cap - 60.0))             # elongation 60°
    waning = _eval("Moon", Sky(moon=cap, sun=cap + 60.0))             # elongation 300°
    assert (waxing.side, waxing.value) == (FAV, 0.125) and (waning.side, waning.value) == (ADV, 0.625)


def test_v2_combustion_overrides_every_rung():
    """B.2 step 1 / golden "COMB: any lord with L1 state combust → adverse 1.00, whatever the sign" (Phaladīpikā XX.30 tail:
    "When a planet is in combustion … its effect will be similar to that in depression"). Jupiter exalted in Cancer, 5° from the
    Sun. Planted reversion: the rung is tested first ⇒ favourable 1.0."""
    e = _eval("Jupiter", Sky(jupiter=_lon("Cancer", 10.0), sun=_lon("Cancer", 15.0)))
    assert (e.rung, e.side, e.value, e.combust) == ("COMB", ADV, 1.0, True)


def test_v3_an_unreadable_value_table_is_refused_by_name_never_defaulted():
    """A missing cell, a value of 0 (spec §2.3 inv. 3: a modifier never removes a window), a value above 1, a side on the
    not-combust state: each is a named refusal for every P1 row. Planted reversion: a missing cell defaults to 1.0."""
    chk = _check()
    no_cell = {k: v for k, v in DIGNITY_MAP.items() if k != "benefic/DEB"}
    cases = {
        "category_mapping_incomplete": [_row("dignity_of_transit_sign", no_cell), _row("combustion", COMB_MAP), _row("agent_nature", NATURE_MAP)],
        "category_mapping_value_out_of_range": [_row("dignity_of_transit_sign", {**DIGNITY_MAP, "malefic/EX": _c(FAV, 0.0)}),
                                                _row("combustion", COMB_MAP), _row("agent_nature", NATURE_MAP)],
        "category_mapping_cell_invalid": [_row("dignity_of_transit_sign", DIGNITY_MAP),
                                          _row("combustion", {**COMB_MAP, "not_combust": _c(FAV, 1.0)}), _row("agent_nature", NATURE_MAP)],
    }
    for reason, rows in cases.items():
        b = chk.bind(rows, "marriage")
        assert {b.record_problem(f, {"agent": "jupiter"}) for f in p1c.P1_FACTORS} == {reason}, reason
    assert chk.bind(p1_rows(), "marriage").record_problem("agent_nature", {"agent": "jupiter"}) is None


def test_v4_maitri_is_retired_from_p1_so_no_derivation_exists_for_it():
    """Q7 b (P1-MAPPING-DECISION): `maitri_compound` is retired from P1 in the new version. A maitrī row that nevertheless
    declares a table is unqualified by name in the verifier. Planted reversion: it becomes a step factor."""
    row = {"factor_id": "maitri_compound", "rule_version": "9.0.0", "null_state": "unqualified", "category_mapping": {"friend": 0.5}}
    rec = {"agent": "jupiter", "root": "r", "relation": "residence", "kind": "sign_span", "house": None, "supports": []}
    assert wv._row_state(row, rec, False, False, p1=_bound(Sky())) == ("unq", "maitri_compound_retired_not_derivable")


class _ReadConn:
    """Answers the three L0 SELECTs in the column order the SQL names, as tuples (as psycopg returns without dict_row)."""

    def __init__(self, swap_nais=False):
        self.sql = []
        self.swap_nais = swap_nais

    def execute(self, sql, params=()):
        self.sql.append(sql)
        if "bg_dignity_reference" in sql:
            cols = ("graha", "exaltation_sign", "debilitation_sign", "moolatrikona_sign", "moolatrikona_from", "moolatrikona_to", "own_signs")
            return _Rows([tuple(r[c] for c in cols) for r in DIGNITY_ROWS])
        if "bg_combustion_orbs" in sql:
            return _Rows([(r["graha"], r["orb_degrees"], r["deep_orb_degrees"]) for r in ORB_ROWS])
        if "bg_graha_naisargika_friendship" in sql:
            m = re.search(r"SELECT (\w+), (\w+), (\w+) FROM", sql)
            assert m
            return _Rows([tuple(r[c] for c in m.groups()) for r in NAIS_ROWS])
        raise AssertionError(sql)


def test_v5_the_verifier_reads_l0_by_its_own_sql_by_column_name():
    """Jupiter in Gemini is INI only if `graha` is the period lord's column (K4). Planted reversion: the SELECT names
    `other_graha, graha` ⇒ the tuple is zipped against the wrong columns ⇒ the asymmetric pair reads the other relation."""
    conn = _ReadConn()
    chk = P1Check.from_conn(conn, _lord_sky("Jupiter", "Gemini"))
    assert chk.rung_at("Jupiter", T0) == "INI"
    assert {t for s in conn.sql for t in ("bg_dignity_reference", "bg_combustion_orbs", "bg_graha_naisargika_friendship") if t in s} == {
        "bg_dignity_reference", "bg_combustion_orbs", "bg_graha_naisargika_friendship"}


# ══ W1–W5: the verifier, on a fake connection (the W0 harness) ═══════════════════════════════════════════════════════════

CLASS = "marriage"


def _stored(wid, lo, hi, peak, score, ev_for, ev_against, valence, null_states=(), prov=(None, None, None)):
    return (wid, lo, hi, peak, score, ev_for, ev_against, None, list(null_states), valence, *prov)


class _ProvConn(_Conn):
    """`_Conn` whose window table carries the provenance columns, so `unresolved` / `qualification` are compared too."""

    def execute(self, sql, params=()):
        if "pg_attribute" in sql:
            return _Rows([(3,)])
        return super().execute(sql, params)


def _jupiter_world():
    """Jupiter (benefic) at Capricorn 29.5°, +0.1°/day: DEBILITATED (adverse 1.0) until it enters Aquarius on day 5, then
    NEU (favourable 0.125). 'marriage' is a gain class, so only the favourable side feeds evidence_for."""
    sky = Sky(jupiter=(_lon("Capricorn", 29.5), 0.1))
    record = ("r1", "root1", "residence", "sign_span", "jupiter", None, _d(0), _d(10))
    want_valence = wv._expected_valence(CLASS, 0.125, 0.0, "evidence_against_channel_not_evaluated")
    stored = _stored("w", _d(0), _d(10), _d(5), 0.125, 0.125, None, want_valence)
    return sky, _Conn([stored], [record], [("w", "r1")]), stored


def _verify(conn, sky, *, rows=None, p1=True, **kw):
    check = _check(sky) if p1 else None
    return wv.verify_window_semantics(conn, factor_rows=rows or p1_rows(), p1_check=check, dynamic_enabled=True,
                                      policy=wv.POLICY_VERSION, **{**GRAIN, "event_class": CLASS}, **kw)


def test_w1_the_verifier_cuts_its_pieces_at_the_derived_change_instants():
    """The window's peak is the day-5 ingress: before it the lord is adverse (the for-channel is 0), after it favourable 0.125.
    The expected values come from ANSWERS.md §B.3, not from the code. Planted reversion: the verifier ignores the derived change
    instants ⇒ one piece, the peak is day 0 and the stored day-5 peak is refused."""
    sky, conn, _ = _jupiter_world()
    report = _verify(conn, sky)
    assert report["numeric_reproduced"] == 1 and report["status"] == "VERIFIED"


def test_w1_a_stored_peak_at_the_wrong_instant_is_refused():
    sky, _, stored = _jupiter_world()
    wrong = _stored("w", _d(0), _d(10), _d(6), *stored[4:7], stored[9])
    conn = _Conn([wrong], [("r1", "root1", "residence", "sign_span", "jupiter", None, _d(0), _d(10))], [("w", "r1")])
    with pytest.raises(RuntimeError, match="peak"):
        _verify(conn, sky)


def test_w1_a_stored_value_that_is_not_the_tables_is_refused():
    sky, _, stored = _jupiter_world()
    wrong = _stored("w", _d(0), _d(10), _d(5), 0.25, 0.25, None, stored[9])
    conn = _Conn([wrong], [("r1", "root1", "residence", "sign_span", "jupiter", None, _d(0), _d(10))], [("w", "r1")])
    with pytest.raises(RuntimeError, match="score"):
        _verify(conn, sky)


def _rahu_world(stored_blank=True):
    """Rāhu (a malefic) at Taurus 29.5° (EXALTED), +0.1°/day: it enters Gemini on day 5 — a sign the verse reserves for its
    mūlatrikoṇa (B.5), which L0 does not hold: from day 5 the rung is undetermined."""
    sky = Sky(rahu=(_lon("Taurus", 29.5), 0.1), ketu=(_lon("Scorpio", 29.5), 0.1))
    record = ("r1", "root1", "residence", "sign_span", "rahu", None, _d(0), _d(10))
    reason = p1c.NODE_DIGNITY_UNCLASSIFIED
    if stored_blank:
        stored = _stored("w", _d(0), _d(10), None, None, None, None, wv._expected_valence(CLASS, 0.0, 0.0, reason), [],
                         ("evidence_for_per_root_sum", None, {"policy": wv.POLICY_VERSION, "unqualified_reason": reason,
                                                              "unresolved": {reason: 1}, "affected_channels": [], "members": 1,
                                                              "qualified_members": 1}))
    else:
        stored = _stored("w", _d(0), _d(10), _d(0), 1.0, 0.0, None, wv._expected_valence(CLASS, 0.0, 0.0, "evidence_against_channel_not_evaluated"))
    return sky, _ProvConn([stored], [record], [("w", "r1")])


def test_w2_an_undeterminable_instant_blanks_the_window_by_the_named_reason_one_count_per_piece():
    """B.5 / Q4: a node record in a reserved sign is `node_dignity_unclassified`; "an unqualified node record blanks every P1
    window it shares" (the policy table: an unknown portion is never dropped). One piece (day 5-10) is unknown ⇒ unresolved
    {reason: 1}. Planted reversion: unknown pieces are skipped ⇒ the verifier derives a number the blank window does not hold."""
    sky, conn = _rahu_world(stored_blank=True)
    report = _verify(conn, sky)
    assert report["fully_reproduced"] == 1 and report["status"] == "VERIFIED"


def test_w2_a_number_stored_for_that_window_is_refused():
    sky, conn = _rahu_world(stored_blank=False)
    with pytest.raises(RuntimeError, match="node_dignity_unclassified"):
        _verify(conn, sky)


def test_w3_a_declared_value_table_with_no_derivation_supplied_is_never_a_number():
    """The rows declare a `category_mapping`, the caller supplies no `p1_check`: every P1 record is unqualified
    `p1_derivation_not_supplied`, so a stored NUMBER is a disagreement. Planted reversion: the record is a constant 1.0."""
    sky, conn, _ = _jupiter_world()
    with pytest.raises(RuntimeError, match=p1c.MAPPING_NOT_SUPPLIED_REASON):
        _verify(conn, sky, p1=False)


def test_w4_a_step_valued_window_follows_the_dynamic_switch():
    """Like a function-valued member, a step-valued one is blank under `dynamic_objective_solver_guarantee_not_available` while
    the switch is off (the builder's `allow_dynamic`). Planted reversion: the switch is ignored ⇒ a number is derived."""
    sky, conn, _ = _jupiter_world()
    with pytest.raises(RuntimeError, match=wv.DYNAMIC_SWITCH_REASON):
        wv.verify_window_semantics(conn, factor_rows=p1_rows(), p1_check=_check(sky), dynamic_enabled=False,
                                   policy=wv.POLICY_VERSION, **{**GRAIN, "event_class": CLASS})


def test_w5_the_builders_w0_hooks_and_the_verifier_agree_on_one_world():
    """Differential (no reversion): a builder record whose `OperandSource` hooks are fed by the same P1 binding, drafted by
    `window_sweep`, is reproduced by the verifier from the stored row alone."""
    sky, _, _ = _jupiter_world()
    binding = _bound(sky)
    agent = {"agent": "jupiter"}

    def side(t):
        c = binding.channel_at(agent, t)
        return None if isinstance(c, P1Unknown) else (ws.CHANNEL_FOR if c == "evidence_for_occurrence" else ws.CHANNEL_AGAINST)

    def value(t):
        v = binding.value_at(agent, t)
        return None if isinstance(v, P1Unknown) else v
    src = OperandSource(value_at=value, channel_at=side, complete=True, boundaries=lambda lo, hi: binding.channel_boundaries(agent, lo, hi))
    rec = _rec("r1", path="P1", root="root1", agent="jupiter", supports=((0, 10),), operand_sources={"agent_nature": src})
    nature = {"factor_id": "agent_nature", "rule_version": "9.0.0", "null_state": "unqualified", "direction": "doctrine-ordered",
              "function": "step", "range": [0.0, 1.0], "units": "unitless"}       # the same `direction` as the P1 rows
    (draft,), _ = ws.draft_windows(CLASS, [rec], lambda p, v: [nature], allow_dynamic=True)
    assert abs((draft.peak_instant - _d(5)).total_seconds()) <= p1c.PEAK_TOLERANCE_SECONDS and draft.score == pytest.approx(0.125)
    lo, hi = draft.interval
    stored = (_stored("w", lo, hi, draft.peak_instant, draft.score, draft.evidence_for, draft.evidence_against,
                      draft.outcome_valence_for_native, draft.null_states_used))
    conn = _Conn([stored], [("r1", "root1", "residence", "sign_span", "jupiter", None, _d(0), _d(10))], [("w", "r1")])
    assert _verify(conn, sky)["numeric_reproduced"] == 1


# ══ W6–W7: independence and "nothing moves" ══════════════════════════════════════════════════════════════════════════════

BUILDER_MODULES = {"window_sweep", "window_solver", "p1_operands", "record_store", "materialise", "contacts", "arcs", "knots", "substrate"}


def test_w6_the_module_imports_nothing_from_the_builder():
    """Independence (plan §3.3): the derivation is written without the builder's operand sources, crossings or geometry; it may
    use the verifier's own reconstruction device and the shared RULE authorities. Planted reversion: an import of window_sweep."""
    src = (Path(p1c.__file__)).read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[-1])
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            imported.update(a.name.split(".")[-1] for a in node.names)
    assert not imported & BUILDER_MODULES, imported & BUILDER_MODULES
    assert {"contact_reconstruct", "p1_inputs", "nature"} <= imported


def test_w7_only_p1_rows_with_a_value_table_trigger_the_derivation():
    """Today's rows declare none (and `karaka_agent` declares a `category_mapping` of its own that is NOT a P1 factor): nothing is
    derived, so no existing output moves. Planted reversion: any `category_mapping` triggers."""
    plain = [{"factor_id": f, "rule_version": "1.0.0"} for f in p1c.P1_FACTORS]
    assert p1c.needs_p1_check(plain) is False
    assert p1c.needs_p1_check(plain + [{"factor_id": "karaka_agent", "category_mapping": {"karaka": 1.0, "non_karaka": 0.0}}]) is False
    assert p1c.needs_p1_check(p1_rows()) is True


# ══ W8: the real Swiss sky (the pinned corpus) against an independent dense scan ════════════════════════════════════════

def _swiss_position_at():
    ephe = os.environ.get("SE_EPHE_PATH")
    if not ephe or not Path(ephe).is_dir():
        pytest.skip("pinned Swiss corpus (SE_EPHE_PATH) not available")
    from services.gochara_kernel.knots import calc_sidereal_lon
    jd0 = datetime(1970, 1, 1, tzinfo=UTC)

    def position_at(body, t):
        jd = (t - jd0).total_seconds() / 86400.0 + 2440587.5
        return calc_sidereal_lon(body.title(), jd, ephe)[0]
    return position_at


def _dense_changes(state_at, lo, hi, step=timedelta(hours=1)):
    """Independent of the code under test: a plain 1-hour scan, each change bisected to 0.1 s."""
    out, a, sa = [], lo, state_at(lo)
    while a < hi:
        b = min(a + step, hi)
        sb = state_at(b)
        if sb != sa:
            x, y = a, b
            while (y - x).total_seconds() > 0.1:
                m = x + (y - x) / 2
                if state_at(m) == sa:
                    x = m
                else:
                    y = m
            out.append(y)
        a, sa = b, sb
    return out


def test_w8_real_sky_the_derived_change_instants_equal_a_dense_scan():
    """Differential (no reversion): the Moon's pakṣa flips and Mercury's combustion entries/exits over 200 days of the real pinned
    sky equal an independent hourly scan to within the tolerance."""
    pos = _swiss_position_at()
    chk = P1Check(pos, dignity_rows=DIGNITY_ROWS, orb_rows=ORB_ROWS, naisargika_rows=NAIS_ROWS)
    lo, hi = datetime(2011, 3, 1, tzinfo=UTC), datetime(2011, 9, 17, tzinfo=UTC)
    for graha, derived, state in (
            ("Moon", chk.nature_boundaries("Moon", lo, hi), lambda t: chk.nature_at("Moon", t)),
            ("Mercury", chk.combustion_boundaries("Mercury", lo, hi), lambda t: chk.combustion_at("Mercury", t)["is_combust"]),
            ("Jupiter", chk.dignity_boundaries("Jupiter", lo, hi), lambda t: chk.rung_at("Jupiter", t))):
        scan = _dense_changes(state, lo, hi)
        assert len(derived) == len(scan) and scan, (graha, len(derived), len(scan))
        for got, want in zip(derived, scan):
            assert abs((got - want).total_seconds()) <= p1c.PEAK_TOLERANCE_SECONDS + 0.1, (graha, got, want)


def test_w9_real_sky_the_rung_equals_l1s_classifier_except_the_two_owner_ruled_precedence_cells():
    """Differential (no reversion): over 26 years of the real sky, for the seven classical grahas, the rung this module derives
    equals L1's `dignity_d1_from_sign` (via p1_inputs) mapped onto the rungs — except where L1 tests mūlatrikoṇa BEFORE exaltation
    (Moon in Taurus, Mercury in Virgo) and the owner ruled EX › MT (ANSWERS.md §B.2). L1's local friendship table and L0's agree
    on every classical pair, so FR / NEU / INI never differ."""
    pos = _swiss_position_at()
    chk = P1Check(pos, dignity_rows=DIGNITY_ROWS, orb_rows=ORB_ROWS, naisargika_rows=NAIS_ROWS)
    l1 = {"exalted": "EX", "moolatrikona": "MT", "own": "OWN", "debilitated": "DEB", "friend_sign": "FR", "neutral_sign": "NEU",
          "enemy_sign": "INI"}
    differ = set()
    for i in range(0, 365 * 26, 5):
        t = datetime(2000, 1, 1, tzinfo=UTC) + timedelta(days=i)
        for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            sign, deg = chk.sign_of(g.lower(), t)
            mine, theirs = chk.rung_at(g, t), l1[p1_inputs.dignity_category(g, sign, deg, DIGNITY_ROWS)]
            if mine != theirs:
                differ.add((g, sign, mine, theirs))
    assert differ == {("Moon", "Taurus", "EX", "MT"), ("Mercury", "Virgo", "EX", "MT")}, differ
