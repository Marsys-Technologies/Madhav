"""Remaining model roles: template contracts and selection, never earned receipts."""
import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_job_engine_roles import (A, B, J, Q, FLEET, ctx, claude_receipt,
                                   codex_receipt, launch, job_launcher_helpers, kyschema)
import kyd_kinds_ops as O

# Cards come from the real intent constructors, including ARTIFACT's reviewer card.
ROLES = {
    'rework': ('build', Path(B.CARD_BUILDER).name, 100, 'K', 'builder'),
    'artifact': ('build', Path(B.CARD_VERIFIER).name, 60, 'V', 'verifier'),
    'pre-accept': ('verify', O.CARDS['verifier'], 40, 'V', 'verifier'),
    'post-readback': ('verify', O.CARDS['verifier'], 40, 'V', 'verifier'),
    'ruling': ('verify', O.CARDS['adhikarin'], 30, 'N', 'builder'),
    'request-prep': ('build', O.CARDS['adhikarin'], 300, 'N', 'builder'),
    'model': ('build', O.CARDS['adhikarin'], 300, 'S', 'builder'),
    'plan': ('build', O.CARDS['adhikarin'], 300, 'S', 'builder'),
}


def template(role):
    return json.loads((FLEET / 'templates' / ('LAUNCH_CONFIG.' + role + '.codex.json')).read_text())


@pytest.mark.parametrize('role', ROLES)
def test_remaining_template_schema_parent_card_cap_and_launcher_env(role, tmp_path, monkeypatch):
    parent, card, cap, stream, pool = ROLES[role]
    cfg, baseline = template(role), template(parent)
    assert Q.validate_codex_config(cfg, check_disk=False) == []
    schema = json.loads((FLEET / 'schemas/launch_config_codex.json').read_text())
    assert kyschema.validate(schema, cfg) == []
    assert cfg['role'] == role and cfg['model'] == A.CODEX_MODEL and cfg['effort'] == 'high'
    assert (FLEET / 'cards' / card).is_file()
    assert cfg['prompt_path'] == '/Users/Dev/kalayantra/fleet_live/cards/' + card
    assert A.TURN_CAPS[role.upper()] == cap
    # The actual Codex contract prohibits max_turns. The requested cap must be
    # visible as preparation metadata, never represented as an enforced limit.
    assert 'max_turns' not in cfg and 'max_turns=%d' % cap in cfg['_note']
    assert '(I) INTERPRETATION' in cfg['_note']
    if cap == 300:
        assert 'xhigh' in cfg['_note'] and 'surrogate' in cfg['_note']
    for key in ('engine', 'model', 'effort', 'sandbox', 'network', 'work_root', 'commit_mode',
                'deadline_seconds', 'worktree', 'codex_bin', 'codex_min_version', 'output_schema',
                'env_names', 'child_path', 'writable_dirs'):
        assert cfg.get(key) == baseline.get(key)
    helper = job_launcher_helpers()
    c = SimpleNamespace(repo=str(tmp_path), controller_id='CTL-test')
    intent = dict(kind=role.upper(), role=role, item='KV3-T', key='env-test', locks=[], stream=stream, pool=pool)
    plan, why = J._plan(c, intent, 'v1' if pool == 'verifier' else 'b1', {'tests': []})
    assert why is None
    job = dict(plan['state'], tmp_path=str(tmp_path), job_scratch=str(tmp_path), job_id='J-env', PRAVAHA=[])
    own = dict(HOME=str(tmp_path), USER='test', KY_ROOT='/Users/Dev/kalayantra', KY_RUN=str(tmp_path),
               KY_FLEET=str(FLEET), KY_SCRATCH=str(tmp_path))
    node = cfg['child_path'].split(':')[1]
    (tmp_path / 'NODE_BIN').write_text(node + '\n')
    isdir = helper['os'].path.isdir
    monkeypatch.setattr(helper['os'].path, 'isdir', lambda p: p == node or isdir(p))
    env = helper['job_environment'](job, own)
    assert cfg['env_names'] == [n for n, _ in env]
    assert cfg['child_path'] == dict(env)['PATH']
    assert Q.resolve_env(cfg, dict(own, KY_STREAM=stream, KY_LANE=job['slot'], KY_CONTROLLER_ID=c.controller_id))[1] == []
    listed = '00_ARCHITECTURE/briefs/kalayantra/fleet/templates/LAUNCH_CONFIG.' + role + '.codex.json'
    assert listed in (FLEET / 'BOOTSTRAP_COMPONENTS.txt').read_text().splitlines()


