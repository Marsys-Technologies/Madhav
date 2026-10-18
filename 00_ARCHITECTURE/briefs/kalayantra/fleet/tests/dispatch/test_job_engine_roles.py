"""Runtime job engine policy: no real agents, Git mutation, network or services."""
import copy
import datetime
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

FLEET = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(FLEET))
sys.path.insert(0, str(FLEET / 'tests'))
import kyd_admit as A
import kyd_jobs as J
import kyd_kinds_build as B
import kyaction as ka
import kyqualify as Q
import kyschema
import kymanifest
from test_kyqualify import job_launcher_helpers


@pytest.fixture
def ctx(tmp_path):
    run, fleet = tmp_path / 'run', tmp_path / 'fleet'
    run.mkdir(); fleet.mkdir()
    (run / 'QUALIFICATIONS').mkdir()
    (fleet / 'templates').mkdir()
    (fleet / 'mcp.none.json').write_text('{"mcpServers":{}}\n')
    calls, journal = [], []
    def sh(argv, **kw):
        calls.append((argv, kw))
        return 0, '', ''  # harness boundary only; never asserted as earned PASS
    c = SimpleNamespace(paths={'run': str(run), 'fleet': str(fleet)}, run=str(run), fleet=str(fleet),
                        repo=str(tmp_path), controller_id='test-controller', sh=sh,
                        now=lambda: datetime.datetime(2026, 10, 13, tzinfo=datetime.timezone.utc),
                        journal=lambda *args: journal.append(args), calls=calls, journal_entries=journal)
    return c


def claude_receipt(c, role='build', model='claude-opus-5-5'):
    binds = dict(model=model, effort='high', permission_mode='bypassPermissions',
                 max_turns=min(60, A.TURN_CAPS.get(role.upper(), 60)),
                 deadline_seconds=3600, claude_bin='/fake/claude',
                 mcp_config_sha256=ka.sha_file(Path(c.fleet) / 'mcp.none.json'), extra_flags=[], disallowed_tools=[])
    doc = dict(schema='ky.qualification/1', role=role, model=binds['model'], result='PASS', context='launchd', binds=binds)
    ka.write_json(Path(c.run) / 'QUALIFICATIONS' / (role + '-' + model + '.json'), doc)
    return binds


def codex_receipt(c, role='build'):
    path = FLEET / 'templates' / ('LAUNCH_CONFIG.' + role + '.codex.json')
    # The template tests below require the actual new file; use the accepted parent
    # here until implementation, so selection fails for the missing behavior first.
    parent = 'bootstrap-builder' if role == 'build' else 'bootstrap-reviewer'
    cfg = json.loads((path if path.exists() else FLEET / 'templates' / ('LAUNCH_CONFIG.' + parent + '.codex.json')).read_text())
    cfg.update(role=role)
    template = Path(c.fleet) / 'templates' / ('LAUNCH_CONFIG.' + role + '.codex.json')
    ka.write_json(template, cfg)
    binds = dict(engine='codex', model=cfg['model'], effort=cfg['effort'], deadline_seconds=cfg['deadline_seconds'])
    doc = dict(schema='ky.qualification/1', engine='codex', role=role, model=cfg['model'], result='PASS',
               context='launchd', binds=binds)
    receipt = Path(c.run) / 'QUALIFICATIONS' / (role + '-gpt-6.1-sol.json')
    ka.write_json(receipt, doc)
    return cfg, receipt


def launch(c, kind='BUILD', chart=False):
    refusals, facts = [], {}
    A._check_launch(c, dict(kind=kind, role=kind.lower(), stream='V' if kind == 'VERIFY' else 'K'),
                    'opus', {'needs_chart_data': chart}, True, refusals, facts)
    return refusals, facts['launch']


@pytest.mark.parametrize('content,kind', [('codex\n','BUILD'), ('codex\n','VERIFY'),
    ('build=codex\n','BUILD'), ('build=codex\n','REWORK'), ('rework=codex\n','REWORK'),
    ('build=claude\nverify=codex\n','VERIFY')])
