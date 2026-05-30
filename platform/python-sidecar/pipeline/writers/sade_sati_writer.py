"""
pipeline.writers.sade_sati_writer — Write Sade Sati cycle phases to chart_facts.
A9 (G3-06): Sade Sati = ~7.5-year period when Saturn transits 12th/natal/2nd from Moon.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

log = logging.getLogger(__name__)

# ── C-07 dispatch constants ────────────────────────────────────────────────────
ASSET_ID = "A9_sade_sati"
ASSET_LABEL = "Sade-Sati Phases"
ENGINE_VERSION = "natal_engine/0.2.0"

# 0-indexed sign order: Aries=0 ... Pisces=11
_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Phase labels keyed by position relative to Moon sign
_PHASE_LABEL = {
    -1: "12th_phase",   # sign before Moon (approaching)
     0: "natal_phase",  # Moon's own sign (peak)
     1: "2nd_phase",    # sign after Moon (departing)
}

# Approximate Saturn ingress dates (year, sign_num) for fallback computation
# Saturn completes one round (~29.5 yr) ≈ 2.46 yr per sign
_APPROX_SATURN_YEAR_PER_SIGN = 2.46

# Historical approximate Saturn sign start years (Tropical → close enough for
# a fallback when ephemeris data is absent).  Covers 1960–2041.
_APPROX_SATURN_INGRESSES: list[tuple[float, int]] = [
    (1959.83,  8),  # Sagittarius
    (1961.75,  9),  # Capricorn
    (1964.16, 10),  # Aquarius
    (1966.62, 11),  # Pisces
    (1969.08,  0),  # Aries
    (1971.54,  1),  # Taurus
    (1973.96,  2),  # Gemini
    (1976.41,  3),  # Cancer
    (1978.83,  4),  # Leo
    (1980.91,  5),  # Virgo
    (1982.95,  6),  # Libra
    (1985.08,  7),  # Scorpio
    (1987.5,   8),  # Sagittarius
    (1990.0,   9),  # Capricorn
    (1992.42, 10),  # Aquarius
    (1994.79, 11),  # Pisces
    (1996.79,  0),  # Aries
    (1998.83,  1),  # Taurus
    (2000.71,  2),  # Gemini
    (2003.21,  3),  # Cancer
    (2005.71,  4),  # Leo
    (2007.75,  5),  # Virgo
    (2009.83,  6),  # Libra
    (2012.0,   7),  # Scorpio
    (2014.5,   8),  # Sagittarius
    (2017.08,  9),  # Capricorn
    (2020.08, 10),  # Aquarius
    (2023.17, 11),  # Pisces
    (2025.83,  0),  # Aries
    (2028.25,  1),  # Taurus
    (2030.67,  2),  # Gemini
    (2033.08,  3),  # Cancer
    (2035.58,  4),  # Leo
    (2037.67,  5),  # Virgo
    (2039.75,  6),  # Libra
    (2041.92,  7),  # Scorpio
]


# ── Row helpers (mirror t1_structural_writer / panchanga_writer_a4 pattern) ────

def _make_fact_id(category: str, subject: str, key: str,
                  chart_id: str, ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _make_citation_ref(category: str, subject: str, key: str,
                       chart_id: str, ayanamsha_id: str) -> str:
    return (
        f"{category}.{subject}.{key}"
        f"@chart={chart_id[:8]}"
        f":ay={ayanamsha_id}"
        f":eng={ENGINE_VERSION}"
    )


def _row(
    chart_id: str, ayanamsha_id: str, build_id: str,
    fact_category: str, fact_subject: str, fact_key: str,
    value_text: Optional[str], value_number: Optional[float],
    citation_ref: str, citation_human: str,
    source_calc: str,
) -> tuple:
    fact_id = _make_fact_id(
        fact_category, fact_subject, fact_key, chart_id, ayanamsha_id, build_id
    )
    provenance = json.dumps({
        "writer": "sade_sati_writer",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,          # category (legacy col)
        "D1",                   # divisional_chart
        "sade_sati_writer",     # source_section
        provenance,
        fact_category, fact_subject, fact_key,
        value_text, value_number,
        citation_ref, citation_human,
        source_calc,
        "single",               # verification_pass_status
        ENGINE_VERSION,
        datetime.now(timezone.utc).isoformat(),  # computed_at_iso
    )


_INSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, chart_id, ayanamsha_id, build_id,
   category, divisional_chart, source_section, provenance,
   fact_category, fact_subject, fact_key,
   value_text, value_number,
   citation_ref, citation_human,
   source_calculation, verification_pass_status,
   engine_version, computed_at_iso)
VALUES %s
ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
DO UPDATE SET
  value_text = EXCLUDED.value_text,
  value_number = EXCLUDED.value_number,
  computed_at_iso = EXCLUDED.computed_at_iso
"""


