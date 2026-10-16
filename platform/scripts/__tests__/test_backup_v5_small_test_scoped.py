"""J-2a scoped small-test backup: scope pin, receipt/window policy and refusals. No DB, program or credential is used.

One oracle per production claim (testing standard D-OWNER-TESTS-20261016):
  C1 every table the small test can write is in the reviewed scope (the detector is shown to read false);
  C2 the scope digest the dispatch policy trusts is the reviewed file's;
  C3 trigger write targets are read from the catalog's function bodies (real bodies from the migrations);
  C4 the capture receipt is bound to the reviewed scope, the archive's file hashes and its validity window;
  C5 a backup outside its validity window (or of another scope, or tampered) cannot admit a dispatch;
  C6 scope and receipt generation cannot be crossed (scoped receipt under full, full receipt under scoped);
  C7 the executor can request the scope, and the plan states it without side effects.
The real pg_dump / pg_restore / SQL-measurement claims are in
tests/l3/kala_db/test_p01_smalltest_backup_scoped.py.
"""
import copy
import hashlib
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import smalltest_backup_scope_support as support  # noqa: E402


@pytest.fixture
def backup():
    return importlib.import_module('backup_v5_small_test_job')


@pytest.fixture
def shared():
    return importlib.import_module('v5_small_test_shared')


@pytest.fixture
def scope(backup):
    return json.loads(backup.SCOPE_FILE.read_text())


# ---- C1: the static scope pin ------------------------------------------------------------------------------------

def test_every_write_target_of_the_small_test_code_is_in_the_reviewed_scope(scope):
    assert support.uncovered_targets(support.write_sites(), scope) == []


def test_scope_pin_detector_reads_false_for_a_new_write_target_and_an_undeclared_placeholder(scope, tmp_path):
    planted = tmp_path / 'planted.py'
    planted.write_text('def f(cur, table):\n'
                       '    cur.execute("INSERT INTO public.brand_new_table (a) VALUES (1)")\n'
                       '    cur.execute(f"DELETE FROM {table} WHERE a = 1")\n'
                       '    cur.execute("insert into ka_gochara_sky_event (a) values (1)")   # in scope: not flagged\n'
                       '    # INSERT INTO commented_out (a) VALUES (1)\n')
    bad = support.uncovered_targets(support.write_sites([planted]), scope)
    assert 'brand_new_table' in bad and any('placeholder' in b for b in bad)
    assert 'ka_gochara_sky_event' not in bad and 'commented_out' not in bad


def test_placeholder_write_sites_resolve_to_the_tables_the_scope_declares(scope):
    written = {e['table'].split('.', 1)[1] for e in scope['written']}
    for site in scope['dynamic_sites']:
        resolved = support.resolve_dynamic(site['resolver'])
        assert resolved == sorted(site['tables']) and set(resolved) <= written, site['function']


def test_tables_declared_unreached_are_written_only_by_modules_nothing_in_the_run_imports(scope):
    scanned = support.scanned_files()
    sites = support.write_sites(scanned)
    for entry in scope['unreached']:
        modules = {m for m in ([entry['module']] if 'module' in entry else entry['modules'])}
        found = {s['file'] for s in sites if s['table'] in entry['tables']}
        assert found and found <= modules, (entry['name'], found - modules)
        outside = [f for f in scanned if support.rel(f) not in modules]
        if 'module_names' in entry:
            cluster = {Path(m).stem for m in modules}
            importers = [support.rel(f) for f in outside if support.imported_module_names([f]) & set(entry['module_names'])
                         and Path(f).stem not in cluster]
            assert importers == [], importers
        else:
            names = set(entry['entry_functions'])
            hits = support.references(names, set(entry['aliases']), outside)
            assert hits == [], hits
            # inside the module only the unreached functions themselves may call one another
            closed = names | set(entry['internal_functions'])
            assert support.internal_callers(support.ROOT / entry['module'], closed) <= closed


# ---- C2: the digest the executor-loaded policy pins ---------------------------------------------------------------