@pytest.mark.parametrize('role', ROLES)
@pytest.mark.parametrize('switch', ['codex', 'role'])
def test_role_selects_own_codex_receipt_only_with_switch(ctx, role, switch):
    claude_receipt(ctx, role)
    cfg, receipt = codex_receipt(ctx, role)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('codex' if switch == 'codex' else role + '=codex')
    refusals, got = launch(ctx, role.upper())
    assert refusals == [] and got['engine'] == 'codex' and got['role'] == role
    assert got['codex_config'] == cfg and str(receipt) in ctx.calls[0][0]


@pytest.mark.parametrize('role', ROLES)
@pytest.mark.parametrize('switch', [None, 'claude', 'verify=codex'])
def test_other_roles_still_use_unchanged_claude_launch(ctx, role, switch):
    binds = claude_receipt(ctx, role)
    codex_receipt(ctx, role)
    if switch is not None:
        (Path(ctx.run) / 'JOB_ENGINE').write_text(switch)
    refusals, got = launch(ctx, role.upper())
    expected = dict(model=binds['model'], effort=binds['effort'], permission_mode=binds['permission_mode'],
                    max_turns=binds['max_turns'], deadline='2026-10-13T01:00:00Z', claude_bin=binds['claude_bin'],
                    mcp_config=str(Path(ctx.fleet) / 'mcp.none.json'), extra_lean_flags=[], disallowed_tools=[])
    assert refusals == [] and json.dumps(got, sort_keys=True).encode() == json.dumps(expected, sort_keys=True).encode()
    assert ctx.calls == []


@pytest.mark.parametrize('role', ROLES)
def test_missing_role_receipt_has_no_claude_fallback(ctx, role):
    claude_receipt(ctx, role)
    _, receipt = codex_receipt(ctx, role)
    receipt.unlink()
    (Path(ctx.run) / 'JOB_ENGINE').write_text('codex')
    refusals, got = launch(ctx, role.upper())
    assert got is None and any(str(receipt) in r['detail'] for r in refusals)
    assert ctx.calls == []


@pytest.mark.parametrize('role', ['pre-accept', 'post-readback', 'ruling', 'request-prep', 'model', 'plan'])
def test_ops_header_respects_codex_policy_and_readonly_mapping(ctx, role, tmp_path):
    cfg, _ = codex_receipt(ctx, role)
    (Path(ctx.run) / 'JOB_ENGINE').write_text(role + '=codex')
    A.refresh_job_engine(ctx)
    parent, _, _, stream, pool = ROLES[role]
    intent = O._intent(ctx, role.upper(), 'KV3-T', stream=stream, runner='model', pool=pool,
                       tier='opus', evidence_fp='evidence', effort='xhigh' if parent == 'build' else 'high')
    assert intent['header']['model'] == A.CODEX_MODEL and intent['header']['effort'] == 'high'
    refusals, admitted = launch(ctx, role.upper())
    assert refusals == []
    plan, why = J._plan(ctx, intent, 'b1', {'launch': admitted, 'tests': []})
    assert why is None
    assert plan['state']['boundary'] == ('verifier' if parent == 'verify' else None)
    job = dict(plan['state'], job_scratch=str(tmp_path), prompt_path=str(tmp_path / 'prompt'))
    J._codex_config(job, plan)
    actual = json.loads(Path(job['launch_config_path']).read_text())
    assert actual == dict(cfg, worktree=job['worktree'], prompt_path=job['prompt_path'])


def surrogate_template(ctx):
    cfg = json.loads((FLEET / 'templates/LAUNCH_CONFIG.surrogate.json').read_text())
    (Path(ctx.fleet) / 'templates/LAUNCH_CONFIG.surrogate.json').write_text(json.dumps(cfg))
    return cfg


