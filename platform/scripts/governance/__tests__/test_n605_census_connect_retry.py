"""test_n605_census_connect_retry.py: SS N-605 (c) / N-607, the census HARDENING of a failed psql connect.

The rev-30 census lost a psql CONNECT to libpq's 10 s connect timeout (`psql: error: connection to server at "127.0.0.1", port 5434 failed: timeout expired`). `_psql_run` retried only a connection dropped AFTER connecting; the failed connect raised an Unknown; `label_read` swallowed it into None; and `_apply_constant_phrases` printed `the live read did not happen` with no cause, so
bo_chart_gestalt's Null.blank_rows / Null.schema_default read PARTIAL although the data would have passed. Pinned here (N-607 narrowed the retry):
  (1) a connect that TIMED OUT is retried ONCE (`_CONNECT_TIMEOUT_LINE`, anchored: psql's `connection to server ... failed:` prefix and the timeout wording on the SAME line); a REFUSED connection, no route, an unreachable
      network, a missing socket, an auth failure, a statement / lock timeout, a permission error and any echoed statement or data literal are NOT retried and NOT classified as a connect failure;
  (2) the retry is `_psql_run`'s own one retry (two attempts in all for a label read's DISTINCT read; never a second loop on top), and a retried-then-ok read reads `retries: 1` in the read log and `read_timings`;
  (3) EVERY failed read, whatever the connect failure, carries its cause (`the live read did not happen (connection to server failed: Connection refused)`); no verdict changes (unread stays unread, never PASS, nothing FAILs).
Fake psql runner and fake clock (`_n430_fakes`): no database, no sleeping. `test_n430_hygiene_retry.py` is unchanged (it still pins that a refused connection is never retried).

MUTANTS (one-line source changes in asset_census.py; each run by hand against this file plus test_n430_hygiene_retry.py and each is KILLED):
  M1  `timeout expired` dropped from _CONNECT_TIMEOUT_LINE                     -> test_a_connect_timeout_is_a_connection_loss, test_label_read_recovers_after_one_connect_timeout
  M2  _psql_run never retries                                                  -> test_a_connect_timeout_is_retried_exactly_once, test_label_read_recovers_after_one_connect_timeout
  M3  the pattern widened to `refused` / `no route` / `unreachable`            -> test_a_refused_or_unreachable_connect_is_not_a_connection_loss, test_a_refused_connection_is_not_retried_but_says_why
  M4  the anchor dropped (`timeout expired` anywhere in the text)              -> test_text_that_merely_contains_the_words_is_never_a_connection_loss
  M5  label_read records no cause (DISTINCT failure) / (bounded failure)       -> test_label_read_says_why_when_both_attempts_fail, test_label_read_a_timeout_still_falls_back_*
  M6  grade_closed_phrases drops the cause                                     -> test_grade_closed_phrases_carries_the_cause_and_changes_no_verdict
  M7  grade_label_columns drops the cause                                      -> test_grade_label_columns_carries_the_cause_and_changes_no_verdict
  M8  the FATAL / ERROR guard removed from _is_connection_loss                 -> test_a_server_answer_is_never_a_connection_loss
  M9  unread_reason carries raw server text / host (no classification)        -> test_unread_reason_is_a_classification_never_raw_text, test_a_label_read_carries_a_classification_*
  M13 n_retried dropped from read_timings_summary / its report line           -> test_read_timings_counts_every_retried_read_not_only_the_slowest_five
  M14 the libpq 13 anchor widened (bare `could not connect to server ... timed out`) -> test_a_libpq_13_style_connect_failure_is_not_retried
  M10 the closed-phrase caller never passes the cause                          -> test_the_gestalt_scenario_a_connect_that_fails_twice_reads_partial_with_the_cause
  M11 the label-columns caller never passes the cause                          -> test_measure_prose_label_columns_carry_the_cause_and_the_verdict_is_unchanged
  M12 an unread closed entry is treated as stray (a verdict change)            -> test_grade_closed_phrases_carries_the_cause_and_changes_no_verdict
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n430_phrase_lists_closed as pl  # noqa: E402  (its fixtures for `_apply_constant_phrases`; none of its database fixtures are used here)
from _n430_fakes import FakeClock, FakePsql, fail, ok  # noqa: E402

CONNECT_TIMEOUT = 'psql: error: connection to server at "127.0.0.1", port 5434 failed: timeout expired'
REFUSED = ('psql: error: connection to server at "127.0.0.1", port 5434 failed: Connection refused\n\tIs the server running on that host and accepting TCP/IP connections?')
NO_ROUTE = 'psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: No route to host\n\tIs the server running on that host and accepting TCP/IP connections?'
UNREACHABLE = 'psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: Network is unreachable'
SOCKET_TIMEOUT = 'psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: timeout expired'
TCP_TIMED_OUT = 'psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: Connection timed out\n\tIs the server running on that host and accepting TCP/IP connections?'
SOCKET_MISSING = 'psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: No such file or directory\n\tIs the server running locally and accepting connections on that socket?'
OLD_REFUSED = "psql: could not connect to server: Connection refused\n\tIs the server running on host \"127.0.0.1\" and accepting TCP/IP connections on port 5434?"
OLD_TIMEOUT = "psql: timeout expired"
STATEMENT_TIMEOUT = "ERROR:  canceling statement due to statement timeout"
LOST = 'psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: server closed the connection unexpectedly\n\tThis probably means the server terminated abnormally'
AUTH = 'psql: error: connection to server at "127.0.0.1", port 5434 failed: FATAL:  password authentication failed for user "census"'
PERMISSION = "ERROR:  42501: permission denied for table chart_facts"


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("SUVARNA_CENSUS_STATEMENT_CAP_SECS", raising=False)
    ac.drain_read_log()
    ac._LABEL_UNREAD_WHY.clear()
    yield
    ac.drain_read_log()
    ac._LABEL_UNREAD_WHY.clear()
    ac.set_read_scope(None)


@pytest.fixture
def clock(monkeypatch):
    c = FakeClock()
    monkeypatch.setattr(ac, "time", c)
    return c


# ───────────────────────── (1) which texts are a connection failure ─────────────────────────

@pytest.mark.parametrize("text", [CONNECT_TIMEOUT, SOCKET_TIMEOUT, TCP_TIMED_OUT, CONNECT_TIMEOUT + "\n"])
def test_a_connect_timeout_is_a_connection_loss(text):
    assert ac._is_connection_loss(text) is True


@pytest.mark.parametrize("text", ["psql: error: connection to server was lost", "server closed the connection unexpectedly", "FATAL:  terminating connection due to administrator command\nserver closed the connection unexpectedly"])
def test_the_dropped_connection_markers_still_count(text):
    assert ac._is_connection_loss(text) is True


@pytest.mark.parametrize("text", [REFUSED, NO_ROUTE, UNREACHABLE, OLD_REFUSED, OLD_TIMEOUT, SOCKET_MISSING])
def test_a_refused_or_unreachable_connect_is_not_a_connection_loss(text):
    """N-607: a down proxy or database is surfaced, not masked; only a connect that TIMED OUT is retried (old libpq's bare `psql: timeout expired` has no connection-failure prefix, so it is not either)."""
    assert ac._is_connection_loss(text) is False


@pytest.mark.parametrize("text", [
    'ERROR:  invalid input syntax for type json\nLINE 1: SELECT * FROM t WHERE note = \'timeout expired\'\n                                        ^',
    'psql:<stdin>:1: LINE 1: select \'psql: error: connection to server at x failed: timeout expired\'',
    'ERROR:  value "psql: error: connection to server at x failed: timeout expired" is not valid',
    "DETAIL:  Key (note)=(connection timed out) already exists.",
    'LINE 1: ... WHERE note = \'timeout expired\' ...',
    'psql: error: something else mentioned: timeout expired',
    'psql: error: connection to server at "x", port 1 failed: Connection refused (the earlier attempt said: timeout expired)',
    'a data literal: connection to server at "x" failed: timeout expired'])
def test_text_that_merely_contains_the_words_is_never_a_connection_loss(text):
    assert ac._is_connection_loss(text) is False


@pytest.mark.parametrize("text", [STATEMENT_TIMEOUT, "ERROR:  canceling statement due to lock timeout", "psql:<stdin>:3: ERROR:  canceling statement due to statement timeout",
                                  f'psql: error: connection to server at "127.0.0.1", port 5434 failed: FATAL:  {STATEMENT_TIMEOUT[len("ERROR:  "):]}'])
def test_a_statement_or_lock_timeout_is_never_a_connection_loss(text):
    assert ac._is_connection_loss(text) is False


@pytest.mark.parametrize("text", [AUTH, 'psql: FATAL:  password authentication failed for user "census"', 'psql: error: connection to server at "127.0.0.1", port 5434 failed: FATAL:  database "x" does not exist',
                                  'psql: error: connection to server at "127.0.0.1", port 5434 failed: FATAL:  sorry, too many clients already',
                                  'psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: Permission denied'])
def test_an_authentication_or_other_fatal_answer_is_never_a_connection_loss(text):
    assert ac._is_connection_loss(text) is False


@pytest.mark.parametrize("text", [PERMISSION, 'ERROR:  permission denied for table chart_facts', 'ERROR:  relation "x" does not exist',
                                  'ERROR:  value "timeout expired" is not valid', 'psql:<stdin>:1: ERROR:  could not connect to server "fdw_remote"\nDETAIL:  Connection refused',
                                  'psql:<stdin>:1: ERROR:  invalid input: "connection refused"', 'FATAL:  timeout expired while waiting',
                                  'psql:<stdin>:1: ERROR:  invalid value in a stored note\nCONTEXT:  the value began a line:\npsql: error: connection to server at "x", port 1 failed: timeout expired'])
def test_a_server_answer_is_never_a_connection_loss(text):
    assert ac._is_connection_loss(text) is False


def test_the_loss_markers_are_the_original_drop_markers_and_the_timeout_pattern_is_anchored():
    assert ac._CONN_LOSS_MARKERS == ("server closed the connection unexpectedly", "connection to server was lost", "could not receive data from server",
                                     "ssl syscall error: eof detected", "connection reset by peer", "no connection to the server")
    assert ac._CONNECT_TIMEOUT_LINE.pattern.startswith("^psql:")


# ───────────────────────── (2) the retry: _psql_run's own, once ─────────────────────────

def test_a_connect_timeout_is_retried_exactly_once(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok(b"7\n")])
    assert ac.psql("SELECT 7") == [["7"]]
    assert len(fake.calls) == 2 and clock.slept == [ac.CONN_RETRY_PAUSE_SECONDS]
    assert ac.drain_read_log()[0]["retries"] == 1


