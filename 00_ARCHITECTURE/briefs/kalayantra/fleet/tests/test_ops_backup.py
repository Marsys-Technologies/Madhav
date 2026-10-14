"""No live database: recording transport; fake PostgreSQL tools on PATH."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
CORE = FLEET / "ops" / "common.py"
NAMES = ["ka_yojaka", "ka_sangam", "ka_vighnakara", "ka_gochara", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate", "ka_gochara_v5", "ka_vedha_gochara", "ph_muhurta"]

def load():
    assert CORE.exists(), "bounded operation adapters have not been implemented"
    if "ops_common_test" in sys.modules:
        return sys.modules["ops_common_test"]
    sys.path.insert(0, str(CORE.parent))
    spec = importlib.util.spec_from_file_location("ops_common_test", CORE)
    m = importlib.util.module_from_spec(spec)
    sys.modules["ops_common_test"] = m
    spec.loader.exec_module(m)
    return m

def scope():
    return {"schema": "ky.ops_scope/1", "registry": [dict(asset_id=n, layer_index="L3" if n.startswith("ka_") else "L4", scope="per_chart", is_active=True, has_writer=True, depends_on=[], target_table=n+"_data", count_sql="SELECT count(*) FROM "+n+"_data WHERE chart_id = '{chart_id}'", integrity_check_sql="SELECT true") for n in NAMES], "tables": [dict(schema="public", name=n+"_data", depends_on=[]) for n in NAMES]}

class FakeTransport:
    def __init__(self, s):
        self.s = s
        self.calls = []
        self.rows = {t["name"]: [dict(chart_id="fixture", value=1)] for t in s["tables"]}
        self.empty = True
        self.restore_damage = False
        self.run_state = "completed"
        self.asset_state = "lit"
        self.count = 1
        self.integrity = True
        self.executed = []
    def inspect_scope(self):
        self.calls.append("inspect")
        return self.s
    def snapshot(self):
        self.calls.append("snapshot")
        return "00000001-00000001-1"
    def measure(self, tables):
        self.calls.append("measure")
        return {name: {"rows": len(self.rows[name]), "sha256": hashlib.sha256(json.dumps(self.rows[name],sort_keys=True).encode()).hexdigest()} for name in tables}
    def close(self):
        self.calls.append("close")
    def empty_scratch(self):
        self.calls.append("empty")
        return self.empty
    def restored(self):
        self.calls.append("restored")
        self.empty = False
        if self.restore_damage:
            self.rows[next(iter(self.rows))][0]["value"] = 2
    def dependencies_ready(self, assets):
        self.calls.append("deps")
        return True
    def run_record(self, run_id):
        self.calls.append("run")
        return dict(id=run_id, chart_id="482012f1-710e-4a25-994a-93821f5871aa", action="rebuild", state="planned", plan=NAMES)
    def execute_rebuild(self, run_id, assets):
        self.executed.append((run_id, assets))
    def readback(self, run_id, assets):
        self.calls.append("readback")
        return {"state": self.run_state, "assets": [dict(asset_id=a, run_state="complete", throughput_state=self.asset_state, rows=self.count, integrity=self.integrity) for a in assets]}

@pytest.fixture
def rig(tmp_path, monkeypatch):
    s = scope()
    source = tmp_path / "scope.json"
    source.write_text(json.dumps(s))
    root = tmp_path / "ky"
    root.mkdir()
    monkeypatch.setenv("KY_ROOT", str(root))
    # Entirely synthetic, never connected. Do not expose connection values in test output.
    monkeypatch.setenv("DATABASE_URL", "postgresql://fixture:fixture@127.0.0.1:1/ky_restore")
    binary = tmp_path / "bin"
    binary.mkdir()
    log = tmp_path / "tools.jsonl"
    tool = """#!/usr/bin/env python3
import json, os, pathlib, sys
with open(LOG_PATH, 'a') as f:
    f.write(json.dumps({'tool': pathlib.Path(sys.argv[0]).name, 'argv': sys.argv[1:], 'env_names': sorted(os.environ)})+'\\n')
