"""W3W4 rehearsal D10: a restart fences only an interrupted PRODUCTION kind (executor.py main(), interrupted_takes_fence).

Oracle source: executor_ops.json `production` flag per kind; fleet/executor.py module docstring ("A production operation in flight at a restart is
NEVER re-run: its receipt says INTERRUPTED" and "read-only operations are not fenced"; `*_dryrun` kinds are `production: false`, A8 §3.8)."""
import importlib.util
import json
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
TABLE = json.loads((FLEET / 'executor_ops.json').read_text())['ops']


def load():
    spec = importlib.util.spec_from_file_location('executor_restart_fence', FLEET / 'executor.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def restart(tmp_path, monkeypatch, request_body, table=TABLE):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    ex = load()
    ex.INFLIGHT.mkdir(parents=True)
    (ex.INFLIGHT / 'interrupted.json').write_text(request_body if isinstance(request_body, str) else json.dumps(request_body))
    (ex.RUN / 'STOP_executor').touch()
    monkeypatch.setattr(ex, 'load_table', lambda: table)
    monkeypatch.setattr(ex, 'capabilities', lambda _: {'none': True})
    monkeypatch.setattr(ex, 'log', lambda *a: None)
    assert ex.main() == 0
    receipt = json.loads((ex.REC / 'interrupted.json').read_text())
    assert receipt['status'] == 'INTERRUPTED'
    return ex


def req(kind):
    return dict(operation_id='interrupted', kind=kind, item_id='D10', requested_by='adhikarin', kyd='D10')


@pytest.mark.parametrize('kind', ['smalltest_dispatch_dryrun', 'publish_head_dryrun', 'readback_sql', 'cloudrun_job_readback', 'served_probe'])
def test_interrupted_dry_run_or_read_only_kind_takes_no_fence(tmp_path, monkeypatch, kind):
    assert TABLE[kind]['production'] is False
    ex = restart(tmp_path, monkeypatch, req(kind))
    assert not ex.FENCE.exists()


@pytest.mark.parametrize('kind', ['smalltest_dispatch', 'publish_head', 'layer_rollback'])
def test_interrupted_production_kind_fences(tmp_path, monkeypatch, kind):
    assert TABLE[kind]['production'] is True
    ex = restart(tmp_path, monkeypatch, req(kind))
    assert json.loads(ex.FENCE.read_text())['interrupted'] == ['interrupted.json']


def test_interrupted_unknown_kind_fences(tmp_path, monkeypatch):
    assert 'no_such_kind' not in TABLE
    assert restart(tmp_path, monkeypatch, req('no_such_kind')).FENCE.exists()


@pytest.mark.parametrize('table', [None, {}])
def test_unreadable_or_empty_table_fences_even_a_read_only_kind(tmp_path, monkeypatch, table):
    assert restart(tmp_path, monkeypatch, req('readback_sql'), table).FENCE.exists()


def test_unreadable_request_fences(tmp_path, monkeypatch):
    assert restart(tmp_path, monkeypatch, '{not json').FENCE.exists()


def test_failing_table_read_fences(tmp_path, monkeypatch):
    def boom(): raise OSError('git unavailable')
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    ex = load()
    ex.INFLIGHT.mkdir(parents=True)
    (ex.INFLIGHT / 'interrupted.json').write_text(json.dumps(req('readback_sql')))
    (ex.RUN / 'STOP_executor').touch()
    monkeypatch.setattr(ex, 'load_table', boom)
    monkeypatch.setattr(ex, 'capabilities', lambda _: {'none': True})
    monkeypatch.setattr(ex, 'log', lambda *a: None)
    assert ex.main() == 0 and ex.FENCE.exists()
