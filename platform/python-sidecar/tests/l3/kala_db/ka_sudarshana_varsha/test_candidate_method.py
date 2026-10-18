"""Real KA-3b store/read + read-time J7 method; no schema or served admission."""
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

import pytest

from services.kala_core.overlays import contested_reader
from services.kala_core.clocks.methods import ClockFact
from services.ka_sudarshana_varsha.candidate import build_candidate
from services.ka_sudarshana_varsha.method import F1Snapshot, HouseEvidence, Influence, evaluate_candidate
from services.ka_sudarshana_varsha.writer import KaSudarshanaVarshaWriter
from tests.l3.ka_adapters.test_candidates import CHART,NATAL,BUILD,CONVENTION,sign_context,cov


def candidate(conn):
    p=build_candidate(ctx=sign_context(),birth_date=date(1984,2,5),years=(42,),
                      coverage=cov(2460676.5,2461406.5,source=(2460676.5,2461406.5)),year_anchor='civil_birthday')
    # Year 42 starts 2025-02-05. This seeded F1 nature and strength cites real
    # fixture L1 rows. They are planted operands, not an ephemeris observation.
    conn.execute("INSERT INTO chart_facts VALUES ('jupiter-position',%s,%s,'lahiri_chitrapaksha',"
                 "'graha_position','JUPITER','longitude_sidereal',150,NULL)",(CHART,NATAL))
    influence=Influence('Jupiter','f1:jupiter-sign5','planted F1 condition assessment',
                        ClockFact('benefic',('jupiter-position',)),ClockFact(None,()),None)
    houses=tuple(HouseEvidence(i,(influence,) if i==5 else (),(),None,True,True) for i in range(12))
    s=F1Snapshot(CHART,'candidate-1',NATAL,CONVENTION.convention_id,p.entries[0]['t_in'],houses,'f1:planted')
    return p,s


def store(conn,p):
    ctx=SimpleNamespace(db_conn=conn,build_id=BUILD,dry_run=False,
        config={'chart_id':CHART,'birth_params':{'datetime_iso':'1984-02-05T10:43:00+05:30'},'ka_adapter_payload':p})
    return KaSudarshanaVarshaWriter().run(ctx)


def read(conn,s):
    return contested_reader.load_sudarshana_method(conn,chart_id=CHART,generation='candidate-1',
            ayanamsha_id='lahiri_chitrapaksha',year=42,evidence=s)


def test_readonly_method_on_stored_candidate_preserves_legacy_head_and_f2_rows(conn):
    assert hasattr(contested_reader,'load_sudarshana_method'), 'explicit candidate method reader missing'
    p,s=candidate(conn)
    before=conn.execute('SELECT to_jsonb(t) FROM kala_sudarshana_varsha t').fetchall()
    assert store(conn,p).rows_inserted==1
    persisted_before=conn.execute('SELECT payload FROM kala_sudarshana_varsha_candidate').fetchall()
    layer_before=conn.execute('SELECT to_jsonb(t) FROM kala_layer_candidate t').fetchall()
    with conn.transaction():
        conn.execute('SET TRANSACTION READ ONLY')
        result=read(conn,s)
    assert result==evaluate_candidate(p,year=42,evidence=s)
    assert len(result['periods'])==1885  # any coincident pair -> birth chart only
    frame=result['frames'][0]
    assert (frame['frame'],frame['active_sign_idx'])==('birth_chart',5)
    assert frame['houses'][0]['conclusion']=='favorable'
    assert set(frame['houses'][0]['fact_ids'])=={'lagna-sign','moon-sign','sun-sign','jupiter-position'}
    assert len(frame['houses'])==12 and frame['coverage']=='partial'
    assert conn.execute('SELECT payload FROM kala_sudarshana_varsha_candidate').fetchall()==persisted_before
    assert conn.execute('SELECT to_jsonb(t) FROM kala_sudarshana_varsha t').fetchall()==before
    assert conn.execute('SELECT to_jsonb(t) FROM kala_layer_candidate t').fetchall()==layer_before
    assert conn.execute('SELECT count(*) FROM kala_layer_head').fetchone()[0]==0
    assert result['admission']=='candidate_only' and result['value'] is None


@pytest.mark.parametrize('field,value',[('chart_id',NATAL),('generation','candidate-2'),
    ('natal_build_id',BUILD),('convention_id','other'),('at_jd',2460000.)])
def test_db_candidate_method_refuses_cross_pin_evidence(conn,field,value):
    assert hasattr(contested_reader,'load_sudarshana_method'), 'explicit candidate method reader missing'
    p,s=candidate(conn); store(conn,p)
    with pytest.raises(ValueError): read(conn,replace(s,**{field:value}))


def test_missing_candidate_never_resolves_a_published_head(conn):
    assert hasattr(contested_reader,'load_sudarshana_method'), 'explicit candidate method reader missing'
    _,s=candidate(conn)
    assert read(conn,s) is None


def test_db_method_refuses_unresolved_or_other_chart_l1_references(conn):
    p,s=candidate(conn); store(conn,p)
    houses=list(s.houses)
    original=houses[5].occupants[0]
    for ref in ('nonexistent-l1-reference','foreign-position'):
        if ref=='foreign-position':
            conn.execute("INSERT INTO chart_facts VALUES (%s,%s,%s,'lahiri_chitrapaksha',"
                         "'graha_position','JUPITER','longitude_sidereal',150,NULL)",(ref,NATAL,NATAL))
        changed=replace(original,nature=ClockFact('benefic',(ref,)))
        houses[5]=replace(houses[5],occupants=(changed,))
        with pytest.raises(ValueError,match='reference|L1'):
            read(conn,replace(s,houses=tuple(houses)))
