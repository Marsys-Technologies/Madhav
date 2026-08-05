"""
test_dasha_sentinel_savepoint_isolation.py — regression for the ga_dashas
scope-cap sentinel poisoning the ORCHESTRATOR's shared transaction.

── THE DEFECT (found live 2026-08-06, both canonical charts) ──────────────────
`write_dasha_scope_cap_sentinels()` builds a Prana-Dasha sentinel row with
`level_n = 5`. `chart_dashas` has carried
`CHECK ((level_n >= 1) AND (level_n <= 4))` — constraint `cd_level_n_max4`,
migration 211 — since long before that row existed, so the INSERT can NEVER
succeed. The write is wrapped in `try/except` and logged "(non-fatal)".

It is not non-fatal. A failed statement puts the PostgreSQL transaction into
INERROR; every subsequent statement on that connection raises
InFailedSqlTransaction until someone rolls back. Catching the Python exception
does not un-abort the transaction.

On the CLI path (`conn=None`) the function owns its own connection, so the
damage is contained and invisible. On the ORCHESTRATOR path the function runs
on the caller-owned `ctx.db_conn` under the FROZEN contract (§N.2) — so the
abort propagates out into the orchestrator, which then cannot even record the
failure:

    ga_dashas: Concurrency post-pass: updated 839 L1 rows
    ga_dashas: Scope-cap sentinel write failed (non-fatal):
      new row for relation "chart_dashas" violates check constraint "cd_level_n_max4"
    ga_dashas: KP scope-cap sentinel write failed (non-fatal):
      current transaction is aborted, commands ignored until end of transaction block
    orchestrator: writer ga_dashas failed: InFailedSqlTransaction
    orchestrator: worker crashed for ga_dashas
    orchestrator: crash-cleanup also failed for ga_dashas:
      can't change 'autocommit' now: connection in transaction status INERROR

`ga_dashas` therefore can never reach 'lit' via the orchestrator on ANY chart,
which transitively BLOCKS all 13 downstream assets. Observed identically on
482012f1, 1c826d5a and cb73cd3d.

── WHY THE EXISTING SUITE MISSED IT ──────────────────────────────────────────
Every test in `test_dasha_scope_cap_sentinel.py` monkeypatches `_upsert_rows`
with a stub that always SUCCEEDS, and asserts `written == 2` — an outcome that
has never once occurred in production. No test exercised a FAILING sentinel
write, and none exercised it against a connection with real transaction
semantics. The fake connection below models those semantics (a raised
statement poisons the connection until a ROLLBACK TO SAVEPOINT clears it), so
the orchestrator-path damage is visible to the suite.

NOTE ON SCOPE: this test pins the TRANSACTION-SAFETY property only. It does
NOT assert that the Prana sentinel writes — it still does not, and cannot,
while `level_n=5` contradicts `cd_level_n_max4`. Making that row land is a
separate SEMANTIC decision (how to represent "5th level, out of scope" inside
a 1-4 domain) reserved for the native. See this module's companion assertion
`test_prana_sentinel_still_does_not_write_pending_semantic_ruling`.

NO DB required.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as gdw  # noqa: E402


class FakeInFailedSqlTransaction(Exception):
    """Stands in for psycopg.errors.InFailedSqlTransaction."""


class FakeCheckViolation(Exception):
    """Stands in for psycopg.errors.CheckViolation on cd_level_n_max4."""


class FakeConn:
    """A connection with REAL PostgreSQL transaction-abort semantics.

    Once a statement raises, the connection is INERROR: every later statement
    raises InFailedSqlTransaction, until a `ROLLBACK TO SAVEPOINT <name>`
    clears it. This is the property the production defect turns on and the
    property the existing always-succeed stubs cannot express.
    """

    def __init__(self) -> None:
        self.aborted = False
        self.statements: list[str] = []
        self.savepoints: list[str] = []
        self.commits = 0

    # -- psycopg-ish surface the writer/savepoint helper uses ----------------
    def execute(self, sql: str, *args, **kwargs):
        stmt = sql.strip()
        upper = stmt.upper()
        self.statements.append(stmt)

        if upper.startswith("ROLLBACK TO SAVEPOINT"):
            # The ONLY way out of INERROR short of a full rollback.
            self.aborted = False
            return self
        if self.aborted:
            raise FakeInFailedSqlTransaction(
                "current transaction is aborted, commands ignored until "
                "end of transaction block"
            )
        if upper.startswith("SAVEPOINT"):
            self.savepoints.append(stmt.split()[-1])
        return self

    def cursor(self):
        return self

    def commit(self):
        if self.aborted:
            raise FakeInFailedSqlTransaction("cannot commit an aborted transaction")
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def poison(self) -> None:
        """Model the CHECK violation having aborted the transaction."""
        self.aborted = True


def _failing_then_ok_upsert(conn):
    """Mimics production exactly: the level_n=5 row violates cd_level_n_max4
    and poisons the connection; the level_n=4 row would be perfectly legal."""

    def _upsert(c, rows, system_id, ayanamsha_id, *, commit=True):
        # Any real _upsert_rows issues statements on the connection first.
        c.execute("DELETE FROM chart_dashas WHERE ...")
        if rows[0]["level_n"] > 4:
            c.poison()
            raise FakeCheckViolation(
                'new row for relation "chart_dashas" violates check '
                'constraint "cd_level_n_max4"'
            )
        c.execute("COPY chart_dashas ...")
        return len(rows)

    return _upsert


def test_sentinel_failure_does_not_leave_orchestrator_conn_aborted(monkeypatch):
    """THE regression assertion.

    After `write_dasha_scope_cap_sentinels()` returns on an INJECTED connection,
    that connection MUST still be usable — the orchestrator owns it and has to
    go on to RELEASE SAVEPOINT, write asset_throughput, and commit. Pre-fix the
    connection comes back INERROR and every one of those fails.
    """
    conn = FakeConn()
    monkeypatch.setattr(gdw, "_upsert_rows", _failing_then_ok_upsert(conn))

    gdw.write_dasha_scope_cap_sentinels("chart-XYZ", "build-123", conn=conn)

    assert not conn.aborted, (
        "the shared orchestrator connection was left in INERROR by a sentinel "
        "write the code calls '(non-fatal)' — this is the production defect: "
        "ga_dashas can never reach 'lit' and all 13 downstream assets BLOCK"
    )
    # And prove it concretely: the orchestrator's very next statement works.
    conn.execute("RELEASE SAVEPOINT writer_exec")


def test_kp_sentinel_is_attempted_on_a_clean_transaction(monkeypatch):
    """The level_n=4 KP sentinel is LEGAL under cd_level_n_max4. Pre-fix it
    never got a chance: it shared one aborted transaction with the level_n=5
    row and died with InFailedSqlTransaction. Post-fix it must be attempted on
    a clean connection and succeed."""
    conn = FakeConn()
    monkeypatch.setattr(gdw, "_upsert_rows", _failing_then_ok_upsert(conn))

    written = gdw.write_dasha_scope_cap_sentinels("chart-XYZ", "build-123", conn=conn)

    assert written == 1, (
        "expected exactly one sentinel to land: the KP level_n=4 row. "
        f"got written={written}"
    )


def test_prana_sentinel_still_does_not_write_pending_semantic_ruling(monkeypatch):
    """HONESTY PIN — SD-DASHA-1 is NOT fixed by the savepoint change.

    The Prana sentinel still does not write, because `level_n=5` still
    contradicts `cd_level_n_max4`. All the savepoint fix does is stop that
    failure from destroying the run. Production still holds ZERO rows at
    system_id='scope_cap', and will continue to until the native rules on how
    to represent "5th level, out of scope" within a 1-4 domain.

    This test exists so that anyone who later makes the Prana row land is
    forced to come here, read that, and delete this test deliberately.
    """
    conn = FakeConn()
    upserts: list[int] = []

    def _upsert(c, rows, system_id, ayanamsha_id, *, commit=True):
        if rows[0]["level_n"] > 4:
            c.poison()
            raise FakeCheckViolation("cd_level_n_max4")
        upserts.append(rows[0]["level_n"])
        return len(rows)

    monkeypatch.setattr(gdw, "_upsert_rows", _upsert)
    gdw.write_dasha_scope_cap_sentinels("chart-XYZ", "build-123", conn=conn)

    assert 5 not in upserts, "the Prana level_n=5 sentinel cannot land under cd_level_n_max4"
    assert upserts == [4], f"only the KP level_n=4 sentinel should land; got {upserts}"


def test_cli_path_also_isolates_each_sentinel(monkeypatch):
    """The owned-connection (CLI) path shares ONE connection across both
    sentinel writes too, so it has the same poisoning bug — it was merely
    invisible because the connection is discarded afterwards. Both paths must
    isolate."""
    conn = FakeConn()
    monkeypatch.setattr(gdw, "_upsert_rows", _failing_then_ok_upsert(conn))
    monkeypatch.setattr(gdw, "_conn", lambda: conn)

    written = gdw.write_dasha_scope_cap_sentinels("chart-XYZ", "build-123")

    assert not conn.aborted
    assert written == 1
    # The owned path still durably commits — once, after both sentinels, rather
    # than once per sentinel (a COMMIT inside a savepoint would discard it).
    assert conn.commits == 1
