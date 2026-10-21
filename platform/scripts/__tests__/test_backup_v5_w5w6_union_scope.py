"""M-W56-6 / KIND-backup_snapshot: the `w5w6_union` scoped-backup scope, the W5+W6 window's ONE dump (SR-MINIMAL-PROTECTION). No DB, program or credential is
used (the real capture against a disposable database is tests/l3/kala_db/test_p01_w5w6_union_backup_scope.py; the executor's admission is
00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_executor_w5w6_union_scope.py).

One doctrine-grounded oracle per distinct production claim (D-OWNER-TESTS-20261016; §N.8: each is a detector that can read false):
U1 the scope lists every table the J-6 head change and the K9 closed plan can write, or read as the head change's retained/guarded surface: the J-2a static
   scan run over head_operation.py, the K9 control modules, the six plan writers' import closure and the orchestrator; the detector is shown to read false ·
U1d every dynamic write site of that code resolves to tables the scope lists (constants; the literal arguments of replace_candidate_partition, failing closed on a
   non-literal one; the teardown's foreign-key referrers, read from the migrations) and every table declared `unreached` really is unreached ·
U2 the digest the executor-loaded policy pins is the file's, recomputed here without the repository's own function, and it covers the NAME and the tables ·
U3 a `w5w6_union` request reaches the scoped mechanism and is admitted only by a proof of the union scope; a proof of another scope never admits it, nor the reverse ·
U5 the union keeps every dump exclusion and every guarded child of the scopes it unions with, so no personal-data relation moves into the archive.
"""
import ast
import copy
import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import smalltest_backup_scope_support as support  # noqa: E402
import smalltest_w5w6_union_support as union  # noqa: E402
from test_backup_v5_small_test_scoped import receipt_and_archive, write_evidence  # noqa: E402,F401  (fixture + helper of the small-test suite)

SCRIPTS = support.SCRIPTS
SCOPE_FILE = SCRIPTS / 'backup_v5_w5w6_union_scope.json'
OTHER_SCOPES = ('small_test', 'century', 'verification_seal')
OTHER_FILES = {'small_test': 'backup_v5_small_test_scope.json', 'century': 'backup_v5_century_scope.json', 'verification_seal': 'backup_v5_verification_seal_scope.json'}
# What the J-6 pack (W5W6 pack v1.2) declares for the same window, an independent statement of the same surface: PACK/SCOPE.json written_tables + read_guarded_tables
# and PACK/k9/SCOPE_PINS.json required_tables (the layer-manifest tables of migration 1330 and the migration ledger).
PACK_J6_WRITTEN = {'public.kala_gochara_authority', 'public.kala_gochara_publication'}
PACK_J6_READ_GUARDED = {'public.ka_gochara_generation_seal'}
PACK_K9_REQUIRED = {'public._migrations_applied', 'public.kala_layer_candidate', 'public.kala_layer_candidate_grain', 'public.kala_layer_head', 'public.kala_layer_verification'}


@pytest.fixture
def backup():
    return importlib.import_module('backup_v5_small_test_job')


@pytest.fixture
def shared():
    return importlib.import_module('v5_small_test_shared')


@pytest.fixture(scope='module')
def scope():
    return json.loads(SCOPE_FILE.read_text())


@pytest.fixture(scope='module')
def files():
    return union.union_scanned_files()


@pytest.fixture(scope='module')
def sites(files):
    return support.write_sites(files)


def table_names(entries):
    return {e['table'].split('.', 1)[1] for e in entries}


# ---- U1: every write target of the J-6 head change and the K9 closed plan is in the scope --------------------------------------

def test_u1_every_write_target_of_the_head_change_and_the_k9_closed_plan_is_in_the_scope(scope, files, sites):
    assert scope['plan'] == list(union.CLOSED_PLAN)
    scanned = {support.rel(f) for f in files}
    assert support.rel(union.HEAD_OPERATION) in scanned and support.rel(union.KALA_CORE / 'rebuild_control.py') in scanned      # the scan reaches both halves
    assert {support.rel(union.WRITERS_DIR / f'{name}.py') for name in union.CLOSED_PLAN} <= scanned
    targets = {s['table'] for s in sites}
    assert {'kala_gochara_authority', 'kala_layer_head', 'kala_layer_candidate', 'kala_layer_verification', 'kala_obstruction', 'asset_throughput'} <= targets     # not vacuous
    assert support.uncovered_targets(sites, scope) == []