def test_a_connect_timeout_that_keeps_failing_is_tried_twice_in_all(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT)])
    with pytest.raises(ac.Unknown) as ei:
        ac.psql("SELECT 7")
    assert len(fake.calls) == 2 and str(ei.value) == CONNECT_TIMEOUT


def test_a_write_is_not_retried_after_a_connect_timeout_either(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql("INSERT INTO t VALUES (1)")
    assert len(fake.calls) == 1


@pytest.mark.parametrize("text", [AUTH, STATEMENT_TIMEOUT, "ERROR:  canceling statement due to lock timeout", PERMISSION, REFUSED, NO_ROUTE, UNREACHABLE, OLD_REFUSED,
                                  'LINE 1: ... WHERE note = \'timeout expired\' ...'])
def test_an_auth_failure_a_timeout_a_permission_error_or_a_refused_connection_are_not_retried(monkeypatch, clock, text):
    fake = FakePsql(monkeypatch, ac, [fail(text), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 7")
    assert len(fake.calls) == 1 and clock.slept == []


def test_label_read_recovers_after_one_connect_timeout(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok(b"a\nb\n")])
    assert ac.label_read("t", "label", ["a", "b"]) == ["a", "b"]
    assert len(fake.calls) == 2 and ac.label_unread_why("t", "label") is None


def test_a_retried_then_ok_label_read_reads_retries_1_in_the_read_log_and_in_read_timings(monkeypatch, clock):
    """N-607 (5): the retry lives in _psql_run, which already records `retries`; a label read goes through it, so no extra plumbing is needed (and none was added)."""
    FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok(b"a\n")], clock=clock, elapsed=10.0)
    assert ac.label_read("t", "label", ["a"]) == ["a"]
    (entry,) = ac.drain_read_log()
    assert entry["retries"] == 1 and entry["outcome"] == "ok" and entry["seconds"] == 20.0 and "DISTINCT" in str(entry["label"])
    summary = ac.read_timings_summary([dict(entry, asset="bo_chart_gestalt")])
    assert summary["per_asset"][0]["slowest"][0]["retries"] == 1
    assert "retries 1" in ac.read_timings_report({"L2": {"read_timings": summary}})
    FakePsql(monkeypatch, ac, [ok(b"a\n")], clock=clock)
    assert ac.label_read("t", "label", ["a"]) == ["a"] and ac.drain_read_log()[0]["retries"] == 0