@pytest.mark.parametrize('switch', [None, 'claude', 'codex', 'surrogate=claude'])
def test_surrogate_always_resolves_template_fable_high(ctx, switch):
    cfg = surrogate_template(ctx)
    assert cfg['model'] == 'claude-fable-5-1' and cfg['effort'] == 'high'
    assert Q.validate_config(cfg, check_disk=False) == []
    assert kyschema.validate(json.loads((FLEET / 'schemas/launch_config.json').read_text()), cfg) == []
    claude_receipt(ctx, 'surrogate', model='claude-fable-5-1')
    if switch is not None:
        (Path(ctx.run) / 'JOB_ENGINE').write_text(switch)
    refusals, got = launch(ctx, 'SURROGATE')
    assert refusals == [] and got['model'] == cfg['model'] and got['effort'] == cfg['effort']
    assert 'engine' not in got and ctx.calls == []
    intent = O._intent(ctx, 'SURROGATE', 'KV3-T', stream='steward', runner='model', evidence_fp='e', effort='high')
    assert intent['header']['model'] == cfg['model'] and intent['header']['effort'] == 'high'


@pytest.mark.parametrize('case', ['absent', 'opus', 'low', 'receipt-opus', 'receipt-low', 'codex-switch'])
def test_surrogate_refuses_missing_wrong_template_or_old_receipt(ctx, case):
    cfg = surrogate_template(ctx)
    if case == 'absent': (Path(ctx.fleet) / 'templates/LAUNCH_CONFIG.surrogate.json').unlink()
    elif case in ('opus', 'low'):
        cfg['model' if case == 'opus' else 'effort'] = 'claude-opus-5-5' if case == 'opus' else 'low'
        (Path(ctx.fleet) / 'templates/LAUNCH_CONFIG.surrogate.json').write_text(json.dumps(cfg))
    if case == 'receipt-opus':
        claude_receipt(ctx, 'surrogate')
    else:
        claude_receipt(ctx, 'surrogate', model='claude-fable-5-1')
    if case == 'receipt-low':
        p = Path(ctx.run) / 'QUALIFICATIONS/surrogate-claude-fable-5-1.json'
        doc = json.loads(p.read_text()); doc['binds']['effort'] = 'low'; p.write_text(json.dumps(doc))
    if case == 'codex-switch': (Path(ctx.run) / 'JOB_ENGINE').write_text('surrogate=codex')
    refusals, got = launch(ctx, 'SURROGATE')
    assert got is None and refusals


def test_artifact_builder_template_does_not_relax_actual_verifier_boundary(ctx):
    codex_receipt(ctx, 'artifact')
    (Path(ctx.run) / 'JOB_ENGINE').write_text('artifact=codex')
    refusals, facts = [], {}
    A._check_launch(ctx, dict(kind='ARTIFACT', role='artifact', pool='verifier', stream='V'),
                    'opus', {'needs_chart_data': False}, True, refusals, facts)
    assert facts['launch'] is None
    assert any('verifier pool' in r['detail'] for r in refusals)


@pytest.mark.parametrize('role', ROLES)
def test_adapter_kind_mapping_preserves_legacy_schema_and_postures(role):
    J.engines.selection(dict(engine='codex', kind=role.upper(), launch_config_path='/fixture/launch.json'))
    assert J.engines.READ_ONLY_KINDS == {'VERIFY', 'PRE-ACCEPT', 'POST-READBACK', 'RULING'}
    # New operation/planning kinds retain their existing result schemas; they
    # do not acquire BUILD's controller-owned code landing protocol.
    schema = J.engines.result_schema(dict(kind=role.upper()))
    expected = 'job_result_launcher_commit.json' if role == 'rework' else 'job_result.json'
    assert schema == json.loads((FLEET / 'schemas' / expected).read_text())


def test_codex_contract_rejects_literal_turn_cap():
    cfg = template('build'); cfg['max_turns'] = 300
    assert any('claude-only' in e for e in Q.validate_codex_config(cfg, check_disk=False))
    assert kyschema.validate(json.loads((FLEET / 'schemas/launch_config_codex.json').read_text()), cfg)


def test_surrogate_ops_context_without_admission_paths_selects_real_template(ctx):
    cfg = surrogate_template(ctx)
    del ctx.paths  # kyd_kinds_ops's documented context uses fleet/run attributes
    intent = O._intent(ctx, 'SURROGATE', 'KV3-T', stream='steward', runner='model', evidence_fp='e', effort='high')
    assert intent['header']['model'] == cfg['model'] and intent['header']['effort'] == cfg['effort']


