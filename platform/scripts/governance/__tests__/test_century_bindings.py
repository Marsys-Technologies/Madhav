"""Offline century authority proofs (SR-PREBUILD-ALL / SR-TEARDOWN-AUTHORITY-GATE items 2 and 3); auto-discovered by governance CI shards.

The century launch is the measuring launch minus the test slice (ordinary, sealable candidate; item J-4e). Every claim below is stated in the
ruling or in the measuring contract it is derived from (J-3c: MEASURING_BUILD_CONTRACT_v1_0 MB-4.1, J3C_BINDINGS_PREBUILD_v1_0), and each oracle
fails on its one planted reversion (the table at the end of the PR lists them). No cloud, Git writes, DB connections or chart computations; the
evidence files are synthetic transport data, never operational acceptance. The real-database teardown oracles are in
platform/python-sidecar/tests/l3/gochara/test_century_teardown_db.py and test_century_staging_db.py.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
FLEET = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'
SCRIPTS = ROOT / 'platform/scripts'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / '__tests__'))
sys.path.insert(0, str(FLEET))
import v5_small_test_shared as shared
import smalltest_safety_support as S

# F-CHANNEL (SR-W34-PREP-RULINGS 1): the century request carries the rule profile, the verify-deferral switch and the horizon. SYNTHETIC bounds only —
# the real D-G9 horizon is life-event derived and appears in no code, test or commit text.
HORIZON = '2001-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00'
# OD-1 (SR-OD1-NUMERICAL): the fifth required value is the numeric-result policy the century build is bound under.
ARGS = {'classes': 'all', 'final_rules': 'true', 'defer_in_build_verify': 'false', 'horizon': HORIZON, 'result_policy': 'window_qualification/1'}


def load(name):
    path = FLEET / (name + '.py')
    spec = importlib.util.spec_from_file_location('century_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def staging_proof(manifest=None, **over):
    manifest = manifest or dict(chart_id=shared.CHART_ID, scope_target=shared.ASSET_ID)
    proof = dict(schema='ky.century_staging/1', status='ROLLED_BACK', rollback_confirmed=True, operation_id='staging-rollback',
                 request_sha256='b' * 64, args=ARGS, triggered_by=shared.CENTURY_TRIGGERED_BY,
                 plan_manifest=manifest, plan_manifest_digest=shared.evidence_digest(manifest))
    proof.update(over)
    return proof


def dispatch_request(root, *, kind='century_dispatch', with_dryrun=True, proof=None, receipt_kind='century_dispatch_dryrun'):
    req = dict(kind=kind, item_id='J-4e', operation_id='launch', args=dict(ARGS))
    req['absence_receipt'], req['absence_acceptance'] = S.absence_for(root)
    if with_dryrun:
        rr, ar = S.accepted(root, receipt_kind, 'staging-rollback', item_id='J-4e', staging=proof or staging_proof())
        req.update(dryrun_receipt=rr, dryrun_acceptance=ar)
    return S.authorize(root, req)


# ───────────────────────────── the table bindings ─────────────────────────────
def test_century_kinds_sit_in_the_reviewed_executor_policy_paths():
    """Claim: the executor routes every century kind to the century policy (never the small-test or measuring one) and the real kinds are fenced."""
    executor = load('executor')
    assert executor.REMOTE_ASYNC_KINDS >= {'century_dispatch'}
    assert executor.LAUNCH_SCHEMAS['century_dispatch'] == 'ky.century_launch/1'
    assert 'century_teardown' in executor.TEARDOWN_KINDS                      # a committed century teardown waits for its independent absence


# ───────────────────────────── the request gate (reviewed policy) ─────────────────────────────
def policy_executor(monkeypatch, tmp_path):
    executor = load('executor')
    monkeypatch.setattr(executor, 'OPS', tmp_path / 'run/ops')
    namespace = {}
    exec((SCRIPTS / 'v5_small_test_shared.py').read_text(), namespace)
    monkeypatch.setattr(executor, 'smalltest_policy', lambda req: namespace)
    return executor


def test_century_policy_is_routed_from_reviewed_source_and_demands_every_gate(tmp_path, monkeypatch):
    """Claim (J3C gates, SR-PREBUILD-ALL): a real century launch needs the previous lifecycle absent, a scoped backup and a same-manifest staging
    rollback; the staging rollback itself needs only the absence; item, args and kind are exact."""
    executor = policy_executor(monkeypatch, tmp_path)
    req = dispatch_request(tmp_path)
    assert executor.smalltest_policy_problem(req) is None

    def signed(**changes):
        """The request with `changes` (None removes the key), RE-SIGNED: the acceptance binds the whole request, so an unsigned edit would be
        refused for that reason alone and prove nothing about the gate under test."""
        edited = {k: v for k, v in req.items() if k != 'acceptance_receipt'}
        for key, value in changes.items():
            edited.pop(key, None) if value is None else edited.__setitem__(key, value)
        edited['acceptance_receipt'] = req['acceptance_receipt']
        S.put(tmp_path, 'acceptance', edited['operation_id'], dict(result='ACCEPTED', by='v2', operation_id=edited['operation_id'],
              request_sha256=shared.request_hash(edited), reviewed_commit=S.COMMIT, ts='2026-10-15T00:10:00+00:00'))
        return edited

    assert executor.smalltest_policy_problem(signed()) is None                       # the re-signing itself keeps a good request good
    # SR-A12-BACKUP-REMOVAL (supersedes the old J-4e rule "backup_label is mandatory for the real kind"): no dump is taken, so a century_dispatch with no
    # backup_label / backup_restore_sha256 but everything else valid is ADMITTED; the absence and the staging dry run stay mandatory.
    assert executor.smalltest_policy_problem(signed(backup_label=None, backup_restore_sha256=None)) is None
    for gone in (['absence_receipt', 'absence_acceptance'], ['dryrun_receipt', 'dryrun_acceptance']):
        assert executor.smalltest_policy_problem(signed(**{k: None for k in gone})), f'{gone[0]} is mandatory for the real kind'
    assert executor.smalltest_policy_problem(signed(backup_label=None, backup_restore_sha256=None, item_id='J-3c')) == 'century dispatch belongs to J-4e'      # any other defect still refuses
    dry = signed(kind='century_dispatch_dryrun', backup_label=None, backup_restore_sha256=None, dryrun_receipt=None, dryrun_acceptance=None)
    assert executor.smalltest_policy_problem(dry) is None                                        # the rollback needs the absence only
    assert executor.smalltest_policy_problem(signed(kind='century_dispatch_dryrun', absence_receipt=None, absence_acceptance=None, backup_label=None,
                                                    backup_restore_sha256=None, dryrun_receipt=None, dryrun_acceptance=None))      # ...but it does need that
    for args in ({'classes': 'marriage'}, {'classes': 'all', 'horizon-start': '2025-01-01'}, {'run': 'all_classes_full', 'classes': 'all'}, {}):
        assert executor.smalltest_policy_problem(signed(args=args)).startswith('century request requires'), args
    assert executor.smalltest_policy_problem(signed(item_id='J-3c')) == 'century dispatch belongs to J-4e'


def test_century_launch_refuses_a_measuring_or_markerd_staging_rollback(tmp_path):
    """Claim: the staging rollback the launch cites is a CENTURY one — not a measuring dry run, not a staging of a test slice, not another trigger."""
    marked = dict(chart_id=shared.CHART_ID, scope_target=shared.ASSET_ID, gochara_v5_test_slice=dict(run='all_classes_full'))
    cases = {
        'measuring dry run receipt': dict(receipt_kind='measuring_dispatch_dryrun'),
        'slice marker in the manifest': dict(proof=staging_proof(marked)),
        'small-test trigger': dict(proof=staging_proof(triggered_by=shared.TRIGGERED_BY)),
        'measuring schema': dict(proof=staging_proof(schema='ky.measuring_staging/1')),
        'rollback not confirmed': dict(proof=staging_proof(rollback_confirmed=False)),
        'different args': dict(proof=staging_proof(args={**ARGS, 'classes': 'marriage'})),
        'different horizon': dict(proof=staging_proof(args={**ARGS, 'horizon': '2002-01-01T00:00:00+00:00,2052-01-01T00:00:00+00:00'})),
    }
    for name, kwargs in cases.items():
        req = dispatch_request(tmp_path / name.replace(' ', '_'), **kwargs)
        assert shared.century_request_problem(req, tmp_path / name.replace(' ', '_') / 'run/ops'), name
    ok = dispatch_request(tmp_path / 'ok')
    assert shared.century_request_problem(ok, tmp_path / 'ok/run/ops') is None


def test_century_launch_requires_the_same_manifest_not_a_boolean(tmp_path):
    """Claim (MB-4.1 sibling): source, args and the newly built manifest must equal the accepted rollback; a different digest refuses."""
    req = dispatch_request(tmp_path)
    proof = shared.century_dryrun_evidence(req, tmp_path / 'run/ops')
    assert shared.century_dryrun_evidence(req, tmp_path / 'run/ops', proof['plan_manifest_digest']) == proof
    with pytest.raises(shared.Refused, match='same source, args and manifest'):
        shared.century_dryrun_evidence(req, tmp_path / 'run/ops', '0' * 64)


# ───────────────────────────── receipts: the executor writes the evidence, the child's words are not it ─────────────────────────────
def test_century_staging_receipt_requires_confirmed_rollback_of_an_unmarked_century_run(tmp_path, monkeypatch):
    executor = load('executor'); monkeypatch.setattr(executor, 'REC', tmp_path); monkeypatch.setattr(executor, 'log', lambda *a: None)
    req = dict(operation_id='rollback', kind='century_dispatch_dryrun', item_id='J-4e', args=dict(ARGS))
    good = staging_proof(operation_id='rollback', request_sha256=shared.request_hash(req))
    marked = dict(good['plan_manifest'], gochara_v5_test_slice=dict(run='all_classes_full'))
    bad = ['{}', json.dumps({**good, 'rollback_confirmed': False}), json.dumps({**good, 'request_sha256': '0' * 64}),
           json.dumps({**good, 'triggered_by': shared.TRIGGERED_BY}),
           json.dumps({**good, 'plan_manifest': marked, 'plan_manifest_digest': shared.evidence_digest(marked)}),
           json.dumps({**good, 'plan_manifest_digest': '0' * 64})]
    for output in bad:
        executor.receipt(req, 'COMPLETED', rc=0, out=output)
        assert json.loads((tmp_path / 'rollback.json').read_text())['status'] == 'FAILED', output[:80]
    executor.receipt(req, 'COMPLETED', rc=0, out=json.dumps(good))
    assert json.loads((tmp_path / 'rollback.json').read_text())['staging'] == good


def test_century_launch_receipt_requires_its_own_launch_record(tmp_path, monkeypatch):
    executor = load('executor')
    monkeypatch.setattr(executor, 'REC', tmp_path)
    monkeypatch.setattr(executor, 'log', lambda *a: None)
    req = dict(operation_id='launch', kind='century_dispatch', item_id='J-4e')
    body = dict(schema='ky.century_launch/1', status='LAUNCHED', run_id=S.RUN, chart_id=shared.CHART_ID,
                asset_id=shared.ASSET_ID, plan_manifest_digest='a' * 64, execution_name='brahma-build-pipeline-job-fixture')
    for output in (S.RUN, json.dumps({**body, 'schema': 'ky.measuring_launch/1'}), json.dumps({**body, 'schema': 'ky.smalltest_launch/1'}),
                   json.dumps(body) + '\n' + json.dumps(body)):
        executor.receipt(req, 'COMPLETED', rc=0, out=output)
        assert json.loads((tmp_path / 'launch.json').read_text())['status'] == 'FAILED'
    executor.receipt(req, 'COMPLETED', rc=0, out=json.dumps(body))
    assert json.loads((tmp_path / 'launch.json').read_text())['launch'] == body


# ───────────────────────────── the launch plan the dry run shows is the launch the real kind makes ─────────────────────────────
def test_the_dry_run_launch_plan_is_the_exact_argv_the_real_launcher_runs(monkeypatch):
    """Claim (SR-TEARDOWN-AUTHORITY-GATE 2: 'the plan it would run'): the argv in the dry-run proof equals what century_launch executes, env override included."""
    import subprocess
    import dispatch_v5_century_job as dry
    century_launch = load('century_launch')
    seen = []
    monkeypatch.setattr(century_launch.bridge.subprocess, 'run', lambda argv, **kw: seen.append(argv) or subprocess.CompletedProcess(argv, 0, 'brahma-build-pipeline-job-x1', ''))
    assert century_launch.century_cloud_launcher(S.RUN, 30) == 'brahma-build-pipeline-job-x1'
    assert dry.launch_plan(S.RUN)['argv'] == seen[0]
    assert century_launch.CENTURY_EXECUTION_ENV == shared.CENTURY_EXECUTION_ENV == 'PUBSUB_DISABLED=1'      # J-3 gate: the log read needs the substep lines printed
    assert century_launch.CENTURY_TRIGGERED_BY == shared.CENTURY_TRIGGERED_BY == dry.TRIGGERED_BY


@pytest.mark.parametrize('kwargs', [dict(run='all_classes_full'), dict(horizon_start='2025-01-01T00:00:00+00:00'), dict(horizon_end='2026-01-01T00:00:00+00:00'), dict(classes='marriage')])
def test_century_chooses_no_run_name_horizon_or_class_subset(kwargs):
    """Claim: the launcher never selects what '5.0' answers (N-G9 is the owner's; the writer derives the horizon): only `--classes all` is a shape."""
    import dispatch_v5_century_job as dry
    with pytest.raises(shared.Refused):
        dry.century_shape(**kwargs)
    assert dry.century_shape(classes='all') == {'classes': 'all'} == dry.century_shape()      # with no config given the shape is the classes-only one


# ───────────────────────────── F-CHANNEL: the profile, the deferral switch and the horizon reach the writer ─────────────────────────────
# Claims (SR-W34-PREP-RULINGS 1, option a; OD-1 adds result_policy): (1) the century request takes exactly classes + final_rules + defer_in_build_verify + horizon + result_policy and refuses
# anything else; (2) the three new values are validated strictly; (3) they are STAGED in plan_manifest under the writer's key, inside plan_manifest_digest
# (so the writer's every read verifies them), in the writer's canonical form; (4) the launcher stages and expects exactly that manifest; (5) the dispatch refuses
# CLI values that differ from the accepted request. The request digest covers `args` (executor.request_digest), so the acceptance and the pack fill bind all four.
# Claims 3-5 validate through the real ka_gochara_v5 writer, which the governance shards (pyyaml + pytest only) cannot import: they run in the sidecar environment, in
# platform/python-sidecar/tests/l3/kala_db/test_century_bindings_writer_bound.py.


@pytest.mark.parametrize('name,args', [
    ('an unknown argument', {**ARGS, 'horizon-start': '2025-01-01T00:00:00+00:00'}),
    ('no final_rules', {k: v for k, v in ARGS.items() if k != 'final_rules'}),
    ('no defer_in_build_verify', {k: v for k, v in ARGS.items() if k != 'defer_in_build_verify'}),
    ('no horizon', {k: v for k, v in ARGS.items() if k != 'horizon'}),
    ('no result_policy', {k: v for k, v in ARGS.items() if k != 'result_policy'}),
    ('an unknown result_policy', {**ARGS, 'result_policy': 'all_null'}),
    ('a result_policy spelled without its version', {**ARGS, 'result_policy': 'window_qualification'}),
    ('a boolean spelled True', {**ARGS, 'final_rules': 'True'}),
    ('a JSON boolean', {**ARGS, 'defer_in_build_verify': False}),
    ('deferral without the final rules', {**ARGS, 'final_rules': 'false', 'defer_in_build_verify': 'true'}),
    ('a naive horizon', {**ARGS, 'horizon': '2001-01-01T00:00:00,2051-01-01T00:00:00'}),
    ('an inverted horizon', {**ARGS, 'horizon': '2051-01-01T00:00:00+00:00,2001-01-01T00:00:00+00:00'}),
    ('one horizon bound', {**ARGS, 'horizon': '2001-01-01T00:00:00+00:00'}),
    ('three horizon bounds', {**ARGS, 'horizon': HORIZON + ',2052-01-01T00:00:00+00:00'}),
])
def test_century_request_args_are_exactly_the_five_and_strictly_valued(name, args):
    """Claims 1-2 (+ OD-1: the result policy is one of the two NAMED policies, required): the exact argument contract; a value that is not spelled exactly, or a horizon that is not two tz-aware ISO bounds in order, is refused by name."""
    assert shared.century_args_problem(dict(ARGS)) is None
    with pytest.raises(shared.Refused):
        shared.century_args_problem(args)



# ───────────────────────────── the century teardown scope ─────────────────────────────
def century_scope(root, **launch_over):
    launch = dict(schema='ky.century_launch/1', status='LAUNCHED', run_id=S.RUN, chart_id=shared.CHART_ID,
                  asset_id=shared.ASSET_ID, plan_manifest_digest='a' * 64, execution_name='brahma-build-pipeline-job-fixture')
    launch.update(launch_over)
    rr, ar = S.accepted(root, 'century_dispatch', 'launch', item_id='J-4e', launch=launch)
    return dict(run_id=S.RUN, chart_id=shared.CHART_ID, generation='5.0', asset_id=shared.ASSET_ID,
                manifest_id='22222222-2222-4222-8222-222222222222', input_vector_sha256='c' * 64,
                plan_manifest_digest='a' * 64, dispatch_receipt=rr, dispatch_acceptance=ar)


def test_century_scope_accepts_j4e_century_launch_and_requires_candidate_vector(tmp_path):
    """Claim: a century teardown is scoped by run_id to ONE accepted century launch with its candidate manifest and input vector."""
    scope = century_scope(tmp_path)
    req = dict(kind='century_teardown_dryrun', item_id='J-4e', century_scope=scope)
    assert shared.staged_scope(req, tmp_path / 'run/ops') == scope
    for field in ('manifest_id', 'input_vector_sha256'):
        bad = copy.deepcopy(req); bad['century_scope'][field] = None
        with pytest.raises(shared.Refused):
            shared.staged_scope(bad, tmp_path / 'run/ops')
    with pytest.raises(shared.Refused, match='belongs to J-4e'):
        shared.staged_scope(dict(req, item_id='J-3d'), tmp_path / 'run/ops')
    with pytest.raises(shared.Refused):                       # the scope key is the kind's own: a small-test or measuring scope cannot stand in
        shared.staged_scope(dict(kind='century_teardown_dryrun', item_id='J-4e', smalltest_scope=scope), tmp_path / 'run/ops')


@pytest.mark.parametrize('change', ['item', 'kind', 'schema', 'run', 'digest', 'execution'])
def test_century_scope_rejects_cross_identity_launch(tmp_path, change):
    scope = century_scope(tmp_path)
    p = tmp_path / 'run/ops/receipts/launch.json'
    r = json.loads(p.read_text())
    if change == 'item': r['item_id'] = 'J-3c'
    elif change == 'kind': r['kind'] = 'measuring_dispatch'
    elif change == 'schema': r['launch']['schema'] = 'ky.measuring_launch/1'
    elif change == 'run': r['launch']['run_id'] = '22222222-2222-4222-8222-222222222222'
    elif change == 'digest': r['launch']['plan_manifest_digest'] = 'b' * 64
    else: r['launch']['execution_name'] = 'other-job-fixture'
    scope['dispatch_receipt'] = S.put(tmp_path, 'receipts', 'launch', r)
    with pytest.raises(shared.Refused):
        shared.staged_scope(dict(kind='century_teardown', item_id='J-4e', century_scope=scope), tmp_path / 'run/ops')


def test_measuring_and_smalltest_scopes_refuse_a_century_launch(tmp_path):
    """Claim: the new family does not widen the old ones — a century launch receipt authorises no measuring or small-test teardown."""
    scope = century_scope(tmp_path)
    for kind, key, item in (('measuring_teardown_dryrun', 'measuring_scope', 'J-3d'), ('smalltest_teardown_dryrun', 'smalltest_scope', 'J-2a')):
        with pytest.raises(shared.Refused):
            shared.staged_scope({'kind': kind, 'item_id': item, key: scope}, tmp_path / 'run/ops')


def teardown_request(root):
    scope = century_scope(root)
    req = dict(operation_id='apply', kind='century_teardown', item_id='J-4e', century_scope=scope)
    req['dryrun_receipt'], req['dryrun_acceptance'] = S.accepted(root, 'century_teardown_dryrun', 'rollback', item_id='J-4e',
        teardown=dict(schema='ky.century_teardown/1', status='ROLLED_BACK', rollback_confirmed=True, operation_id='rollback',
                      request_sha256='b' * 64, scope=scope, scope_sha256=shared.evidence_digest(scope), rowset_sha256='d' * 64))
    return S.authorize(root, req)


def test_century_teardown_binds_real_rollback_scope_rowset_and_executor_receipt(tmp_path, monkeypatch):
    """Claim (SR-TEARDOWN-AUTHORITY-GATE 3): a century teardown commit needs a rollback-confirmed dry run of the SAME scope and row set; its commit
    is AWAITING_ABSENCE until an independent readback bound to it; completion is the century's own record."""
    req = teardown_request(tmp_path)
    root = tmp_path / 'run/ops'
    proof = shared.dryrun_evidence(req, root, req['century_scope'], 'd' * 64)
    assert proof['rollback_confirmed']
    with pytest.raises(shared.Refused):
        shared.dryrun_evidence(req, root, req['century_scope'], 'e' * 64)
    wrong_family = dict(req, dryrun_receipt=S.accepted(tmp_path, 'measuring_teardown_dryrun', 'rollback-m', item_id='J-3d', teardown=proof)[0])
    with pytest.raises(shared.Refused):
        shared.dryrun_evidence(wrong_family, root, req['century_scope'], 'd' * 64)
    executor = load('executor'); monkeypatch.setattr(executor, 'REC', root / 'receipts'); monkeypatch.setattr(executor, 'log', lambda *a: None)
    monkeypatch.setattr(executor, 'now', lambda: '2026-10-15T00:00:00+00:00')
    committed = dict(proof, status='COMMITTED_AWAITING_ABSENCE', rollback_confirmed=False,
                     operation_id='apply', request_sha256=shared.request_hash(req))
    wrong_schema = dict(committed, schema='ky.measuring_teardown/1')
    executor.receipt(req, 'COMPLETED', rc=0, out='teardown_proof\t' + json.dumps(wrong_schema))
    assert json.loads((root / 'receipts/apply.json').read_text())['status'] == 'FAILED'
    executor.receipt(req, 'COMPLETED', rc=0, out='teardown_proof\t' + json.dumps(committed))
    r = json.loads((root / 'receipts/apply.json').read_text())
    assert r['status'] == 'AWAITING_ABSENCE' and r['teardown'] == committed
    rr, ar = S.absence_for(tmp_path, committed=r)
    observed = shared.absence_evidence(dict(absence_receipt=rr, absence_acceptance=ar), root, teardown_receipt=r)
    assert observed['run_id'] == S.RUN
    monkeypatch.setattr(executor, 'OPS', root)
    monkeypatch.setattr(executor, 'ACC', root / 'acceptance')
    monkeypatch.setattr(executor, 'FENCE', root / 'production.fence.json')
    monkeypatch.setattr(executor, 'smalltest_policy', lambda req: vars(shared))
    executor.FENCE.write_text(json.dumps(dict(operation_id='apply', request_sha256=r['request_sha256'])))
    q = dict(operation_id='apply', request_sha256=r['request_sha256'], result='ACCEPTED', by='v2', ts=executor.now())
    qp = executor.ACC / 'apply.quiescence.json'; qp.write_text(json.dumps(q))
    assert executor.fence_quiescent() is False
    qp.write_text(json.dumps(dict(q, absence_receipt=rr, absence_acceptance=ar)))
    assert executor.fence_quiescent() is True
    completion = json.loads((root / 'receipts/apply.completion.json').read_text())
    assert completion['schema'] == 'ky.century_completion/1' and completion['run_id'] == S.RUN


def test_the_century_absence_census_counts_the_century_trigger_and_other_lifecycles_keep_theirs():
    """Claim: the independent absence SELECT for a century teardown counts the century runs (the small-test count would read 0 over a surviving century run)."""
    base = dict(request_sha256='b' * 64, operation_id='apply', status='AWAITING_ABSENCE', exit_code=0)
    teardown = dict(scope=dict(run_id=S.RUN), scope_sha256='a' * 64, rowset_sha256='d' * 64)
    century = shared.absence_readback_sql(dict(base, kind='century_teardown', teardown=teardown))
    small = shared.absence_readback_sql(dict(base, kind='measuring_teardown', teardown=teardown))
    assert f"triggered_by = '{shared.CENTURY_TRIGGERED_BY}'" in century and f"triggered_by = '{shared.TRIGGERED_BY}'" not in century
    assert f"triggered_by = '{shared.TRIGGERED_BY}'" in small and shared.CENTURY_TRIGGERED_BY not in small
    assert f"triggered_by = '{shared.TRIGGERED_BY}'" in shared.absence_readback_sql(None)         # the baseline readback is unchanged


# ───────────────────────────── lifecycle: a later century launch cannot reuse an older absence ─────────────────────────────
def test_a_later_century_launch_needs_its_own_teardown_and_absence(tmp_path):
    """Claim (absence lifecycle, shared with J-3c): a COMPLETED century launch after a committed teardown, or before a baseline readback, refuses reuse."""
    root = tmp_path / 'run/ops'
    committed = dict(kind='measuring_teardown', operation_id='td', status='AWAITING_ABSENCE', exit_code=0, request_sha256='f' * 64,
                     reviewed_commit=S.COMMIT, ts='2026-10-15T00:00:00+00:00',
                     teardown=dict(schema='ky.measuring_teardown/1', status='COMMITTED_AWAITING_ABSENCE', scope=dict(run_id=S.RUN),
                                   scope_sha256='a' * 64, rowset_sha256='d' * 64))
    rr, ar = S.absence_for(tmp_path, committed=committed)
    ev = dict(absence_receipt=rr, absence_acceptance=ar)
    assert shared.absence_evidence(ev, root, teardown_receipt=committed)['run_id'] == S.RUN
    S.put(tmp_path, 'receipts', 'later-century', dict(kind='century_dispatch', status='COMPLETED', launch=dict(status='LAUNCHED'),
                                                      ts='2026-10-15T01:00:00+00:00'))
    with pytest.raises(shared.Refused, match='later staged launch'):
        shared.absence_evidence(ev, root, teardown_receipt=committed)
    baseline = S.absence_for(tmp_path / 'b')
    with pytest.raises(shared.Refused, match='prior teardown requires its own independent absence'):
        S.put(tmp_path / 'b', 'receipts', 'prior-century', dict(kind='century_dispatch', status='COMPLETED', launch=dict(status='LAUNCHED'),
                                                                ts='2026-10-15T01:00:00+00:00'))
        shared.absence_evidence(dict(absence_receipt=baseline[0], absence_acceptance=baseline[1]), tmp_path / 'b/run/ops')