def test_the_real_label_distinct_sql_is_retry_safe_in_a_chart_scope():
    ac.set_read_scope({"bo_chart_gestalt": dict(where="chart_id = '482012f1-710e-4a25-994a-93821f5871aa'", label="measured chart")})
    for entry in ("defining_threads_jsonb.$.note", "label", "doc.$.items[*].k"):
        assert ac._retry_safe([ac.label_distinct_sql("bo_chart_gestalt", entry)]) and ac._retry_safe([ac.label_stray_sql("bo_chart_gestalt", entry, ["a"])])


# ───────────────────────── (3) the cause beside a read that did not happen ─────────────────────────

def test_label_read_says_why_when_both_attempts_fail(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT)])
    assert ac.label_read("t", "label", ["a"]) is None
    assert len(fake.calls) == 2                                                          # two attempts in all: no second loop on top of _psql_run's
    assert ac.label_unread_why("t", "label") == "connection to server failed: timeout expired"
    assert ac.label_unread_why("t", "label") is None                                     # taken once


@pytest.mark.parametrize("text,why", [(REFUSED, "connection to server failed: Connection refused"), (NO_ROUTE, "connection to server failed: No route to host"),
                                      (UNREACHABLE, "connection to server failed: Network is unreachable")])
def test_a_refused_connection_is_not_retried_but_says_why(monkeypatch, clock, text, why):
    """N-607 (3): the cause appears for ALL connect failures, even those that are not retried."""
    fake = FakePsql(monkeypatch, ac, [fail(text), ok(b"a\n")])
    assert ac.label_read("t", "label", ["a"]) is None
    assert len(fake.calls) == 1 and clock.slept == [] and ac.label_unread_why("t", "label") == why
    out = ac.grade_closed_phrases({"e": ["a"]}, {"e": None}, {"e": why})
    assert out["unread"] == {"e": f"the live read did not happen ({why})"} and out["stray"] == {} and out["stored"] == {}


