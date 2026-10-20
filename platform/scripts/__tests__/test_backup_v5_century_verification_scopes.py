"""W3W4 pack verify E3: the `century` and `verification_seal` scoped-backup scopes. No DB, program or credential is used (the real pg_dump / pg_restore round trip of both
names is in tests/l3/kala_db/test_p01_smalltest_backup_scoped.py).

One doctrine-grounded oracle per distinct production claim (D-OWNER-TESTS-20261016):
S1 every table the CENTURY code can write is in the century scope (the same AST scan as the small-test scope, run over the century dispatch and launch modules too; the
   detector is shown to read false against a planted write) ·
V1 the verification_seal scope IS the write surface the code declares and enforces for the verifier and the sealer (verification_job.VERIFIER_WRITE_TABLES, seal_flow.
   SEALER_WRITE_ALLOWED), re-derived from the constants; the detector is shown to read false when a constant gains a table ·
V2 every write statement of the verification and sealing modules targets a table of that scope ·
P1 each scope's digest is pinned in the executor-loaded policy and equals its reviewed file; the digest covers the scope NAME, so scopes never share one ·
P2 a proof of one scope never admits a dispatch of another, and a century dispatch demands the CENTURY scope's proof ·
L1 scope selection: `load_scope(name=...)` reads that scope's file, a path override keeps its name, an unknown or mismatched name is refused ·
R1 a capture of one scope is not valid as another and each name reaches the scoped mechanism, `--scope` offers the three names and the plan states the chosen digest ·
B1 the downstream bind predicate: the pack's rebind refuses a backup script whose first `--scope` mention lacks `'century'` within 200 characters.
"""
import ast
import copy
import importlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import smalltest_backup_scope_support as support  # noqa: E402
from test_backup_v5_small_test_scoped import receipt_and_archive, write_evidence  # noqa: E402,F401  (fixture + helper of the small-test suite)

SCRIPTS = support.SCRIPTS
FLEET = support.ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'
KERNEL = support.SIDECAR / 'services/gochara_kernel'
# the J5S pack's own derivation of the verification_seal digest (PACK/verify/derive_scope.py over the same constants): an independent computation of the same rule
# Re-derived after merging main (P06b added ka_gochara_near_miss_verification to VERIFIER_WRITE_TABLES): sha256 of the canonical JSON {schema, name, sorted tables} computed by hand, not by the repo's scope_digest.
PACK_VERIFICATION_SEAL_DIGEST = 'd20d37b36dad2c7707379415a3981dc434caf85bf952f2bb43546fe392fca7ad'


@pytest.fixture
def backup():
    return importlib.import_module('backup_v5_small_test_job')


@pytest.fixture
def shared():
    return importlib.import_module('v5_small_test_shared')


def scope_doc(name):
    return json.loads((SCRIPTS / {'small_test': 'backup_v5_small_test_scope.json', 'century': 'backup_v5_century_scope.json',
                                  'verification_seal': 'backup_v5_verification_seal_scope.json'}[name]).read_text())


# ---- S1: the century scope covers every table the century code can write -----------------------------------------------------

def test_every_write_target_of_the_century_code_is_in_the_century_scope():
    century_modules = [SCRIPTS / 'dispatch_v5_century_job.py', FLEET / 'century_launch.py']
    sites = support.write_sites([*support.scanned_files(), *century_modules])
    assert sites                                                                                   # the scan is not vacuous
    assert support.uncovered_targets(sites, scope_doc('century')) == []


def test_century_scope_detector_reads_false_for_a_write_the_scope_does_not_list(tmp_path):
    planted = tmp_path / 'planted.py'
    planted.write_text('def f(cur):\n    cur.execute("INSERT INTO public.century_only_table (a) VALUES (1)")\n'
                       '    cur.execute("insert into ka_gochara_sky_event (a) values (1)")   # in scope: not flagged\n')
    bad = support.uncovered_targets(support.write_sites([planted]), scope_doc('century'))
    assert bad == ['century_only_table']


# ---- V1/V2: the verification_seal scope is the declared, enforced write surface ---------------------------------------------

