"""
pipeline.writers.panchanga_writer_a4 — Write birth-day panchanga limbs to chart_facts.
A4-S1: 5 limbs — tithi, vara, nakshatra (ayanamsha-dependent), yoga, karana.
A4-S2: hora + choghadiya birth windows.
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta

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


# ── A4-S2: Hora + Choghadiya ─────────────────────────────────────────────────

_IST = timezone(timedelta(hours=5, minutes=30))

HORA_LORDS_FROM_WEEKDAY = {
    0: ['SUN', 'VEN', 'MER', 'MOO', 'SAT', 'JUP', 'MAR'],  # Sunday
    1: ['MOO', 'SAT', 'JUP', 'MAR', 'SUN', 'VEN', 'MER'],  # Monday
    2: ['MAR', 'SUN', 'VEN', 'MER', 'MOO', 'SAT', 'JUP'],  # Tuesday
    3: ['MER', 'MOO', 'SAT', 'JUP', 'MAR', 'SUN', 'VEN'],  # Wednesday
    4: ['JUP', 'MAR', 'SUN', 'VEN', 'MER', 'MOO', 'SAT'],  # Thursday
    5: ['VEN', 'MER', 'MOO', 'SAT', 'JUP', 'MAR', 'SUN'],  # Friday
    6: ['SAT', 'JUP', 'MAR', 'SUN', 'VEN', 'MER', 'MOO'],  # Saturday
}

_HORA_SHUBH = {'JUP', 'VEN', 'MER', 'MOO'}

CHOGHADIYA_SEQUENCE_DAY = {
    0: ['Udveg', 'Char', 'Labh', 'Amrit', 'Kaal', 'Shubh', 'Rog', 'Udveg'],  # Sunday
    1: ['Amrit', 'Kaal', 'Shubh', 'Rog', 'Udveg', 'Char', 'Labh', 'Amrit'],  # Monday
    2: ['Rog', 'Udveg', 'Char', 'Labh', 'Amrit', 'Kaal', 'Shubh', 'Rog'],    # Tuesday
    3: ['Labh', 'Amrit', 'Kaal', 'Shubh', 'Rog', 'Udveg', 'Char', 'Labh'],   # Wednesday
    4: ['Shubh', 'Rog', 'Udveg', 'Char', 'Labh', 'Amrit', 'Kaal', 'Shubh'],  # Thursday
    5: ['Char', 'Labh', 'Amrit', 'Kaal', 'Shubh', 'Rog', 'Udveg', 'Char'],   # Friday
    6: ['Kaal', 'Shubh', 'Rog', 'Udveg', 'Char', 'Labh', 'Amrit', 'Kaal'],   # Saturday
}

CHOGHADIYA_CLASSIFICATION = {
    'Amrit': 'shubh', 'Shubh': 'shubh', 'Labh': 'shubh', 'Char': 'shubh',
    'Kaal': 'ashubh', 'Rog': 'ashubh', 'Udveg': 'ashubh',
}

_CHOGHADIYA_LORD = {
    'Amrit': 'MOO', 'Shubh': 'VEN', 'Labh': 'MER', 'Char': 'MER',
    'Kaal': 'SAT', 'Rog': 'MAR', 'Udveg': 'SUN',
}


def _parse_hm(birth_date, time_str):
    """Parse 'HH:MM' or 'HH:MM:SS' + birth_date into an IST-aware datetime."""
    parts = time_str.strip().split(':')
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) > 2 else 0
    y, mo, d = (int(x) for x in birth_date.split('-'))
    return datetime(y, mo, d, h, m, s, tzinfo=_IST)


def emit_hora_birth(chart_id, build_id, birth_time, sunrise_time, weekday, birth_date):
    """
    Compute chart_facts rows for panchanga_hora_birth (6 keys).

    Args:
        chart_id: str UUID
        build_id: str
        birth_time: 'HH:MM' or 'HH:MM:SS' in IST
        sunrise_time: 'HH:MM' or 'HH:MM:SS' in IST
        weekday: int 0=Sunday … 6=Saturday
        birth_date: 'YYYY-MM-DD'

    Returns:
        list of 6 row tuples (hora_number, lord, day_or_night, classification,
        start_iso, end_iso)
    """
    birth_dt = _parse_hm(birth_date, birth_time)
    sunrise_dt = _parse_hm(birth_date, sunrise_time)

    elapsed_minutes = (birth_dt - sunrise_dt).total_seconds() / 60
    if elapsed_minutes < 0:
        elapsed_minutes += 1440  # handle past-midnight case

    hora_num = int(elapsed_minutes / 60) + 1  # 1-indexed
    hora_num = min(max(hora_num, 1), 24)

    sequence = HORA_LORDS_FROM_WEEKDAY[weekday]
    lord = sequence[(hora_num - 1) % 7]
    day_night = 'day' if hora_num <= 12 else 'night'
    classification = 'shubh' if lord in _HORA_SHUBH else 'ashubh'

    start_dt = sunrise_dt + timedelta(minutes=(hora_num - 1) * 60)
    end_dt = sunrise_dt + timedelta(minutes=hora_num * 60)

    fields = [
        ('hora_number',    hora_num,             'num'),
        ('lord',           lord,                 'text'),
        ('day_or_night',   day_night,            'text'),
        ('classification', classification,        'text'),
        ('start_iso',      start_dt.isoformat(), 'text'),
        ('end_iso',        end_dt.isoformat(),   'text'),
    ]

    rows = []
    for key, val, vtype in fields:
        cref = make_citation_ref('panchanga_hora_birth', 'HORA_BIRTH', key, chart_id, 'INVARIANT')
        chum = f"Hora at birth: lord={val}." if key == 'lord' else f"Hora {key}: {val}."
        rows.append(_row(
            chart_id, 'INVARIANT', build_id,
            'panchanga_hora_birth', 'HORA_BIRTH', key,
            str(val) if vtype == 'text' else None,
            float(val) if vtype == 'num' else None,
            cref, chum, 'panchanga_writer_a4/hora',
        ))
    return rows


def emit_choghadiya_birth(chart_id, build_id, birth_time, sunrise_time, sunset_time, weekday, birth_date):
    """
    Compute chart_facts rows for panchanga_choghadiya_birth (6 keys).

    Args:
        chart_id: str UUID
        build_id: str
        birth_time: 'HH:MM' or 'HH:MM:SS' in IST
        sunrise_time: 'HH:MM' or 'HH:MM:SS' in IST
        sunset_time: 'HH:MM' or 'HH:MM:SS' in IST
        weekday: int 0=Sunday … 6=Saturday
        birth_date: 'YYYY-MM-DD'

    Returns:
        list of 6 row tuples (choghadiya_number, name, lord, classification,
        start_iso, end_iso)
    """
    birth_dt = _parse_hm(birth_date, birth_time)
    sunrise_dt = _parse_hm(birth_date, sunrise_time)
    sunset_dt = _parse_hm(birth_date, sunset_time)

    day_secs = (sunset_dt - sunrise_dt).total_seconds()
    segment_secs = day_secs / 8
    elapsed_secs = (birth_dt - sunrise_dt).total_seconds()
    if elapsed_secs < 0:
        elapsed_secs += 86400

    if elapsed_secs < day_secs:
        seg_idx = min(int(elapsed_secs / segment_secs), 7)
        chog_name = CHOGHADIYA_SEQUENCE_DAY[weekday][seg_idx]
        chog_num = seg_idx + 1  # 1–8 day
        start_dt = sunrise_dt + timedelta(seconds=seg_idx * segment_secs)
        end_dt = sunrise_dt + timedelta(seconds=(seg_idx + 1) * segment_secs)
    else:
        # Night choghadiya (9–16)
        night_secs = 86400 - day_secs
        night_segment_secs = night_secs / 8
        night_elapsed = elapsed_secs - day_secs
        seg_idx = min(int(night_elapsed / night_segment_secs), 7)
        next_weekday = (weekday + 1) % 7
        chog_name = CHOGHADIYA_SEQUENCE_DAY[next_weekday][seg_idx]
        chog_num = seg_idx + 9  # 9–16 night
        start_dt = sunset_dt + timedelta(seconds=seg_idx * night_segment_secs)
        end_dt = sunset_dt + timedelta(seconds=(seg_idx + 1) * night_segment_secs)

    lord = _CHOGHADIYA_LORD.get(chog_name, 'SUN')
    classification = CHOGHADIYA_CLASSIFICATION.get(chog_name, 'mishrit')

    fields = [
        ('choghadiya_number', chog_num,              'num'),
        ('name',              chog_name,              'text'),
        ('lord',              lord,                   'text'),
        ('classification',    classification,          'text'),
        ('start_iso',         start_dt.isoformat(),   'text'),
        ('end_iso',           end_dt.isoformat(),     'text'),
    ]

    rows = []
    for key, val, vtype in fields:
        cref = make_citation_ref('panchanga_choghadiya_birth', 'CHOGHADIYA_BIRTH', key, chart_id, 'INVARIANT')
        chum = f"Choghadiya at birth: {val}."
        rows.append(_row(
            chart_id, 'INVARIANT', build_id,
            'panchanga_choghadiya_birth', 'CHOGHADIYA_BIRTH', key,
            str(val) if vtype == 'text' else None,
            float(val) if vtype == 'num' else None,
            cref, chum, 'panchanga_writer_a4/choghadiya',
        ))
    return rows
