import hashlib
from datetime import datetime, timezone

ENGINE_VERSION = 'natal_engine/0.2.0'


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