def sealer_allowed(seal_flow: Path) -> set[str]:
    """SEALER_WRITE_ALLOWED as written in the source: a frozenset of "INSERT on <t>" / "UPDATE(<col>) on <t>" strings."""
    for node in ast.parse(seal_flow.read_text()).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'SEALER_WRITE_ALLOWED':
            return set(ast.literal_eval(node.value.args[0]))
    raise AssertionError('SEALER_WRITE_ALLOWED not found')


def derived_verification_seal_tables(verification_job: Path, seal_flow: Path) -> set[str]:
    """What the code itself allows the two principals to write: VERIFIER_WRITE_TABLES, and the table of each grant in SEALER_WRITE_ALLOWED."""
    verifier = support.eval_constant([verification_job], 'VERIFIER_WRITE_TABLES')
    sealer = {grant.rsplit(' on ', 1)[1] for grant in sealer_allowed(seal_flow)}
    return {f'public.{t}' for t in verifier} | {f'public.{t}' for t in sealer}


def test_v1_the_verification_seal_scope_is_the_declared_write_surface_of_the_verifier_and_the_sealer():
    derived = derived_verification_seal_tables(KERNEL / 'verification_job.py', KERNEL / 'seal_flow.py')
    scope = scope_doc('verification_seal')
    assert derived == {e['table'] for e in scope['written']}
    assert derived == {'public.ka_gochara_eval_window_verification', 'public.ka_gochara_generation_seal', 'public.ka_gochara_seal_approval',
                       'public.ka_gochara_seal_brief', 'public.ka_gochara_search_inventory_verification', 'public.kala_gochara_publication',
                       'public.ka_gochara_near_miss_verification'}    # P06b (main, migration 1381): VERIFIER_WRITE_TABLES gained the near-miss verification table
    assert [e['table'] for e in scope['context']] == ['public._migrations_applied']
    # separation: the verifier's tables and the builder's never overlap, except the publication row the SEALER (another login) updates
    builder = {f'public.{t}' for t in support.eval_constant([KERNEL / 'verification_job.py'], 'BUILDER_TABLES')}
    verifier_only = {f'public.{t}' for t in support.eval_constant([KERNEL / 'verification_job.py'], 'VERIFIER_WRITE_TABLES')}
    assert not (builder & verifier_only)
    assert set(scope['builder_tables_verifier_must_not_write']) == {t.split('.', 1)[1] for t in builder}


def test_v1_detector_reads_false_when_a_declared_write_surface_gains_a_table(tmp_path):
    seal = tmp_path / 'seal_flow.py'
    seal.write_text((KERNEL / 'seal_flow.py').read_text().replace('"INSERT on ka_gochara_seal_approval",', '"INSERT on ka_gochara_seal_approval", "INSERT on ka_gochara_new_receipt",', 1))
    verification = tmp_path / 'verification_job.py'
    verification.write_text((KERNEL / 'verification_job.py').read_text().replace('("ka_gochara_seal_brief", "ka_gochara_near_miss_verification")', '("ka_gochara_seal_brief", "ka_gochara_near_miss_verification", "ka_gochara_extra")', 1))
    assert 'ka_gochara_extra' in verification.read_text()                                                   # the plant landed on main's real VERIFIER_WRITE_TABLES text
    planted = derived_verification_seal_tables(verification, seal)
    real = {e['table'] for e in scope_doc('verification_seal')['written']}
    assert planted - real == {'public.ka_gochara_new_receipt', 'public.ka_gochara_extra'}


def test_v2_every_write_statement_of_the_verification_and_sealing_modules_targets_a_scope_table():
    modules = [KERNEL / name for name in ('verification_job.py', 'seal_flow.py', 'seal_brief.py', 'inventory_verifier.py', 'window_verifier.py', 'record_verifier.py',
                                          'near_miss_verifier.py', 'input_vector_verifier.py')]
    sites = [s for s in support.write_sites(modules)]
    gate = [s for s in support.write_sites([KERNEL / 'window_gate.py']) if s['function'] == 'record_verification']      # the one persisting function of the window gate
    written = {e['table'].split('.', 1)[1] for e in scope_doc('verification_seal')['written']}
    targets = {s['table'] for s in sites + gate}
    assert {'ka_gochara_seal_approval', 'ka_gochara_seal_brief', 'ka_gochara_search_inventory_verification', 'ka_gochara_eval_window_verification'} <= targets    # not vacuous
    assert targets <= written, targets - written


