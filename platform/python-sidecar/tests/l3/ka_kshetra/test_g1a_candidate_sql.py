"""Candidate boundary tests exercise executable SQL, not source-text claims."""
import pytest


def test_candidate_sql_scopes_reads_writes_conflicts_and_quoted_values():
    from services.ka_kshetra.candidate import candidate_sql
    read=candidate_sql('SELECT * FROM kala_field WHERE chart_id=%s ORDER BY t_start','g1')
    assert 'kala_field_candidate' in read and "generation = 'g1'" in read
    insert=candidate_sql('INSERT INTO kala_field (chart_id, segment_index) VALUES (%s,%s) '
                         'ON CONFLICT (chart_id, segment_index) DO NOTHING', 'g1')
    assert '(generation, chart_id, segment_index)' in insert
    assert "VALUES ('g1', %s,%s)" in insert
    assert 'ON CONFLICT (generation, chart_id, segment_index)' in insert
    delete=candidate_sql('DELETE FROM kala_insights WHERE chart_id=%s AND lel_derived=FALSE','g2')
    assert "WHERE generation = 'g2' AND" in delete
    assert candidate_sql("SELECT 'kala_field' AS source_table FROM chart_facts",'g1') == "SELECT 'kala_field' AS source_table FROM chart_facts"
    with pytest.raises(ValueError): candidate_sql('UPDATE kala_field SET alpha=2','g1')
    with pytest.raises(ValueError): candidate_sql('TRUNCATE kala_field','g1')
    with pytest.raises(ValueError): candidate_sql('SELECT * FROM kala_field',"g';DROP TABLE x;--")


def test_moorti_reader_validates_shared_testimony_envelope():
    import json
    from services.kala_core.overlays.contested import AdapterContext,envelope
    from services.kala_core.overlays.contested_reader import load_candidate_payload
    from services.kala_core.sky import SkyConvention,coverage_of
    convention=SkyConvention()
    ctx=AdapterContext('chart','candidate:1','natal',convention,
        ({'fact_id':'moon','fact_subject':'MOON','fact_key':'longitude_sidereal','fact_value_num':300.},))
    payload=envelope('moorti_nirnaya',ctx,coverage_of((2460000.,2460010.),(2460000.,2460010.),
        backend='swieph',convention_id=convention.convention_id),[])
    class Conn:
        def cursor(self,**kwargs): return self
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def execute(self,*a): pass
        def fetchone(self): return self.row
    conn=Conn();conn.row={'payload':json.loads(json.dumps(payload.content())), 'upstream_fingerprint':payload.upstream_fingerprint}
    loaded=load_candidate_payload(conn,chart_id='chart',generation='candidate:1',ayanamsha_id='lahiri_chitrapaksha',family='moorti_nirnaya')
    assert loaded.operator_role=='testimony'
    conn.row['payload']['entries']=[{'graha':'Saturn','quality_tier':4}]
    with pytest.raises(ValueError,match='fingerprint'):
        load_candidate_payload(conn,chart_id='chart',generation='candidate:1',ayanamsha_id='lahiri_chitrapaksha',family='moorti_nirnaya')
