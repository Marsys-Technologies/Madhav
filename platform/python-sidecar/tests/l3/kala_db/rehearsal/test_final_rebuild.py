"""K9-4a/b preparation is inert; actual stored readbacks decide each claim."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from tests.l3.kala_db.rehearsal.test_rehearsal import stored, ASSETS, WAVES


def tool():
    from services.kala_core import final_rebuild
    return final_rebuild


@pytest.fixture
def prepared(stored):
    conn, plan, candidate = stored
    plan = deepcopy(plan)
    grains = {aid: [aid + ':fixture'] for aid in ASSETS}
    plan['conventions']['publication_grains'] = grains
    conn.execute('UPDATE kala_layer_candidate SET conventions=%s', (Jsonb(plan['conventions']),))
    from services.kala_core.manifest import attest_grain
    for keys in grains.values():
        for key in keys:
            attest_grain(conn, candidate, grain_key=key, result_state='zero_rows', input_vector='fixture-input')
    conn.commit()
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT * FROM build_runs')
        run = cursor.fetchone()
    run['id'], run['chart_id'] = str(run['id']), str(run['chart_id'])
    return conn, tool().prepare(plan, run), plan


def readback(conn, bundle):
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute(bundle['readback_sql'])
        return cursor.fetchone()['evidence']


def test_preparation_uses_frozen_canonical_roster_and_k9_23_interface_without_dispatch(prepared):
    _, bundle, plan = prepared
    assert bundle['status'] == 'PREPARATION_ONLY'
    assert bundle['production_acceptance'] is None and bundle['dry_run_passed'] is None
    assert bundle['assets'] == ASSETS and len(bundle['assets']) == 20
    assert bundle['candidate']['expected_head_generation'] is None
    steps = {row['kind']: row for row in bundle['operations']}
    assert list(steps) == ['backup_snapshot', 'backup_restore_verify', 'orchestrator_rebuild_dryrun',
                           'orchestrator_rebuild', 'readback_sql', 'layer_verify', 'layer_publish', 'publication_readback']
    assert steps['orchestrator_rebuild']['args'] == {'run-id': plan['build_id'], 'assets': ','.join(ASSETS)}
    assert steps['layer_publish']['args']['expected-head'] == 'NONE'
    assert steps['layer_verify']['needs'] == 'layer_verifier'
    assert 'independently-derived-digest' in steps['layer_verify']['missing_inputs']
    assert all(op['enabled'] is False for op in bundle['operations'])
    assert all(op['request'] is None for op in bundle['operations'])
    assert bundle['rollback']['missing'] == 'no previous head exists'
    assert 'ka_bhavishya_lekha' not in bundle['assets']


@pytest.mark.parametrize('change', ['roster', 'resonance', 'order', 'registrar', 'chart', 'clear', 'generation', 'grain', 'service_grain', 'resonance_grain', 'manifest'])
def test_prepare_rejects_incomplete_or_widened_scope(stored, change):
    conn, plan, _ = stored
    plan = deepcopy(plan)
    plan['conventions']['publication_grains'] = {aid: [aid + ':fixture'] for aid in ASSETS}
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT * FROM build_runs')
        run = cursor.fetchone()
    run['id'], run['chart_id'] = str(run['id']), str(run['chart_id'])
    if change == 'roster': run['plan'] = run['plan'][:-1]
    elif change == 'resonance': run['plan'] = [aid for aid in run['plan'] if aid != 'ka_gochara_resonance']
    elif change == 'order': run['plan'] = list(reversed(run['plan']))
    elif change == 'registrar': run['plan'] += ['ka_bhavishya_lekha']
    elif change == 'chart': plan['chart_id'] = '11111111-1111-4111-8111-111111111111'
    elif change == 'clear': plan['request']['clear_before'] = True
    elif change == 'generation': plan['generation'] = 'NONE'
    elif change == 'grain': plan['conventions']['publication_grains']['ka_yojaka'] = ['ka_avadhi:fixture']
    elif change == 'service_grain': del plan['conventions']['publication_grains']['ka_graha_sancara']
    elif change == 'resonance_grain': del plan['conventions']['publication_grains']['ka_gochara_resonance']
    else: run['plan_manifest_digest'] = '0' * 64
    if change in {'roster', 'resonance', 'order', 'registrar'}:
        # Keep the manifest internally valid: this must test the final-layer
        # scope/order guard, not merely the frozen-manifest digest detector.
        by_asset={row['asset_id']:row for row in run['plan_manifest']['assets']}
        if change=='registrar':
            by_asset['ka_bhavishya_lekha']={**deepcopy(by_asset['ka_taranga']), 'asset_id':'ka_bhavishya_lekha'}
        run['plan_manifest']['waves']=[[aid] for aid in run['plan']]
        run['plan_manifest']['assets']=[by_asset[aid] for aid in run['plan']]
        run['plan_manifest_digest']=hashlib.sha256(json.dumps(run['plan_manifest'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        from pipeline.orchestrator.runner import validate_frozen_run_manifest
        validate_frozen_run_manifest(run)
    with pytest.raises(ValueError): tool().prepare(plan, run)


def test_real_single_select_readback_measures_each_writer_and_zero_row_grain(prepared):
    conn, bundle, _ = prepared
    result = tool().inspect_readback(bundle, readback(conn, bundle), phase='rebuilt')
    assert result['status'] == 'OBSERVED_COMPLETE'
    assert result['writer_results_complete'] is True and result['grain_results_complete'] is True
    assert len(result['writers']) == 20
    assert result['independent_verification'] is False
    assert result['production_acceptance'] is None
    assert result['semantic_verification'] is None
    assert result['head_unchanged'] is True


@pytest.mark.parametrize('mutation', ['writer_missing', 'writer_failed', 'writer_error', 'writer_overlap', 'run_wrong',
                                    'candidate_wrong', 'grain_missing', 'grain_failed', 'grain_empty', 'grain_extra', 'head_changed'])
def test_stored_rebuild_faults_cannot_earn_complete(prepared, mutation):
    conn, bundle, plan = prepared
    statements = {
      'writer_missing': "DELETE FROM build_run_assets WHERE asset_id='ka_taranga'",
      'writer_failed': "UPDATE build_run_assets SET state='error' WHERE asset_id='ka_taranga'",
      # The fixture models the nullable production error column additively.
      'writer_error': "ALTER TABLE build_run_assets ADD COLUMN error text; UPDATE build_run_assets SET error='failed' WHERE asset_id='ka_taranga'",
      'writer_overlap': "UPDATE build_run_assets SET started_at='2026-10-01T00:00Z' WHERE asset_id='ka_kshetra'",
      'run_wrong': "UPDATE build_runs SET state='failed'",
      'candidate_wrong': "UPDATE kala_layer_candidate SET build_id='11111111-1111-4111-8111-111111111111'",
      'grain_missing': "DELETE FROM kala_layer_candidate_grain WHERE grain_key='ka_taranga:fixture'",
      'grain_failed': "UPDATE kala_layer_candidate_grain SET result_state='failed' WHERE grain_key='ka_taranga:fixture'",
      'grain_empty': "UPDATE kala_layer_candidate_grain SET input_vector='' WHERE grain_key='ka_taranga:fixture'",
      'grain_extra': "INSERT INTO kala_layer_candidate_grain(chart_id,generation,grain_key,result_state,input_vector) SELECT chart_id,generation,'extra','rows','input' FROM kala_layer_candidate",
      'head_changed': "INSERT INTO kala_layer_head(chart_id,generation) SELECT chart_id,'other' FROM kala_layer_candidate",
    }
    conn.execute(statements[mutation]); conn.commit()
    with pytest.raises(ValueError): tool().inspect_readback(bundle, readback(conn, bundle), phase='rebuilt')


def test_verification_and_publication_readback_bind_current_grain_digest_and_previous_head(prepared):
    conn, bundle, plan = prepared
    rows = conn.execute('SELECT grain_key,input_vector FROM kala_layer_candidate_grain ORDER BY grain_key').fetchall()
    digest = hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()
    conn.execute("INSERT INTO kala_layer_verification(chart_id,generation,verifier_principal,result,detail) VALUES (%s,%s,'verifier_principal','accepted',%s)",
                 (plan['chart_id'], plan['generation'], Jsonb({'input_digest': digest})))
    conn.commit()
    result = tool().inspect_readback(bundle, readback(conn, bundle), phase='verified')
    assert result['independent_verification'] is True
    # An input-digest verification is never misrepresented as all-writer semantic acceptance.
    assert result['semantic_verification'] is None and result['production_acceptance'] is None
    conn.execute("UPDATE kala_layer_candidate SET state='published'")
    conn.execute('INSERT INTO kala_layer_head(chart_id,generation) VALUES (%s,%s)', (plan['chart_id'],plan['generation']))
    conn.commit()
    assert tool().inspect_readback(bundle, readback(conn, bundle), phase='published')['publication_observed'] is True
    conn.execute("UPDATE kala_layer_candidate_grain SET input_vector='changed'")
    conn.commit()
    with pytest.raises(ValueError): tool().inspect_readback(bundle, readback(conn, bundle), phase='published')


def test_readback_cannot_be_imported_under_a_changed_plan(prepared):
    conn, bundle, _ = prepared
    evidence = readback(conn, bundle)
    changed = deepcopy(bundle); changed['assets'] = changed['assets'][:-1]
    with pytest.raises(ValueError): tool().inspect_readback(changed, evidence, phase='rebuilt')

@pytest.mark.parametrize('mutation', [None, 'absent_verification', 'wrong_principal', 'missing_retained', 'retained_not_published', 'wrong_head'])
def test_existing_previous_head_and_independent_verification_are_read_back(prepared, mutation):
    conn, original, plan = prepared
    plan = deepcopy(plan); plan['expected_head_generation'] = 'retained-head'
    conn.execute("UPDATE kala_layer_candidate SET expected_head_generation='retained-head'")
    conn.execute("""INSERT INTO kala_layer_candidate(chart_id,generation,build_id,state,model_digest,rule_registry_version,conventions)
      VALUES (%s,'retained-head','33333333-3333-4333-8333-333333333333','published','old-model','old-rules','{}')""", (plan['chart_id'],))
    bundle = tool().prepare(plan, original['frozen_run'])
    assert bundle['rollback']['args'] == {'generation':'retained-head','expected-head':plan['generation']}
    rows = conn.execute('SELECT grain_key,input_vector FROM kala_layer_candidate_grain ORDER BY grain_key').fetchall()
    digest = hashlib.sha256(json.dumps(rows,separators=(',', ':')).encode()).hexdigest()
    conn.execute("INSERT INTO kala_layer_verification(chart_id,generation,verifier_principal,result,detail) VALUES (%s,%s,'verifier_principal','accepted',%s)",
                 (plan['chart_id'], plan['generation'], Jsonb({'input_digest':digest})))
    conn.execute("UPDATE kala_layer_candidate SET state='published' WHERE generation=%s", (plan['generation'],))
    conn.execute('INSERT INTO kala_layer_head(chart_id,generation) VALUES (%s,%s)',(plan['chart_id'],plan['generation']))
    if mutation == 'absent_verification': conn.execute('DELETE FROM kala_layer_verification')
    if mutation == 'wrong_principal': conn.execute("UPDATE kala_layer_verification SET verifier_principal='builder'")
    if mutation == 'missing_retained': conn.execute("DELETE FROM kala_layer_candidate WHERE generation='retained-head'")
    if mutation == 'retained_not_published': conn.execute("UPDATE kala_layer_candidate SET state='building' WHERE generation='retained-head'")
    if mutation == 'wrong_head': conn.execute("UPDATE kala_layer_head SET generation='retained-head'")
    conn.commit()
    if mutation:
        with pytest.raises(ValueError): tool().inspect_readback(bundle, readback(conn,bundle), phase='published')
    else:
        assert tool().inspect_readback(bundle, readback(conn,bundle), phase='published')['publication_observed'] is True


def test_cli_is_offline_and_never_accepts_execute_or_dsn_flags(prepared, tmp_path, monkeypatch, capsys):
    _,bundle,plan = prepared
    module=tool()
    monkeypatch.setattr(psycopg,'connect',lambda *a,**kw: pytest.fail('offline tool attempted a connection'))
    p,r=tmp_path/'plan.json',tmp_path/'run.json'
    p.write_text(json.dumps(plan)); r.write_text(json.dumps(bundle['frozen_run']))
    assert module.main(['prepare','--plan',str(p),'--run',str(r)]) == 0
    assert json.loads(capsys.readouterr().out)['status']=='PREPARATION_ONLY'
    for args in (['--execute'],['--dsn','postgresql://invalid']):
        with pytest.raises(SystemExit): module.main(['prepare','--plan',str(p),'--run',str(r),*args])

def test_valid_order_inside_one_wave_preserves_the_actual_frozen_dispatch_order(prepared):
    _, original, plan = prepared
    run=deepcopy(original['frozen_run'])
    manifest=run['plan_manifest']
    manifest['waves'][0]=list(reversed(manifest['waves'][0]))
    run['plan']=[aid for wave in manifest['waves'] for aid in wave]
    indexed={row['asset_id']:row for row in manifest['assets']}
    manifest['assets']=[indexed[aid] for aid in run['plan']]
    run['plan_manifest_digest']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    bundle=tool().prepare(plan,run)
    assert bundle['assets']==run['plan']
    dispatch=next(row for row in bundle['operations'] if row['kind']=='orchestrator_rebuild')
    assert dispatch['args']['assets']==','.join(run['plan'])