def test_u1_detector_reads_false_for_a_write_the_scope_does_not_list(scope, tmp_path):
    planted = tmp_path / 'planted.py'
    planted.write_text('def f(cur, table):\n    cur.execute("UPDATE public.union_only_table SET a = 1")\n'
                       '    cur.execute(f"DELETE FROM {table} WHERE a = 1")\n'
                       '    cur.execute("UPDATE public.kala_gochara_authority SET authoritative_generation = 1")   # in scope: not flagged\n')
    bad = support.uncovered_targets(support.write_sites([planted]), scope)
    assert 'union_only_table' in bad and any('placeholder' in b for b in bad) and 'kala_gochara_authority' not in bad


def test_u1_the_scope_lists_what_the_head_change_reads_and_what_the_pack_declares_for_the_window(scope):
    listed = {e['table'] for e in scope['written']} | {e['table'] for e in scope['context']}
    retained = {f'public.{t}' for t in support.eval_constant([union.HEAD_OPERATION], 'RETAINED_TABLES')}
    assert len(retained) == 9
    read = {f"public.{m}" for _, _, text in support.sql_strings(ast.parse(union.HEAD_OPERATION.read_text()))
            for m in re.findall(r'(?i)\b(?:FROM|JOIN)\s+public\.([a-z_][a-z0-9_]*)', text)}
    assert {'public.kala_gochara_authority', 'public.kala_gochara_publication', 'public.ka_gochara_generation_seal'} <= read       # not vacuous
    assert (retained | read) <= listed, (retained | read) - listed
    assert PACK_J6_WRITTEN | PACK_J6_READ_GUARDED | PACK_K9_REQUIRED <= listed
    assert {e['table'] for e in scope['written']} >= PACK_J6_WRITTEN                                     # the pack's written pair stays in the stricter class
    assert {e['table'] for e in scope['context']} >= PACK_J6_READ_GUARDED | {'public._migrations_applied'}


# ---- U1d: dynamic sites and `unreached` ------------------------------------------------------------------------------------------

def test_u1_dynamic_write_sites_resolve_to_the_tables_the_scope_declares(scope, files):
    written = table_names(scope['written'])
    literal, non_literal = union.partition_calls(files)
    assert non_literal == []                                       # a computed table argument is unreviewed: it fails closed, never assumed away
    referrers = union.fk_referrers(support.ROOT / 'platform/migrations', 'kala_layer_candidate')
    kinds = set()
    for site in scope['dynamic_sites']:
        kind = site['resolver'].split(':')[0]
        kinds.add(kind)
        if kind == 'literals':
            resolved = sorted({table for _, _, table in literal})
        elif kind == 'fk_referrers':
            assert set(site['tables']) <= set(referrers), set(site['tables']) - set(referrers)    # every declared table really references the candidate
            resolved = sorted(site['tables'])                      # the run-time catalog read cannot be repeated offline: the set is bounded by `written` below
        else:
            resolved = support.resolve_dynamic(site['resolver'])
        assert resolved == sorted(site['tables']) and set(resolved) <= written | {t for u in scope['unreached'] for t in u['tables']}, site['function']
    assert kinds == {'const', 'literals', 'fk_referrers'}
    assert {t for _, _, t in literal} <= written                   # no literal partition call reaches a table the plan does not own
    assert not ({t for _, _, t in literal} & {t for u in scope['unreached'] for t in u['tables']})