def test_switch_selects_codex_receipt_and_pins_role(ctx, content, kind):
    role = kind.lower()
    cfg, receipt = codex_receipt(ctx, role)
    (Path(ctx.run) / 'JOB_ENGINE').write_text(content)
    refusals, got = launch(ctx, kind)
    assert refusals == []
    assert got['engine'] == 'codex' and got['model'] == 'gpt-6.1-sol' and got['role'] == role
    assert got['effort'] == 'high' and got['max_turns'] is None
    assert got['permission_mode'] is None and got['claude_bin'] is None and got['mcp_config'] is None
    assert got['codex_config'] == cfg
    assert ctx.calls[0][0] == ['python3','-I','-B',str(Path(ctx.fleet) / 'kyqualify.py'),'check',str(receipt),
                              '--config',got['launch_config_path'],'--require-context','launchd']


@pytest.mark.parametrize('content', [None, 'claude\n', 'verify=codex\n'])
def test_claude_launch_bytes_unchanged_and_never_checks_codex(ctx, content):
    binds = claude_receipt(ctx)
    if content is not None:
        (Path(ctx.run) / 'JOB_ENGINE').write_text(content)
    refusals, got = launch(ctx)
    expected = dict(model=binds['model'], effort=binds['effort'], permission_mode=binds['permission_mode'],
                    max_turns=binds['max_turns'], deadline='2026-10-13T01:00:00Z', claude_bin=binds['claude_bin'],
                    mcp_config=str(Path(ctx.fleet) / 'mcp.none.json'), extra_lean_flags=[], disallowed_tools=[])
    assert refusals == [] and json.dumps(got, sort_keys=True).encode() == json.dumps(expected, sort_keys=True).encode()
    assert ctx.calls == []


@pytest.mark.parametrize('content', ['', ' ', 'CODEX', 'unknown', 'build=unknown', 'build=codex\nbuild=claude',
    'codex\nclaude', 'unknown=codex', 'verify=codex\ngarbage', '# comment', 'codex\x00'])
def test_invalid_policy_never_falls_back(ctx, content):
    claude_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').write_text(content)
    refusals, got = launch(ctx)
    assert got is None and any('JOB_ENGINE' in r['detail'] for r in refusals)
    assert ctx.calls == []


def test_unreadable_policy_refuses(ctx):
    claude_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').mkdir()
    refusals, got = launch(ctx)
    assert got is None and 'JOB_ENGINE' in refusals[0]['detail']


def test_policy_refreshes_once_per_intent_tick_and_journals_invalid(ctx, monkeypatch):
    monkeypatch.setattr(B, '_compute', lambda *args: [])
    cfg, _ = codex_receipt(ctx)
    claude_receipt(ctx)
    switch = Path(ctx.run) / 'JOB_ENGINE'
    switch.write_text('codex\n')
    B.intents(ctx)
    switch.write_text('claude\n')
    assert launch(ctx)[1]['engine'] == 'codex'  # same tick snapshot
    B.intents(ctx)
    assert 'engine' not in launch(ctx)[1]
    switch.write_text('bad\n')
    B.intents(ctx)
    assert launch(ctx)[1] is None
    assert any('JOB_ENGINE' in str(entry) for entry in ctx.journal_entries)


@pytest.mark.parametrize('case', ['missing','failed','wrong_engine','wrong_model','wrong_effort','interactive','harness','chart'])
def test_codex_receipt_failures_never_use_available_claude(ctx, case):
    claude_receipt(ctx)
    cfg, receipt = codex_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('codex\n')
    doc = json.loads(receipt.read_text())
    if case == 'missing': receipt.unlink()
    elif case == 'failed': doc['result'] = 'FAIL'
    elif case == 'wrong_engine': doc['engine'] = 'claude'
    elif case == 'wrong_model': doc['model'] = 'other'
    elif case == 'wrong_effort': doc['binds']['effort'] = 'low'
    elif case == 'interactive': doc['context'] = 'interactive'
    elif case == 'harness': ctx.sh = lambda *args, **kw: (1, '', 'binds differ')
    if case != 'missing': ka.write_json(receipt, doc)
    refusals, got = launch(ctx, chart=case == 'chart')
    assert got is None and refusals


