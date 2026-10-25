"""J-2a scoped small-test backup: scope pin, receipt/window policy and refusals. No DB, program or credential is used.

One oracle per production claim (testing standard D-OWNER-TESTS-20261016):
  C1 every table the small test can write is in the reviewed scope (the detector is shown to read false);
  C2 the scope digest the dispatch policy trusts is the reviewed file's;
  C3 trigger write targets are read from the catalog's function bodies (real bodies from the migrations);
  C4 the capture receipt is bound to the reviewed scope, the archive's file hashes and its validity window;
  C5 a scoped backup admits a dispatch exactly while its scoped-content digest is unchanged (SR-BACKUP-VALIDITY-A8: no
     clock; another scope, a tampered record or a changed row cannot admit);
  C6 scope and receipt generation cannot be crossed (scoped receipt under full, full receipt under scoped);
  C7 the executor can request the scope, and the plan states it without side effects.
The real pg_dump / pg_restore / SQL-measurement claims are in
tests/l3/kala_db/test_p01_smalltest_backup_scoped.py.
"""
import ast
import copy
import hashlib
import importlib
import json
import re
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
    measured = {'tables': {t: {'rows': 0, 'sha256': 'a' * 64} for t in sc['tables']},
                'sequences': {'public.s_seq': {'last_value': 1, 'is_called': False}}}
    receipt = {'schema': 'ky.smalltest_backup/2', 'status': 'captured', 'label': 'p02_fixture',
               'snapshot': '00000003-0000001B-1', 'source': {'database': 'fixture_source', 'address': '192.0.2.1', 'port': 5432},
               'archive_sha256': manifest['sha256'], 'archive': {'format': 'directory', 'files': manifest['files']},
               'measurements': measured, 'scoped_content_digest': backup.shared_policy.scoped_content_digest(measured),
               'measurement_method': backup.SCOPED_MEASUREMENT_METHOD,
               'scope': {'name': sc['name'], 'sha256': sc['sha256'], 'tables': list(sc['tables']), 'closure': [],
                         'sequences': ['public.s_seq'], 'data_bytes': 0, 'dump_excludes': []},
               'validity': {'not_before': start.isoformat(), 'basis': 'scoped_content_digest_unchanged'}}
    return receipt, archive


def test_a_well_formed_scoped_capture_validates(backup, receipt_and_archive):
    receipt, archive = receipt_and_archive
    assert backup.validate_scoped_capture(receipt, archive, 'p02_fixture') == receipt['measurements']


