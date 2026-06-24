"""
pipeline.writers.sensitive_points_writer_a5_adapter — A5 Marma-Bindu adapter.

Bridges the standard WRITER_REGISTRY write(build_id, chart_id, ayanamsha_id, chart_output, conn)
signature to the real sensitive_points_writer_a5 emit_* functions.

Extracts graha longitudes, lagna longitude, house cusps, etc. from chart_output
and dispatches to each emit_* function, collecting the resulting rows and writing
them to chart_facts via execute_values.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ENGINE_VERSION = "natal_engine/0.2.0"


def _graha_lons(chart_output: dict) -> Dict[str, float]:
    """Extract {graha_id: longitude} map from chart_output."""
    planets = chart_output.get('planets', {}) or {}
    result = {}
    for g, p in planets.items():
        if isinstance(p, dict):
            lon = p.get('longitude')
            if lon is not None:
                try:
                    result[g] = float(lon)
                except (TypeError, ValueError):
                    pass
    return result


def _house_cusps(chart_output: dict) -> Dict[int, float]:
    """Extract {house_num: cusp_longitude} map from chart_output."""
    houses = chart_output.get('houses', {}) or {}
    result = {}
    for k, hd in houses.items():
        if isinstance(hd, dict):
            lon = hd.get('longitude') or hd.get('cusp_longitude')
            if lon is not None:
                try:
                    result[int(k)] = float(lon)
                except (TypeError, ValueError):
                    pass
    return result


def _lagna_lon(chart_output: dict) -> Optional[float]:
    """Extract lagna longitude from chart_output."""
    lagna = chart_output.get('lagna', {}) or {}
    lon = lagna.get('longitude')
    if lon is not None:
        try:
            return float(lon)
        except (TypeError, ValueError):
            pass
    return None


def _write_rows(rows: List[dict], conn, build_id: str, chart_id: str, ayanamsha_id: str) -> int:
    """
    Insert rows (dicts with fact_id, fact_category, fact_subject, fact_key, etc.)
    into chart_facts using execute_values.
    Returns number of rows inserted.
    """
    if not rows:
        return 0

    from psycopg2.extras import execute_values

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
          value_text      = EXCLUDED.value_text,
          value_number    = EXCLUDED.value_number,
          computed_at_iso = EXCLUDED.computed_at_iso
    """

    import json
    now_iso = datetime.now(timezone.utc).isoformat()
    provenance = json.dumps({
        "writer": "sensitive_points_writer_a5_adapter",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })

    tuples = []
    for r in rows:
        fact_category = r.get('fact_category', '')
        fact_subject = r.get('fact_subject', '')
        fact_key = r.get('fact_key', '')
        value_text = r.get('fact_value_text') or r.get('value_text')
        value_number = r.get('fact_value_num') or r.get('value_number')
        if value_number is not None:
            try:
                value_number = float(value_number)
            except (TypeError, ValueError):
                value_number = None
        citation_ref = r.get('citation_ref', '')
        citation_human = r.get('citation_human', '')
        source_calc = r.get('source_calculation', 'sensitive_points_writer_a5_adapter')
        verification = r.get('verification_pass_status', 'single')
        fact_id = r.get('fact_id', '')

        tuples.append((
            fact_id, chart_id, ayanamsha_id, build_id,
            fact_category,                             # category
            "D1",                                      # divisional_chart
            "sensitive_points_writer_a5_adapter",      # source_section
            provenance,
            fact_category, fact_subject, fact_key,
            str(value_text) if value_text is not None else None,
            value_number,
            citation_ref,
            citation_human,
            source_calc,
            verification,
            ENGINE_VERSION,
            now_iso,
        ))

    try:
        with conn.cursor() as cur:
            execute_values(cur, _INSERT_SQL, tuples)
        return len(tuples)
    except Exception as exc:
        logger.error("A5 adapter _write_rows failed: %s", exc)
        raise


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    A5 Marma-Bindu adapter: dispatches to real sensitive_points_writer_a5 emit_* functions.

    Collects rows from each emit function and writes them to chart_facts.
    """
    try:
        import pipeline.writers.sensitive_points_writer_a5 as sp5
    except ImportError as exc:
        logger.error("A5 adapter: cannot import sensitive_points_writer_a5: %s", exc)
        return 0

    graha_lons = _graha_lons(chart_output)
    house_cusps_map = _house_cusps(chart_output)
    lagna_lon = _lagna_lon(chart_output)

    sun_lon = graha_lons.get('SU')
    moon_lon = graha_lons.get('MO')
    saturn_lon = graha_lons.get('SA')
    rahu_lon = graha_lons.get('RA')

    # Weekday (0=Sun..6=Sat) from chart_output meta
    meta = chart_output.get('meta', {}) or {}
    weekday_raw = meta.get('weekday_num') or meta.get('weekday')
    try:
        weekday = int(weekday_raw) if weekday_raw is not None else 0
    except (TypeError, ValueError):
        weekday = 0

    all_rows: List[dict] = []

    # Upagrahas (require sun_lon)
    if sun_lon is not None:
        try:
            rows = sp5.emit_upagrahas(conn, chart_id, build_id, ayanamsha_id, sun_lon, saturn_lon)
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_upagrahas failed: %s", exc)

    # Saturn-derived points
    if saturn_lon is not None:
        try:
            rows = sp5.emit_saturn_derived(conn, chart_id, build_id, ayanamsha_id, saturn_lon, weekday)
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_saturn_derived failed: %s", exc)

    # Sahams (require lagna_lon + sun + moon)
    if graha_lons and lagna_lon is not None:
        try:
            rows = sp5.emit_sahams(
                chart_id, build_id, ayanamsha_id,
                graha_lons, lagna_lon,
                house_cusps=house_cusps_map,
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_sahams failed: %s", exc)

    # Chara Karakas
    if graha_lons:
        try:
            rows = sp5.emit_karakas(chart_id, build_id, ayanamsha_id, graha_lons)
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_karakas failed: %s", exc)

    # Karakamsa
    if graha_lons:
        navamsa = chart_output.get('navamsa', {}) or {}
        nav_ak_sign = navamsa.get('atmakaraka_sign') or navamsa.get('lagna_sign')
        try:
            rows = sp5.emit_karakamsa(
                chart_id, build_id, ayanamsha_id, graha_lons,
                navamsa_sign_of_ak=nav_ak_sign,
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_karakamsa failed: %s", exc)

    # Swamsa
    if lagna_lon is not None:
        try:
            rows = sp5.emit_swamsa(chart_id, build_id, ayanamsha_id, lagna_lon)
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_swamsa failed: %s", exc)

    # Arudhas
    if house_cusps_map and graha_lons:
        try:
            rows = sp5.emit_arudhas(
                chart_id, build_id, ayanamsha_id, house_cusps_map, graha_lons
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_arudhas failed: %s", exc)

    # Midpoints
    if graha_lons and lagna_lon is not None:
        try:
            rows = sp5.emit_midpoints(
                chart_id, build_id, ayanamsha_id, graha_lons, lagna_lon
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_midpoints failed: %s", exc)

    # KP ruling planets
    if lagna_lon is not None and moon_lon is not None:
        try:
            rows = sp5.emit_kp_ruling_planets(
                chart_id, build_id, ayanamsha_id, lagna_lon, moon_lon, weekday
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_kp_ruling_planets failed: %s", exc)

    # KP cuspal significators
    if house_cusps_map:
        try:
            rows = sp5.emit_kp_cuspal_significators(
                chart_id, build_id, ayanamsha_id, house_cusps_map
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_kp_cuspal_significators failed: %s", exc)

    # Esoteric bindus (Vimshottari / Bhrigu)
    if all([sun_lon, moon_lon, lagna_lon, rahu_lon, saturn_lon]):
        try:
            rows = sp5.emit_esoteric_bindus(
                conn, chart_id, build_id, ayanamsha_id,
                moon_lon=moon_lon, sun_lon=sun_lon,
                lagna_lon=lagna_lon, rahu_lon=rahu_lon, saturn_lon=saturn_lon,
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_esoteric_bindus failed: %s", exc)

    # Bhrigu Nadi points
    if moon_lon is not None and rahu_lon is not None and sun_lon is not None:
        try:
            rows = sp5.emit_bhrigu_nadi_points(
                chart_id, build_id, ayanamsha_id, moon_lon, rahu_lon, sun_lon
            )
            if rows:
                all_rows.extend(rows)
        except Exception as exc:
            logger.warning("A5 emit_bhrigu_nadi_points failed: %s", exc)

    if not all_rows:
        logger.warning(
            "A5 adapter: 0 rows collected for chart=%s ayanamsha=%s", chart_id, ayanamsha_id
        )
        return 0

    written = _write_rows(all_rows, conn, build_id, chart_id, ayanamsha_id)
    logger.info(
        "A5 adapter complete: chart=%s ayanamsha=%s rows=%d",
        chart_id, ayanamsha_id, written,
    )
    return written
