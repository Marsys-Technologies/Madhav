from __future__ import annotations

from pipeline.orchestrator import locks, runner


class Cursor:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class Connection:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def test_claim_planned_run_is_an_atomic_compare_and_swap() -> None:
    """Catches a terminalized run being revived by a late Cloud Run execution."""
    cur = Cursor([{"id": "run-1"}])
    conn = Connection()

    assert runner.claim_planned_run(conn, cur, "run-1") is True
    assert cur.calls == [(
        "UPDATE build_runs SET state='running', started_at=COALESCE(started_at, NOW()) WHERE id=%s AND state='planned' RETURNING id",
        ("run-1",),
    )]
    assert conn.commits == 1


def test_claim_loses_cleanly_after_dispatch_failure_terminalizes_run() -> None:
    """Catches work starting after the dispatcher already won the terminal-state race."""
    cur = Cursor([])
    conn = Connection()

    assert runner.claim_planned_run(conn, cur, "run-1") is False
    assert conn.commits == 1


def test_global_asset_lock_uses_one_shared_session_key() -> None:
    """Catches different charts concurrently mutating global writer outputs."""
    cur = Cursor([{"got": True}])

    assert locks.acquire_global_assets_lock(cur) is True
    locks.release_global_assets_lock(cur)

    assert cur.calls == [
        (
            "SELECT pg_try_advisory_lock(hashtext(%s)) AS got",
            ("nirmana-global-assets",),
        ),
        (
            "SELECT pg_advisory_unlock(hashtext(%s))",
            ("nirmana-global-assets",),
        ),
    ]
