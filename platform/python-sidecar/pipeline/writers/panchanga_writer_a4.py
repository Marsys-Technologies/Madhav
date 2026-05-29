"""
pipeline.writers.panchanga_writer_a4 — Write birth-day panchanga limbs to chart_facts.
A4-S1: 5 limbs — tithi, vara, nakshatra (ayanamsha-dependent), yoga, karana.
"""
import hashlib
import json
from datetime import datetime, timezone

ENGINE_VERSION = "natal_engine/0.2.0"

# panchanga_daily actual column names (confirmed against live schema)
_COL_TITHI_NAME = "tithi_name"
_COL_TITHI_NUM = "tithi"
_COL_PAKSHA = "paksha"
_COL_VARA = "vara"
_COL_VARA_LORD = "vara_lord"
_COL_MOON_NAK = "moon_nakshatra"
_COL_MOON_NAK_PADA = "moon_nakshatra_pada"
_COL_YOGA = "yoga"
_COL_KARANA = "karana"


def make_fact_id(category, subject, key, chart_id, ayanamsha_id, build_id):
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_citation_ref(category, subject, key, chart_id, ayanamsha_id):
    return (
        f"{category}.{subject}.{key}"
        f"@chart={chart_id[:8]}"
        f":ay={ayanamsha_id}"
        f":eng={ENGINE_VERSION}"
    )


def _row(
    chart_id, ayanamsha_id, build_id,
    fact_category, fact_subject, fact_key,
    value_text, value_number,
    citation_ref, citation_human,
    source_calc,
):
    fact_id = make_fact_id(fact_category, fact_subject, fact_key, chart_id, ayanamsha_id, build_id)
    provenance = json.dumps({
        "writer": "panchanga_writer_a4",
        "engine_version": ENGINE_VERSION,
        "ayanamsha_id": ayanamsha_id,
    })
    return (
        fact_id, chart_id, ayanamsha_id, build_id,
        fact_category,           # category (legacy col — mirrors fact_category)
        "D1",                    # divisional_chart
        "panchanga_writer_a4",   # source_section
        provenance,
        fact_category, fact_subject, fact_key,
        value_text, value_number,
        citation_ref, citation_human,
        source_calc,
        "single",                # verification_pass_status
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


def write_panchanga_limbs(conn, chart_id, build_id, birth_date, chart_outputs_by_ayanamsha):
    """
    Write 5 panchanga limbs to chart_facts.

    Args:
        conn: psycopg2 connection (or mock in tests)
        chart_id: str UUID of the chart
        build_id: str build identifier
        birth_date: str 'YYYY-MM-DD'
        chart_outputs_by_ayanamsha: dict {ayanamsha_id: chart_output_dict}
            Each value may contain 'nakshatra_moon' and 'nakshatra_moon_pada'
            for per-ayanamsha nakshatra override.

    Returns:
        int: number of rows written
    """
    row = conn.execute(
        "SELECT * FROM panchanga_daily WHERE date = %s LIMIT 1",
        (birth_date,),
    ).fetchone()

    if not row:
        raise ValueError(f"No panchanga_daily row for {birth_date}")

    # Support both dict-like and psycopg2 RealDictRow access
    def get(col):
        try:
            return row[col]
        except (KeyError, IndexError):
            return None

    tuples = []
    INVARIANT = "INVARIANT"

    # ── TITHI (INVARIANT) ───────────────────────────────────────────────────────
    tithi_fields = [
        ("name",                   get(_COL_TITHI_NAME),  "text"),
        ("number_in_lunar_month",  get(_COL_TITHI_NUM),   "num"),
        ("paksha",                 get(_COL_PAKSHA),       "text"),
    ]
    for key, value, vtype in tithi_fields:
        vtext = str(value) if vtype == "text" and value is not None else None
        vnum = float(value) if vtype == "num" and value is not None else None
        if key == "name":
            chum = f"Tithi at birth: {value}."
        elif key == "paksha":
            chum = f"Tithi paksha: {value}."
        else:
            chum = f"Tithi {key}: {value}."
        cref = make_citation_ref("panchanga_tithi", "TITHI_BIRTH", key, chart_id, INVARIANT)
        tuples.append(_row(
            chart_id, INVARIANT, build_id,
            "panchanga_tithi", "TITHI_BIRTH", key,
            vtext, vnum, cref, chum, "panchanga_writer_a4/tithi",
        ))

    # ── VARA (INVARIANT) ────────────────────────────────────────────────────────
    vara_fields = [
        ("name",  get(_COL_VARA),       "text"),
        ("lord",  get(_COL_VARA_LORD),  "text"),
    ]
    for key, value, vtype in vara_fields:
        chum = f"Vara at birth: {value}." if key == "name" else f"Vara lord: {value}."
        cref = make_citation_ref("panchanga_vara", "VARA_BIRTH", key, chart_id, INVARIANT)
        tuples.append(_row(
            chart_id, INVARIANT, build_id,
            "panchanga_vara", "VARA_BIRTH", key,
            str(value) if value is not None else None, None,
            cref, chum, "panchanga_writer_a4/vara",
        ))

    # ── YOGA (INVARIANT) ────────────────────────────────────────────────────────
    yoga_fields = [
        ("name", get(_COL_YOGA), "text"),
    ]
    for key, value, vtype in yoga_fields:
        chum = f"Yoga at birth: {value}."
        cref = make_citation_ref("panchanga_yoga", "YOGA_BIRTH", key, chart_id, INVARIANT)
        tuples.append(_row(
            chart_id, INVARIANT, build_id,
            "panchanga_yoga", "YOGA_BIRTH", key,
            str(value) if value is not None else None, None,
            cref, chum, "panchanga_writer_a4/yoga",
        ))

    # ── KARANA (INVARIANT) ──────────────────────────────────────────────────────
    karana_fields = [
        ("name", get(_COL_KARANA), "text"),
    ]
    for key, value, vtype in karana_fields:
        chum = f"Karana at birth: {value}."
        cref = make_citation_ref("panchanga_karana", "KARANA_BIRTH", key, chart_id, INVARIANT)
        tuples.append(_row(
            chart_id, INVARIANT, build_id,
            "panchanga_karana", "KARANA_BIRTH", key,
            str(value) if value is not None else None, None,
            cref, chum, "panchanga_writer_a4/karana",
        ))

    # ── NAKSHATRA (ayanamsha-DEPENDENT) ─────────────────────────────────────────
    db_nakshatra = get(_COL_MOON_NAK)
    db_pada = get(_COL_MOON_NAK_PADA)

    for aya_id, chart_out in chart_outputs_by_ayanamsha.items():
        nak_name = chart_out.get("nakshatra_moon", db_nakshatra)
        nak_pada = chart_out.get("nakshatra_moon_pada", db_pada)
        nak_fields = [
            ("name", nak_name, "text"),
            ("pada", nak_pada, "num"),
        ]
        for key, value, vtype in nak_fields:
            vtext = str(value) if vtype == "text" and value is not None else None
            vnum = float(value) if vtype == "num" and value is not None else None
            chum = (
                f"Moon nakshatra at birth: {value} ({aya_id})."
                if key == "name"
                else f"Nakshatra pada: {value} ({aya_id})."
            )
            cref = make_citation_ref(
                "panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", key, chart_id, aya_id
            )
            tuples.append(_row(
                chart_id, aya_id, build_id,
                "panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", key,
                vtext, vnum, cref, chum, "panchanga_writer_a4/nakshatra",
            ))

    if tuples:
        from psycopg2.extras import execute_values
        execute_values(conn, _INSERT_SQL, tuples)

    return len(tuples)