@pytest.mark.parametrize('role,parent', [('build','bootstrap-builder'),('verify','bootstrap-reviewer')])
def test_templates_match_schema_and_real_launcher_environment(role, parent, tmp_path, monkeypatch):
    path = FLEET / 'templates' / ('LAUNCH_CONFIG.' + role + '.codex.json')
    cfg = json.loads(path.read_text())
    baseline = json.loads((FLEET / 'templates' / ('LAUNCH_CONFIG.' + parent + '.codex.json')).read_text())
    assert Q.validate_codex_config(cfg) == []
    assert kyschema.validate(json.loads((FLEET / 'schemas/launch_config_codex.json').read_text()), cfg) == []
    for name in ('engine','model','effort','sandbox','network','commit_mode','work_root','deadline_seconds',
                 'codex_bin','codex_min_version','writable_dirs'):
        assert cfg.get(name) == baseline.get(name)
    assert cfg['worktree'] == '/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign'
    assert cfg['prompt_path'] == '/Users/Dev/kalayantra/fleet_live/cards/' + ('KARAKA.md' if role == 'build' else 'PARIKSAKA.md')
    helper = job_launcher_helpers()
    c = SimpleNamespace(repo=str(tmp_path), controller_id='test-controller')
    intent = dict(kind=role.upper(), role=role, item='KV3-T', key='template-test', locks=['item.KV3-T'],
                  stream='K' if role == 'build' else 'V', pool='builder' if role == 'build' else 'verifier')
    plan, why = J._plan(c, intent, 'b1' if role == 'build' else 'v1', {'tests': []})
    assert why is None
    job = dict(plan['state'], tmp_path=str(tmp_path), job_scratch=str(tmp_path), job_id='template-test', PRAVAHA=[])
    own = dict(HOME=str(tmp_path), USER='test', KY_ROOT='/Users/Dev/kalayantra', KY_RUN=str(tmp_path),
               KY_FLEET=str(FLEET), KY_SCRATCH=str(tmp_path))
    node = cfg['child_path'].split(':')[1]
    (tmp_path / 'NODE_BIN').write_text(node + '\n')
    isdir = helper['os'].path.isdir
    monkeypatch.setattr(helper['os'].path, 'isdir', lambda p: p == node or isdir(p))
    env = helper['job_environment'](job, own)
    assert cfg['env_names'] == [n for n, _ in env] and cfg['child_path'] == dict(env)['PATH']
    assert Q.resolve_env(cfg, dict(own, KY_STREAM=job['stream'], KY_LANE=job['slot'], KY_CONTROLLER_ID=c.controller_id))[1] == []
    listed = kymanifest.launch_config_of(dict(role=role, engine='codex'))
    assert listed in (FLEET / 'BOOTSTRAP_COMPONENTS.txt').read_text().splitlines()


def test_admitted_config_is_materialised_for_job_and_claude_header_cannot_override(ctx, tmp_path):
    cfg, _ = codex_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('build=codex\n')
    _, admitted = launch(ctx)
    intent = dict(kind='REWORK', role='rework', item='KV3-T', key='test-role', locks=['item.KV3-T'],
                  header={'model':'claude-opus-5-5','engine':'claude'})
    plan, why = J._plan(ctx, intent, 'b1', {'launch': admitted, 'tests': []})
    assert why is not None  # policy-pinned engine/model cannot be undone by a header
    intent['header'] = {}
    plan, why = J._plan(ctx, intent, 'b1', {'launch': admitted, 'tests': []})
    assert why is None
    job = plan['state']
    job.update(job_id='J-test', job_scratch=str(tmp_path), prompt_path=str(tmp_path / 'prompt'))
    J._codex_config(job, plan)
    actual = json.loads(Path(job['launch_config_path']).read_text())
    assert actual == dict(cfg, role='build', worktree=job['worktree'], prompt_path=job['prompt_path'])
    assert job['role'] == 'build' and job['engine'] == 'codex' and job['sandbox_mode'] == 'locked'
    assert job['launch_config_path'] == str(tmp_path / 'launch_config.json')
    assert plan['codex_config'] == cfg  # only a copy is adapted


