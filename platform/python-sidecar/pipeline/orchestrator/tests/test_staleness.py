import pytest
from ..staleness import compute_downstream_ids, propagate_downstream_staleness

# Linear chain: ga_positions -> bo_laksana -> bo_bimba -> ph_result
REGISTRY = [
    {'asset_id': 'ga_positions', 'depends_on': []},
    {'asset_id': 'bo_laksana',   'depends_on': ['ga_positions']},
    {'asset_id': 'bo_bimba',     'depends_on': ['bo_laksana']},
    {'asset_id': 'ph_result',    'depends_on': ['bo_bimba']},
]

def test_compute_downstream_root():
    """Root asset: all others are downstream."""
    result = compute_downstream_ids('ga_positions', REGISTRY)
    assert result == {'bo_laksana', 'bo_bimba', 'ph_result'}

def test_compute_downstream_mid_chain():
    result = compute_downstream_ids('bo_laksana', REGISTRY)
    assert result == {'bo_bimba', 'ph_result'}

def test_compute_downstream_leaf():
    """Leaf asset: no downstream."""
    result = compute_downstream_ids('ph_result', REGISTRY)
    assert result == set()

def test_compute_downstream_does_not_include_self():
    result = compute_downstream_ids('bo_laksana', REGISTRY)
    assert 'bo_laksana' not in result

def test_compute_downstream_diamond():
    """Diamond dep: A -> B, A -> C, B -> D, C -> D. Downstream of A = {B, C, D}."""
    diamond = [
        {'asset_id': 'A', 'depends_on': []},
        {'asset_id': 'B', 'depends_on': ['A']},
        {'asset_id': 'C', 'depends_on': ['A']},
        {'asset_id': 'D', 'depends_on': ['B', 'C']},
    ]
    result = compute_downstream_ids('A', diamond)
    assert result == {'B', 'C', 'D'}
    # D must not appear twice (set dedup)
    assert len(result) == 3

def test_compute_downstream_isolated():
    """Asset with no dependents returns empty set."""
    result = compute_downstream_ids('ga_positions', [
        {'asset_id': 'ga_positions', 'depends_on': []},
    ])
    assert result == set()


# ── propagate_downstream_staleness — delta-directional gate (O-wave WP-1) ─────

class _FakeCursor:
    """Routes each execute() to a canned response by SQL substring, and records
    every statement for assertion. `output_changed_row` controls the very first
    query (the WP-1 delta signal lookup); `downstream_rows` controls the bulk
    UPDATE ... RETURNING that only runs when propagation proceeds."""

    def __init__(self, output_changed_row, downstream_rows=None):
        self._output_changed_row = output_changed_row
        self._downstream_rows = downstream_rows or []
        self.executed: list[tuple[str, object]] = []
        self._last_sql = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._last_sql = sql

    def fetchone(self):
        assert "SELECT output_changed" in self._last_sql
        return self._output_changed_row

    def fetchall(self):
        assert "RETURNING" in self._last_sql
        return self._downstream_rows


class _FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_no_delta_skips_propagation_and_emits_refreshed_no_delta():
    """output_changed=False (the writer reproduced identical output) must not
    touch any downstream row -- only the refreshed_no_delta signal fires."""
    cur = _FakeCursor(output_changed_row=(False,))
    conn = _FakeConn()
    events: list[dict] = []

    propagate_downstream_staleness(
        conn=conn, cur=cur, chart_id='chart-1', completed_asset_id='ga_positions',
        plan_set=set(), registry=REGISTRY, emit_fn=events.append, run_id='run-1',
    )

    assert len(cur.executed) == 1, "no downstream UPDATE should run on no-delta"
    assert events == [{
        "type": "asset.refreshed_no_delta", "chart_id": "chart-1",
        "asset_id": "ga_positions", "run_id": "run-1",
    }]
    assert conn.commits == 0


def test_delta_propagates_exactly_as_before():
    """output_changed=True must still mark transitive downstream stale."""
    cur = _FakeCursor(
        output_changed_row=(True,),
        downstream_rows=[('bo_laksana', 'lit'), ('bo_bimba', 'lit'), ('ph_result', 'lit')],
    )
    conn = _FakeConn()
    events: list[dict] = []

    propagate_downstream_staleness(
        conn=conn, cur=cur, chart_id='chart-1', completed_asset_id='ga_positions',
        plan_set=set(), registry=REGISTRY, emit_fn=events.append, run_id='run-1',
    )

    assert len(cur.executed) == 2, "the delta-signal SELECT, then the UPDATE ... RETURNING"
    assert "UPDATE asset_throughput" in cur.executed[1][0]
    staled_asset_ids = {e["asset_id"] for e in events}
    assert staled_asset_ids == {'bo_laksana', 'bo_bimba', 'ph_result'}
    assert all(e["to_state"] == "stale" for e in events)
    assert conn.commits == 1


def test_unknown_delta_signal_fails_open_and_propagates():
    """A missing build_run_assets row or NULL output_changed (probe/service
    asset, or a row predating migration 640) must never be read as no-delta --
    fail-open, propagate exactly as the pre-WP-1 code always did."""
    cur = _FakeCursor(output_changed_row=None, downstream_rows=[('bo_laksana', 'lit')])
    conn = _FakeConn()
    events: list[dict] = []

    propagate_downstream_staleness(
        conn=conn, cur=cur, chart_id='chart-1', completed_asset_id='ga_positions',
        plan_set=set(), registry=REGISTRY, emit_fn=events.append, run_id='run-1',
    )

    assert any(e["type"] == "asset.state_change" for e in events)
    assert not any(e["type"] == "asset.refreshed_no_delta" for e in events)
    assert conn.commits == 1


def test_no_downstream_targets_still_checks_the_delta_signal_first():
    """A leaf asset (no downstream) with output_changed=True returns early
    without an UPDATE -- but the delta-signal SELECT still ran."""
    cur = _FakeCursor(output_changed_row=(True,))
    conn = _FakeConn()
    events: list[dict] = []

    propagate_downstream_staleness(
        conn=conn, cur=cur, chart_id='chart-1', completed_asset_id='ph_result',
        plan_set=set(), registry=REGISTRY, emit_fn=events.append, run_id='run-1',
    )

    assert len(cur.executed) == 1
    assert events == []
    assert conn.commits == 0
