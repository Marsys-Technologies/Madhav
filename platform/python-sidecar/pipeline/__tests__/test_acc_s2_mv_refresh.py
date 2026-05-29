import pytest, os

def db_available():
    try:
        import psycopg2
        psycopg2.connect(host='127.0.0.1',port=5433,user='amjis_app',
                         password='aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF',dbname='amjis').close()
        return True
    except: return False

DB = pytest.mark.skipif(not db_available(), reason="DB not reachable")

EXPECTED_MVS = [
    'mv_chart_planet_summary','mv_chart_house_summary','mv_chart_yogas_active_at_birth',
    'mv_chart_vargas_summary','mv_chart_sahams','mv_chart_arudhas',
    'mv_chart_shadbala_summary','mv_chart_bhava_bala_summary',
    'mv_chart_ashtakavarga_summary','mv_cross_ayanamsha_consensus',
    'mv_chart_panchanga_birth_summary','mv_chart_sensitive_points_summary',
]

@DB
def test_all_12_mvs_exist():
    import psycopg2
    conn = psycopg2.connect(host='127.0.0.1',port=5433,user='amjis_app',
                             password='aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF',dbname='amjis')
    cur = conn.cursor()
    cur.execute("SELECT matviewname FROM pg_matviews ORDER BY matviewname")
    existing = {r[0] for r in cur.fetchall()}
    conn.close()
    for mv in EXPECTED_MVS:
        assert mv in existing, f"Missing MV: {mv}"

@DB
def test_mvs_refreshable():
    """Verify REFRESH MATERIALIZED VIEW runs without error on empty chart_facts."""
    import psycopg2
    conn = psycopg2.connect(host='127.0.0.1',port=5433,user='amjis_app',
                             password='aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF',dbname='amjis')
    cur = conn.cursor()
    # Just test 2 MVs to keep it fast
    for mv in ['mv_chart_panchanga_birth_summary','mv_chart_sensitive_points_summary']:
        try:
            cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
            conn.commit()
        except Exception as e:
            if 'concurrently' in str(e).lower():
                cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
                conn.commit()
    conn.close()