if pathlib.Path(FAIL_PATH).exists() and pathlib.Path(FAIL_PATH).read_text() == pathlib.Path(sys.argv[0]).name:
    print('private diagnostic suppressed', file=sys.stderr)
    sys.exit(1)
if pathlib.Path(sys.argv[0]).name == 'pg_dump':
    pathlib.Path(sys.argv[sys.argv.index('--file')+1]).write_text('-- fixture dump\\n')
"""
    for name in ("pg_dump", "psql"):
        p = binary / name
        p.write_text(tool.replace('LOG_PATH', repr(str(log))).replace('FAIL_PATH', repr(str(tmp_path/'fail'))))
        p.chmod(0o700)
    monkeypatch.setenv("PATH", str(binary)+os.pathsep+os.environ['PATH'])
    monkeypatch.setenv("FAKE_OPS_LOG", str(log))
    t = FakeTransport(s)
    return tmp_path, source, root, log, t

def args(source, key="test-key", label="backup-one"):
    return ["--scope", str(source), "--idempotency-key", key, "--label", label]

def call(kind, argv, t):
    return load().operate(kind, argv, transport=t)

def test_default_and_explicit_dryrun_have_exact_dump_plan_and_zero_effect(rig):
    tmp, source, root, log, t = rig
    before = sorted(str(p) for p in tmp.rglob('*'))
    record = call("backup_snapshot", args(source), t)
    assert record['schema'] == 'ky.op_adapter/1'
    assert record['mode'] == 'dry_run' and record['submitted'] is False
    assert record['restore_verified'] is None
    assert record['planned_argv'][0][0] == 'pg_dump'
    assert '--snapshot' in record['planned_argv'][0]
    assert record == call("backup_snapshot", ['--dry-run']+args(source), t)
    assert t.calls == [] and not log.exists()
    assert sorted(str(p) for p in tmp.rglob('*')) == before

@pytest.mark.parametrize('tail', [['--execute','--dry-run'], ['--label','twice'], ['--connection','forbidden']])
def test_ambiguous_repeated_and_unknown_args_refuse_without_effect(rig, tail):
    _, source, _, log, t = rig
    with pytest.raises(load().Refusal):
        call('backup_snapshot', args(source)+tail, t)
    assert not log.exists() and t.calls == []

def test_backup_binds_snapshot_dump_bytes_counts_and_content_and_never_claims_restore(rig):
    _, source, root, log, t = rig
    r = call('backup_snapshot', ['--execute']+args(source), t)
    assert r['backup_taken'] is True and r['restore_verified'] is None
    manifest = json.loads((root/'run/ops/artifacts/backup-one/manifest.json').read_text())
    assert manifest['snapshot'] == '00000001-00000001-1'
    assert manifest['measurements'] == t.measure(NAMES_TO_TABLES())
    assert all(x['rows'] == 1 for x in manifest['measurements'].values())
    assert log.exists()
    for line in log.read_text().splitlines():
        row = json.loads(line)
        assert not any('postgresql://' in a for a in row['argv'])
        assert 'PGPASSFILE' in row['env_names']
    assert t.calls.index('snapshot') < t.calls.index('measure') < t.calls.index('close')

def NAMES_TO_TABLES():
    return [n+'_data' for n in NAMES]

def test_duplicate_or_partial_key_never_reruns_dump(rig):
    _, source, _, log, t = rig
    call('backup_snapshot', ['--execute']+args(source), t)
    before = log.read_bytes()
    with pytest.raises(load().Refusal):
        call('backup_snapshot', ['--execute']+args(source), t)
    assert log.read_bytes() == before

@pytest.mark.parametrize('damage', ['digest', 'content', 'nonempty', 'unsafe_target'])
def test_restore_refuses_changed_backup_content_nonempty_or_nonlane_target(rig, monkeypatch, damage):
    _, source, root, log, t = rig
    call('backup_snapshot', ['--execute']+args(source), t)
    if damage == 'digest':
        (root/'run/ops/artifacts/backup-one/data.sql').write_text('corrupted')
    elif damage == 'content':
        t.restore_damage = True
    elif damage == 'nonempty':
        t.empty = False
    else:
        monkeypatch.setenv('DATABASE_URL', 'postgresql://fixture:fixture@remote.invalid:1/production')
    with pytest.raises(load().Refusal):
        call('backup_restore_verify', ['--execute']+args(source, key='restore-key'), t)

def test_restore_executes_one_transaction_and_compares_exact_content_and_counts(rig):
    _, source, _, log, t = rig
    call('backup_snapshot', ['--execute']+args(source), t)
    r = call('backup_restore_verify', ['--execute']+args(source, key='restore-key'), t)
    assert r['restore_verified'] is True
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    psql = [r for r in rows if r['tool']=='psql']
    assert len(psql) == 1 and '--single-transaction' in psql[0]['argv']
    assert psql[0]['argv'].count('--file') == 3

@pytest.mark.parametrize('kind', ['backup_snapshot','backup_restore_verify'])
def test_cli_dryrun_cannot_connect_even_without_connection_env(rig, kind):
    _, source, _, log, t = rig
    env = {k:v for k,v in os.environ.items() if k != 'DATABASE_URL'}
    p = subprocess.run([sys.executable,'-B',str(FLEET/'ops'/ (kind+'.py')), '--dry-run']+args(source), env=env, text=True, capture_output=True)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)['submitted'] is False
    assert not log.exists()

def test_runtime_scope_drift_and_dump_failure_fail_closed(rig, monkeypatch):
    _, source, _, log, t = rig
    t.s = json.loads(json.dumps(t.s))
    t.s['registry'][0]['depends_on']=['ka_avadhi']
    with pytest.raises(load().Refusal):
        call('backup_snapshot', ['--execute']+args(source), t)
    assert not log.exists()
    t.s = scope()
    (source.parent/'fail').write_text('pg_dump')
    with pytest.raises(load().Refusal):
        call('backup_snapshot', ['--execute']+args(source, key='dump-failure'), t)


def test_backup_scope_includes_secondary_layer_tables_and_pipeline_progress(rig):
    _,source,_,_,t=rig
    s=scope()
    for name in ['kala_extra_output','phala_extra_output','build_substep_progress','asset_build_receipts']:
        s['tables'].append(dict(schema='public',name=name,depends_on=[]))
    source.write_text(json.dumps(s))
    r=call('backup_snapshot',args(source),t)
    assert {'kala_extra_output','phala_extra_output','build_substep_progress','asset_build_receipts'} <= set(r['tables'])


def test_backup_then_restore_loads_predata_data_and_constraints_in_that_order(rig):
    _,source,_,log,t=rig
    call('backup_snapshot',['--execute']+args(source),t)
    call('backup_restore_verify',['--execute']+args(source,key='restore-three-sections'),t)
    rows=[json.loads(x) for x in log.read_text().splitlines()]
    assert len([x for x in rows if x['tool']=='pg_dump'])==3
    argv=next(x['argv'] for x in rows if x['tool']=='psql')
    files=[Path(argv[i+1]).name for i,x in enumerate(argv) if x=='--file']
    assert files==['schema.sql','data.sql','constraints.sql']


def test_real_measurement_digest_sees_same_count_changed_values_and_nulls():
    m=load()
    class Conn:
        def __init__(self): self.rows=[{'row':'{"v":null}'},{'row':'{"v":1}'}]
        def execute(self,sql):
            assert 'COLLATE "C"' in sql
            return iter(self.rows)
    t=m.Postgres.__new__(m.Postgres)
    t.conn=Conn()
    first=t.measure(['fixture'])
    t.conn.rows[1]={'row':'{"v":2}'}
    second=t.measure(['fixture'])
    assert first['fixture']['rows']==second['fixture']['rows']==2
    assert first['fixture']['sha256']!=second['fixture']['sha256']