def test_policy_pins_the_reviewed_scope_digest_and_the_digest_is_over_the_table_list_only(backup, shared, scope, tmp_path):
    assert shared.SCOPED_BACKUP_SCOPE_SHA256 == backup.load_scope()['sha256']
    prose = copy.deepcopy(scope)
    prose['written'][0]['note'] = 'edited prose and moved line numbers do not invalidate a backup'
    prose['written'][0]['sites'] = []
    longer = copy.deepcopy(scope)
    longer['written'].append({'table': 'public.one_more_table'})
    for name, doc in (('prose', prose), ('longer', longer)):
        (tmp_path / f'{name}.json').write_text(json.dumps(doc))
    assert backup.load_scope(tmp_path / 'prose.json')['sha256'] == backup.load_scope()['sha256']
    assert backup.load_scope(tmp_path / 'longer.json')['sha256'] != backup.load_scope()['sha256']


# ---- C3: trigger write targets (real function bodies from the migrations) ---------------------------------------------

@pytest.mark.parametrize('body,expected', [
    # 586_f152_asset_throughput_state_audit.sql:96-110
    ("BEGIN INSERT INTO asset_throughput_state_audit (chart_id, asset_id) VALUES (NEW.chart_id, NEW.asset_id); RETURN NEW; END;",
     {'public.asset_throughput_state_audit'}),
    # ka_gochara_contact_propagate_precision: UPDATE with an alias
    ("DECLARE restated jsonb; BEGIN UPDATE public.ka_gochara_relationship_record r SET precision = restated WHERE r.chart_id = NEW.chart_id; RETURN NULL; END;",
     {'public.ka_gochara_relationship_record'}),
    # 596_nirmana_provenance_receipts.sql nirmana_invalidate_registry_receipts
    ("BEGIN UPDATE asset_freshness SET freshness_state = 'stale' WHERE asset_id = NEW.asset_id; RETURN NEW; END;", {'public.asset_freshness'}),
    # a guard that only refuses: prose, comments and string literals are not writes
    ("BEGIN -- never update the table\n IF true THEN RAISE EXCEPTION 'refused: delete from x is not allowed, insert into y neither'; END IF; RETURN NULL; END;", set()),
])
def test_trigger_write_targets_come_from_the_function_body(backup, body, expected):
    assert backup.trigger_write_targets(body) == expected


# ---- C4: the capture receipt binds scope, archive file hashes and the validity window ----------------------------------

@pytest.fixture
def receipt_and_archive(backup, tmp_path):
    archive = tmp_path / 'database.dir'
    archive.mkdir()
    (archive / 'toc.dat').write_bytes(b'toc')
    (archive / '1.dat.gz').write_bytes(b'rows')
    manifest = backup.archive_manifest(archive)
    sc = backup.load_scope()
    start = datetime.now(timezone.utc)
    window = timedelta(seconds=backup.scoped_validity_seconds())
    receipt = {'schema': 'ky.smalltest_backup/2', 'status': 'captured', 'label': 'p02_fixture',
               'snapshot': '00000003-0000001B-1', 'source': {'database': 'fixture_source', 'address': '192.0.2.1', 'port': 5432},
               'archive_sha256': manifest['sha256'], 'archive': {'format': 'directory', 'files': manifest['files']},
               'measurements': {'tables': {t: {'rows': 0, 'sha256': 'a' * 64} for t in sc['tables']},
                                'sequences': {'public.s_seq': {'last_value': 1, 'is_called': False}}},
               'measurement_method': backup.SCOPED_MEASUREMENT_METHOD,
               'scope': {'name': sc['name'], 'sha256': sc['sha256'], 'tables': list(sc['tables']), 'closure': [],
                         'sequences': ['public.s_seq'], 'data_bytes': 0},
               'validity': {'not_before': start.isoformat(), 'not_after': (start + window).isoformat(),
                            'seconds': int(window.total_seconds())}}
    return receipt, archive


def test_a_well_formed_scoped_capture_validates(backup, receipt_and_archive):
    receipt, archive = receipt_and_archive
    assert backup.validate_scoped_capture(receipt, archive, 'p02_fixture') == receipt['measurements']


