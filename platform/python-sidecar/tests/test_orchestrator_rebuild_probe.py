"""Orchestrator Convergence Phase 4 — generic rebuild-on-probe-fail primitive.

Proves:
  A. _probe_asset: service → health_probe GREEN/down; data → integrity_check_sql
     truthy/falsy/error.
  B. run_asset dispatch (metadata-driven, no layer branch):
     - check + rebuild + GREEN  → skip (mark lit, writer NOT run);
     - check + rebuild + FAIL + writer → regenerate (writer run) → re-probe;
     - check + rebuild + FAIL + no writer → error;
     - service without rebuild policy → existing health-probe path;
     - data without check → normal writer path.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar  # noqa: E402


# ── Fakes ───────────────────────────────────────────────────────────────────────

class FakeCur:
    def __init__(self, registry_row):
        self._registry_row = registry_row
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._registry_row


class FakeConn:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def _calls(monkeypatch):
    """Stub every dispatch helper to record which fired."""
    rec = {'probe': [], 'data_writer': 0, 'mark_green': 0, 'mark_error': 0, 'service_probe': 0}
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)
    monkeypatch.setattr(ar, '_mark_probe_green', lambda *a, **k: rec.__setitem__('mark_green', rec['mark_green'] + 1))
    monkeypatch.setattr(ar, 'mark_asset_error', lambda *a, **k: rec.__setitem__('mark_error', rec['mark_error'] + 1))
    monkeypatch.setattr(ar, '_run_service_health_probe', lambda *a, **k: rec.__setitem__('service_probe', rec['service_probe'] + 1))
    monkeypatch.setattr(ar, '_run_data_writer', lambda *a, **k: (rec.__setitem__('data_writer', rec['data_writer'] + 1) or True))
    return rec


# ── A. _probe_asset ──────────────────────────────────────────────────────────────

def test_probe_service_green(monkeypatch):
    monkeypatch.setattr('pipeline.orchestrator.service_probes.run_health_probe',
                        lambda aid, spec: {'status': 'GREEN', 'message': 'ok'})
    ok, msg = ar._probe_asset(FakeConn(), FakeCur(None), 'bg_x', {'health_probe': {}}, True)
    assert ok is True


def test_probe_service_down(monkeypatch):
    monkeypatch.setattr('pipeline.orchestrator.service_probes.run_health_probe',
                        lambda aid, spec: {'status': 'down', 'message': 'broken'})
    ok, msg = ar._probe_asset(FakeConn(), FakeCur(None), 'bg_x', {'health_probe': {}}, True)
    assert ok is False
    assert 'broken' in msg


def test_probe_integrity_sql_truthy():
    cur = FakeCur({'ok': True})
    ok, msg = ar._probe_asset(FakeConn(), cur, 'd', {'integrity_check_sql': 'SELECT true AS ok'}, False)
    assert ok is True


def test_probe_integrity_sql_falsy():
    cur = FakeCur({'ok': False})
    ok, _ = ar._probe_asset(FakeConn(), cur, 'd', {'integrity_check_sql': 'SELECT false AS ok'}, False)
    assert ok is False


def test_probe_no_check():
    ok, msg = ar._probe_asset(FakeConn(), FakeCur(None), 'd', {}, False)
    assert ok is False
    assert 'no check' in msg


# ── B. run_asset dispatch ────────────────────────────────────────────────────────

def _run(monkeypatch, registry_row, probe_results):
    """Drive run_asset with a controlled _probe_asset sequence."""
    rec = _calls(monkeypatch)
    seq = list(probe_results)
    monkeypatch.setattr(ar, '_probe_asset', lambda *a, **k: seq.pop(0))
    ar.run_asset(FakeConn(), FakeCur(registry_row), 'run-1', 'chart-C', 'asset_x', 0)
    return rec


def test_dispatch_green_skips_writer(monkeypatch):
    rec = _run(monkeypatch, {'asset_type': 'service', 'rebuild_on_probe_fail': True}, [(True, 'green')])
    assert rec['mark_green'] == 1
    assert rec['data_writer'] == 0
    assert rec['service_probe'] == 0


def test_dispatch_fail_regenerates_then_reprobes(monkeypatch):
    monkeypatch.setattr(ar, 'get_writer', lambda aid: object)  # writer exists
    rec = _run(monkeypatch,
               {'asset_type': 'service', 'rebuild_on_probe_fail': True},
               [(False, 'down'), (True, 'green')])  # fail → regen → green
    assert rec['data_writer'] == 1          # regenerated
    assert rec['mark_error'] == 0           # re-probe green ⇒ no error


def test_dispatch_fail_no_writer_errors(monkeypatch):
    monkeypatch.setattr(ar, 'get_writer', lambda aid: None)  # no writer to regenerate
    rec = _run(monkeypatch,
               {'asset_type': 'service', 'rebuild_on_probe_fail': True},
               [(False, 'down')])
    assert rec['data_writer'] == 0
    assert rec['mark_error'] == 1


def test_dispatch_regen_still_failing_errors(monkeypatch):
    monkeypatch.setattr(ar, 'get_writer', lambda aid: object)
    rec = _run(monkeypatch,
               {'asset_type': 'service', 'rebuild_on_probe_fail': True},
               [(False, 'down'), (False, 'still down')])  # regen didn't fix it
    assert rec['data_writer'] == 1
    assert rec['mark_error'] == 1


def test_dispatch_service_without_policy_uses_existing_probe(monkeypatch):
    rec = _calls(monkeypatch)
    ar.run_asset(FakeConn(), FakeCur({'asset_type': 'service', 'rebuild_on_probe_fail': False}),
                 'run-1', 'chart-C', 'bg_x', 0)
    assert rec['service_probe'] == 1
    assert rec['mark_green'] == 0


def test_dispatch_data_without_check_runs_writer(monkeypatch):
    rec = _calls(monkeypatch)
    ar.run_asset(FakeConn(), FakeCur({'asset_type': 'data', 'rebuild_on_probe_fail': False}),
                 'run-1', 'chart-C', 'ga_positions', 0)
    assert rec['data_writer'] == 1
    assert rec['service_probe'] == 0