def _upsert_chart_facts(conn, rows: list[tuple]) -> None:
    from psycopg2.extras import execute_values
    execute_values(conn, _INSERT_SQL, rows)


# ── Core computation ───────────────────────────────────────────────────────────

def _year_frac_to_date(year_frac: float) -> str:
    """Convert a fractional year (e.g. 2017.08) to an approximate 'YYYY-MM-DD' string."""
    year = int(year_frac)
    remainder = year_frac - year
    day_of_year = int(remainder * 365.25)
    try:
        d = datetime(year, 1, 1) + __import__("datetime").timedelta(days=day_of_year)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return f"{year}-01-01"


def _build_approximate_sign_changes(moon_sign_num: int) -> list[dict]:
    """
    Build Saturn sign-change list from the approximate ingress table.
    Returns only the three Sade Sati sign entries that have start+end dates.
    """
    ss_signs = {
        (moon_sign_num - 1) % 12,
        moon_sign_num,
        (moon_sign_num + 1) % 12,
    }

    # Walk the ingress list and emit one period per entry (next entry = end date)
    periods = []
    for i, (yr, sign_num) in enumerate(_APPROX_SATURN_INGRESSES):
        if sign_num in ss_signs:
            start_date = _year_frac_to_date(yr)
            # end_date = next ingress start
            if i + 1 < len(_APPROX_SATURN_INGRESSES):
                end_date = _year_frac_to_date(_APPROX_SATURN_INGRESSES[i + 1][0])
            else:
                end_date = _year_frac_to_date(yr + _APPROX_SATURN_YEAR_PER_SIGN)
            periods.append({
                "sign": _SIGN_NAMES[sign_num],
                "sign_num": sign_num,
                "start_date": start_date,
                "end_date": end_date,
            })
    return periods


def _compute_sade_sati_rows(
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    moon_sign_num: int,
    moon_sign_name: str,
    saturn_sign_changes: list[dict],
) -> list[tuple]:
    """
    Build all chart_facts rows for Sade Sati given a list of Saturn sign periods.
    Groups consecutive periods for the same Sade Sati cycle and numbers them.
    """
    ss_signs = {
        (moon_sign_num - 1) % 12: -1,
        moon_sign_num: 0,
        (moon_sign_num + 1) % 12: 1,
    }

    # Filter Saturn periods that fall in Sade Sati signs
    matching = []
    for period in saturn_sign_changes:
        sn = period.get("sign_num")
        if sn in ss_signs:
            matching.append({**period, "_phase_offset": ss_signs[sn]})

    # Group into Sade Sati cycles: a new cycle starts each time we see the
    # "12th_phase" (or after a long gap — more than 5 years from the last).
    cycles: list[list[dict]] = []
    current_cycle: list[dict] = []

    for period in matching:
        if not current_cycle:
            current_cycle.append(period)
        else:
            # Check if this is a continuation or a new cycle
            last_phase = current_cycle[-1]["_phase_offset"]
            this_phase = period["_phase_offset"]
            # A new cycle begins if we see 12th_phase again after having seen
            # natal or 2nd, or if phases reset
            if this_phase == -1 and last_phase != -1:
                # New Sade Sati cycle
                cycles.append(current_cycle)
                current_cycle = [period]
            else:
                current_cycle.append(period)

    if current_cycle:
        cycles.append(current_cycle)

    rows = []

    for cycle_n, cycle_phases in enumerate(cycles):
        for phase_dict in cycle_phases:
            offset = phase_dict["_phase_offset"]
            phase_label = _PHASE_LABEL[offset]
            start_date = phase_dict.get("start_date", "")
            end_date = phase_dict.get("end_date", "")

            # Duration in years (approximate)
            duration_years: float = _APPROX_SATURN_YEAR_PER_SIGN
            try:
                from datetime import datetime as _dt
                d0 = _dt.fromisoformat(start_date)
                d1 = _dt.fromisoformat(end_date)
                duration_years = round((d1 - d0).days / 365.25, 2)
            except Exception:
                pass

            fact_subject = f"cycle_{cycle_n}"
            cref = _make_citation_ref(
                "sade_sati", fact_subject, phase_label, chart_id, ayanamsha_id
            )
            rows.append(_row(
                chart_id, ayanamsha_id, build_id,
                "sade_sati",
                fact_subject,
                phase_label,
                f"{start_date} to {end_date}",
                duration_years,
                cref,
                "BPHS Ch 71 (Sade Sati)",
                "sade_sati_writer/cycle_phases",
            ))

    return rows