@pytest.mark.parametrize('mutation,reason', [
    ('scope_digest', 'differs from the reviewed scope'),
    ('closure_inconsistent', 'differs from the reviewed scope'),
    ('file_tampered', 'file hashes differ'),
    ('file_added', 'file hashes differ'),
    ('window_shortened', 'validity window'),
    ('window_naive_clock', 'validity window'),
    ('window_missing', 'validity window'),
    ('method_changed', 'measurement method'),
    ('table_not_measured', 'measured relations differ'),
    ('label', 'label differs'),
    ('snapshot_malformed', 'provenance'),
])
def test_scoped_capture_refuses_anything_not_bound_to_the_reviewed_scope_files_and_window(backup, receipt_and_archive, mutation, reason):
    receipt, archive = receipt_and_archive
    if mutation == 'scope_digest':
        receipt['scope']['sha256'] = '0' * 64
    elif mutation == 'closure_inconsistent':
        receipt['scope']['closure'] = ['public.charts']
    elif mutation == 'file_tampered':
        (archive / '1.dat.gz').write_bytes(b'ROWS')
    elif mutation == 'file_added':
        (archive / 'extra.dat.gz').write_bytes(b'x')
    elif mutation == 'window_shortened':
        start = datetime.fromisoformat(receipt['validity']['not_before'])
        receipt['validity'].update(not_after=(start + timedelta(hours=40)).isoformat(), seconds=40 * 3600)
    elif mutation == 'window_naive_clock':
        receipt['validity']['not_before'] = receipt['validity']['not_before'][:19]
    elif mutation == 'window_missing':
        del receipt['validity']
    elif mutation == 'method_changed':
        receipt['measurement_method'] = 'python_sorted_rowjson/1'
    elif mutation == 'table_not_measured':
        receipt['measurements']['tables'].popitem()
    elif mutation == 'label':
        receipt['label'] = 'someone_else'
    elif mutation == 'snapshot_malformed':
        receipt['snapshot'] = 'this is not an exported PostgreSQL snapshot'
    with pytest.raises(backup.BackupRefused, match=reason):
        backup.validate_scoped_capture(receipt, archive, 'p02_fixture')


def test_exclude_args_quote_every_name_so_no_pattern_character_widens_the_exclusion(backup):
    assert backup.exclude_data_args(['public.plain', 'Mixed.t"q?']) == [
        '--exclude-table-data="public"."plain"', '--exclude-table-data="Mixed"."t""q?"']


# ---- C5: the validity window gates the dispatch ------------------------------------------------------------------------

def write_evidence(root, shared, *, label='p02_win', scope_sha=None, started=None, ts=None, tamper=None, proof_schema='ky.smalltest_restore/2'):
    started = started or datetime.now(timezone.utc) - timedelta(minutes=30)
    window = timedelta(seconds=shared.SCOPED_BACKUP_VALIDITY_S)
    folder = root / 'backups' / label
    folder.mkdir(parents=True)
    capture = {'schema': 'ky.smalltest_backup/2', 'label': label, 'archive_sha256': 'b' * 64,
               'scope': {'sha256': scope_sha or shared.SCOPED_BACKUP_SCOPE_SHA256},
               'validity': {'not_before': started.isoformat(), 'not_after': (started + window).isoformat(),
                            'seconds': shared.SCOPED_BACKUP_VALIDITY_S}}
    (folder / 'capture.json').write_text(json.dumps(capture))
    proof = {'schema': proof_schema, 'label': label, 'status': 'verified', 'scoped': True, 'restore_verified': True,
             'backup_taken': True, 'target_removed': True, 'scope_sha256': scope_sha or shared.SCOPED_BACKUP_SCOPE_SHA256,
             'archive_sha256': 'b' * 64, 'capture_sha256': hashlib.sha256((folder / 'capture.json').read_bytes()).hexdigest(),
             'validity': capture['validity'], 'ts': (ts or started + timedelta(minutes=10)).isoformat()}
    if tamper:
        proof.update(tamper)
    (folder / 'restore.json').write_text(json.dumps(proof))
    digest = hashlib.sha256((folder / 'restore.json').read_bytes()).hexdigest()
    return {'backup_label': label, 'backup_restore_sha256': digest}


def test_dispatch_naming_a_valid_scoped_backup_inside_its_window_is_admitted(shared, tmp_path):
    req = write_evidence(tmp_path, shared)
    shared.scoped_backup_problem(req, tmp_path)


def test_dispatch_after_the_window_requires_a_fresh_backup(shared, tmp_path):
    req = write_evidence(tmp_path, shared, started=datetime.now(timezone.utc) - timedelta(seconds=shared.SCOPED_BACKUP_VALIDITY_S + 60))
    with pytest.raises(shared.Refused, match='outside its validity window'):
        shared.scoped_backup_problem(req, tmp_path)