def test_label_read_an_auth_failure_is_one_attempt_with_its_cause(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(AUTH)])
    assert ac.label_read("t", "label", ["a"]) is None
    assert len(fake.calls) == 1 and ac.label_unread_why("t", "label") == "connection to server failed: the server refused the session"


def test_label_read_a_timeout_still_falls_back_to_the_bounded_read_and_a_second_failure_says_so(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(STATEMENT_TIMEOUT), ok(b"")])
    assert ac.label_read("t", "label", ["a"]) == dict(stray=[], bounded=True) and len(fake.calls) == 2
    fake = FakePsql(monkeypatch, ac, [fail(STATEMENT_TIMEOUT)])
    assert ac.label_read("t", "label", ["a"]) is None and len(fake.calls) == 2           # a timeout is never retried
    assert ac.label_unread_why("t", "label") == "the DISTINCT read timed out and the bounded read failed too: statement timeout"


def test_a_successful_read_leaves_no_stale_cause(monkeypatch, clock):
    FakePsql(monkeypatch, ac, [fail(AUTH)])
    assert ac.label_read("t", "label", ["a"]) is None
    FakePsql(monkeypatch, ac, [ok(b"a\n")])
    assert ac.label_read("t", "label", ["a"]) == ["a"] and ac.label_unread_why("t", "label") is None


PG_HBA = 'psql: error: connection to server at "1.2.3.4", port 5432 failed: FATAL:  no pg_hba.conf entry for host "1.2.3.4", user "u", database "d", no encryption'
PG_HBA_BARE = 'FATAL:  no pg_hba.conf entry for host "1.2.3.4", user "u", database "d", SSL off'
ECHOED = 'ERROR:  invalid input syntax for type json\nLINE 1: SELECT * FROM secret_table WHERE note = \'permission denied for user census\'\n                                        ^'
LIBPQ13_NO_SOCKET = "psql: could not connect to server: No such file or directory\n\tIs the server running locally and accepting\n\tconnections on Unix domain socket \"/tmp/.s.PGSQL.5432\"?"


