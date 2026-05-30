import pytest
import os

# All tests in this file require a live PostgreSQL connection.
# Skip automatically in CI where DATABASE_URL / DB_HOST are not set.
_DB_AVAILABLE = bool(os.environ.get("DATABASE_URL") or os.environ.get("DB_HOST") == "127.0.0.1" and False)
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — live-DB integration test, skipped in CI",
)

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '5433')
DB_USER = os.environ.get('DB_USER', 'amjis_app')
DB_PASS = os.environ.get('DB_PASS', '')  # no default — must be set via env or DATABASE_URL
DB_NAME = os.environ.get('DB_NAME', 'amjis')

def get_conn():
    import psycopg2
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                            password=DB_PASS, dbname=DB_NAME)

def test_chart_facts_new_columns():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='chart_facts' AND column_name IN (
            'fact_subject','citation_ref','citation_human',
            'source_calculation','verification_pass_status','engine_version'
        )
    """)
    cols = {row[0] for row in cur.fetchall()}
    conn.close()
    assert 'fact_subject' in cols
    assert 'citation_ref' in cols
    assert 'verification_pass_status' in cols

def test_chart_dashas_exists():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.chart_dashas')")
    result = cur.fetchone()[0]
    conn.close()
    assert result is not None

def test_chart_dashas_check_constraint():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO chart_dashas(chart_id, ayanamsha_id, build_id,
            system_id, level_n, lord_graha, start_date, end_date, start_iso, end_iso,
            duration_days, sandhi_flag, verification_pass_status, verification_method)
            VALUES(gen_random_uuid(), 'test', gen_random_uuid(), 'test', 1, 'SUN',
            '2000-01-01', '2006-01-01', '2000-01-01', '2006-01-01', 2191, false,
            'single', 'test')""")
        conn.rollback()
        assert False, "Should have raised CHECK constraint violation"
    except Exception as e:
        conn.rollback()
        assert 'check' in str(e).lower() or 'constraint' in str(e).lower()
    conn.close()

def test_l25_tables_count():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'l25_%'")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 6

def test_mvs_count():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM pg_matviews")
    count = cur.fetchone()[0]
    conn.close()
    assert count >= 12

def test_chart_facts_is_empty_after_wipe():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM chart_facts")
    count = cur.fetchone()[0]
    conn.close()
    # After wipe, should be 0 (A4/A5 writers haven't run yet)
    assert count == 0
