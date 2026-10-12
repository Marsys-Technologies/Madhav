"""Real SQL K6 consumer oracles over a disposable, explicitly planted candidate."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from pipeline.orchestrator.writers.ka_kalasutra import KaKalasutraWriter
from pipeline.orchestrator.writers.ka_kala_darshana import KaKalaDarshanaWriter
from pipeline.orchestrator.writers.ka_jivana_parva import KaJivanaParvaWriter
from pipeline.orchestrator.writers.k6_candidate import MODELS
from tests.l3.ka_kalasutra.test_candidate_contract import bundle

PLATFORM = Path(__file__).resolve().parents[5]
CHART = '00000000-0000-0000-0000-000000000601'
BUILD = '00000000-0000-0000-0000-000000000602'
GEN = 'candidate:CODEX-k6'
WRITERS = [KaKalasutraWriter, KaKalaDarshanaWriter, KaJivanaParvaWriter]
ASSETS = list(MODELS)
MIGRATIONS = ['1353_k6_kalasutra_candidate.sql', '1354_k6_darshana_candidate.sql',
              '1355_k6_jivana_candidate.sql', '1356_k6_read_model_build_scoped_detectors.sql']


def evidence():
    return dict(chart_id=CHART, generation=GEN, scenario_id='CODEX-scenario',
                ayanamsha_id='lahiri_chitrapaksha',
                source={'text': 'CODEX', 'locator': 'CODEX/1'},
                provenance={'acceptance_scope': 'fixture_only', 'source_id': 'CODEX-input'})


def span(start='2000-01-01', end='2001-01-01'):
    return dict(**evidence(), start=start+'T00:00:00+00:00', end=end+'T00:00:00+00:00',
                coverage={'state': 'complete', 'reason': None})


def planted():
    value = bundle()
    value['mechanisms'] = [dict(**evidence(), mechanism_id=f'CODEX-m{i}',
        assertion_id=f'CODEX-f1-{i}', participant_ids=['CODEX-Mars'],
        constituent_lords=['Mars'], event_class='CODEX-gain') for i in range(2)]
    value['windows'] = [dict(**span(), assertion_id='CODEX-judge', event_class='CODEX-gain',
        participant_ids=['CODEX-Mars'], contact_ids=['CODEX-contact-1'], record_ids=['CODEX-record'],
        operator_role='scored', period_anchor={'system': None, 'level': None, 'lord': None,
                                             'period_id': None, 'no_prerequisite': True},
        valence={'natal': None, 'transit': 'adverse', 'occurrence': {'evidence': 'CODEX'}})]
    value['contacts'] = [dict(**span(), contact_id=f'CODEX-contact-{i+1}',
        occurrence_ordinal=i+1, participant_ids=['CODEX-Mars']) for i in range(12)]
    condition = dict(participant_conditions={'CODEX-Mars': 'own'},
                     commencement_condition={'state': 'CODEX-onset'}, effective_state='in_force',
                     coverage={'state': 'complete', 'reason': None})
    for i, (start, end, lord) in enumerate([('2000-01-01','2001-01-01','Saturn'),
                                           ('2001-01-01','2002-01-01','Venus')]):
        current = deepcopy(condition)
        if i: current['participant_conditions']['CODEX-Mars'] = 'debilitated'
        value['periods'].append(dict(**span(start,end), period_id=f'CODEX-MD-{i}',
            assertion_id=f'CODEX-f2-{i}', system='vimshottari', level=1, lord=lord,
            parent_id=None, sigma_boundary={'value': None, 'null_reason': 'information_unavailable'},
            dossier={'lord': lord}, mechanism_conditions={'CODEX-m0': current}))
    value['periods'].append(dict(**span('2000-02-01','2000-03-01'), period_id='CODEX-AD',
        assertion_id='CODEX-f2-ad', system='vimshottari', level=2, lord='Moon',
        parent_id='CODEX-MD-0', sigma_boundary={'value': 3, 'unit': 'seconds'},
        dossier={'lord': 'Moon'}, mechanism_conditions={}))
    value['negative_space'] = [dict(**evidence(), assertion_id='CODEX-negative',
        target_assertion_id='CODEX-judge', effective_state='cancelled',
        coverage={'state': 'complete', 'reason': None})]
    value['jury'] = [dict(**span(), assertion_id='CODEX-jury', event_class='CODEX-gain',
        dw=None, null_reason='information_unavailable', witness_signature=['G-P'], segment_support=[])]
    value['contexts'] = [dict(**span('2002-01-01','2003-01-01'), assertion_id='CODEX-gap',
        event_class='CODEX-gain', kind='coverage_gap', reason='judge_horizon_unsearched')]
    value['contexts'][0]['coverage'] = {'state': 'absent', 'reason': 'judge_horizon_unsearched'}
    value['lel'] = [dict(**evidence(), event_id=f'CODEX-LEL-{i}', period_id='CODEX-MD-0',
                        role=role, used_for_selection=used)
                    for i, (role, used) in enumerate([('explains', False), ('selects', True),
                                                      ('explains', True), ('scores', False)])]
    return value


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute('''CREATE TABLE kala_layer_candidate(chart_id uuid,generation text,build_id uuid,
            state text,conventions jsonb,PRIMARY KEY(chart_id,generation));
            CREATE TABLE kala_layer_head(chart_id uuid,generation text);
            CREATE TABLE build_runs(id uuid,chart_id uuid,state text,created_at timestamptz);
            CREATE TABLE asset_registry(asset_id text PRIMARY KEY,count_sql text,integrity_check_sql text);
            CREATE TABLE kala_activation(chart_id uuid,payload jsonb);
            CREATE TABLE kala_darshana(chart_id uuid,payload jsonb);
            CREATE TABLE kala_jivana_parva(chart_id uuid,payload jsonb);''')
        conn.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,'building','{\"fixture\":true}')", (CHART,GEN,BUILD))
        conn.execute("INSERT INTO build_runs VALUES (%s,%s,'running','2000-01-01')",(BUILD,CHART))
        for asset in ASSETS: conn.execute("INSERT INTO asset_registry VALUES (%s,'SELECT 0','SELECT true;')", (asset,))
        for table in ('kala_activation', 'kala_darshana', 'kala_jivana_parva'):
            conn.execute(f"INSERT INTO {table} VALUES (%s,'{{\"served\":\"unchanged\"}}')", (CHART,))
        for filename in MIGRATIONS: conn.execute((PLATFORM/'migrations'/filename).read_text())
        yield conn
        conn.rollback()


def ctx(db, value=None):
    return SimpleNamespace(db_conn=db, build_id=BUILD, dry_run=False,
                          config={'chart_id': CHART, 'kala_read_model_fixture': planted() if value is None else value})


def payloads(db, asset, kind=None):
    table = MODELS[asset][0]
    return [r[0] for r in db.execute(f'SELECT payload FROM {table} WHERE chart_id=%s AND generation=%s '
        + ('AND row_kind=%s ' if kind else '') + 'ORDER BY interval_start,model_key',
        (CHART,GEN,kind) if kind else (CHART,GEN)).fetchall()]


def test_shared_contact_identity(db):
    KaKalasutraWriter().run(ctx(db))
    assert [p['contact_ids'] for p in payloads(db, 'ka_kalasutra', 'judge')] == [['CODEX-contact-1']]*2


def test_no_universal_dasha_gate_or_synthetic_bounds(db):
    KaKalasutraWriter().run(ctx(db))
    assert [(p['period_anchor']['no_prerequisite'],p['lord_period_concurrent'],p['judge']['start'],p['judge']['end'])
        for p in payloads(db,'ka_kalasutra','judge')] == [(True,False,'2000-01-01T00:00:00Z','2001-01-01T00:00:00Z')]*2


def test_ladder_has_no_eight_match_cap(db):
    KaKalasutraWriter().run(ctx(db))
    assert len(payloads(db,'ka_kalasutra','contact')) == 24


def test_unsearched_interval_survives(db):
    KaKalasutraWriter().run(ctx(db))
    assert [p['search_state'] for p in payloads(db,'ka_kalasutra','context')] == ['unsearched']*2


def test_pd_testimony_is_never_scored(db):
    value=planted(); value['windows'][0].update(operator_role='testimony',
        period_anchor=dict(system='vimshottari',level=3,lord='Mars',period_id='CODEX-PD-judge',no_prerequisite=False))
    KaKalasutraWriter().run(ctx(db,value))
    assert [p['scored'] for p in payloads(db,'ka_kalasutra','judge')] == [False,False]


def test_scored_pd_refused_before_replacement(db):
    value=planted(); value['windows'][0]['period_anchor']=dict(system='vimshottari',level=3,lord='Mars',period_id='CODEX-PD',no_prerequisite=False)
    with pytest.raises(ValueError,match='PD'): KaKalasutraWriter().run(ctx(db,value))


def test_f2_concurrency_is_annotation_only(db):
    value=planted(); value['periods'][0]['lord']='Mars'
    KaKalasutraWriter().run(ctx(db,value))
    assert [p['lord_period_ids'] for p in payloads(db,'ka_kalasutra','judge')] == [['CODEX-MD-0']]*2


def test_darshana_retains_cancelled_negative_space_and_separate_valence(db):
    KaKalaDarshanaWriter().run(ctx(db))
    assert [(p['negative_space']['assertion_id'],p['effective_state'],p['valence']['natal'],p['jury'][0]['dw'])
        for p in payloads(db,'ka_kala_darshana','judge')] == [('CODEX-negative','cancelled',None,None)]


def test_missing_negative_mapping_stays_unavailable(db):
    value=planted(); value['negative_space']=[]
    KaKalaDarshanaWriter().run(ctx(db,value))
    assert payloads(db,'ka_kala_darshana','judge')[0]['null_reason'] == 'negative_space_mapping_missing'


def test_forecaster_zero_is_retained_separately(db):
    value=planted(); value['upstream_refs']['forecaster']=deepcopy(value['upstream_refs']['jury'])
    value['forecaster']=[dict(**span(),assertion_id='CODEX-forecast',event_class='CODEX-gain',
                              alignment_surprise=0.0,null_reason=None)]
    KaKalaDarshanaWriter().run(ctx(db,value))
    assert payloads(db,'ka_kala_darshana','judge')[0]['forecaster'][0]['alignment_surprise']==0.0


def test_coverage_gap_is_visible_without_judge(db):
    value=planted(); value['windows']=[]; value['negative_space']=[]
    KaKalaDarshanaWriter().run(ctx(db,value))
    assert payloads(db,'ka_kala_darshana','context')[0]['context']['assertion_id'] == 'CODEX-gap'


def test_no_top_750_truncation(db):
    value=planted(); base=value['windows'][0]
    value['windows']=[dict(base,assertion_id=f'CODEX-judge-{i}') for i in range(751)]; value['negative_space']=[]
    KaKalaDarshanaWriter().run(ctx(db,value))
    assert len(payloads(db,'ka_kala_darshana','judge')) == 751


def test_jivana_ignores_legacy_convergence(db):
    writer=KaJivanaParvaWriter(); writer.run(ctx(db)); before=payloads(db,'ka_jivana_parva')
    db.execute('CREATE TABLE kala_convergence(score numeric); INSERT INTO kala_convergence VALUES (999)')
    writer.run(ctx(db)); db.execute('DROP TABLE kala_convergence'); writer.run(ctx(db))
    assert payloads(db,'ka_jivana_parva') == before


@pytest.mark.parametrize('field,value', [('participant_conditions',{'CODEX-Mars':'changed'}),
    ('commencement_condition',{'state':'changed'}),('effective_state','defeated'),
    ('coverage',{'state':'absent','reason':'changed'})])
def test_same_mechanism_condition_change_is_attributable(db,field,value):
    data=planted(); data['periods'][1]['mechanism_conditions']=deepcopy(data['periods'][0]['mechanism_conditions'])
    data['periods'][1]['mechanism_conditions']['CODEX-m0'][field]=value
    KaJivanaParvaWriter().run(ctx(db,data))
    last=next(p for p in payloads(db,'ka_jivana_parva') if p['period']['period_id']=='CODEX-MD-1')
    assert [(d['mechanism_id'],d['kind'],d['changed_fields']) for d in last['diff']] == [('CODEX-m0','changed',[field])]


def test_ad_names_its_own_lord(db):
    KaJivanaParvaWriter().run(ctx(db))
    assert next(p['lord'] for p in payloads(db,'ka_jivana_parva') if p['period']['level']==2) == 'Moon'


def test_lel_selection_circularity_guard(db):
    KaJivanaParvaWriter().run(ctx(db))
    assert [r['event_id'] for p in payloads(db,'ka_jivana_parva') for r in p['lel']] == ['CODEX-LEL-0']


@pytest.mark.parametrize('writer',WRITERS)
def test_rebuild_twice_zero_net_rows_and_identical_output(db,writer):
    instance=writer(); first=instance.run(ctx(db)); rows=payloads(db,first.asset_id); second=instance.run(ctx(db))
    assert (second.rows_inserted,payloads(db,first.asset_id)) == (first.rows_inserted,rows)


@pytest.mark.parametrize('writer',WRITERS)
def test_preserve_served_rows_and_other_candidates(db,writer):
    db.execute("INSERT INTO kala_layer_candidate VALUES (%s,'candidate:CODEX-other',%s,'building','{\"fixture\":true}')",
                 ('00000000-0000-0000-0000-000000000603','00000000-0000-0000-0000-000000000604'))
    writer().run(ctx(db))
    assert [db.execute(f'SELECT payload FROM {t}').fetchall() for t in
        ('kala_activation','kala_darshana','kala_jivana_parva')] == [[({'served':'unchanged'},)]]*3


@pytest.mark.parametrize('writer',WRITERS)
@pytest.mark.parametrize('mutation', ['complete','published','head','live'])
def test_refuse_nonbuilding_published_or_live_candidates(db,writer,mutation):
    if mutation in ('complete','published'): db.execute('UPDATE kala_layer_candidate SET state=%s',(mutation,))
    if mutation=='head': db.execute('INSERT INTO kala_layer_head VALUES (%s,%s)',(CHART,GEN))
    if mutation=='live': db.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    with pytest.raises(ValueError): writer().run(ctx(db))


@pytest.mark.parametrize('writer',WRITERS)
def test_dry_run_performs_no_sql(db,writer):
    context=ctx(None); context.dry_run=True
    assert writer().run(context).rows_inserted == 0


@pytest.mark.parametrize('asset',ASSETS)
def test_real_count_is_chart_scoped_and_integrity_survives_completion(db,asset):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    count,check=db.execute('SELECT count_sql,integrity_check_sql FROM asset_registry WHERE asset_id=%s',(asset,)).fetchone()
    db.execute("UPDATE kala_layer_candidate SET state='complete'")
    db.execute("UPDATE build_runs SET state='completed'")
    assert (db.execute(count.replace('$1','%s'),(CHART,CHART)).fetchone()[0],db.execute(check).fetchone()[0],
        db.execute(count.replace('$1','%s'),('00000000-0000-0000-0000-000000000999',)*2).fetchone()[0]) == (len(payloads(db,asset)),True,0)


def test_three_migrations_are_repeatable_and_no_numeric_composite_exists(db):
    before=db.execute('SELECT * FROM asset_registry ORDER BY asset_id').fetchall()
    for name in MIGRATIONS: db.execute((PLATFORM/'migrations'/name).read_text())
    assert (db.execute('SELECT * FROM asset_registry ORDER BY asset_id').fetchall(),
        db.execute("SELECT column_name FROM information_schema.columns WHERE table_name='kala_darshana_candidate' AND data_type IN ('numeric','double precision','real')").fetchall()) == (before,[])


@pytest.mark.parametrize('writer',WRITERS)
def test_empty_rebuild_removes_only_its_partition(db,writer):
    instance=writer(); asset=instance.run(ctx(db)).asset_id
    instance.run(ctx(db,bundle()))
    assert payloads(db,asset) == []


@pytest.mark.parametrize('mutation', ['chart','generation','scenario','source','contact','duplicate','parent'])
def test_bad_reference_fails_before_old_candidate_is_replaced(db,mutation):
    instance=KaKalasutraWriter(); instance.run(ctx(db)); before=payloads(db,'ka_kalasutra')
    value=planted()
    if mutation=='chart': value['windows'][0]['chart_id']='CODEX-wrong'
    if mutation=='generation': value['windows'][0]['generation']='legacy'
    if mutation=='scenario': value['windows'][0]['scenario_id']='CODEX-wrong'
    if mutation=='source': del value['windows'][0]['source']['locator']
    if mutation=='contact': value['windows'][0]['contact_ids']=['CODEX-missing']
    if mutation=='duplicate': value['contacts'].append(deepcopy(value['contacts'][0]))
    if mutation=='parent': value['periods'][2]['parent_id']='CODEX-missing'
    with pytest.raises(ValueError): instance.run(ctx(db,value))
    assert payloads(db,'ka_kalasutra') == before


def test_changed_as_of_is_explicit_and_deterministic(db):
    value=planted(); value['as_of']='2010-01-01T00:00:00+00:00'
    KaKalasutraWriter().run(ctx(db,value))
    assert db.execute('SELECT DISTINCT as_of::date::text FROM kala_activation_candidate').fetchall() == [('2010-01-01',)]


def test_other_candidate_rows_cannot_be_deleted(db):
    KaKalasutraWriter().run(ctx(db))
    other='candidate:CODEX-retained'
    db.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,'00000000-0000-0000-0000-000000000605','complete','{\"fixture\":true}')",(CHART,other))
    db.execute('''INSERT INTO kala_activation_candidate SELECT chart_id,%s,model_key,row_kind,
        interval_start,interval_end,as_of,payload,upstream_refs,tier FROM kala_activation_candidate''',(other,))
    before=db.execute('SELECT * FROM kala_activation_candidate WHERE generation=%s ORDER BY model_key',(other,)).fetchall()
    KaKalasutraWriter().run(ctx(db,bundle()))
    assert db.execute('SELECT * FROM kala_activation_candidate WHERE generation=%s ORDER BY model_key',(other,)).fetchall()==before


def test_integrity_rejects_changed_acceptance_scope(db):
    KaKalaDarshanaWriter().run(ctx(db))
    db.execute("UPDATE kala_darshana_candidate SET payload=jsonb_set(payload,'{acceptance_scope}','\"admitted\"')")
    check=db.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_kala_darshana'").fetchone()[0]
    assert db.execute(check).fetchone()[0] is False


@pytest.mark.parametrize('asset',ASSETS)
def test_detector_never_counts_retained_generation(db,asset):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    table=MODELS[asset][0]; other='candidate:CODEX-retained'
    db.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,'00000000-0000-0000-0000-000000000605','complete','{\"fixture\":true}')",(CHART,other))
    db.execute(f'''INSERT INTO {table} SELECT chart_id,%s,model_key,row_kind,interval_start,interval_end,
        as_of,payload,upstream_refs,tier FROM {table}''',(other,))
    count=db.execute('SELECT count_sql FROM asset_registry WHERE asset_id=%s',(asset,)).fetchone()[0]
    assert db.execute(count.replace('$1','%s'),(CHART,CHART)).fetchone()[0]==len(payloads(db,asset))


@pytest.mark.parametrize('asset',ASSETS)
def test_later_legacy_build_keeps_original_count_and_integrity(db,asset):
    WRITERS[ASSETS.index(asset)]().run(ctx(db))
    db.execute("INSERT INTO build_runs VALUES ('00000000-0000-0000-0000-000000000606',%s,'completed','2001-01-01')",(CHART,))
    count,check=db.execute('SELECT count_sql,integrity_check_sql FROM asset_registry WHERE asset_id=%s',(asset,)).fetchone()
    assert (db.execute(count.replace('$1','%s'),(CHART,CHART)).fetchone()[0],db.execute(check).fetchone()[0])==(1,True)