def test_u1_dynamic_detectors_read_false(files, tmp_path):
    planted = tmp_path / 'planted.py'
    planted.write_text('def f(conn, name):\n    replace_candidate_partition(conn, "kala_darshana", "c", "g", None, [])\n    replace_candidate_partition(conn, "kala_" + name, "c", "g", None, [])\n')
    literal, non_literal = union.partition_calls([planted])
    assert [t for _, _, t in literal] == ['kala_darshana'] and len(non_literal) == 1
    edges = tmp_path / 'migrations'
    edges.mkdir()
    (edges / '9001_x.sql').write_text('CREATE TABLE public.kala_new_child (chart_id uuid, generation text,\n  FOREIGN KEY (chart_id, generation) REFERENCES public.kala_layer_candidate(chart_id, generation));\n'
                                      'CREATE TABLE public.kala_grandchild (a int REFERENCES public.kala_new_child(a));\n-- CREATE TABLE public.kala_commented (a int REFERENCES public.kala_layer_candidate(a));\n')
    assert sorted(union.fk_referrers(edges, 'kala_layer_candidate')) == ['kala_grandchild', 'kala_new_child']


def references_name(files, name):
    hits = []
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            if (isinstance(node, ast.Name) and node.id == name) or (isinstance(node, ast.Attribute) and node.attr == name) \
                    or (isinstance(node, (ast.ImportFrom, ast.Import)) and any(a.name.split('.')[-1] == name for a in node.names)):
                hits.append(support.rel(path))
    return sorted(set(hits))


def test_u1_tables_declared_unreached_are_written_only_by_code_the_closed_plan_never_runs(scope, files, sites):
    assert {u['name'] for u in scope['unreached']} == {'idempotency_catalog_of_other_writers', 'issued_forecast_registrar', 'sky_event_store', 'bg_gochara_arcs_writer'}
    literal, _ = union.partition_calls(files)
    for entry in scope['unreached']:
        found = {s['file'] for s in sites if s['table'] in entry['tables']} | {s['file'] for s in sites if s['table'].startswith('{') and entry['name'] == 'bg_gochara_arcs_writer'
                                                                           and s['file'] == entry['module']}
        assert found == {entry['module']}, (entry['name'], found)
        outside = [f for f in files if support.rel(f) != entry['module']]
        if entry['check'] == 'catalog':
            assert not {t for _, _, t in literal} & set(entry['tables'])                  # the closed plan's partition calls never name one of these tables
        elif entry['check'] == 'entry_functions':
            names = set(entry['entry_functions'])
            assert support.references(names, set(entry['aliases']), outside) == []
            assert support.internal_callers(support.ROOT / entry['module'], names | set(entry['internal_functions'])) <= names
        elif entry['check'] == 'class_imports':
            for name in entry['class_names']:
                assert references_name(outside, name) == [], (name, references_name(outside, name))
        else:
            assert entry['check'] == 'imported_names'
            stem = Path(entry['module']).stem
            imported = set()
            for path in outside:
                for node in ast.walk(ast.parse(path.read_text())):
                    if isinstance(node, ast.ImportFrom):
                        if (node.module or '').split('.')[-1] == stem:
                            imported |= {a.name for a in node.names}
                        assert stem not in {a.name for a in node.names}, support.rel(path)     # `from <package> import <module>` would reach the whole module
                    elif isinstance(node, ast.Import):
                        assert stem not in {a.name.split('.')[-1] for a in node.names}, support.rel(path)
            assert imported and imported <= set(entry['allowed_imports']), imported


def test_u1_unreached_detector_reads_false_when_the_plan_starts_to_use_an_unreached_writer(tmp_path):
    planted = tmp_path / 'planted.py'
    planted.write_text('from services.gochara_kernel.substrate import SkyEventStore\nfrom services.kala_core.idempotency import insert_immutable_checked\n'
                       'def f(conn):\n    insert_immutable_checked(conn, "issued_forecast", {})\n')
    assert references_name([planted], 'SkyEventStore') == [support.rel(planted)]
    assert support.references({'insert_immutable_checked'}, {'idempotency'}, [planted]) != []


def test_u1_the_union_never_deletes_a_build_runs_row_so_the_guarded_children_never_fire(scope, sites):
    assert [s for s in sites if s['table'] == 'build_runs' and s['kind'] in ('DELETE', 'TRUNCATE')] == []
    assert any(s['table'] == 'build_runs' and s['kind'] == 'UPDATE' for s in sites)


