"""SR-RESUME-NOW (ruling madhav-f9 lane 2; standing owner requirement OWNER-RESUMABLE-REQUIRED-20261025, "resumable substeps for heavy assets"): the absence gate of
`century_resume`, in v5_small_test_shared.py. A century_dispatch admits only a generation '5.0' independently ABSENT; a century_resume admits a PARTLY present chain,
and only a ledger-attested one.

One doctrine-grounded oracle per distinct production claim (owner decision D-OWNER-TESTS-20261016; root CLAUDE.md §N.8: a signal is computed by a detector that can read
false; §B.10: nothing here invents a value). Each oracle passes on the real module and FAILS on a copy of it with that ONE claim's line reverted (the planted reversion). The
ledger table and its columns are the WRITER lane's (migration 1410): the names the gate reads are the RESUME_* constants of the module, stated in the job result.

  A1 a century_dispatch still refuses a partly present chain (every absence count must be zero: unchanged)
  A2 a century_resume admits a partly present chain exactly when the ledger attests it
  A3 a row no committed substep accounts for refuses, naming its table
  A4 a ledger that accounts for more rows than are present (a deleted row) refuses, naming the table
  A5 a ledger whose program identity differs from the request's refuses, naming the field (a resume continues only the same program)
  A6 no ledger refuses: with a chain present, and with nothing to resume
  A7 verification rows (the verifier started) refuse
  A8 a substep committed by an execution outside the resumed lineage refuses; a resume of a resume follows its lineage back to the dispatch
  A9 the readback must be the measured output: an acceptance that says anything else refuses
  A10 the request binds the run it resumes (resume_run_id) to the cited launch receipt, and cites only a COMPLETED launch of a century dispatch or resume
  A11 the readback must follow the launch it resumes
  A12 the one manifest must be a candidate
  A13 the readback query reads exactly the ledger columns and census tables the gate consumes (against the REAL migration-1410 table: test_century_resume_ledger_schema.py)
  A14 a ledger whose substeps are not 0..n-1 (not a prefix of the plan) refuses
  A15 a ledger row's scope digest must be the digest of its scope (a changed scope under an old digest refuses); a chain-owning substep with no scope refuses, a global one is honest null
  A16 the ledger's manifest binding is whole (manifest and vector together), one manifest, and the live candidate
  A17 contacts and near-miss rows no record substep can account for refuse; once a record substep is ledgered they are not equated (build_ledger HONEST LIMITS)
  A18 a substep committed by a RUN outside the resumed lineage refuses (the producer list of the generation)
  A19 a fresh century dispatch refuses a leftover ledger BY NAME (SR-RESUME-INTEGRATION: the ledger is in the century absence census at 0)
  A20 the century absence census must COUNT the ledger: a readback without it is incomplete (other lifecycles keep their census)
  A21 the absence readback SQL counts the ledger for a century lifecycle (explicitly, or after a committed century teardown) and for no other
The ledger table, its columns and the shapes of `scope` are migration 1410's (the WRITER lane's): test_century_resume_ledger_schema.py parses the migration itself.
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest

import century_resume_support as S
import v5_small_test_shared as shared

SRC = Path(shared.__file__)
CLUSTER = os.environ.get('KALA_ADMIN_DSN', 'postgresql://postgres@127.0.0.1:55433/postgres')


def module_with(tmp_path, mutation=None):
    """The gate module, or a copy of it with ONE line reverted (the planted reversion)."""
    text = SRC.read_text()
    if mutation:
        old, new = mutation
        if text.count(old) != 1:
            raise RuntimeError(f'mutation anchor not unique: {old!r}')      # a bad anchor must never read as a failed oracle
        text = text.replace(old, new)
    path = tmp_path / f'v5_small_test_shared_{abs(hash(mutation))}.py'
    path.write_text(text)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def judged(module, root, req):
    return module.century_request_problem(req, Path(root))


def ops(tmp_path, name='ops'):
    root = tmp_path / name
    root.mkdir()
    return root


# ───────────────────────────── A1 / A2 ─────────────────────────────
def oracle_a1_dispatch_still_refuses_a_partly_present_chain(module, tmp_path):
    clean = ops(tmp_path, 'clean')
    zero = S.absence(clean)
    assert module.absence_evidence(dict(zero, kind='century_dispatch'), clean)['counts']['ka_gochara_contact'] == 0, 'control failed — an all-zero baseline absence is admitted'
    for table in ('ka_gochara_contact', 'ka_gochara_eval_window', 'kala_gochara_publication'):
        root = ops(tmp_path, 'partial-' + table)
        req = dict(S.absence(root, counts_over={table: 3}), kind='century_dispatch', item_id='J-4e', args=dict(S.ARGS))
        try:
            module.absence_evidence(req, root)
        except module.Refused as refusal:
            assert 'independent absence' in str(refusal), refusal
        else:
            raise AssertionError(f'a dispatch with {table} rows present was not refused')
        assert 'independent absence' in judged(module, root, req), table
    root = ops(tmp_path, 'cross')                                       # a resume's attested readback is no absence proof for a dispatch
    resume = S.scenario(root)
    swapped = dict(kind='century_dispatch', absence_receipt=resume['resume_receipt'], absence_acceptance=resume['resume_acceptance'])
    try:
        module.absence_evidence(swapped, root)
    except module.Refused:
        pass
    else:
        raise AssertionError('a resume readback was accepted as a dispatch absence proof')


def oracle_a2_a_ledger_attested_partial_chain_is_admitted(module, tmp_path):
    root = ops(tmp_path)
    assert judged(module, root, S.scenario(root)) is None


# ───────────────────────────── A3 / A4 ─────────────────────────────
def oracle_a3_an_unattested_row_refuses_naming_its_table(module, tmp_path):
    for table in ('ka_gochara_search_inventory', 'ka_gochara_eval_window', 'ka_gochara_eval_window_record'):
        root = ops(tmp_path, 'extra-' + table)
        census = S.census_of(S.ledger_rows())
        census[table] += 1
        problem = judged(module, root, S.scenario(root, census=census))
        assert problem and f'unattested rows in {table}' in problem, (table, problem)


def oracle_a4_a_ledger_accounting_for_more_than_is_present_refuses(module, tmp_path):
    root = ops(tmp_path)
    census = S.census_of(S.ledger_rows())
    census['ka_gochara_eval_window'] -= 1
    problem = judged(module, root, S.scenario(root, census=census))
    assert problem and 'accounts for more rows in ka_gochara_eval_window' in problem, problem


# ───────────────────────────── A5 ─────────────────────────────
def oracle_a5_a_different_program_identity_refuses(module, tmp_path):
    for field, other in (('writer_digest', '1' * 64), ('implementation_digest', '2' * 64), ('plan_digest', '3' * 64), ('horizon', '1999-01-01T00:00:00+00:00,2084-02-05T00:00:00+00:00')):
        root = ops(tmp_path, 'identity-' + field)
        problem = judged(module, root, S.scenario(root, request_identity=dict(S.IDENTITY, **{field: other}), **({'args': dict(S.ARGS, horizon=other)} if field == 'horizon' else {})))
        assert problem and field in problem, (field, problem)
    root = ops(tmp_path, 'mixed')                                       # one substep committed by another program than the rest
    rows = S.ledger_rows()
    rows[3] = dict(rows[3], writer_digest='9' * 64)
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'writer_digest of substep inventory:career' in problem, problem


# ───────────────────────────── A6 / A7 ─────────────────────────────
def oracle_a6_no_ledger_refuses(module, tmp_path):
    root = ops(tmp_path, 'chain-no-ledger')                             # rows present, nothing attests them
    problem = judged(module, root, S.scenario(root, rows=[], census=S.census_of(S.ledger_rows())))
    assert problem, 'a chain with no ledger must refuse'
    root = ops(tmp_path, 'nothing')                                     # nothing present and no ledger: there is nothing to resume
    problem = judged(module, root, S.scenario(root, rows=[]))
    assert problem and 'nothing to resume' in problem, problem


def oracle_a7_verification_rows_refuse(module, tmp_path):
    for table in shared.RESUME_NEVER_PRESENT:
        root = ops(tmp_path, 'verified-' + table)
        census = S.census_of(S.ledger_rows())
        census[table] = 1
        problem = judged(module, root, S.scenario(root, census=census))
        assert problem and table in problem and 'verifier started' in problem, (table, problem)


# ───────────────────────────── A8 ─────────────────────────────
def oracle_a8_the_lineage_of_the_resumed_run_is_what_committed_the_substeps(module, tmp_path):
    root = ops(tmp_path, 'foreign')
    foreign = S.ledger_rows()
    foreign[4] = dict(foreign[4], execution_id=S.OTHER_EXECUTION)
    problem = judged(module, root, S.scenario(root, rows=foreign))
    assert problem and 'execution outside the resumed lineage' in problem, problem
    root = ops(tmp_path, 'no-execution')                                # a run outside Cloud Run records no execution id (NULL): its lineage cannot be proved
    nulled = S.ledger_rows()
    nulled[4] = dict(nulled[4], execution_id=None)
    problem = judged(module, root, S.scenario(root, rows=nulled))
    assert problem and 'execution outside the resumed lineage' in problem, problem
    root = ops(tmp_path, 'chain')                                       # dispatch (EXECUTION) -> resume 1 (OTHER_EXECUTION), resuming the run of resume 1
    first = S.launch(root, 'dispatch-1')
    second = S.launch(root, 'resume-1', kind='century_resume', run_id=S.NEW_RUN, execution=S.OTHER_EXECUTION, resumes=first, ts='2026-10-25T02:00:00+00:00')
    rows = S.ledger_rows()                                              # snapshot + inventory by the dispatch, the window by the first resume
    rows[4] = dict(rows[4], execution_id=S.OTHER_EXECUTION, build_run_id=S.NEW_RUN)
    receipt, acceptance = S.readback(root, S.proof_of(rows))
    req = {'operation_id': 'resume-2', 'kind': 'century_resume', 'item_id': 'J-4e', 'args': dict(S.ARGS), 'resumes': second, 'resume_run_id': S.NEW_RUN,
           'program_identity': dict(S.IDENTITY), 'resume_receipt': receipt, 'resume_acceptance': acceptance}
    assert judged(module, root, req) is None, 'control failed — a resume of a resume that follows its lineage is admitted'


# ───────────────────────────── A9 ─────────────────────────────
def oracle_a9_the_readback_must_be_the_measured_output(module, tmp_path):
    root = ops(tmp_path, 'acceptance-says-more')                        # the verifier's acceptance states a different census than the retained output holds
    census = S.census_of(S.ledger_rows())
    said = S.proof_of(S.ledger_rows(), census=dict(census, ka_gochara_contact=4))
    problem = judged(module, root, S.scenario(root, accepted=said))
    assert problem and 'differs from the measured readback output' in problem, problem


# ───────────────────────────── A10 ─────────────────────────────
def oracle_a10_the_request_binds_the_run_it_resumes(module, tmp_path):
    root = ops(tmp_path, 'other-run')
    problem = judged(module, root, S.scenario(root, run_id=S.NEW_RUN))
    assert problem and 'resume_run_id' in problem, problem
    root = ops(tmp_path, 'not-a-launch')                                # a receipt of anything but a COMPLETED century launch resumes nothing
    req = S.scenario(root)
    for status, kind in (('FAILED', 'century_dispatch'), ('COMPLETED', 'century_cancel'), ('COMPLETED', 'measuring_dispatch')):
        req['resumes'] = S.launch(root, 'dispatch-1', kind=kind, status=status)
        problem = judged(module, root, req)
        assert problem and 'COMPLETED launch receipt of a century dispatch or resume' in problem, (status, kind, problem)


# ───────────────────────────── A11 / A12 ─────────────────────────────
def oracle_a11_the_readback_follows_the_launch(module, tmp_path):
    root = ops(tmp_path)
    problem = judged(module, root, S.scenario(root, ts='2026-10-25T00:30:00+00:00'))      # taken before the launch it resumes was recorded
    assert problem and 'must follow the launch' in problem, problem


def oracle_a12_exactly_one_candidate_manifest(module, tmp_path):
    for manifest in ({'count': 1, 'status': 'published'}, {'count': 0, 'status': None}, {'count': 2, 'status': 'candidate'}):
        root = ops(tmp_path, f"manifest-{manifest['count']}-{manifest['status']}")
        problem = judged(module, root, S.scenario(root, manifest=manifest))
        assert problem and 'candidate manifest' in problem, (manifest, problem)


# ───────────────────────────── A14 – A18 (migration 1410 shapes) ─────────────────────────────
def oracle_a14_the_recorded_substeps_are_a_prefix_of_the_plan(module, tmp_path):
    root = ops(tmp_path, 'gap')                      # build_ledger.check_binding: the orchestrator runs the plan in order and stops at the first failure
    rows = S.ledger_rows()
    rows[3] = dict(rows[3], ordinal=7)
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'not a prefix of the plan' in problem, problem


def oracle_a15_a_scope_digest_is_the_digest_of_its_scope(module, tmp_path):
    root = ops(tmp_path, 'changed-scope')            # the scope was edited after its digest was taken
    rows = S.ledger_rows()
    scope = json.loads(json.dumps(rows[3]['scope']))
    scope['tables']['ka_gochara_search_inventory']['rows'] += 1
    rows[3] = dict(rows[3], scope=scope)
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'is not the digest of its scope' in problem, problem
    root = ops(tmp_path, 'chain-without-scope')      # a substep that owns chain rows with a NULL scope attests nothing
    rows = S.ledger_rows()
    rows[3] = dict(rows[3], scope=None, scope_digest=None)
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'owns chain rows but carries no scope' in problem, problem
    root = ops(tmp_path, 'half-scope')               # migration 1410 kgbl_scope_ck: a scope and its digest travel together
    rows = S.ledger_rows()
    rows[3] = dict(rows[3], scope_digest=None)
    assert judged(module, root, S.scenario(root, rows=rows)), 'a scope without its digest must refuse'


def oracle_a16_the_ledger_is_bound_to_the_one_live_candidate_manifest(module, tmp_path):
    root = ops(tmp_path, 'other-manifest')           # the live candidate is not the manifest the substeps were bound to
    problem = judged(module, root, S.scenario(root, manifest={'count': 1, 'status': 'candidate', 'manifest_id': '99999999-9999-4999-8999-999999999999'}))
    assert problem and 'not bound to the live candidate manifest' in problem, problem
    root = ops(tmp_path, 'two-manifests')            # two rows bound to different manifests
    rows = S.ledger_rows()
    rows[4] = dict(rows[4], manifest_id='99999999-9999-4999-8999-999999999999')
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'more than one manifest' in problem, problem
    root = ops(tmp_path, 'half-binding')             # migration 1410 kgbl_manifest_binding_ck: a manifest-bound row carries both halves or neither
    rows = S.ledger_rows()
    rows[3] = dict(rows[3], vector_sha256=None)
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'half of a manifest binding' in problem, problem


def oracle_a17_unattributable_rows_need_a_record_substep(module, tmp_path):
    for table in shared.RESUME_UNATTRIBUTED_TABLES:
        root = ops(tmp_path, 'no-record-' + table)   # contacts / near-miss rows are written by a record grain: with none ledgered they are orphans
        census = S.census_of(S.ledger_rows())
        census[table] += 3
        problem = judged(module, root, S.scenario(root, census=census))
        assert problem and f'unattested rows in {table}' in problem and 'no record substep' in problem, (table, problem)
    root = ops(tmp_path, 'with-record')              # once a record grain is ledgered they are not attributable to it, so they are not equated (the writer re-verifies)
    withrecord = S.SUBSTEPS + (('record:career:p1', {'ka_gochara_relationship_record': 4, 'ka_gochara_record_prerequisite': 2,
                                                       'ka_gochara_contact (referenced by the grain\'s records)': 6}),)
    rows = S.ledger_rows(substeps=withrecord)
    census = S.census_of(rows)
    census['ka_gochara_contact'] = 9
    census['ka_gochara_near_miss'] = 2
    assert judged(module, root, S.scenario(root, rows=rows, census=census)) is None, 'control failed — contacts of a ledgered record grain are admitted'


def oracle_a18_the_producing_run_is_in_the_resumed_lineage(module, tmp_path):
    root = ops(tmp_path, 'foreign-run')
    rows = S.ledger_rows()
    rows[3] = dict(rows[3], build_run_id=S.NEW_RUN)  # a run the cited launch lineage does not contain
    problem = judged(module, root, S.scenario(root, rows=rows))
    assert problem and 'run outside the resumed lineage' in problem, problem


# ───────────────────────────── A19 – A21 the ledger in the century absence census ─────────────────────────────
def century_dispatch_request(root, **counts_over):
    return dict(S.absence(root, counts_over=counts_over), kind='century_dispatch', item_id='J-4e', args=dict(S.ARGS))


def oracle_a19_a_leftover_ledger_refuses_a_fresh_century_dispatch(module, tmp_path):
    root = ops(tmp_path, 'clean')
    assert judged(module, root, century_dispatch_request(root)) is None or 'ledger' not in judged(module, root, century_dispatch_request(root)), 'control failed — a zero ledger is not what refuses'
    assert module.absence_evidence(century_dispatch_request(root), root)['counts'][module.LEDGER_ABSENCE_TABLE] == 0
    root = ops(tmp_path, 'leftover')
    req = century_dispatch_request(root, **{module.LEDGER_ABSENCE_TABLE: 2})
    for problem in (judged(module, root, req), judged(module, root, dict(req, kind='century_dispatch_dryrun'))):
        assert problem and 'committed-substep ledger rows exist' in problem and module.LEDGER_ABSENCE_TABLE + ': 2' in problem and 'century_resume' in problem, problem


def oracle_a20_the_century_census_must_count_the_ledger(module, tmp_path):
    root = ops(tmp_path, 'legacy-census')            # an accepted readback taken without the ledger count (the census before migration 1410)
    old = S.absence(root, drop=(module.LEDGER_ABSENCE_TABLE,))
    assert module.absence_evidence(dict(old, kind='smalltest_dispatch'), root)['counts'], 'control failed — another lifecycle keeps its census'
    try:
        module.absence_evidence(dict(old, kind='century_dispatch'), root)
    except module.Refused as refusal:
        assert 'census is incomplete' in str(refusal), refusal
    else:
        raise AssertionError('a century census that does not count the ledger was admitted')


def oracle_a21_the_absence_readback_counts_the_ledger_for_a_century_lifecycle(module, tmp_path):
    counted = f"'{module.LEDGER_ABSENCE_TABLE}', (SELECT count(*) FROM {module.LEDGER_ABSENCE_TABLE} WHERE chart_id = '{shared.CHART_ID}'::uuid AND generation = '5.0')"
    assert counted in module.absence_readback_sql(century=True)
    committed = {'kind': 'century_teardown', 'teardown': {'scope': {'run_id': S.RUN}}, 'request_sha256': 'a' * 64, 'operation_id': 'td'}
    teardown_scope = dict(committed['teardown'], scope_sha256='b' * 64, rowset_sha256='c' * 64)
    assert counted in module.absence_readback_sql(dict(committed, teardown=teardown_scope)), 'after a committed century teardown the census counts the ledger too'
    assert module.LEDGER_ABSENCE_TABLE not in module.absence_readback_sql(), 'another lifecycle: its census is byte for byte what it was'
    assert module.LEDGER_ABSENCE_TABLE not in module.absence_readback_sql(dict(committed, kind='smalltest_teardown', teardown=teardown_scope))


# claim -> (oracle, the ONE planted reversion of v5_small_test_shared.py that must make it fail)
ORACLES = {
    'a1': (oracle_a1_dispatch_still_refuses_a_partly_present_chain,
           ("            or any(type(n) is not int or n != 0 for n in p['counts'].values())):", '            ):')),
    'a2': (oracle_a2_a_ledger_attested_partial_chain_is_admitted, ('\n            resume_evidence(req, root)\n', '\n            absence_evidence(req, root)\n')),
    'a3': (oracle_a3_an_unattested_row_refuses_naming_its_table, ('        if present > attested[table]:\n', '        if False:\n')),
    'a4': (oracle_a4_a_ledger_accounting_for_more_than_is_present_refuses, ('        if present < attested[table]:\n', '        if False:\n')),
    'a5': (oracle_a5_a_different_program_identity_refuses, ('            if not same:\n', '            if False:\n')),
    'a6': (oracle_a6_no_ledger_refuses, ('    if not isinstance(rows, list) or not rows:\n', '    if not isinstance(rows, list):\n')),
    'a7': (oracle_a7_verification_rows_refuse, ("        if census[table]:\n            raise Refused('verification rows exist in '", "        if False:\n            raise Refused('verification rows exist in '")),
    'a8': (oracle_a8_the_lineage_of_the_resumed_run_is_what_committed_the_substeps, ("        if row['execution_id'] not in executions:\n", '        if False:\n')),
    'a9': (oracle_a9_the_readback_must_be_the_measured_output,
           ("    if measured != {k: v for k, v in p.items() if k != 'output_sha256'} or p.get('output_sha256') != r['output_sha256']:\n", '    if False:\n')),
    'a10': (oracle_a10_the_request_binds_the_run_it_resumes, ("    if (prior.get('launch') or {}).get('run_id') != req.get('resume_run_id'):\n", '    if False:\n')),
    'a11': (oracle_a11_the_readback_follows_the_launch, ("        if datetime.fromisoformat(r['ts']) <= datetime.fromisoformat(prior['ts']):\n", '        if False:\n')),
    'a12': (oracle_a12_exactly_one_candidate_manifest, ("manifest.get('count') != 1 or manifest.get('status') != 'candidate'", 'False')),
    'a14': (oracle_a14_the_recorded_substeps_are_a_prefix_of_the_plan, ("    if sorted(ordinals) != list(range(len(rows))):\n", '    if False:\n')),
    'a15': (oracle_a15_a_scope_digest_is_the_digest_of_its_scope, ("        if hashlib.sha256(canonical.encode('utf-8')).hexdigest() != scope_digest:\n", '        if False:\n')),
    'a16': (oracle_a16_the_ledger_is_bound_to_the_one_live_candidate_manifest, ("    if not bound or next(iter(bound))[0] != manifest.get('manifest_id'):\n", '    if False:\n')),
    'a17': (oracle_a17_unattributable_rows_need_a_record_substep, ("            if census[table]:\n                raise Refused('unattested rows in ' + table + ': ' + str(census[table]) + ' present and no record", "            if False:\n                raise Refused('unattested rows in ' + table + ': ' + str(census[table]) + ' present and no record")),
    'a18': (oracle_a18_the_producing_run_is_in_the_resumed_lineage, ("        if row['build_run_id'] not in lineage_runs:\n", '        if False:\n')),
    'a19': (oracle_a19_a_leftover_ledger_refuses_a_fresh_century_dispatch,
            ("    if century and isinstance(p.get('counts'), dict) and type(p['counts'].get(LEDGER_ABSENCE_TABLE)) is int and p['counts'][LEDGER_ABSENCE_TABLE] != 0:\n", '    if False:\n')),
    'a20': (oracle_a20_the_century_census_must_count_the_ledger, ("        required = required | {LEDGER_ABSENCE_TABLE}\n", '        pass\n')),
    'a21': (oracle_a21_the_absence_readback_counts_the_ledger_for_a_century_lifecycle, (' + (((LEDGER_ABSENCE_TABLE, ""),) if century else ())}', '}')),
}
# the lineage walk is its own claim (A8, second half): a resume of a resume is only admitted because the walk reaches back to the original dispatch
LINEAGE_REVERSION = ("        if prior['kind'] == 'century_dispatch':\n            return executions, runs\n", '        if True:\n            return executions, runs\n')


@pytest.mark.parametrize('claim', sorted(ORACLES))
def test_oracle_passes_on_the_real_gate(tmp_path, claim):
    ORACLES[claim][0](module_with(tmp_path), tmp_path)


@pytest.mark.parametrize('claim', sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, claim):
    oracle, mutation = ORACLES[claim]
    with pytest.raises(AssertionError):
        oracle(module_with(tmp_path, mutation), tmp_path)


def test_a8_a_resume_of_a_resume_needs_the_lineage_walk(tmp_path):
    with pytest.raises(AssertionError):
        oracle_a8_the_lineage_of_the_resumed_run_is_what_committed_the_substeps(module_with(tmp_path, LINEAGE_REVERSION), tmp_path)


def test_a8_a_lineage_hop_must_be_the_request_its_receipt_bound(tmp_path):
    root = ops(tmp_path)
    first = S.launch(root, 'dispatch-1')
    second = S.launch(root, 'resume-1', kind='century_resume', run_id=S.NEW_RUN, execution=S.OTHER_EXECUTION, resumes=first, ts='2026-10-25T02:00:00+00:00')
    archived = root / 'done' / 'resume-1.json'
    request = json.loads(archived.read_text())
    request['resumes'] = {'name': 'elsewhere.json', 'sha256': '0' * 64}      # an archived request that is not the one the receipt bound
    archived.write_text(json.dumps(request, sort_keys=True))
    receipt, acceptance = S.readback(root, S.proof_of(S.ledger_rows()))
    req = {'operation_id': 'resume-2', 'kind': 'century_resume', 'item_id': 'J-4e', 'args': dict(S.ARGS), 'resumes': second, 'resume_run_id': S.NEW_RUN,
           'program_identity': dict(S.IDENTITY), 'resume_receipt': receipt, 'resume_acceptance': acceptance}
    problem = judged(shared, root, req)
    assert problem and 'is not the request its receipt bound' in problem, problem


# ───────────────────────────── shape checks that carry no reversion of their own ─────────────────────────────
def test_the_request_names_exactly_the_identity_fields_and_a_matching_horizon(tmp_path):
    root = ops(tmp_path, 'a')
    short = S.scenario(root, request_identity={k: v for k, v in S.IDENTITY.items() if k != 'plan_digest'})
    assert 'program_identity must name exactly' in judged(shared, root, short)
    root = ops(tmp_path, 'b')
    assert 'must be 64 lowercase hex' in judged(shared, root, S.scenario(root, request_identity=dict(S.IDENTITY, writer_digest='nothex')))
    root = ops(tmp_path, 'c')                                           # the request's horizon is the request args' horizon (the executor binds those to the contract)
    assert 'differs from the request horizon' in judged(shared, root, S.scenario(root, request_identity=dict(S.IDENTITY, horizon='1999-01-01T00:00:00+00:00,2084-02-05T00:00:00+00:00')))
    root = ops(tmp_path, 'd')
    assert 'century resume belongs to J-4e' in judged(shared, root, S.scenario(root, item_id='J-4d'))


def test_a_ledger_row_with_a_malformed_count_refuses(tmp_path):
    bad_scope = json.loads(json.dumps(S.ledger_rows()[3]['scope']))
    bad_scope['tables']['ka_gochara_search_inventory']['rows'] = -1
    foreign_table = json.loads(json.dumps(S.ledger_rows()[3]['scope']))
    foreign_table['tables']['some_other_table'] = {'rows': 1, 'digest': 'f' * 64}
    for broken in ({'rows_written': -1}, {'ordinal': True}, {'scope_digest': 'short'}, {'scope': {'schema': 'other/1', 'tables': {}}},
                   {'scope': bad_scope, 'scope_digest': S.scope_of({})[1] or 'x'}, {'scope': foreign_table}, {'vector_sha256': 'nothex'}):
        root = ops(tmp_path, 'bad-' + str(abs(hash(json.dumps(broken, sort_keys=True, default=str)))))
        rows = S.ledger_rows()
        rows[3] = dict(rows[3], **broken)
        assert judged(shared, root, S.scenario(root, rows=rows)), broken
    root = ops(tmp_path, 'dup')
    rows = S.ledger_rows()
    rows[1] = dict(rows[1], substep_key=rows[0]['substep_key'])
    assert 'duplicated' in judged(shared, root, S.scenario(root, rows=rows))


def test_a_century_resume_launch_counts_as_a_launch_of_the_lifecycle():
    assert 'century_resume' in shared.DISPATCH_KINDS      # a later dispatch needs its own teardown and independent absence after a resume's launch too


# ───────────────────────────── A13 the readback query ─────────────────────────────
def test_a13_the_readback_query_reads_what_the_gate_consumes():
    sql = shared.resume_readback_sql()
    assert sql.startswith('SELECT (') and sql.endswith('AS resume_proof') and ';' not in sql
    assert shared.RESUME_LEDGER_TABLE in sql
    for column in shared.RESUME_LEDGER_COLUMNS:
        assert f"'{column}', l.{column}" in sql, column
    assert "'horizon', jsonb_build_array(lower(l.horizon), upper(l.horizon))" in sql       # a tstzrange is read as [lower, upper], not as range text
    for table in shared.RESUME_CHAIN_TABLES + shared.RESUME_NEVER_PRESENT:
        assert f"'{table}', (SELECT count(*) FROM {table} WHERE chart_id = '{shared.CHART_ID}'::uuid AND generation = '5.0'" in sql, table
    assert "partition_kind = 'event_class'" in sql      # the coverage census keeps its absence-census filter
    assert "FROM kala_gochara_publication" in sql and shared.CHART_ID in sql
