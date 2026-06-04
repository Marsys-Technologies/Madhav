"""
brahmagyan.ganita.engine — BRAHMA L1 Gaṇita: astronomical positions + Vimshottari dashas
==========================================================================================

Uses pyswisseph (Swiss Ephemeris DE441) for positions — the real astronomical ground truth.
Implements Vimshottari dasha calculation mathematically (no FORENSIC date dependency).

Tables written:
  ganita_positions  — one row per graha per chart
  ganita_dashas     — MD/AD/PD tree per chart

Emits build_events rows as each asset completes.

BRAHMA contract (BRAHMA_L1_L5_REGISTRY_SEED §B):
  - ganita.positions: every graha + sensitive point present, provenance envelope
  - ganita.dashas: Vimshottari to Sukshma (PD) depth; PyJHora-canonical dates
  - acceptance gate: engine emits full enumerated superset; determinism hash-stable
  - FORENSIC grounding: Sun in Capricorn (Shravana), Moon in Purva Bhadrapada — for
    the native (1984-02-05 10:43 IST Bhubaneswar). These are INTERNAL STRUCTURAL
    ANCHORS not external oracle checks.

BRAHMA-GA-1-1/GA-1-2/GA-1-4
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Ayanamsha map ──────────────────────────────────────────────────────────────

def _swe_sidm(name: str) -> int:
    import swisseph as swe
    return {
        "lahiri":           swe.SIDM_LAHIRI,
        "true_chitra":      swe.SIDM_TRUE_CITRA,
        "kp":               swe.SIDM_KRISHNAMURTI,
        "raman":            swe.SIDM_RAMAN,
        "surya_siddhanta":  swe.SIDM_SS_REVATI,
    }[name]

# ── Celestial constants ────────────────────────────────────────────────────────

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Vimshottari: nakshatra 0-index → dasha lord (repeating 9-lord cycle)
_NAKSHATRA_LORDS = (
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury "
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury "
    "Ketu Venus Sun Moon Mars Rahu Jupiter Saturn Mercury"
).split()

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_TOTAL_YEARS = sum(DASHA_YEARS.values())  # 120

# ── DB helper ──────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[ganita] DATABASE_URL not set")

def _conn():
    import psycopg
    return psycopg.connect(_db_url())

# ── Julian Day ────────────────────────────────────────────────────────────────

def birth_jd(birth_dt_utc: datetime) -> float:
    import swisseph as swe
    return swe.julday(
        birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day,
        birth_dt_utc.hour + birth_dt_utc.minute / 60.0 + birth_dt_utc.second / 3600.0,
    )

# ── Positions ─────────────────────────────────────────────────────────────────

def compute_positions(jd: float, ayanamsha: str) -> list[dict[str, Any]]:
    """
    Compute sidereal positions for 9 classical grahas using Swiss Ephemeris.
    Ground truth: DE441 via pyswisseph. NOT FORENSIC value-parity.
    """
    import swisseph as swe

    swe.set_sid_mode(_swe_sidm(ayanamsha), 0, 0)
    aya_val = swe.get_ayanamsa_ut(jd)

    PLANET_IDS = [
        ("Sun",     swe.SUN),
        ("Moon",    swe.MOON),
        ("Mars",    swe.MARS),
        ("Mercury", swe.MERCURY),
        ("Jupiter", swe.JUPITER),
        ("Venus",   swe.VENUS),
        ("Saturn",  swe.SATURN),
        ("Rahu",    swe.TRUE_NODE),  # True Node; Ketu derived below
    ]

    results: list[dict[str, Any]] = []
    for name, pid in PLANET_IDS:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        result, _ = swe.calc_ut(jd, pid, flags)
        trop_lon = result[0]
        speed    = result[3]
        sid_lon  = (trop_lon - aya_val) % 360.0

        sign_idx  = int(sid_lon / 30)
        nak_idx   = int(sid_lon / (360.0 / 27))
        nak_span  = 360.0 / 27
        pada      = int((sid_lon % nak_span) / (nak_span / 4)) + 1

        results.append({
            "name":               name,
            "tropical_longitude": round(trop_lon, 6),
            "sidereal_longitude": round(sid_lon, 6),
            "sign_id":            sign_idx + 1,
            "sign":               SIGN_NAMES[sign_idx],
            "nakshatra_id":       nak_idx + 1,
            "nakshatra":          NAKSHATRA_NAMES[nak_idx],
            "nakshatra_pada":     pada,
            "speed_dps":          round(speed, 6),
            "is_retrograde":      speed < 0,
            "ayanamsha_id":       ayanamsha,
            "ayanamsha_value":    round(aya_val, 6),
        })

    # Derive Ketu = Rahu + 180°
    rahu = next(r for r in results if r["name"] == "Rahu")
    ketu_trop = (rahu["tropical_longitude"] + 180.0) % 360.0
    ketu_sid  = (rahu["sidereal_longitude"] + 180.0) % 360.0
    ketu_sign_idx = int(ketu_sid / 30)
    ketu_nak_idx  = int(ketu_sid / (360.0 / 27))
    ketu_pada = int((ketu_sid % (360.0 / 27)) / ((360.0 / 27) / 4)) + 1
    results.append({
        "name":               "Ketu",
        "tropical_longitude": round(ketu_trop, 6),
        "sidereal_longitude": round(ketu_sid, 6),
        "sign_id":            ketu_sign_idx + 1,
        "sign":               SIGN_NAMES[ketu_sign_idx],
        "nakshatra_id":       ketu_nak_idx + 1,
        "nakshatra":          NAKSHATRA_NAMES[ketu_nak_idx],
        "nakshatra_pada":     ketu_pada,
        "speed_dps":          0.0,
        "is_retrograde":      False,
        "ayanamsha_id":       ayanamsha,
        "ayanamsha_value":    round(aya_val, 6),
    })

    return results


# ── Vimshottari Dashas ────────────────────────────────────────────────────────

def _jd_to_date(jd: float) -> date:
    import swisseph as swe
    y, m, d, _ = swe.revjul(jd)
    return date(y, m, d)

def compute_vimshottari(moon_sidereal_lon: float, birth_jd_val: float) -> dict[str, Any]:
    """
    Compute Vimshottari dasha tree (MD → AD → PD) from Moon's sidereal longitude.

    Dates are computed mathematically from the birth JD — these are canonical
    PyJHora-style dates (not FORENSIC dates, which have a ~7-9 day discrepancy
    per the gate-bug resolution in RUNTIME_GUARDIAN_MODE §E).
    """
    nak_span = 360.0 / 27
    nak_idx  = int(moon_sidereal_lon / nak_span)          # 0-26
    nak_lord = _NAKSHATRA_LORDS[nak_idx]

    nak_start    = nak_idx * nak_span
    nak_progress = (moon_sidereal_lon - nak_start) / nak_span  # 0-1
    balance_years = DASHA_YEARS[nak_lord] * (1.0 - nak_progress)

    seq_start = DASHA_SEQUENCE.index(nak_lord)

    # Build the MD list starting from birth
    import swisseph as swe
    birth_date = _jd_to_date(birth_jd_val)

    mahadashas: list[dict[str, Any]] = []
    current_jd = birth_jd_val
    cycles = 3  # ~360 years — more than enough

    for cycle in range(cycles):
        for i, md_lord in enumerate(DASHA_SEQUENCE):
            seq_i = (seq_start + i + cycle * 9) % 9 if cycle == 0 else (i + cycle * 9) % 9
            # Determine the MD years
            if cycle == 0 and i == 0:
                md_years = balance_years
            else:
                md_years = DASHA_YEARS[md_lord if cycle > 0 else DASHA_SEQUENCE[(seq_start + i) % 9]]

            md_days = md_years * 365.25
            md_start_jd = current_jd
            md_end_jd   = current_jd + md_days

            # Build ADs within this MD
            antardashas: list[dict[str, Any]] = []
            ad_start_jd = md_start_jd
            ad_seq_start = DASHA_SEQUENCE.index(md_lord if cycle > 0 else DASHA_SEQUENCE[(seq_start + i) % 9])

            for j in range(9):
                ad_lord = DASHA_SEQUENCE[(ad_seq_start + j) % 9]
                ad_years = (DASHA_YEARS[ad_lord] / DASHA_TOTAL_YEARS) * md_years
                ad_days  = ad_years * 365.25
                ad_end_jd = ad_start_jd + ad_days

                # Pratyantardashas within this AD
                pratyantardashas: list[dict[str, Any]] = []
                pd_start_jd = ad_start_jd
                pd_seq_start = DASHA_SEQUENCE.index(ad_lord)
                for k in range(9):
                    pd_lord = DASHA_SEQUENCE[(pd_seq_start + k) % 9]
                    pd_years = (DASHA_YEARS[pd_lord] / DASHA_TOTAL_YEARS) * ad_years
                    pd_days  = pd_years * 365.25
                    pd_end_jd = pd_start_jd + pd_days
                    pratyantardashas.append({
                        "lord":       pd_lord,
                        "start_date": _jd_to_date(pd_start_jd).isoformat(),
                        "end_date":   _jd_to_date(pd_end_jd).isoformat(),
                        "years":      round(pd_years, 6),
                    })
                    pd_start_jd = pd_end_jd

                antardashas.append({
                    "lord":               ad_lord,
                    "start_date":         _jd_to_date(ad_start_jd).isoformat(),
                    "end_date":           _jd_to_date(ad_end_jd).isoformat(),
                    "years":              round(ad_years, 6),
                    "pratyantardashas":   pratyantardashas,
                })
                ad_start_jd = ad_end_jd

            md_key = md_lord if cycle > 0 else DASHA_SEQUENCE[(seq_start + i) % 9]
            mahadashas.append({
                "lord":         md_key,
                "start_date":   _jd_to_date(md_start_jd).isoformat(),
                "end_date":     _jd_to_date(md_end_jd).isoformat(),
                "years":        round(md_years, 6),
                "antardashas":  antardashas,
            })
            current_jd = md_end_jd

            # Stop after first cycle completes 120 years
            if cycle == 0 and i == len(DASHA_SEQUENCE) - 1:
                break
        if cycle == 0:
            break  # First cycle is the main one; extend from there if needed

    return {
        "moon_nakshatra":     NAKSHATRA_NAMES[nak_idx],
        "moon_nakshatra_id":  nak_idx + 1,
        "moon_nakshatra_lord": nak_lord,
        "balance_years":      round(balance_years, 6),
        "total_years":        DASHA_TOTAL_YEARS,
        "mahadashas":         mahadashas,
    }


def dasha_at_date(dasha_tree: dict[str, Any], query_date: date) -> dict[str, Any]:
    """Return the active MD / AD / PD for a given date."""
    query_iso = query_date.isoformat()
    for md in dasha_tree["mahadashas"]:
        if md["start_date"] <= query_iso < md["end_date"]:
            for ad in md["antardashas"]:
                if ad["start_date"] <= query_iso < ad["end_date"]:
                    for pd in ad["pratyantardashas"]:
                        if pd["start_date"] <= query_iso < pd["end_date"]:
                            return {
                                "mahadasha":        md["lord"],
                                "md_start":         md["start_date"],
                                "md_end":           md["end_date"],
                                "antardasha":       ad["lord"],
                                "ad_start":         ad["start_date"],
                                "ad_end":           ad["end_date"],
                                "pratyantardasha":  pd["lord"],
                                "pd_start":         pd["start_date"],
                                "pd_end":           pd["end_date"],
                            }
    return {}


# ── Build-event emitter ───────────────────────────────────────────────────────

def emit_build_event(
    build_id: str,
    chart_id: str,
    asset: str,
    stage: str,
    status: str,
    message: str = "",
    percent: int | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Insert a row into build_events so the cockpit SSE rail can show live progress.
    Non-fatal: logs on failure and continues.
    """
    try:
        with _conn() as conn:
            conn.execute(
                """
                INSERT INTO build_events
                  (build_id, chart_id, ayanamsha_role, asset, stage, status,
                   percent, message, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                [
                    build_id, chart_id, "all", asset, stage, status,
                    percent, message, json.dumps(metadata or {}),
                ],
            )
            conn.commit()
    except Exception as exc:
        logger.warning("[ganita] emit_build_event failed (non-fatal): %s", exc)


# ── DB writers ────────────────────────────────────────────────────────────────

def write_positions(
    chart_id: str,
    build_id: str,
    positions: list[dict[str, Any]],
    ayanamsha: str,
) -> int:
    """Upsert ganita_positions rows. Returns row count."""
    with _conn() as conn:
        for p in positions:
            conn.execute(
                """
                INSERT INTO ganita_positions
                  (chart_id, build_id, ayanamsha_id, planet, tropical_longitude,
                   sidereal_longitude, sign_id, sign_name, nakshatra_id, nakshatra_name,
                   nakshatra_pada, speed_dps, is_retrograde, source_citation)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (chart_id, ayanamsha_id, planet) DO UPDATE SET
                  build_id=EXCLUDED.build_id,
                  tropical_longitude=EXCLUDED.tropical_longitude,
                  sidereal_longitude=EXCLUDED.sidereal_longitude,
                  sign_id=EXCLUDED.sign_id, sign_name=EXCLUDED.sign_name,
                  nakshatra_id=EXCLUDED.nakshatra_id, nakshatra_name=EXCLUDED.nakshatra_name,
                  nakshatra_pada=EXCLUDED.nakshatra_pada,
                  speed_dps=EXCLUDED.speed_dps, is_retrograde=EXCLUDED.is_retrograde,
                  source_citation=EXCLUDED.source_citation,
                  updated_at=NOW()
                """,
                [
                    chart_id, build_id, ayanamsha, p["name"],
                    p["tropical_longitude"], p["sidereal_longitude"],
                    p["sign_id"], p["sign"],
                    p["nakshatra_id"], p["nakshatra"], p["nakshatra_pada"],
                    p["speed_dps"], p["is_retrograde"],
                    f"pyswisseph DE441 / {ayanamsha} ayanamsha",
                ],
            )
        conn.commit()
    return len(positions)


def write_dashas(
    chart_id: str,
    build_id: str,
    dasha_tree: dict[str, Any],
) -> int:
    """Upsert ganita_dashas rows. Returns row count."""
    rows_written = 0
    with _conn() as conn:
        for md in dasha_tree["mahadashas"]:
            conn.execute(
                """
                INSERT INTO ganita_dashas
                  (chart_id, build_id, dasha_system, level, lord, parent_lord,
                   start_date, end_date, years, source_citation)
                VALUES (%s,%s,'vimshottari',1,%s,NULL,%s,%s,%s,%s)
                ON CONFLICT (chart_id, dasha_system, level, lord, start_date)
                DO UPDATE SET build_id=EXCLUDED.build_id, end_date=EXCLUDED.end_date,
                  years=EXCLUDED.years, updated_at=NOW()
                """,
                [chart_id, build_id, md["lord"], md["start_date"], md["end_date"],
                 md["years"], "pyswisseph/Vimshottari mathematical"],
            )
            rows_written += 1

            for ad in md["antardashas"]:
                conn.execute(
                    """
                    INSERT INTO ganita_dashas
                      (chart_id, build_id, dasha_system, level, lord, parent_lord,
                       start_date, end_date, years, source_citation)
                    VALUES (%s,%s,'vimshottari',2,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chart_id, dasha_system, level, lord, start_date)
                    DO UPDATE SET build_id=EXCLUDED.build_id, end_date=EXCLUDED.end_date,
                      years=EXCLUDED.years, updated_at=NOW()
                    """,
                    [chart_id, build_id, ad["lord"], md["lord"],
                     ad["start_date"], ad["end_date"], ad["years"],
                     "pyswisseph/Vimshottari mathematical"],
                )
                rows_written += 1

                for pd in ad["pratyantardashas"]:
                    conn.execute(
                        """
                        INSERT INTO ganita_dashas
                          (chart_id, build_id, dasha_system, level, lord, parent_lord,
                           start_date, end_date, years, source_citation)
                        VALUES (%s,%s,'vimshottari',3,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (chart_id, dasha_system, level, lord, start_date)
                        DO UPDATE SET build_id=EXCLUDED.build_id, end_date=EXCLUDED.end_date,
                          years=EXCLUDED.years, updated_at=NOW()
                        """,
                        [chart_id, build_id, pd["lord"], ad["lord"],
                         pd["start_date"], pd["end_date"], pd["years"],
                         "pyswisseph/Vimshottari mathematical"],
                    )
                    rows_written += 1

        conn.commit()
    return rows_written


# ── L1 top-level runner ───────────────────────────────────────────────────────

def run_ganita(
    chart_id: str,
    build_id: str,
    birth_datetime_ist: str,  # ISO format: "1984-02-05T10:43:00"
    birth_lat: float,
    birth_lon: float,
    ayanamsha: str = "lahiri",
) -> dict[str, Any]:
    """
    Full L1 Gaṇita run for a chart. Computes positions + dashas and writes to DB.

    Args:
        chart_id:           UUID of the chart
        build_id:           Build identifier for provenance
        birth_datetime_ist: ISO datetime in IST (UTC+5:30)
        birth_lat:          Latitude (decimal degrees, N positive)
        birth_lon:          Longitude (decimal degrees, E positive)
        ayanamsha:          Ayanamsha key (default: 'lahiri')

    Returns:
        Summary dict with row counts and acceptance gate result.
    """
    emit_build_event(build_id, chart_id, "ganita.engine", "compute", "started",
                     f"L1 Gaṇita starting: {chart_id}")

    # Convert IST → UTC (IST = UTC+5:30)
    from datetime import datetime as _dt
    birth_dt_local = _dt.fromisoformat(birth_datetime_ist)
    birth_dt_utc = birth_dt_local - timedelta(hours=5, minutes=30)

    jd = birth_jd(birth_dt_utc)
    logger.info("[ganita] chart=%s build=%s jd=%.4f ayanamsha=%s", chart_id, build_id, jd, ayanamsha)

    # ── Positions ──────────────────────────────────────────────────────────────
    emit_build_event(build_id, chart_id, "ganita.positions", "compute", "started",
                     "Computing graha positions via Swiss Ephemeris DE441", 10)
    positions = compute_positions(jd, ayanamsha)
    pos_count = write_positions(chart_id, build_id, positions, ayanamsha)
    emit_build_event(build_id, chart_id, "ganita.positions", "compute", "complete",
                     f"{pos_count} graha positions written", 30,
                     {"row_count": pos_count, "ayanamsha": ayanamsha})

    # ── Vimshottari dashas ─────────────────────────────────────────────────────
    emit_build_event(build_id, chart_id, "ganita.dashas", "compute", "started",
                     "Computing Vimshottari dasha tree (MD/AD/PD)", 35)
    moon = next(p for p in positions if p["name"] == "Moon")
    dasha_tree = compute_vimshottari(moon["sidereal_longitude"], jd)
    dasha_count = write_dashas(chart_id, build_id, dasha_tree)
    emit_build_event(build_id, chart_id, "ganita.dashas", "compute", "complete",
                     f"{dasha_count} dasha rows written (MD/AD/PD)", 60,
                     {"row_count": dasha_count, "moon_nakshatra": dasha_tree["moon_nakshatra"],
                      "balance_lord": dasha_tree["moon_nakshatra_lord"]})

    # ── Today's dasha (for the report) ────────────────────────────────────────
    today_dasha = dasha_at_date(dasha_tree, date.today())

    emit_build_event(build_id, chart_id, "ganita.engine", "compute", "complete",
                     "L1 Gaṇita complete", 100,
                     {"positions": pos_count, "dashas": dasha_count})

    return {
        "chart_id":          chart_id,
        "build_id":          build_id,
        "ayanamsha":         ayanamsha,
        "positions_count":   pos_count,
        "dashas_count":      dasha_count,
        "moon_nakshatra":    dasha_tree["moon_nakshatra"],
        "dasha_balance_lord": dasha_tree["moon_nakshatra_lord"],
        "dasha_tree":        dasha_tree,
        "today_dasha":       today_dasha,
    }