# ---- U2: the pinned digest -------------------------------------------------------------------------------------------------------

def test_u2_the_policy_pins_the_files_digest_and_the_digest_covers_the_name_and_the_tables(backup, shared, scope, tmp_path):
    loaded = backup.load_scope(name='w5w6_union')
    pinned = shared.SCOPED_BACKUP_SCOPE_SHA256S['w5w6_union']
    assert loaded['name'] == 'w5w6_union' and loaded['sha256'] == pinned
    tables = sorted({e['table'] for e in scope['written']} | {e['table'] for e in scope['context']})
    assert len(tables) == 38 and loaded['tables'] == tables
    # the rule recomputed by hand, not by the repository's scope_digest
    by_hand = hashlib.sha256(json.dumps({'schema': 'ky.smalltest_backup_scope/1', 'name': 'w5w6_union', 'tables': tables}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert by_hand == pinned
    assert pinned not in {shared.SCOPED_BACKUP_SCOPE_SHA256S[name] for name in OTHER_SCOPES}
    assert backup.scope_digest('century', tables) != pinned                                                     # the NAME is covered
    assert backup.scope_digest('w5w6_union', tables + ['public.one_more']) != pinned                            # and the tables
    assert backup.scope_digest('w5w6_union', list(reversed(tables))) == pinned
    renamed = copy.deepcopy(scope)
    renamed['name'] = 'century'
    (tmp_path / 'renamed.json').write_text(json.dumps(renamed))
    assert backup.load_scope(tmp_path / 'renamed.json')['sha256'] != pinned


def test_u2_an_edited_scope_file_that_is_not_repinned_is_caught(backup, shared, scope, tmp_path):
    edited = copy.deepcopy(scope)
    edited['written'] = [e for e in edited['written'] if e['table'] != 'public.kala_gochara_authority']
    (tmp_path / 'edited.json').write_text(json.dumps(edited))
    assert backup.load_scope(tmp_path / 'edited.json')['sha256'] != shared.SCOPED_BACKUP_SCOPE_SHA256S['w5w6_union']


# ---- U3: the scope reaches the mechanism and a proof of another scope never admits it -------------------------------------------------

@pytest.mark.parametrize('proof_scope', ['small_test', 'century', 'verification_seal', 'w5w6_union'])
def test_u3_a_union_dispatch_is_admitted_only_by_a_union_proof_and_a_union_proof_admits_no_other_scope(shared, tmp_path, proof_scope):
    req = write_evidence(tmp_path, shared, scope_sha=shared.SCOPED_BACKUP_SCOPE_SHA256S[proof_scope])
    if proof_scope == 'w5w6_union':
        assert shared.scoped_backup_problem(req, tmp_path, scope='w5w6_union') is None
        for other in OTHER_SCOPES:
            with pytest.raises(shared.Refused, match='scope other than the reviewed'):
                shared.scoped_backup_problem(req, tmp_path, scope=other)
    else:
        with pytest.raises(shared.Refused, match='scope other than the reviewed'):
            shared.scoped_backup_problem(req, tmp_path, scope='w5w6_union')


def test_u3_a_capture_of_another_scope_is_not_valid_as_the_union(backup, receipt_and_archive):
    receipt, archive = receipt_and_archive                                                                   # a small_test capture
    with pytest.raises(backup.BackupRefused, match='capture scope differs from the reviewed scope'):
        backup.validate_scoped_capture(receipt, archive, 'p02_fixture', 'w5w6_union')


def test_u3_the_cli_offers_the_union_scope_and_plans_its_digest_without_side_effects(backup, shared, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    for operation in ('snapshot', 'restore-verify'):
        assert backup.main(['--operation', operation, '--label', 'w56_union_plan', '--scope', 'w5w6_union', '--dry-run']) == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan['scope'] == 'w5w6_union' and plan['scope_sha256'] == shared.SCOPED_BACKUP_SCOPE_SHA256S['w5w6_union']
        assert plan['validity_basis'] == 'scoped_content_digest_unchanged'
    assert list(tmp_path.iterdir()) == []


def test_u3_the_union_name_reaches_the_scoped_capture_and_restore(backup, tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(backup, 'snapshot_scoped', lambda folder, label, scope_name='small_test': seen.append(('snapshot', scope_name)) or {})
    monkeypatch.setattr(backup, 'restore_verify_scoped', lambda folder, label, receipt, scope_name='small_test': seen.append(('restore', scope_name)) or {})
    backup.snapshot(tmp_path / 'f', 'w56_x', 'w5w6_union')
    (tmp_path / 'f').mkdir()
    (tmp_path / 'f' / 'capture.json').write_text(json.dumps({'schema': 'ky.smalltest_backup/2'}))
    backup.restore_verify(tmp_path / 'f', 'w56_x', 'w5w6_union')
    assert seen == [('snapshot', 'w5w6_union'), ('restore', 'w5w6_union')]


def test_u3_the_script_names_the_union_scope_where_the_packs_rebind_looks_for_it():
    text = (SCRIPTS / 'backup_v5_small_test_job.py').read_text()
    assert "'w5w6_union'" in text.split('--scope', 1)[1][:200]                                              # the pack's rebind check: "the script does not name the 'w5w6_union' scope"


# ---- U5: the union keeps the fences of the scopes it unions with ------------------------------------------------------------------------

def declared(doc, key):
    return {e['table'] for e in doc.get(key, [])}


def fences_dropped(union_doc, other_docs):
    """The dump exclusions and guarded children of the other scopes that the union does not keep, and the union tables an other scope excludes from its dump."""
    lost = set()
    for doc in other_docs:
        lost |= (declared(doc, 'dump_excludes') - declared(union_doc, 'dump_excludes')) | (declared(doc, 'guarded_children') - declared(union_doc, 'guarded_children'))
    in_scope = declared(union_doc, 'written') | declared(union_doc, 'context')
    return sorted(lost | {t for doc in other_docs for t in declared(doc, 'dump_excludes') & in_scope})


def test_u5_the_union_keeps_every_dump_exclusion_and_guarded_child_of_the_other_scopes(scope):
    others = [json.loads((SCRIPTS / OTHER_FILES[name]).read_text()) for name in OTHER_SCOPES]
    assert declared(others[1], 'guarded_children')                                                          # not vacuous: the century fence names six personal-data/history relations
    assert fences_dropped(scope, others) == []
    assert {'public.conversations', 'public.mimamsa_predictions'} <= declared(scope, 'guarded_children')
    assert not ({'public.conversations', 'public.mimamsa_predictions', 'public.charts', 'public.chart_facts'} & (declared(scope, 'written') | declared(scope, 'context')))
    # FACT, stated rather than assumed: today no reviewed scope declares a `dump_excludes` entry, so that half of the rule holds for an empty set
    assert all(not declared(doc, 'dump_excludes') for doc in [*others, scope])


def test_u5_detector_reads_false_when_a_fence_is_dropped_or_an_excluded_relation_enters_the_scope(scope):
    others = [json.loads((SCRIPTS / OTHER_FILES[name]).read_text()) for name in OTHER_SCOPES]
    dropped = copy.deepcopy(scope)
    dropped['guarded_children'] = [e for e in dropped['guarded_children'] if e['table'] != 'public.conversations']
    assert fences_dropped(dropped, others) == ['public.conversations']
    excluding = copy.deepcopy(others[1])
    excluding['dump_excludes'] = [{'table': 'public.some_personal_table'}]
    assert fences_dropped(scope, [excluding]) == ['public.some_personal_table']                            # excluded elsewhere, not kept here
    entered = copy.deepcopy(scope)
    entered['context'].append({'table': 'public.some_personal_table'})
    entered['dump_excludes'] = [{'table': 'public.some_personal_table'}]
    assert fences_dropped(entered, [excluding]) == ['public.some_personal_table']                          # kept as an exclusion but also in the data set
