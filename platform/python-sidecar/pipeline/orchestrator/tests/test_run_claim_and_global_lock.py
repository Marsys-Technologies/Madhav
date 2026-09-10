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


def test_claim_runnable_run_is_an_atomic_compare_and_swap() -> None:
    """Catches a terminalized run being revived by a late Cloud Run execution."""
    cur = Cursor([{"id": "run-1"}])
    conn = Connection()

    assert runner.claim_runnable_run(conn, cur, "run-1") is True
    assert cur.calls == [(
        "UPDATE build_runs SET state='running', started_at=COALESCE(started_at, NOW()) WHERE id=%s AND state IN ('planned', 'running') RETURNING id",
        ("run-1",),
    )]
    assert conn.commits == 1


def test_claim_loses_cleanly_after_dispatch_failure_terminalizes_run() -> None:
    """Catches work starting after the dispatcher already won the terminal-state race."""
    cur = Cursor([])
    conn = Connection()

    assert runner.claim_runnable_run(conn, cur, "run-1") is False
    assert conn.commits == 1


def test_claim_reclaims_a_running_run_after_session_locks_prove_owner_is_gone() -> None:
    """Catches a crash-after-claim defeating Cloud Run retry recovery."""
    cur = Cursor([{"id": "run-1"}])
    conn = Connection()

    assert runner.claim_runnable_run(conn, cur, "run-1") is True
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


def test_concurrency_cap_does_not_count_the_retrying_run_itself() -> None:
    """Catches a crashed running attempt blocking its own Cloud Run retry."""
    cur = Cursor([{"active": 5}])

    assert runner.count_other_running_runs(cur, "run-1") == 5
    assert cur.calls == [(
        "SELECT count(*) AS active FROM build_runs WHERE state='running' AND id<>%s",
        ("run-1",),
    )]
