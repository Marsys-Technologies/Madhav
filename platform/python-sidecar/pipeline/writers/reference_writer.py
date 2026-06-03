"""
pipeline/writers/reference_writer.py
Seed writer for brahmagyan.reference asset.
Reads Python constants from panchang_engine.shastra_tables and populates
reference_* DB tables. Idempotent: uses ON CONFLICT DO NOTHING.
Run: python -m pipeline.writers.reference_writer
or:  python platform/python-sidecar/pipeline/writers/reference_writer.py
Requires: DATABASE_URL env var (same pattern as routers/panchang.py).
"""
import os, sys
import psycopg
from psycopg.rows import dict_row

# Adjust sys.path so the script runs both as __main__ and as a module.
# When run as __main__ from repo root or from python-sidecar/:
_HERE = os.path.dirname(__file__)
_SIDECAR_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

from panchang_engine.shastra_tables import (
    NAKSHATRA_NAMES, NAKSHATRA_DEITIES, NAKSHATRA_LORDS,
    TITHI_NAMES,
    YOGA_NAMES,
    KARANA_NAMES,
    VARA_NAMES,
    SIGN_NAMES, SIGN_LORDS,
    VARA_HORA_START,
    COMBUSTION_ORBS,
    EVENT_TABLES,
    RAHU_KALAM_INDEX, YAMAGANDAM_INDEX, GULIKA_INDEX,
)

CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]


def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


