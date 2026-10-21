"""K9-1 preparation: real stored evidence, never a synthetic full-build claim."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from services.kala_core import rehearsal
from services.kala_core.manifest import attest_grain, open_candidate, publish_candidate


# Independent contract roster from PLAN §4.1 / §6.4. Removing a writer, admitting
# the delivery registrar, placing Avadhi before F1, or dropping ka_gochara_resonance (K9 r4:
# registry edges ka_yojaka -> ka_gochara_resonance -> ka_gochara/ka_kshetra, migration 1392)
# must break these tests.
WAVES = [
    ['ka_dasha_kala', 'ka_vedha_gochara', 'ka_moorti_nirnaya', 'ka_kota_chakra',
     'ka_tithi_pravesha', 'ka_sudarshana_varsha'],
    ['ka_yojaka'], ['ka_gochara_resonance'], ['ka_avadhi'], ['ka_gochara_v5'], ['ka_vighnakara'],
    ['ka_sangam'], ['ka_kshetra'],
    ['ka_kalasutra', 'ka_kala_darshana', 'ka_taranga', 'ka_jivana_parva'],
    ['ka_tulana', 'ka_muhurta_seva', 'ka_graha_sancara'],
]
ASSETS = [asset for wave in WAVES for asset in wave]
MATERIALIZED = ['ka_yojaka', 'ka_gochara_resonance', 'ka_avadhi', 'ka_gochara_v5', 'ka_vighnakara',
                'ka_sangam', 'ka_kshetra', 'ka_kalasutra', 'ka_kala_darshana',
                'ka_taranga', 'ka_jivana_parva']
CODE = 'a' * 64


def spec():
    return dict(lane='k9_1', chart_id='482012f1-710e-4a25-994a-93821f5871aa',
                generation='k9-fixture', build_id=str(uuid4()), expected_head_generation=None,
                model_digest='fixture-model', rule_registry_version='fixture-rules',
                conventions={'fixture': True},
                grains_by_asset={asset: [asset + ':fixture'] for asset in MATERIALIZED})


def test_preparation_has_safe_real_api_request_and_explicit_grains():
    plan = rehearsal.prepare_rehearsal(**spec())
    assert plan['request'] == {
        'chart_id': '482012f1-710e-4a25-994a-93821f5871aa', 'scope': 'asset_set',
        'scope_target': ','.join(ASSETS), 'action': 'rebuild', 'clear_before': False,
    }
    assert plan['waves'] == WAVES
    assert plan['status'] == 'prepared'
    assert plan['operational_rehearsal_passed'] is None
    assert plan['publication_path_verified'] is None
    assert 'ka_bhavishya_lekha' not in plan['request']['scope_target']


@pytest.mark.parametrize('mutation', ['missing', 'missing_resonance', 'empty', 'duplicate', 'extra', 'current', 'same_head'])
def test_preparation_refuses_unpinned_or_incomplete_workload(mutation):
    args = spec()
    if mutation == 'missing': del args['grains_by_asset']['ka_taranga']
    if mutation == 'missing_resonance': del args['grains_by_asset']['ka_gochara_resonance']
    if mutation == 'empty': args['grains_by_asset']['ka_taranga'] = []
    if mutation == 'duplicate': args['grains_by_asset']['ka_taranga'] = ['ka_yojaka:fixture']
    if mutation == 'extra': args['grains_by_asset']['ka_bhavishya_lekha'] = ['delivery']
    if mutation == 'current': args['generation'] = 'current'
    if mutation == 'same_head': args['expected_head_generation'] = args['generation']
    with pytest.raises(ValueError):
        rehearsal.prepare_rehearsal(**args)


@pytest.fixture
def stored(kala_db_dsn):
    """Only the existing guarded fixture creates/drops this isolated database."""
    with psycopg.connect(kala_db_dsn) as conn:
        migration = Path(__file__).resolve().parents[5] / 'migrations/1330_kala_layer_manifest_candidates.sql'
        conn.execute(migration.read_text().split('-- A separately dispatched verifier')[0])
        conn.execute('''CREATE TABLE build_runs
            (id uuid PRIMARY KEY, chart_id uuid, scope text, scope_target text,
             action text, state text, plan jsonb, plan_manifest jsonb, plan_manifest_digest text)''')
        conn.execute('''CREATE TABLE build_run_assets
            (run_id uuid, asset_id text, state text, started_at timestamptz, ended_at timestamptz)''')
        conn.execute('''CREATE TABLE asset_registry
            (asset_id text PRIMARY KEY, asset_kind text, integrity_check_sql text, health_probe jsonb)''')
        conn.execute('CREATE TABLE detector_values (asset_id text PRIMARY KEY, passed boolean)')
        conn.execute('CREATE TABLE asset_throughput (chart_id uuid, asset_id text, state text)')
        conn.execute('''CREATE TABLE asset_freshness
            (chart_id uuid, asset_id text, partition_key text, freshness_state text, reasons jsonb)''')
        conn.execute('''CREATE TABLE asset_provenance_receipts
            (asset_id text, chart_id uuid, build_id uuid, partition_key text, code_digest text,
             config_digest text, upstream_digest text, partition_digest text, output_digest text,
             upstream_receipts jsonb, receipt_state text, unknown_reasons jsonb)''')
        args = spec()
        plan = rehearsal.prepare_rehearsal(**args)
        candidate = open_candidate(conn, **{key: args[key] for key in
            ('chart_id', 'generation', 'build_id', 'model_digest', 'rule_registry_version', 'conventions')})
        manifest = dict(version='nirmana-run-manifest/v1', **{
            key: plan['request'][key] for key in ('chart_id', 'scope', 'scope_target', 'action')},
            waves=WAVES, assets=[dict(asset_id=asset, scope='per_chart', depends_on=[],
                natural_key_partition='chart_id', has_cowriters=False, expected_code_digest=CODE)
                for asset in ASSETS])
        digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        conn.execute('INSERT INTO build_runs VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                     (args['build_id'], args['chart_id'], 'asset_set', ','.join(ASSETS), 'rebuild',
                      'completed', Jsonb(ASSETS), Jsonb(manifest), digest))
        for level, wave in enumerate(WAVES):
            for asset in wave:
                conn.execute('INSERT INTO build_run_assets VALUES (%s,%s,%s,%s,%s)',
                    (args['build_id'], asset, 'complete', f'2026-10-01 {level:02}:00Z',
                     f'2026-10-01 {level:02}:30Z'))
                conn.execute('INSERT INTO detector_values VALUES (%s,true)', (asset,))
                # Detector truth comes from a stored row, not a callback mock.
                detector = "SELECT passed FROM detector_values WHERE asset_id = '" + asset + "'"
                conn.execute('INSERT INTO asset_registry VALUES (%s,%s,%s,NULL)', (asset, 'data', detector))
                conn.execute('INSERT INTO asset_throughput VALUES (%s,%s,%s)', (args['chart_id'], asset, 'lit'))
                conn.execute('INSERT INTO asset_freshness VALUES (%s,%s,%s,%s,%s)',
                             (args['chart_id'], asset, 'chart_id', 'fresh', Jsonb([])))
                conn.execute('INSERT INTO asset_provenance_receipts VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    (asset, args['chart_id'], args['build_id'], 'chart_id', CODE, 'config', 'upstream',
                     'partition', 'output', Jsonb([]), 'proven', Jsonb([])))
        for grains in args['grains_by_asset'].values():
            for grain in grains:
                attest_grain(conn, candidate, grain_key=grain, result_state='zero_rows', input_vector='fixture-input')
        conn.commit()
        yield conn, plan, candidate
        # Tables are in this test's guarded, isolated DB, not a lane or production.
        conn.execute('DROP TABLE build_runs, build_run_assets, asset_registry, detector_values, '
                     'asset_throughput, asset_freshness, asset_provenance_receipts, kala_layer_head, kala_layer_verification, '
                     'kala_layer_candidate_grain, kala_layer_candidate CASCADE')
        conn.commit()


def audit(stored):
    conn, plan, _ = stored
    return rehearsal.audit_rehearsal(conn, plan, allow_fixture=True)


def test_zero_row_grains_are_complete_but_unverified_candidate_is_not_published(stored):
    report = audit(stored)
    assert report['status'] == 'awaiting_verification'
    assert len(report['lineage']) == 20
    assert report['operational_rehearsal_passed'] is None
    assert report['published_generation'] is None
    # SR-W56-S3: the receipt discloses the named L1 mudda boundary overlaps; this fixture has no settled dasha read, so it says so
    # (a typed null with its refusal code) rather than reporting a count of zero
    assert report['mudda_boundary_overlap']['status'] == 'not_readable' and report['mudda_boundary_overlap']['reason']


@pytest.mark.parametrize('mutation', ['missing_asset', 'error', 'stale', 'missing_detector',
    'false_detector', 'null_detector', 'old_receipt', 'unknown_receipt', 'wrong_code',
    'missing_grain', 'failed_grain', 'wrong_candidate', 'changed_pins', 'incomplete_run',
    'bad_manifest', 'wrong_order', 'overlap', 'stale_freshness', 'missing_freshness'])
def test_no_green_from_incomplete_or_stale_evidence(stored, mutation):
    conn, plan, candidate = stored
    asset = 'ka_taranga'
    params = (asset,)
    queries = {
        'missing_asset': 'DELETE FROM build_run_assets WHERE asset_id=%s',
        'error': "UPDATE build_run_assets SET state='error' WHERE asset_id=%s",
        'stale': "UPDATE asset_throughput SET state='stale' WHERE asset_id=%s",
        'missing_detector': 'UPDATE asset_registry SET integrity_check_sql=NULL WHERE asset_id=%s',
        'false_detector': 'UPDATE detector_values SET passed=false WHERE asset_id=%s',
        'null_detector': 'UPDATE detector_values SET passed=NULL WHERE asset_id=%s',
        'old_receipt': 'UPDATE asset_provenance_receipts SET build_id=NULL WHERE asset_id=%s',
        'unknown_receipt': "UPDATE asset_provenance_receipts SET unknown_reasons='[\"missing_input\"]' WHERE asset_id=%s",
        'wrong_code': "UPDATE asset_provenance_receipts SET code_digest='other-code' WHERE asset_id=%s",
        'missing_grain': "DELETE FROM kala_layer_candidate_grain WHERE grain_key='ka_taranga:fixture'",
        'failed_grain': "UPDATE kala_layer_candidate_grain SET result_state='failed' WHERE grain_key='ka_taranga:fixture'",
        'wrong_candidate': "UPDATE kala_layer_candidate SET build_id='00000000-0000-0000-0000-000000000001'",
        'changed_pins': "UPDATE kala_layer_candidate SET conventions='{}'",
        'incomplete_run': "UPDATE build_runs SET state='running'",
        'bad_manifest': "UPDATE build_runs SET plan_manifest_digest=repeat('0',64)",
        'wrong_order': "UPDATE build_run_assets SET started_at='2026-10-01 00:00Z' WHERE asset_id='ka_avadhi'",
        'overlap': "UPDATE build_run_assets SET ended_at='2026-10-01 08:30Z' WHERE asset_id='ka_kshetra'",
        'stale_freshness': "UPDATE asset_freshness SET freshness_state='stale' WHERE asset_id=%s",
        'missing_freshness': 'DELETE FROM asset_freshness WHERE asset_id=%s',
    }
    query = queries[mutation]
    conn.execute(query, params if '%s' in query else None)
    conn.commit()
    report = audit(stored)
    assert report['status'] == 'incomplete', report
    assert report['failures'], mutation
    assert report['operational_rehearsal_passed'] is None
    assert conn.execute('SELECT count(*) FROM kala_layer_head').fetchone() == (0,)
    conn.commit()


def test_audit_runs_detectors_read_only_and_never_moves_the_head(stored):
    conn, _, _ = stored
    conn.execute("UPDATE asset_registry SET integrity_check_sql='DELETE FROM detector_values RETURNING true' "
                 "WHERE asset_id='ka_taranga'")
    conn.commit()
    report = audit(stored)
    assert report['status'] == 'incomplete'
    assert conn.execute('SELECT count(*) FROM detector_values').fetchone() == (20,)
    assert conn.execute('SELECT count(*) FROM kala_layer_head').fetchone() == (0,)
    conn.commit()


def test_published_status_requires_real_cas_and_matching_verifier_receipt(stored, monkeypatch):
    import services.kala_core.manifest as manifest_module
    conn, plan, candidate = stored
    grains = [grain for values in plan['grains_by_asset'].values() for grain in values]
    # Hand-derived fixture input digest, not the production digest helper.
    digest = hashlib.sha256(json.dumps([(grain, 'fixture-input') for grain in sorted(grains)],
                                      separators=(',', ':')).encode()).hexdigest()
    conn.execute('INSERT INTO kala_layer_verification VALUES (%s,%s,%s,%s,%s,now())',
                 (candidate.chart_id, candidate.generation, 'verifier_principal', 'accepted',
                  Jsonb({'input_digest': digest})))
    conn.commit()
    assert audit(stored)['status'] == 'awaiting_publication'
    assert conn.execute('SELECT count(*) FROM kala_layer_head').fetchone() == (0,)
    conn.commit()
    original = manifest_module.publish_head
    calls = []
    def observed(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(manifest_module, 'publish_head', observed)
    publish_candidate(conn, candidate, expected_grains=grains)
    conn.commit()
    report = audit(stored)
    assert calls == [True]
    assert report['status'] == 'fixture_passed'
    assert report['published_generation'] == candidate.generation
    assert report['publication_path_verified'] is None  # readback cannot prove historical code execution
    assert report['operational_rehearsal_passed'] is None
    conn.execute("UPDATE kala_layer_verification SET detail='{}'")
    conn.commit()
    assert audit(stored)['status'] == 'incomplete'


def test_fixture_cannot_masquerade_as_lane_rehearsal(stored):
    conn, plan, _ = stored
    with pytest.raises(ValueError, match='lane'):
        rehearsal.audit_rehearsal(conn, plan)
    conn.rollback()


def test_prepared_contract_tampering_is_refused(stored):
    conn, plan, _ = stored
    plan = deepcopy(plan)
    plan['request']['clear_before'] = True
    with pytest.raises(ValueError):
        rehearsal.audit_rehearsal(conn, plan, allow_fixture=True)
    conn.rollback()


def test_existing_dict_row_caller_gets_same_detector_results(stored):
    conn, _, _ = stored
    conn.row_factory = dict_row
    assert audit(stored)['status'] == 'awaiting_verification'


def test_service_probe_uses_real_stored_contract_and_requires_current_lineage(stored):
    conn, _, _ = stored
    migration = Path(__file__).resolve().parents[5] / 'migrations/1377_k7_4_tulana_pareto_health_probe.sql'
    conn.execute(migration.read_text())
    conn.execute("UPDATE asset_registry SET asset_kind='service' WHERE asset_id='ka_tulana'")
    conn.execute("UPDATE asset_throughput SET state='service_ok' WHERE asset_id='ka_tulana'")
    conn.commit()
    report = audit(stored)
    assert report['status'] == 'awaiting_verification', report
    detector = next(row['detector'] for row in report['lineage'] if row['asset_id'] == 'ka_tulana')
    assert detector['passed'] is True
    assert any(check['check'] == 'forensic_front_and_order' and check['passed']
               for check in detector['measured']['checks'])
    conn.execute("DELETE FROM asset_provenance_receipts WHERE asset_id='ka_tulana'")
    conn.commit()
    assert audit(stored)['status'] == 'incomplete'


def test_global_service_evidence_uses_frozen_execution_scope(stored):
    conn, _, _ = stored
    conn.execute("UPDATE asset_registry SET asset_kind='service' WHERE asset_id='ka_tulana'")
    migration = Path(__file__).resolve().parents[5] / 'migrations/1377_k7_4_tulana_pareto_health_probe.sql'
    conn.execute(migration.read_text())
    conn.execute("UPDATE asset_throughput SET chart_id=NULL WHERE asset_id='ka_tulana'")
    conn.execute("UPDATE asset_provenance_receipts SET chart_id=NULL WHERE asset_id='ka_tulana'")
    manifest = conn.execute('SELECT plan_manifest FROM build_runs').fetchone()[0]
    next(asset for asset in manifest['assets'] if asset['asset_id'] == 'ka_tulana')['scope'] = 'global'
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    conn.execute('UPDATE build_runs SET plan_manifest=%s, plan_manifest_digest=%s', (Jsonb(manifest), digest))
    conn.commit()
    assert audit(stored)['status'] == 'awaiting_verification'


@pytest.mark.parametrize('host,port,name', [
    ('db.example.invalid', 55433, 'ky_k9_1'), ('127.0.0.1', 5432, 'ky_k9_1'),
    ('127.0.0.1', 55433, 'madhav'), ('127.0.0.1', 55433, 'ky_other'),
])
def test_external_or_wrong_lane_endpoint_is_refused_before_any_query(host, port, name):
    conn = SimpleNamespace(info=SimpleNamespace(host=host, port=port, dbname=name,
                          transaction_status=psycopg.pq.TransactionStatus.IDLE))
    with pytest.raises(ValueError):
        rehearsal.audit_rehearsal(conn, rehearsal.prepare_rehearsal(**spec()))


def test_audit_does_not_take_ownership_of_caller_transaction(stored):
    conn, plan, _ = stored
    conn.execute('SELECT 1')
    with pytest.raises(ValueError, match='idle'):
        rehearsal.audit_rehearsal(conn, plan, allow_fixture=True)
    assert conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS
    conn.rollback()


def test_offline_preparation_command_needs_no_database(tmp_path, monkeypatch):
    inputs = tmp_path / 'inputs.json'
    output = tmp_path / 'prepared.json'
    inputs.write_text(json.dumps(spec()))
    def forbidden_connection(*args, **kwargs):
        pytest.fail('offline preparation opened a database connection')
    monkeypatch.setattr(psycopg, 'connect', forbidden_connection)
    monkeypatch.setattr('sys.argv', ['rehearsal', '--prepare', str(inputs), '--output', str(output)])
    assert rehearsal.main() == 0
    prepared = json.loads(output.read_text())
    assert prepared['request']['clear_before'] is False
    assert prepared['request']['scope_target'].split(',') == ASSETS
    assert prepared['operational_rehearsal_passed'] is None
