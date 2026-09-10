"""S7-LOCK gate: build-session connections must set lock_timeout='300s' and emit
a GUC smoke-log immediately after connection setup.

SAMPŪRTI-Δ1 RESTART EDITION — SM-R-4 binding protocol P1.

BACKGROUND
----------
Adds `SET lock_timeout = '300s'` to every build-session connection to bound
lock-wait hangs. A build connection that is blocked waiting to acquire a lock
for more than 5 minutes is a hang, not a legitimate slow operation — this
converts an otherwise indefinite stall into a recoverable error that the
conductor's FM-21 active hang watch can detect and redispatch from checkpoint.

Adds a GUC smoke-log (logged at INFO) immediately after connection setup that
reads `current_setting()` for all three key GUCs
(`idle_in_transaction_session_timeout`, `statement_timeout`, `lock_timeout`)
and logs them, providing per-run, per-connection ground truth in every job log
— closing the evidence gap from the 2026-08-14 stop-and-analyze investigation
(F-4: current_setting() queried on a different session ≠ ground truth for the
hung backend).

GATES
-----
  (a) db.py::connect() — orchestrator connection factory — issues
      `SET lock_timeout = '300s'` and emits GUC smoke-log (mock-based, no DB).
  (b) run_ka_sangam_prod.py::main() — issues `SET lock_timeout = '300s'` in
      the MR-39 block and emits GUC smoke-log (mock-based, no DB).
  (c) run_ph_pratikara_prod.py::main() — same as (b).
"""
from __future__ import annotations

import logging
import sys
import os

import pytest

# ─── path helpers ──────────────────────────────────────────────────────────────
# Resolve the sidecar root so we can import the standalone scripts as modules.
_SIDECAR_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _SIDECAR_ROOT not in sys.path:
    sys.path.insert(0, _SIDECAR_ROOT)

from .. import db as orchestrator_db  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
# Shared fake psycopg infrastructure (matches MR-39 pattern)
# ═══════════════════════════════════════════════════════════════════════════════


class _FakeCursor:
    """Fake cursor that records execute() calls and returns a canned row for SELECT."""

    def __init__(self, owner: "_FakeConn"):
        self._owner = owner
        self._last_row: dict | tuple | None = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql: str, params=None):
        self._owner.executed.append(sql)
        # If this is the GUC smoke-log SELECT, prime the fake row.
        if "current_setting" in sql and "idle_in_transaction_session_timeout" in sql:
            if self._owner.row_factory == "dict":
                self._last_row = {
                    "idle_in_txn": "1800000",
                    "stmt_timeout": "0",
                    "lock_timeout": "300s",
                }
            else:
                self._last_row = ("1800000", "0", "300s")

    def fetchone(self):
        return self._last_row


class _FakeConn:
    def __init__(self, row_factory: str = "dict"):
        self.executed: list[str] = []
        self.committed = False
        self.row_factory = row_factory

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        self.committed = True


# ═══════════════════════════════════════════════════════════════════════════════
# Gate (a) — db.py::connect()
# ═══════════════════════════════════════════════════════════════════════════════


def test_connect_issues_lock_timeout_set(monkeypatch):
    """S7-LOCK GATE (a-1): db.connect() must issue SET lock_timeout = '300s'."""
    fake_conn = _FakeConn(row_factory="dict")
    monkeypatch.setattr(orchestrator_db.psycopg, "connect", lambda *a, **k: fake_conn)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")

    orchestrator_db.connect()

    lock_stmts = [sql for sql in fake_conn.executed if "lock_timeout" in sql.lower()]
    assert lock_stmts, (
        "S7-LOCK GATE (a-1) FAILED: db.connect() did not issue any SQL statement "
        "containing 'lock_timeout' — build sessions would be vulnerable to "
        "indefinite lock-wait hangs."
    )
    assert any("300s" in sql or "300000" in sql for sql in lock_stmts), (
        f"S7-LOCK GATE (a-1) FAILED: lock_timeout SET found but does not use '300s'. "
        f"Found: {lock_stmts!r}"
    )


def test_connect_issues_guc_smoke_log(monkeypatch, caplog):
    """S7-LOCK GATE (a-2): db.connect() must read current_setting() for all 3 GUCs
    and log them at INFO with the '[GUC smoke-log]' prefix."""
    fake_conn = _FakeConn(row_factory="dict")
    monkeypatch.setattr(orchestrator_db.psycopg, "connect", lambda *a, **k: fake_conn)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")

    with caplog.at_level(logging.INFO, logger="pipeline.orchestrator.db"):
        orchestrator_db.connect()

    # Verify SELECT current_setting() was called
    select_stmts = [
        sql for sql in fake_conn.executed
        if "current_setting" in sql and "idle_in_transaction_session_timeout" in sql
    ]
    assert select_stmts, (
        "S7-LOCK GATE (a-2) FAILED: db.connect() did not execute a SELECT "
        "current_setting(...) query to read GUC ground truth after connection setup."
    )

    # Verify the smoke-log INFO message was emitted
    smoke_log_records = [
        r for r in caplog.records
        if "[GUC smoke-log]" in r.message and r.levelno == logging.INFO
    ]
    assert smoke_log_records, (
        "S7-LOCK GATE (a-2) FAILED: db.connect() did not emit a '[GUC smoke-log]' "
        "INFO log line after reading current_setting() — the per-connection GUC "
        "ground truth evidence is missing from job logs."
    )


