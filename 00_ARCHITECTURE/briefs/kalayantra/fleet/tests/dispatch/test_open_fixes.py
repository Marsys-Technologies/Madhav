"""Live OPEN refusal regressions; fixtures only, no live services or agents."""
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest
from test_job_engine_roles import ctx, launch, claude_receipt, codex_receipt, FLEET
import kyd_admit as A
import kyd_jobs as J
import kyd_kinds_build as B
import kyaction as ka
import kyqualify as Q


@pytest.mark.parametrize('foreign', ['ky.bootstrap_job_state/3', 'ky.legacy_job_state/1', 'cockpit-direct'])
def test_mapping_reader_skips_ledger_and_positively_foreign_folders(ctx, foreign):
    jobs = Path(ctx.run) / 'jobs'
    jobs.mkdir()
    (jobs / 'failures.json').write_text('{"attempts":{}}')
    folder = jobs / 'foreign'; folder.mkdir()
    doc = {'schema': foreign} if foreign != 'cockpit-direct' else {'launcher': foreign}
    doc['prerequisites'] = 'invalid foreign value'
    ka.write_json(folder / 'state.json', doc)
    assert A.recorded_mappings(ctx) == ({}, None)
    assert B._history(ctx, 'K-1') == []


def test_unreadable_native_mapping_stays_unknown(ctx):
    folder = Path(ctx.run) / 'jobs' / 'J-20261013T000000Z-b1'
    folder.mkdir(parents=True)
    (folder / 'state.json').write_text('{')
    assert A.recorded_mappings(ctx)[1] is not None


@pytest.mark.parametrize('kind', ['BUILD', 'REWORK', 'VERIFY'])
def test_chart_policy_selects_claude_chart_receipt_and_exact_missing_name(ctx, kind):
    (Path(ctx.run) / 'JOB_ENGINE').write_text('codex\n')
    claude_receipt(ctx, role=kind.lower())
    refusals, got = launch(ctx, kind, chart=True)
    exact = str(Path(ctx.run) / 'QUALIFICATIONS' / (kind.lower() + '-chart-claude-opus-5-5.json'))
    assert got is None and any(exact in r['detail'] for r in refusals)
    (Path(ctx.fleet) / 'mcp.marsys-only.json').write_text('{"mcpServers":{"marsys":{}}}')
    normal = Path(ctx.run) / 'QUALIFICATIONS' / (kind.lower() + '-claude-opus-5-5.json')
    doc = json.loads(normal.read_text())
    doc['binds']['mcp_config_sha256'] = ka.sha_file(Path(ctx.fleet) / 'mcp.marsys-only.json')
    ka.write_json(exact, doc)
    refusals, got = launch(ctx, kind, chart=True)
    assert refusals == [] and got['model'] == 'claude-opus-5-5'
    assert got['mcp_config'].endswith('/mcp.marsys-only.json')
    assert any('chart' in str(e) and 'Claude' in str(e) for e in ctx.journal_entries)


@pytest.mark.parametrize('role', ['build', 'rework', 'verify'])
def test_chart_template_preserves_parent_and_launcher_environment(role):
    cfg = json.loads((FLEET / 'templates' / ('LAUNCH_CONFIG.' + role + '.chart.json')).read_text())
    parent_role = 'build' if role == 'rework' else role
    baseline = json.loads((FLEET / 'templates' / ('LAUNCH_CONFIG.' + parent_role + '.json')).read_text())
    expected = dict(baseline, role=role, mcp_config='/Users/Dev/kalayantra/fleet_live/mcp.marsys-only.json')
    if role == 'rework': expected['max_turns'] = 100
    assert cfg == expected
    assert cfg['env_names'] == baseline['env_names']
    assert 'templates/LAUNCH_CONFIG.' + role + '.chart.json' in (FLEET / 'BOOTSTRAP_COMPONENTS.txt').read_text()