# ---- P1: pinned digests ----------------------------------------------------------------------------------------------------

def test_p1_the_policy_pins_each_reviewed_scope_digest_and_the_digest_covers_the_name(backup, shared):
    pins = shared.SCOPED_BACKUP_SCOPE_SHA256S
    assert set(pins) == {'small_test', 'century', 'verification_seal'}
    for name, digest in pins.items():
        assert backup.load_scope(name=name)['sha256'] == digest, name
    assert pins['small_test'] == shared.SCOPED_BACKUP_SCOPE_SHA256                                          # the J-2a name still means the small-test scope
    assert len(set(pins.values())) == 3
    assert pins['verification_seal'] == PACK_VERIFICATION_SEAL_DIGEST
    century, small = backup.load_scope(name='century'), backup.load_scope(name='small_test')
    assert century['tables'] == small['tables'] and century['sha256'] != small['sha256']                     # same tables, another scope: the name is part of the digest


def test_p1_the_digest_is_over_schema_name_and_the_sorted_table_list_only(backup):
    tables = backup.load_scope(name='verification_seal')['tables']
    assert backup.scope_digest('verification_seal', tables) == PACK_VERIFICATION_SEAL_DIGEST
    assert backup.scope_digest('verification_seal', list(reversed(tables))) == PACK_VERIFICATION_SEAL_DIGEST
    assert backup.scope_digest('century', tables) != PACK_VERIFICATION_SEAL_DIGEST
    assert backup.scope_digest('verification_seal', tables + ['public.one_more']) != PACK_VERIFICATION_SEAL_DIGEST


# ---- P2: a proof of one scope never admits a dispatch of another -------------------------------------------------------------

@pytest.mark.parametrize('proof_scope', ['small_test', 'century', 'verification_seal'])
@pytest.mark.parametrize('dispatch_scope', ['small_test', 'century', 'verification_seal'])
def test_p2_a_scoped_proof_admits_only_a_dispatch_of_its_own_scope(shared, tmp_path, proof_scope, dispatch_scope):
    req = write_evidence(tmp_path, shared, scope_sha=shared.SCOPED_BACKUP_SCOPE_SHA256S[proof_scope])
    if proof_scope == dispatch_scope:
        assert shared.scoped_backup_problem(req, tmp_path, scope=dispatch_scope) is None
    else:
        with pytest.raises(shared.Refused, match='scope other than the reviewed'):
            shared.scoped_backup_problem(req, tmp_path, scope=dispatch_scope)


def test_p2_a_century_dispatch_demands_the_century_scopes_proof_and_the_default_stays_small_test(shared, tmp_path, monkeypatch):
    monkeypatch.setattr(shared, 'absence_evidence', lambda req, root: None)
    monkeypatch.setattr(shared, 'century_dryrun_evidence', lambda req, root, digest=None: None)
    base = {'kind': 'century_dispatch', 'item_id': shared.CENTURY_ITEM, 'args': {'classes': 'all', 'final_rules': 'true', 'defer_in_build_verify': 'true',
                                                                                            'horizon': '2001-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00'}}   # synthetic bounds (F-CHANNEL: the four exact args)
    (tmp_path / 'small').mkdir()
    (tmp_path / 'century').mkdir()
    small = write_evidence(tmp_path / 'small', shared, label='p02_small')
    century = write_evidence(tmp_path / 'century', shared, label='p02_century', scope_sha=shared.SCOPED_BACKUP_SCOPE_SHA256S['century'])
    assert shared.century_request_problem({**base, **small}, tmp_path / 'small') == 'scoped backup covers a scope other than the reviewed one'
    assert shared.century_request_problem({**base, **century}, tmp_path / 'century') is None
    with pytest.raises(shared.Refused, match='scope other than the reviewed'):
        shared.scoped_backup_problem(century, tmp_path / 'century')                                          # no `scope=`: the small-test default, as every earlier caller


# ---- L1: scope selection ------------------------------------------------------------------------------------------------------

