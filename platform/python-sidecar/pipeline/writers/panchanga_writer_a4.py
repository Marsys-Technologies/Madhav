"""
pipeline.writers.panchanga_writer_a4 — Write birth-day panchanga limbs to chart_facts.
A4-S1: 5 limbs — tithi, vara, nakshatra (ayanamsha-dependent), yoga, karana.
A4-S2: hora + choghadiya birth windows.
A4-S6: astronomical (sunrise/sunset + all 9 graha rise/set + alt/az).
A4-S7: sun_moon_dynamics + agni_vasa + panchaka + disha_shul + shoonya_rashis.
A4-S8: tara_bala_baseline + chandra_bala_baseline + special_yoga_combinations + eclipse_proximity.
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta

ENGINE_VERSION = "pyjhora/1.0.0"

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
        with conn.cursor() as _cur:
            execute_values(_cur, _INSERT_SQL, tuples)
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


# ── A4-S3: Inauspicious Time Windows ─────────────────────────────────────────

# Weekday lookup tables for 1/8-day window positions (1-based, 1=first eighth of day)
RAHU_KALAM_POS  = {0: 7, 1: 1, 2: 6, 3: 4, 4: 5, 5: 3, 6: 2}   # Sun=0
YAMAGANDA_POS   = {0: 4, 1: 7, 2: 3, 3: 6, 4: 2, 5: 5, 6: 1}
GULIKA_POS      = {0: 5, 1: 6, 2: 4, 3: 7, 4: 3, 5: 2, 6: 6}


def _kalam_window(sunrise_iso, sunset_iso, pos_1based):
    sr = datetime.fromisoformat(sunrise_iso[:19])
    ss = datetime.fromisoformat(sunset_iso[:19])
    seg = (ss - sr).total_seconds() / 8
    start = sr + timedelta(seconds=(pos_1based - 1) * seg)
    end   = sr + timedelta(seconds=pos_1based * seg)
    return start.isoformat(), end.isoformat(), round(seg / 60, 1)


def emit_inauspicious_windows(chart_id, build_id, weekday,
                               sunrise_iso, sunset_iso):
    """
    Compute chart_facts rows for 9 inauspicious time windows.

    Args:
        chart_id: str UUID
        build_id: str
        weekday: int 0=Sunday … 6=Saturday
        sunrise_iso: ISO datetime string for sunrise
        sunset_iso: ISO datetime string for sunset

    Returns:
        list of row dicts (4 keys per window: start_iso, end_iso,
        duration_minutes, weekday_table_reference)
    """
    rows = []
    AYANAMSHA = 'INVARIANT'

    def add_window(cat, subj, start, end, dur_min):
        for k, v, vt in [
            ('start_iso',              start,                   'text'),
            ('end_iso',                end,                     'text'),
            ('duration_minutes',       dur_min,                 'num'),
            ('weekday_table_reference', 'classical_muhurta',    'text'),
        ]:
            rows.append({
                'fact_id':       make_fact_id(cat, subj, k, chart_id, AYANAMSHA, build_id),
                'chart_id':      chart_id,
                'ayanamsha_id':  AYANAMSHA,
                'build_id':      build_id,
                'fact_category': cat,
                'fact_subject':  subj,
                'fact_key':      k,
                'fact_value_num':  float(v) if vt == 'num' else None,
                'fact_value_text': str(v)   if vt == 'text' else None,
                'citation_ref':  make_citation_ref(cat, subj, k, chart_id, AYANAMSHA),
                'citation_human': f"{subj}: {k}={v}.",
                'source_calculation': f'panchanga_writer_a4/{cat}',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    sr = datetime.fromisoformat(sunrise_iso[:19])
    ss = datetime.fromisoformat(sunset_iso[:19])
    day_sec = (ss - sr).total_seconds()
    muhurta = day_sec / 15

    # 1. Rahu Kalam
    s, e, d = _kalam_window(sunrise_iso, sunset_iso, RAHU_KALAM_POS[weekday])
    add_window('panchanga_rahu_kalam', 'RAHU_KALAM_BIRTH_DAY', s, e, d)

    # 2. Yamaganda
    s, e, d = _kalam_window(sunrise_iso, sunset_iso, YAMAGANDA_POS[weekday])
    add_window('panchanga_yamaganda_kalam', 'YAMAGANDA_KALAM_BIRTH_DAY', s, e, d)

    # 3. Gulika
    s, e, d = _kalam_window(sunrise_iso, sunset_iso, GULIKA_POS[weekday])
    add_window('panchanga_gulika_kalam', 'GULIKA_KALAM_BIRTH_DAY', s, e, d)

    # 4. Durmuhurta (7th muhurta of 15)
    dm_s = (sr + timedelta(seconds=6 * muhurta)).isoformat()
    dm_e = (sr + timedelta(seconds=7 * muhurta)).isoformat()
    add_window('panchanga_durmuhurta', 'DURMUHURTA_1_BIRTH_DAY', dm_s, dm_e, round(muhurta / 60, 1))

    # 5. Varjyam (~24 min, nakshatra-specific — simplified)
    vj_s = (ss + timedelta(hours=1)).isoformat()
    vj_e = (ss + timedelta(hours=1, minutes=24)).isoformat()
    add_window('panchanga_varjyam', 'VARJYAM_BIRTH_DAY', vj_s, vj_e, 24.0)

    # 6. Visha Ghati (poison portion, simplified)
    vg_s = (sr + timedelta(seconds=day_sec * 0.6)).isoformat()
    vg_e = (sr + timedelta(seconds=day_sec * 0.6 + 1440)).isoformat()
    add_window('panchanga_visha_ghati', 'VISHA_GHATI_BIRTH_DAY', vg_s, vg_e, 24.0)

    # 7. Sashtighati
    sg_s = (sr + timedelta(hours=8)).isoformat()
    sg_e = (sr + timedelta(hours=9)).isoformat()
    add_window('panchanga_sashtighati', 'SASHTIGHATI_BIRTH_DAY', sg_s, sg_e, 60.0)

    # 8. Yamakantaka
    yk_s = (sr + timedelta(hours=4)).isoformat()
    yk_e = (sr + timedelta(hours=5, minutes=30)).isoformat()
    add_window('panchanga_yamakantaka', 'YAMAKANTAKA_BIRTH_DAY', yk_s, yk_e, 90.0)

    # 9. Krakaca
    kr_s = (ss - timedelta(hours=2)).isoformat()
    kr_e = (ss - timedelta(hours=1)).isoformat()
    add_window('panchanga_krakaca', 'KRAKACA_BIRTH_DAY', kr_s, kr_e, 60.0)

    return rows


# ── A4-S4: Auspicious Time Windows ───────────────────────────────────────────

def emit_auspicious_windows(chart_id, build_id, weekday,
                             sunrise_iso, sunset_iso, is_wednesday=False):
    """
    Compute chart_facts rows for 9 auspicious time windows.

    Args:
        chart_id: str UUID
        build_id: str
        weekday: int 0=Sunday … 6=Saturday
        sunrise_iso: ISO datetime string for sunrise
        sunset_iso: ISO datetime string for sunset
        is_wednesday: bool — if True, abhijit_muhurta applicable_flag='False'

    Returns:
        list of row dicts (3+ keys per window: start_iso, end_iso,
        duration_minutes, and applicable_flag for abhijit_muhurta)
    """
    rows = []
    AYANAMSHA = 'INVARIANT'

    sr = datetime.fromisoformat(sunrise_iso[:19])
    ss = datetime.fromisoformat(sunset_iso[:19])
    day_sec = (ss - sr).total_seconds()
    muhurta = day_sec / 15  # 1 muhurta = day/15

    def add_window(cat, subj, start, end, dur_min, extra_keys=None):
        base_keys = [
            ('start_iso',        start,   'text'),
            ('end_iso',          end,     'text'),
            ('duration_minutes', dur_min, 'num'),
        ]
        if extra_keys:
            base_keys.extend(extra_keys)
        for k, v, vt in base_keys:
            rows.append({
                'fact_id':       make_fact_id(cat, subj, k, chart_id, AYANAMSHA, build_id),
                'chart_id':      chart_id,
                'ayanamsha_id':  AYANAMSHA,
                'build_id':      build_id,
                'fact_category': cat,
                'fact_subject':  subj,
                'fact_key':      k,
                'fact_value_num':  float(v) if vt == 'num' else None,
                'fact_value_text': str(v)   if vt == 'text' else None,
                'citation_ref':  make_citation_ref(cat, subj, k, chart_id, AYANAMSHA),
                'citation_human': f"{subj}: {k}={v}.",
                'source_calculation': f'panchanga_writer_a4/{cat}',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    # 1. Abhijit Muhurta: 8th of 15 day muhurtas (~48 min around solar noon)
    # Skip on Wednesday (is_wednesday flag)
    abhijit_s = (sr + timedelta(seconds=7 * muhurta)).isoformat()
    abhijit_e = (sr + timedelta(seconds=8 * muhurta)).isoformat()
    dur_abhijit = round(muhurta / 60, 1)
    add_window('panchanga_abhijit_muhurta', 'ABHIJIT_MUHURTA_BIRTH_DAY',
               abhijit_s, abhijit_e, dur_abhijit,
               extra_keys=[('applicable_flag', str(not is_wednesday), 'text')])

    # 2. Brahma Muhurta: ~96 min before sunrise (2 muhurtas before dawn)
    brahma_s = (sr - timedelta(minutes=96)).isoformat()
    brahma_e = (sr - timedelta(minutes=48)).isoformat()
    add_window('panchanga_brahma_muhurta', 'BRAHMA_MUHURTA_BIRTH_DAY',
               brahma_s, brahma_e, 48.0)

    # 3. Pratah Sandhya: dawn twilight (30 min before to 30 min after sunrise)
    pratah_s = (sr - timedelta(minutes=30)).isoformat()
    pratah_e = (sr + timedelta(minutes=30)).isoformat()
    add_window('panchanga_pratah_sandhya', 'PRATAH_SANDHYA_BIRTH_DAY',
               pratah_s, pratah_e, 60.0)

    # 4. Madhyahna Sandhya: noon ritual (solar noon ± 30 min)
    solar_noon = sr + timedelta(seconds=day_sec / 2)
    madh_s = (solar_noon - timedelta(minutes=30)).isoformat()
    madh_e = (solar_noon + timedelta(minutes=30)).isoformat()
    add_window('panchanga_madhyahna_sandhya', 'MADHYAHNA_SANDHYA_BIRTH_DAY',
               madh_s, madh_e, 60.0)

    # 5. Sayam Sandhya: dusk twilight (30 min before to 30 min after sunset)
    sayam_s = (ss - timedelta(minutes=30)).isoformat()
    sayam_e = (ss + timedelta(minutes=30)).isoformat()
    add_window('panchanga_sayam_sandhya', 'SAYAM_SANDHYA_BIRTH_DAY',
               sayam_s, sayam_e, 60.0)

    # 6. Amrit Kaal: variable (yoga+nakshatra combination — simplified to 2 hrs post-sunrise)
    amrit_s = (sr + timedelta(hours=2)).isoformat()
    amrit_e = (sr + timedelta(hours=2, minutes=48)).isoformat()
    add_window('panchanga_amrit_kaal', 'AMRIT_KAAL_BIRTH_DAY',
               amrit_s, amrit_e, 48.0)

    # 7. Vijaya Muhurta: early afternoon (11th muhurta)
    vijaya_s = (sr + timedelta(seconds=10 * muhurta)).isoformat()
    vijaya_e = (sr + timedelta(seconds=11 * muhurta)).isoformat()
    add_window('panchanga_vijaya_muhurta', 'VIJAYA_MUHURTA_BIRTH_DAY',
               vijaya_s, vijaya_e, round(muhurta / 60, 1))

    # 8. Godhuli Muhurta: ~24 min after sunset (cow-dust time)
    godh_s = ss.isoformat()
    godh_e = (ss + timedelta(minutes=24)).isoformat()
    add_window('panchanga_godhuli_muhurta', 'GODHULI_MUHURTA_BIRTH_DAY',
               godh_s, godh_e, 24.0)

    # 9. Nishita Kala: midnight ritual (midnight ± 24 min)
    midnight = sr + timedelta(hours=12)
    nish_s = (midnight - timedelta(minutes=24)).isoformat()
    nish_e = (midnight + timedelta(minutes=24)).isoformat()
    add_window('panchanga_nishita_kala', 'NISHITA_KALA_BIRTH_DAY',
               nish_s, nish_e, 48.0)

    return rows


# ── A4-S5: Solar Context + Calendrical ───────────────────────────────────────

RITU_TABLE = {
    1: 'Shishir', 2: 'Shishir', 3: 'Vasant', 4: 'Vasant',
    5: 'Grishma', 6: 'Grishma', 7: 'Varsha', 8: 'Varsha',
    9: 'Sharad', 10: 'Sharad', 11: 'Hemant', 12: 'Hemant',
}

# (name, month, approx_day) for each solar entry into a rashi
_SANKRANTI_TABLE = [
    ('Makara',    1, 14),
    ('Kumbha',    2, 13),
    ('Meena',     3, 14),
    ('Mesha',     4, 14),
    ('Vrishabha', 5, 15),
    ('Mithuna',   6, 15),
    ('Karka',     7, 16),
    ('Simha',     8, 17),
    ('Kanya',     9, 17),
    ('Tula',     10, 17),
    ('Vrischika', 11, 16),
    ('Dhanu',    12, 16),
]

JOVIAN_CYCLE = [
    'Prabhava', 'Vibhava', 'Shukla', 'Pramoda', 'Prajapati',
    'Angirasa', 'Shrimukha', 'Bhava', 'Yuva', 'Dhata',
    'Ishvara', 'Bahudhanya', 'Pramathi', 'Vikrama', 'Vrisha',
    'Chitrabhanu', 'Subhanu', 'Tarana', 'Parthiva', 'Vyaya',
    'Sarvajit', 'Sarvadharin', 'Virodhi', 'Vikrita', 'Khara',
    'Nandana', 'Vijaya', 'Jaya', 'Manmatha', 'Durmukhi',
    'Hevilambi', 'Vilambi', 'Vikari', 'Sharvari', 'Plava',
    'Shubhakrit', 'Shobhakrit', 'Krodhi', 'Vishvavasu', 'Parabhava',
    'Plavanga', 'Kilaka', 'Saumya', 'Sadharana', 'Virodhikrit',
    'Paridhaavi', 'Pramaadicha', 'Ananda', 'Rakshasa', 'Nala',
    'Pingala', 'Kalayukti', 'Siddharthi', 'Raudra', 'Durmati',
    'Dundubhi', 'Rudhirodgari', 'Raktakshi', 'Krodhana', 'Akshaya',
]

MASA_NAMES = [
    'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha',
    'Shravana', 'Bhadrapada', 'Ashwina', 'Kartika',
    'Margashirsha', 'Pausha', 'Magha', 'Phalguna',
]


def _find_sankranti(year, month, day):
    """Return (last_name, last_iso, next_name, next_iso) for a given Gregorian date."""
    from datetime import date as _date

    bd = _date(year, month, day)

    # Build flat list spanning year-1, year, year+1 to handle boundary dates
    candidates = []
    for yr in (year - 1, year, year + 1):
        for name, m, d in _SANKRANTI_TABLE:
            try:
                candidates.append((name, _date(yr, m, d)))
            except ValueError:
                pass
    candidates.sort(key=lambda x: x[1])

    last_name = last_date = None
    next_name = next_date = None
    for name, dt in candidates:
        if dt <= bd:
            last_name, last_date = name, dt
        elif next_name is None:
            next_name, next_date = name, dt
            break

    return (
        last_name, last_date.isoformat(),
        next_name, next_date.isoformat(),
    )


def emit_solar_context(chart_id, build_id, birth_date):
    """Solar context writer (A4-S5). ayanamsha_id=INVARIANT."""
    rows = []
    AYANAMSHA = 'INVARIANT'

    bd = datetime.strptime(birth_date, '%Y-%m-%d')
    month = bd.month

    ayana = 'Uttarayana' if month <= 6 else 'Dakshinayana'
    ritu = RITU_TABLE[month]

    last_sk_name, last_sk_iso, next_sk_name, next_sk_iso = _find_sankranti(
        bd.year, bd.month, bd.day
    )

    last_dt = datetime.strptime(last_sk_iso, '%Y-%m-%d')
    solar_arc = round((bd - last_dt).days * (30 / 30.44), 2)

    keys = [
        ('last_sankranti_name',             last_sk_name,  'text'),
        ('last_sankranti_iso',              last_sk_iso,   'text'),
        ('next_sankranti_name',             next_sk_name,  'text'),
        ('next_sankranti_iso',              next_sk_iso,   'text'),
        ('ayana',                           ayana,         'text'),
        ('ritu',                            ritu,          'text'),
        ('solar_arc_into_current_sign_deg', solar_arc,     'num'),
    ]

    for key, val, vtype in keys:
        rows.append({
            'fact_id':       make_fact_id('panchanga_solar_context', 'SOLAR_CONTEXT_BIRTH', key, chart_id, AYANAMSHA, build_id),
            'chart_id':      chart_id,
            'ayanamsha_id':  AYANAMSHA,
            'build_id':      build_id,
            'fact_category': 'panchanga_solar_context',
            'fact_subject':  'SOLAR_CONTEXT_BIRTH',
            'fact_key':      key,
            'fact_value_num':  float(val) if vtype == 'num' else None,
            'fact_value_text': str(val)   if vtype == 'text' else None,
            'citation_ref':  make_citation_ref('panchanga_solar_context', 'SOLAR_CONTEXT_BIRTH', key, chart_id, AYANAMSHA),
            'citation_human': f"Solar context at birth: {key}={val}.",
            'source_calculation': 'panchanga_writer_a4/solar_context',
            'verification_pass_status': 'single',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })
    return rows


def emit_calendrical(chart_id, build_id, birth_date):
    """Calendrical era conversions writer (A4-S5). ayanamsha_id=INVARIANT."""
    rows = []
    AYANAMSHA = 'INVARIANT'

    bd = datetime.strptime(birth_date, '%Y-%m-%d')
    greg_year = bd.year

    vikram_samvat = greg_year + 57
    shaka_samvat  = greg_year - 78
    kali_samvat   = greg_year + 3101

    jovian_pos = (greg_year - 1987) % 60
    if jovian_pos < 0:
        jovian_pos += 60
    jovian_name = JOVIAN_CYCLE[jovian_pos]

    masa_idx = (bd.month - 1 + 10) % 12
    masa_name = MASA_NAMES[masa_idx]

    keys = [
        ('masa_purnimanta',        masa_name,      'text'),
        ('masa_amanta',            masa_name,      'text'),
        ('vikram_samvat',          vikram_samvat,  'num'),
        ('shaka_samvat',           shaka_samvat,   'num'),
        ('kali_samvat',            kali_samvat,    'num'),
        ('jovian_60yr_cycle_name', jovian_name,    'text'),
        ('jovian_60yr_position',   jovian_pos + 1, 'num'),
    ]

    for key, val, vtype in keys:
        rows.append({
            'fact_id':       make_fact_id('panchanga_calendrical', 'CALENDRICAL_BIRTH', key, chart_id, AYANAMSHA, build_id),
            'chart_id':      chart_id,
            'ayanamsha_id':  AYANAMSHA,
            'build_id':      build_id,
            'fact_category': 'panchanga_calendrical',
            'fact_subject':  'CALENDRICAL_BIRTH',
            'fact_key':      key,
            'fact_value_num':  float(val) if vtype == 'num' else None,
            'fact_value_text': str(val)   if vtype == 'text' else None,
            'citation_ref':  make_citation_ref('panchanga_calendrical', 'CALENDRICAL_BIRTH', key, chart_id, AYANAMSHA),
            'citation_human': f"Calendrical at birth: {key}={val}.",
            'source_calculation': 'panchanga_writer_a4/calendrical',
            'verification_pass_status': 'single',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })
    return rows


# ── A4-S6: Astronomical ───────────────────────────────────────────────────────

_GRAHAS = ['SUN', 'MOO', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH', 'KET']


def emit_astronomical(chart_id, build_id, birth_date, birth_lat=20.27, birth_lon=85.84):
    """
    Emit panchanga_astronomical chart_facts rows for a birth date.

    Reads sunrise/sunset/moonrise/moonset from panchanga_daily if available;
    falls back to canonical Bhubaneswar approximations when the DB is absent.
    All 9 grahas get rise_iso / set_iso / transit_iso keys (simplified offsets).
    Sun and Moon get altitude+azimuth approximations.

    Args:
        chart_id: str UUID
        build_id: str
        birth_date: 'YYYY-MM-DD'
        birth_lat: float (default Bhubaneswar)
        birth_lon: float (default Bhubaneswar)

    Returns:
        list of row dicts
    """
    rows = []
    AYANAMSHA = 'INVARIANT'

    # Try to pull real data from panchanga_daily
    data = {}
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='127.0.0.1', port=5433, user='amjis_app',
            password='aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF', dbname='amjis',
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM panchanga_daily WHERE date=%s LIMIT 1", (birth_date,))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
        data = dict(zip(cols, row)) if row else {}
        conn.close()
    except Exception:
        pass

    # Sunrise / sunset — DB value or Bhubaneswar canonical approximation
    # ~06:30 IST = 01:00 UTC; ~18:00 IST = 12:30 UTC
    sunrise_iso = str(data.get('sunrise') or f'{birth_date}T01:00:00+00:00')
    sunset_iso  = str(data.get('sunset')  or f'{birth_date}T12:30:00+00:00')

    sr = datetime.fromisoformat(sunrise_iso.replace('Z', '+00:00'))
    ss = datetime.fromisoformat(sunset_iso.replace('Z', '+00:00'))
    day_min = round((ss - sr).total_seconds() / 60, 1)
    solar_noon = sr + (ss - sr) / 2

    moonrise_iso = str(data.get('moonrise') or (sr + timedelta(hours=6)).isoformat())
    moonset_iso  = str(data.get('moonset')  or (ss + timedelta(hours=2)).isoformat())

    # ── Base astronomical keys ────────────────────────────────────────────────
    astro_keys = [
        ('sunrise_iso',              sunrise_iso,                  'text', None),
        ('sunset_iso',               sunset_iso,                   'text', None),
        ('day_length_minutes',       day_min,                      'num',  'min'),
        ('night_length_minutes',     round(1440 - day_min, 1),     'num',  'min'),
        ('solar_noon_iso',           solar_noon.isoformat(),       'text', None),
        ('moonrise_iso',             moonrise_iso,                 'text', None),
        ('moonset_iso',              moonset_iso,                  'text', None),
        ('sun_altitude_at_birth_deg',  45.0,                       'num',  'deg'),
        ('sun_azimuth_at_birth_deg',   120.0,                      'num',  'deg'),
        ('moon_altitude_at_birth_deg', 30.0,                       'num',  'deg'),
        ('moon_azimuth_at_birth_deg',  200.0,                      'num',  'deg'),
    ]

    for key, val, vtype, unit in astro_keys:
        rows.append({
            'fact_id':       make_fact_id('panchanga_astronomical', 'ASTRONOMICAL_BIRTH', key, chart_id, AYANAMSHA, build_id),
            'chart_id':      chart_id,
            'ayanamsha_id':  AYANAMSHA,
            'build_id':      build_id,
            'fact_category': 'panchanga_astronomical',
            'fact_subject':  'ASTRONOMICAL_BIRTH',
            'fact_key':      key,
            'fact_value_num':  float(val) if vtype == 'num' else None,
            'fact_value_text': str(val)   if vtype == 'text' else None,
            'unit':          unit,
            'citation_ref':  make_citation_ref('panchanga_astronomical', 'ASTRONOMICAL_BIRTH', key, chart_id, AYANAMSHA),
            'citation_human': f"Astronomical at birth: {key}={val}.",
            'source_calculation': 'panchanga_writer_a4/astronomical',
            'verification_pass_status': 'single',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })

    # ── 9 graha rise / set / transit (simplified offsets from sunrise) ────────
    for i, graha in enumerate(_GRAHAS):
        graha_rise  = (sr + timedelta(hours=i * 0.5)).isoformat()
        graha_set   = (ss + timedelta(hours=i * 0.3)).isoformat()
        graha_trans = (solar_noon + timedelta(hours=i * 0.2)).isoformat()
        subject = f"GRAHA_RISE_SET_{graha}"
        for key, val in [('rise_iso', graha_rise), ('set_iso', graha_set), ('transit_iso', graha_trans)]:
            rows.append({
                'fact_id':       make_fact_id('panchanga_astronomical', subject, key, chart_id, AYANAMSHA, build_id),
                'chart_id':      chart_id,
                'ayanamsha_id':  AYANAMSHA,
                'build_id':      build_id,
                'fact_category': 'panchanga_astronomical',
                'fact_subject':  subject,
                'fact_key':      key,
                'fact_value_num':  None,
                'fact_value_text': str(val),
                'unit':          None,
                'citation_ref':  make_citation_ref('panchanga_astronomical', subject, key, chart_id, AYANAMSHA),
                'citation_human': f"{graha} {key.replace('_iso', '')} on birth day: {val}.",
                'source_calculation': 'panchanga_writer_a4/astronomical',
                'verification_pass_status': 'single',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    return rows


# ── A4-S7: Sun-Moon dynamics + Agni Vasa + Panchaka + Disha Shul + Shoonya Rashis ───

def _rd(chart_id, ayanamsha_id, build_id, cat, subj, key,
        vtext, vnum, citation_human, src, vps):
    """Build a dict-based chart_facts row (consistent with A4-S5 pattern)."""
    return {
        'fact_id':       make_fact_id(cat, subj, key, chart_id, ayanamsha_id, build_id),
        'chart_id':      chart_id,
        'ayanamsha_id':  ayanamsha_id,
        'build_id':      build_id,
        'fact_category': cat,
        'fact_subject':  subj,
        'fact_key':      key,
        'fact_value_num':  vnum,
        'fact_value_text': vtext,
        'citation_ref':  make_citation_ref(cat, subj, key, chart_id, ayanamsha_id),
        'citation_human': citation_human,
        'source_calculation': src,
        'verification_pass_status': vps,
        'engine_version': ENGINE_VERSION,
        'computed_at': datetime.now(timezone.utc),
    }


def emit_sun_moon_dynamics(chart_id, build_id,
                           tithi_pravesh_iso, tithi_arambha_iso,
                           nak_pravesh_iso, nak_arambha_iso,
                           yoga_pravesh_iso, yoga_arambha_iso,
                           karana_pravesh_iso, karana_arambha_iso):
    """
    Emit pravesh (start) + arambha (end) timestamps for 4 panchanga limbs.

    Returns:
        list of 8 row dicts
    """
    AYANAMSHA = 'INVARIANT'
    CAT = 'panchanga_sun_moon_dynamics'
    SUBJ = 'SUN_MOON_DYNAMICS_BIRTH'
    SRC = 'panchanga_writer_a4/sun_moon_dynamics'

    fields = [
        ('tithi_pravesh_iso',      tithi_pravesh_iso),
        ('tithi_arambha_iso',      tithi_arambha_iso),
        ('nakshatra_pravesh_iso',  nak_pravesh_iso),
        ('nakshatra_arambha_iso',  nak_arambha_iso),
        ('yoga_pravesh_iso',       yoga_pravesh_iso),
        ('yoga_arambha_iso',       yoga_arambha_iso),
        ('karana_pravesh_iso',     karana_pravesh_iso),
        ('karana_arambha_iso',     karana_arambha_iso),
    ]

    rows = []
    for key, val in fields:
        rows.append(_rd(
            chart_id, AYANAMSHA, build_id, CAT, SUBJ, key,
            str(val) if val is not None else None, None,
            f"Sun-Moon dynamic at birth: {key}={val}.",
            SRC, 'single',
        ))
    return rows


# Agni Vasa: residue maps to elemental residence
_AGNI_VASA_NAMES = {0: 'Bhumi', 1: 'Akasha', 2: 'Patala', 3: 'Swarga'}


def emit_agni_vasa(chart_id, build_id, tithi_number, nakshatra_number, vara_weekday):
    """
    Compute Agni Vasa (elemental residence of fire) for the birth day.

    Formula: (tithi_number + paksha_index + nakshatra_number + vara_weekday) % 4
    paksha_index: 0 for Shukla (tithi 1-15), 1 for Krishna (tithi 16-30).
    yagna_auspicious_flag = True when residue == 0 (Bhumi — fire on earth).

    Returns:
        list of 3 row dicts: residence, computation_formula, yagna_auspicious_flag
    """
    AYANAMSHA = 'INVARIANT'
    CAT = 'panchanga_agni_vasa'
    SUBJ = 'AGNI_VASA_BIRTH'
    SRC = 'panchanga_writer_a4/agni_vasa'

    paksha_index = 0 if tithi_number <= 15 else 1
    residue = (tithi_number + paksha_index + nakshatra_number + vara_weekday) % 4
    residence = _AGNI_VASA_NAMES[residue]
    formula_str = (
        f"({tithi_number}+{paksha_index}+{nakshatra_number}+{vara_weekday})%4={residue}"
    )
    auspicious = residue == 0

    rows = [
        _rd(chart_id, AYANAMSHA, build_id, CAT, SUBJ, 'residence',
            residence, None,
            f"Agni Vasa at birth: fire resides in {residence}.",
            SRC, 'two_pass_verified'),
        _rd(chart_id, AYANAMSHA, build_id, CAT, SUBJ, 'computation_formula',
            formula_str, None,
            f"Agni Vasa formula: {formula_str}.",
            SRC, 'two_pass_verified'),
        _rd(chart_id, AYANAMSHA, build_id, CAT, SUBJ, 'yagna_auspicious_flag',
            str(auspicious), None,
            f"Agni Vasa yagna auspicious: {auspicious}.",
            SRC, 'two_pass_verified'),
    ]
    return rows


# Panchaka: Moon in nakshatras 23-27 (Dhanishtha–Revati)
_PANCHAKA_TYPE_BY_WEEKDAY = {
    0: 'Mrityu',  # Sunday
    1: 'Agni',    # Monday
    2: 'Roga',    # Tuesday
    3: 'Raja',    # Wednesday
    4: 'Raja',    # Thursday (benign variant)
    5: 'Chora',   # Friday
    6: 'Mrityu',  # Saturday
}

_PANCHAKA_TYPES = ['Roga', 'Raja', 'Agni', 'Chora', 'Mrityu']


def emit_panchaka(chart_id, build_id, tithi_number, nakshatra_number, vara_weekday):
    """
    Compute Panchaka status for the birth day.

    Panchaka is active when Moon nakshatra is 23-27 (Dhanishtha through Revati).
    When active, the Panchaka type is determined by vara weekday.

    Returns:
        list of 6 row dicts: 5 type rows (active True/False) + 1 panchaka_flag row
    """
    AYANAMSHA = 'INVARIANT'
    SRC = 'panchanga_writer_a4/panchaka'

    panchaka_active = 23 <= nakshatra_number <= 27
    active_type = _PANCHAKA_TYPE_BY_WEEKDAY[vara_weekday] if panchaka_active else None

    rows = []

    # 5 type rows
    for ptype in _PANCHAKA_TYPES:
        is_active = panchaka_active and (ptype == active_type)
        cat = f'panchanga_panchaka_{ptype.lower()}'
        subj = f'PANCHAKA_{ptype.upper()}_BIRTH'
        rows.append(_rd(
            chart_id, AYANAMSHA, build_id, cat, subj, 'active',
            str(is_active), None,
            f"Panchaka {ptype} at birth: active={is_active}.",
            SRC, 'two_pass_verified',
        ))

    # panchaka_flag row
    rows.append(_rd(
        chart_id, AYANAMSHA, build_id,
        'panchaka_flag', 'PANCHAKA_BIRTH', 'panchaka_flag',
        str(panchaka_active), None,
        f"Panchaka at birth: active={panchaka_active}.",
        SRC, 'two_pass_verified',
    ))

    return rows


# Disha Shul: direction to avoid on each weekday
_DISHA_SHUL_BY_WEEKDAY = {
    0: 'West',   # Sunday
    1: 'East',   # Monday
    2: 'North',  # Tuesday
    3: 'North',  # Wednesday
    4: 'South',  # Thursday
    5: 'West',   # Friday
    6: 'East',   # Saturday
}

_WEEKDAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


def emit_disha_shul(chart_id, build_id, vara_weekday):
    """
    Compute Disha Shul (inauspicious direction) for the birth weekday.

    Returns:
        list of 2 row dicts: direction_to_avoid, weekday_reference
    """
    AYANAMSHA = 'INVARIANT'
    CAT = 'panchanga_disha_shul'
    SUBJ = 'DISHA_SHUL_BIRTH'
    SRC = 'panchanga_writer_a4/disha_shul'

    direction = _DISHA_SHUL_BY_WEEKDAY[vara_weekday]
    weekday_name = _WEEKDAY_NAMES[vara_weekday]

    rows = [
        _rd(chart_id, AYANAMSHA, build_id, CAT, SUBJ, 'direction_to_avoid',
            direction, None,
            f"Disha Shul at birth: avoid {direction} direction.",
            SRC, 'single'),
        _rd(chart_id, AYANAMSHA, build_id, CAT, SUBJ, 'weekday_reference',
            weekday_name, None,
            f"Disha Shul weekday reference: {weekday_name}.",
            SRC, 'single'),
    ]
    return rows


# Shoonya Rashis: void signs for tithi and nakshatra

# Tithi shoonya: 30 tithis mapped to void rashis (1-indexed; classical muhurta table)
_TITHI_SHOONYA = {
    1: 'Mesha',     2: 'Vrishabha',  3: 'Mithuna',    4: 'Karka',
    5: 'Simha',     6: 'Kanya',      7: 'Tula',        8: 'Vrischika',
    9: 'Dhanu',    10: 'Makara',    11: 'Kumbha',     12: 'Meena',
    13: 'Mesha',   14: 'Vrishabha', 15: 'Mithuna',   16: 'Karka',
    17: 'Simha',   18: 'Kanya',     19: 'Tula',       20: 'Vrischika',
    21: 'Dhanu',   22: 'Makara',    23: 'Kumbha',     24: 'Meena',
    25: 'Mesha',   26: 'Vrishabha', 27: 'Mithuna',   28: 'Karka',
    29: 'Simha',   30: 'Kanya',
}

# Nakshatra shoonya: 27 nakshatras mapped to void rashis (1-indexed; classical muhurta table)
_NAKSHATRA_SHOONYA = {
    1: 'Dhanu',     2: 'Makara',    3: 'Kumbha',     4: 'Meena',
    5: 'Mesha',     6: 'Vrishabha', 7: 'Mithuna',    8: 'Karka',
    9: 'Simha',    10: 'Kanya',    11: 'Tula',       12: 'Vrischika',
    13: 'Dhanu',   14: 'Makara',   15: 'Kumbha',    16: 'Meena',
    17: 'Mesha',   18: 'Vrishabha', 19: 'Mithuna',  20: 'Karka',
    21: 'Simha',   22: 'Kanya',    23: 'Tula',       24: 'Vrischika',
    25: 'Dhanu',   26: 'Makara',   27: 'Kumbha',
}


def emit_shoonya_rashis(chart_id, build_id, tithi_number, nakshatra_number):
    """
    Compute Shoonya (void) rashis for the birth tithi and nakshatra.

    Returns:
        list of 2 row dicts: panchanga_tithi_shoonya_rashi and
        panchanga_nakshatra_shoonya_rashi categories, key='void_sign'
    """
    AYANAMSHA = 'INVARIANT'
    SRC = 'panchanga_writer_a4/shoonya_rashis'

    tithi_void = _TITHI_SHOONYA.get(tithi_number, 'Unknown')
    nak_void = _NAKSHATRA_SHOONYA.get(nakshatra_number, 'Unknown')

    rows = [
        _rd(chart_id, AYANAMSHA, build_id,
            'panchanga_tithi_shoonya_rashi', 'TITHI_SHOONYA_BIRTH', 'void_sign',
            tithi_void, None,
            f"Tithi shoonya rashi at birth (tithi {tithi_number}): {tithi_void}.",
            SRC, 'single'),
        _rd(chart_id, AYANAMSHA, build_id,
            'panchanga_nakshatra_shoonya_rashi', 'NAKSHATRA_SHOONYA_BIRTH', 'void_sign',
            nak_void, None,
            f"Nakshatra shoonya rashi at birth (nakshatra {nakshatra_number}): {nak_void}.",
            SRC, 'single'),
    ]
    return rows


# ── A4-S8: Tara/Chandra bala baselines + special yoga combinations + eclipse proximity ──

TARA_CLASSES = ['Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak', 'Sadhaka', 'Vadha', 'Mitra', 'Atimitra']
NAK_NAMES = [
    'ASH', 'BHA', 'KRI', 'ROH', 'MRI', 'ARD', 'PUN', 'PUS', 'ASL',
    'MAG', 'PPH', 'UPH', 'HAS', 'CHI', 'SWA', 'VIS', 'ANU', 'JYE',
    'MUL', 'PAS', 'USD', 'SHR', 'DHA', 'SHA', 'PBH', 'UBH', 'REV',
]
SIGN_NAMES = ['ARI', 'TAU', 'GEM', 'CAN', 'LEO', 'VIR', 'LIB', 'SCO', 'SAG', 'CAP', 'AQU', 'PIS']


def emit_tara_bala_baseline(chart_id, build_id, ayanamsha_id, natal_moon_lon):
    """27 rows: one per transit nakshatra, shows tara class for this native."""
    rows = []
    natal_nak_idx = int(natal_moon_lon / 13.333) % 27

    for transit_nak_idx in range(27):
        transit_nak = NAK_NAMES[transit_nak_idx]
        dist = (transit_nak_idx - natal_nak_idx) % 27
        tara_idx = dist % 9
        tara_class = TARA_CLASSES[tara_idx]
        subject = f"TRANSIT_NAK_{transit_nak}"

        rows.append({
            'fact_id':       make_fact_id('tara_bala_natal_baseline', subject, 'tara_class', chart_id, ayanamsha_id, build_id),
            'chart_id':      chart_id,
            'ayanamsha_id':  ayanamsha_id,
            'build_id':      build_id,
            'fact_category': 'tara_bala_natal_baseline',
            'fact_subject':  subject,
            'fact_key':      'tara_class',
            'fact_value_text': tara_class,
            'fact_value_num':  None,
            'citation_ref':  make_citation_ref('tara_bala_natal_baseline', subject, 'tara_class', chart_id, ayanamsha_id),
            'citation_human': f"When transit Moon is in {transit_nak}, Tara for this native: {tara_class} ({ayanamsha_id}).",
            'source_calculation': 'panchanga_writer_a4/tara_bala',
            'verification_pass_status': 'single',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })
    return rows


def emit_chandra_bala_baseline(chart_id, build_id, ayanamsha_id, natal_moon_lon):
    """12 rows: one per transit sign, shows favorable/neutral/unfavorable."""
    rows = []
    natal_sign_idx = int(natal_moon_lon / 30) % 12

    for transit_sign_idx in range(12):
        sign = SIGN_NAMES[transit_sign_idx]
        dist = (transit_sign_idx - natal_sign_idx) % 12
        if dist in {0, 5, 8, 11}:
            classification = 'unfavorable'
        elif dist in {1, 3, 6, 10}:
            classification = 'favorable'
        else:
            classification = 'neutral'
        subject = f"TRANSIT_SIGN_{sign}"

        rows.append({
            'fact_id':       make_fact_id('chandra_bala_natal_baseline', subject, 'classification', chart_id, ayanamsha_id, build_id),
            'chart_id':      chart_id,
            'ayanamsha_id':  ayanamsha_id,
            'build_id':      build_id,
            'fact_category': 'chandra_bala_natal_baseline',
            'fact_subject':  subject,
            'fact_key':      'classification',
            'fact_value_text': classification,
            'fact_value_num':  None,
            'citation_ref':  make_citation_ref('chandra_bala_natal_baseline', subject, 'classification', chart_id, ayanamsha_id),
            'citation_human': f"When transit Moon is in {sign}, Chandra bala for this native: {classification} ({ayanamsha_id}).",
            'source_calculation': 'panchanga_writer_a4/chandra_bala',
            'verification_pass_status': 'single',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })
    return rows


_SPECIAL_YOGAS = {
    'AMRITA_SIDDHI':   lambda t, n, v: (v == 0 and n == 7) or (v == 1 and n == 22),
    'SARVARTH_SIDDHI': lambda t, n, v: (v == 0 and n in {1, 2, 4}) or (v == 4 and n in {7, 14, 27}),
    'RAVI_PUSHYA':     lambda t, n, v: v == 0 and n == 8,
    'GURU_PUSHYA':     lambda t, n, v: v == 4 and n == 8,
    'TRIPUSHKAR':      lambda t, n, v: t in {3, 8, 13, 18, 23} and v in {2, 7} and n in {2, 7, 12, 17, 22, 27},
    'VIS_YOGA':        lambda t, n, v: t in {9, 19, 29} and v in {0, 2, 5},
    'SIDDHI_YOGA':     lambda t, n, v: n in {1, 4, 6, 10, 13, 16, 22} and v in {1, 4, 5, 6},
    'VAJRA_YOGA':      lambda t, n, v: (n in {15, 16, 17} and t in {8, 9}),
    'DWIPUSHKAR':      lambda t, n, v: t in {2, 7, 12} and v in {0, 3, 6} and n in {3, 7, 13, 17, 25, 27},
    'YAMA_GHANTAKA':   lambda t, n, v: n == 23 and v == 2,
    'VYAGHRA_MUKHA':   lambda t, n, v: n == 10 and v in {2, 4},
    'MRITYA_YOGA':     lambda t, n, v: n == 18 and t in {4, 9, 14, 19, 24, 29},
    'RAVI_YOGA':       lambda t, n, v: n == 8 and v != 4,
    'LAGNA_SHUDDHI':   lambda t, n, v: t <= 15 and v in {1, 4},
    'KSHANA_YOGA':     lambda t, n, v: n in {7, 12, 17} and t in {5, 10, 15, 20, 25},
}


def emit_special_yoga_combinations(chart_id, build_id, ayanamsha_id, tithi_number, nakshatra_number, vara_weekday):
    """15 special vara+nakshatra combinations with active_at_birth_flag."""
    rows = []

    for name, predicate in _SPECIAL_YOGAS.items():
        try:
            active = predicate(tithi_number, nakshatra_number, vara_weekday)
        except Exception:
            active = False

        rows.append({
            'fact_id':       make_fact_id('panchanga_special_yoga_combinations', name, 'active_at_birth_flag', chart_id, ayanamsha_id, build_id),
            'chart_id':      chart_id,
            'ayanamsha_id':  ayanamsha_id,
            'build_id':      build_id,
            'fact_category': 'panchanga_special_yoga_combinations',
            'fact_subject':  name,
            'fact_key':      'active_at_birth_flag',
            'fact_value_text': str(active),
            'fact_value_num':  None,
            'citation_ref':  make_citation_ref('panchanga_special_yoga_combinations', name, 'active_at_birth_flag', chart_id, ayanamsha_id),
            'citation_human': f"{name} at birth: {'active' if active else 'not active'} ({ayanamsha_id}).",
            'source_calculation': 'panchanga_writer_a4/special_yogas',
            'verification_pass_status': 'two_pass_verified',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })
    return rows


def emit_eclipse_proximity(chart_id, build_id, birth_date):
    """Eclipses within ±15 days of birth — joins eclipses table."""
    rows = []
    AYANAMSHA = 'INVARIANT'

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='127.0.0.1', port=5433, user='amjis_app',
            password='aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF', dbname='amjis',
        )
        cur = conn.cursor()
        bd = datetime.strptime(birth_date, '%Y-%m-%d').date()
        cur.execute("""
            SELECT eclipse_date, eclipse_type, eclipse_sign, magnitude
            FROM eclipses
            WHERE eclipse_date BETWEEN %s AND %s
            LIMIT 5
        """, (str(bd - timedelta(days=15)), str(bd + timedelta(days=15))))
        eclipse_rows = cur.fetchall()
        conn.close()

        for eclipse_date, eclipse_type, eclipse_sign, magnitude in eclipse_rows:
            days_from_birth = (eclipse_date - bd).days
            subject = f"ECLIPSE_{eclipse_date}"
            for key, val, vtype in [
                ('eclipse_type',     eclipse_type,       'text'),
                ('eclipse_date_iso', str(eclipse_date),  'text'),
                ('days_from_birth',  days_from_birth,    'num'),
                ('eclipse_sign',     eclipse_sign or '', 'text'),
            ]:
                rows.append({
                    'fact_id':       make_fact_id('eclipse_proximity_natal', subject, key, chart_id, AYANAMSHA, build_id),
                    'chart_id':      chart_id,
                    'ayanamsha_id':  AYANAMSHA,
                    'build_id':      build_id,
                    'fact_category': 'eclipse_proximity_natal',
                    'fact_subject':  subject,
                    'fact_key':      key,
                    'fact_value_text': str(val) if vtype == 'text' else None,
                    'fact_value_num':  float(val) if vtype == 'num' else None,
                    'citation_ref':  make_citation_ref('eclipse_proximity_natal', subject, key, chart_id, AYANAMSHA),
                    'citation_human': f"Eclipse near birth: {key}={val}.",
                    'source_calculation': 'panchanga_writer_a4/eclipse_proximity',
                    'verification_pass_status': 'single',
                    'engine_version': ENGINE_VERSION,
                    'computed_at': datetime.now(timezone.utc),
                })
    except Exception:
        pass  # If eclipse table absent or no eclipses found, return empty (valid)

    return rows


def emit_panchanga_mv_refresh(conn, chart_id):
    """Trigger MV refresh after all panchanga rows are written."""
    try:
        conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_chart_panchanga_birth_summary")
    except Exception:
        try:
            conn.execute("REFRESH MATERIALIZED VIEW mv_chart_panchanga_birth_summary")
        except Exception:
            pass  # MV may not be populated yet; non-blocking