def test_template_change_after_admission_refuses(ctx, tmp_path):
    cfg, _ = codex_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('codex')
    _, admitted = launch(ctx)
    intent = dict(kind='BUILD', role='build', item='KV3-T', key='test-role', locks=['item.KV3-T'])
    plan, why = J._plan(ctx, intent, 'b1', {'launch': admitted, 'tests': []})
    assert why is None
    Path(admitted['launch_config_path']).write_text('{}')
    job = dict(plan['state'], job_scratch=str(tmp_path), prompt_path=str(tmp_path / 'prompt'))
    with pytest.raises(J.engines.Refusal, match='template changed'):
        J._codex_config(job, plan)


@pytest.mark.parametrize('verifier', [False, True])
def test_derived_template_runs_through_accepted_launcher(tmp_path, verifier):
    from test_kyjob_engines import codex_world
    import test_kyjob as legacy
    import time
    w, _ = codex_world(tmp_path / 'shell', verifier=verifier)
    role = 'verify' if verifier else 'build'
    cfg = json.loads((FLEET / 'templates' / ('LAUNCH_CONFIG.' + role + '.codex.json')).read_text())
    cfg.update(codex_bin=str(w.program), child_path=w.child_path())
    if verifier: cfg['output_schema'] = str(FLEET / 'schemas/codex_reviewer_output.json')
    source = tmp_path / 'qualified-template.json'
    ka.write_json(source, cfg)
    w.state.update(role=role, launch_config_path=str(source), tests=[], se_ephe_path=None, swe_ephe_path=None,
                   deadline=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + cfg['deadline_seconds'] - 10)))
    plan = dict(codex_config=cfg, codex_config_sha256=ka.sha_file(source))
    J._codex_config(w.state, plan)
    w.header['deadline'] = w.state['deadline']
    Path(w.state['prompt_path']).write_bytes(w.prompt())
    legacy.write_json(w.state_path, w.state)
    completed = w.launch()
    assert completed.code == 0, completed.err
    recorded = json.loads((w.job_scratch / 'kyjob.launch.json').read_text())
    assert recorded['engine'] == 'codex' and recorded['env_names'] == sorted(cfg['env_names'])
    args = recorded['argv']
    assert args[args.index('-m') + 1] == 'gpt-6.1-sol'
    assert args[args.index('-C') + 1] == str(w.job_scratch if verifier else w.worktree)
    assert '--max-turns' not in args and '-s' in args and args[args.index('-s') + 1] == 'workspace-write'
    assert 'sandbox_workspace_write.network_access=false' in args
    if verifier:
        assert [call.split()[0] for call in w.boundary_calls()] == ['prepare', 'exec']
        (w.fleet / 'boundary.prepare.rc').write_text('1\n')
        assert w.launch().code == 65  # no unconfined fallback


def test_codex_job_root_preserves_real_seatbelt_source_and_git_boundary(tmp_path):
    from test_kyboundary import World, JOB
    w = World(tmp_path / 'boundary')
    # Simulate the accepted Codex -C JOB_SCRATCH: a descendant moving its cwd
    # cannot escape the actual kyboundary profile. No real Codex/sign-in.
    old_source = (w.wt / 'a.txt').read_bytes()
    old_git = (w.wt / '.git').read_bytes()
    run = w.bounded('cd "$S"; printf allowed > "$S/result-fixture.txt"; '
                    '! (printf forbidden > "$WT/a.txt"); ! (printf forbidden > "$WT/.git"); '
                    '! (printf forbidden > "$VIEW/a.txt")')
    assert run.returncode == 0, run.stderr
    assert (w.S / 'result-fixture.txt').read_text() == 'allowed'
    assert (w.wt / 'a.txt').read_bytes() == old_source and (w.wt / '.git').read_bytes() == old_git
    checked, evidence, _ = w.check()
    assert checked == 0 and evidence['head_unchanged'] is True and evidence['status_clean'] is True
    assert w.kyb('release', JOB).returncode == 0


@pytest.mark.parametrize('optional', ['tests', 'se_ephe_path', 'swe_ephe_path', 'fixture'])
def test_optional_job_environment_needs_its_own_qualification(ctx, tmp_path, optional):
    cfg, _ = codex_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('codex')
    _, admitted = launch(ctx)
    intent = dict(kind='BUILD', role='build', item='KV3-T', key='test-role', locks=['item.KV3-T'])
    plan, why = J._plan(ctx, intent, 'b1', {'launch': admitted, 'tests': []})
    assert why is None
    job = dict(plan['state'], job_scratch=str(tmp_path), prompt_path=str(tmp_path / 'prompt'))
    job[optional] = ['test_a.py'] if optional == 'tests' else {'fixture': True} if optional == 'fixture' else '/ephe'
    with pytest.raises(J.engines.Refusal, match='optional'):
        J._codex_config(job, plan)


