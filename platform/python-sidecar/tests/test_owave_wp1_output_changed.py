"""O-wave WP-1 (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.1) -- truthful
invalidation. Verifies _run_data_writer computes and durably records
build_run_assets.output_changed by comparing the freshly-computed
output_digest against the prior complete receipt's output_digest, BEFORE
capture_and_persist_receipt overwrites it.

All fakes -- no live DB. Writer is NOT @register-decorated (would pollute the
global registry and break test_has_writer_completeness).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar
from pipeline.orchestrator import output_digest as output_digest_module
from pipeline.orchestrator import provenance as provenance_module
from pipeline.orchestrator.writers import WriterBase, WriterResult


class FakeCursor:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []
        self._next_fetch = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        s = " ".join(sql.split())
        self._next_fetch = None
        if "SELECT integrity_check_sql FROM asset_registry" in s:
            self._next_fetch = {"integrity_check_sql": None}
        elif "SELECT target_floor FROM asset_registry" in s:
            self._next_fetch = {"target_floor": None}

    def fetchone(self):
        return self._next_fetch

    def fetchall(self):
        return []

    def params_for(self, keyword: str) -> list[tuple]:
        return [p for s, p in self.executed if keyword in s]


class FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _NonZeroRowWriter(WriterBase):
    asset_id = "_test_owave_wp1"

    def run(self, ctx):
        return WriterResult(asset_id=self.asset_id, rows_inserted=3, rows_updated=0)


def _run(monkeypatch, *, prior_output_digest, new_output_digest):
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "get_writer", lambda aid: _NonZeroRowWriter)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid, *a: "hash-upstream")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "hash-writer")
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(
        output_digest_module, "compute_output_digest",
        lambda cur, *, asset_id: (new_output_digest, "b" * 64),
    )
    monkeypatch.setattr(
        provenance_module, "previous_output_digest",
        lambda cur, *, asset_id, chart_id, partition_key: prior_output_digest,
    )
    captured_calls: list[dict] = []

    def _fake_capture(cur, **kwargs):
        captured_calls.append(kwargs)
        return ("fresh", [])

    monkeypatch.setattr(provenance_module, "capture_and_persist_receipt", _fake_capture)

    conn = FakeConn()
    cur = FakeCursor()
    ok = ar._run_data_writer(conn, cur, "run-1", "chart-abc", _NonZeroRowWriter.asset_id, declared_deps=[])
    return ok, cur, conn, captured_calls


def test_first_ever_build_with_no_prior_receipt_counts_as_changed(monkeypatch):
    """No prior receipt at all -- fail-open, never fake-fresh (§N.8)."""
    ok, cur, conn, _ = _run(monkeypatch, prior_output_digest=None, new_output_digest="output-a")
    assert ok is True
    calls = cur.params_for("SET output_changed")
    assert len(calls) == 1
    assert calls[0] == (True, "run-1", "_test_owave_wp1")
    assert conn.commits >= 1


def test_identical_output_records_output_changed_false(monkeypatch):
    """Same output_digest as the prior receipt -- an idempotent rebuild."""
    ok, cur, conn, _ = _run(monkeypatch, prior_output_digest="output-a", new_output_digest="output-a")
    assert ok is True
    calls = cur.params_for("SET output_changed")
    assert len(calls) == 1
    assert calls[0] == (False, "run-1", "_test_owave_wp1")


def test_different_output_records_output_changed_true(monkeypatch):
    ok, cur, conn, _ = _run(monkeypatch, prior_output_digest="output-a", new_output_digest="output-b")
    assert ok is True
    calls = cur.params_for("SET output_changed")
    assert len(calls) == 1
    assert calls[0] == (True, "run-1", "_test_owave_wp1")


def test_previous_output_digest_is_read_before_the_receipt_is_overwritten(monkeypatch):
    """Ordering matters: the prior receipt must be read BEFORE
    capture_and_persist_receipt overwrites it, or the comparison is against
    the asset's own freshly-written value and would always read unchanged."""
    call_order: list[str] = []
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "get_writer", lambda aid: _NonZeroRowWriter)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid, *a: "hash-upstream")
    monkeypatch.setattr(ar, "get_writer_source_hash", lambda aid: "hash-writer")
    monkeypatch.setattr(ar, "load_upstream_receipts", lambda cur, deps, cid: [])
    monkeypatch.setattr(
        output_digest_module, "compute_output_digest",
        lambda cur, *, asset_id: ("output-b", "b" * 64),
    )

    def _fake_previous(cur, *, asset_id, chart_id, partition_key):
        call_order.append("previous_output_digest")
        return "output-a"

    def _fake_capture(cur, **kwargs):
        call_order.append("capture_and_persist_receipt")
        return ("fresh", [])

    monkeypatch.setattr(provenance_module, "previous_output_digest", _fake_previous)
    monkeypatch.setattr(provenance_module, "capture_and_persist_receipt", _fake_capture)

    conn = FakeConn()
    cur = FakeCursor()
    ar._run_data_writer(conn, cur, "run-1", "chart-abc", _NonZeroRowWriter.asset_id, declared_deps=[])

    assert call_order == ["previous_output_digest", "capture_and_persist_receipt"]
