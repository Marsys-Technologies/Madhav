"""test_n178_completion_latest_attempt.py: Build.completion reads the LATEST attempt (SS N-178, 2026-10-07; registry Build.completion revision 6; revision 7 = SS N-305, below).

THE FALSE GREEN ('lit after an errored attempt'): Build.completion compared the build record (`asset_throughput.state` lit / stale, rows_written) with the live count. A record is what an EARLIER completion left behind: an
asset whose latest attempt errored still read PASS because the registry said `lit` and the counts agreed. The measurement now reads the latest STARTED build_run_assets attempt of the asset at the measured scope
and FAILs when it ended `error` / `aborted`, whatever the registry state and row counts say. Measurement side only: no runner change.

Window rule CHOSEN (stated, tested): NO age window. A failed latest attempt stands until a NEWER attempt completes, however old it is and whatever changed in the code since (Build.history's window judges the
current code's attempts; Build.completion asks whether the asset is built NOW). A cascade `blocked_dependency` row (the writer never ran), a skip_no_delta / probe-green / complete latest attempt, no attempt at all and an
all leave today's logic untouched. An UNREAD attempt log (the read failed) is the one exception (revision 7, SS N-305, §N.8): it can never leave a PASS standing: the PASS is cut to PARTIAL naming the unread fact.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_n99_build_completion_integrity as n99  # noqa: E402  (the offline measure() harness)

PASS, FAIL, PARTIAL, NO_DET, NA, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED
CHART = ac.CHART_ID
OTHER = "99999999-0000-0000-0000-000000000000"
AID = "ga_x"
EPOCH0 = 1_790_000_000.0                      # 2026-09-21; the fixtures count days from it


def att(run, state, disp="build", days=0, when=None, started=True):
    """One latest-attempt row as `latest_attempts()` returns it: {run_id, state, disposition, ended_epoch, created_epoch, when, receipt}."""
    e = EPOCH0 + days * 86400
    return dict(run_id=f"{run:08d}-aaaa-bbbb-cccc-dddddddddddd", state=state, disposition=disp, ended_epoch=str(e + 60), created_epoch=e, when=when or f"d{days}", receipt=False)


def log(*attempts, chart=CHART):
    """A fixture attempt LOG reduced the way `latest_attempts()` reduces it: per (asset, chart) the attempt with the greatest (created_epoch, run_id): {asset: {chart: latest}}."""
    best = max(attempts, key=lambda a: (a["created_epoch"], a["run_id"]))
    return {AID: {chart: best}}


REC_OK = dict(v=PASS, measured="rows_written=5 = live=5 (count_sql over the target table; global)")


# ───────────────────────── the pure rule ─────────────────────────

def test_complete_then_error_is_fail_whatever_the_record_and_counts_say():
    got = ac.completion_latest_attempt(REC_OK, log(att(1, "complete", days=0), att(2, "error", days=3))[AID], "global", CHART)
    assert got["v"] == FAIL and "ended error" in got["measured"] and "00000002" in got["measured"] and "N-178" in got["measured"]
    assert "rows_written=5 = live=5" in got["measured"] and "Reading without this rule: PASS" in got["measured"]           # the reading it replaces is carried, not lost
    assert got["latest_attempt"] == dict(checked=True, state="error", disposition="build", run_id=att(2, "error")["run_id"], when="d3", scope="any chart (global build record)", prior_verdict=PASS)


def test_error_then_complete_keeps_todays_verdict_exactly():
    rec = dict(REC_OK)
    got = ac.completion_latest_attempt(rec, log(att(1, "error", days=0), att(2, "complete", days=3))[AID], "global", CHART)
    assert got is rec                                                                                    # not even copied: the very same record


def test_aborted_is_a_fail_too():
    got = ac.completion_latest_attempt(REC_OK, log(att(1, "aborted", disp="", days=1))[AID], "global", CHART)
    assert got["v"] == FAIL and "ended aborted" in got["measured"]


@pytest.mark.parametrize("age_days", [0, 30, 400, 3000])
def test_no_age_window_an_old_failed_latest_attempt_stands_until_a_newer_one_completes(age_days):
    old_error = att(1, "error", days=-age_days, when="2025-01-01")
    got = ac.completion_latest_attempt(REC_OK, log(old_error)[AID], "global", CHART)
    assert got["v"] == FAIL and "2025-01-01" in got["measured"] and "no age window" in got["measured"]       # the date is IN the text; the window is NOT a rule
    newer = ac.completion_latest_attempt(REC_OK, log(old_error, att(2, "complete", days=0))[AID], "global", CHART)
    assert newer["v"] == PASS                                                                            # only a newer completed attempt replaces it


@pytest.mark.parametrize("state,disp", [("complete", "build"), ("complete", "skip_no_delta"), ("complete", ""), ("complete", "probe_green"), ("queued", ""), ("building", "")])
def test_a_latest_attempt_that_is_not_error_or_aborted_leaves_todays_logic(state, disp):
    rec = dict(REC_OK)
    assert ac.completion_latest_attempt(rec, log(att(1, state, disp=disp))[AID], "global", CHART) is rec


def test_a_cascade_blocked_latest_attempt_is_not_the_assets_own_failure():
    rec = dict(REC_OK)
    assert ac.completion_latest_attempt(rec, log(att(1, "error", disp="blocked_dependency"))[AID], "global", CHART) is rec


def test_no_attempt_at_all_leaves_todays_logic():
    rec = dict(REC_OK)
    assert ac.completion_latest_attempt(rec, {}, "global", CHART) is rec                                 # a read that succeeded and found no attempt: nothing to contradict the count


def test_an_unread_attempt_log_never_leaves_a_pass_standing():
    """SS N-305 (§N.8): the PASS claims 'the most recent attempt did not fail'; with the read failed no code path that could read that false has run, so the PASS is cut to PARTIAL, naming the unread fact."""
    got = ac.completion_latest_attempt(dict(REC_OK), None, "global", CHART)
    assert got["v"] == PARTIAL and got is not REC_OK
    assert "could not be read" in got["measured"] and "N-305" in got["measured"]
    assert got["latest_attempt"] == dict(checked=False, unread="the build_run_assets attempt read failed", prior_verdict=PASS)
    assert REC_OK["v"] == PASS                                                                           # pure: the input record is not mutated
    for scope in ("global", f"chart {CHART[:8]}", f"chart {CHART[:8]} (global count_sql; no global build row)"):
        assert ac.completion_latest_attempt(dict(REC_OK), None, scope, CHART)["v"] == PARTIAL, scope


def test_an_unread_attempt_log_leaves_every_non_pass_verdict_alone():
    for rec in (dict(v=FAIL, measured="rows_written=3 != live=5"), dict(v=PARTIAL, measured="integrity check unread"),
                dict(v=NO_DET, measured="NO_DETECTOR"), dict(v=ERRORED, measured="check errored"),
                dict(v=NA, measured="nothing to build", cause="no-writer-no-count-sql")):
        assert ac.completion_latest_attempt(rec, None, "global", CHART) is rec, rec["v"]               # downward-only: nothing is promoted and nothing is rewritten


def test_an_na_stays_na():
    rec = dict(v=NA, measured="no count_sql and nothing to count", cause="no-writer-no-count-sql")
    assert ac.completion_latest_attempt(rec, log(att(1, "error"))[AID], "global", CHART) is rec


@pytest.mark.parametrize("prior", [FAIL, PARTIAL, NO_DET, ERRORED, PASS])
def test_every_other_verdict_becomes_fail_and_names_what_it_replaces(prior):
    rec = dict(v=prior, measured=f"a {prior} reading", produced_set=dict(parts=[]))
    got = ac.completion_latest_attempt(rec, log(att(1, "error"))[AID], "global", CHART)
    assert got["v"] == FAIL and f"Reading without this rule: {prior}: a {prior} reading" in got["measured"] and got["produced_set"] == dict(parts=[])      # other keys survive


def test_scope_a_chart_scoped_record_reads_the_bound_charts_attempt_a_global_one_the_latest_on_any_chart():
    by_chart = {CHART: att(1, "complete", days=0), OTHER: att(2, "error", days=5)}
    scoped = dict(REC_OK)
    assert ac.completion_latest_attempt(scoped, by_chart, f"chart {CHART[:8]}", CHART) is scoped          # the error is on ANOTHER chart: not this chart's build
    assert ac.completion_latest_attempt(scoped, by_chart, f"chart {CHART[:8]} (global count_sql; no global build row)", CHART) is scoped
    got = ac.completion_latest_attempt(scoped, by_chart, "global", CHART)
    assert got["v"] == FAIL and got["latest_attempt"]["scope"] == "any chart (global build record)"       # a global record is written by a run on ANY chart
    only_bound = {CHART: att(1, "error", days=1)}
    assert ac.completion_latest_attempt(scoped, only_bound, f"chart {CHART[:8]}", CHART)["latest_attempt"]["scope"] == f"chart {CHART[:8]}"


def test_the_latest_attempt_is_chosen_by_created_then_run_id_as_latest_attempts_orders_them():
    a, b = att(1, "error", days=2), att(9, "complete", days=2)                                           # the same instant: the greater run_id is the latest
    assert ac.latest_attempt_at_scope(log(a, b)[AID], "global", CHART)[0]["state"] == "complete"
    assert ac.latest_attempt_at_scope({}, "global", CHART)[0] is None and ac.latest_attempt_at_scope({}, f"chart {CHART[:8]}", CHART)[0] is None


def test_latest_attempts_reads_only_started_attempts_latest_per_asset_and_chart(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: (seen.append(sql), [])[1])
    monkeypatch.setattr(ac, "scalar", lambda sql, *a, **k: None)
    ac.latest_attempts(["ga_x"])
    q = seen[0]
    assert "DISTINCT ON (a.asset_id, r.chart_id)" in q and "a.started_at IS NOT NULL" in q and "ORDER BY a.asset_id, r.chart_id, a.started_at DESC, r.created_at DESC, a.run_id DESC" in q


# ───────────────────────── measure(): the same rule on the real path ─────────────────────────

def _measure(monkeypatch, tmp_path, by_chart, rec=None, live=5):
    reg = {AID: n99._reg_row(AID, has_integrity=False)}
    n99._stub_layer(monkeypatch, tmp_path, reg, live=live, rec=rec)
    def latest(ids):
        if by_chart is None:
            raise ac.Unknown("read failed")
        return {AID: by_chart}, None
    monkeypatch.setattr(ac, "latest_attempts", latest)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "format_type(a.atttypid" in sql:
            return [["text"]]
        if "IS NOT NULL" in sql:
            return [["5"]]
        if "EXISTS" in sql:
            return [["f"]]
        return []
    monkeypatch.setattr(ac, "psql", fake_psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: (fake_psql(sql) or [[None]])[0][0])
    return n99._cell(ac.measure("L1"), AID)


def test_measure_lit_after_an_errored_attempt_is_no_longer_green(monkeypatch, tmp_path):
    base = _measure(monkeypatch, tmp_path, {})                                                          # no attempt at all: today's logic
    assert base["v"] == PASS and "rows_written=5 = live=5" in base["measured"]
    got = _measure(monkeypatch, tmp_path, {CHART: att(2, "error", days=3)})
    assert got["v"] == FAIL and "ended error" in got["measured"] and "state='lit'" not in got["measured"] and "rows_written=5 = live=5" in got["measured"]
    assert got["latest_attempt"]["state"] == "error" and got["latest_attempt"]["prior_verdict"] == PASS


def test_measure_error_then_complete_is_todays_verdict_and_an_unread_log_is_never_a_pass(monkeypatch, tmp_path):
    base = _measure(monkeypatch, tmp_path, {})
    assert _measure(monkeypatch, tmp_path, {CHART: att(2, "complete", days=3)}) == base                  # the latest completed: byte for byte today's record
    unread = _measure(monkeypatch, tmp_path, None)                                                       # the attempt read failed (Unknown): SS N-305, §N.8, a PASS cannot rest on an unread fact
    assert base["v"] == PASS and unread["v"] == PARTIAL and unread["latest_attempt"]["checked"] is False
    assert _measure(monkeypatch, tmp_path, {CHART: att(2, "error", disp="blocked_dependency")}) == base


def test_the_registry_text_states_the_rule_the_window_and_the_revision():
    e = ac.CRITERION_REGISTRY["Build.completion"]
    assert e["revision"] == 7 and "N-178" in e["applicability"] and "LATEST started build_run_assets attempt" in e["applicability"] and "NO age window" in e["applicability"]
    assert "the runner is unchanged" in e["applicability"]


# ───────────────────────── review LOW: a TOTAL, deterministic order of attempts ─────────────────────────

def test_the_latest_attempt_is_the_one_that_started_last_then_the_runs_creation_then_run_id():
    """A long-lived run created EARLY whose asset attempt started AFTER a newer run's attempt is the latest (the run's created_at alone would have chosen the newer run's); a tie on both is broken by run_id."""
    long_lived = dict(att(1, "error", days=0), started_epoch=EPOCH0 + 10 * 86400)               # run created day 0, this asset's attempt started day 10
    newer_run = dict(att(2, "complete", days=5), started_epoch=EPOCH0 + 5 * 86400)               # run created day 5, attempt started day 5
    assert ac._attempt_order_key(long_lived) > ac._attempt_order_key(newer_run)
    got = ac.completion_latest_attempt(REC_OK, {CHART: long_lived, OTHER: newer_run}, "global", CHART)
    assert got["v"] == FAIL and got["latest_attempt"]["run_id"] == long_lived["run_id"]
    tie_a, tie_b = dict(att(3, "error"), started_epoch=EPOCH0), dict(att(4, "complete"), started_epoch=EPOCH0)
    assert max([tie_a, tie_b], key=ac._attempt_order_key) is tie_b and max([tie_b, tie_a], key=ac._attempt_order_key) is tie_b      # the greater run_id, whatever the input order
    no_start = att(5, "error", days=2)                                                          # a row without a start epoch (an older fixture) falls back to the run's creation
    assert ac._attempt_order_key(no_start)[0] == no_start["created_epoch"]


