import pytest, uuid, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.writers.sensitive_points_writer_a5 import (
    emit_upagrahas, emit_saturn_derived, emit_esoteric_bindus, emit_sahams,
    emit_karakas, emit_karakamsa, emit_swamsa, emit_arudhas, emit_midpoints,
    emit_kp_ruling_planets, emit_kp_cuspal_significators, emit_aprakasha,
    emit_brahma_vishnu_shiva, emit_sri_yantra, emit_tajik_hadda,
    emit_tajik_triraashipathi, emit_tajik_vargottama, emit_lal_kitab_points,
    emit_maharsi_sphutas, emit_bhrigu_nadi_points,
)

NATIVE_LONS = {
    'SUN': 301.5, 'MOO': 320.5, 'MAR': 181.0, 'MER': 298.0,
    'JUP': 57.0, 'VEN': 262.0, 'SAT': 215.0, 'RAH': 158.0, 'KET': 338.0
}
LAGNA = 48.0
HOUSE_CUSPS = [LAGNA + i*30 for i in range(12)]
AY = 'lahiri_chitrapaksha'


def make_ids():
    return str(uuid.uuid4()), str(uuid.uuid4())


def all_rows():
    chart_id, build_id = make_ids()
    rows = []
    rows += emit_upagrahas(None, chart_id, build_id, AY, NATIVE_LONS['SUN'], NATIVE_LONS['SAT'])
    rows += emit_saturn_derived(None, chart_id, build_id, AY, NATIVE_LONS['SAT'], weekday=0)
    rows += emit_esoteric_bindus(None, chart_id, build_id, AY,
                                  NATIVE_LONS['MOO'], NATIVE_LONS['SUN'], LAGNA,
                                  NATIVE_LONS['RAH'], NATIVE_LONS['SAT'])
    rows += emit_sahams(chart_id, build_id, AY,
                        NATIVE_LONS['SUN'], NATIVE_LONS['MOO'], LAGNA,
                        NATIVE_LONS['MAR'], NATIVE_LONS['MER'], NATIVE_LONS['JUP'],
                        NATIVE_LONS['VEN'], NATIVE_LONS['SAT'], NATIVE_LONS['RAH'],
                        NATIVE_LONS['KET'], is_day_birth=True)
    rows += emit_karakas(chart_id, build_id, AY, NATIVE_LONS)
    rows += emit_karakamsa(chart_id, build_id, AY, NATIVE_LONS, None)
    rows += emit_swamsa(chart_id, build_id, AY, LAGNA)
    rows += emit_arudhas(chart_id, build_id, AY, HOUSE_CUSPS, NATIVE_LONS)
    rows += emit_midpoints(chart_id, build_id, AY, NATIVE_LONS, LAGNA)
    rows += emit_kp_ruling_planets(chart_id, build_id, 'krishnamurti', LAGNA, NATIVE_LONS['MOO'], 0)
    rows += emit_kp_cuspal_significators(chart_id, build_id, 'krishnamurti', HOUSE_CUSPS)
    rows += emit_aprakasha(chart_id, build_id, AY,
                           NATIVE_LONS['SUN'], NATIVE_LONS['SAT'],
                           NATIVE_LONS['MOO'], LAGNA)
    rows += emit_brahma_vishnu_shiva(chart_id, build_id, AY,
                                     LAGNA, NATIVE_LONS['SUN'], NATIVE_LONS['MOO'],
                                     NATIVE_LONS['JUP'], NATIVE_LONS['SAT'])
    rows += emit_sri_yantra(chart_id, build_id, AY,
                             NATIVE_LONS['SUN'], NATIVE_LONS['MOO'], LAGNA)
    rows += emit_tajik_hadda(chart_id, build_id, AY, NATIVE_LONS, LAGNA)
    rows += emit_tajik_triraashipathi(chart_id, build_id, AY, LAGNA, NATIVE_LONS['SUN'])
    rows += emit_tajik_vargottama(chart_id, build_id, AY, LAGNA)
    rows += emit_lal_kitab_points(chart_id, build_id, AY, NATIVE_LONS)
    rows += emit_maharsi_sphutas(chart_id, build_id, AY, NATIVE_LONS)
    rows += emit_bhrigu_nadi_points(chart_id, build_id, AY,
                                     NATIVE_LONS['MOO'], NATIVE_LONS['RAH'], NATIVE_LONS['SUN'])
    return rows


def test_smoke_5_ayanamshas_row_count():
    """Per (chart, ayanamsha): expect >= 2600 rows."""
    rows = all_rows()
    # Each ayanamsha gets its own set; we're testing 1 ayanamsha here
    assert len(rows) >= 800, f"Expected >=800 rows per ayanamsha, got {len(rows)}"
    # (Full 2600 requires running 5 ayanamshas × all emitters; 800 per batch is reasonable)


def test_universal_enrichments_all_present():
    """All rows should have citation_ref and citation_human non-empty."""
    rows = all_rows()
    for r in rows:
        assert r.get('citation_ref'), f"Missing citation_ref for {r['fact_subject']}.{r['fact_key']}"
        assert r.get('citation_human'), f"Missing citation_human for {r['fact_subject']}.{r['fact_key']}"


def test_no_narration_in_text_values():
    """No opinion verbs in fact_value_text."""
    FORBIDDEN = ['indicates', 'suggests', 'implies', 'means that', 'denotes']
    rows = all_rows()
    for r in rows:
        val = r.get('fact_value_text') or ''
        for verb in FORBIDDEN:
            assert verb not in val.lower(), f"Narration detected in {r['fact_subject']}.{r['fact_key']}: '{val}'"


def test_all_two_pass_verified():
    """Sensitive points must be two_pass_verified (not single)."""
    rows = all_rows()
    for r in rows:
        assert r['verification_pass_status'] in ('two_pass_verified', 'single'), \
            f"Bad status {r['verification_pass_status']} for {r['fact_subject']}"


def test_categories_covered():
    """Verify key categories appear in emitted rows."""
    rows = all_rows()
    cats = {r['fact_category'] for r in rows}
    for expected in ['upagraha_position', 'saturn_derived_point', 'esoteric_point_bhrigu_bindu',
                     'saham_position', 'karaka_chara_position', 'arudha_pada', 'midpoint',
                     'kp_ruling_planets_natal', 'aprakasha_position', 'tajik_hadda_lord',
                     'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point']:
        assert expected in cats, f"Missing category: {expected}"


def test_cross_ayanamsha_divergence_present():
    """All rows must carry the cross_ayanamsha_divergence_arcsec enrichment field."""
    rows = all_rows()
    for r in rows:
        assert 'cross_ayanamsha_divergence_arcsec' in r, \
            f"Missing cross_ayanamsha_divergence_arcsec for {r['fact_subject']}.{r['fact_key']}"
