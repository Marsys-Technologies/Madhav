"""MR-39 gate: orchestrator build-session connections must disable the
server-side idle-in-transaction killer for the duration of the session.

GOCHARA-UTKARSA / PARIṢKĀRA register MR-39.

BACKGROUND (the defect this closes)
------------------------------------
`idle_in_transaction_session_timeout` defaults to 10 minutes at the DB-role
level. The orchestrator (and several standalone build-runner scripts that
bypass the orchestrator's own connection factory) hold a transaction open
while a writer's substep does CPU-heavy work with NO DB traffic — for a
substep whose compute exceeds ~10 minutes, the server kills the connection
mid-substep and the failure surfaces as a bare "connection lost" error with
no indication of the real cause.

`pipeline/orchestrator/db.py::connect()` — the factory used by `runner.py`
and `global_runner.py`, the two entry points that drive real chart builds —
already carried the fix (a SESSION-scoped `SET
idle_in_transaction_session_timeout = 0`, issued both via the libpq startup
`options` parameter and, defense-in-depth, as an explicit `SET` statement,
since a Cloud SQL Auth Proxy or pooler is not guaranteed to forward arbitrary
startup options) before this MR-39 pass. What MR-39 found and closed: three
standalone build-runner scripts at the sidecar root
(`run_heavy_writer_standalone.py`, `run_elev_beta_d_rebuild.py`,
`run_elev_beta_integration_rebuild.py`) drove real writer substeps via
`_run_data_writer` on a BARE `psycopg.connect()` that bypassed
`db.connect()` entirely — exactly the long-running-substep-with-no-DB-traffic
scenario this doctrine targets, unprotected. `run_ka_sangam_prod.py` /
`run_ph_pratikara_prod.py` needed to keep a `prepare_threshold=None` pooler
flag `db.connect()` does not set, so they were given the equivalent `SET`
directly instead.

GATE (per MR-39 register text)
-------------------------------
  (a) The connection factory issues the SET — structural + mock-based proof,
      no real DB required.
  (b) A lightweight local-postgres harness demonstrates the mechanism at a
      scaled timeout: SET idle_in_transaction_session_timeout='2s' on an
      un-fixed connection, idle 3s inside a transaction, observe the kill;
      then show the fixed setup survives. This repo already has an
      established pattern for exactly this (see
      tests/l2/test_n8_earned_signal_detectors.py's `N8_DETECTOR_TEST_DSN`-
      gated live layer) — skips (does not fail) unless
      `MR39_IDLE_TIMEOUT_TEST_DSN` points at a throwaway local Postgres, so
      CI without a DB does not silently report a green it did not earn.

To run layer (b):
    initdb -D /tmp/mr39pg -U postgres --auth=trust
    pg_ctl -D /tmp/mr39pg -o "-p 55433 -k /tmp" start
    MR39_IDLE_TIMEOUT_TEST_DSN="host=127.0.0.1 port=55433 dbname=postgres user=postgres" \
        pytest pipeline/orchestrator/tests/test_mr39_idle_timeout_connection_setup.py
"""
from __future__ import annotations

import os
import re
import time

import pytest

from .. import db as orchestrator_db


# ═══════════════════════════════════════════════════════════════════════════
# Layer (a) — structural + mock-based: the connection factory issues the SET,
# no real DB required.
# ═══════════════════════════════════════════════════════════════════════════


class _FakeCursor:
    def __init__(self, owner):
        self._owner = owner

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._owner.executed.append(sql)


class _FakeConn:
    def __init__(self):
        self.executed: list[str] = []
        self.committed = False

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        self.committed = True