def test_latest_attempts_returns_the_started_epoch_and_orders_by_it(monkeypatch):
    row = ["ga_x", CHART, "11111111-aaaa-bbbb-cccc-dddddddddddd", "error", "build", "", "1790000000", "2026-09-21", "f", "1790500000"]
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [row])
    monkeypatch.setattr(ac, "scalar", lambda sql, *a, **k: None)
    got, _era = ac.latest_attempts(["ga_x"])
    assert got["ga_x"][CHART]["started_epoch"] == 1790500000.0 and got["ga_x"][CHART]["created_epoch"] == 1790000000.0
    old_shape = row[:9]                                                                         # a 9-field row (no start): parsed, the start is unknown (-inf), the order falls back to creation
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [old_shape])
    assert ac._attempt_order_key(ac.latest_attempts(["ga_x"])[0]["ga_x"][CHART])[0] == 1790000000.0


# ───────────────────────── revision 7 (SS N-305): the unread-log PARTIAL is classified for what it is ─────────────────────────

def test_the_unread_attempt_partial_is_classified_as_a_transient_read_failure_not_a_stored_aggregate_need():
    import census_postprocess as cp
    got = ac.completion_latest_attempt(dict(REC_OK), None, "global", CHART)
    cls, why = cp.classify_blocker("Build.completion", got["v"], got["measured"])
    assert cls == cp.STRUCTURAL and "could not be read" in why and "stored aggregate" not in why
    # an ordinary Build.completion PARTIAL keeps the generic rule
    assert "stored aggregate" in cp.classify_blocker("Build.completion", "PARTIAL", "integrity check unread")[1]


def test_the_partial_text_does_not_claim_an_integrity_reading_it_may_not_have():
    """Review note 5 (§N.7): a PASS with no declared integrity_check_sql (has_writer=false, a zero-row PASS) has no integrity reading, so the text must not say one 'holds'."""
    got = ac.completion_latest_attempt(dict(REC_OK), None, "global", CHART)
    assert "integrity" not in got["measured"].split("Reading without this rule")[0]
