"""test_n430_hygiene_retry.py: SS N-430 T4, ONE RETRY ON CONNECTION LOSS for read-only statements.

A read-only statement whose psql run fails with a dropped-connection message ('server closed the connection unexpectedly' and its equivalents) is run ONE more time after a short pause;
the read timing entry records `retries: 1`. A timeout, an SQL error, a second failure, and any statement that is not provably read-only are NOT retried (they are reported exactly as before).
Fake psql runner and fake clock: no database, no sleeping.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _n430_fakes import FakeClock, FakePsql, fail, ok  # noqa: E402

LOST = "psql: error: connection to server on socket \"/tmp/.s.PGSQL.5432\" failed: server closed the connection unexpectedly\n\tThis probably means the server terminated abnormally\n\tbefore or while processing the request."


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("SUVARNA_CENSUS_STATEMENT_CAP_SECS", raising=False)
    ac.drain_read_log()
    yield
    ac.drain_read_log()


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(ac, "time", c)
    return c


def test_a_dropped_connection_is_retried_once_after_a_pause_and_the_retry_is_recorded(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(LOST), ok(b"42\n")], clock=clock, elapsed=2.0)
    assert ac.psql("SELECT 42") == [["42"]]
    assert len(fake.calls) == 2 and fake.calls[0] == fake.calls[1], "the SAME statement, the same command line"
    assert clock.slept == [ac.CONN_RETRY_PAUSE_SECONDS]
    (e,) = ac.drain_read_log()
    assert e["retries"] == 1 and e["outcome"] == "ok" and e["seconds"] == 4.0          # both attempts are in the elapsed time


def test_a_first_try_success_records_no_retry_and_never_sleeps(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [ok()], clock=clock)
    ac.psql("SELECT 1")
    assert len(fake.calls) == 1 and clock.slept == []
    assert ac.drain_read_log()[0]["retries"] == 0


def test_a_second_failure_is_reported_as_before_with_the_second_error_line(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(LOST), fail("psql: error: connection to server was lost")])
    with pytest.raises(ac.Unknown) as ei:
        ac.psql("SELECT 1")
    assert len(fake.calls) == 2 and str(ei.value) == "psql: error: connection to server was lost"
    (e,) = ac.drain_read_log()
    assert e["retries"] == 1 and e["outcome"] == "error"


def test_the_retry_happens_at_most_once_even_if_every_attempt_drops(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(LOST)])                                      # the last outcome repeats forever
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 1")
    assert len(fake.calls) == 2 and len(clock.slept) == 1


@pytest.mark.parametrize("msg", ["psql: error: connection to server was lost", "psql: error: could not receive data from server: Connection reset by peer",
                                 "SSL SYSCALL error: EOF detected", "psql: error: no connection to the server", "Connection reset by peer"])
def test_the_equivalent_connection_reset_messages_are_retried(monkeypatch, clock, msg):
    fake = FakePsql(monkeypatch, ac, [fail(msg), ok()])
    ac.psql("SELECT 1")
    assert len(fake.calls) == 2


@pytest.mark.parametrize("stderr", ['ERROR:  canceling statement due to statement timeout', 'ERROR:  canceling statement due to lock timeout',
                                    'ERROR:  relation "x" does not exist', 'ERROR:  permission denied for table x',
                                    "psql: error: connection to server at \"db\" (10.0.0.1), port 5432 failed: Connection refused",
                                    "psql: error: connection to server failed: FATAL:  password authentication failed",
                                    'ERROR:  value "server closed the connection unexpectedly" is not valid',
                                    "FATAL:  terminating connection due to administrator command"])
def test_a_timeout_an_sql_error_or_a_refused_connection_is_never_retried(monkeypatch, clock, stderr):
    fake = FakePsql(monkeypatch, ac, [fail(stderr), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 1")
    assert len(fake.calls) == 1 and clock.slept == []


def test_a_client_side_timeout_is_never_retried(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, ["timeout", ok()])
    with pytest.raises(ac.CheckTimeout):
        ac.psql("SELECT 1")
    assert len(fake.calls) == 1 and clock.slept == []


@pytest.mark.parametrize("sql", ["INSERT INTO t VALUES (1)", "UPDATE t SET a = 1", "DELETE FROM t", "CREATE TABLE t(a int)", "DROP TABLE t", "TRUNCATE t",
                                 "SELECT nextval('s')", "SELECT setval('s', 1)", "SELECT * INTO t2 FROM t", "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x",
                                 "SELECT * FROM t FOR UPDATE", "COPY t TO '/tmp/x'", "SELECT pg_advisory_lock(1)", "VACUUM t", "SELECT lo_import('/x')", "CALL p()",
                                 "SELECT 1; INSERT INTO t VALUES (1)"])
def test_a_statement_that_is_not_provably_read_only_is_never_retried(monkeypatch, clock, sql):
    fake = FakePsql(monkeypatch, ac, [fail(LOST), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql(sql)
    assert len(fake.calls) == 1 and clock.slept == []
    assert ac.drain_read_log()[0]["retries"] == 0


@pytest.mark.parametrize("sql", ["SELECT 1", "  select a from t where b = 'x'", "WITH x AS (SELECT 1) SELECT * FROM x", "SHOW server_version",
                                 "SELECT created_at, updated_at, lockdown FROM t"])
def test_plain_reads_are_retry_safe(sql):
    assert ac._retry_safe([sql])


def test_the_integrity_runner_read_only_transaction_is_retried_too(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(LOST), ok(b"none\n")])
    assert ac.psql_read_only("SELECT true") == []
    assert len(fake.calls) == 2 and ac.drain_read_log()[0]["retries"] == 1
    assert "BEGIN READ ONLY" in fake.commands(0)


def test_a_dropped_connection_in_the_capped_runner_is_retried_too(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(LOST), ok()])
    assert ac._psql_run(["SELECT 1"], "\x1f", 30, None, cap=1000) == [["1"]]
    assert len(fake.calls) == 2


def test_the_retry_re_sends_the_cap_prelude_too(monkeypatch, clock):
    monkeypatch.setenv("SUVARNA_CENSUS_STATEMENT_CAP_SECS", "30")
    fake = FakePsql(monkeypatch, ac, [fail(LOST), ok()])
    ac.psql("SELECT 1")
    assert fake.commands(0) == fake.commands(1) == ["SET statement_timeout = 30000", "SET lock_timeout = 5000", "SELECT 1"]


def test_the_retry_shows_up_in_the_read_timings_summary(monkeypatch, clock):
    FakePsql(monkeypatch, ac, [fail(LOST), ok()])
    ac.set_read_asset("bo_laksana_rerank")
    with ac.read_label("Ldgr.source_presence"):
        ac.psql("SELECT 1")
    s = ac.read_timings_summary(ac.drain_read_log())
    assert s["per_asset"][0]["slowest"][0]["retries"] == 1
    ac.set_read_asset(None)


def test_a_dropped_connection_that_stays_dropped_is_still_an_errored_cell_not_a_timeout(monkeypatch, clock):
    """bo_laksana_rerank Ldgr.source_presence: a dropped connection that persists is a real failure (ERRORED), distinct from a timeout (T3)."""
    FakePsql(monkeypatch, ac, [fail(LOST)])
    with pytest.raises(ac.Unknown) as ei:
        ac.psql("SELECT 1")
    assert ac._read_timeout_kind(ei.value) is None
    errored = dict(v=ac.ERRORED, measured=f"check errored: {ei.value}")
    assert ac._read_failure_cell(ei.value, errored) is errored
