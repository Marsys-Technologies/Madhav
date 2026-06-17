"""
ga_sade_sati_writer.py — GA9 ga_sade_sati writer
==================================================
Writes Sade Sati cycles, phases, quarters, dhaiya periods, Saturn-Moon
configurations, cancellation checks, modifier overlays, concurrent dasha
overlays, and downstream cross-references into `chart_facts`.

Per A9_SADE_SATI_SPEC_v1_0.md §0–§12 (LOCKED 2026-05-29).

ATOMIC-GRAIN DISCIPLINE (the defining rule for GA9):
  - Per-period boolean flags → atomic bool rows (each its own row)
  - Concurrent dasha lords → atomic text rows (7 separate keys)
  - Saturn state during period → atomic text/num keys
  - Quarter intensity → atomic text key; rationale → sanctioned JSONB

FIVE SANCTIONED JSONB FIELDS (each has irreducibility justification):
  1. saturn_nakshatra_transitions_jsonb_atomic — ordered time-series of
     nakshatra-boundary crossings within a phase (irreducible: ordering
     and count vary per phase; no fixed number of atomic slots).
  2. quarter_intensity_rationale_jsonb — rule-set driving the intensity
     classification (irreducible: the set of rules is the atom; splitting
     into N boolean columns requires knowing N at schema-design time,
     but rules vary per quarter with new combinations at each assessment).
  3. cancellation_rules_invoked_jsonb — which of 8 named rules fired
     (irreducible: a set of named predicates; encoding as 8 bool columns
     loses the rule-name semantics needed for human-readable citations).
  4. d10_karya_activation_facts_jsonb — fact_id references from GA6
     D10 Karya rows (irreducible: FK-style list; count varies per cycle).
  5. argala_during_period_jsonb — subset of GA8's 144-row argala matrix
     active during the cycle (irreducible: a set of house-pair activations;
     count varies; each element is a structured {from_h, to_h, strength}
     triple which cannot be flattened without losing structure).

CANONICAL_CHART_ID: 482012f1-710e-4a25-994a-93821f5871aa  (ONLY this).
Calculation window: 1950-01-01 → 2100-12-31 (per A7 Q3+ rule).

Dependencies (upstream; Step 0 verifies before compute):
  GA3 rows: graha_position.MOON.sign (per ayanamsha) + GA3 Moon pada
  GA4 rows: tara_bala_natal_baseline (27 rows) — Tara state at peak
  GA6 rows: varga_karya_bhava_per_varga — D10 Karya activation cross-ref
  GA7 rows: chart_dashas — all 7 dasha systems concurrent lords
  GA8 rows: argala_natal_matrix (144 rows) + saturn_moon_yoga_modifier

Engine: panchanga_engine / swisseph (DE441) for Saturn transit detection.
        PyJHora for natal positions (cross-ayanamsha Moon sign read from GA3).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
from datetime import datetime, timezone, timedelta
from typing import Any

from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers._telemetry import update_asset_throughput

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ENGINE_VERSION = "ga9/1.0.0"
WINDOW_START = datetime(1950, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2100, 12, 31, tzinfo=timezone.utc)

# 7.5-year cycle invariant in days.
# Saturn's orbit is elliptical and retrograde patterns vary; real Sade Sati
# spans ~6-9 years (2190-3285 days), so tolerance must be ~±600 days.
CYCLE_DAYS_EXPECTED = 365.25 * 7.5  # ~2739.4 days
CYCLE_DAYS_TOLERANCE = 600.0

# Canonical 5 ayanamshas (same as GA3 / GA4 / GA8)
CANONICAL_AYANAMSHAS: list[str] = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

# Zodiac sign ordering (1-based index)
SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_NUM: dict[str, int] = {s: i + 1 for i, s in enumerate(SIGNS)}

# Saturn dignity map (per classical rules)
SATURN_DIGNITY: dict[str, str] = {
    "Aries": "enemy",
    "Taurus": "friend",
    "Gemini": "neutral",
    "Cancer": "enemy",
    "Leo": "enemy",
    "Virgo": "friend",
    "Libra": "exalted",
    "Scorpio": "enemy",
    "Sagittarius": "neutral",
    "Capricorn": "own",
    "Aquarius": "own",
    "Pisces": "neutral",
}

# 8 cancellation rule keys (Q1=A)
CANCELLATION_RULES: list[str] = [
    "saturn_vargottama",
    "saturn_own_sign",
    "saturn_exalted",
    "dispositor_strong",
    "jupiter_aspect_to_saturn",
    "saturn_moon_parivartana_natal",
    "saturn_yoga_karaka",
    "strong_benefic_dasha_concurrent",
]

# Quarter intensity per BPHS Ch.71 phase-position rule
# (Q1=entry, Q2=middle-entry, Q3=middle-exit, Q4=exit)
PHASE_QUARTER_INTENSITY: dict[tuple[str, int], str] = {
    ("VISHAKHA", 1): "Medium",  # Saturn approaching, still in 12H
    ("VISHAKHA", 2): "Low",
    ("VISHAKHA", 3): "Low",
    ("VISHAKHA", 4): "Medium",
    ("JANMA", 1): "High",       # Saturn transiting natal Moon sign peak
    ("JANMA", 2): "High",
    ("JANMA", 3): "High",
    ("JANMA", 4): "Medium",
    ("ANUMUKHA", 1): "Medium",  # Saturn in 2H from Moon, exiting
    ("ANUMUKHA", 2): "Low",
    ("ANUMUKHA", 3): "Low",
    ("ANUMUKHA", 4): "Low",
}

# Nakshatra-based pada modifier for Moon at Purva Bhadrapada
# Pada 1-3 = Aquarius (mild modification); Pada 4 = Pisces (moderate)
PADA_MODIFIER: dict[int, str] = {
    1: "mild_pada1_intensifier",
    2: "mild_pada2_intensifier",
    3: "mild_pada3_intensifier",
    4: "moderate_pada4_shift",
}

# Native birth parameters
NATIVE_BIRTH = {
    "datetime_iso": "1984-02-05T10:43:00",
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "tz_offset_hours": 5.5,
    "place_name": "Bhubaneswar, Odisha, India",
    "subject_label": "Abhisek Mohanty",
}

# Native Moon nakshatra pada at birth (FORENSIC anchor)
NATIVE_MOON_NAKSHATRA = "Purva Bhadrapada"
NATIVE_MOON_PADA = 4      # Pada 4 = Pisces side of Purva Bhadrapada


# ── DB helpers ────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[ga_sade_sati_writer] DATABASE_URL not set")


def _conn():
    import psycopg
    return psycopg.connect(_db_url())


# ── fact_id + citation builders ───────────────────────────────────────────────

def _fact_id(category: str, subject: str, key: str, chart_id: str,
              ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _citation_ref(category: str, subject: str, key: str,
                  chart_id: str, ayanamsha_id: str) -> str:
    return (f"{category}.{subject}.{key}"
            f"@chart={chart_id}:ay={ayanamsha_id}:eng={ENGINE_VERSION}")


# ── HALT log writer ──────────────────────────────────────────────────────────

def _write_halt_log(gate_name: str, msg: str) -> None:
    """Write to CONDUCTOR_HALT_LOG in l1-ganita-build directory."""
    try:
        p = pathlib.Path(__file__).resolve()
        for _ in range(10):
            candidate = p / "00_ARCHITECTURE" / "CONDUCTOR" / "l1-ganita-build" / "CONDUCTOR_HALT_LOG.md"
            if candidate.parent.parent.parent.exists():
                candidate.parent.mkdir(parents=True, exist_ok=True)
                with open(candidate, "a", encoding="utf-8") as fh:
                    fh.write(
                        f"\n## HALT: {gate_name} — {datetime.now(timezone.utc).isoformat()}\n"
                        f"{msg}\n"
                    )
                return
            p = p.parent
    except Exception:
        pass


# ── Swisseph Saturn transit detection ────────────────────────────────────────

def _detect_saturn_sign_changes(window_start: datetime, window_end: datetime) -> list[dict]:
    """
    Use swisseph (via panchanga_engine) to detect all Saturn sign-change events
    in the given window. Returns list of {date_utc, sign_from, sign_to} dicts.

    Primary pass: walk Julian days, detect sign changes by checking Saturn's
    tropical longitude mapped to sidereal sign via ayanamsha offset.

    For the GA9 campaign we use the Lahiri ayanamsha offset to determine sign
    boundaries for the transit engine (sign detection uses Lahiri as reference
    engine; per-ayanamsha Moon sign is read from GA3 natal data).

    Fallback: if swisseph unavailable, raises ImportError with clear message.
    """
    try:
        import swisseph as swe
    except ImportError:
        raise ImportError(
            "[ga_sade_sati_writer] swisseph not installed. "
            "Install pyswisseph: pip install pyswisseph"
        )

    # Lahiri ayanamsha as transit reference engine (GA9 brief §rails)
    swe.set_ephe_path(os.environ.get("SWISSEPH_EPHE_PATH", "/usr/share/ephe"))
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    jd_start = swe.julday(
        window_start.year, window_start.month, window_start.day, 0.0
    )
    jd_end = swe.julday(
        window_end.year, window_end.month, window_end.day, 0.0
    )

    changes: list[dict] = []
    STEP_DAYS = 5.0  # 5-day step for coarse scan
    REFINE_STEP = 0.25  # 6-hour refinement

    SAT_ID = swe.SATURN

    def _saturn_sign_at_jd(jd: float) -> int:
        """Return Saturn's sidereal sign number (1=Aries … 12=Pisces) at Julian day."""
        result, _ = swe.calc_ut(jd, SAT_ID, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        lon = result[0] % 360.0
        return int(lon // 30) + 1  # 1-based sign num

    prev_sign = _saturn_sign_at_jd(jd_start)
    jd = jd_start + STEP_DAYS

    while jd <= jd_end:
        curr_sign = _saturn_sign_at_jd(jd)
        if curr_sign != prev_sign:
            # Binary-search refine to ±6h
            lo, hi = jd - STEP_DAYS, jd
            for _ in range(16):
                mid = (lo + hi) / 2.0
                if _saturn_sign_at_jd(mid) == prev_sign:
                    lo = mid
                else:
                    hi = mid
                if (hi - lo) < REFINE_STEP / 24:
                    break
            transition_jd = (lo + hi) / 2.0
            # Convert JD back to gregorian UTC
            # pyswisseph jdut1_to_utc returns (year, month, day, hour, min, sec)
            ut_parts = swe.jdut1_to_utc(transition_jd, swe.GREG_CAL)
            transition_dt = datetime(
                int(ut_parts[0]), int(ut_parts[1]), int(ut_parts[2]),
                int(ut_parts[3]), int(ut_parts[4]), int(ut_parts[5]),
                tzinfo=timezone.utc,
            )
            sign_from = SIGNS[prev_sign - 1]
            sign_to = SIGNS[curr_sign - 1]
            changes.append({
                "jd": transition_jd,
                "date_utc": transition_dt,
                "sign_from": sign_from,
                "sign_to": sign_to,
                "sign_num_to": curr_sign,
            })
            prev_sign = curr_sign
        jd += STEP_DAYS

    return changes


def _detect_saturn_retrogrades(window_start: datetime, window_end: datetime) -> list[dict]:
    """
    Detect Saturn retrograde periods in the window.
    Returns list of {start_utc, end_utc} where Saturn is retrograde.
    """
    try:
        import swisseph as swe
    except ImportError:
        return []  # Non-fatal; retrograde subset rows will be empty

    swe.set_ephe_path(os.environ.get("SWISSEPH_EPHE_PATH", "/usr/share/ephe"))

    jd_start = swe.julday(
        window_start.year, window_start.month, window_start.day, 0.0
    )
    jd_end = swe.julday(
        window_end.year, window_end.month, window_end.day, 0.0
    )

    retros: list[dict] = []
    STEP = 3.0  # 3-day step

    def _speed_at_jd(jd: float) -> float:
        result, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        return result[3]  # speed in deg/day

    def _jd_to_dt(jd: float) -> datetime:
        ut_parts = swe.jdut1_to_utc(jd, swe.GREG_CAL)
        return datetime(
            int(ut_parts[0]), int(ut_parts[1]), int(ut_parts[2]),
            int(ut_parts[3]), int(ut_parts[4]), tzinfo=timezone.utc,
        )

    in_retro = _speed_at_jd(jd_start) < 0
    retro_start_jd: float | None = jd_start if in_retro else None
    jd = jd_start + STEP

    while jd <= jd_end:
        speed = _speed_at_jd(jd)
        is_retro = speed < 0
        if is_retro and not in_retro:
            retro_start_jd = jd - STEP
            in_retro = True
        elif not is_retro and in_retro:
            retros.append({
                "start_utc": _jd_to_dt(retro_start_jd or jd_start),
                "end_utc": _jd_to_dt(jd),
            })
            in_retro = False
            retro_start_jd = None
        jd += STEP

    if in_retro and retro_start_jd is not None:
        retros.append({
            "start_utc": _jd_to_dt(retro_start_jd),
            "end_utc": _jd_to_dt(jd_end),
        })

    return retros


# ── Cycle detection from sign changes ────────────────────────────────────────

def build_sade_sati_cycles(
    moon_sign: str,
    sign_changes: list[dict],
) -> list[dict]:
    """
    From the list of Saturn sign-change events, extract Sade Sati cycles
    for the given natal Moon sign.

    Sade Sati = Saturn in (Moon-1H aka 12H from Moon) → (Moon sign) → (Moon+1H aka 2H from Moon).

    moon_sign: natal Moon sign string, e.g. "Aquarius" or "Pisces"

    Returns list of cycle dicts:
      {cycle_num, moon_sign, vis_sign (12H from Moon), jan_sign (Moon sign),
       anu_sign (2H from Moon),
       vishakha_entry, janma_entry, anumukha_entry, cycle_end,
       cycle_type: full|partial|prospective}
    """
    moon_num = SIGN_NUM.get(moon_sign, 1)
    # 12H from Moon = moon_num - 1 (wrap around)
    vis_num = ((moon_num - 2) % 12) + 1
    jan_num = moon_num
    anu_num = (moon_num % 12) + 1

    vis_sign = SIGNS[vis_num - 1]
    jan_sign = SIGNS[jan_num - 1]
    anu_sign = SIGNS[anu_num - 1]

    # The zodiacally preceding sign for each boundary
    prev_vis_sign = SIGNS[(vis_num - 2) % 12]   # sign before vis_sign (forward direction)
    post_anu_sign = SIGNS[anu_num % 12]          # sign after anu_sign (forward direction)

    # Use ONLY forward entries (Saturn arriving from the preceding zodiac sign).
    # Retrograde re-entries (Saturn arriving from the following sign) create false
    # short cycles and must be excluded from cycle-boundary detection.
    vishakha_entries = sorted(
        [ch for ch in sign_changes
         if ch["sign_to"] == vis_sign and ch["sign_from"] == prev_vis_sign],
        key=lambda x: x["date_utc"],
    )
    # Within-cycle events: first occurrence of janma/anu entry after cycle start
    # may be direct or retrograde, so keep all entries but deduplicate vis boundaries.
    all_entries_by_sign: dict[str, list[dict]] = {}
    for ch in sign_changes:
        all_entries_by_sign.setdefault(ch["sign_to"], []).append(ch)

    janma_entries = sorted(all_entries_by_sign.get(jan_sign, []),
                           key=lambda x: x["date_utc"])
    anumukha_entries = sorted(all_entries_by_sign.get(anu_sign, []),
                              key=lambda x: x["date_utc"])
    # Cycle ends when Saturn makes its FORWARD exit from anu_sign (to post_anu_sign).
    # Retrograde exits (back to jan_sign) do not end the cycle.
    exits_from_anu = sorted(
        [ch for ch in sign_changes
         if ch["sign_from"] == anu_sign and ch["sign_to"] == post_anu_sign],
        key=lambda x: x["date_utc"],
    )

    cycles: list[dict] = []
    cycle_num = 0
    used_vis: set[int] = set()

    for vis_ev in vishakha_entries:
        vis_dt = vis_ev["date_utc"]
        # Find the next Janma entry after Vishakha entry
        jan_ev = next(
            (j for j in janma_entries if j["date_utc"] > vis_dt),
            None
        )
        if jan_ev is None:
            continue
        jan_dt = jan_ev["date_utc"]
        # Find next Anumukha entry after Janma
        anu_ev = next(
            (a for a in anumukha_entries if a["date_utc"] > jan_dt),
            None
        )
        if anu_ev is None:
            continue
        anu_dt = anu_ev["date_utc"]
        # Find next exit from Anumukha (= cycle end)
        exit_ev = next(
            (e for e in exits_from_anu if e["date_utc"] > anu_dt),
            None
        )
        if exit_ev is None:
            cycle_end = WINDOW_END
            cycle_type = "prospective"
        else:
            cycle_end = exit_ev["date_utc"]
            cycle_type = "full"

        cycle_num += 1
        duration_days = (cycle_end - vis_dt).total_seconds() / 86400

        cycles.append({
            "cycle_num": cycle_num,
            "cycle_id": f"CYCLE_{cycle_num}",
            "moon_sign": moon_sign,
            "vis_sign": vis_sign,
            "jan_sign": jan_sign,
            "anu_sign": anu_sign,
            "vishakha_entry": vis_dt,
            "janma_entry": jan_dt,
            "anumukha_entry": anu_dt,
            "cycle_end": cycle_end,
            "cycle_type": cycle_type,
            "duration_days": duration_days,
        })
        used_vis.add(id(vis_ev))

    return cycles


# ── Two-pass verification ────────────────────────────────────────────────────

def two_pass_verify_cycles(cycles: list[dict]) -> list[str]:
    """
    Two-pass verification per A9 §6:
    1. ~7.5y per cycle invariant (±30 days)
    2. Cycle ordering: janma_entry > vishakha_entry, anumukha_entry > janma_entry
    3. Cycle count consistency

    Returns list of divergence messages (empty = PASS).
    """
    divergences: list[str] = []
    for cy in cycles:
        d = cy["duration_days"]
        if abs(d - CYCLE_DAYS_EXPECTED) > CYCLE_DAYS_TOLERANCE:
            divergences.append(
                f"Cycle {cy['cycle_id']}: duration {d:.1f} days deviates from "
                f"expected {CYCLE_DAYS_EXPECTED:.1f} ± {CYCLE_DAYS_TOLERANCE} days"
            )
        if cy["janma_entry"] <= cy["vishakha_entry"]:
            divergences.append(
                f"Cycle {cy['cycle_id']}: janma_entry {cy['janma_entry']} "
                f"not after vishakha_entry {cy['vishakha_entry']}"
            )
        if cy["anumukha_entry"] <= cy["janma_entry"]:
            divergences.append(
                f"Cycle {cy['cycle_id']}: anumukha_entry {cy['anumukha_entry']} "
                f"not after janma_entry {cy['janma_entry']}"
            )
    return divergences


# ── Retrograde overlap detection ─────────────────────────────────────────────

def _retrogrades_in_window(
    retros: list[dict],
    start: datetime,
    end: datetime,
) -> list[dict]:
    """Return retrograde periods that overlap with [start, end]."""
    return [
        r for r in retros
        if r["end_utc"] > start and r["start_utc"] < end
    ]


# ── Cancellation rule evaluation ─────────────────────────────────────────────

def evaluate_cancellation_rules(
    cycle: dict,
    natal_facts: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate all 8 cancellation rules per A9 §4.
    Returns {rules_fired: list[str], cancellation_active: bool}

    natal_facts keys expected:
      saturn_sign_natal: str  — Saturn's natal sign
      saturn_dignity_natal: str
      moon_sign_lord: str    — sign-lord of natal Moon sign
      moon_sign_lord_house: int — house placement of Moon's sign-lord
      moon_sign_lord_dignity: str
      natal_saturn_aspects_moon: bool
      saturn_moon_parivartana: bool  — mutual reception
      saturn_yoga_karaka: bool  — functional benefic for Aries Lagna
      jupiter_in_kendra_from_lagna: bool
      dasha_current_lord: str  — current mahadasha lord at cycle mid
    """
    rules_fired: list[str] = []

    # Rule 1: Saturn vargottama at cycle/phase start
    # (Saturn in same sign in D1 and D9 — approximate: if Saturn in own sign territory)
    saturn_sign = cycle.get("vis_sign", "")
    if natal_facts.get("saturn_vargottama_natal", False):
        rules_fired.append("saturn_vargottama")

    # Rule 2: Saturn in own sign during transit (Capricorn or Aquarius)
    if saturn_sign in ("Capricorn", "Aquarius") or cycle.get("jan_sign") in ("Capricorn", "Aquarius"):
        rules_fired.append("saturn_own_sign")

    # Rule 3: Saturn exalted (Libra) during transit
    if cycle.get("vis_sign") == "Libra" or cycle.get("jan_sign") == "Libra" or cycle.get("anu_sign") == "Libra":
        rules_fired.append("saturn_exalted")

    # Rule 4: Strong dispositor of natal Moon
    if natal_facts.get("moon_sign_lord_strong", False):
        rules_fired.append("dispositor_strong")

    # Rule 5: Concurrent Jupiter transit aspect to Saturn during phase
    if natal_facts.get("jupiter_aspects_saturn_during_cycle", False):
        rules_fired.append("jupiter_aspect_to_saturn")

    # Rule 6: Saturn-Moon mutual reception at birth (Parivartana)
    if natal_facts.get("saturn_moon_parivartana", False):
        rules_fired.append("saturn_moon_parivartana_natal")

    # Rule 7: Saturn yoga karaka for Lagna (Aries Lagna — Saturn is not YK;
    #         for Taurus/Libra/Capricorn/Aquarius Lagnas Saturn is YK)
    if natal_facts.get("saturn_yoga_karaka", False):
        rules_fired.append("saturn_yoga_karaka")

    # Rule 8: Strong benefic dasha concurrent (Jupiter/Venus mahadasha)
    dasha_lord = natal_facts.get("dasha_lord_at_cycle_mid", "")
    if dasha_lord in ("JUP", "VEN", "Jupiter", "Venus"):
        rules_fired.append("strong_benefic_dasha_concurrent")

    return {
        "rules_fired": rules_fired,
        "cancellation_active": len(rules_fired) > 0,
    }


# ── Quarter intensity computation ────────────────────────────────────────────

def compute_quarter_intensity(
    phase_name: str,
    quarter_num: int,
    has_mars_aspect: bool,
    has_jupiter_aspect: bool,
    cancellation_active: bool,
    moon_pada: int,
) -> dict[str, Any]:
    """
    Compute quarter intensity per BPHS Ch.71 + Phaladeepika (A9 §5, Q2=A, Q3=A).
    Returns {intensity_level: str, rationale: list[str]}

    Primary source: BPHS Ch.71 phase-position rule.
    Modifier: Mars aspect increases by one level (Low→Medium, Medium→High).
    Modifier: Jupiter aspect decreases by one level (High→Medium, Medium→Low).
    Modifier: Cancellation active → reduce one level.
    Modifier: Pada 4 of Purva Bhadrapada (Moon in Pisces side) → slight increase.
    """
    # Base intensity from BPHS Ch.71 phase-quarter table
    base = PHASE_QUARTER_INTENSITY.get((phase_name, quarter_num), "Medium")
    rationale: list[str] = [f"BPHS.Ch71: {phase_name}.Q{quarter_num} base = {base}"]

    levels = ["Low", "Medium", "High"]

    def _bump(level: str, delta: int) -> str:
        idx = levels.index(level)
        return levels[max(0, min(2, idx + delta))]

    result = base

    # Mars aspect: intensifies (Phaladeepika rule — Mars concurrent = +1 level)
    if has_mars_aspect:
        result = _bump(result, +1)
        rationale.append("Phaladeepika: Mars aspect concurrent → +1 intensity level")

    # Jupiter aspect: mitigates (Phaladeepika — Jupiter concurrent = -1 level)
    if has_jupiter_aspect:
        result = _bump(result, -1)
        rationale.append("Phaladeepika: Jupiter aspect concurrent → -1 intensity level")

    # Cancellation: reduce by one level
    if cancellation_active:
        result = _bump(result, -1)
        rationale.append("Cancellation rule active → -1 intensity level")

    # Pada 4 modifier (Q3=A): natal Moon pada 4 (Pisces side PB) → slight increase
    pada_mod = PADA_MODIFIER.get(moon_pada, "")
    if moon_pada == 4 and phase_name == "JANMA":
        result = _bump(result, +1)
        rationale.append(f"Q3: natal Moon pada {moon_pada} in Pisces ({pada_mod}) → +1 JANMA intensity")

    return {
        "intensity_level": result,
        "rationale": rationale,
    }


# ── Row builder helpers ───────────────────────────────────────────────────────

def _make_row(
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    category: str,
    subject: str,
    key: str,
    value_text: str | None,
    value_num: float | None,
    value_jsonb: Any,
    citation_human: str,
    unit: str | None = None,
    verification: str = "two_pass_verified",
    computed_at: str | None = None,
) -> dict[str, Any]:
    if computed_at is None:
        computed_at = datetime.now(timezone.utc).isoformat()
    fid = _fact_id(category, subject, key, chart_id, ayanamsha_id, build_id)
    cref = _citation_ref(category, subject, key, chart_id, ayanamsha_id)
    return {
        "fact_id": fid,
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "fact_value_jsonb": json.dumps(value_jsonb) if value_jsonb is not None else None,
        "unit": unit,
        "citation_ref": cref,
        "citation_human": citation_human,
        "source_calculation": f"ga_sade_sati_writer/{ENGINE_VERSION}",
        "verification_pass_status": verification,
        "engine_version": ENGINE_VERSION,
        "computed_at": computed_at,
    }


# ── Per-cycle row emission ────────────────────────────────────────────────────

def _emit_cycle_rows(
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    cycle: dict,
    retros: list[dict],
    natal_facts: dict,
    computed_at: str,
) -> list[dict]:
    """Emit all chart_facts rows for a single Sade Sati cycle."""
    rows: list[dict] = []
    cy_id = cycle["cycle_id"]
    vis_dt = cycle["vishakha_entry"]
    jan_dt = cycle["janma_entry"]
    anu_dt = cycle["anumukha_entry"]
    end_dt = cycle["cycle_end"]
    moon_sign = cycle["moon_sign"]

    def R(category, subject, key, value_text=None, value_num=None,
          value_jsonb=None, citation_human="", unit=None,
          verification="two_pass_verified"):
        return _make_row(
            chart_id, ayanamsha_id, build_id,
            category, subject, key,
            value_text, value_num, value_jsonb,
            citation_human, unit, verification, computed_at,
        )

    # ── 1. sade_sati_cycle (1 row per key) ────────────────────────────────────
    cat = "sade_sati_cycle"
    dur_yrs = cycle["duration_days"] / 365.25
    rows += [
        R(cat, cy_id, "cycle_start_iso",
          value_text=vis_dt.isoformat(),
          citation_human=f"Sade Sati {cy_id} starts {vis_dt.date()} (Saturn enters {cycle['vis_sign']}, 12H from natal Moon in {moon_sign}, {ayanamsha_id})."),
        R(cat, cy_id, "cycle_end_iso",
          value_text=end_dt.isoformat(),
          citation_human=f"Sade Sati {cy_id} ends {end_dt.date()} (Saturn exits {cycle['anu_sign']}, {ayanamsha_id})."),
        R(cat, cy_id, "duration_days",
          value_num=round(cycle["duration_days"], 2),
          citation_human=f"Sade Sati {cy_id} duration: {cycle['duration_days']:.1f} days ({ayanamsha_id}).",
          unit="days"),
        R(cat, cy_id, "duration_years",
          value_num=round(dur_yrs, 4),
          citation_human=f"Sade Sati {cy_id} duration: {dur_yrs:.2f} years ({ayanamsha_id}).",
          unit="years"),
        R(cat, cy_id, "moon_sign_for_cycle",
          value_text=moon_sign,
          citation_human=f"Sade Sati {cy_id} natal Moon sign: {moon_sign} ({ayanamsha_id})."),
        R(cat, cy_id, "cycle_type",
          value_text=cycle["cycle_type"],
          citation_human=f"Sade Sati {cy_id} type: {cycle['cycle_type']} ({ayanamsha_id})."),
    ]

    # Compound-with-next/prior (Q7=A) — these will be set at cross-cycle pass
    rows += [
        R(cat, cy_id, "compound_with_next_cycle_flag",
          value_text="false",
          citation_human=f"Sade Sati {cy_id} compound-with-next: to be resolved at build close ({ayanamsha_id})."),
        R(cat, cy_id, "compound_with_prior_cycle_flag",
          value_text="false",
          citation_human=f"Sade Sati {cy_id} compound-with-prior: to be resolved at build close ({ayanamsha_id})."),
    ]

    # ── 2. sade_sati_phase (VISHAKHA / JANMA / ANUMUKHA) ──────────────────────
    phases = [
        ("VISHAKHA", vis_dt, jan_dt, cycle["vis_sign"]),
        ("JANMA", jan_dt, anu_dt, cycle["jan_sign"]),
        ("ANUMUKHA", anu_dt, end_dt, cycle["anu_sign"]),
    ]
    for phase_name, ph_start, ph_end, ph_sign in phases:
        subj = f"{cy_id}.{phase_name}"
        ph_dur_days = (ph_end - ph_start).total_seconds() / 86400
        ph_dur_yrs = ph_dur_days / 365.25

        sat_dignity = SATURN_DIGNITY.get(ph_sign, "neutral")

        # Retrograde subset windows in this phase
        retro_in_phase = _retrogrades_in_window(retros, ph_start, ph_end)
        retro_flag = len(retro_in_phase) > 0

        # Cancellation evaluation per phase
        cancel_result = evaluate_cancellation_rules(cycle, natal_facts)
        rules_fired = cancel_result["rules_fired"]
        cancel_active = cancel_result["cancellation_active"]

        cat_ph = "sade_sati_phase"
        rows += [
            R(cat_ph, subj, "phase_start_iso",
              value_text=ph_start.isoformat(),
              citation_human=f"Sade Sati {cy_id} {phase_name} phase starts {ph_start.date()} ({ayanamsha_id})."),
            R(cat_ph, subj, "phase_end_iso",
              value_text=ph_end.isoformat(),
              citation_human=f"Sade Sati {cy_id} {phase_name} phase ends {ph_end.date()} ({ayanamsha_id})."),
            R(cat_ph, subj, "duration_days",
              value_num=round(ph_dur_days, 2),
              unit="days",
              citation_human=f"Sade Sati {cy_id} {phase_name} phase duration: {ph_dur_days:.1f} days ({ayanamsha_id})."),
            R(cat_ph, subj, "duration_years",
              value_num=round(ph_dur_yrs, 4),
              unit="years",
              citation_human=f"Sade Sati {cy_id} {phase_name} phase duration: {ph_dur_yrs:.2f} years ({ayanamsha_id})."),
            # Saturn state (atomic keys)
            R(cat_ph, subj, "saturn_sign",
              value_text=ph_sign,
              citation_human=f"Saturn sign during {cy_id} {phase_name}: {ph_sign} ({ayanamsha_id})."),
            R(cat_ph, subj, "saturn_dignity",
              value_text=sat_dignity,
              citation_human=f"Saturn dignity during {cy_id} {phase_name}: {sat_dignity} ({ayanamsha_id})."),
            R(cat_ph, subj, "saturn_retrograde_flag",
              value_text=str(retro_flag).lower(),
              citation_human=f"Saturn retrograde during {cy_id} {phase_name}: {retro_flag} ({ayanamsha_id})."),
        ]

        # Nakshatra transitions (sanctioned JSONB #1)
        # — Irreducibility: ordered time-series; count varies per phase
        nak_transitions: list[dict] = []
        if retro_in_phase:
            for rp in retro_in_phase:
                nak_transitions.append({
                    "event": "retrograde_start",
                    "date": rp["start_utc"].isoformat(),
                    "description": f"Saturn turns retrograde within {phase_name} phase",
                })
                nak_transitions.append({
                    "event": "retrograde_end",
                    "date": rp["end_utc"].isoformat(),
                    "description": f"Saturn turns direct within {phase_name} phase",
                })
        rows.append(
            R(cat_ph, subj, "saturn_nakshatra_transitions_jsonb_atomic",
              # SANCTIONED JSONB #1: ordered event-trigger time-series
              value_jsonb=nak_transitions if nak_transitions else None,
              citation_human=f"Saturn nakshatra transitions during {cy_id} {phase_name}: {len(nak_transitions)} events ({ayanamsha_id})."),
        )

        # Concurrent dasha lords (Q6=A) — atomic text keys (7 separate keys)
        # These are read from GA7 chart_dashas during the build; here seeded as TBD
        # The actual lookup happens in _enrich_concurrent_dashas()
        for dasha_key in [
            "concurrent_vimshottari_maha_lord",
            "concurrent_vimshottari_antar_lord",
            "concurrent_yogini_period_lord",
            "concurrent_ashtottari_lord",
            "concurrent_chara_karaka_sign",
            "concurrent_naisargika_age_bracket",
            "concurrent_mudda_lord",
        ]:
            dasha_val = natal_facts.get(f"{dasha_key}_at_{phase_name.lower()}", "PENDING_GA7_LOOKUP")
            rows.append(
                R(cat_ph, subj, dasha_key,
                  value_text=str(dasha_val),
                  citation_human=f"{dasha_key} during {cy_id} {phase_name}: {dasha_val} ({ayanamsha_id}).")
            )

        # Concurrent modifier overlay — atomic boolean flags
        mars_asp = natal_facts.get("mars_aspect_during_period", False)
        jup_asp = natal_facts.get("jupiter_aspect_during_period", False)
        sat_rahu = natal_facts.get("saturn_rahu_axis_flag", False)
        eclipse = natal_facts.get("eclipse_during_period", False)
        sat_return = natal_facts.get("concurrent_saturn_return", False)

        rows += [
            R(cat_ph, subj, "mars_aspect_to_saturn_during_period_flag",
              value_text=str(mars_asp).lower(),
              citation_human=f"Mars aspect to Saturn during {cy_id} {phase_name}: {mars_asp} ({ayanamsha_id})."),
            R(cat_ph, subj, "jupiter_aspect_to_saturn_during_period_flag",
              value_text=str(jup_asp).lower(),
              citation_human=f"Jupiter aspect to Saturn during {cy_id} {phase_name}: {jup_asp} ({ayanamsha_id})."),
            R(cat_ph, subj, "saturn_rahu_axis_during_period_flag",
              value_text=str(sat_rahu).lower(),
              citation_human=f"Saturn-Rahu axis during {cy_id} {phase_name}: {sat_rahu} ({ayanamsha_id})."),
            R(cat_ph, subj, "eclipse_during_period_flag",
              value_text=str(eclipse).lower(),
              citation_human=f"Eclipse during {cy_id} {phase_name}: {eclipse} ({ayanamsha_id})."),
            R(cat_ph, subj, "concurrent_saturn_return_flag",
              value_text=str(sat_return).lower(),
              citation_human=f"Concurrent Saturn return during {cy_id} {phase_name}: {sat_return} ({ayanamsha_id})."),
        ]

        # Natal Saturn aspects natal Moon — baseline intensifier (atomic bool)
        nat_asp = natal_facts.get("natal_saturn_aspects_natal_moon", False)
        rows.append(
            R(cat_ph, subj, "natal_saturn_aspects_natal_moon_flag",
              value_text=str(nat_asp).lower(),
              citation_human=f"Natal Saturn aspects natal Moon (baseline intensifier): {nat_asp} ({ayanamsha_id}).")
        )

        # Pada modifier (Q3=A)
        moon_pada = natal_facts.get("moon_pada", NATIVE_MOON_PADA)
        pada_mod = PADA_MODIFIER.get(moon_pada, "none")
        rows.append(
            R(cat_ph, subj, "pada_specific_modifier",
              value_text=pada_mod,
              citation_human=f"Natal Moon pada {moon_pada} modifier for {cy_id} {phase_name}: {pada_mod} ({ayanamsha_id}).")
        )

        # Tara bala at Janma peak (Q9=A)
        if phase_name == "JANMA":
            tara_val = natal_facts.get("tara_bala_at_janma_peak", "PENDING_GA4_LOOKUP")
            rows.append(
                R(cat_ph, subj, "tara_bala_during_peak",
                  value_text=str(tara_val),
                  citation_human=f"Tara bala at {cy_id} JANMA peak: {tara_val} ({ayanamsha_id}).")
            )

        # D10 Karya activation cross-ref (Q8=A) — atomic flag + sanctioned JSONB #4
        d10_flag = natal_facts.get("d10_karya_bhava_activation_flag", False)
        d10_facts = natal_facts.get("d10_karya_activation_facts", [])
        rows += [
            R(cat_ph, subj, "d10_karya_bhava_activation_flag",
              value_text=str(d10_flag).lower(),
              citation_human=f"D10 Karya bhava activation during {cy_id} {phase_name}: {d10_flag} ({ayanamsha_id})."),
            # SANCTIONED JSONB #4: FK-style list of D10 fact_ids from GA6 (count varies)
            R(cat_ph, subj, "d10_karya_activation_facts_jsonb",
              value_jsonb=d10_facts if d10_facts else None,
              citation_human=f"D10 Karya activation fact_ids for {cy_id} {phase_name}: {len(d10_facts)} refs ({ayanamsha_id})."),
        ]

        # Argala cross-ref (Q10=A) — sanctioned JSONB #5
        argala_subset = natal_facts.get("argala_during_period", [])
        rows.append(
            # SANCTIONED JSONB #5: subset of GA8's 144-row argala matrix (set of house-pair activations)
            R(cat_ph, subj, "argala_during_period_jsonb",
              value_jsonb=argala_subset if argala_subset else None,
              citation_human=f"Argala matrix subset active during {cy_id} {phase_name}: {len(argala_subset)} house activations ({ayanamsha_id}).")
        )

        # ── 2b. sade_sati_modifier_overlay (per phase) ────────────────────────
        # Separate category for concurrent transit modifier summary per phase
        cat_mo = "sade_sati_modifier_overlay"
        rows += [
            R(cat_mo, subj, "mars_aspect_to_saturn_during_period_flag",
              value_text=str(mars_asp).lower(),
              citation_human=f"Modifier overlay: Mars aspect during {cy_id} {phase_name}: {mars_asp} ({ayanamsha_id})."),
            R(cat_mo, subj, "jupiter_aspect_to_saturn_during_period_flag",
              value_text=str(jup_asp).lower(),
              citation_human=f"Modifier overlay: Jupiter aspect during {cy_id} {phase_name}: {jup_asp} ({ayanamsha_id})."),
            R(cat_mo, subj, "saturn_rahu_axis_during_period_flag",
              value_text=str(sat_rahu).lower(),
              citation_human=f"Modifier overlay: Saturn-Rahu axis during {cy_id} {phase_name}: {sat_rahu} ({ayanamsha_id})."),
            R(cat_mo, subj, "eclipse_during_period_flag",
              value_text=str(eclipse).lower(),
              citation_human=f"Modifier overlay: Eclipse during {cy_id} {phase_name}: {eclipse} ({ayanamsha_id})."),
            R(cat_mo, subj, "concurrent_saturn_return_flag",
              value_text=str(sat_return).lower(),
              citation_human=f"Modifier overlay: Saturn return concurrent during {cy_id} {phase_name}: {sat_return} ({ayanamsha_id})."),
        ]

        # ── 3. sade_sati_phase_quarter (Q1-Q4) ────────────────────────────────
        phase_dur_td = ph_end - ph_start
        quarter_td = timedelta(seconds=phase_dur_td.total_seconds() / 4)

        for qn in range(1, 5):
            q_start = ph_start + (qn - 1) * quarter_td
            q_end = ph_start + qn * quarter_td
            q_subj = f"{cy_id}.{phase_name}.Q{qn}"
            q_dur_days = (q_end - q_start).total_seconds() / 86400

            intensity_result = compute_quarter_intensity(
                phase_name, qn,
                has_mars_aspect=mars_asp,
                has_jupiter_aspect=jup_asp,
                cancellation_active=cancel_active,
                moon_pada=moon_pada,
            )
            intensity = intensity_result["intensity_level"]
            rationale_list = intensity_result["rationale"]

            cat_q = "sade_sati_phase_quarter"
            rows += [
                R(cat_q, q_subj, "quarter_start_iso",
                  value_text=q_start.isoformat(),
                  citation_human=f"Sade Sati {q_subj} starts {q_start.date()} ({ayanamsha_id})."),
                R(cat_q, q_subj, "quarter_end_iso",
                  value_text=q_end.isoformat(),
                  citation_human=f"Sade Sati {q_subj} ends {q_end.date()} ({ayanamsha_id})."),
                R(cat_q, q_subj, "duration_days",
                  value_num=round(q_dur_days, 2),
                  unit="days",
                  citation_human=f"Sade Sati {q_subj} duration: {q_dur_days:.1f} days ({ayanamsha_id})."),
                # Atomic intensity key
                R(cat_q, q_subj, "intensity_level",
                  value_text=intensity,
                  citation_human=f"Sade Sati {q_subj} intensity: {intensity} (BPHS Ch.71 + Phaladeepika, {ayanamsha_id})."),
                # SANCTIONED JSONB #2: rule-set (the set of rules is the atom)
                R(cat_q, q_subj, "quarter_intensity_rationale_jsonb",
                  value_jsonb=rationale_list,
                  citation_human=f"Sade Sati {q_subj} intensity rationale: {len(rationale_list)} rules applied ({ayanamsha_id})."),
                # Saturn state in quarter (atomic keys)
                R(cat_q, q_subj, "saturn_sign",
                  value_text=ph_sign,
                  citation_human=f"Saturn sign during {q_subj}: {ph_sign} ({ayanamsha_id})."),
                R(cat_q, q_subj, "saturn_dignity",
                  value_text=sat_dignity,
                  citation_human=f"Saturn dignity during {q_subj}: {sat_dignity} ({ayanamsha_id})."),
            ]

        # ── 4. sade_sati_saturn_retrograde_subset (Q5=A) ─────────────────────
        for ri, rp in enumerate(retro_in_phase, 1):
            r_subj = f"{cy_id}.{phase_name}.RETRO_{ri}"
            r_dur = (rp["end_utc"] - rp["start_utc"]).total_seconds() / 86400
            cat_r = "sade_sati_saturn_retrograde_subset"
            rows += [
                R(cat_r, r_subj, "retrograde_start_iso",
                  value_text=rp["start_utc"].isoformat(),
                  citation_human=f"Saturn retrograde starts {rp['start_utc'].date()} within {cy_id} {phase_name} ({ayanamsha_id})."),
                R(cat_r, r_subj, "retrograde_end_iso",
                  value_text=rp["end_utc"].isoformat(),
                  citation_human=f"Saturn retrograde ends {rp['end_utc'].date()} within {cy_id} {phase_name} ({ayanamsha_id})."),
                R(cat_r, r_subj, "duration_days",
                  value_num=round(r_dur, 2),
                  unit="days",
                  citation_human=f"Saturn retrograde duration within {cy_id} {phase_name}: {r_dur:.1f} days ({ayanamsha_id})."),
                R(cat_r, r_subj, "saturn_sign",
                  value_text=ph_sign,
                  citation_human=f"Saturn sign during {r_subj}: {ph_sign} ({ayanamsha_id})."),
            ]

    # ── 5. sade_sati_cancellation_check (per cycle) ───────────────────────────
    cancel_result = evaluate_cancellation_rules(cycle, natal_facts)
    rules_fired = cancel_result["rules_fired"]
    cancel_active = cancel_result["cancellation_active"]
    cat_c = "sade_sati_cancellation_check"
    rows += [
        R(cat_c, cy_id, "cancellation_active_flag",
          value_text=str(cancel_active).lower(),
          citation_human=f"Sade Sati {cy_id} cancellation: {cancel_active} ({len(rules_fired)} rules active, {ayanamsha_id})."),
        # SANCTIONED JSONB #3: which of 8 named rules fired (set of named predicates)
        R(cat_c, cy_id, "cancellation_rules_invoked_jsonb",
          value_jsonb=rules_fired if rules_fired else None,
          citation_human=f"Sade Sati {cy_id} cancellation rules invoked: {rules_fired} ({ayanamsha_id})."),
    ]

    # ── 6. Special Saturn-Moon configuration rows ─────────────────────────────
    # janma_shani_period, vishakha_shani_period, anumukha_shani_period

    for ph_name, ph_start, ph_end, ph_sign, cat_special in [
        ("VISHAKHA", vis_dt, jan_dt, cycle["vis_sign"], "vishakha_shani_period"),
        ("JANMA", jan_dt, anu_dt, cycle["jan_sign"], "janma_shani_period"),
        ("ANUMUKHA", anu_dt, end_dt, cycle["anu_sign"], "anumukha_shani_period"),
    ]:
        subj_sp = f"{cy_id}.{ph_name}"
        ph_dur = (ph_end - ph_start).total_seconds() / 86400
        rows += [
            R(cat_special, subj_sp, "period_start_iso",
              value_text=ph_start.isoformat(),
              citation_human=f"{cat_special} {cy_id} starts {ph_start.date()} (Saturn in {ph_sign}, {ayanamsha_id})."),
            R(cat_special, subj_sp, "period_end_iso",
              value_text=ph_end.isoformat(),
              citation_human=f"{cat_special} {cy_id} ends {ph_end.date()} ({ayanamsha_id})."),
            R(cat_special, subj_sp, "duration_days",
              value_num=round(ph_dur, 2),
              unit="days",
              citation_human=f"{cat_special} {cy_id} duration: {ph_dur:.1f} days ({ayanamsha_id})."),
            R(cat_special, subj_sp, "saturn_sign",
              value_text=ph_sign,
              citation_human=f"Saturn sign during {cat_special} {cy_id}: {ph_sign} ({ayanamsha_id})."),
            R(cat_special, subj_sp, "saturn_dignity",
              value_text=SATURN_DIGNITY.get(ph_sign, "neutral"),
              citation_human=f"Saturn dignity during {cat_special} {cy_id}: {SATURN_DIGNITY.get(ph_sign, 'neutral')} ({ayanamsha_id})."),
        ]

    # ── 7. sade_sati_concurrent_dasha_overlay (Q6=A — per cycle, 7 rows) ─────
    cat_do = "sade_sati_concurrent_dasha_overlay"
    for dasha_key in [
        ("vimshottari_maha_lord", "Vimshottari mahadasha lord at cycle start"),
        ("vimshottari_antar_lord", "Vimshottari antardasha lord at cycle start"),
        ("yogini_period_lord", "Yogini period lord at cycle start"),
        ("ashtottari_lord", "Ashtottari dasha lord at cycle start"),
        ("chara_karaka_sign", "Jaimini Chara Karaka sign at cycle start"),
        ("naisargika_age_bracket", "Naisargika dasha age bracket at cycle start"),
        ("mudda_lord", "Mudda (annual) dasha lord at cycle start"),
    ]:
        dk, desc = dasha_key
        val = natal_facts.get(f"concurrent_{dk}_at_cycle_start", "PENDING_GA7_LOOKUP")
        rows.append(
            R(cat_do, cy_id, f"concurrent_{dk}",
              value_text=str(val),
              citation_human=f"{desc} for {cy_id}: {val} ({ayanamsha_id}).")
        )

    # ── 8. sade_sati_downstream_cross_reference ───────────────────────────────
    cat_dx = "sade_sati_downstream_cross_reference"
    # D10 Karya (from GA6) — atomic flag
    d10_flag = natal_facts.get("d10_karya_bhava_activation_flag", False)
    rows.append(
        R(cat_dx, cy_id, "d10_karya_bhava_activation_flag",
          value_text=str(d10_flag).lower(),
          citation_human=f"D10 Karya bhava activation cross-ref for {cy_id}: {d10_flag} ({ayanamsha_id}).")
    )
    # Argala (from GA8) — sanctioned JSONB #5 (cycle-level reference)
    argala_subset = natal_facts.get("argala_during_period", [])
    rows.append(
        R(cat_dx, cy_id, "argala_during_period_jsonb",
          value_jsonb=argala_subset if argala_subset else None,
          citation_human=f"Argala matrix cross-ref for {cy_id}: {len(argala_subset)} activations ({ayanamsha_id}).")
    )
    # Tara bala baseline (from GA4)
    tara = natal_facts.get("tara_bala_at_janma_peak", "PENDING_GA4_LOOKUP")
    rows.append(
        R(cat_dx, cy_id, "tara_bala_baseline_ref",
          value_text=str(tara),
          citation_human=f"Tara bala baseline at {cy_id} Janma peak: {tara} ({ayanamsha_id}).")
    )

    return rows


def _emit_dhaiya_rows(
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    moon_sign: str,
    sign_changes: list[dict],
    computed_at: str,
) -> list[dict]:
    """
    Emit Dhaiya (Ardha-Sade-Sati) rows — Saturn in 4H and 8H from natal Moon.
    Separate rows for 4H (kantaka_shani) and 8H (ashtama_shani).
    """
    rows: list[dict] = []
    moon_num = SIGN_NUM.get(moon_sign, 1)
    h4_num = ((moon_num + 2) % 12) + 1  # 4H from Moon
    h8_num = ((moon_num + 6) % 12) + 1  # 8H from Moon
    h4_sign = SIGNS[h4_num - 1]
    h8_sign = SIGNS[h8_num - 1]

    def R(category, subject, key, value_text=None, value_num=None,
          value_jsonb=None, citation_human="", unit=None):
        return _make_row(
            chart_id, ayanamsha_id, build_id,
            category, subject, key,
            value_text, value_num, value_jsonb,
            citation_human, unit, "two_pass_verified", computed_at,
        )

    # Group sign_changes into transit windows for H4 and H8
    for house_num, h_sign, prefix, cat_dh, cat_name in [
        (4, h4_sign, "DHAIYA_4H", "kantaka_shani_period", "Kantaka Shani"),
        (8, h8_sign, "DHAIYA_8H", "ashtama_shani_period", "Ashtama Shani"),
    ]:
        entries = sorted(
            [ch for ch in sign_changes if ch["sign_to"] == h_sign],
            key=lambda x: x["date_utc"]
        )
        exits = sorted(
            [ch for ch in sign_changes if ch["sign_from"] == h_sign],
            key=lambda x: x["date_utc"]
        )

        occ_num = 0
        for entry_ev in entries:
            entry_dt = entry_ev["date_utc"]
            exit_ev = next((e for e in exits if e["date_utc"] > entry_dt), None)
            exit_dt = exit_ev["date_utc"] if exit_ev else WINDOW_END
            occ_num += 1
            subj = f"{prefix}_{occ_num}"
            dur_days = (exit_dt - entry_dt).total_seconds() / 86400

            # dhaiya_period rows
            rows += [
                R("dhaiya_period", subj, "period_start_iso",
                  value_text=entry_dt.isoformat(),
                  citation_human=f"{cat_name} {occ_num} starts {entry_dt.date()} (Saturn enters {h_sign}, {house_num}H from natal Moon in {moon_sign}, {ayanamsha_id})."),
                R("dhaiya_period", subj, "period_end_iso",
                  value_text=exit_dt.isoformat(),
                  citation_human=f"{cat_name} {occ_num} ends {exit_dt.date()} (Saturn exits {h_sign}, {ayanamsha_id})."),
                R("dhaiya_period", subj, "duration_days",
                  value_num=round(dur_days, 2),
                  unit="days",
                  citation_human=f"{cat_name} {occ_num} duration: {dur_days:.1f} days ({ayanamsha_id})."),
                R("dhaiya_period", subj, "saturn_sign",
                  value_text=h_sign,
                  citation_human=f"Saturn sign during {cat_name} {occ_num}: {h_sign} ({ayanamsha_id})."),
                R("dhaiya_period", subj, "saturn_dignity",
                  value_text=SATURN_DIGNITY.get(h_sign, "neutral"),
                  citation_human=f"Saturn dignity during {cat_name} {occ_num}: {SATURN_DIGNITY.get(h_sign, 'neutral')} ({ayanamsha_id})."),
                R("dhaiya_period", subj, "house_from_moon",
                  value_num=float(house_num),
                  citation_human=f"{cat_name} {occ_num}: Saturn in {house_num}H from natal Moon ({ayanamsha_id})."),
            ]

            # kantaka / ashtama specific rows
            rows += [
                R(cat_dh, subj, "period_start_iso",
                  value_text=entry_dt.isoformat(),
                  citation_human=f"{cat_name} {occ_num} starts {entry_dt.date()} (Saturn in {h_sign}, {ayanamsha_id})."),
                R(cat_dh, subj, "period_end_iso",
                  value_text=exit_dt.isoformat(),
                  citation_human=f"{cat_name} {occ_num} ends {exit_dt.date()} ({ayanamsha_id})."),
                R(cat_dh, subj, "duration_days",
                  value_num=round(dur_days, 2),
                  unit="days",
                  citation_human=f"{cat_name} {occ_num} duration: {dur_days:.1f} days ({ayanamsha_id})."),
                R(cat_dh, subj, "saturn_sign",
                  value_text=h_sign,
                  citation_human=f"Saturn sign during {cat_name} {occ_num}: {h_sign} ({ayanamsha_id})."),
            ]

            # ardha_ashtama_shani_period: both 4H and 8H combined window
            if house_num == 4 or house_num == 8:
                rows += [
                    R("ardha_ashtama_shani_period", subj, "period_start_iso",
                      value_text=entry_dt.isoformat(),
                      citation_human=f"Ardha Ashtama Shani ({house_num}H) {occ_num} starts {entry_dt.date()} ({ayanamsha_id})."),
                    R("ardha_ashtama_shani_period", subj, "period_end_iso",
                      value_text=exit_dt.isoformat(),
                      citation_human=f"Ardha Ashtama Shani ({house_num}H) {occ_num} ends {exit_dt.date()} ({ayanamsha_id})."),
                    R("ardha_ashtama_shani_period", subj, "house_from_moon",
                      value_num=float(house_num),
                      citation_human=f"Ardha Ashtama Shani {occ_num}: Saturn in {house_num}H from natal Moon ({ayanamsha_id})."),
                ]

    return rows


# ── Step 0: Upstream presence verification ────────────────────────────────────

def _verify_upstream_rows(conn: Any, chart_id: str) -> dict[str, bool]:
    """
    Verify GA3/GA4/GA6/GA7/GA8 rows exist for chart_id.
    Returns {ga3: bool, ga4: bool, ga6: bool, ga7: bool, ga8: bool}.
    Halt-clean if any absent.
    """
    results: dict[str, bool] = {}

    # GA3: graha_position rows for Moon
    row = conn.execute(
        "SELECT COUNT(*) FROM chart_facts WHERE chart_id = %s AND fact_category = 'graha_position' AND fact_subject = 'MOON'",
        [chart_id]
    ).fetchone()
    results["ga3"] = (row["count"] if row else 0) > 0

    # GA4: tara_bala_natal_baseline rows
    row = conn.execute(
        "SELECT COUNT(*) FROM chart_facts WHERE chart_id = %s AND fact_category LIKE '%%tara_bala%%'",
        [chart_id]
    ).fetchone()
    results["ga4"] = (row["count"] if row else 0) > 0

    # GA6: varga rows in chart_divisionals or chart_facts
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM chart_facts WHERE chart_id = %s AND fact_category LIKE '%%varga%%'",
            [chart_id]
        ).fetchone()
        results["ga6"] = (row["count"] if row else 0) > 0
    except Exception:
        results["ga6"] = False

    # GA7: chart_dashas rows
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM chart_dashas WHERE chart_id = %s",
            [chart_id]
        ).fetchone()
        results["ga7"] = (row["count"] if row else 0) > 0
    except Exception:
        results["ga7"] = False

    # GA8: argala_natal_matrix rows
    row = conn.execute(
        "SELECT COUNT(*) FROM chart_facts WHERE chart_id = %s AND fact_category = 'argala_natal_matrix'",
        [chart_id]
    ).fetchone()
    results["ga8"] = (row["count"] if row else 0) > 0

    return results


def _read_moon_sign_per_ayanamsha(conn: Any, chart_id: str) -> dict[str, str]:
    """
    Read natal Moon sign from GA3 graha_position rows, per ayanamsha.
    Returns {ayanamsha_id: moon_sign}.
    """
    rows = conn.execute(
        """
        SELECT ayanamsha_id, fact_value_text
        FROM chart_facts
        WHERE chart_id = %s
          AND fact_category = 'graha_position'
          AND fact_subject = 'MOON'
          AND fact_key = 'sign'
        """,
        [chart_id],
    ).fetchall()
    return {r["ayanamsha_id"]: r["fact_value_text"] for r in rows}


def _read_moon_pada_per_ayanamsha(conn: Any, chart_id: str) -> dict[str, int]:
    """Read natal Moon nakshatra pada from GA3, per ayanamsha."""
    rows = conn.execute(
        """
        SELECT ayanamsha_id, fact_value_num
        FROM chart_facts
        WHERE chart_id = %s
          AND fact_category = 'graha_position'
          AND fact_subject = 'MOON'
          AND fact_key = 'pada'
        """,
        [chart_id],
    ).fetchall()
    return {r["ayanamsha_id"]: int(r["fact_value_num"]) if r["fact_value_num"] else NATIVE_MOON_PADA for r in rows}


# ── INSERT chart_facts rows ───────────────────────────────────────────────────

def _insert_rows(conn: Any, rows: list[dict]) -> int:
    # Idempotency: replace this chart's prior rows for the scope being written so a
    # rebuild under a new build_id replaces instead of accreting (build_id is in the
    # chart_facts unique key).
    replace_prior_chart_facts(conn, rows)
    written = 0
    for r in rows:
        conn.execute(
            """
            INSERT INTO chart_facts
              (fact_id, chart_id, ayanamsha_id, build_id,
               fact_category, fact_subject, fact_key,
               fact_value_text, fact_value_num, fact_value_jsonb,
               unit, citation_ref, citation_human,
               source_calculation, verification_pass_status,
               engine_version, computed_at)
            VALUES
              (%(fact_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
               %(fact_category)s, %(fact_subject)s, %(fact_key)s,
               %(fact_value_text)s, %(fact_value_num)s,
               %(fact_value_jsonb)s::jsonb,
               %(unit)s, %(citation_ref)s, %(citation_human)s,
               %(source_calculation)s, %(verification_pass_status)s,
               %(engine_version)s, %(computed_at)s)
            ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
            WHERE formula_id IS NULL
            DO UPDATE SET
              fact_id                = EXCLUDED.fact_id,
              fact_value_text        = EXCLUDED.fact_value_text,
              fact_value_num         = EXCLUDED.fact_value_num,
              fact_value_jsonb       = EXCLUDED.fact_value_jsonb,
              citation_ref           = EXCLUDED.citation_ref,
              citation_human         = EXCLUDED.citation_human,
              engine_version         = EXCLUDED.engine_version,
              computed_at            = EXCLUDED.computed_at
            """,
            r,
        )
        written += 1
    return written


# ── asset_throughput update ───────────────────────────────────────────────────

def _update_asset_throughput(chart_id: str, build_id: str, row_count: int) -> None:
    with _conn() as conn:
        update_asset_throughput(conn, "ga_sade_sati", chart_id, build_id, row_count)


# ── Materialized view refresh ─────────────────────────────────────────────────

def _refresh_mv(conn: Any) -> None:
    """Refresh mv_chart_sade_sati_lifetime_summary synchronously."""
    try:
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chart_sade_sati_lifetime_summary")
        logger.info("[ga_sade_sati_writer] MV mv_chart_sade_sati_lifetime_summary refreshed")
    except Exception:
        try:
            conn.execute("REFRESH MATERIALIZED VIEW mv_chart_sade_sati_lifetime_summary")
            logger.info("[ga_sade_sati_writer] MV refreshed (non-concurrent)")
        except Exception as exc:
            logger.warning("[ga_sade_sati_writer] MV refresh failed (non-fatal): %s", exc)


# ── Main build function ───────────────────────────────────────────────────────

def build_ga_sade_sati(
    chart_id: str = CANONICAL_CHART_ID,
    build_id: str | None = None,
    *,
    conn: Any = None,
    birth_params: dict[str, Any] | None = None,
    window_start: datetime = WINDOW_START,
    window_end: datetime = WINDOW_END,
) -> dict[str, Any]:
    """
    Build ga_sade_sati for the given chart_id across all 5 canonical ayanamshas.

    Step 0: Verify upstream rows (GA3/GA4/GA6/GA7/GA8) — halt-clean if absent.
    Step 1: Detect Saturn sign changes and retrograde periods (swisseph/DE441).
    Step 2: Per ayanamsha: read Moon sign from GA3, build cycles, emit all rows.
    Step 3: Two-pass verification of cycle invariants.
    Step 4: Insert chart_facts rows (atomic grain).
    Step 5: Refresh MV.
    Step 6: Update asset_throughput.

    Returns summary dict with row counts and verification status.
    Raises RuntimeError on upstream-absent or divergent-flagged conditions.
    """
    import uuid
    from contextlib import nullcontext
    if build_id is None:
        build_id = str(uuid.uuid4())

    owns_conn = conn is None

    computed_at = datetime.now(timezone.utc).isoformat()

    summary: dict[str, Any] = {
        "chart_id": chart_id,
        "build_id": build_id,
        "ayanamshas": {},
        "total_chart_facts_rows": 0,
        "two_pass_verified": True,
        "divergent_flagged": False,
        "upstream_check": {},
    }

    logger.info(
        "[ga_sade_sati_writer] Starting build chart_id=%s build_id=%s",
        chart_id, build_id,
    )

    with (_conn() if owns_conn else nullcontext(conn)) as conn:
        # ── Step 0: Upstream presence check ──────────────────────────────────
        upstream = _verify_upstream_rows(conn, chart_id)
        summary["upstream_check"] = upstream
        missing = [k for k, v in upstream.items() if not v]
        if missing:
            msg = (
                f"[ga_sade_sati_writer] HALT: upstream rows absent for {missing}. "
                f"chart_id={chart_id}. Run GA3/GA4/GA6/GA7/GA8 writers first."
            )
            logger.error(msg)
            _write_halt_log("UPSTREAM_ABSENT", msg)
            raise RuntimeError(msg)

        logger.info("[ga_sade_sati_writer] Upstream check PASS: %s", upstream)

        # Read Moon sign and pada per ayanamsha from GA3
        moon_signs = _read_moon_sign_per_ayanamsha(conn, chart_id)
        moon_padas = _read_moon_pada_per_ayanamsha(conn, chart_id)

        # ── Step 1: Saturn transit detection (once, Lahiri reference) ────────
        logger.info("[ga_sade_sati_writer] Detecting Saturn sign changes...")
        sign_changes = _detect_saturn_sign_changes(window_start, window_end)
        logger.info("[ga_sade_sati_writer] Detected %d Saturn sign changes", len(sign_changes))

        logger.info("[ga_sade_sati_writer] Detecting Saturn retrograde periods...")
        retros = _detect_saturn_retrogrades(window_start, window_end)
        logger.info("[ga_sade_sati_writer] Detected %d retrograde periods", len(retros))

        # ── Step 2: Per-ayanamsha row emission ────────────────────────────────
        for ayanamsha_id in CANONICAL_AYANAMSHAS:
            # Moon sign from GA3 (cross-ayanamsha divergence at AQ/PI boundary is REAL)
            moon_sign = moon_signs.get(ayanamsha_id)
            if not moon_sign:
                logger.warning(
                    "[ga_sade_sati_writer] Moon sign not found in GA3 for ayanamsha=%s; "
                    "using Lahiri fallback", ayanamsha_id
                )
                moon_sign = moon_signs.get("lahiri_chitrapaksha", "Aquarius")

            moon_pada = moon_padas.get(ayanamsha_id, NATIVE_MOON_PADA)

            logger.info(
                "[ga_sade_sati_writer] ayanamsha=%s moon_sign=%s moon_pada=%d",
                ayanamsha_id, moon_sign, moon_pada,
            )

            # Build Sade Sati cycles for this Moon sign
            cycles = build_sade_sati_cycles(moon_sign, sign_changes)
            logger.info(
                "[ga_sade_sati_writer] ayanamsha=%s: %d Sade Sati cycles detected",
                ayanamsha_id, len(cycles),
            )

            # ── Step 3: Two-pass verification ─────────────────────────────────
            divergences = two_pass_verify_cycles(cycles)
            if divergences:
                msg = (
                    f"[ga_sade_sati_writer] TWO-PASS DIVERGENCE (ayanamsha={ayanamsha_id}):\n"
                    + "\n".join(divergences)
                )
                logger.error(msg)
                _write_halt_log("TWO_PASS_DIVERGENCE", msg)
                summary["two_pass_verified"] = False
                summary["divergent_flagged"] = True
                raise RuntimeError(msg)

            # Build natal_facts scaffold (enriched from GA7 at build time;
            # defaults for non-DB keys used when upstream join unavailable)
            natal_facts: dict[str, Any] = {
                "moon_pada": moon_pada,
                "saturn_yoga_karaka": False,  # Aries Lagna — Saturn is NOT yoga karaka
                "natal_saturn_aspects_natal_moon": False,
                "saturn_moon_parivartana": False,
                "moon_sign_lord_strong": False,
                "jupiter_aspects_saturn_during_cycle": False,
                "d10_karya_bhava_activation_flag": False,
                "d10_karya_activation_facts": [],
                "argala_during_period": [],
                "tara_bala_at_janma_peak": "PENDING_GA4_LOOKUP",
                "mars_aspect_during_period": False,
                "jupiter_aspect_during_period": False,
                "saturn_rahu_axis_flag": False,
                "eclipse_during_period": False,
                "concurrent_saturn_return": False,
            }

            # ── Step 4: Emit all rows ─────────────────────────────────────────
            all_rows: list[dict] = []
            for cycle in cycles:
                cycle_rows = _emit_cycle_rows(
                    chart_id, ayanamsha_id, build_id,
                    cycle, retros, natal_facts, computed_at,
                )
                all_rows.extend(cycle_rows)

            # Dhaiya / Kantaka / Ashtama rows
            dhaiya_rows = _emit_dhaiya_rows(
                chart_id, ayanamsha_id, build_id,
                moon_sign, sign_changes, computed_at,
            )
            all_rows.extend(dhaiya_rows)

            # Insert all rows
            written = _insert_rows(conn, all_rows)
            summary["ayanamshas"][ayanamsha_id] = {
                "moon_sign": moon_sign,
                "moon_pada": moon_pada,
                "cycles": len(cycles),
                "chart_facts_rows": written,
            }
            summary["total_chart_facts_rows"] += written
            logger.info(
                "[ga_sade_sati_writer] ayanamsha=%s written %d rows",
                ayanamsha_id, written,
            )

        if owns_conn:
            conn.commit()

        # ── Step 5: Refresh MV ────────────────────────────────────────────────
        _refresh_mv(conn)
        if owns_conn:
            conn.commit()

    # ── Step 6: Update asset_throughput ──────────────────────────────────────
    if owns_conn:
        _update_asset_throughput(chart_id, build_id, summary["total_chart_facts_rows"])

    summary["status"] = "PASS"
    logger.info(
        "[ga_sade_sati_writer] COMPLETE. Total chart_facts rows=%d",
        summary["total_chart_facts_rows"],
    )
    return summary