# ── Public write() entry-point ─────────────────────────────────────────────────

def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Compute and store Sade Sati cycle phase rows into chart_facts.

    Reads chart_output["planets"] for natal Moon sign_num.
    Reads chart_output["saturn_sign_changes"] (optional) for precise Saturn
    ingress dates; falls back to approximate table when absent.

    Returns: rows_written (int).
    """
    log.info(
        "%s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )

    planets: list[dict] = chart_output.get("planets", [])
    moon_planet = next(
        (p for p in planets if str(p.get("id", "")).lower() == "moon"), None
    )

    rows: list[tuple] = []

    if moon_planet is None:
        log.warning("sade_sati_writer: no Moon planet in chart_output — storing only summary row")
        # Still store a minimal summary so the writer doesn't crash
        cref = _make_citation_ref("sade_sati", "natal_moon", "sign", chart_id, ayanamsha_id)
        rows.append(_row(
            chart_id, ayanamsha_id, build_id,
            "sade_sati", "natal_moon", "sign",
            None, None,
            cref, "BPHS Ch 71 (Sade Sati)",
            "sade_sati_writer/natal_moon",
        ))
        if rows:
            _upsert_chart_facts(conn, rows)
        return len(rows)

    moon_sign_num: int = int(moon_planet.get("sign_num", 0))
    moon_sign_name: str = moon_planet.get("sign", _SIGN_NAMES[moon_sign_num % 12])

    # ── Summary row: natal Moon sign ──────────────────────────────────────────
    cref_moon = _make_citation_ref("sade_sati", "natal_moon", "sign", chart_id, ayanamsha_id)
    rows.append(_row(
        chart_id, ayanamsha_id, build_id,
        "sade_sati", "natal_moon", "sign",
        moon_sign_name, float(moon_sign_num),
        cref_moon, "BPHS Ch 71 (Sade Sati)",
        "sade_sati_writer/natal_moon",
    ))

    # ── Saturn sign changes (precise or approximate) ──────────────────────────
    saturn_sign_changes: list[dict] = chart_output.get("saturn_sign_changes") or []
    if not saturn_sign_changes:
        log.info(
            "sade_sati_writer: saturn_sign_changes absent — using approximate table"
        )
        saturn_sign_changes = _build_approximate_sign_changes(moon_sign_num)

    # ── Cycle phase rows ──────────────────────────────────────────────────────
    cycle_rows = _compute_sade_sati_rows(
        chart_id, ayanamsha_id, build_id,
        moon_sign_num, moon_sign_name, saturn_sign_changes,
    )
    rows.extend(cycle_rows)

    if rows:
        _upsert_chart_facts(conn, rows)

    log.info(
        "sade_sati_writer: wrote %d rows (1 summary + %d cycle-phase rows)",
        len(rows), len(cycle_rows),
    )
    return len(rows)


# ── Legacy IBuildWriter class (retained; not used by dispatch) ─────────────────

TABLE_STAGING = "sade_sati_phases_staging"
TABLE_LIVE = "sade_sati_phases"

_STAGING_INSERT_SQL = f"""
INSERT INTO {TABLE_STAGING}
  (cycle_number, phase, start_date, end_date, saturn_sign_at_start,
   notes, source_section, build_id)