def test_connect_guc_smoke_log_contains_all_three_gucs(monkeypatch, caplog):
    """S7-LOCK GATE (a-3): the GUC smoke-log message must mention all 3 GUC values."""
    fake_conn = _FakeConn(row_factory="dict")
    monkeypatch.setattr(orchestrator_db.psycopg, "connect", lambda *a, **k: fake_conn)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")

    with caplog.at_level(logging.INFO, logger="pipeline.orchestrator.db"):
        orchestrator_db.connect()

    smoke_log_messages = [
        r.message for r in caplog.records
        if "[GUC smoke-log]" in r.message
    ]
    assert smoke_log_messages, "No [GUC smoke-log] messages found — see gate (a-2)."

    combined = " ".join(smoke_log_messages)
    assert "idle_in_txn" in combined, (
        f"S7-LOCK GATE (a-3) FAILED: smoke-log does not mention idle_in_txn. "
        f"Messages: {smoke_log_messages!r}"
    )
    assert "statement_timeout" in combined or "stmt_timeout" in combined, (
        f"S7-LOCK GATE (a-3) FAILED: smoke-log does not mention statement_timeout. "
        f"Messages: {smoke_log_messages!r}"
    )
    assert "lock_timeout" in combined, (
        f"S7-LOCK GATE (a-3) FAILED: smoke-log does not mention lock_timeout. "
        f"Messages: {smoke_log_messages!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Gate (b) — run_ka_sangam_prod.py::main()
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# Gates (b) and (c) — standalone runners: source-level structural checks
#
# These scripts use `psycopg.connect()` directly (not the orchestrator factory)
# and have their own MR-39 block.  The MR-39 test (test_prod_runners_set_idle_
# timeout_directly) already uses source-text inspection for the structural
# assertion — we follow the same pattern here for the S7-LOCK additions.
# Behavioral mocking of these scripts is brittle because the scripts trigger
# @register at module import time (side-effecting the live _REGISTRY), making
# the registry-patch-before-import ordering impossible without importlib tricks.
# Source inspection is the correct tool for a "this statement must appear in
# the MR-39 block" claim, matching the precedent set by MR-39's own gate.
# ═══════════════════════════════════════════════════════════════════════════════


def _sidecar_root() -> str:
    """Return absolute path to the python-sidecar root directory."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


@pytest.mark.parametrize("script", ["run_ka_sangam_prod.py", "run_ph_pratikara_prod.py"])
def test_prod_runners_set_lock_timeout(script):
    """S7-LOCK GATE (b/c-1): run_ka_sangam_prod.py / run_ph_pratikara_prod.py must
    issue SET lock_timeout = '300s' in their MR-39 block."""
    path = os.path.join(_sidecar_root(), script)
    assert os.path.isfile(path), f"expected standalone runner at {path!r}"
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    import re
    assert re.search(r"SET lock_timeout\s*=\s*['\"]?300s['\"]?", source), (
        f"S7-LOCK GATE (b/c-1) FAILED: {script} does not issue "
        f"\"SET lock_timeout = '300s'\" in its MR-39 block — build sessions "
        f"would be vulnerable to indefinite lock-wait hangs."
    )


@pytest.mark.parametrize("script", ["run_ka_sangam_prod.py", "run_ph_pratikara_prod.py"])
def test_prod_runners_have_guc_smoke_log(script):
    """S7-LOCK GATE (b/c-2): run_ka_sangam_prod.py / run_ph_pratikara_prod.py must
    execute SELECT current_setting() for all 3 GUCs and log with [GUC smoke-log]."""
    path = os.path.join(_sidecar_root(), script)
    assert os.path.isfile(path), f"expected standalone runner at {path!r}"
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    assert "current_setting(" in source, (
        f"S7-LOCK GATE (b/c-2) FAILED: {script} does not call current_setting() "
        f"to read GUC ground truth after connection setup."
    )
    assert "[GUC smoke-log]" in source, (
        f"S7-LOCK GATE (b/c-2) FAILED: {script} does not emit a '[GUC smoke-log]' "
        f"log line — per-connection GUC evidence missing from job logs."
    )
    # All 3 GUC names must be referenced in the smoke-log SELECT / log call
    assert "idle_in_transaction_session_timeout" in source, (
        f"S7-LOCK GATE (b/c-2) FAILED: {script} smoke-log does not cover "
        f"idle_in_transaction_session_timeout."
    )
    assert "statement_timeout" in source, (
        f"S7-LOCK GATE (b/c-2) FAILED: {script} smoke-log does not cover statement_timeout."
    )
    assert "lock_timeout" in source, (
        f"S7-LOCK GATE (b/c-2) FAILED: {script} smoke-log does not cover lock_timeout."
    )