@pytest.mark.parametrize("exc,want", [
    (ac.Unknown(CONNECT_TIMEOUT), "connection to server failed: timeout expired"),
    (ac.Unknown(REFUSED), "connection to server failed: Connection refused"),
    (ac.Unknown(SOCKET_MISSING.splitlines()[0]), "connection to server failed: No such file or directory"),
    (ac.Unknown('psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: No route to host'), "connection to server failed: No route to host"),
    (ac.Unknown(UNREACHABLE), "connection to server failed: Network is unreachable"),
    (ac.Unknown(TCP_TIMED_OUT.splitlines()[0]), "connection to server failed: Connection timed out"),
    (ac.Unknown(AUTH), "connection to server failed: the server refused the session"),
    (ac.Unknown(PG_HBA), "connection to server failed: the server refused the session"),
    (ac.Unknown(LOST.splitlines()[0]), "connection lost"),
    (ac.Unknown(PG_HBA_BARE), "server refused the session"),
    (ac.Unknown('psql: FATAL:  password authentication failed for user "census"'), "server refused the session"),
    (ac.Unknown(STATEMENT_TIMEOUT), "statement timeout"),
    (ac.Unknown("ERROR:  canceling statement due to lock timeout"), "lock timeout"),
    (ac.CheckTimeout("client-side timeout after 180s (psql killed): SELECT secret FROM t"), "client timeout"),
    (ac.Unknown(PERMISSION), "permission denied"),
    (ac.Unknown('ERROR:  relation "chart_facts" does not exist'), "object does not exist"),
    (ac.ReadError("psql output is not valid UTF-8: ..."), "unreadable answer"),
    (ValueError("label entry 'a.$.*': wildcard refused\nsecond line"), "read refused"),
    (OSError("[Errno 2] No such file: /Users/x/psql"), "operating-system error"),
    (ac.Unknown(ECHOED), "read error"),
    (ac.Unknown(""), "read error"),
    (ac.Unknown("x" * 500), "read error")])
def test_unread_reason_is_a_classification_never_raw_text(exc, want):
    """N-605 review (A): cell text is committed under 00_ARCHITECTURE/control/census; no host, port, socket path, user, database, table, SQL or raw server text may reach it."""
    got = ac.unread_reason(exc)
    assert got == want and len(got) <= 80
    for leak in ("127.0.0.1", "5434", "1.2.3.4", "census", "pg_hba", "secret", "chart_facts", "10.0.0.1", "/tmp", "/Users", "LINE 1", "SELECT", '"'):
        assert leak not in got


@pytest.mark.parametrize("text", [PG_HBA, PG_HBA_BARE, AUTH, ECHOED])
def test_a_label_read_carries_a_classification_for_a_server_answer_never_the_raw_text(monkeypatch, clock, text):
    FakePsql(monkeypatch, ac, [fail(text)])
    assert ac.label_read("t", "label", ["a"]) is None
    why = ac.label_unread_why("t", "label")
    assert why in ("connection to server failed: the server refused the session", "server refused the session", "read error")
    out = ac.grade_closed_phrases({"e": ["a"]}, {"e": None}, {"e": why})
    assert all(x not in out["unread"]["e"] for x in ("1.2.3.4", "census", "pg_hba", "secret_table", "LINE 1"))


@pytest.mark.parametrize("text", [LIBPQ13_NO_SOCKET, "psql: could not connect to server: Connection refused\n\tIs the server running on host \"db\" and accepting TCP/IP connections on port 5432?",
                                  "psql: could not connect to server: Connection timed out\n\tIs the server running on host \"db\" (10.0.0.1) and accepting\n\tTCP/IP connections on port 5432?", OLD_TIMEOUT])