VALUES
  (%(cycle_number)s, %(phase)s, %(start_date)s, %(end_date)s,
   %(saturn_sign_at_start)s, %(notes)s, %(source_section)s, %(build_id)s)
ON CONFLICT (cycle_number, phase, start_date) DO UPDATE SET
  end_date             = EXCLUDED.end_date,
  saturn_sign_at_start = EXCLUDED.saturn_sign_at_start,
  notes                = EXCLUDED.notes,
  source_section       = EXCLUDED.source_section,
  build_id             = EXCLUDED.build_id
"""


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


from pipeline.writers.base import IBuildWriter, SwapResult, ValidationResult, WriteResult  # noqa: E402


class SadeSatiWriter(IBuildWriter):
    """Legacy staging/live writer — write sade_sati_phases_staging rows."""

    def write_to_staging(self, rows: list[Any], build_id: str) -> WriteResult:
        import psycopg
        if not rows:
            return WriteResult(chunk_count=0, errors=["No rows provided"])

        errors: list[str] = []
        written = 0

        with psycopg.connect(_db_url()) as conn:
            for row in rows:
                params = {**row, "build_id": build_id}
                try:
                    conn.execute(_STAGING_INSERT_SQL, params)
                    written += 1
                except Exception as exc:
                    errors.append(f"{row.get('notes', '?')}: {exc}")
            conn.commit()

        log.info(
            "sade_sati_phases_staging written: %d rows, %d errors", written, len(errors)
        )
        return WriteResult(chunk_count=written, errors=errors)

    def validate_staging(self, build_id: str) -> ValidationResult:
        import psycopg
        with psycopg.connect(_db_url()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM sade_sati_phases_staging WHERE build_id = %s",
                (build_id,),
            ).fetchone()
            count = int(row[0]) if row else 0

        valid = 20 <= count <= 80
        issues = [] if valid else [
            f"sade_sati_phases_staging count {count} outside 20–80 for build_id={build_id}"
        ]
        log.info(
            "sade_sati validate_staging: build_id=%s count=%d valid=%s",
            build_id, count, valid,
        )
        return ValidationResult(valid=valid, chunk_count=count, issues=issues)

    def swap_to_live(self, build_id: str) -> SwapResult:
        import psycopg
        with psycopg.connect(_db_url()) as conn:
            live_count = int(
                (conn.execute("SELECT COUNT(*) FROM sade_sati_phases").fetchone() or [0])[0]
            )
            staging_count = int(
                (conn.execute(
                    "SELECT COUNT(*) FROM sade_sati_phases_staging WHERE build_id = %s",
                    (build_id,),
                ).fetchone() or [0])[0]
            )

        if live_count > 0 and staging_count < (0.5 * live_count):
            msg = (
                f"ABORT: staging={staging_count}, live={live_count} — "
                "below 50% safety threshold."
            )
            log.error(msg)
            return SwapResult(success=False, promoted_chunk_count=0, message=msg)

        import psycopg
        with psycopg.connect(_db_url(), autocommit=False) as conn:
            with conn.transaction():
                conn.execute("DELETE FROM sade_sati_phases")
                conn.execute(
                    """
                    INSERT INTO sade_sati_phases
                      (cycle_number, phase, start_date, end_date,
                       saturn_sign_at_start, notes, source_section, build_id)
                    SELECT cycle_number, phase, start_date, end_date,
                           saturn_sign_at_start, notes, source_section, build_id
                    FROM sade_sati_phases_staging
                    WHERE build_id = %s
                    """,
                    (build_id,),
                )
                conn.execute("TRUNCATE sade_sati_phases_staging")
                try:
                    conn.execute(
                        "UPDATE build_manifests SET status='live', promoted_at=NOW() "
                        "WHERE build_id=%s",
                        (build_id,),
                    )
                except Exception as exc:
                    log.warning("build_manifests update skipped: %s", exc)

        log.info(
            "sade_sati swap_to_live: promoted %d rows for build_id=%s",
            staging_count, build_id,
        )
        return SwapResult(
            success=True,
            promoted_chunk_count=staging_count,
            message=f"sade_sati_phases live: {staging_count} rows (build_id={build_id})",
        )