@pytest.mark.parametrize('mutation,reason', [
    ('scope_digest', 'differs from the reviewed scope'),
    ('closure_inconsistent', 'differs from the reviewed scope'),
    ('file_tampered', 'file hashes differ'),
    ('file_added', 'file hashes differ'),
    ('window_naive_clock', 'capture instant'),
    ('window_missing', 'capture instant'),
    ('digest_tampered', 'scoped-content digest differs'),
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
    elif mutation == 'digest_tampered':
        receipt['measurements']['tables'][next(iter(receipt['measurements']['tables']))]['rows'] = 7
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


def test_an_older_capture_with_an_expired_not_after_still_validates_and_the_field_is_never_a_gate(backup, receipt_and_archive):
    """SR-BACKUP-VALIDITY-A8: not_after / seconds from the 4 h era stay readable; an expired one does not refuse."""
    receipt, archive = receipt_and_archive
    start = datetime.fromisoformat(receipt['validity']['not_before']) - timedelta(days=3)
    receipt['validity'] = {'not_before': start.isoformat(), 'not_after': (start + timedelta(hours=4)).isoformat(), 'seconds': 4 * 3600}
    del receipt['scoped_content_digest']                                    # captures of that era carry no separate digest
    assert backup.validate_scoped_capture(receipt, archive, 'p02_fixture') == receipt['measurements']


def test_dump_names_exactly_the_data_set_one_quoted_table_each_and_nothing_else(backup):
    """SR-J2A-BACKUP-POSITIVE: an explicit -t per relation (no pattern character widens it); no schema-wide selector."""
    args = backup.dump_table_args(['public.plain', 'Mixed.t"q?'], [{'table': 'public.skip', 'owner': 'someone'}])
    assert args == ['--strict-names', '--table="public"."plain"', '--table="Mixed"."t""q?"', '--exclude-table="public"."skip"']
    assert not any(a.startswith(('--schema', '-n', '--exclude-table-data')) for a in args)


def _bundle(tmp_path, backup, monkeypatch, body):
    """A synthetic stand-in for the governed L1 bundle's schema.sql, pinned the way the real one is."""
    path = tmp_path / 'run/canonical_l1/b/schema.sql'
    path.parent.mkdir(parents=True)
    path.write_bytes(body)
    monkeypatch.setattr(backup, 'SCOPED_RESTORE_BASE_PATH', 'run/canonical_l1/b/schema.sql')
    monkeypatch.setattr(backup, 'SCOPED_RESTORE_BASE_SHA256', hashlib.sha256(body).hexdigest())
    return tmp_path


def test_restore_base_is_the_hash_checked_governed_bundle_bootstrapped_the_way_its_own_restore_ran(backup, tmp_path, monkeypatch):
    body = b"\\restrict k\nSET x = 1;\n\nCREATE SCHEMA public;\nCREATE TABLE public.t (id int);\n\\unrestrict k\n"
    root = _bundle(tmp_path, backup, monkeypatch, body)
    text, identity = backup.restore_base_sql(root)
    assert '\\restrict' not in text and '\\unrestrict' not in text                  # psql-only guard lines are not SQL
    order = [text.index(m) for m in ('DROP SCHEMA public;', 'CREATE SCHEMA public;', 'CREATE EXTENSION IF NOT EXISTS "vector"',
                                     'CREATE TABLE public.t')]
    assert order == sorted(order)                                                    # schema, then extensions, then the rest
    assert identity == {'bundle': 'run/canonical_l1/b/schema.sql', 'sha256': hashlib.sha256(body).hexdigest(), 'migrations': []}
    (root / 'run/canonical_l1/b/schema.sql').write_bytes(body + b'-- drift\n')
    with pytest.raises(backup.BackupRefused, match='differs from the governed L1 bundle'):
        backup.restore_base_sql(root)


def test_restore_base_migrations_are_applied_in_order_and_only_as_reviewed(backup, tmp_path, monkeypatch):
    root = _bundle(tmp_path, backup, monkeypatch, b"-- x\nCREATE SCHEMA public;\n")
    migrations = tmp_path / 'migrations'
    migrations.mkdir()
    (migrations / '1_a.sql').write_text('SELECT 1;')
    (migrations / '2_b.sql').write_text('SELECT 2;')
    monkeypatch.setattr(backup, 'MIGRATIONS_DIR', migrations)
    pins = tuple((n, hashlib.sha256((migrations / n).read_bytes()).hexdigest()) for n in ('1_a.sql', '2_b.sql'))
    text, identity = backup.restore_base_sql(root, pins)
    assert text.index('SELECT 1;') < text.index('SELECT 2;') and [m['file'] for m in identity['migrations']] == ['1_a.sql', '2_b.sql']
    (migrations / '2_b.sql').write_text('SELECT 3;')
    with pytest.raises(backup.BackupRefused, match='migration is missing or differs'):
        backup.restore_base_sql(root, pins)


# ---- SR-J2A-RESTORE-BASE: the migrations on top of the bundle are derived from the ledger, never pinned ------------------

def _ledger(backup, tmp_path, monkeypatch, files):
    """files: [(ledger id, name, applied hour relative to the cut, SQL text)] -> (ledger entries, migrations dir)."""
    directory = tmp_path / 'migrations'
    directory.mkdir()
    monkeypatch.setattr(backup, 'SCOPED_RESTORE_BASE_CUT', '2026-10-16T17:10:23+00:00')
    cut = datetime.fromisoformat(backup.SCOPED_RESTORE_BASE_CUT)
    rows = []
    for ident, name, hours, text in files:
        (directory / name).write_text(text)
        rows.append((ident, name, cut + timedelta(hours=hours), hashlib.sha256(text.encode()).hexdigest()))
    return backup.ledger_entries(rows), directory


def test_restore_migrations_are_those_applied_after_the_bundle_that_mention_a_scope_table_and_create_a_schema_object_in_ledger_order(backup, tmp_path, monkeypatch):
    """Claim: base = bundle + every ledger migration applied after the bundle that touches a scope table AND creates something an archived
    table can depend on (the 1394 shape: a function and a trigger on kala_gochara_publication). Earlier ones are already in the bundle;
    unrelated ones are not needed; a pure data-fix on a scope table (the 1395 shape) is not carried; order is the ledger's, not the file name's."""
    ledger, directory = _ledger(backup, tmp_path, monkeypatch, [
        (9, '1394_late.sql', 17, 'CREATE TRIGGER t BEFORE UPDATE ON public.kala_gochara_publication EXECUTE FUNCTION f();'),
        (4, '1235_before_the_bundle.sql', -3, 'ALTER TABLE public.kala_gochara_publication ADD COLUMN x int;'),
        (7, '1393_unrelated.sql', 5, 'CREATE FUNCTION g() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$; -- no scope table'),
        (8, '1500_between.sql', 6, 'CREATE OR REPLACE FUNCTION public.h() RETURNS int LANGUAGE sql AS $$ SELECT count(*)::int FROM public.asset_throughput $$;'),
        (10, '1501_datafix.sql', 18, "UPDATE public.asset_throughput SET state = state; -- CREATE FUNCTION in a comment\n/* CREATE TABLE x (); */"),
        (11, '1502_alter_only.sql', 19, 'ALTER TABLE public.asset_throughput ADD COLUMN y int; GRANT SELECT ON public.asset_throughput TO someone;'),
        (12, '1503_temp_table.sql', 20, 'CREATE TEMP TABLE scratch AS SELECT * FROM public.asset_throughput;')])
    chosen = backup.derive_restore_migrations(ledger, ['public.kala_gochara_publication', 'public.asset_throughput'], directory)
    assert [name for name, _ in chosen] == ['1500_between.sql', '1394_late.sql']
    assert chosen[0][1] == hashlib.sha256((directory / '1500_between.sql').read_bytes()).hexdigest()


def test_a_skipped_post_bundle_migration_is_still_hash_checked(backup, tmp_path, monkeypatch):
    """Not selecting a file does not mean not reading it: the repository must still reproduce exactly what production ran."""
    ledger, directory = _ledger(backup, tmp_path, monkeypatch, [(1, '1395_datafix.sql', 17, 'UPDATE public.t SET x = 1;')])
    (directory / '1395_datafix.sql').write_text('UPDATE public.t SET x = 2;')
    with pytest.raises(backup.BackupRefused, match='differs from the file production applied'):
        backup.derive_restore_migrations(ledger, ['public.t'], directory)


@pytest.mark.parametrize('fault,reason', [('absent', 'missing from the repository'), ('edited', 'differs from the file production applied')])
def test_a_ledger_migration_the_repository_cannot_reproduce_exactly_refuses_the_base(backup, tmp_path, monkeypatch, fault, reason):
    ledger, directory = _ledger(backup, tmp_path, monkeypatch, [(1, '1394_late.sql', 17, 'ALTER TABLE public.t ADD COLUMN x int;')])
    if fault == 'absent':
        (directory / '1394_late.sql').unlink()
    else:
        (directory / '1394_late.sql').write_text('ALTER TABLE public.t ADD COLUMN x bigint;')
    with pytest.raises(backup.BackupRefused, match=reason):
        backup.derive_restore_migrations(ledger, ['public.t'], directory)


# ---- C5: the validity window gates the dispatch ------------------------------------------------------------------------

MEASURED = {'tables': {'public.a': {'rows': 3, 'sha256': 'a' * 64}, 'public.b': {'rows': 0, 'sha256': 'b' * 64}},
            'sequences': {'public.a_id_seq': {'last_value': 3, 'is_called': True}}}


def now_measure(changed=None):
    """What a fresh read-only measurement of the recorded relations returns: the same content, or one changed table."""
    seen = []

    def measure(tables, sequences, dsn=None, presence_only=None):
        seen.append((tables, sequences))
        out = json.loads(json.dumps(MEASURED))
        if changed:
            out['tables'][changed]['sha256'] = 'c' * 64                  # one row of one table differs
        return out
    measure.seen = seen
    return measure


def write_evidence(root, shared, *, label='p02_win', scope_sha=None, started=None, ts=None, tamper=None, proof_schema='ky.smalltest_restore/2',
                   legacy_window=False, proof_measured=None, capture_digest=None):
    started = started or datetime.now(timezone.utc) - timedelta(minutes=30)
    folder = root / 'backups' / label
    folder.mkdir(parents=True)
    validity = {'not_before': started.isoformat(), 'basis': 'scoped_content_digest_unchanged'}
    if legacy_window:                                                    # the 4 h era: a window that has long expired
        validity = {'not_before': started.isoformat(), 'not_after': (started + timedelta(hours=4)).isoformat(), 'seconds': 4 * 3600}
    capture = {'schema': 'ky.smalltest_backup/2', 'label': label, 'archive_sha256': 'b' * 64,
               'scope': {'sha256': scope_sha or shared.SCOPED_BACKUP_SCOPE_SHA256},
               'measurements': MEASURED, 'measurement_method': shared.SCOPED_MEASUREMENT_METHOD, 'validity': validity}
    if not legacy_window:
        capture['scoped_content_digest'] = capture_digest or shared.scoped_content_digest(MEASURED)
    (folder / 'capture.json').write_text(json.dumps(capture))
    proof = {'schema': proof_schema, 'label': label, 'status': 'verified', 'scoped': True, 'restore_verified': True,
             'backup_taken': True, 'target_removed': True, 'scope_sha256': scope_sha or shared.SCOPED_BACKUP_SCOPE_SHA256,
             'archive_sha256': 'b' * 64, 'capture_sha256': hashlib.sha256((folder / 'capture.json').read_bytes()).hexdigest(),
             'measurements': proof_measured or MEASURED, 'validity': validity, 'ts': (ts or started + timedelta(minutes=10)).isoformat()}
    if tamper:
        proof.update(tamper)
    (folder / 'restore.json').write_text(json.dumps(proof))
    digest = hashlib.sha256((folder / 'restore.json').read_bytes()).hexdigest()
    return {'backup_label': label, 'backup_restore_sha256': digest}


def test_dispatch_naming_a_valid_scoped_backup_with_unchanged_content_is_admitted(shared, tmp_path):
    req = write_evidence(tmp_path, shared)
    measure = now_measure()
    shared.scoped_backup_problem(req, tmp_path, measure=measure)
    assert measure.seen == [(['public.a', 'public.b'], ['public.a_id_seq'])]       # the recorded relations, nothing else


@pytest.mark.parametrize('legacy_window', [False, True])
def test_an_unchanged_scope_reads_valid_hours_and_days_later(shared, tmp_path, legacy_window):
    """SR-BACKUP-VALIDITY-A8: no clock. Captured nine hours ago (past the old 4 h) and read three days later, with the
    expired not_after of an older capture left in place, the backup is still valid while the content digest is equal."""
    started = datetime.now(timezone.utc) - timedelta(hours=9)
    req = write_evidence(tmp_path, shared, started=started, legacy_window=legacy_window)
    shared.scoped_backup_problem(req, tmp_path, now=started + timedelta(hours=9), measure=now_measure())
    shared.scoped_backup_problem(req, tmp_path, now=started + timedelta(days=3), measure=now_measure())


def test_one_changed_row_in_scope_makes_the_backup_invalid(shared, tmp_path):
    req = write_evidence(tmp_path, shared)
    with pytest.raises(shared.Refused, match='content has changed since the backup'):
        shared.scoped_backup_problem(req, tmp_path, measure=now_measure(changed='public.b'))


def test_a_backup_that_cannot_be_measured_now_is_refused_never_assumed_valid(shared, tmp_path):
    req = write_evidence(tmp_path, shared)

    def broken(tables, sequences):
        raise RuntimeError('permission denied for table b')
    with pytest.raises(shared.Refused, match='could not be measured now'):
        shared.scoped_backup_problem(req, tmp_path, measure=broken)


def test_executor_admission_without_a_database_checks_the_recorded_evidence_and_leaves_the_fresh_read_to_the_dispatch(shared, tmp_path):
    shared.scoped_backup_problem(write_evidence(tmp_path / 'ok', shared), tmp_path / 'ok')
    bad = write_evidence(tmp_path / 'bad', shared, proof_measured={'tables': MEASURED['tables'], 'sequences': {}})
    with pytest.raises(shared.Refused, match='measured content other than the capture recorded'):
        shared.scoped_backup_problem(bad, tmp_path / 'bad')


def test_a_capture_whose_digest_is_not_its_measurements_digest_is_refused(shared, tmp_path):
    req = write_evidence(tmp_path, shared, capture_digest='0' * 64)
    with pytest.raises(shared.Refused, match='digest differs from its recorded measurements'):
        shared.scoped_backup_problem(req, tmp_path, measure=now_measure())


@pytest.mark.parametrize('fault,reason', [
    ('other_scope', 'scope other than the reviewed'),
    ('proof_edited_after_review', 'digest mismatch'),
    ('proof_not_from_the_restore', 'not a verified proof'),
    ('capture_swapped', 'does not match its capture|digest mismatch'),
    ('proof_before_window', 'predates its capture'),
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
    monkeypatch.setattr(shared, 'scoped_backup_problem', lambda req, root, **kw: seen.append((req.get('backup_label'), kw.get('measure'))) or (_ for _ in ()).throw(
        shared.Refused('stale')))
    req = {'kind': 'smalltest_dispatch', 'args': {'run': 'one_class_full', 'classes': 'marriage'}, 'backup_label': 'p02_win'}
    assert shared.smalltest_request_problem(req, tmp_path) == 'stale'
    assert shared.smalltest_request_problem(req, tmp_path, measure=now_measure) == 'stale'
    assert seen == [('p02_win', None), ('p02_win', now_measure)]
    seen.clear()
    assert shared.smalltest_request_problem(dict(req, kind='smalltest_dispatch_dryrun'), tmp_path) is None and not seen


def write_full_evidence(root, shared, *, label='p02_full', captured=None):
    """A full-form (/1) backup + restore proof pair, as backup_v5_small_test_job.py writes them."""
    captured = captured or datetime.now(timezone.utc) - timedelta(minutes=30)
    folder = root / 'backups' / label
    folder.mkdir(parents=True)
    capture = {'schema': 'ky.smalltest_backup/1', 'label': label, 'status': 'captured', 'archive_sha256': 'c' * 64,
               'ts': captured.isoformat()}
    (folder / 'capture.json').write_text(json.dumps(capture))
    proof = {'schema': 'ky.smalltest_restore/1', 'label': label, 'status': 'verified', 'archive_sha256': 'c' * 64,
             'capture_sha256': hashlib.sha256((folder / 'capture.json').read_bytes()).hexdigest(), 'target_removed': True,
             'backup_taken': True, 'restore_verified': True, 'ts': (captured + timedelta(minutes=10)).isoformat()}
    (folder / 'restore.json').write_text(json.dumps(proof))
    return {'backup_label': label, 'backup_restore_sha256': hashlib.sha256((folder / 'restore.json').read_bytes()).hexdigest()}


# SR-J2A-BACKUP-SCOPE condition 4 ("dispatch outside the window requires a fresh step 10"), review B1: the window is not
# opt-in. One oracle per admission claim, driven through the request policy the executor and the dispatch script both call.
def dispatch_problem(shared, tmp_path, monkeypatch, **backup):
    monkeypatch.setattr(shared, 'absence_evidence', lambda req, root: None)
    req = {'kind': 'smalltest_dispatch', 'args': {'run': 'one_class_full', 'classes': 'marriage'}, **backup}
    return shared.smalltest_request_problem(req, tmp_path)


def test_dispatch_without_a_named_backup_is_refused_even_when_no_backup_exists_to_be_stale(shared, tmp_path, monkeypatch):
    for backup in ({}, {'backup_label': 'p02_win'}, {'backup_restore_sha256': '0' * 64}):
        assert 'must name its backup' in dispatch_problem(shared, tmp_path, monkeypatch, **backup), backup


def test_dispatch_policy_admits_a_nine_hour_old_scoped_backup_while_its_content_is_unchanged_and_refuses_it_after_a_change(shared, tmp_path, monkeypatch):
    old = write_evidence(tmp_path, shared, started=datetime.now(timezone.utc) - timedelta(hours=9))
    monkeypatch.setattr(shared, 'absence_evidence', lambda req, root: None)
    req = {'kind': 'smalltest_dispatch', 'args': {'run': 'one_class_full', 'classes': 'marriage'}, **old}
    assert shared.smalltest_request_problem(req, tmp_path, measure=now_measure()) is None
    assert 'content has changed' in shared.smalltest_request_problem(req, tmp_path, measure=now_measure(changed='public.a'))


def test_a_full_backup_proof_is_admitted_only_inside_the_same_window(shared, tmp_path, monkeypatch):
    stale = write_full_evidence(tmp_path / 'stale', shared, captured=datetime.now(timezone.utc) - timedelta(hours=9))
    fresh = write_full_evidence(tmp_path / 'fresh', shared)
    assert 'outside its validity window' in dispatch_problem(shared, tmp_path / 'stale', monkeypatch, **stale)
    assert dispatch_problem(shared, tmp_path / 'fresh', monkeypatch, **fresh) is None


def test_a_full_backup_proof_without_a_timestamp_is_refused_not_allowed(shared, tmp_path, monkeypatch):
    req = write_full_evidence(tmp_path, shared)
    capture = tmp_path / 'backups' / req['backup_label'] / 'capture.json'
    body = json.loads(capture.read_text())
    del body['ts']
    capture.write_text(json.dumps(body))
    proof = tmp_path / 'backups' / req['backup_label'] / 'restore.json'
    edited = json.loads(proof.read_text())
    edited['capture_sha256'] = hashlib.sha256(capture.read_bytes()).hexdigest()
    proof.write_text(json.dumps(edited))
    req['backup_restore_sha256'] = hashlib.sha256(proof.read_bytes()).hexdigest()
    assert 'no timestamp' in dispatch_problem(shared, tmp_path, monkeypatch, **req)


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


def test_scoped_plan_states_scope_digest_and_validity_basis_and_touches_nothing(backup, shared, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    assert backup.main(['--operation', 'snapshot', '--label', 'p02_plan', '--scope', 'small_test', '--dry-run']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['scope'] == 'small_test' and plan['scope_sha256'] == shared.SCOPED_BACKUP_SCOPE_SHA256
    assert plan['validity_basis'] == 'scoped_content_digest_unchanged' and 'validity_seconds' not in plan and plan['backup_taken'] is None
    assert list(tmp_path.iterdir()) == []
    assert backup.main(['--operation', 'snapshot', '--label', 'p02_plan', '--dry-run']) == 0
    assert 'scope' not in json.loads(capsys.readouterr().out)


def test_the_executor_table_lets_a_backup_request_carry_the_scope_and_nothing_else_new():
    ops = json.loads((support.ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json').read_text())['ops']
    for kind in ('backup_snapshot', 'backup_restore_verify'):
        assert ops[kind]['allowed_args'] == ['label', 'scope'], kind
        assert ops[kind]['fixed_args'][-1] == '--execute'


# ---- C9: the dispatch script's own --execute policy measures the scope (the only fresh-content gate in production) ------

def test_the_dispatch_execute_policy_measures_the_scope_and_refuses_a_backup_whose_content_changed(backup, shared, tmp_path, monkeypatch):
    """SR-BACKUP-VALIDITY-A8 §3.10/§4: with the clock gone, `_smalltest_request_policy` (what `--execute` runs before staging) is the
    only production check that reads the database. It must hand backup.measure_scope_now to the evidence policy: a 9 h old backup
    is admitted while the fresh measurement equals the recorded digest, and refused as soon as it differs."""
    dispatch = importlib.import_module('dispatch_v5_small_test_job')
    old = write_evidence(tmp_path, shared, started=datetime.now(timezone.utc) - timedelta(hours=9))
    monkeypatch.setattr(shared, 'absence_evidence', lambda req, root: None)
    req = {'kind': 'smalltest_dispatch', 'args': {'run': 'one_class_full', 'classes': 'marriage'}, **old}
    unchanged = now_measure()
    monkeypatch.setattr(backup, 'measure_scope_now', unchanged)
    assert dispatch._smalltest_request_policy(req, tmp_path) is None
    assert unchanged.seen == [(['public.a', 'public.b'], ['public.a_id_seq'])]       # it really measured the recorded relations
    monkeypatch.setattr(backup, 'measure_scope_now', now_measure(changed='public.a'))
    assert 'content has changed' in dispatch._smalltest_request_policy(req, tmp_path)


def test_the_century_execute_policy_names_no_backup_and_keeps_every_other_admission_check(backup, shared, tmp_path, monkeypatch):
    """SR-A12-BACKUP-REMOVAL (supersedes SR-BACKUP-VALIDITY-A8 §3.10 for the century dispatch): no dump is taken, so a century dispatch that names no
    backup_label / backup_restore_sha256 is ADMITTED by `_century_request_policy` (what `--execute` runs before staging), and a request that still
    names a stale or changed backup is not refused for it. What stays is the ruling's exact-scope measurability: the reviewed scope's relations are
    measured (no backup content is compared) and a scope that cannot be measured refuses. Every other check of that policy still refuses: the item,
    the four exact args, the independent absence of the generation and the completed staging dry run."""
    century = importlib.import_module('dispatch_v5_century_job')
    refuse = {}
    def gate(name):
        def check(req, root, digest=None):
            if name in refuse:
                raise shared.Refused(refuse[name])
        return check
    monkeypatch.setattr(shared, 'absence_evidence', gate('absence'))
    monkeypatch.setattr(shared, 'century_dryrun_evidence', gate('dryrun'))
    req = {'kind': 'century_dispatch', 'item_id': shared.CENTURY_ITEM, 'args': {'classes': 'all', 'final_rules': 'true', 'defer_in_build_verify': 'true', 'horizon': '2001-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00', 'result_policy': 'window_qualification/1'}}      # the five exact args (F-CHANNEL, OD-1), synthetic bounds
    assert 'backup_label' not in req and 'backup_restore_sha256' not in req
    unchanged = now_measure()
    monkeypatch.setattr(backup, 'measure_scope_now', unchanged)
    assert century._century_request_policy(req, tmp_path) is None
    assert unchanged.seen == [(backup.load_scope()['tables'], [])], 'the reviewed scope relations are measured, once, for measurability only'
    def cannot_measure(tables, sequences, dsn=None, presence_only=None):
        raise RuntimeError('relation does not exist')
    monkeypatch.setattr(backup, 'measure_scope_now', cannot_measure)
    assert 'scoped content could not be measured now' in century._century_request_policy(req, tmp_path)
    old = write_evidence(tmp_path, shared, scope_sha=shared.SCOPED_BACKUP_SCOPE_SHA256S['century'], started=datetime.now(timezone.utc) - timedelta(days=30))
    monkeypatch.setattr(backup, 'measure_scope_now', now_measure(changed='public.a'))
    assert century._century_request_policy({**req, **old}, tmp_path) is None, 'a named backup is ignored, not judged'
    assert 'belongs to' in century._century_request_policy(dict(req, item_id='K9-4a'), tmp_path)
    assert century._century_request_policy(dict(req, args=dict(req['args'], final_rules='maybe')), tmp_path)
    refuse['absence'] = 'generation 5.0 is not absent'
    assert century._century_request_policy(req, tmp_path) == 'generation 5.0 is not absent'
    del refuse['absence']
    refuse['dryrun'] = 'no completed staging dry run'
    assert century._century_request_policy(req, tmp_path) == 'no completed staging dry run'


def test_the_century_policy_pins_the_four_builder_unreadable_relations_and_shows_a_named_refusal(backup, shared, tmp_path, monkeypatch):
    """Claims (SR-J4E-FIX-AMEND-1; migration 1240 'the builder gets NOTHING on the new table', migration 1211 'no grant of SELECT'): (a) the presence-only set is
    EXACTLY the four relations the production read-only measurement found the builder cannot SELECT (receipt J-4e.builder-select-20261024T1756Z: of the 38
    scoped relations none missing; the migrations ledger, the two window-verification tables and asset_throughput_state_audit), all inside both reviewed scopes, and the policy hands exactly that set to the measurement; (b) a named refusal
    of the measurement (a missing relation) reaches the caller with its relation name, while any other failure stays the fixed text."""
    century = importlib.import_module('dispatch_v5_century_job')
    monkeypatch.setattr(shared, 'absence_evidence', lambda req, root, *a: None)
    monkeypatch.setattr(shared, 'century_dryrun_evidence', lambda req, root, *a: None)
    req = {'kind': 'century_dispatch', 'item_id': shared.CENTURY_ITEM, 'args': dict(zip(shared.CENTURY_ARG_KEYS, ('all', 'true', 'true', '2001-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00', 'window_qualification/1')))}
    assert century.PRESENCE_ONLY_RELATIONS == {'public._migrations_applied', 'public.ka_gochara_eval_window_verification',
                                                'public.ka_gochara_search_inventory_verification', 'public.asset_throughput_state_audit'}
    assert len(century.PRESENCE_ONLY_RELATIONS) == 4
    assert century.PRESENCE_ONLY_RELATIONS <= set(backup.load_scope()['tables'])
    assert century.PRESENCE_ONLY_RELATIONS <= set(backup.load_scope(name='century')['tables'])
    seen = []

    def measure(tables, sequences, dsn=None, presence_only=None):
        seen.append(presence_only)
        return {'tables': {}, 'sequences': {}}
    monkeypatch.setattr(backup, 'measure_scope_now', measure)
    assert century._century_request_policy(req, tmp_path) is None
    assert seen == [century.PRESENCE_ONLY_RELATIONS]

    def missing(tables, sequences, dsn=None, presence_only=None):
        raise backup.BackupRefused('scope relation missing: public.ka_gochara_x')
    monkeypatch.setattr(backup, 'measure_scope_now', missing)
    problem = century._century_request_policy(req, tmp_path)
    assert 'scoped content could not be measured now' in problem and 'public.ka_gochara_x' in problem


def test_century_scope_relations_equal_the_small_test_scope(backup):
    """Claim (A12-M1): `_century_request_policy` measures the reviewed small-test scope's tables as the century scope's relations; that stand-in is only
    sound while the two reviewed files list the same relations (SR-A12-BACKUP-REMOVAL keeps the exact-scope measurement)."""
    century, small = backup.load_scope(name='century'), backup.load_scope(name='small_test')
    assert century['tables'] == small['tables'] and century['written'] == small['written']


# ---- SR-RESTORE-SCHEMA-ONLY: the century backup's real migration set; the unchanged capture path; the reset search_path -----

CENTURY_LEDGER_AFTER_THE_BUNDLE = [
    '1394_gochara_statement_lock_touched_charts.sql', '1395_ka_gochara_v5_writer_timeout_72000.sql', '1305_gochara_snapshot_owns_l1_copy.sql',
    '1306_gochara_expected_class_census.sql', '1308_gochara_near_miss_storage.sql', '1392_k8_registry_truth.sql',
    '1381_gochara_near_miss_seal_integration.sql', '1390_kala_layer_operation_verifier_reads.sql', '1398_gochara_snapshot_dasha_held.sql',
    '1397_k8_registry_remainder.sql', '1399_ka_yojaka_output_digest_v2.sql', '1400_ka_yojaka_output_digest_v3.sql',
    '1405_kala_convergence_generation.sql', '1404_gochara_resonance_map_generation.sql', '1408_ka_vedha_gochara_writer_timeout_600.sql',
    '1406_kala_obstruction_generation_scope.sql', '1409_k9_floors_achieved_zero.sql', '1403_ka_gochara_v5_depends_on_l0_dignity.sql',
    '1402_gochara_qualification_provenance_certificate.sql']       # the 19 that mention a century scope table, in production's ledger order (run 7b62d268)
CENTURY_SCHEMA_MIGRATIONS = ['1394_gochara_statement_lock_touched_charts.sql', '1305_gochara_snapshot_owns_l1_copy.sql',
                             '1306_gochara_expected_class_census.sql', '1308_gochara_near_miss_storage.sql',
                             '1381_gochara_near_miss_seal_integration.sql', '1398_gochara_snapshot_dasha_held.sql',
                             '1402_gochara_qualification_provenance_certificate.sql']


def test_the_century_backups_nineteen_later_migrations_reduce_to_the_seven_that_create_schema_objects(backup, monkeypatch):
    """Claim A (run 7b62d268): the repository's real migration files, the reviewed century scope. Mention alone picks 19, 12 of which only
    edit registry rows (or grant to a role) and cannot run on a copy without production rows; the schema-object rule keeps the 7 that
    create a function, trigger or table."""
    cut = datetime.fromisoformat(backup.SCOPED_RESTORE_BASE_CUT)
    rows = [(n, name, cut + timedelta(hours=n), hashlib.sha256((backup.MIGRATIONS_DIR / name).read_bytes()).hexdigest())
            for n, name in enumerate(CENTURY_LEDGER_AFTER_THE_BUNDLE, start=1)]
    ledger = backup.ledger_entries(rows)
    tables = backup.load_scope(name='century')['tables'] + ['public.asset_output_digest_specs', 'public.charts', 'public.profiles']   # + the capture's 3 FK parents
    chosen = backup.derive_restore_migrations(ledger, tables)
    assert [n for n, _ in chosen] == CENTURY_SCHEMA_MIGRATIONS
    with monkeypatch.context() as old_rule:
        old_rule.setattr(backup, 'SCHEMA_OBJECT', re.compile(''))                 # the mention-only rule that failed
        assert len(backup.derive_restore_migrations(ledger, tables)) == 19


def test_the_restore_base_resets_the_bundles_empty_search_path_before_the_first_migration_and_the_steps_join_to_the_script(backup, tmp_path, monkeypatch):
    """Claim B: the bundle sets search_path to '' for its session; production applied migrations with the default path."""
    root = _bundle(tmp_path, backup, monkeypatch, b"SELECT pg_catalog.set_config('search_path', '', false);\nCREATE SCHEMA public;\nCREATE TABLE public.t (id int);\n")
    migrations = tmp_path / 'migrations'
    migrations.mkdir()
    (migrations / '1_a.sql').write_text('SELECT 1;')
    monkeypatch.setattr(backup, 'MIGRATIONS_DIR', migrations)
    pins = (('1_a.sql', hashlib.sha256(b'SELECT 1;').hexdigest()),)
    steps, identity = backup.restore_base_steps(root, pins)
    assert [name for name, _ in steps] == ['bundle', '1_a.sql']
    assert steps[0][1].rstrip().endswith('RESET search_path;') and 'SELECT 1;' not in steps[0][1]
    text, same_identity = backup.restore_base_sql(root, pins)
    assert text == ''.join(sql for _, sql in steps) and same_identity == identity
    assert text.index("set_config('search_path'") < text.index('RESET search_path;') < text.index('SELECT 1;')


H2_CAPTURE_SCRIPT = '94f76c4ffbe3533e9954a0742e8dc11707e3c4827b380ec57a473239f980e0b0'          # backup_v5_small_test_job.py at c718a5535
# sha256 over the source text of every module-level definition reachable from `snapshot` (the capture entry point), taken from c718a5535
H2_CAPTURE_PATH_DIGEST = 'a4493df17426dd96fed7e4c50fc73c111c366bb98959e636af1a93253ddac9bd'


def capture_path_digest(source):
    """(digest, names): the source text of each module-level function/class/constant reachable by name from `snapshot`, hashed together."""
    tree = ast.parse(source)
    defs = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defs[node.name] = node
        elif isinstance(node, ast.Assign):
            defs.update({t.id: node for t in node.targets if isinstance(t, ast.Name)})
    reach, todo = set(), ['snapshot']
    while todo:
        name = todo.pop()
        if name not in reach and name in defs:
            reach.add(name)
            todo += [n.id for n in ast.walk(defs[name]) if isinstance(n, ast.Name)]
    parts = {n: ast.get_source_segment(source, defs[n]) for n in sorted(reach)}
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest(), sorted(reach)


def test_the_capture_path_is_byte_identical_to_the_h2_script(backup):
    """Claim E: SCOPED_LEGACY_CAPTURE_SCRIPTS admits the H2 script's captures only while this file would have written the very same capture.
    Any edit to a definition the capture reaches changes this digest: then the H2 entry must be removed (and the label re-captured)."""
    digest, names = capture_path_digest(Path(backup.__file__).read_text())
    assert {'snapshot', 'snapshot_scoped', 'scoped_catalog', 'scoped_measurements', 'validate_scoped_capture', 'dump_table_args'} <= set(names)
    assert not {'restore_verify', 'restore_verify_scoped', 'derive_restore_migrations', 'restore_base_sql', 'SCHEMA_OBJECT',
                'SCOPED_LEGACY_CAPTURE_SCRIPTS'} & set(names)                     # the restore side is outside the capture path
    assert digest == H2_CAPTURE_PATH_DIGEST


def test_the_legacy_capture_list_holds_exactly_the_two_reviewed_identities(backup):
    assert sorted(backup.SCOPED_LEGACY_CAPTURE_SCRIPTS) == sorted([H2_CAPTURE_SCRIPT, '3f967bf9cd99abe725db9983b50f99d4263e96336c44ee4b2ce3a707022aeb29'])
    assert hashlib.sha256(Path(backup.__file__).read_bytes()).hexdigest() != H2_CAPTURE_SCRIPT      # this file is a new script: the entry is what admits the old capture


@pytest.mark.parametrize('error,expected', [
    ('42P01', 'restore base step 1395_x.sql failed: FakeError sqlstate=42P01 (relation "asset_registry" does not exist)'),
    ('P0001', 'restore base step 1395_x.sql failed: FakeError sqlstate=P0001'),
])
def test_a_base_step_failure_repeats_only_identifier_messages(backup, error, expected):
    class Diag:
        schema_name = table_name = column_name = constraint_name = None
        message_primary = 'relation "asset_registry" does not exist' if error == '42P01' else 'row content (secret-row-value) is not allowed'

    class FakeError(Exception):
        sqlstate, diag = error, Diag()
    assert str(backup.base_step_failure('1395_x.sql', FakeError())) == expected