def test_a_libpq_13_style_connect_failure_is_not_retried(monkeypatch, clock, text):
    """The anchor needs libpq 14+'s `connection to server ... failed:` prefix; the old texts are surfaced (safe: no retry), with their cause classified."""
    assert ac._is_connection_loss(text) is False
    fake = FakePsql(monkeypatch, ac, [fail(text), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 1")
    assert len(fake.calls) == 1 and clock.slept == []


def test_read_timings_counts_every_retried_read_not_only_the_slowest_five():
    entries = [dict(asset="ga_a", label=f"r{i}", seconds=float(100 - i), retries=0, outcome="ok") for i in range(10)]
    entries += [dict(asset="ga_a", label=f"fast-retried-{i}", seconds=0.1, retries=1, outcome="ok") for i in range(3)]       # fast: they fall out of the five slowest
    entries.append(dict(asset="ga_b", label="failed-after-retry", seconds=0.2, retries=1, outcome="error"))
    sm = ac.read_timings_summary(entries)
    assert sm["n_retried"] == 4 and sm["n_reads"] == 14
    assert not any(r["retries"] for pa in sm["per_asset"] for r in pa["slowest"] if pa["asset"] == "ga_a")                          # none is visible in the bounded lists ...
    assert "4 read(s) retried" in ac.read_timings_report({"L2": {"read_timings": sm}})                                              # ... but the count is
    assert ac.read_timings_summary([])["n_retried"] == 0 and "retried" not in ac.read_timings_report({"L2": {"read_timings": ac.read_timings_summary(entries[:10])}})


LC = [dict(column="label", values=["a", "b"])]


def test_grade_label_columns_carries_the_cause_and_changes_no_verdict():
    plain = ac.grade_label_columns(LC, {"label": None})
    why = ac.grade_label_columns(LC, {"label": None}, {"label": "connection to server failed: timeout expired"})
    assert plain["v"] == why["v"] == ac.PARTIAL and plain["label_columns"]["unread"] == ["label"]
    assert why["label_columns"]["unread"] == ["label (the read did not happen: connection to server failed: timeout expired)"]
    assert "connection to server failed: timeout expired" in why["measured"]
    for k in ("closed", "undeclared", "declared_never_seen"):
        assert plain["label_columns"][k] == why["label_columns"][k]
    # a reason beside a read that DID happen is ignored: the verdicts are the same with and without it
    for got, v in ((["a"], ac.PASS), (["zzz"], ac.FAIL), (dict(stray=[], bounded=True), ac.PASS)):
        assert ac.grade_label_columns(LC, {"label": got}, {"label": "stale"})["v"] == v == ac.grade_label_columns(LC, {"label": got})["v"]


CORPUS = {"e.$.note": ["x"]}


def test_grade_closed_phrases_carries_the_cause_and_changes_no_verdict():
    plain = ac.grade_closed_phrases(CORPUS, {"e.$.note": None})
    why = ac.grade_closed_phrases(CORPUS, {"e.$.note": None}, {"e.$.note": "connection to server failed: timeout expired"})
    assert plain["unread"] == {"e.$.note": "the live read did not happen"}
    assert why["unread"] == {"e.$.note": "the live read did not happen (connection to server failed: timeout expired)"}
    assert plain["stray"] == why["stray"] == {} and plain["stored"] == why["stored"] == {}          # unread stays unread: never stray (a FAIL), never stored (a PASS)
    assert ac.grade_closed_phrases(CORPUS, {"e.$.note": None}, {"e.$.note": ""}) == plain
    assert ac.grade_closed_phrases(CORPUS, {"e.$.note": ["x"]}, {"e.$.note": "stale"}) == ac.grade_closed_phrases(CORPUS, {"e.$.note": ["x"]})
    assert ac.grade_closed_phrases(CORPUS, {"e.$.note": ["y"]}, {"e.$.note": "stale"})["stray"] == {"e.$.note": ["y"]}


# ───────────────────────── the rev-30 scenario, end to end (fake psql, real label_read and _apply_constant_phrases) ─────────────────────────

def _live(items=None):
    ac.set_read_scope({"gest": dict(where=f"chart_id = '{pl.CHART_A}'", label="measured chart")})
    return pl._apply(items or pl.CLOSED_ITEMS, ctx_extra=dict(own=pl.OWN))


def test_the_gestalt_scenario_a_failed_connect_is_retried_and_the_closure_is_earned(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok((pl.POINTER + "\n").encode()), ok((pl.SPINE + "\n").encode())])
    out, _ = _live()
    assert len(fake.calls) == 3
    assert all(out[c]["v"] == ac.PASS for c in ac.NULL_CHECKS), out["Null.blank_rows"]["measured"][:300]
    assert out["Narr.agree"]["v"] == ac.PARTIAL


def test_the_gestalt_scenario_a_connect_that_fails_twice_reads_partial_with_the_cause(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT)])
    out, _ = _live()
    assert len(fake.calls) == 4                                                          # two closed entries x two attempts
    for c in ac.NULL_CHECKS:
        assert out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c]                  # unread: never PASS
        assert "the live read did not happen (connection to server failed: timeout expired)" in out[c]["measured"]
        assert "127.0.0.1" not in out[c]["measured"]
    assert out["Narr.agree"]["v"] == ac.PARTIAL                                           # nothing FAILs on a read that did not happen


