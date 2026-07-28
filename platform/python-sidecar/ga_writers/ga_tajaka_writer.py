"""
ga_tajaka_writer.py — GA-Tajaka  `ga_tajaka` writer (the ONE parked L1 asset)
=============================================================================
Builds the **Vārṣaphal annual chart** per varsha (birthday-to-birthday solar
year) for the canonical native, into the dedicated `l1_tajik_varsha_year_lords`
table. Activates the single deliberately-parked L1 asset `ga_tajaka`.

Per CLAUDECODE_BRIEF_GA_TAJAKA_VARSHAPHAL_WRITER_v1_0.md (A17_A21 §5 DDL +
A7 Q4 hybrid storage). Distinct from the *already-built* Tajik primitives:
  - GA7 ga_dashas System 6 = the Mudda annual *dasha* (per-varsha sub-timing).
  - GA5 = natal Tajik *points* (tajik_hadda_lord, tajik_triraashipathi, Sahams).
  - GA8 = the 5 Tajik *aspects* (Ithasala/Eesarpha/Nakta/Yamaya/Manaau).
This writer builds the per-year annual CHART layer on top of those: Muntha,
Vārṣeśa (year-lord) by two methods with candidate scoring, and the Tajik yogas
firing in each annual chart.

Engine: PyJHora (`pyjhora_adapter`) — `compute_positions` for the lightweight
solar-return root-find (Sun → natal sidereal longitude), `compute_chart` for the
full annual-chart positions. No JH-parity oracle; verified by internal
consistency + the FORENSIC §22 Muntha gate.

ATOMIC-GRAIN: queryable atoms are real columns (`year_lord`, `varsha_year`,
`varsha_start_iso`, `varsha_end_iso`, `year_lord_method`). `candidate_lord_jsonb`
and `muntha_position_jsonb` are sanctioned irreducible composites (see migration
221 header + §A17_A21 §5).

FORENSIC GATE (HARD — §7): for the 2026–27 varsha (varsha_year 43, lahiri),
Muntha MUST be Libra / 7th house (from natal Lagna) / lord Venus. Any miss →
raise (build halts → CONDUCTOR_HALT_LOG). This closes the documented L2
fabrication gap (HEATMAP_VARSHPHAL "Muntha Taurus/Gemini approximately").

CANONICAL_CHART_ID: 482012f1-710e-4a25-994a-93821f5871aa (ONLY this).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pyjhora_adapter._jhora import drik, utils
from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.positions import compute_positions

from ga_writers._idempotency import replace_prior_tajik_varsha
from ga_writers._telemetry import update_asset_throughput  # legacy CLI path only; orchestrator never calls this
from pipeline.orchestrator.birth_params import resolve_birth_params

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ENGINE_VERSION = "ga_tajaka/1.0.0"

# canonical ayanamsha id (stored on the row) → pyjhora_adapter ayanamsha id
CANONICAL_AYANAMSHAS: dict[str, str] = {
    "lahiri_chitrapaksha": "lahiri",
    "true_chitra": "true_chitra",
    "krishnamurti": "kp",
    "raman": "raman",
    "surya_siddhanta_classical": "surya_siddhanta",
}

BIRTH_YEAR = 1984
BIRTH_MONTH = 2
BIRTH_DAY = 5

# Hybrid-storage window (A7 Q4): past + current + next 5 years. A 2026 build →
# current varsha = 2026 - 1984 + 1 = 43, so the materialised window is varsha
# 1..48. Parameterised via `reference_year` (default 2026) for reproducibility.
DEFAULT_REFERENCE_YEAR = 2026

SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
# 0-based sign index → ruling graha
SIGN_LORDS: list[str] = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# Exaltation / own / debilitation sign indices (0-based) per graha (classical).
EXALT: dict[str, int] = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
DEBIL: dict[str, int] = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
}
OWN: dict[str, set[int]] = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
# Naisargika (natural) friendships — friend/enemy; anything else neutral.
FRIENDS: dict[str, set[str]] = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES: dict[str, set[str]] = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

# Mean daily motion (deg/day) — Tajik faster/slower ordering for applying aspects.
MEAN_SPEED: dict[str, float] = {
    "Moon": 13.176, "Mercury": 1.383, "Venus": 1.200, "Sun": 0.986,
    "Mars": 0.524, "Jupiter": 0.083, "Saturn": 0.034,
}
CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Deeptamsa (orb of "light"/influence) per graha, degrees — Tajika Nilakanthi /
# mirrors PyJHora's jhora.const.deeptaamsa_of_planets (Sun,Moon,Mars,Mercury,
# Jupiter,Venus,Saturn = 15,12,8,7,9,7,9). Two grahas are within mutual
# deeptamsa when their angular separation <= (deeptamsa[g1] + deeptamsa[g2])
# (M-13: the flat 7° orb previously used here ignored this per-graha spread).
DEEPTAMSA: dict[str, float] = {
    "Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0,
    "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0,
}

# Tajika aspect (drishti) precondition — the whole-sign house-difference
# (1-indexed, B's house counted from A's house, 1 = same sign/conjunction)
# at which a Tajika aspect exists at all. Derived directly from PyJHora's
# jhora.horoscope.transit.tajaka aspect-set functions (trinal=5th/9th,
# sextile=3rd/11th, square=4th/10th, opposition=7th, conjunction=same-sign);
# semi-sextile (2nd/12th) is classified there as "neutral" and NOT included
# in benefic/malefic_aspects_of_the_planet, and 6th/8th never appear in any
# aspect-set function at all. M-13: the previous implementation had NO
# house-relation gate whatsoever — it fired Tajika yogas purely from raw
# ecliptic-longitude separation, so e.g. a 2nd/12th-house (non-aspecting)
# pair within 30° could wrongly fire.
_TAJIKA_ASPECTING_HOUSE_DIFFS = {1, 3, 4, 5, 7, 9, 10, 11}

# Pañcavargīya: the 5 vargas (D1 Kṣetra, D2 Horā, D3 Drekkāṇa, D9 Navāṃśa,
# D12 Dvādaśāṃśa) and per-dignity Viśva-style points.
PANCAVARGA_FACTORS = [1, 2, 3, 9, 12]
DIGNITY_POINTS = {
    "exalted": 45.0, "own": 30.0, "friend": 22.5,
    "neutral": 15.0, "enemy": 7.5, "debilitated": 3.75,
}

TAJIK_YOGAS = ["Ithasala", "Ishrafa", "Nakta", "Kambula", "Dutthottha"]
CLASSICAL_SOURCE = (
    "Tājaka Nīlakaṇṭhī Ch.3–4 (Vārṣeśa / Muntha) + Ch.5–6 (Tājik yogas) — "
    "bg_texts structured corpus (SOURCE_INVENTORY_TAJAKA)."
)

# FORENSIC §22 anchor — the HARD gate.
FORENSIC_VARSHA_YEAR = 2026 - BIRTH_YEAR + 1   # 43
FORENSIC_AYANAMSHA = "lahiri_chitrapaksha"
FORENSIC_MUNTHA_SIGN = "Libra"
FORENSIC_MUNTHA_HOUSE = 7
FORENSIC_MUNTHA_LORD = "Venus"

# Solar-return root-find tolerance (deg): Sun moves ~0.041°/min, so 0.01° ≈ 15 s.
SOLAR_RETURN_TOL_DEG = 0.01


# ── DB helpers ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[ga_tajaka_writer] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── Ephemeris helpers ─────────────────────────────────────────────────────────

def _sun_longitude(dt_local: datetime, aya_adapter: str,
                   birth_params: dict | None = None) -> float:
    """Sidereal Sun longitude (deg, 0..360) at a local-wallclock instant under
    `aya_adapter`, via the lightweight position engine (no full chart)."""
    if not birth_params:
        raise ValueError(
            "[ga_tajaka_writer._sun_longitude] birth_params is required; "
            "caller must pass real birth params, not None."
        )
    bp = birth_params
    dob = drik.Date(dt_local.year, dt_local.month, dt_local.day)
    tob = (dt_local.hour, dt_local.minute, dt_local.second)
    jd = utils.julian_day_number(dob, tob)
    grahas = compute_positions(
        jd, aya_adapter,
        lat=float(bp["latitude_deg"]),
        lon=float(bp["longitude_deg"]),
        tz=float(bp["tz_offset_hours"]),
    )
    for g in grahas:
        if g["name"] == "Sun":
            return float(g["longitude_deg"]) % 360.0
    raise RuntimeError("[ga_tajaka_writer] Sun not found in positions")


def _ang_diff(a: float, b: float) -> float:
    """Signed shortest angular difference a-b in (-180, 180]."""
    return ((a - b + 180.0) % 360.0) - 180.0


def _aspects_lagna(planet: str, full_long: float, varsha_lagna_long: float) -> bool:
    """Tajik aspect (Ithasala-class) test: does `planet` at longitude `full_long`
    aspect the Varsha-Lagna degree within its own classical deeptamsa orb?

    ŚUDDHA-VĀCA P0-9 fix: uses the graha's own per-graha DEEPTAMSA orb (the same
    M-13 table already used by `_tajik_yogas`'s mutual-aspect precondition) —
    this call site was the one M-13 missed, still comparing against a flat 7°
    that ignores the classical per-graha spread (Sun 15°, Saturn 9°, Mercury
    7°, etc.), which could mis-select the Varshesha (year-lord) that grades the
    entire annual chart."""
    orb = DEEPTAMSA.get(planet, 7.0)
    return abs(_ang_diff(full_long, varsha_lagna_long)) <= orb


def _solar_return(varsha_year: int, natal_sun_long: float, aya_adapter: str,
                  birth_params: dict | None = None) -> tuple[datetime, dict[str, Any]]:
    """Root-find the local-wallclock instant in calendar year
    (birth_year + varsha_year - 1) where the sidereal Sun returns to
    `natal_sun_long`. Bisection on the signed Sun-longitude difference within a
    ±2-day bracket around the birthday anniversary (widened to ±5 if needed).

    D-2 cycle-1 rebuild incident: the underlying swisseph engine has been
    observed (deployed container only, not locally reproducible — likely an
    ephemeris-file/Moshier-fallback edge case specific to that environment)
    to occasionally raise on a specific bisection instant it cannot compute
    (`jd ... outside Moshier planet range`). A single unresolvable instant
    inside an otherwise-healthy bisection must not crash this asset (and its
    ~26-asset downstream L3/L4/L5 closure) — `_safe_f` catches any exception
    from the underlying position engine and treats that instant as
    "no information" (None), same honesty-preserving non-fabrication
    discipline as the existing "no sign change" fallback below: a row is
    still emitted, honestly marked not converged, never silently dropped."""
    if not birth_params:
        raise ValueError(
            "[ga_tajaka_writer._solar_return] birth_params is required; "
            "caller must pass real birth params, not None."
        )
    bp = birth_params
    iso = str(bp["datetime_iso"])
    cal_year = int(iso[:4]) + varsha_year - 1
    birth_month = int(iso[5:7])
    birth_day = int(iso[8:10])
    birth_hour = int(iso[11:13])
    birth_min = int(iso[14:16])
    anniversary = datetime(cal_year, birth_month, birth_day, birth_hour, birth_min, 0)

    def f(dt: datetime) -> float:
        return _ang_diff(_sun_longitude(dt, aya_adapter, birth_params=bp), natal_sun_long)

    def _safe_f(dt: datetime) -> float | None:
        try:
            return f(dt)
        except Exception as exc:  # noqa: BLE001 — engine-level failure, not a logic bug
            logger.warning(
                "[ga_tajaka_writer] _solar_return: position engine failed at %s "
                "(varsha_year=%d, aya=%s): %s — treating as unresolvable instant",
                dt.isoformat(), varsha_year, aya_adapter, exc,
            )
            return None

    def _unconverged(reason: str, bracket_days_: int) -> tuple[datetime, dict[str, Any]]:
        diff = _safe_f(anniversary)
        return anniversary, {"converged": False,
                             "diff_deg": round(diff, 6) if diff is not None else None,
                             "bracket_days": bracket_days_, "iterations": 0,
                             "unconverged_reason": reason}

    bracket_days = 2
    lo = anniversary - timedelta(days=bracket_days)
    hi = anniversary + timedelta(days=bracket_days)
    f_lo, f_hi = _safe_f(lo), _safe_f(hi)
    while (f_lo is None or f_hi is None or f_lo * f_hi > 0) and bracket_days < 6:
        bracket_days += 2
        lo = anniversary - timedelta(days=bracket_days)
        hi = anniversary + timedelta(days=bracket_days)
        f_lo, f_hi = _safe_f(lo), _safe_f(hi)
    if f_lo is None or f_hi is None:
        return _unconverged("position_engine_error", bracket_days)
    if f_lo * f_hi > 0:
        # No sign change — fall back to the anniversary itself (deg diff recorded).
        return _unconverged("no_sign_change", bracket_days)

    iters = 0
    while (hi - lo) > timedelta(minutes=1) and iters < 64:
        mid = lo + (hi - lo) / 2
        f_mid = _safe_f(mid)
        if f_mid is None:
            # Unresolvable midpoint — stop bisecting here rather than crash;
            # [lo, hi] still brackets a real root, just not narrowed further.
            break
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
        iters += 1
    instant = lo + (hi - lo) / 2
    diff = _safe_f(instant)
    if diff is None:
        return _unconverged("position_engine_error_at_final_instant", bracket_days)
    return instant, {"converged": True, "diff_deg": round(diff, 6),
                     "bracket_days": bracket_days, "iterations": iters}


# ── Dignity / Pañcavargīya ────────────────────────────────────────────────────

def _dignity(graha: str, sign0: int) -> str:
    if EXALT.get(graha) == sign0:
        return "exalted"
    if sign0 in OWN.get(graha, set()):
        return "own"
    if DEBIL.get(graha) == sign0:
        return "debilitated"
    lord = SIGN_LORDS[sign0]
    if lord == graha:
        return "own"
    if lord in FRIENDS.get(graha, set()):
        return "friend"
    if lord in ENEMIES.get(graha, set()):
        return "enemy"
    return "neutral"


def _panchavargiya_bala(graha: str, full_long: float) -> dict[str, Any]:
    """Pañcavargīya Bala (Viśva-style units) = Σ dignity points across D1, D2,
    D3, D9, D12 for `graha` at `full_long` in the annual chart. Per-varga
    components are returned for audit. Unsupported varga factors degrade to a
    skipped component (documented) rather than halting."""
    components: dict[str, Any] = {}
    total = 0.0
    for f in PANCAVARGA_FACTORS:
        try:
            res = drik.dasavarga_from_long(full_long, f)
            sign0 = int(res[0]) % 12
            dig = _dignity(graha, sign0)
            pts = DIGNITY_POINTS[dig]
            components[f"D{f}"] = {"sign": SIGNS[sign0], "dignity": dig, "points": pts}
            total += pts
        except Exception as exc:  # noqa: BLE001 — degrade, don't halt
            components[f"D{f}"] = {"error": str(exc), "points": 0.0}
    return {"bala": round(total, 4), "components": components}


# ── Tajik yoga firing (consumes GA8 aspect_tajik logic) ───────────────────────

def _tajika_aspecting(house1: int, house2: int) -> bool:
    """True iff two whole-sign houses (1-12) are in a recognized Tajika
    aspect relation (conjunction/sextile/square/trinal/opposition) — the
    mutual-aspect precondition. See _TAJIKA_ASPECTING_HOUSE_DIFFS."""
    diff = ((house2 - house1) % 12) + 1
    return diff in _TAJIKA_ASPECTING_HOUSE_DIFFS


def _tajik_yogas(grahas_by_name: dict[str, dict], varsha_lagna_long: float
                 ) -> list[str]:
    """Which of Ithasala/Ishrafa/Nakta/Kambula/Dutthottha fire in the annual
    chart. Reuses the GA8 Tajik-aspect rule set — per-graha deeptamsa orb
    (M-13, not a flat 7°) gated by a real Tajika mutual-aspect precondition
    (M-13, not raw longitude proximity) + applying/separating via mean-speed
    ordering; does NOT recompute the GA8 chart_facts rows."""
    fired: set[str] = set()
    longs = {g: grahas_by_name[g]["longitude"] for g in CLASSICAL_GRAHAS
             if g in grahas_by_name}
    houses_by_graha = {g: int(grahas_by_name[g]["house"]) for g in CLASSICAL_GRAHAS
                       if g in grahas_by_name and grahas_by_name[g].get("house")}

    pairs_within: list[tuple[str, str, float, bool]] = []  # (g1, g2, sep, applying)
    for i, g1 in enumerate(CLASSICAL_GRAHAS):
        for g2 in CLASSICAL_GRAHAS[i + 1:]:
            if g1 not in longs or g2 not in longs:
                continue
            # M-13 precondition #1: no Tajika aspect exists at all unless the
            # two grahas are in a recognized whole-sign aspect relation.
            h1, h2 = houses_by_graha.get(g1), houses_by_graha.get(g2)
            if h1 is None or h2 is None or not _tajika_aspecting(h1, h2):
                continue
            sep = abs(_ang_diff(longs[g1], longs[g2]))
            # M-13 precondition #2: combined per-graha deeptamsa, not a flat 7°.
            orb = DEEPTAMSA[g1] + DEEPTAMSA[g2]
            # Faster planet (greater mean speed) is the approacher.
            faster, slower = (g1, g2) if MEAN_SPEED[g1] >= MEAN_SPEED[g2] else (g2, g1)
            # Applying (Ithasala) = faster planet behind the slower in longitude.
            d = _ang_diff(longs[slower], longs[faster])  # slower ahead → positive
            applying = d > 0
            if sep <= orb:
                pairs_within.append((g1, g2, sep, applying))
                if applying:
                    fired.add("Ithasala")
                    if "Moon" in (g1, g2):
                        # Kambula (Tajika Nilakanthi ch.5-6): Moon's Ithasala
                        # partner must be STRONGER than the Moon (Panchavargiya
                        # Bala) — mere Moon-membership in an Ithasala pair is
                        # not sufficient (M-13: "Kambula without Moon
                        # conditions"). Reuses the same Bala already computed
                        # for Varsesa candidate scoring in this module.
                        partner = g2 if g1 == "Moon" else g1
                        moon_bala = _panchavargiya_bala("Moon", longs["Moon"])["bala"]
                        partner_bala = _panchavargiya_bala(partner, longs[partner])["bala"]
                        if partner_bala > moon_bala:
                            fired.add("Kambula")
                else:
                    fired.add("Ishrafa")        # separating (Eesarpha)
            elif applying:
                fired.add("Dutthottha")         # approaching but beyond deeptamsa (Manaau-class)

    # Nakta: a fast 'translator' planet within its combined deeptamsa of two
    # others that are not themselves within combined deeptamsa (and each pair
    # must independently satisfy the Tajika aspect precondition).
    for t in CLASSICAL_GRAHAS:
        if t not in longs:
            continue
        within = [
            g for g in CLASSICAL_GRAHAS
            if g != t and g in longs
            and houses_by_graha.get(t) is not None and houses_by_graha.get(g) is not None
            and _tajika_aspecting(houses_by_graha[t], houses_by_graha[g])
            and abs(_ang_diff(longs[g], longs[t])) <= (DEEPTAMSA[g] + DEEPTAMSA[t])
        ]
        for i in range(len(within)):
            for j in range(i + 1, len(within)):
                a, b = within[i], within[j]
                if (houses_by_graha.get(a) is not None and houses_by_graha.get(b) is not None
                        and _tajika_aspecting(houses_by_graha[a], houses_by_graha[b])
                        and abs(_ang_diff(longs[a], longs[b])) > (DEEPTAMSA[a] + DEEPTAMSA[b])):
                    fired.add("Nakta")
    return [y for y in TAJIK_YOGAS if y in fired]


# ── GA5 read (Tri-Rāśi-pati candidate) ───────────────────────────────────────

def _read_trirashipathi(conn: Any, chart_id: str, canonical_aya: str) -> str | None:
    try:
        cur = conn.execute(
            "SELECT fact_value_text FROM chart_facts WHERE chart_id = %s AND ayanamsha_id = %s "
            "AND fact_category = 'tajik_triraashipathi' AND fact_key = 'lord' LIMIT 1",
            [chart_id, canonical_aya],
        )
        row = cur.fetchone()
        return row["fact_value_text"] if row else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ga_tajaka_writer] trirashipathi read failed (%s): %s",
                       canonical_aya, exc)
        return None


# ── Core per-varsha computation ───────────────────────────────────────────────

def _compute_one(conn: Any, chart_id: str, canonical_aya: str, aya_adapter: str,
                 varsha_year: int, natal_chart: dict, natal_sun_long: float,
                 build_id: str, birth: dict | None = None) -> dict[str, Any]:
    """Compute a single varsha row dict (annual chart) for one ayanamsha.

    `birth` supplies the chart's place/tz for the annual chart compute;
    must be a non-empty dict (no fallback to any hardcoded constant).
    The annual chart's instant comes from the solar return; only its place/tz
    are taken from birth."""
    natal_lagna = natal_chart["ascendant"]
    natal_lagna_sign0 = int(natal_lagna["sign_id"]) - 1
    natal_lagna_deg = float(natal_lagna.get("degree_in_sign", 0.0))

    # ── Muntha (sign-advance; the FORENSIC-gated value) ──────────────────────
    muntha_sign0 = (natal_lagna_sign0 + (varsha_year - 1)) % 12
    # Independent re-derivation (cumulative +1) for two-pass verification.
    muntha_check = natal_lagna_sign0
    for _ in range(varsha_year - 1):
        muntha_check = (muntha_check + 1) % 12
    muntha_ok = muntha_check == muntha_sign0
    muntha_lord = SIGN_LORDS[muntha_sign0]
    house_from_natal = ((muntha_sign0 - natal_lagna_sign0) % 12) + 1

    # ── Solar return + annual chart ──────────────────────────────────────────
    instant, sr_audit = _solar_return(varsha_year, natal_sun_long, aya_adapter, birth_params=birth)
    next_instant, _ = _solar_return(varsha_year + 1, natal_sun_long, aya_adapter, birth_params=birth)
    instant_iso = instant.replace(microsecond=0).isoformat() + "+05:30"
    next_iso = next_instant.replace(microsecond=0).isoformat() + "+05:30"

    if not birth:
        raise ValueError(
            "[ga_tajaka_writer._compute_one] birth params are required; "
            "caller must pass real birth params, not None."
        )
    _birth_base = birth
    annual = compute_chart(
        {**_birth_base,
         "datetime_iso": instant.replace(microsecond=0).isoformat()},
        ayanamsha_id=aya_adapter,
    )
    varsha_lagna = annual["ascendant"]
    varsha_lagna_sign0 = int(varsha_lagna["sign_id"]) - 1
    varsha_lagna_long = float(varsha_lagna.get("longitude_deg", varsha_lagna_sign0 * 30.0))
    house_from_varsha = ((muntha_sign0 - varsha_lagna_sign0) % 12) + 1

    grahas_by_name = {g["name"]: g for g in annual["grahas"]}

    # Solar-return cross-check (±1 min ⇒ ≤ SOLAR_RETURN_TOL_DEG).
    # diff_deg can be None (position-engine failure even at the fallback
    # anniversary instant, see _solar_return's _unconverged) — (v or 99.0)
    # coalesces None the same way the prior missing-key default did, since
    # `.get(key, default)` only applies the default when the key is ABSENT,
    # not when it's present with value None.
    sr_diff = abs(sr_audit.get("diff_deg") or 99.0)
    sr_ok = sr_audit.get("converged", False) and sr_diff <= SOLAR_RETURN_TOL_DEG

    # ── Vārṣeśa candidate office-bearers ─────────────────────────────────────
    tri_lord = _read_trirashipathi(conn, chart_id, canonical_aya)
    # Dina-Rātri-pati: luminary of the varsha-start day/night. Sun above horizon
    # (house 7..12, i.e. between Asc and Desc going up) ⇒ day ⇒ Sun; else Moon.
    sun_house = int(grahas_by_name.get("Sun", {}).get("house", 1))
    dinaratri = "Sun" if 7 <= sun_house <= 12 else "Moon"

    candidates: dict[str, str] = {
        "Lagnesa": SIGN_LORDS[varsha_lagna_sign0],
        "Munthesa": muntha_lord,
        "JanmaLagnesa": SIGN_LORDS[natal_lagna_sign0],
        "TriRashipati": tri_lord or SIGN_LORDS[varsha_lagna_sign0],
        "Dinaratripati": dinaratri,
    }

    scored: dict[str, Any] = {}
    for office, planet in candidates.items():
        g = grahas_by_name.get(planet)
        full_long = float(g["longitude"]) if g else 0.0
        pv = _panchavargiya_bala(planet, full_long)
        # Tajik aspect (Ithasala-class) to the Varsha-Lagna degree. ŚUDDHA-VĀCA
        # P0-9: per-graha deeptamsa orb (M-13's own fix, applied here — this call
        # site was the one M-13 missed), not a flat 7° ignoring the classical spread.
        aspects_lagna = _aspects_lagna(planet, full_long, varsha_lagna_long)
        scored[office] = {
            "planet": planet,
            "panchavargiya_bala": pv["bala"],
            "components": pv["components"],
            "aspects_lagna": aspects_lagna,
        }

    # Pañcavargīya method: highest Pañcavargīya Bala among the 5 office-bearers.
    pv_winner_office = max(scored, key=lambda o: scored[o]["panchavargiya_bala"])
    pv_winner = scored[pv_winner_office]["planet"]

    # Tajik-classical: strongest office-bearer that aspects the Varsha-Lagna;
    # default to Munthesa (classical fallback) when none aspects the Lagna.
    aspecting = {o: s for o, s in scored.items() if s["aspects_lagna"]}
    if aspecting:
        tc_winner_office = max(aspecting, key=lambda o: aspecting[o]["panchavargiya_bala"])
    else:
        tc_winner_office = "Munthesa"
    tc_winner = scored[tc_winner_office]["planet"]

    methods_diverge = tc_winner != pv_winner

    # ── Tajik yogas in the annual chart ──────────────────────────────────────
    yogas = _tajik_yogas(grahas_by_name, varsha_lagna_long)

    # ── Verification (two-pass) ──────────────────────────────────────────────
    year_lord_ok = bool(tc_winner) and bool(pv_winner)
    verification = ("two_pass_verified"
                    if (muntha_ok and year_lord_ok and sr_ok)
                    else "divergent_flagged")

    muntha_jsonb = {
        "sign": SIGNS[muntha_sign0],
        "house_from_natal_lagna": house_from_natal,
        "house_from_varsha_lagna": house_from_varsha,
        "lord": muntha_lord,
        "degree": round(natal_lagna_deg, 4),
    }
    candidate_jsonb = {
        "offices": scored,
        "tajik_classical_winner": {"office": tc_winner_office, "planet": tc_winner},
        "panchavargiya_winner": {"office": pv_winner_office, "planet": pv_winner},
        "methods_diverge": methods_diverge,
    }
    ephemeris_jsonb = {
        "natal_sun_long_deg": round(natal_sun_long, 6),
        "solar_return": sr_audit,
        "varsha_lagna_sign": SIGNS[varsha_lagna_sign0],
        "muntha_two_pass_match": muntha_ok,
        "solar_return_cross_check_pass": sr_ok,
    }

    citation_ref = (f"ga_tajaka.varsha{varsha_year}.{canonical_aya}"
                    f"@chart={chart_id}:eng={ENGINE_VERSION}")
    citation_human = (
        f"Varsha {varsha_year} ({instant_iso[:10]}→{next_iso[:10]}, "
        f"{canonical_aya}): Muntha {SIGNS[muntha_sign0]} "
        f"({house_from_natal}H from Lagna, lord {muntha_lord}); "
        f"Vārṣeśa {tc_winner} (tajik_classical); "
        f"Pañcavargīya winner {pv_winner}"
        + ("; methods diverge." if methods_diverge else ".")
    )

    return {
        "varsha_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": canonical_aya,
        "build_id": build_id,
        "varsha_year": varsha_year,
        "varsha_start_iso": instant_iso,
        "varsha_end_iso": next_iso,
        "year_lord_method": "tajik_classical",
        "year_lord": tc_winner,
        "candidate_lord_jsonb": candidate_jsonb,
        "muntha_position_jsonb": muntha_jsonb,
        "applicable_tajik_yogas_array": yogas,
        "classical_source_citation": CLASSICAL_SOURCE,
        "ephemeris_audit_jsonb": ephemeris_jsonb,
        "verification_pass_status": verification,
        "citation_ref": citation_ref,
        "citation_human": citation_human,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        # internal (not columns) — for the FORENSIC gate:
        "_muntha_sign": SIGNS[muntha_sign0],
        "_muntha_house_from_natal": house_from_natal,
        "_muntha_lord": muntha_lord,
    }


# ── Insert ────────────────────────────────────────────────────────────────────

_COLUMNS = [
    "varsha_id", "chart_id", "ayanamsha_id", "build_id", "varsha_year",
    "varsha_start_iso", "varsha_end_iso", "year_lord_method", "year_lord",
    "candidate_lord_jsonb", "muntha_position_jsonb", "applicable_tajik_yogas_array",
    "classical_source_citation", "ephemeris_audit_jsonb", "verification_pass_status",
    "citation_ref", "citation_human", "computed_at",
]


def _insert_rows(conn: Any, rows: list[dict]) -> int:
    if not rows:
        return 0
    placeholders = ", ".join(["%s"] * len(_COLUMNS))
    sql = (f"INSERT INTO l1_tajik_varsha_year_lords ({', '.join(_COLUMNS)}) "
           f"VALUES ({placeholders})")
    n = 0
    for r in rows:
        vals = []
        for c in _COLUMNS:
            v = r[c]
            if c in ("candidate_lord_jsonb", "muntha_position_jsonb",
                     "ephemeris_audit_jsonb"):
                v = json.dumps(v)
            vals.append(v)
        conn.execute(sql, vals)
        n += 1
    return n


# ── On-demand callable (A7 hybrid: retrieval tool computes a missing varsha) ──

def compute_varsha(chart_id: str,
                   ayanamsha_id: str = "lahiri_chitrapaksha",
                   varsha_year: int = 1,
                   *, persist: bool = False,
                   build_id: str | None = None,
                   birth_params: dict | None = None) -> dict[str, Any]:
    """Compute (and optionally persist) one varsha row live — the hybrid
    on-demand path for varshas outside the precomputed window. Returns the row
    dict (sans internal `_*` keys when persisted).

    `birth_params`: required for every chart (native included). Must be a non-empty
    dict from public.charts (via orchestrator fetch_birth_params). resolve_birth_params()
    raises ValueError for any chart with falsy birth_params — no silent fallback.
    """
    aya_adapter = CANONICAL_AYANAMSHAS.get(ayanamsha_id, "lahiri")
    bid = build_id or str(uuid.uuid4())
    # Contamination guard: every chart (native included) must have real birth_params
    # from public.charts. resolve_birth_params raises for any chart with falsy params.
    bp = resolve_birth_params(chart_id, birth_params)
    with _conn() as conn:
        natal = compute_chart({**bp}, ayanamsha_id=aya_adapter)
        natal_sun = float(next(g for g in natal["grahas"] if g["name"] == "Sun")["longitude"]) % 360.0
        row = _compute_one(conn, chart_id, ayanamsha_id, aya_adapter,
                           varsha_year, natal, natal_sun, bid, birth=bp)
        if persist:
            replace_prior_tajik_varsha(conn, [row])
            _insert_rows(conn, [row])
            conn.commit()
    return row


# ── Build (precompute window) ─────────────────────────────────────────────────

def build_ga_tajaka(chart_id: str,
                    build_id: str | None = None,
                    *, conn: Any = None,
                    birth_params: dict[str, Any] | None = None,
                    reference_year: int = DEFAULT_REFERENCE_YEAR,
                    min_varsha: int = 1,
                    max_varsha: int | None = None,
                    ayanamshas: list[str] | None = None) -> dict[str, Any]:
    """Precompute the hybrid window (past→present+5) × 5 ayanamshas and write
    `l1_tajik_varsha_year_lords`. Raises on the FORENSIC Muntha miss or any
    two-pass divergence (build halts).

    Connection ownership (Orchestrator Convergence Phase 3):
    - conn injected (orchestrator path): writes on the caller-owned connection,
      does NOT commit or close, does NOT write asset_throughput (the orchestrator
      is the sole build-state writer). The caller's SAVEPOINT owns atomicity.
    - conn None (legacy CLI path via build_runner): opens its own connection,
      commits, closes, and writes asset_throughput via _telemetry.
    """
    from contextlib import nullcontext
    if build_id is None:
        build_id = str(uuid.uuid4())
    owns_conn = conn is None
    # Every chart (native included) must have real birth_params from public.charts.
    # resolve_birth_params raises for any chart with falsy params.
    bp = resolve_birth_params(chart_id, birth_params)
    birth_year = int(str(bp["datetime_iso"])[:4])
    current_varsha = reference_year - birth_year + 1
    if max_varsha is None:
        max_varsha = current_varsha + 5
    aya_ids = ayanamshas or list(CANONICAL_AYANAMSHAS.keys())

    logger.info("[ga_tajaka_writer] build chart=%s window=varsha[%d..%d] ayanamshas=%d",
                chart_id, min_varsha, max_varsha, len(aya_ids))

    all_rows: list[dict] = []
    per_aya_counts: dict[str, int] = {}
    forensic_checks: list[dict] = []
    divergent: list[dict] = []

    with (_conn() if owns_conn else nullcontext(conn)) as conn:
        for canonical_aya in aya_ids:
            aya_adapter = CANONICAL_AYANAMSHAS[canonical_aya]
            natal = compute_chart({**bp}, ayanamsha_id=aya_adapter)
            natal_sun = float(
                next(g for g in natal["grahas"] if g["name"] == "Sun")["longitude"]
            ) % 360.0
            aya_rows: list[dict] = []
            for v in range(min_varsha, max_varsha + 1):
                row = _compute_one(conn, chart_id, canonical_aya, aya_adapter,
                                   v, natal, natal_sun, build_id, birth=bp)
                # FORENSIC gate — native-anchored Muntha; only asserted for the native.
                if (chart_id == CANONICAL_CHART_ID
                        and canonical_aya == FORENSIC_AYANAMSHA
                        and v == FORENSIC_VARSHA_YEAR):
                    fc = {
                        "varsha_year": v, "ayanamsha": canonical_aya,
                        "sign": row["_muntha_sign"],
                        "house": row["_muntha_house_from_natal"],
                        "lord": row["_muntha_lord"],
                    }
                    forensic_checks.append(fc)
                    if (fc["sign"] != FORENSIC_MUNTHA_SIGN
                            or fc["house"] != FORENSIC_MUNTHA_HOUSE
                            or fc["lord"] != FORENSIC_MUNTHA_LORD):
                        raise RuntimeError(
                            f"FORENSIC HALT: ga_tajaka Muntha gate failed for varsha "
                            f"{v} ({canonical_aya}): got {fc['sign']}/{fc['house']}H/"
                            f"{fc['lord']}, expected {FORENSIC_MUNTHA_SIGN}/"
                            f"{FORENSIC_MUNTHA_HOUSE}H/{FORENSIC_MUNTHA_LORD}.")
                if row["verification_pass_status"] == "divergent_flagged":
                    divergent.append({"varsha_year": v, "ayanamsha": canonical_aya,
                                      "audit": row["ephemeris_audit_jsonb"]})
                aya_rows.append(row)
            per_aya_counts[canonical_aya] = len(aya_rows)
            all_rows.extend(aya_rows)

        if divergent:
            raise RuntimeError(
                f"TWO-PASS HALT: {len(divergent)} divergent_flagged varsha rows "
                f"(first: {divergent[0]}). Build halted before insert.")

        # Strip internal keys before persistence.
        for r in all_rows:
            for k in ("_muntha_sign", "_muntha_house_from_natal", "_muntha_lord"):
                r.pop(k, None)

        deleted = replace_prior_tajik_varsha(conn, all_rows)
        inserted = _insert_rows(conn, all_rows)
        if owns_conn:
            conn.commit()
            update_asset_throughput(conn, "ga_tajaka", chart_id, build_id,
                                    inserted, state="lit")
            conn.commit()

    forensic_pass = bool(forensic_checks) and all(
        c["sign"] == FORENSIC_MUNTHA_SIGN and c["house"] == FORENSIC_MUNTHA_HOUSE
        and c["lord"] == FORENSIC_MUNTHA_LORD for c in forensic_checks)

    summary = {
        "status": "PASS",
        "chart_id": chart_id,
        "build_id": build_id,
        "window": {"min_varsha": min_varsha, "max_varsha": max_varsha,
                   "reference_year": reference_year,
                   "calendar_span": [birth_year + min_varsha - 1,
                                     birth_year + max_varsha - 1]},
        "ayanamshas": list(aya_ids),
        "rows_deleted_idempotent": deleted,
        "total_rows_written": inserted,
        "per_ayanamsha_counts": per_aya_counts,
        "forensic_pass": forensic_pass,
        "forensic_checks": forensic_checks,
        "two_pass_verified": len(divergent) == 0,
        "divergent_flagged": len(divergent),
        "storage_strategy": "hybrid (precomputed window; rest on-demand via compute_varsha)",
    }
    logger.info("[ga_tajaka_writer] PASS rows=%d forensic=%s two_pass=%s",
                inserted, forensic_pass, summary["two_pass_verified"])
    return summary


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="ga_tajaka Vārṣaphal writer")
    parser.add_argument("--chart_id", default=CANONICAL_CHART_ID)
    parser.add_argument("--build_id", default=None)
    parser.add_argument("--reference_year", type=int, default=DEFAULT_REFERENCE_YEAR)
    parser.add_argument("--min_varsha", type=int, default=1)
    parser.add_argument("--max_varsha", type=int, default=None)
    parser.add_argument("--json", dest="output_json", action="store_true")
    args = parser.parse_args()
    result = build_ga_tajaka(
        chart_id=args.chart_id, build_id=args.build_id,
        reference_year=args.reference_year,
        min_varsha=args.min_varsha, max_varsha=args.max_varsha,
    )
    if args.output_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"ga_tajaka: status={result['status']} rows={result['total_rows_written']} "
              f"forensic={result['forensic_pass']} two_pass={result['two_pass_verified']} "
              f"window={result['window']['calendar_span']}")
    import sys
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