def test_connect_issues_idle_timeout_set_statement(monkeypatch):
    """GATE (a): db.connect() must issue an explicit
    `SET idle_in_transaction_session_timeout = 0` after connecting — proven
    behaviorally (not just by reading the source), via a fake psycopg.connect
    that records every cursor.execute() call."""
    fake_conn = _FakeConn()
    monkeypatch.setattr(
        orchestrator_db.psycopg, "connect",
        lambda *a, **k: fake_conn,
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")

    result = orchestrator_db.connect()

    assert result is fake_conn
    set_statements = [
        sql for sql in fake_conn.executed
        if "idle_in_transaction_session_timeout" in sql
    ]
    assert set_statements, (
        "MR-39 GATE (a) FAILED: db.connect() did not issue any SQL statement "
        "containing 'idle_in_transaction_session_timeout' — a build session "
        "established via this factory would be vulnerable to the 10-minute "
        "server-side idle-in-transaction kill during long substep compute."
    )
    assert any(
        re.search(r"idle_in_transaction_session_timeout\s*=\s*0", sql)
        for sql in set_statements
    ), (
        f"MR-39 GATE (a) FAILED: the SET statement(s) found do not disable "
        f"the timeout (expect '= 0'). Found: {set_statements!r}"
    )
    assert fake_conn.committed, (
        "db.connect() must commit the session-setup SET statements so they "
        "are not left inside an open (rollback-able) transaction."
    )


def test_connect_startup_option_also_present(monkeypatch):
    """Defense-in-depth: the libpq startup `options` kwarg PASSED TO
    psycopg.connect() must also request idle_in_transaction_session_timeout=0,
    in case a pooler forwards startup options but strips a later SET
    (belt-and-suspenders, not either/or).

    PARĪKṢAKA F-1: the prior version of this test asserted
    `"idle_in_transaction_session_timeout" in inspect.getsource(...)` — a
    source-text grep that stays GREEN even if the `options=` kwarg is deleted
    entirely (as long as some other line, including a comment or the explicit
    SET string, still mentions the setting name) and even if BOTH the kwarg
    and the SET line are deleted, because the docstring/comments around
    `connect()` still name it. That is an unearned signal (§N.8): the
    assertion does not measure the specific claim ("the startup option is
    passed"), it measures "the substring appears somewhere in ~30 lines of
    source including four paragraphs of comments." Fixed to capture the
    ACTUAL kwargs passed to psycopg.connect() via a fake connect(), so only
    the real keyword argument value can satisfy it.
    """
    fake_conn = _FakeConn()
    captured_kwargs: dict = {}

    def _fake_connect(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return fake_conn

    monkeypatch.setattr(orchestrator_db.psycopg, "connect", _fake_connect)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/fake")

    orchestrator_db.connect()

    assert "options" in captured_kwargs, (
        "MR-39 GATE FAILED: db.connect() did not pass an 'options' kwarg to "
        "psycopg.connect() at all — the libpq startup-option defense-in-depth "
        f"layer is missing. kwargs passed: {captured_kwargs!r}"
    )
    assert "-c idle_in_transaction_session_timeout=0" in captured_kwargs["options"], (
        f"MR-39 GATE FAILED: the 'options' kwarg passed to psycopg.connect() "
        f"does not contain '-c idle_in_transaction_session_timeout=0'. "
        f"Got: {captured_kwargs['options']!r}"
    )


@pytest.mark.parametrize(
    "script",
    [
        "run_heavy_writer_standalone.py",
        "run_elev_beta_d_rebuild.py",
        "run_elev_beta_integration_rebuild.py",
    ],
)
def test_standalone_heavy_runners_route_through_orchestrator_connect(script):
    """MR-39: the standalone build-runner scripts that drive writer substeps
    via `_run_data_writer` (the exact long-compute-no-DB-traffic scenario)
    must route through `pipeline.orchestrator.db.connect()` — not a bare
    `psycopg.connect()` that bypasses the idle-timeout protection."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    path = os.path.join(root, script)
    assert os.path.isfile(path), f"expected standalone runner at {path!r}"
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    assert "from pipeline.orchestrator.db import connect" in source, (
        f"MR-39 regression: {script} must import the orchestrator's hardened "
        f"connection factory (pipeline.orchestrator.db.connect), not "
        f"establish its own bare psycopg.connect()."
    )
    # The bare psycopg.connect() CALL this MR-39 fix removed must not return
    # (comment lines that merely MENTION psycopg.connect() for explanatory
    # purposes are fine — strip full-line comments before checking).
    code_lines = [
        line for line in source.splitlines()
        if not line.strip().startswith("#")
    ]
    code_only = "\n".join(code_lines)
    assert not re.search(r"psycopg\.connect\(", code_only), (
        f"MR-39 regression: {script} still calls psycopg.connect() directly "
        f"— this bypasses the idle_in_transaction_session_timeout=0 "
        f"protection that pipeline.orchestrator.db.connect() provides."
    )


@pytest.mark.parametrize(
    "script",
    ["run_ka_sangam_prod.py", "run_ph_pratikara_prod.py"],
)
def test_prod_runners_set_idle_timeout_directly(script):
    """MR-39: run_ka_sangam_prod.py / run_ph_pratikara_prod.py keep their own
    `prepare_threshold=None` pooler-compatibility flag (so they cannot be
    routed wholesale through db.connect()), but must still issue the
    equivalent session-scoped SET immediately after connecting."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    path = os.path.join(root, script)
    assert os.path.isfile(path), f"expected standalone runner at {path!r}"
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    assert re.search(
        r"SET idle_in_transaction_session_timeout\s*=\s*0", source
    ), (
        f"MR-39 regression: {script} does not issue "
        f"'SET idle_in_transaction_session_timeout = 0' after connecting."
    )


# ═══════════════════════════════════════════════════════════════════════════
# Layer (b) — live can-fail proof: a real local Postgres, scaled timeout.
# Skips (not fails) unless MR39_IDLE_TIMEOUT_TEST_DSN is set — see module
# docstring for how to stand up the throwaway instance.
# ═══════════════════════════════════════════════════════════════════════════

_DSN = os.environ.get("MR39_IDLE_TIMEOUT_TEST_DSN", "")


@pytest.mark.skipif(not _DSN, reason="set MR39_IDLE_TIMEOUT_TEST_DSN to run the live can-fail proof")
def test_idle_timeout_mechanism_live_scaled_demo():
    """GATE (b): prove the mechanism against a real Postgres at a scaled
    timeout — an UN-fixed connection (default/short idle_in_transaction
    timeout) gets its connection killed while idle-in-transaction past the
    limit; a connection with idle_in_transaction_session_timeout=0 survives
    the identical idle window."""
    import psycopg

    # --- (1) UN-fixed session: a short server-side timeout kills a
    #         transaction left idle past the limit. ---
    unfixed = psycopg.connect(_DSN, autocommit=False)
    with unfixed.cursor() as cur:
        cur.execute("SET idle_in_transaction_session_timeout = '2s'")
    unfixed.commit()
    with unfixed.cursor() as cur:
        cur.execute("SELECT 1")
        unfixed.commit()  # close out the SET's own implicit txn cleanly
    # Open a fresh transaction and go idle past the 2s limit.
    with unfixed.cursor() as cur:
        cur.execute("SELECT 1")  # opens a transaction (autocommit=False)
    time.sleep(3.0)
    with pytest.raises(Exception) as excinfo:
        with unfixed.cursor() as cur:
            cur.execute("SELECT 1")
    # psycopg surfaces this as an OperationalError / connection-closed style
    # exception — the exact "bare connection-lost error" MR-39's register
    # text describes.
    assert excinfo.value is not None
    try:
        unfixed.close()
    except Exception:
        pass

    # --- (2) FIXED session (idle_in_transaction_session_timeout=0):
    #         survives an identical idle window with no error. ---
    fixed = psycopg.connect(_DSN, autocommit=False)
    with fixed.cursor() as cur:
        cur.execute("SET idle_in_transaction_session_timeout = 0")
    fixed.commit()
    with fixed.cursor() as cur:
        cur.execute("SELECT 1")  # opens a transaction
    time.sleep(3.0)  # idle well past the 2s window that killed the unfixed session
    with fixed.cursor() as cur:
        cur.execute("SELECT 1")
        row = cur.fetchone()
    fixed.commit()
    assert row[0] == 1, (
        "MR-39 GATE (b) FAILED: a connection with "
        "idle_in_transaction_session_timeout=0 was killed by an idle window "
        "that a genuinely fixed session should survive."
    )
    fixed.close()
