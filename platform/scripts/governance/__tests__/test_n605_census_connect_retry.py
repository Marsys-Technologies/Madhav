"""test_n605_census_connect_retry.py: SS N-605 (c), the census HARDENING of a failed psql connect.

The rev-30 census lost a psql CONNECT to libpq's 10 s connect timeout (`psql: error: connection to server at "127.0.0.1", port 5434 failed: timeout expired`). `_psql_run` retried only a connection
dropped AFTER connecting; the failed connect raised an Unknown; `label_read` swallowed it into None; and `_apply_constant_phrases` printed `the live read did not happen` with no cause, so
bo_chart_gestalt's Null.blank_rows / Null.schema_default read PARTIAL although the data would have passed. Three changes, each pinned here:
  (1) a failed CONNECT is a retried connection failure (`_CONNECT_FAIL_MARKERS`); a statement timeout, a lock timeout, an auth failure, any `FATAL:` / `ERROR:` answer is NOT;
  (2) the retry is `_psql_run`'s own one retry (two attempts in all for a label read's DISTINCT read; never a second loop on top);
  (3) a read that did not happen carries its cause (`the live read did not happen (connection to server failed: timeout expired)`); no verdict changes (unread stays unread, never PASS, nothing FAILs).
Fake psql runner and fake clock (`_n430_fakes`): no database, no sleeping.

MUTANTS (each a one-line source change in asset_census.py; all eleven were run by hand against this file plus test_n430_hygiene_retry.py and each is KILLED):
  M1  `timeout expired` dropped from _CONNECT_FAIL_MARKERS            -> test_a_failed_connect_is_a_connection_loss, test_label_read_recovers_after_one_failed_connect
  M2  _psql_run never retries                                          -> test_a_failed_connect_is_retried_exactly_once, test_label_read_recovers_after_one_failed_connect
  M3  label_read records no cause (DISTINCT failure) / (bounded failure) -> test_label_read_says_why_when_both_attempts_fail, test_label_read_a_timeout_still_falls_back_*
  M4  grade_closed_phrases drops the cause                             -> test_grade_closed_phrases_carries_the_cause_and_changes_no_verdict
  M5  grade_label_columns drops the cause                              -> test_grade_label_columns_carries_the_cause_and_changes_no_verdict
  M6  the FATAL / ERROR guard removed from _is_connection_loss         -> test_a_server_answer_is_never_a_connection_loss
  M7  `connection refused` / `could not connect to server` dropped     -> test_a_failed_connect_is_a_connection_loss
  M8  unread_reason keeps host and port                                -> test_unread_reason_is_the_first_line_without_host_and_port
  M9  the closed-phrase caller never passes the cause                  -> test_the_gestalt_scenario_a_connect_that_fails_twice_reads_partial_with_the_cause
  M10 the label-columns caller never passes the cause                  -> test_measure_prose_label_columns_carry_the_cause_and_the_verdict_is_unchanged
  M11 an unread closed entry is treated as stray (a verdict change)    -> test_grade_closed_phrases_carries_the_cause_and_changes_no_verdict
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
SOCKET_MISSING = 'psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed: No such file or directory\n\tIs the server running locally and accepting connections on that socket?'
OLD_REFUSED = "psql: could not connect to server: Connection refused\n\tIs the server running on host \"127.0.0.1\" and accepting TCP/IP connections on port 5434?"
OLD_TIMEOUT = "psql: timeout expired"
STATEMENT_TIMEOUT = "ERROR:  canceling statement due to statement timeout"
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

@pytest.mark.parametrize("text", [CONNECT_TIMEOUT, REFUSED, OLD_REFUSED, OLD_TIMEOUT,
                                  'psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: Connection timed out',
                                  'psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: No route to host',
                                  'psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: Network is unreachable'])
def test_a_failed_connect_is_a_connection_loss(text):
    assert ac._is_connection_loss(text) is True


@pytest.mark.parametrize("text", ["psql: error: connection to server was lost", "server closed the connection unexpectedly", "FATAL:  terminating connection due to administrator command\nserver closed the connection unexpectedly"])
def test_the_dropped_connection_markers_still_count(text):
    assert ac._is_connection_loss(text) is True


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
                                  'psql:<stdin>:1: ERROR:  invalid input: "connection refused"', 'FATAL:  timeout expired while waiting'])
def test_a_server_answer_is_never_a_connection_loss(text):
    assert ac._is_connection_loss(text) is False


def test_a_missing_local_socket_is_deliberately_not_retried():
    """`No such file or directory` on a unix socket means no server is running locally: a retry one second later cannot help, and the census connects over TCP (127.0.0.1)."""
    assert ac._is_connection_loss(SOCKET_MISSING) is False


def test_every_connect_marker_is_part_of_the_loss_markers():
    assert set(ac._CONNECT_FAIL_MARKERS) <= set(ac._CONN_LOSS_MARKERS) and set(ac._CONN_DROP_MARKERS) <= set(ac._CONN_LOSS_MARKERS)


# ───────────────────────── (2) the retry: _psql_run's own, once ─────────────────────────

def test_a_failed_connect_is_retried_exactly_once(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok(b"7\n")])
    assert ac.psql("SELECT 7") == [["7"]]
    assert len(fake.calls) == 2 and clock.slept == [ac.CONN_RETRY_PAUSE_SECONDS]
    assert ac.drain_read_log()[0]["retries"] == 1


def test_a_failed_connect_that_keeps_failing_is_tried_twice_in_all(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT)])
    with pytest.raises(ac.Unknown) as ei:
        ac.psql("SELECT 7")
    assert len(fake.calls) == 2 and str(ei.value) == CONNECT_TIMEOUT


def test_a_write_is_not_retried_after_a_failed_connect_either(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql("INSERT INTO t VALUES (1)")
    assert len(fake.calls) == 1


@pytest.mark.parametrize("text", [AUTH, STATEMENT_TIMEOUT, PERMISSION])
def test_an_auth_failure_a_timeout_and_a_permission_error_are_not_retried(monkeypatch, clock, text):
    fake = FakePsql(monkeypatch, ac, [fail(text), ok()])
    with pytest.raises(ac.Unknown):
        ac.psql("SELECT 7")
    assert len(fake.calls) == 1 and clock.slept == []


def test_label_read_recovers_after_one_failed_connect(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(CONNECT_TIMEOUT), ok(b"a\nb\n")])
    assert ac.label_read("t", "label", ["a", "b"]) == ["a", "b"]
    assert len(fake.calls) == 2 and ac.label_unread_why("t", "label") is None


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


def test_label_read_an_auth_failure_is_one_attempt_with_its_cause(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(AUTH)])
    assert ac.label_read("t", "label", ["a"]) is None
    assert len(fake.calls) == 1 and ac.label_unread_why("t", "label") == 'connection to server failed: FATAL:  password authentication failed for user "census"'


def test_label_read_a_timeout_still_falls_back_to_the_bounded_read_and_a_second_failure_says_so(monkeypatch, clock):
    fake = FakePsql(monkeypatch, ac, [fail(STATEMENT_TIMEOUT), ok(b"")])
    assert ac.label_read("t", "label", ["a"]) == dict(stray=[], bounded=True) and len(fake.calls) == 2
    fake = FakePsql(monkeypatch, ac, [fail(STATEMENT_TIMEOUT)])
    assert ac.label_read("t", "label", ["a"]) is None and len(fake.calls) == 2           # a timeout is never retried
    assert ac.label_unread_why("t", "label") == "the DISTINCT read timed out and the bounded read failed too: canceling statement due to statement timeout"


def test_a_successful_read_leaves_no_stale_cause(monkeypatch, clock):
    FakePsql(monkeypatch, ac, [fail(AUTH)])
    assert ac.label_read("t", "label", ["a"]) is None
    FakePsql(monkeypatch, ac, [ok(b"a\n")])
    assert ac.label_read("t", "label", ["a"]) == ["a"] and ac.label_unread_why("t", "label") is None


@pytest.mark.parametrize("exc,want", [
    (ac.Unknown(CONNECT_TIMEOUT), "connection to server failed: timeout expired"),
    (ac.Unknown(REFUSED), "connection to server failed: Connection refused"),
    (ac.Unknown(SOCKET_MISSING.splitlines()[0]), "connection to server failed: No such file or directory"),
    (ac.Unknown('psql: error: connection to server at "db" (10.0.0.1), port 5432 failed: No route to host'), "connection to server failed: No route to host"),
    (ac.Unknown(STATEMENT_TIMEOUT), "canceling statement due to statement timeout"),
    (ac.Unknown(PERMISSION), "42501: permission denied for table chart_facts"),
    (ValueError("label entry 'a.$.*': wildcard refused\nsecond line"), "label entry 'a.$.*': wildcard refused"),
    (ac.Unknown(""), "Unknown"),
    (ac.Unknown("x" * 500), "x" * ac.UNREAD_REASON_CHARS)])
def test_unread_reason_is_the_first_line_without_host_and_port(exc, want):
    got = ac.unread_reason(exc)
    assert got == want and "127.0.0.1" not in got and "5434" not in got


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
        assert out[c]["v"] == ac.PARTIAL and "the live read did not happen (the owned-table facts could not be read: the column facts read failed)" in out[c]["measured"]


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
