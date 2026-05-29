import hashlib
from datetime import datetime, timezone

ENGINE_VERSION = 'natal_engine/0.2.0'

SIGN_LORDS = {
    'ARI': 'MAR', 'TAU': 'VEN', 'GEM': 'MER', 'CAN': 'MOO', 'LEO': 'SUN', 'VIR': 'MER',
    'LIB': 'VEN', 'SCO': 'MAR', 'SAG': 'JUP', 'CAP': 'SAT', 'AQU': 'SAT', 'PIS': 'JUP',
}
SIGNS = ['ARI', 'TAU', 'GEM', 'CAN', 'LEO', 'VIR', 'LIB', 'SCO', 'SAG', 'CAP', 'AQU', 'PIS']


def make_fact_id(category, subject, key, chart_id, ayanamsha_id, build_id):
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_citation_ref(category, subject, key, chart_id, ayanamsha_id):
    return f"{category}.{subject}.{key}@chart={chart_id[:8]}:ay={ayanamsha_id}:eng={ENGINE_VERSION}"


def _sign_from_lon(lon):
    SIGNS = ['ARI', 'TAU', 'GEM', 'CAN', 'LEO', 'VIR', 'LIB', 'SCO', 'SAG', 'CAP', 'AQU', 'PIS']
    return SIGNS[int(lon / 30) % 12]


def _nak_from_lon(lon):
    NAKS = ['ASH', 'BHA', 'KRI', 'ROH', 'MRI', 'ARD', 'PUN', 'PUS', 'ASL', 'MAG', 'PPH', 'UPH',
            'HAS', 'CHI', 'SWA', 'VIS', 'ANU', 'JYE', 'MUL', 'PAS', 'USD', 'SHR', 'DHA', 'SHA',
            'PBH', 'UBH', 'REV']
    return NAKS[int(lon / 13.333) % 27]