@pytest.mark.parametrize('fault,reason', [
    ('other_scope', 'scope other than the reviewed'),
    ('proof_edited_after_review', 'digest mismatch'),
    ('proof_not_from_the_restore', 'not a verified proof'),
    ('capture_swapped', 'does not match its capture|digest mismatch'),
    ('proof_before_window', 'outside its validity window'),
])
def test_dispatch_refuses_a_scoped_backup_that_is_not_the_reviewed_scope_or_not_the_evidence_reviewed(shared, tmp_path, fault, reason):
    if fault == 'other_scope':
        req = write_evidence(tmp_path, shared, scope_sha='0' * 64)
    elif fault == 'proof_edited_after_review':
        req = write_evidence(tmp_path, shared)
        path = tmp_path / 'backups' / req['backup_label'] / 'restore.json'
        path.write_text(path.read_text().replace('"verified"', '"verified" '))
    elif fault == 'proof_not_from_the_restore':
        req = write_evidence(tmp_path, shared, tamper={'target_removed': False})
    elif fault == 'capture_swapped':
        req = write_evidence(tmp_path, shared)
        (tmp_path / 'backups' / req['backup_label'] / 'capture.json').write_text('{}')
    else:
        started = datetime.now(timezone.utc) - timedelta(minutes=30)
        req = write_evidence(tmp_path, shared, started=started, ts=started - timedelta(minutes=1))
    with pytest.raises(shared.Refused, match=reason):
        shared.scoped_backup_problem(req, tmp_path)


def test_request_policy_applies_the_window_to_a_dispatch_that_names_a_backup(shared, tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(shared, 'absence_evidence', lambda req, root: None)
    monkeypatch.setattr(shared, 'scoped_backup_problem', lambda req, root: seen.append(req.get('backup_label')) or (_ for _ in ()).throw(
        shared.Refused('stale')))
    req = {'kind': 'smalltest_dispatch', 'args': {'run': 'one_class_full', 'classes': 'marriage'}, 'backup_label': 'p02_win'}
    assert shared.smalltest_request_problem(req, tmp_path) == 'stale'
    assert seen == ['p02_win']
    seen.clear()
    assert shared.smalltest_request_problem(dict(req, kind='smalltest_dispatch_dryrun'), tmp_path) is None and not seen


def test_a_dispatch_that_names_no_backup_label_or_the_full_backup_proof_is_unchanged(shared, tmp_path):
    shared.scoped_backup_problem({}, tmp_path)
    req = write_evidence(tmp_path, shared, proof_schema='ky.smalltest_restore/1', started=datetime(2020, 1, 1, tzinfo=timezone.utc))
    shared.scoped_backup_problem(req, tmp_path)


# ---- C6/C7: scope selection, cross-refusal and the executor table ----------------------------------------------------------

def test_full_receipt_cannot_be_restored_as_scoped_and_scoped_receipt_cannot_be_restored_as_full(backup, tmp_path, monkeypatch):
    import psycopg
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **k: pytest.fail('crossed scope reached libpq'))
    for schema, requested in (('ky.smalltest_backup/1', 'small_test'), ('ky.smalltest_backup/2', 'full')):
        folder = tmp_path / requested
        folder.mkdir()
        (folder / 'capture.json').write_text(json.dumps({'schema': schema, 'status': 'captured', 'label': 'p02_fixture'}))
        with pytest.raises(backup.BackupRefused, match='capture scope differs from the requested scope'):
            backup.restore_verify(folder, 'p02_fixture', requested)
        assert not (folder / 'restore.json').exists()


def test_scoped_plan_states_scope_digest_and_window_and_touches_nothing(backup, shared, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    assert backup.main(['--operation', 'snapshot', '--label', 'p02_plan', '--scope', 'small_test', '--dry-run']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['scope'] == 'small_test' and plan['scope_sha256'] == shared.SCOPED_BACKUP_SCOPE_SHA256
    assert plan['validity_seconds'] == shared.SCOPED_BACKUP_VALIDITY_S and plan['backup_taken'] is None
    assert list(tmp_path.iterdir()) == []
    assert backup.main(['--operation', 'snapshot', '--label', 'p02_plan', '--dry-run']) == 0
    assert 'scope' not in json.loads(capsys.readouterr().out)


def test_the_executor_table_lets_a_backup_request_carry_the_scope_and_nothing_else_new():
    ops = json.loads((support.ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json').read_text())['ops']
    for kind in ('backup_snapshot', 'backup_restore_verify'):
        assert ops[kind]['allowed_args'] == ['label', 'scope'], kind
        assert ops[kind]['fixed_args'][-1] == '--execute'