def test_fifo_switch_refuses_without_opening_it(ctx, monkeypatch):
    import builtins
    import os
    switch = Path(ctx.run) / 'JOB_ENGINE'
    os.mkfifo(switch)
    original = builtins.open
    def guarded(path, *args, **kw):
        if str(path) == str(switch):
            pytest.fail('JOB_ENGINE reader tried opening a FIFO and could block the tick')
        return original(path, *args, **kw)
    monkeypatch.setattr(builtins, 'open', guarded)
    refusals, got = launch(ctx)
    assert got is None and 'JOB_ENGINE' in refusals[0]['detail']


def test_absent_switch_job_state_and_prompt_are_byte_identical_to_installed_bundle(ctx, tmp_path):
    import subprocess
    baseline_path = '00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_jobs.py'
    read = subprocess.run(['/usr/bin/git', '-C', str(FLEET.parents[3]), 'show', '4fca17c70a35abf84f6e077b6f9e8f35ed299cfd:' + baseline_path],
                          env={'PATH':'/usr/bin:/bin','GIT_OPTIONAL_LOCKS':'0'}, capture_output=True, check=True)
    baseline = {'__file__': str(FLEET / 'kyd_jobs.py'), '__name__':'installed_jobs_baseline'}
    exec(compile(read.stdout, baseline_path, 'exec'), baseline)
    claude_receipt(ctx)
    _, admitted = launch(ctx)
    intent = dict(kind='BUILD', role='build', item='KV3-T', key='claude-test', locks=['item.KV3-T'],
                  stream='K', pool='builder', header={'loop':1,'max_loops':3})
    facts = {'launch':admitted,'tests':[]}
    old, old_reason = baseline['_plan'](ctx, copy.deepcopy(intent), 'b1', copy.deepcopy(facts))
    new, new_reason = J._plan(ctx, copy.deepcopy(intent), 'b1', copy.deepcopy(facts))
    assert old_reason is new_reason is None
    serialise = lambda obj: json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()
    assert serialise(old['state']) == serialise(new['state'])
    old_job = dict(old['state'], job_id='J-test', job_scratch=str(tmp_path), prompt_path=str(tmp_path / 'prompt'))
    new_job = dict(new['state'], job_id='J-test', job_scratch=str(tmp_path), prompt_path=str(tmp_path / 'prompt'))
    baseline['_prompt'](old_job, old)
    before = Path(old_job['prompt_path']).read_bytes()
    J._prompt(new_job, new)
    assert before == Path(new_job['prompt_path']).read_bytes()


# Reuse the existing landing fixture: all Git/PR/claim writes are recorded doubles.
from test_kyjob_engines import land  # noqa: E402, F401


def test_policy_selected_builder_uses_controller_commit_push_and_pr(ctx, land):
    cfg, _ = codex_receipt(ctx)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('build=codex')
    refusals, admitted = launch(ctx)
    assert refusals == []
    intent = dict(kind='BUILD', role='build', item=land.job['item'], key=land.job['key'],
                  locks=land.job['locks'], packet=land.job['packet_path'], card=land.job['card_path'])
    plan, why = J._plan(land.ctx, intent, 'k1', {'launch':admitted, 'tests':[]})
    assert why is None
    land.job.update({k:plan['state'][k] for k in J.LAUNCH_FACTS + J.engines.FIELDS + ('role',)})
    J._codex_config(land.job, plan)
    land.job['checkpoint'].pop('codex_launch')
    land.E.prepare(land.ctx, land.job)
    J._save(land.ctx, land.job)
    raw = (Path(land.job['job_scratch']) / 'result.json').read_bytes()
    assert land.finish()['outcome'] == 'done'
    for verb in ('add','commit','push','create'):
        assert sum(verb in args for args in land.calls) == 1
    assert land.job['registered_head'] == land.head and land.job['pr'] == 27
    assert (Path(land.job['job_scratch']) / 'result.json').read_bytes() == raw