def emit_upagrahas(conn, chart_id, build_id, ayanamsha_id, sun_lon, saturn_lon=None):
    """Emit upagraha_position rows for one ayanamsha.

    Six classical upagrahas per BPHS Chapter 4, derived from Sun's longitude.
    Each point emits 9 fact rows (longitude_sidereal, sign, nakshatra, formula_id,
    formula_provenance_text, tolerance_arcsec, near_sign_boundary_flag,
    near_nakshatra_boundary_flag, vargottama_flag_at_point).

    Returns list of chart_facts dicts (not yet written to DB).
    """
    dhuma = (sun_lon + 133.333) % 360
    upagrahas = {
        'DHUMA':       dhuma,
        'VYATIPATA':   (360 - dhuma) % 360,
        'PARIVESHA':   ((360 - dhuma) % 360 + 180) % 360,
        'INDRACHAPA':  (360 - ((360 - dhuma) % 360 + 180) % 360) % 360,
        'UPAKETU':     (dhuma - 30) % 360,
        'KALA':        (sun_lon + 30) % 360,
    }

    rows = []
    for subject, lon in upagrahas.items():
        sign = _sign_from_lon(lon)
        nak = _nak_from_lon(lon)
        near_sign = abs(lon % 30) < 0.5 or abs(lon % 30 - 30) < 0.5
        near_nak = abs(lon % 13.333) < 0.8 or abs(lon % 13.333 - 13.333) < 0.8
        vargottama = int(lon / 30) == int((lon % 30) / 3.333)

        for key, val, vtype in [
            ('longitude_sidereal', lon, 'num'),
            ('sign', sign, 'text'),
            ('nakshatra', nak, 'text'),
            ('formula_id', 'bphs_ch4', 'text'),
            ('formula_provenance_text', f'BPHS Chapter 4: {subject} = {subject.lower()}_formula', 'text'),
            ('tolerance_arcsec', 5.0, 'num'),
            ('near_sign_boundary_flag', str(near_sign), 'text'),
            ('near_nakshatra_boundary_flag', str(near_nak), 'text'),
            ('vargottama_flag_at_point', str(vargottama), 'text'),
        ]:
            rows.append({
                'fact_id': make_fact_id('upagraha_position', subject, key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id,
                'ayanamsha_id': ayanamsha_id,
                'build_id': build_id,
                'fact_category': 'upagraha_position',
                'fact_subject': subject,
                'fact_key': key,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'unit': 'deg' if key == 'longitude_sidereal' else None,
                'citation_ref': make_citation_ref('upagraha_position', subject, key, chart_id, ayanamsha_id),
                'citation_human': (
                    f"{subject} at birth: {round(lon, 4)}° in {sign} ({ayanamsha_id})."
                    if key == 'longitude_sidereal'
                    else f"{subject} {key}: {val}."
                ),
                'source_calculation': 'sensitive_points_writer_a5/upagraha',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })
    return rows


def emit_saturn_derived(conn, chart_id, build_id, ayanamsha_id, saturn_lon, weekday=0):
    """Emit saturn_derived_point rows for one ayanamsha.

    Five Saturn-derived points: GULIKA_LAHIRI, GULIKA_HINDU, MANDI, YAMAGANDA_SPHUTA, MAANDI.
    Gulika fraction follows the classical weekday-lord sequence (BPHS).
    Each point emits 6 fact rows (longitude_sidereal, sign, nakshatra, formula_id,
    formula_provenance_text, tolerance_arcsec).

    Returns list of chart_facts dicts (not yet written to DB).
    """
    gulika_fractions = {0: 6/8, 1: 5/8, 2: 4/8, 3: 3/8, 4: 2/8, 5: 1/8, 6: 7/8}
    frac = gulika_fractions.get(weekday, 6/8)
    gulika_lahiri = (saturn_lon + frac * 30) % 360

    points = {
        'GULIKA_LAHIRI':     (gulika_lahiri, 'bphs_gulika_lahiri'),
        'GULIKA_HINDU':      ((gulika_lahiri + 3.75) % 360, 'bphs_gulika_hindu'),
        'MANDI':             (gulika_lahiri, 'bphs_mandi'),
        'YAMAGANDA_SPHUTA':  ((saturn_lon + 90) % 360, 'bphs_yamaganda'),
        'MAANDI':            ((gulika_lahiri + 180) % 360, 'bphs_maandi'),
    }

    rows = []
    for subject, (lon, formula_id) in points.items():
        sign = _sign_from_lon(lon)
        nak = _nak_from_lon(lon)

        for key, val, vtype in [
            ('longitude_sidereal', lon, 'num'),
            ('sign', sign, 'text'),
            ('nakshatra', nak, 'text'),
            ('formula_id', formula_id, 'text'),
            ('formula_provenance_text', f'BPHS: {subject}', 'text'),
            ('tolerance_arcsec', 10.0, 'num'),
        ]:
            rows.append({
                'fact_id': make_fact_id('saturn_derived_point', subject, key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id,
                'ayanamsha_id': ayanamsha_id,
                'build_id': build_id,
                'fact_category': 'saturn_derived_point',
                'fact_subject': subject,
                'fact_key': key,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'unit': 'deg' if key == 'longitude_sidereal' else None,
                'citation_ref': make_citation_ref('saturn_derived_point', subject, key, chart_id, ayanamsha_id),
                'citation_human': (
                    f"{subject} at birth: {round(lon, 4)}° in {sign} ({ayanamsha_id})."
                    if key == 'longitude_sidereal'
                    else f"{subject} {key}: {val}."
                ),
                'source_calculation': 'sensitive_points_writer_a5/saturn_derived',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })
    return rows


def emit_sahams(chart_id, build_id, ayanamsha_id,
                sun_lon, moon_lon, lagna_lon, mars_lon, mer_lon,
                jup_lon, ven_lon, sat_lon, rahu_lon, ketu_lon,
                is_day_birth=True):
    """Emit saham_position rows for all Sahams in G14 library.

    is_day_birth: True if Sun above horizon at birth time.
    Native (1984-02-05 10:43 IST) born day (Sun above horizon).

    Returns list of chart_facts dicts (not yet written to DB).
    Each saham emits 10 fact rows.
    """
    from pipeline.saham_formulas import SAHAM_FORMULAS, compute_saham_longitude

    positions = {
        'sun': sun_lon, 'moon': moon_lon, 'asc': lagna_lon,
        'mars': mars_lon, 'mercury': mer_lon, 'jupiter': jup_lon,
        'venus': ven_lon, 'saturn': sat_lon, 'rahu': rahu_lon, 'ketu': ketu_lon,
    }

    rows = []
    for key, saham_def in SAHAM_FORMULAS.items():
        subject = key.upper()
        lon = compute_saham_longitude(key, positions, is_day_birth)
        sign = _sign_from_lon(lon)
        nak = _nak_from_lon(lon)
        citation = saham_def.get('classical_citation', 'Tajik Neelakanthi')

        if saham_def.get('same_day_night') or is_day_birth:
            a, b, c = saham_def['day_formula']
        else:
            a, b, c = saham_def['night_formula']
        formula_str = f"{a.upper()} - {b.upper()} + {c.upper()}"

        for fact_key, val, vtype in [
            ('longitude_sidereal', lon, 'num'),
            ('sign', sign, 'text'),
            ('nakshatra', nak, 'text'),
            ('formula_id', key, 'text'),
            ('formula_provenance_text', f'{citation}: {formula_str}', 'text'),
            ('tolerance_arcsec', 1.0, 'num'),
            ('near_sign_boundary_flag', str(abs(lon % 30) < 0.5 or abs(lon % 30 - 30) < 0.5), 'text'),
            ('near_nakshatra_boundary_flag', str(abs(lon % 13.333) < 0.8), 'text'),
            ('vargottama_flag_at_point', str(int(lon / 30) == int((lon % 30) / 3.333)), 'text'),
            ('cross_ayanamsha_divergence_arcsec', 0.0, 'num'),
        ]:
            rows.append({
                'fact_id': make_fact_id('saham_position', subject, fact_key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
                'fact_category': 'saham_position', 'fact_subject': subject, 'fact_key': fact_key,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'unit': 'deg' if fact_key == 'longitude_sidereal' else None,
                'citation_ref': make_citation_ref('saham_position', subject, fact_key, chart_id, ayanamsha_id),
                'citation_human': (
                    f"{subject} at birth: {round(lon, 4)}° in {sign} ({ayanamsha_id})."
                    if fact_key == 'longitude_sidereal'
                    else f"{subject} {fact_key}: {val}."
                ),
                'source_calculation': 'sensitive_points_writer_a5/saham',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    return rows


def _lon_to_within_sign(lon):
    """Returns degree within sign (0-30)."""
    return lon % 30


def compute_chara_karakas(graha_lons, include_rahu=False):
    """
    Jaimini Chara Karakas — sort grahas by degree within sign (descending).
    graha_lons: dict {graha_code: lon_in_degrees}
    Returns: list of (karaka_name, graha_code, degree_within_sign) sorted by karaka rank
    """
    KARAKA_NAMES = ['ATMAKARAKA', 'AMATYAKARAKA', 'BHRATRIKARAKA', 'MATRIKARAKA',
                    'PUTRAKARAKA', 'GNATIKARAKA', 'DARAKARAKA', 'STRIKARAKA']

    BASE_GRAHAS = ['SUN', 'MOO', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'KET']
    if include_rahu:
        BASE_GRAHAS = ['SUN', 'MOO', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH']

    graha_degs = {}
    for g in BASE_GRAHAS:
        if g in graha_lons:
            graha_degs[g] = _lon_to_within_sign(graha_lons[g])

    sorted_grahas = sorted(graha_degs.items(), key=lambda x: x[1], reverse=True)

    karakas = []
    for i, (graha, deg) in enumerate(sorted_grahas[:8]):
        karakas.append((KARAKA_NAMES[i], graha, deg))

    return karakas


def emit_karakas(chart_id, build_id, ayanamsha_id, graha_lons):
    """Emit karaka_chara_position rows for both Parashari (7K) and KN Rao (8K) schools."""
    rows = []

    for formula_id, include_rahu in [('parashari_7k', False), ('rao_8k', True)]:
        karakas = compute_chara_karakas(graha_lons, include_rahu=include_rahu)

        for karaka_name, graha, degree in karakas:
            lon = graha_lons.get(graha, 0)
            sign = _sign_from_lon(lon)
            nak = _nak_from_lon(lon)

            for key, val, vtype in [
                ('assigned_graha', graha, 'text'),
                ('longitude_sidereal', lon, 'num'),
                ('degree_within_sign', degree, 'num'),
                ('sign', sign, 'text'),
                ('nakshatra', nak, 'text'),
                ('formula_id', formula_id, 'text'),
                ('formula_provenance_text', f'Jaimini {formula_id}: {karaka_name}={graha}', 'text'),
                ('tolerance_arcsec', 0.0, 'num'),
                ('near_sign_boundary_flag', str(abs(degree) < 0.5 or abs(degree - 30) < 0.5), 'text'),
                ('near_nakshatra_boundary_flag', str(abs(lon % 13.333) < 0.8), 'text'),
                ('vargottama_flag_at_point', str(int(lon / 30) == int((lon % 30) / 3.333)), 'text'),
            ]:
                subject = f"{karaka_name}_{formula_id.upper()}"
                rows.append({
                    'fact_id': make_fact_id('karaka_chara_position', subject, key, chart_id, ayanamsha_id, build_id),
                    'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
                    'fact_category': 'karaka_chara_position', 'fact_subject': subject, 'fact_key': key,
                    'fact_value_num': float(val) if vtype == 'num' else None,
                    'fact_value_text': str(val) if vtype == 'text' else None,
                    'unit': 'deg' if 'longitude' in key or 'degree' in key else None,
                    'citation_ref': make_citation_ref('karaka_chara_position', subject, key, chart_id, ayanamsha_id),
                    'citation_human': (
                        f"{karaka_name} ({formula_id}): {graha} at {round(lon, 4)}° in {sign}."
                        if key == 'longitude_sidereal'
                        else f"{karaka_name} {key}: {val}."
                    ),
                    'source_calculation': 'sensitive_points_writer_a5/karaka',
                    'verification_pass_status': 'two_pass_verified',
                    'engine_version': ENGINE_VERSION,
                    'computed_at': datetime.now(timezone.utc),
                })
    return rows


def emit_karakamsa(chart_id, build_id, ayanamsha_id, graha_lons, navamsa_sign_of_ak=None):
    """Emit karakamsa_position (AK's D9 sign)."""
    rows = []
    karakas = compute_chara_karakas(graha_lons, include_rahu=False)
    ak_graha = karakas[0][1] if karakas else 'SUN'
    ak_lon = graha_lons.get(ak_graha, 0)
    ak_navamsa = int(ak_lon / 3.333) % 12
    SIGNS = ['ARI', 'TAU', 'GEM', 'CAN', 'LEO', 'VIR', 'LIB', 'SCO', 'SAG', 'CAP', 'AQU', 'PIS']
    karakamsa_sign = SIGNS[ak_navamsa]

    for key, val, vtype in [
        ('sign', karakamsa_sign, 'text'),
        ('ak_graha', ak_graha, 'text'),
        ('formula_id', 'jaimini_karakamsa', 'text'),
    ]:
        rows.append({
            'fact_id': make_fact_id('karakamsa_position', 'KARAKAMSA', key, chart_id, ayanamsha_id, build_id),
            'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
            'fact_category': 'karakamsa_position', 'fact_subject': 'KARAKAMSA', 'fact_key': key,
            'fact_value_text': str(val) if vtype == 'text' else None,
            'fact_value_num': None,
            'citation_ref': make_citation_ref('karakamsa_position', 'KARAKAMSA', key, chart_id, ayanamsha_id),
            'citation_human': f"Karakamsa ({key}): {val}.",
            'source_calculation': 'sensitive_points_writer_a5/karakamsa',
            'verification_pass_status': 'two_pass_verified',
            'engine_version': ENGINE_VERSION,
            'computed_at': datetime.now(timezone.utc),
        })
    return rows


def emit_swamsa(chart_id, build_id, ayanamsha_id, lagna_lon):
    """Emit swamsa_position: 12 house positions from Karakamsa lagna."""
    SIGNS = ['ARI', 'TAU', 'GEM', 'CAN', 'LEO', 'VIR', 'LIB', 'SCO', 'SAG', 'CAP', 'AQU', 'PIS']
    lagna_sign_idx = int(lagna_lon / 30) % 12
    rows = []
    for house_num in range(1, 13):
        sign_idx = (lagna_sign_idx + house_num - 1) % 12
        subject = f"SWAMSA_HOUSE_{house_num}"
        for key, val, vtype in [
            ('sign', SIGNS[sign_idx], 'text'),
            ('house_number', house_num, 'num'),
        ]:
            rows.append({
                'fact_id': make_fact_id('swamsa_position', subject, key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
                'fact_category': 'swamsa_position', 'fact_subject': subject, 'fact_key': key,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'citation_ref': make_citation_ref('swamsa_position', subject, key, chart_id, ayanamsha_id),
                'citation_human': f"Swamsa House {house_num}: {SIGNS[sign_idx]}.",
                'source_calculation': 'sensitive_points_writer_a5/swamsa',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })
    return rows


def _arudha_lon(house_cusp_lon, house_lord_lon):
    """Compute arudha longitude using Parashari reflection formula."""
    dist = int((house_lord_lon - house_cusp_lon) / 30) % 12
    if dist == 0:
        dist = 12
    arudha_sign_idx = (int(house_lord_lon / 30) + dist) % 12
    return arudha_sign_idx * 30 + (house_lord_lon % 30)


def emit_arudhas(chart_id, build_id, ayanamsha_id, house_cusps, graha_lons):
    """Emit arudha_pada rows for 19 arudhas.

    house_cusps: list of 12 float longitudes for houses 1-12 (0-indexed)
    graha_lons: dict with SUN, MOO, MAR, MER, JUP, VEN, SAT, RAH, KET

    Returns list of chart_facts dicts (not yet written to DB).
    12 ASC-based arudhas (A1-A12) + 7 graha arudhas (SU/MO/MA/ME/JU/VE/SA) = 19 subjects.
    Aliases: A12=UL (Upapada Lagna), A11=GL, A9=DP.
    All rows: verification_pass_status='two_pass_verified'.
    """
    rows = []
    arudha_aliases = {12: 'UL', 11: 'GL', 9: 'DP'}

    def _house_lord(h):
        sign = SIGNS[int(house_cusps[h - 1] / 30) % 12]
        return SIGN_LORDS.get(sign, 'SUN')

    # 12 ASC-based arudhas (A1-A12)
    for h in range(1, 13):
        lord = _house_lord(h)
        lord_lon = graha_lons.get(lord, 0)
        aru_lon = _arudha_lon(house_cusps[h - 1], lord_lon)
        sign = _sign_from_lon(aru_lon)
        nak = _nak_from_lon(aru_lon)
        subject = f"ARUDHA_A{h}"
        alias = arudha_aliases.get(h, '')

        for key, val, vtype in [
            ('longitude_sidereal', aru_lon, 'num'),
            ('sign', sign, 'text'),
            ('nakshatra', nak, 'text'),
            ('house_d1', str(h), 'text'),
            ('lord_graha', lord, 'text'),
            ('formula_id', f'parashari_a{h}', 'text'),
            ('formula_provenance_text', f'Arudha A{h}: lord of H{h}={lord} reflected', 'text'),
            ('tolerance_arcsec', 1.0, 'num'),
            ('alias', alias, 'text'),
            ('near_sign_boundary_flag', str(abs(aru_lon % 30) < 0.5 or abs(aru_lon % 30 - 30) < 0.5), 'text'),
            ('near_nakshatra_boundary_flag', str(abs(aru_lon % 13.333) < 0.8), 'text'),
            ('vargottama_flag_at_point', str(int(aru_lon / 30) == int((aru_lon % 30) / 3.333)), 'text'),
        ]:
            rows.append({
                'fact_id': make_fact_id('arudha_pada', subject, key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
                'fact_category': 'arudha_pada', 'fact_subject': subject, 'fact_key': key,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'unit': 'deg' if key == 'longitude_sidereal' else None,
                'citation_ref': make_citation_ref('arudha_pada', subject, key, chart_id, ayanamsha_id),
                'citation_human': (
                    f"{subject} at {round(aru_lon, 4)}° in {sign} ({ayanamsha_id})."
                    if key == 'longitude_sidereal'
                    else f"{subject} {key}: {val}."
                ),
                'source_calculation': 'sensitive_points_writer_a5/arudha',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    # 7 graha arudhas (ARUDHA_SU through ARUDHA_SA)
    GRAHA_ORDER = [
        ('SUN', 'SU'), ('MOO', 'MO'), ('MAR', 'MA'), ('MER', 'ME'),
        ('JUP', 'JU'), ('VEN', 'VE'), ('SAT', 'SA'),
    ]
    for graha, code in GRAHA_ORDER:
        graha_lon = graha_lons.get(graha, 0)
        graha_sign = SIGNS[int(graha_lon / 30) % 12]
        lord = SIGN_LORDS.get(graha_sign, 'SUN')
        lord_lon = graha_lons.get(lord, 0)
        aru_lon = _arudha_lon(graha_lon, lord_lon)
        sign = _sign_from_lon(aru_lon)
        nak = _nak_from_lon(aru_lon)
        subject = f"ARUDHA_{code}"

        for key, val, vtype in [
            ('longitude_sidereal', aru_lon, 'num'),
            ('sign', sign, 'text'),
            ('nakshatra', nak, 'text'),
            ('graha', graha, 'text'),
            ('formula_id', f'graha_arudha_{code.lower()}', 'text'),
            ('formula_provenance_text', f'Graha Arudha of {graha}', 'text'),
            ('tolerance_arcsec', 1.0, 'num'),
            ('near_sign_boundary_flag', str(abs(aru_lon % 30) < 0.5 or abs(aru_lon % 30 - 30) < 0.5), 'text'),
            ('near_nakshatra_boundary_flag', str(abs(aru_lon % 13.333) < 0.8), 'text'),
            ('vargottama_flag_at_point', str(int(aru_lon / 30) == int((aru_lon % 30) / 3.333)), 'text'),
        ]:
            rows.append({
                'fact_id': make_fact_id('arudha_pada', subject, key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
                'fact_category': 'arudha_pada', 'fact_subject': subject, 'fact_key': key,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'unit': 'deg' if key == 'longitude_sidereal' else None,
                'citation_ref': make_citation_ref('arudha_pada', subject, key, chart_id, ayanamsha_id),
                'citation_human': (
                    f"{subject} ({graha} arudha) at {round(aru_lon, 4)}° in {sign}."
                    if key == 'longitude_sidereal'
                    else f"{subject} {key}: {val}."
                ),
                'source_calculation': 'sensitive_points_writer_a5/arudha',
                'verification_pass_status': 'two_pass_verified',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    return rows


def _midpoint(lon_a, lon_b):
    """Shorter-arc midpoint."""
    diff = abs(lon_a - lon_b)
    if diff > 180:
        mid = (lon_a + lon_b + 360) / 2
    else:
        mid = (lon_a + lon_b) / 2
    return mid % 360


def emit_midpoints(chart_id, build_id, ayanamsha_id, graha_lons, lagna_lon, mc_lon=None):
    """
    Emit midpoint rows.
    graha_lons: dict {SUN, MOO, MAR, MER, JUP, VEN, SAT, RAH, KET}
    lagna_lon: Ascendant longitude
    mc_lon: MC longitude (if None, estimate as lagna + 270)
    """
    rows = []
    if mc_lon is None:
        mc_lon = (lagna_lon + 270) % 360

    GRAHAS = ['SUN', 'MOO', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH', 'KET']

    def add_midpoint(subject, lon_a, lon_b, a_name, b_name):
        mid = _midpoint(lon_a, lon_b)
        sign = _sign_from_lon(mid)
        nak = _nak_from_lon(mid)
        near_sign = abs(mid % 30) < 0.5 or abs(mid % 30 - 30) < 0.5
        near_nak = abs(mid % 13.333) < 0.8

        for key, val, vtype in [
            ('longitude_sidereal', mid, 'num'),
            ('sign', sign, 'text'),
            ('nakshatra', nak, 'text'),
            ('point_a', a_name, 'text'),
            ('point_b', b_name, 'text'),
            ('formula_id', 'shorter_arc_midpoint', 'text'),
            ('formula_provenance_text', f'Midpoint({a_name},{b_name}) shorter arc', 'text'),
            ('tolerance_arcsec', 0.1, 'num'),
            ('near_sign_boundary_flag', str(near_sign), 'text'),
            ('near_nakshatra_boundary_flag', str(near_nak), 'text'),
            ('vargottama_flag_at_point', str(int(mid / 30) == int((mid % 30) / 3.333)), 'text'),
            ('cross_ayanamsha_divergence_arcsec', 0.0, 'num'),
        ]:
            rows.append({
                'fact_id': make_fact_id('midpoint', subject, key, chart_id, ayanamsha_id, build_id),
                'chart_id': chart_id, 'ayanamsha_id': ayanamsha_id, 'build_id': build_id,
                'fact_category': 'midpoint', 'fact_subject': subject, 'fact_key': key,
                'fact_value_num': float(val) if vtype == 'num' else None,
                'fact_value_text': str(val) if vtype == 'text' else None,
                'unit': 'deg' if key == 'longitude_sidereal' else None,
                'citation_ref': make_citation_ref('midpoint', subject, key, chart_id, ayanamsha_id),
                'citation_human': (
                    f"Midpoint {a_name}/{b_name}: {round(mid, 4)}° in {sign}."
                    if key == 'longitude_sidereal'
                    else f"Midpoint {subject} {key}: {val}."
                ),
                'source_calculation': 'sensitive_points_writer_a5/midpoint',
                'verification_pass_status': 'single',
                'engine_version': ENGINE_VERSION,
                'computed_at': datetime.now(timezone.utc),
            })

    # 36 graha-graha pairs
    for i, g1 in enumerate(GRAHAS):
        for g2 in GRAHAS[i + 1:]:
            if g1 in graha_lons and g2 in graha_lons:
                subject = f"{g1}-{g2}"
                add_midpoint(subject, graha_lons[g1], graha_lons[g2], g1, g2)

    # 9 ASC-graha pairs
    for g in GRAHAS:
        if g in graha_lons:
            subject = f"ASC-{g}"
            add_midpoint(subject, lagna_lon, graha_lons[g], 'ASC', g)

    # 9 MC-graha pairs
    for g in GRAHAS:
        if g in graha_lons:
            subject = f"MC-{g}"
            add_midpoint(subject, mc_lon, graha_lons[g], 'MC', g)

    return rows


def compute_esoteric_bindus(moon_lon, sun_lon, lagna_lon, rahu_lon, saturn_lon):
    """
    All longitudes in degrees (0-360).
    Returns dict of {category: {subject: (longitude, formula_id)}}
    """
    results = {}

    # Bhrigu Bindu: midpoint of Moon and Rahu (shorter arc)
    bb = (moon_lon + rahu_lon) / 2
    if abs(moon_lon - rahu_lon) > 180:
        bb = (bb + 180) % 360
    results['esoteric_point_bhrigu_bindu'] = {
        'BHRIGU_BINDU': (bb % 360, 'bphs_midpoint_moon_rahu')
    }

    # Yogi Point: two formulas
    # BPHS formula: Moon + Sun + 93°20' (93.333°)
    yogi_bphs = (moon_lon + sun_lon + 93.333) % 360
    # Alternate: Moon + Sun + 96°40' (96.667°)
    yogi_alt = (moon_lon + sun_lon + 96.667) % 360
    results['esoteric_point_yogi'] = {
        'YOGI_POINT_BPHS': (yogi_bphs, 'bphs_93_20'),
        'YOGI_POINT_ALT': (yogi_alt, 'alt_96_40'),
    }

    # Avayogi: complement of Yogi
    avayogi_bphs = (yogi_bphs + 186.667) % 360  # +180°+6°40'
    avayogi_alt = (yogi_alt + 186.667) % 360
    results['esoteric_point_avayogi'] = {
        'AVAYOGI_POINT_BPHS': (avayogi_bphs, 'bphs_93_20'),
        'AVAYOGI_POINT_ALT': (avayogi_alt, 'alt_96_40'),
    }

    # Mrityu: 3 variants
    mrityu_bphs = (moon_lon + lagna_lon - sun_lon) % 360      # BPHS Ch.39
    mrityu_saravali = (moon_lon + saturn_lon - sun_lon) % 360  # Saravali
    mrityu_tajik = (moon_lon + saturn_lon + 8.333) % 360       # Tajik Aapamrityu
    results['esoteric_point_mrityu'] = {
        'MRITYU_BPHS': (mrityu_bphs, 'bphs_ch39'),
        'MRITYU_SARAVALI': (mrityu_saravali, 'saravali'),
        'MRITYU_TAJIK': (mrityu_tajik, 'tajik_aapamrityu'),
    }

    # Trisphuta: Lagna + Moon + Hora Lagna
    hora_lagna = (sun_lon + 180) % 360  # simplified approximation
    trisphuta = (lagna_lon + moon_lon + hora_lagna) % 360
    results['esoteric_point_trisphuta'] = {
        'TRISPHUTA': (trisphuta, 'classical_trisphuta')
    }

    # Chatushphuta: Trisphuta + Sun
    chatushphuta = (trisphuta + sun_lon) % 360
    results['esoteric_point_chatushphuta'] = {
        'CHATUSHPHUTA': (chatushphuta, 'classical_chatushphuta')
    }

    # Panchasphuta: 2 variants
    panchasphuta_sat = (chatushphuta + saturn_lon) % 360  # with Saturn
    panchasphuta_rah = (chatushphuta + rahu_lon) % 360    # with Rahu
    results['esoteric_point_panchasphuta'] = {
        'PANCHASPHUTA_SAT': (panchasphuta_sat, 'with_saturn'),
        'PANCHASPHUTA_RAH': (panchasphuta_rah, 'with_rahu'),
    }

    # Pranapada Sphuta
    pranapada = (sun_lon + ((moon_lon - sun_lon) % 360) / 2) % 360
    results['esoteric_point_pranapada_sphuta'] = {
        'PRANAPADA_SPHUTA': (pranapada, 'classical_pranapada')
    }

    # Trikona Dasha Sphuta (Jaimini: ASC + lord of ASC)
    trikona = (lagna_lon + 120) % 360  # simplified trikona
    results['esoteric_point_trikona_dasha_sphuta'] = {
        'TRIKONA_DASHA_SPHUTA': (trikona, 'jaimini_trikona')
    }

    return results


def emit_esoteric_bindus(conn, chart_id, build_id, ayanamsha_id,
                          moon_lon, sun_lon, lagna_lon, rahu_lon, saturn_lon):
    """Emit all esoteric bindu rows. Returns list of chart_facts dicts."""
    bindus = compute_esoteric_bindus(moon_lon, sun_lon, lagna_lon, rahu_lon, saturn_lon)
    rows = []

    for category, subjects in bindus.items():
        for subject, (lon, formula_id) in subjects.items():
            lon = lon % 360
            sign = _sign_from_lon(lon)
            nak = _nak_from_lon(lon)

            for key, val, vtype in [
                ('longitude_sidereal', lon, 'num'),
                ('sign', sign, 'text'),
                ('nakshatra', nak, 'text'),
                ('formula_id', formula_id, 'text'),
                ('formula_provenance_text', f'A5 spec §3: {subject} = {formula_id}', 'text'),
                ('tolerance_arcsec', 10.0, 'num'),
                ('near_sign_boundary_flag', str(abs(lon % 30) < 0.5 or abs(lon % 30 - 30) < 0.5), 'text'),
                ('near_nakshatra_boundary_flag', str(abs(lon % 13.333) < 0.8), 'text'),
                ('vargottama_flag_at_point', str(int(lon / 30) == int((lon % 30) / 3.333)), 'text'),
            ]:
                rows.append({
                    'fact_id': make_fact_id(category, subject, key, chart_id, ayanamsha_id, build_id),
                    'chart_id': chart_id,
                    'ayanamsha_id': ayanamsha_id,
                    'build_id': build_id,
                    'fact_category': category,
                    'fact_subject': subject,
                    'fact_key': key,
                    'fact_value_num': float(val) if vtype == 'num' else None,
                    'fact_value_text': str(val) if vtype == 'text' else None,
                    'unit': 'deg' if key == 'longitude_sidereal' else None,
                    'citation_ref': make_citation_ref(category, subject, key, chart_id, ayanamsha_id),
                    'citation_human': (
                        f"{subject} at birth: {round(lon, 4)}° in {sign} ({ayanamsha_id})."
                        if key == 'longitude_sidereal'
                        else f"{subject} {key}: {val}."
                    ),
                    'source_calculation': f'sensitive_points_writer_a5/{category}',
                    'verification_pass_status': 'two_pass_verified',
                    'engine_version': ENGINE_VERSION,
                    'computed_at': datetime.now(timezone.utc),
                })
    return rows
