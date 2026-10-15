"""VERIFY publication uses real proposal/schema/Git/action/ledger readers; only boundary execution is faked.

Regressions: lost result_path must not strand a completed review, bad proposals must retain their named
refusal, and finish of an ended job must reuse the proposal without another model launch.
"""
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(FLEET))
sys.path.insert(0, str(FLEET / 'tests'))
import kyd_jobs as J
import kyd_kinds_build as B
import kyverdicts as K
from test_kyverdicts import World, JOB, ITEM, CID


@pytest.fixture(params=['VERIFY', 'ARTIFACT'])
def review(tmp_path, request):
    w = World(tmp_path)
    kind = request.param
    job = dict.fromkeys(J.LAUNCH_KEYS + J.LIFECYCLE_KEYS)
    job.update(schema='ky.job/1', job_id=JOB, item=ITEM, kind=kind, slot='v1', role=kind.lower(),
               key=kind + '.' + ITEM + '.123456789abc', phase='ended', exit_code=0, outcome='failed',
               worktree=str(w.wt), job_scratch=str(w.scratch), controller_id=CID,
               head=w.head if kind == 'VERIFY' else None, digest=w.digest if kind == 'ARTIFACT' else None,
               verdict_phase='pre_merge' if kind == 'VERIFY' else 'artifact', locks=[],
               failure_fp='publish_inputs_unknown', checkpoint={'steps': {'boundary': '2026-10-12T09:01:59Z', 'ended': '2026-10-12T09:02:00Z'}})
    detail = 'PR #12 @ ' + w.head if kind == 'VERIFY' else str(w.artifact) + ' sha256=' + w.digest
    # Match the real author's registration syntax, rather than faking B._registration.
    ledger = [{'kind': 'item', 'item': ITEM, 'state': 'review', 'actor': 'stream-K:b1', 'detail': detail, 'evidence': str(w.artifact)}]
    if kind == 'ARTIFACT':
        w.write_result(verdict={'verdict': 'ACCEPTED', 'phase': 'artifact', 'artifact_digest': w.digest})
    calls = []
    ctx = SimpleNamespace(root=str(w.root / 'kyroot'), run=str(w.run_dir), fleet=str(FLEET),
                          repo=str(w.wt), scratch=str(w.scratch.parent), controller_id=CID,
                          events=lambda item: ledger, journal=lambda *args: None)
    def sh(argv, **kwargs):
        calls.append(argv)
        if 'kyboundary.sh' in ' '.join(argv):
            assert argv[-2:] == ['check', JOB]
            return 0, '', ''
        assert argv[:4] == ['python3', '-B', str(FLEET / 'kyverdicts.py'), 'publish']
        out = io.StringIO()
        rc = K.main(argv[3:], environ=w.env, stdout=out)
        return rc, out.getvalue(), ''
    ctx.sh = sh
    folder = w.run_dir / 'jobs' / JOB
    folder.mkdir(parents=True)
    (folder / 'state.json').write_text(json.dumps(job))
    return w, ctx, job, calls


def test_finish_ended_review_with_null_result_path_publishes_once_without_model(review):
    w, ctx, job, calls = review
    before = (Path(ctx.run) / 'jobs' / JOB / 'state.json').read_bytes()
    assert B.finish(ctx, J.load(ctx)[0])['outcome'] == 'done'
    assert B.finish(ctx, J.load(ctx)[0])['outcome'] == 'done'
    assert len(w.verdicts()) == len(w.calls()) == 1
    assert all('kyjob.sh' not in ' '.join(argv) for argv in calls)
    assert w.result.read_bytes() and w.verdicts()[0]['result'] == 'ACCEPTED'
    assert (Path(ctx.run) / 'jobs' / JOB / 'state.json').read_bytes() == before


@pytest.mark.parametrize('bad,reason', [('missing', 'result_missing'), ('json', 'result_invalid'),
    ('schema', 'result_invalid'), ('symlink', 'result_invalid'), ('wrong_job', 'result_job_mismatch'),
    ('no_verdict', 'verdict_not_proposed'), ('blocked', 'result_not_done')])
def test_proposal_refusals_retain_the_named_reason(review, bad, reason):
    w, ctx, job, _ = review
    doc = json.loads(w.result.read_text())
    if bad == 'missing': w.result.unlink()
    if bad == 'json': w.result.write_text('{broken')
    if bad == 'schema': doc['notes'] = []; w.result.write_text(json.dumps(doc))
    if bad == 'symlink':
        other = w.result.with_name('other.json'); w.result.rename(other); w.result.symlink_to(other)
    if bad == 'wrong_job': doc['job_id'] = 'J-other'; w.result.write_text(json.dumps(doc))
    if bad == 'no_verdict': doc.pop('proposed_verdict'); w.result.write_text(json.dumps(doc))
    if bad == 'blocked': doc.update(status='blocked', blocked_reason='tests unrun'); w.result.write_text(json.dumps(doc))
    result = B.finish(ctx, job)
    assert result['outcome'] == 'failed'
    assert result['failure_fp'] == 'publish_' + reason
    assert reason in result['detail']
    w.nothing_published()


def test_recovery_rechecks_current_tree(review):
    w, ctx, job, _ = review
    (w.wt / 'code.py').write_text('changed after review\n')
    result = B.finish(ctx, job)
    assert result['outcome'] == 'failed' and 'tree_dirty' in result['detail']
    w.nothing_published()


def test_recovery_uses_preserved_boundary_evidence_after_view_release(review):
    w, ctx, job, calls = review
    before = w.boundary.read_bytes()
    publish = ctx.sh
    def after_release(argv, **kwargs):
        if 'kyboundary.sh' in ' '.join(argv):
            return 1, '', 'the verifier view has been released'
        return publish(argv, **kwargs)
    ctx.sh = after_release
    assert B.finish(ctx, job)['outcome'] == 'done'
    assert w.boundary.read_bytes() == before
    assert len(w.verdicts()) == 1


@pytest.mark.parametrize('bad,reason', [('missing', 'boundary_missing'), ('violated', 'boundary_not_intact'),
                                       ('other_job', 'boundary_job_mismatch')])
def test_recovery_never_trusts_missing_or_bad_preserved_boundary(review, bad, reason):
    w, ctx, job, _ = review
    if bad == 'missing': w.boundary.unlink()
    if bad == 'violated': w.write_boundary(mechanism_intact=False, result='violated')
    if bad == 'other_job': w.write_boundary(job_id='J-other')
    result = B.finish(ctx, job)
    assert result['outcome'] == 'failed' and reason in result['detail']
    w.nothing_published()


def test_first_finish_still_checks_boundary_before_publishing(review):
    w, ctx, job, _ = review
    job['phase'] = 'terminating'
    job['checkpoint'] = {'steps': {}}
    ctx.sh = lambda argv, **kwargs: (1, '', 'boundary violated')
    result = B.finish(ctx, job)
    assert result['outcome'] == 'failed' and result['failure_fp'] == 'boundary_violated'
    w.nothing_published()