@pytest.mark.parametrize('role', ['artifact', 'request-prep', 'model', 'plan'])
def test_new_writer_mapping_cannot_inherit_code_landing(role, monkeypatch):
    def forbidden(*args):
        pytest.fail('unqualified completion touched Git before refusal')
    monkeypatch.setattr(J.engines, 'pointer', forbidden)
    with pytest.raises(J.engines.Refusal, match='completion adapter is unqualified'):
        J.engines.prepare(None, dict(kind=role.upper(), checkpoint={}))


@pytest.mark.parametrize('role', ['pre-accept', 'post-readback', 'ruling'])
def test_new_readonly_mapping_refuses_missing_snapshot_packet(role, monkeypatch):
    monkeypatch.setattr(J.engines, 'pointer', lambda *args: pytest.fail('missing packet touched Git'))
    with pytest.raises(J.engines.Refusal, match='requires a packet_path'):
        J.engines.prepare(None, dict(kind=role.upper(), checkpoint={}, packet_path=None))


@pytest.mark.parametrize('role', ['build', 'verify'])
def test_existing_codex_templates_are_byte_identical_to_assembly_head(role):
    path = FLEET / 'templates' / ('LAUNCH_CONFIG.' + role + '.codex.json')
    rel = str(path.relative_to(FLEET.parents[3]))
    read = subprocess.run(['/usr/bin/git', '-C', str(FLEET), 'show', 'HEAD:' + rel],
                          env={'PATH': '/usr/bin:/bin', 'GIT_OPTIONAL_LOCKS': '0'}, capture_output=True, check=True)
    assert path.read_bytes() == read.stdout


@pytest.mark.parametrize('role', ['pre-accept', 'post-readback', 'ruling', 'request-prep', 'model', 'plan'])
def test_unswitched_ops_intent_bytes_match_assembly_head(ctx, role):
    path = FLEET / 'kyd_kinds_ops.py'
    rel = str(path.relative_to(FLEET.parents[3]))
    read = subprocess.run(['/usr/bin/git', '-C', str(FLEET), 'show', 'HEAD:' + rel],
                          env={'PATH': '/usr/bin:/bin', 'GIT_OPTIONAL_LOCKS': '0'}, capture_output=True, check=True)
    baseline = {'__file__': str(path), '__name__': 'ops_assembly_baseline'}
    exec(compile(read.stdout, str(path), 'exec'), baseline)
    parent, _, _, stream, pool = ROLES[role]
    args = dict(stream=stream, runner='model', pool=pool, tier='opus', evidence_fp='e',
                effort='xhigh' if parent == 'build' else 'high')
    old = baseline['_intent'](ctx, role.upper(), 'KV3-T', **copy.deepcopy(args))
    new = O._intent(ctx, role.upper(), 'KV3-T', **copy.deepcopy(args))
    serialise = lambda obj: json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()
    assert serialise(old) == serialise(new)


def test_retained_surrogate_environment_still_needs_cockpit_resolution(ctx, tmp_path):
    cfg = surrogate_template(ctx)
    helper = job_launcher_helpers()
    intent = dict(kind='SURROGATE', role='surrogate', item='KV3-T', key='surrogate-env',
                  stream='steward', pool='builder', locks=[])
    plan, why = J._plan(ctx, intent, 'b1', {'tests': []})
    assert why is None
    job = dict(plan['state'], tmp_path=str(tmp_path), job_scratch=str(tmp_path), job_id='J-env', PRAVAHA=[])
    own = dict(HOME=str(tmp_path), USER='test', KY_ROOT='/Users/Dev/kalayantra', KY_RUN=str(tmp_path),
               KY_FLEET=str(FLEET), KY_SCRATCH=str(tmp_path))
    env = helper['job_environment'](job, own)
    assert set(n for n, _ in env) - set(cfg['env_names']) == {
        'KY_STREAM', 'KY_LANE', 'KY_ITEM', 'KY_PY', 'KY_RUN_ID', 'KY_ROLE', 'KY_CONTROLLER_ID'}