def test_the_gestalt_scenario_a_refused_connection_is_not_retried_and_the_cause_is_in_the_text(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(REFUSED)])
    out, _ = _live()
    assert len(fake.calls) == 2                                                          # two closed entries x ONE attempt
    for c in ac.NULL_CHECKS:
        assert out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c]
        assert "the live read did not happen (connection to server failed: Connection refused)" in out[c]["measured"]
    assert out["Narr.agree"]["v"] == ac.PARTIAL


def test_a_closed_entry_in_an_unowned_table_still_says_the_plain_text(monkeypatch):
    monkeypatch.setattr(ac, "label_read", lambda *a: pytest.fail("no owned table, so nothing is read"))
    out, _ = pl._apply(pl.CLOSED_ITEMS, ctx_extra=dict(own={"other": (["x"], {}, {})}))
    assert all(out[c]["v"] == ac.PARTIAL and "the live read did not happen (" not in out[c]["measured"] and "the live read did not happen" in out[c]["measured"] for c in ac.NULL_CHECKS)


def test_unreadable_owned_table_facts_say_why(monkeypatch):
    def boom(ctx):
        raise ac.Unknown("the column facts read failed")
    monkeypatch.setattr(ac, "_own3", boom)
    out, _ = pl._apply(pl.CLOSED_ITEMS, ctx_extra=dict())
    for c in ac.NULL_CHECKS:
        assert out[c]["v"] == ac.PARTIAL and "the live read did not happen (the owned-table facts could not be read: read error)" in out[c]["measured"]


def test_measure_prose_label_columns_carry_the_cause_and_the_verdict_is_unchanged(monkeypatch):
    """The real `_measure_prose` wiring of `label_columns` (psql replaced, as test_e5_7_decl_forms does): a failed DISTINCT read leaves the entry unread WITH its cause; never PASS, never FAIL."""
    decl = {"prose_fields": ["doc"], "evidence": {"prose_fields": "x.py:1"}, "label_columns": [dict(column="doc2.$.linking_mechanism", values=["domain_tension"])]}
    r = dict(target_table="t", count_sql="SELECT count(*) FROM t WHERE chart_id = $1")
    cat = dict(exists={"t"}, cols={"t": ["chart_id", "doc", "doc2"]}, types={"t": {"chart_id": "text", "doc": "text", "doc2": "jsonb"}}, defaults={"t": {}})

    def run(distinct):
        def fake(sql, *a, **k):
            if "DISTINCT" in sql:
                if isinstance(distinct, Exception):
                    raise distinct
                return [[v] for v in distinct]
            return [["0", "0"]]
        monkeypatch.setattr(ac, "psql", fake)
        return ac._measure_prose("a_x", decl, r, [], cat, [], set(), (), set())["Narr.agree"]
    ok_ = run(["domain_tension"])
    assert ok_["v"] != ac.FAIL and "hold only declared values" in ok_["measured"] and "did not happen" not in ok_["measured"]
    bad = run(ac.Unknown(CONNECT_TIMEOUT))
    assert bad["v"] not in (ac.PASS, ac.FAIL) and "connection to server failed: timeout expired" in bad["measured"] and "127.0.0.1" not in bad["measured"]
    assert bad["label_columns"]["unread"] == ["doc2.$.linking_mechanism (the read did not happen: connection to server failed: timeout expired)"]
    assert run(["domain_tension", "old_literal"])["v"] == ac.FAIL                          # a read that happened and found a stray value still FAILs