def write_nakshatra_attrs(conn) -> int:
    """
    Populates reference_nakshatra_attrs from NAKSHATRA_NAMES/DEITIES/LORDS.
    Returns number of rows inserted.
    """
    # NAKSHATRA_NAMES is 0-indexed; nakshatra_id is 1-based.
    citation = "BS §2; MC §3; Parasara Hora Shastra (Vimshottari Dasha chapter)"
    rows = []
    for i, name in enumerate(NAKSHATRA_NAMES):
        rows.append((i + 1, name, NAKSHATRA_DEITIES[i], NAKSHATRA_LORDS[i], citation))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_nakshatra_attrs
              (nakshatra_id, name, deity, lord, source_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (nakshatra_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_tithi_attrs(conn) -> int:
    """
    Populates reference_tithi_attrs from TITHI_NAMES (1..30).
    """
    citation = "MC §1; BS §2"
    rows = []
    for tid, name in TITHI_NAMES.items():
        paksha = "shukla" if tid <= 15 else "krishna"
        rows.append((tid, name, paksha, citation))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_tithi_attrs (tithi_id, name, paksha, source_citation)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (tithi_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_yoga_attrs(conn) -> int:
    """
    Populates reference_yoga_attrs from YOGA_NAMES (0-indexed, yoga_id 1-based).
    """
    citation = "MC §4; BS §2"
    rows = [(i + 1, name, citation) for i, name in enumerate(YOGA_NAMES)]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_yoga_attrs (yoga_id, name, source_citation)
            VALUES (%s, %s, %s)
            ON CONFLICT (yoga_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_karana_attrs(conn) -> int:
    """
    Populates reference_karana_attrs from KARANA_NAMES (0-indexed, karana_id 1-based).
    Movable = first 7 (ids 1-7), fixed = last 4 (ids 8-11).
    """
    citation = "MC §2; BS §2"
    rows = []
    for i, name in enumerate(KARANA_NAMES):
        karana_id = i + 1
        ktype = "movable" if karana_id <= 7 else "fixed"
        rows.append((karana_id, name, ktype, citation))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_karana_attrs (karana_id, name, karana_type, source_citation)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (karana_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_vara_attrs(conn) -> int:
    """
    Populates reference_vara_attrs from VARA_NAMES + inauspicious period indices.
    """
    citation = "VS; MC §1; DP (Drik Panchang) published tables"
    rows = []
    for vara_id, d in VARA_NAMES.items():
        rows.append((
            vara_id,
            d["name_sanskrit"],
            d["name_english"],
            d["lord"],
            d["color"],
            RAHU_KALAM_INDEX[vara_id],
            YAMAGANDAM_INDEX[vara_id],
            GULIKA_INDEX[vara_id],
            citation,
        ))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_vara_attrs
              (vara_id, name_sanskrit, name_english, lord, color,
               rahu_kalam_part, yamagandam_part, gulika_part, source_citation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (vara_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_sign_attrs(conn) -> int:
    """
    Populates reference_sign_attrs from SIGN_NAMES + SIGN_LORDS (0-indexed).
    sign_id is 1-based.
    """
    citation = "BS §1; Parasara Hora Shastra"
    rows = [(i + 1, name, SIGN_LORDS[i], citation) for i, name in enumerate(SIGN_NAMES)]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_sign_attrs (sign_id, name, lord, source_citation)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (sign_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def _build_chaldean_cycle_from(start_planet: str) -> list:
    """Return the 7-planet Chaldean hora cycle starting from start_planet."""
    idx = CHALDEAN_ORDER.index(start_planet)
    return [CHALDEAN_ORDER[(idx + i) % 7] for i in range(7)]


def write_hora_cycle(conn) -> int:
    """
    Populates reference_hora_cycle from VARA_HORA_START.
    """
    citation = "VS; Hora Sara (Prithuyashas)"
    rows = []
    for vara_id, start_planet in VARA_HORA_START.items():
        cycle = _build_chaldean_cycle_from(start_planet)
        rows.append((vara_id, start_planet, cycle, citation))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_hora_cycle
              (vara_id, hora_start_planet, chaldean_cycle, source_citation)
            VALUES (%s, %s, %s::text[], %s)
            ON CONFLICT (vara_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_combustion_orbs(conn) -> int:
    """
    Populates reference_combustion_orbs from COMBUSTION_ORBS.
    Shadow planets (Rahu, Ketu) have NULL orbs.
    """
    citation = "MC §6; Phaladeepika (Mantresvara) §4; DP convention"
    rows = []
    for planet, orbs in COMBUSTION_ORBS.items():
        rows.append((planet, orbs["direct"], orbs["retro"], citation))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_combustion_orbs
              (planet, orb_direct_deg, orb_retro_deg, source_citation)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (planet) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_event_quality(conn) -> int:
    """
    Populates reference_event_quality from EVENT_TABLES.
    EVENT_TABLES maps event_type -> {tithi: {id: score}, nakshatra: {...}, vara: {...}}.
    """
    # Citation map per event (from shastra_tables.py section headers)
    EVENT_CITATIONS = {
        "vivah":               "MC 3.2 (tithis); MC 3.5 (nakshatras); MC §3 (varas)",
        "griha_pravesh":       "MC 4.1 (tithis); MC 4.3 (nakshatras); MMP §Griha Pravesh",
        "vyapara":             "MC 5.1 (tithis); MMP §Vyapara; DP convention",
        "yatra":               "MC 6.1 (tithis); BS §Yatra; MMP §Yatra; DP convention",
        "property_purchase":   "MC 7.1; MMP §Property; DP convention",
        "mantra_initiation":   "MC 8.1 (diksha muhurta); BS §Diksha; DP convention",
    }
    rows = []
    for event_type, factors in EVENT_TABLES.items():
        citation = EVENT_CITATIONS.get(event_type, "MC; BS; DP")
        for factor_type in ("tithi", "nakshatra", "vara"):
            for factor_id, score in factors.get(factor_type, {}).items():
                rows.append((event_type, factor_type, int(factor_id), float(score), citation))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_event_quality
              (event_type, factor_type, factor_id, quality_score, source_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (event_type, factor_type, factor_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def write_inauspicious_periods(conn) -> int:
    """
    Populates reference_inauspicious_periods — one row per vara
    (mirrors vara_attrs inauspicious columns; kept as separate queryable table).
    """
    citation = "DP (Drik Panchang) published tables"
    rows = [
        (vara_id, RAHU_KALAM_INDEX[vara_id], YAMAGANDAM_INDEX[vara_id], GULIKA_INDEX[vara_id], citation)
        for vara_id in sorted(RAHU_KALAM_INDEX.keys())
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO reference_inauspicious_periods
              (vara_id, rahu_kalam_part, yamagandam_part, gulika_part, source_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (vara_id) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def run_all(db_url: str | None = None) -> dict:
    """
    Main entrypoint. Runs all writers in a single connection.
    Returns dict of {table_name: rows_attempted}.
    """
    url = db_url or get_db_url()
    results = {}
    with psycopg.connect(url) as conn:
        results["reference_nakshatra_attrs"]    = write_nakshatra_attrs(conn)
        results["reference_tithi_attrs"]        = write_tithi_attrs(conn)
        results["reference_yoga_attrs"]         = write_yoga_attrs(conn)
        results["reference_karana_attrs"]       = write_karana_attrs(conn)
        results["reference_vara_attrs"]         = write_vara_attrs(conn)
        results["reference_sign_attrs"]         = write_sign_attrs(conn)
        results["reference_hora_cycle"]         = write_hora_cycle(conn)
        results["reference_combustion_orbs"]    = write_combustion_orbs(conn)
        results["reference_event_quality"]      = write_event_quality(conn)
        results["reference_inauspicious_periods"] = write_inauspicious_periods(conn)
        conn.commit()
    return results


if __name__ == "__main__":
    import json
    r = run_all()
    print(json.dumps(r, indent=2))
    for table, count in r.items():
        print(f"  {table}: {count} rows attempted")