def test_l1_load_scope_reads_the_named_scopes_file_and_refuses_what_it_cannot_vouch_for(backup, tmp_path, monkeypatch):
    for name in ('small_test', 'century', 'verification_seal'):
        assert backup.load_scope(name=name)['name'] == name
    assert backup.load_scope(SCRIPTS / 'backup_v5_century_scope.json')['name'] == 'century'                  # a path override keeps the name inside the file (the pack's rebind loads it so)
    with pytest.raises(backup.BackupRefused):
        backup.load_scope(name='nonexistent')
    renamed = copy.deepcopy(scope_doc('century'))
    renamed['name'] = 'someone_elses_scope'
    (tmp_path / 'renamed.json').write_text(json.dumps(renamed))
    with pytest.raises(backup.BackupRefused, match='missing or malformed'):
        backup.load_scope(tmp_path / 'renamed.json')
    monkeypatch.setitem(backup.SCOPE_PATHS, 'century', SCRIPTS / 'backup_v5_small_test_scope.json')         # the century name pointed at the small-test file
    with pytest.raises(backup.BackupRefused, match='missing or malformed'):
        backup.load_scope(name='century')


# ---- R1: a capture of one scope is not another's; the names reach the mechanism ------------------------------------------------

@pytest.mark.parametrize('other', ['century', 'verification_seal'])
def test_r1_a_capture_receipt_is_valid_only_as_the_scope_it_was_taken_for(backup, receipt_and_archive, other):
    receipt, archive = receipt_and_archive                                                                   # a small_test capture
    assert backup.validate_scoped_capture(receipt, archive, 'p02_fixture') == receipt['measurements']
    assert backup.validate_scoped_capture(receipt, archive, 'p02_fixture', 'small_test') == receipt['measurements']
    with pytest.raises(backup.BackupRefused, match='capture scope differs from the reviewed scope'):
        backup.validate_scoped_capture(receipt, archive, 'p02_fixture', other)


@pytest.mark.parametrize('name', ['small_test', 'century', 'verification_seal'])
def test_r1_every_scope_name_reaches_the_scoped_capture_and_restore(backup, tmp_path, monkeypatch, name):
    seen = []
    monkeypatch.setattr(backup, 'snapshot_scoped', lambda folder, label, scope_name='small_test': seen.append(('snapshot', scope_name)) or {})
    monkeypatch.setattr(backup, 'restore_verify_scoped', lambda folder, label, receipt, scope_name='small_test': seen.append(('restore', scope_name)) or {})
    backup.snapshot(tmp_path / 'f', 'p02_x', name)
    (tmp_path / 'f').mkdir()
    (tmp_path / 'f' / 'capture.json').write_text(json.dumps({'schema': 'ky.smalltest_backup/2'}))
    backup.restore_verify(tmp_path / 'f', 'p02_x', name)
    assert seen == [('snapshot', name), ('restore', name)]


def test_r1_the_cli_offers_exactly_the_three_scopes_and_plans_the_chosen_digest(backup, shared, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    for name in ('small_test', 'century', 'verification_seal'):
        assert backup.main(['--operation', 'snapshot', '--label', 'p02_plan', '--scope', name, '--dry-run']) == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan['scope'] == name and plan['scope_sha256'] == shared.SCOPED_BACKUP_SCOPE_SHA256S[name]
    with pytest.raises(SystemExit) as caught:
        backup.main(['--operation', 'snapshot', '--label', 'p02_plan', '--scope', 'verification', '--dry-run'])
    assert caught.value.code == 2
    assert list(tmp_path.iterdir()) == []                                                                    # a plan touches nothing


def test_r1_the_executor_table_still_lets_a_backup_request_carry_only_a_label_and_a_scope():
    ops = json.loads((FLEET / 'executor_ops.json').read_text())['ops']
    for kind in ('backup_snapshot', 'backup_restore_verify'):
        assert ops[kind]['allowed_args'] == ['label', 'scope'], kind


# ---- B1: the downstream bind predicate -----------------------------------------------------------------------------------------

def test_b1_the_backup_script_offers_century_where_the_packs_rebind_looks_for_it():
    text = (SCRIPTS / 'backup_v5_small_test_job.py').read_text()
    assert "'century'" in text.split('--scope', 1)[1][:200]                                                  # PACK/century/rebind_pins.py: the check that refuses a main without --scope century
    assert "'verification_seal'" in text.split('--scope', 1)[1][:200]