@pytest.fixture
def reviewed(tmp_path):
    repo = tmp_path / 'repo'; repo.mkdir()
    env = dict(PATH='/usr/bin:/bin', HOME=str(tmp_path), GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
               GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid', GIT_OPTIONAL_LOCKS='0')
    def git(*args):
        p = subprocess.run(['/usr/bin/git', *args], cwd=repo, env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        return p.stdout.strip()
    git('init', '-q', '-b', 'main')
    (repo / 'owned.py').write_text('before\n'); (repo / 'base.txt').write_text('base\n')
    git('add', '.'); git('commit', '-qm', 'base')
    git('checkout', '-qb', 'item')
    (repo / 'owned.py').write_text('reviewed\n'); git('commit', '-qam', 'item patch')
    old = git('rev-parse', 'HEAD')
    git('checkout', '-q', 'main')
    (repo / 'base.txt').write_text('base updated\n'); git('commit', '-qam', 'base update')
    git('checkout', '-q', 'item'); git('merge', '-qm', 'merge base', 'main')
    new = git('rev-parse', 'HEAD')
    git('update-ref', 'refs/remotes/origin/main', git('rev-parse', 'main'))
    c = SimpleNamespace(repo=str(repo), fleet=str(FLEET), run=str(tmp_path / 'run'), controller_id='fixture',
                        priority=['K-1'], next={'running':[{'id':'K-1','owner':'K','status':'review','completion_kind':'code'}]},
                        ledger=[{'kind':'item','item':'K-1','state':'review','actor':'stream-K:b2',
                                 'detail':'PR #12 @ ' + old}], calls=[], journal_entries=[])
    Path(c.run).mkdir()
    packet = repo / B.PACKETS / 'PACKET_K-1_v1.md'; packet.parent.mkdir(parents=True)
    packet.write_text('```json\n'+json.dumps({'id':'K-1','d1_paths':['owned.py'],'build_tier':'opus','max_loops':3})+'\n```\n')
    c.pr_value = {'number':12,'head':new,'base':'main','state':'OPEN','files':['owned.py'],
                  'checks':{'CI':{'status':'SUCCESS','attempt':1,'run_id':1}}}
    c.pr = lambda item: dict(c.pr_value)
    c.accepted = lambda item: None
    c.events = lambda item: list(c.ledger)
    c.verify = lambda item, step: False
    c.journal = lambda *args: c.journal_entries.append(args)
    def sh(argv, **kw):
        if argv[0] == 'git' or argv[0] == '/usr/bin/git':
            p = subprocess.run(argv, env=env, capture_output=True, text=True, **{k:v for k,v in kw.items() if k in ('cwd','timeout')})
            return p.returncode, p.stdout, p.stderr
        if 'kyroute.py' in ' '.join(argv): return 0, '{}', ''
        raise AssertionError(argv)
    c.sh = sh
    def ky(*args, stream=None, lane=None):
        c.calls.append(('ky',args,stream,lane))
        c.ledger.append({'kind':'item','item':'K-1','state':'review','actor':'stream-'+stream+':'+lane,
                         'detail':args[3]})
        return 0, '', ''
    c.ky = ky
    def act(action_id, kind, inputs, target, effect, observer):
        c.calls.append(('act',action_id,kind,inputs,target))
        return effect()
    c.act = act
    return c, git, old, new, packet


def test_merge_only_head_reregisters_and_then_verifies_new_head(reviewed):
    c, git, old, new, _ = reviewed
    intents = B.intents(c)
    assert len(intents) == 1
    intent = intents[0]
    assert intent['runner'] == 'script' and intent['header']['action'] == 'reregister_review'
    assert intent['head'] == new and intent['locks'] == ['item.K-1']
    job = dict(intent, job_id='J-fixture', **{'job_scratch':c.run})
    assert B.start(c, job)['outcome'] == 'done'
    assert B._registration(c.ledger)['head'] == new
    assert B._registration(c.ledger)['actor'] == 'stream-K:b2'
    verify = B.intents(c)[0]
    assert verify['kind'] == 'VERIFY' and verify['head'] == new and verify['not_slot'] == 'b2'
    assert any(x[0] == 'act' for x in c.calls)
    assert any('re-registration' in str(x) for x in c.journal_entries)


def test_changed_item_patch_is_unknown_and_never_reregistered(reviewed):
    c, git, _, _, _ = reviewed
    (Path(c.repo) / 'owned.py').write_text('changed\n'); git('commit','-qam','changed item')
    c.pr_value['head'] = git('rev-parse','HEAD')
    assert B.intents(c) == []
    assert any('patch_differs' in str(x) for x in c.journal_entries)
    assert c.calls == []



@pytest.mark.parametrize('outside', ['text', 'binary', 'rename'])
def test_unchanged_owned_patch_with_fresh_outside_edit_never_reregisters(reviewed, outside):
    c, git, old, _, _ = reviewed
    base_before = git('merge-base', 'origin/main', c.pr_value['head'])
    if outside == 'text':
        (Path(c.repo) / 'base.txt').write_text('fresh unrelated edit\n')
    elif outside == 'binary':
        (Path(c.repo) / 'outside.bin').write_bytes(b'\0fresh unrelated bytes\xff')
    else:
        git('mv', 'base.txt', 'renamed.txt')
    git('add', '.'); git('commit', '-qm', 'fresh outside edit')
    c.pr_value['head'] = git('rev-parse', 'HEAD')
    assert git('merge-base', 'origin/main', c.pr_value['head']) == base_before
    assert B.intents(c) == []
    assert B._registration(c.ledger)['head'] == old
    assert any('patch_differs' in str(x) for x in c.journal_entries)
    assert c.calls == []


def test_equal_whole_patch_already_outside_packet_scope_never_reregisters(reviewed):
    c, git, _, _, _ = reviewed
    git('checkout', '-q', 'main')
    git('checkout', '-qb', 'outside-item')
    (Path(c.repo) / 'owned.py').write_text('reviewed\n')
    (Path(c.repo) / 'outside.txt').write_text('unreviewable outside patch\n')
    git('add', '.'); git('commit', '-qm', 'item plus outside patch')
    old = git('rev-parse', 'HEAD')
    git('checkout', '-q', 'main')
    (Path(c.repo) / 'base.txt').write_text('next base update\n')
    git('commit', '-qam', 'advance base')
    git('update-ref', 'refs/remotes/origin/main', git('rev-parse', 'HEAD'))
    git('checkout', '-q', 'outside-item'); git('merge', '-qm', 'merge base', 'main')
    c.ledger[0]['detail'] = 'PR #12 @ ' + old
    c.pr_value['head'] = git('rev-parse', 'HEAD')
    assert B.intents(c) == []
    assert B._registration(c.ledger)['head'] == old and c.calls == []
    assert any('scope' in str(x) for x in c.journal_entries)


def test_identical_rebased_patch_reregisters(reviewed):
    c, git, old, _, _ = reviewed
    git('checkout', '-qb', 'rebased-item', old)
    git('rebase', 'main')
    new = git('rev-parse', 'HEAD')
    c.pr_value['head'] = new
    intents = B.intents(c)
    assert len(intents) == 1 and intents[0]['header']['action'] == 'reregister_review'
    job = dict(intents[0], job_id='J-fixture', job_scratch=c.run)
    assert B.start(c, job)['outcome'] == 'done'
    assert B._registration(c.ledger)['head'] == new
    assert B._registration(c.ledger)['actor'] == 'stream-K:b2'


@pytest.mark.parametrize('base', ['missing', 'unrelated'])
def test_unobserved_origin_base_never_falls_back_to_local_branch(reviewed, base):
    c, git, old, _, _ = reviewed
    if base == 'missing':
        git('update-ref', '-d', 'refs/remotes/origin/main')
    else:
        git('checkout', '--orphan', 'unrelated')
        git('commit', '-qam', 'unrelated root')
        git('update-ref', 'refs/remotes/origin/main', git('rev-parse', 'HEAD'))
    assert B.intents(c) == []
    assert B._registration(c.ledger)['head'] == old and c.calls == []
    assert any('unproven_base' in str(x) for x in c.journal_entries)


@pytest.mark.parametrize('operation', ['rev-parse', 'diff'])
@pytest.mark.parametrize('exit_code', [128, None])
def test_unavailable_whole_patch_observation_registers_nothing(reviewed, operation, exit_code):
    c, _, old, _, _ = reviewed
    old_sh = c.sh
    def sh(argv, **kw):
        if operation in argv:
            return exit_code, '', 'fixture unavailable'
        return old_sh(argv, **kw)
    c.sh = sh
    assert B.intents(c) == []
    assert B._registration(c.ledger)['head'] == old and c.calls == []
    assert c.journal_entries


def test_registration_action_rechecks_shrunken_packet_scope_at_same_head(reviewed):
    c, git, old, new, _ = reviewed
    intent = B.intents(c)[0]
    job = dict(intent, job_id='J-fixture', job_scratch=c.run)
    # Shrinking the packet after planning must also invalidate the controller's proof.
    packet = Path(intent['packet'])
    packet.write_text('```json\n{"id":"K-1","d1_paths":["base.txt"]}\n```\n')
    assert c.pr_value['head'] == new
    assert B.start(c, job)['outcome'] == 'refused'
    assert B._registration(c.ledger)['head'] == old and c.calls == []


def test_registration_action_rechecks_changed_head(reviewed):
    c, git, _, _, _ = reviewed
    intent = B.intents(c)[0]
    job = dict(intent, job_id='J-fixture', job_scratch=c.run)
    c.pr_value['head'] = 'f' * 40
    assert B.start(c, job)['outcome'] == 'refused'
    assert c.calls == []


def test_missing_packet_scope_never_inherits(reviewed):
    c, _, _, _, packet = reviewed
    packet.write_text('```json\n{"id":"K-1"}\n```\n')
    assert B.intents(c) == [] and c.calls == []
    assert any('scope' in str(x) for x in c.journal_entries)


def test_chart_launcher_uses_selected_variant_receipt(ctx):
    from test_kyqualify import job_launcher_helpers
    helper = job_launcher_helpers()
    state = dict(role='verify', model='claude-opus-5-5', mcp_config=str(Path(ctx.fleet)/'mcp.marsys-only.json'), tests=[])
    with pytest.raises(helper['Refuse']) as error:
        helper['check_qualification'](state, {'KY_RUN':ctx.run}, [], [], {}, None)
    assert 'verify-chart-claude-opus-5-5.json' in error.value.reason


@pytest.mark.parametrize('engine', ['claude', 'codex'])
def test_test_commit_environment_selects_qualified_tests_variant(ctx, engine):
    (Path(ctx.run) / 'JOB_ENGINE').write_text(engine)
    if engine == 'codex': codex_receipt(ctx)
    else: claude_receipt(ctx)
    refusals, facts = [], {}
    A._check_launch(ctx, dict(kind='BUILD',role='build',stream='K'), 'opus',
                    {'needs_chart_data':False, 'test_commits':[{'path':'test.py'}]}, True, refusals, facts)
    assert facts['launch'] is None
    assert any('build-tests-' in r['detail'] for r in refusals)


def test_test_environment_template_materialises_without_trimming_tests(ctx, tmp_path):
    cfg, _ = codex_receipt(ctx)
    cfg['env_names'].insert(cfg['env_names'].index('KY_SCRATCH'), 'TESTS')
    template = tmp_path / 'qualified-tests.json'; ka.write_json(template,cfg)
    job = dict(role='build',worktree=str(tmp_path),prompt_path=str(tmp_path/'prompt'),job_scratch=str(tmp_path),
               launch_config_path=str(template),tests=['test.py'],se_ephe_path=None,swe_ephe_path=None,fixture=None)
    J._codex_config(job, dict(codex_config=cfg,codex_config_sha256=ka.sha_file(template)))
    assert json.loads(Path(job['launch_config_path']).read_text())['env_names'] == cfg['env_names']
    assert job['tests'] == ['test.py']


def test_full_autonomy_copy_limits_are_owner_authorised():
    import kydispatch
    assert A.ALL_COPIES_MAX == 24
    assert kydispatch.COPIES == 16


@pytest.mark.parametrize('role,parent,cap,card', [('post-readback','verify',40,'PARIKSAKA.md'),
                                                 ('ruling','build',30,'ADHIKARIN.md')])
def test_live_missing_receipt_has_a_qualifiable_role_template(role,parent,cap,card):
    cfg=json.loads((FLEET/'templates'/('LAUNCH_CONFIG.'+role+'.json')).read_text())
    baseline=json.loads((FLEET/'templates'/('LAUNCH_CONFIG.'+parent+'.json')).read_text())
    assert cfg == dict(baseline,role=role,max_turns=cap,prompt_path='/Users/Dev/kalayantra/fleet_live/cards/'+card)


@pytest.mark.parametrize('role', ['build','rework','verify'])
@pytest.mark.parametrize('chart', [False,True])
def test_tests_variants_have_exact_real_launcher_environment(role,chart,tmp_path,monkeypatch):
    from test_kyqualify import job_launcher_helpers
    name='LAUNCH_CONFIG.'+role+('.chart' if chart else '')+'.tests.json'
    cfg=json.loads((FLEET/'templates'/name).read_text())
    assert Q.validate_config(cfg,check_disk=False) == []
    helper=job_launcher_helpers()
    job=dict(stream='V' if role=='verify' else 'K',slot='v1' if role=='verify' else 'b1',item='K-1',
             tmp_path=str(tmp_path),tests=['test.py'],se_ephe_path=None,swe_ephe_path=None,
             job_scratch=str(tmp_path),job_id='J-fixture',role=role,controller_id='fixture',PRAVAHA=[])
    own=dict(HOME=str(tmp_path),USER='fixture',KY_ROOT='/Users/Dev/kalayantra',KY_RUN=str(tmp_path),
             KY_FLEET=str(FLEET),KY_SCRATCH=str(tmp_path))
    (tmp_path/'NODE_BIN').write_text(cfg['child_path'].split(':')[1]+'\n')
    isdir=helper['os'].path.isdir
    monkeypatch.setattr(helper['os'].path,'isdir',lambda p:p==cfg['child_path'].split(':')[1] or isdir(p))
    env=helper['job_environment'](job,own)
    assert cfg['env_names'] == [n for n,_ in env]
    assert cfg['child_path'] == dict(env)['PATH']


@pytest.mark.parametrize('tests', [False,True])
def test_real_chart_launcher_reads_variant_and_preserves_bind_checks(tmp_path,tests):
    import test_kyjob as L
    w=L.World(tmp_path)
    w.state.update(role='build',tests=['test.py'] if tests else [],se_ephe_path=None,swe_ephe_path=None)
    mcp=w.fleet/'mcp.marsys-only.json';mcp.write_text('{"mcpServers":{"marsys":{}}}\n')
    w.state['mcp_config']=str(mcp)
    w.build()
    source=w.run/'QUALIFICATIONS/build-claude-opus-5-5.json'
    variant=w.run/('QUALIFICATIONS/build-chart'+('-tests' if tests else '')+'-claude-opus-5-5.json')
    source.rename(variant)
    # The install receipt must bind the actual chart configuration, not the empty MCP file.
    p=w.run/'INSTALL_RECEIPT.json'
    doc=json.loads(p.read_text())
    doc['components'].append({'path':'00_ARCHITECTURE/briefs/kalayantra/fleet/mcp.marsys-only.json',
                             'installed_path':str(mcp),'sha256':ka.sha_file(mcp)})
    p.write_text(json.dumps(doc))
    done=w.launch()
    assert done.code == 0,done.err
    receipt=json.loads(variant.read_text());receipt['binds']['mcp_config_sha256']='0'*64
    variant.write_text(json.dumps(receipt))
    done=w.launch()
    assert done.code == 65 and 'mcp_config_sha256' in done.err


def test_history_missing_native_state_is_unknown(ctx):
    folder=Path(ctx.run)/'jobs/J-20261013T000000Z-b1';folder.mkdir(parents=True)
    with pytest.raises(B._Unknown): B._history(ctx,'K-1')


def test_native_identity_wins_over_foreign_launcher_marker(ctx):
    folder=Path(ctx.run)/'jobs/J-20261013T000000Z-b1';folder.mkdir(parents=True)
    ka.write_json(folder/'state.json',{'schema':'ky.job/1','launcher':'cockpit-direct','prerequisites':'bad'})
    assert A.recorded_mappings(ctx)[1] is not None


def test_git_failure_during_scoped_base_derivation_stays_unknown(reviewed):
    c,_,_,_,_=reviewed
    old_sh=c.sh
    def sh(argv,**kw):
        if '--all' in argv: return 128,'','unavailable'
        return old_sh(argv,**kw)
    c.sh=sh
    assert B.intents(c) == []
    assert any('git_failed' in str(x) for x in c.journal_entries)



def test_rework_codex_pinned_tests_use_own_bound_variant(ctx, tmp_path):
    source = FLEET / 'templates' / 'LAUNCH_CONFIG.rework.tests.codex.json'
    assert source.is_file(), 'REWORK selects a tests variant of its own role, not BUILD'
    cfg = json.loads(source.read_text())
    parent, plain_receipt = codex_receipt(ctx, 'rework')
    assert {k:v for k,v in cfg.items() if k not in ('env_names','_note')} == {
        k:v for k,v in parent.items() if k not in ('env_names','_note')}
    assert Q.validate_codex_config(cfg, check_disk=False) == []
    template = Path(ctx.fleet) / 'templates' / source.name
    ka.write_json(template, cfg)
    receipt = Path(ctx.run) / 'QUALIFICATIONS' / 'rework-tests-gpt-6.1-sol.json'
    doc = json.loads(plain_receipt.read_text())
    doc['binds']['env_names'] = sorted(cfg['env_names'])
    ka.write_json(receipt, doc)
    (Path(ctx.run) / 'JOB_ENGINE').write_text('build=codex')
    refusals, facts = [], {}
    A._check_launch(ctx, dict(kind='REWORK', role='rework', stream='K', pool='builder'), 'opus',
                    {'needs_chart_data':False, 'test_commits':[{'path':'tests/test_a.py'}]}, True,
                    refusals, facts, slot='b1')
    assert refusals == []
    assert facts['launch']['launch_config_path'] == str(template)
    assert ctx.calls[0][0][5] == str(receipt)
    job = dict(role='rework', worktree=str(tmp_path), prompt_path=str(tmp_path/'prompt'),
               job_scratch=str(tmp_path), launch_config_path=str(template),
               tests=['tests/test_a.py','tests/test_b.py'], se_ephe_path=None, swe_ephe_path=None, fixture=None)
    J._codex_config(job, dict(codex_config=cfg,codex_config_sha256=ka.sha_file(template)))
    assert json.loads(Path(job['launch_config_path']).read_text())['env_names'] == cfg['env_names']
    assert job['tests'] == ['tests/test_a.py','tests/test_b.py']
