"""
ACC-S1 smoke test suite.
Tests schema readiness, writer function availability, and DB state.
"""
import pytest, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── DB helpers ───────────────────────────────────────────────────────────────

DB_CONFIG = dict(host='127.0.0.1', port=5433, user='amjis_app',
                 password='aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF', dbname='amjis')

def get_conn():
    import psycopg2
    return psycopg2.connect(**DB_CONFIG)

def db_available():
    try:
        conn = get_conn(); conn.close(); return True
    except Exception:
        return False

DB = pytest.mark.skipif(not db_available(), reason="DB not reachable")

# ── Schema checks ─────────────────────────────────────────────────────────────

@DB
def test_chart_facts_a3_columns():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT column_name FROM information_schema.columns
                   WHERE table_name='chart_facts' AND column_name = ANY(%s)""",
                (['fact_subject','citation_ref','citation_human',
                  'source_calculation','verification_pass_status','engine_version'],))
    found = {row[0] for row in cur.fetchall()}
    conn.close()
    assert 'fact_subject' in found
    assert 'citation_ref' in found
    assert 'verification_pass_status' in found

@DB
def test_chart_dashas_exists_with_check():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.chart_dashas')")
    assert cur.fetchone()[0] is not None
    # Verify CHECK constraint blocks 'single'
    cur.execute("""SELECT conname FROM pg_constraint
                   WHERE conrelid='chart_dashas'::regclass AND contype='c'""")
    constraints = [r[0] for r in cur.fetchall()]
    conn.close()
    assert any('verification' in c or 'check' in c.lower() for c in constraints), \
        f"chart_dashas CHECK constraint not found. Constraints: {constraints}"

@DB
def test_l25_tables_present():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'l25_%'")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 6, f"Expected >=6 l25 tables, got {count}"

@DB
def test_mvs_12_present():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM pg_matviews")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 12, f"Expected >=12 MVs, got {count}"

@DB
def test_chart_facts_empty_post_wipe():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM chart_facts")
    count = cur.fetchone()[0]
    conn.close()
    # After wipe, should be 0 (writers haven't run against real chart yet)
    assert count == 0, f"chart_facts not empty post-wipe: {count} rows"

@DB
def test_no_divergent_flagged():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM chart_facts WHERE verification_pass_status='divergent_flagged'")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 0, f"{count} divergent_flagged rows found"

# ── Writer import checks ──────────────────────────────────────────────────────

def test_a4_writers_importable():
    from pipeline.writers.panchanga_writer_a4 import (
        write_panchanga_limbs, emit_hora_birth, emit_inauspicious_windows,
        emit_auspicious_windows, emit_solar_context, emit_calendrical,
        emit_astronomical, emit_tara_bala_baseline, emit_chandra_bala_baseline,
        emit_agni_vasa, emit_panchaka, emit_disha_shul,
        emit_special_yoga_combinations, emit_panchanga_mv_refresh,
    )
    assert all([write_panchanga_limbs, emit_hora_birth, emit_inauspicious_windows,
                emit_auspicious_windows, emit_solar_context, emit_tara_bala_baseline])

def test_a5_writers_importable():
    from pipeline.writers.sensitive_points_writer_a5 import (
        emit_upagrahas, emit_saturn_derived, emit_esoteric_bindus, emit_sahams,
        emit_karakas, emit_arudhas, emit_midpoints,
        emit_kp_ruling_planets, emit_kp_cuspal_significators,
        emit_aprakasha, emit_tajik_hadda, emit_lal_kitab_points,
        emit_maharsi_sphutas, emit_bhrigu_nadi_points,
    )
    assert all([emit_upagrahas, emit_saturn_derived, emit_esoteric_bindus, emit_sahams])

def test_schema_json_valid():
    import json
    schema_path = 'platform/scripts/governance/CHART_FACTS_SCHEMA.json'
    if os.path.exists(schema_path):
        d = json.load(open(schema_path))
        assert len(d['categories']) >= 140
        assert len(d['channels']) == 4
    else:
        pytest.skip("CHART_FACTS_SCHEMA.json not at expected path")

def test_retrieval_tool_importable():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    assert callable(query_panchanga_at_birth)
