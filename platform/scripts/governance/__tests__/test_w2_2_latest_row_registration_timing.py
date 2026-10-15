"""test_w2_2_latest_row_registration_timing.py — Nikaṣa wave 2, packet W2-2: latest row, right
registration, attempt-linked timing.

One section per register row (R44, R49, R45, D6 item 2, R43, R46, R50, R51, R53, R54, R232; R233's
tests live beside the C4 tests they flipped, in test_w2_1_earned_verdicts.py). Every test drives the
REAL census code path with only the database answered by a stub — or, in the `live_` tests, by the
real read-only database. No test here greps source text.

The offline measure() harness (`_stub_layer`, `_reg_row`, `_rec`, `_m`, `_open_gap`) is W2-1's,
imported rather than copied.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_w2_2_latest_row_registration_timing.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

CANONICAL = w1.CANONICAL
OTHER = "1c826d5a-0000-4000-8000-000000000000"
LIVE = w1.LIVE
_REAL = dict(w1._REAL)


def _scalar_via(fake):
    return lambda sql: (lambda r: r[0][0] if r and r[0] else None)(fake(sql))


# ─────────────────────────── R44: the latest asset_throughput row per (asset, chart) ───────────────────────────

def _thru_row(aid, chart, rows_written, built_epoch, measured_epoch="", state="lit"):
    """One asset_throughput row as throughput()'s read returns it (8 columns)."""
    return [aid, state, str(rows_written), "", "2026-09-%02d" % 1, chart,
            "" if built_epoch is None else str(built_epoch), str(measured_epoch)]


def _thru_psql(rows):
    def fake(sql, sep="\x1f", timeout=None):
        assert "FROM asset_throughput" in sql, sql[:100]
        return [list(r) for r in rows]
    return fake


@pytest.mark.parametrize("order", ["newest_first", "oldest_first"])
def test_r44_the_latest_row_wins_whatever_the_read_order(monkeypatch, order):
    """Two build rows for the same (asset, chart): the one built later is THE record, whichever order
    the read returns them in. Fails without the fix for `newest_first` (the order the fixed query's
    ORDER BY … DESC produces): the unordered read kept whichever row came LAST — the older one."""
    old = _thru_row("ga_x", CANONICAL, 5, 1_700_000_000)
    new = _thru_row("ga_x", CANONICAL, 9, 1_800_000_000)
    rows = [new, old] if order == "newest_first" else [old, new]
    monkeypatch.setattr(ac, "psql", _thru_psql(rows))
    rec = ac.throughput("ga_", ["ga_x"])["ga_x"][CANONICAL]
    assert rec["rows_written"] == "9", rec
    assert rec["n_rows"] == 2 and rec["ambiguous"] is False


def test_r44_a_null_build_time_never_beats_a_measured_one(monkeypatch):
    """NULLs sort lowest: a row with no last_built_at never displaces one that has it."""
    rows = [_thru_row("ga_x", CANONICAL, 9, 1_800_000_000), _thru_row("ga_x", CANONICAL, 5, None)]
    monkeypatch.setattr(ac, "psql", _thru_psql(rows))
    assert ac.throughput("ga_", ["ga_x"])["ga_x"][CANONICAL]["rows_written"] == "9"


def test_r44_a_tie_is_ambiguous_and_completion_is_errored_closing_nothing(monkeypatch, tmp_path):
    """Two rows tie on (last_built_at, last_measured_at): the latest is undetermined, so
    Build.completion reads ERRORED and an OPEN gap stays OPEN. Fails without the fix: the last row
    read silently became the record and Build.completion PASSed on it (rows_written=4 = live=4)."""
    rows = [_thru_row("ga_x", CANONICAL, 9, 1_800_000_000, 5), _thru_row("ga_x", CANONICAL, 4, 1_800_000_000, 5)]
    reg = {"ga_x": w1._reg_row("ga_x", "ga_t", count_sql="SELECT count(*) FROM ga_t WHERE chart_id = $1")}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"ga_t": (["a"], [])})
    monkeypatch.setattr(ac, "throughput", _REAL["throughput"])
    count = w1._pg_like_psql({"ga_t": 4})

    def fake(sql, sep="\x1f", timeout=None):
        return _thru_psql(rows)(sql) if "FROM asset_throughput" in sql else count(sql)
    monkeypatch.setattr(ac, "psql", fake)
    w1._open_gap(tmp_path, "ga_x", "Build.completion")
    c = ac.measure("L1")
    bc = w1._m(c, "ga_x", "Build.completion")
    assert bc["v"] == ac.ERRORED and "cannot be determined" in bc["measured"], bc
    assert ac.emit_gaps(c)[2] == 0


@LIVE
def test_live_r44_every_record_is_the_distinct_on_latest_row():
    """Live, read-only: for every layer, throughput()'s record per (asset, chart) is the row a
    `DISTINCT ON (asset_id, chart_id) … ORDER BY last_built_at DESC NULLS LAST, last_measured_at DESC
    NULLS LAST` query selects, and no record is ambiguous."""
    for layer, cfg in ac.LAYERS.items():
        reg, _ = ac.registry(layer)
        thru = ac.throughput(cfg["prefix"], sorted(reg))
        ids = ", ".join(f"'{a}'" for a in sorted(reg))
        direct = {(r[0], r[1]): r[2] for r in ac.psql(
            "SELECT DISTINCT ON (asset_id, chart_id) asset_id, coalesce(chart_id::text,''), "
            "coalesce(rows_written::text,'') FROM asset_throughput "
            f"WHERE asset_id IN ({ids}) ORDER BY asset_id, chart_id, last_built_at DESC NULLS LAST, "
            "last_measured_at DESC NULLS LAST")}
        got = {(a, ch): rec["rows_written"] for a, by in thru.items() for ch, rec in by.items()}
        assert got == direct, layer
        assert not any(rec["ambiguous"] for by in thru.values() for rec in by.values()), layer


# ─────────────────────────── R49: the latest build_run_assets error, on a total order ───────────────────────────

_ORDER_COLS = {"a.asset_id": "asset_id", "r.created_at": "created_at", "a.run_id": "run_id"}


def _ordering_history_psql(rows, lit=()):
    """build_history()'s reads, with the attempt read answered in the order its OWN `ORDER BY` names
    (only the keys a PostgreSQL row would carry: asset_id, created_at, run_id). Rows tying on every
    named key keep their insertion order — PostgreSQL's order there is unspecified, so a census that
    orders on a partial key gets an answer that depends on how the rows happen to lie."""
    def fake(sql, sep="\x1f", timeout=None):
        if "FROM build_run_assets a JOIN build_runs r" in sql:
            order = sql.split("ORDER BY", 1)[1]
            keys = [_ORDER_COLS[k.strip()] for k in order.split(",")]
            for k in keys:
                assert k, f"unknown ORDER BY key in {order}"
            out = sorted(rows, key=lambda r: tuple(r[k] for k in keys))
            return [[r["asset_id"], r.get("scope", "layer"), r["state"], r.get("disposition", ""),
                     r["created_at"][:10], r.get("error", ""), "t" if r.get("started", True) else "f"]
                    for r in out]
        if sql.startswith("SELECT count(*)::text FROM build_runs"):
            return [["0"]]
        if "FROM asset_throughput WHERE state='lit'" in sql:
            return [[a] for a in lit]
        raise AssertionError(f"unexpected query: {sql[:100]}")
    return fake


def _real_history(monkeypatch, rows, lit=()):
    fake = _ordering_history_psql(rows, lit)
    monkeypatch.setattr(ac, "psql", fake)
    monkeypatch.setattr(ac, "scalar", _scalar_via(fake))
    return _REAL["build_history"]


def _open_window(monkeypatch, aid, attempts):
    """Build.history is judged inside its window (SS): give `aid` a window that opened before every attempt and the timed attempt log the same
    rows describe, so a test about the TALLY of an executed history keeps testing it."""
    bw = ac._lint_module("build_window")
    monkeypatch.setattr(bw, "compute_window", lambda reader, a, paths: dict(ok=True, epoch=0.0, basis="test window", opens="1970-01-01T00:00:00Z"))
    monkeypatch.setattr(ac._WindowedHistory, "cert_floor", lambda self: (0.0, None))      # N-233 R1: the pass instant (a DB read) is out of these tests' scope; 0.0 = earlier than every test window
    monkeypatch.setattr(bw.WindowReader, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(ac, "_writer_code_paths", lambda a, f, h: ["x"])
    monkeypatch.setattr(ac, "build_attempt_log", lambda prefix, ids=None: {aid: [dict(a, epoch=float(i + 1)) for i, a in enumerate(attempts)]})


def test_r49_the_quoted_error_is_the_latest_not_the_first(monkeypatch, tmp_path):
    """ka_avadhi's shape: an old UndefinedColumn error, then a later integrity failure. Build.history
    FAILs and quotes the LATEST error with its date. Fails without the fix: the census kept the FIRST
    error ever recorded and quoted it under "most recent run error"."""
    rows = [dict(asset_id="ka_x", created_at="2026-07-04T06:55", run_id="r1", state="error",
                 error="UndefinedColumn: column d.dasha_start does not exist"),
            dict(asset_id="ka_x", created_at="2026-08-01T00:00", run_id="r2", state="complete",
                 disposition="build"),
            dict(asset_id="ka_x", created_at="2026-09-10T19:10", run_id="r3", state="error",
                 error="post-write integrity check failed: integrity_check_sql → False")]
    reg = {"ka_x": w1._reg_row("ka_x", None, has_writer=True, asset_kind="service")}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "build_history", _real_history(monkeypatch, rows))
    _open_window(monkeypatch, "ka_x", [dict(scope="layer", state=r["state"], disposition=r.get("disposition", ""), when=r["created_at"][:10],
                                            error=r.get("error", ""), started=True) for r in rows])
    hi = w1._m(ac.measure("L3"), "ka_x", "Build.history")
    assert hi["v"] == ac.FAIL, hi
    assert "latest error (2026-09-10): post-write integrity check failed" in hi["measured"], hi
    assert "UndefinedColumn" not in hi["measured"], hi


@pytest.mark.parametrize("lie", ["as_inserted", "reversed"])
def test_r49_attempts_of_simultaneous_runs_are_read_in_one_deterministic_order(monkeypatch, lie):
    """Two runs created at the same instant (12 such pairs live): the latest-state and quoted error
    must not depend on how the rows happen to lie. Fails without the fix for one of the two lies: the
    old ORDER BY (asset_id, created_at) left the tie to row order."""
    rows = [dict(asset_id="ka_x", created_at="2026-09-10T19:10", run_id="r-a", state="error", error="first"),
            dict(asset_id="ka_x", created_at="2026-09-10T19:10", run_id="r-b", state="complete",
                 disposition="build")]
    if lie == "reversed":
        rows = rows[::-1]
    h = _real_history(monkeypatch, rows)("ka_", ["ka_x"])["per"]["ka_x"]
    assert h["last_state"] == "complete", h
    assert (h["sample_error"], h["sample_error_when"]) == ("first", "2026-09-10"), h


@LIVE
def test_live_r49_every_quoted_error_is_the_latest_by_a_direct_query():
    """Live, read-only, L3: for every asset with a non-cascade error, build_history()'s quoted error is
    the one a direct `DISTINCT ON (asset_id) … ORDER BY created_at DESC, run_id DESC` selects."""
    reg, _ = ac.registry("L3")
    per = ac.build_history("ka_", sorted(reg))["per"]
    ids = ", ".join(f"'{a}'" for a in sorted(reg))
    direct = {r[0]: (r[1], r[2]) for r in ac.psql(
        "SELECT DISTINCT ON (a.asset_id) a.asset_id, r.created_at::date::text, "
        "left(translate(a.error, E'\\n\\r' || chr(31), '   '),200) FROM build_run_assets a "
        f"JOIN build_runs r ON r.id=a.run_id WHERE a.asset_id IN ({ids}) AND a.state='error' "
        "AND coalesce(a.disposition,'') <> 'blocked_dependency' AND coalesce(a.error,'') <> '' "
        "ORDER BY a.asset_id, r.created_at DESC, a.run_id DESC")}
    assert "ka_avadhi" in direct and "ka_kshetra" in direct
    for aid, (when, err) in direct.items():
        assert (per[aid]["sample_error"], per[aid]["sample_error_when"]) == (err, when), aid


# ─────────────────────────── R45: Build.dep_liveness at the census's chart scope ───────────────────────────

class _ThroughputDB:
    """One asset_throughput row set (asset_id, chart_id or '' for global, state, last_built epoch),
    answering EVERY asset_throughput read the census makes by evaluating it against those rows: the
    per-asset build-record read (`asset_id IN (…)`) and the chart-agnostic `state='lit'` read the
    pre-R45 census used. build_history()'s other reads see an empty build_run_assets."""

    def __init__(self, rows):
        self.rows = rows

    def psql(self, sql, sep="\x1f", timeout=None):
        if "FROM asset_throughput WHERE state='lit'" in sql:
            return [[r[0]] for r in self.rows if r[2] == "lit"]
        if "FROM asset_throughput WHERE asset_id IN" in sql:
            ids = {x.strip().strip("'") for x in sql.split("asset_id IN (", 1)[1].split(")", 1)[0].split(",")}
            return [[a, st, "7", "", "2026-09-27", ch, str(ep), ""] for a, ch, st, ep in self.rows if a in ids]
        if "FROM build_run_assets a JOIN build_runs r" in sql:
            return []
        if sql.startswith("SELECT count(*)::text FROM build_runs"):
            return [["0"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")


def _dep_measure(monkeypatch, ctrl, deps, rows, layer="L2"):
    aid = "bo_x"
    r = w1._reg_row(aid, None, has_writer=False, asset_kind="service")
    r["depends_on"] = list(deps)
    w1._stub_layer(monkeypatch, ctrl, {aid: r})
    db = _ThroughputDB(rows)
    monkeypatch.setattr(ac, "psql", db.psql)
    monkeypatch.setattr(ac, "scalar", _scalar_via(db.psql))
    monkeypatch.setattr(ac, "throughput", _REAL["throughput"])
    monkeypatch.setattr(ac, "build_history", _REAL["build_history"])
    return w1._m(ac.measure(layer), aid, "Build.dep_liveness")


@pytest.mark.parametrize("case, rows, verdict", [
    ("lit only on another chart", [("ga_d", OTHER, "lit", 1)], ac.FAIL),
    ("stale here, lit on another chart (the live 10-asset shape)",
     [("ga_d", CANONICAL, "stale", 1), ("ga_d", OTHER, "lit", 2)], ac.PARTIAL),
    ("error here, lit on another chart", [("ga_d", CANONICAL, "error", 1), ("ga_d", OTHER, "lit", 2)], ac.FAIL),
])
def test_r45_a_dependency_not_lit_on_this_chart_never_reads_pass(monkeypatch, tmp_path, case, rows, verdict):
    """Fails without the fix: the census counted a dependency live if it was `lit` on ANY chart, so
    every case here read PASS "all declared dependencies are lit"."""
    v = _dep_measure(monkeypatch, tmp_path, ["ga_d"], rows)
    assert v["v"] == verdict, (case, v)
    assert "482012f1" in v["measured"], v


@pytest.mark.parametrize("rows", [[("ga_d", CANONICAL, "lit", 1), ("ga_d", OTHER, "stale", 2)],
                                  [("bg_d", "", "lit", 1)]])
def test_r45_positive_controls_lit_here_or_lit_globally_pass(monkeypatch, tmp_path, rows):
    """The detector can read true: lit on the canonical chart (whatever other charts say), or lit as a
    global (chart_id NULL) asset."""
    v = _dep_measure(monkeypatch, tmp_path, [rows[0][0]], rows)
    assert v["v"] == ac.PASS, v


def test_r45_an_open_dep_liveness_gap_does_not_close_on_another_charts_lit(monkeypatch, tmp_path):
    """W2-1_REVIEW C2's emit risk: an OPEN Build.dep_liveness row on a ledger copy, the dependency
    stale on the canonical chart and lit on another. Fails without the fix: PASS, and the gap CLOSED."""
    w1._open_gap(tmp_path, "bo_x", "Build.dep_liveness")
    v = _dep_measure(monkeypatch, tmp_path, ["ga_d"], [("ga_d", CANONICAL, "stale", 1), ("ga_d", OTHER, "lit", 2)])
    assert v["v"] not in ac.CLOSABLE
    census = dict(layer="L2", assets=[dict(asset_id="bo_x", measurements={"Build.dep_liveness": v})])
    assert ac.emit_gaps(census)[2] == 0


# The 10 assets W2-1_REVIEW §2.3 / C2 found reading PASS while a dependency was stale on the
# canonical chart and lit only on 1c826d5a.
_C2_ASSETS = ["bo_anveshana", "bo_chart_gestalt", "bo_pramana_mapa", "bo_samvada", "bo_upaya",
              "bo_yantra_mechanism", "ka_avadhi", "ka_kshetra", "ka_sangam", "ka_yojaka"]


@LIVE
def test_live_r45_dep_liveness_matches_a_direct_chart_scoped_query():
    """Live, read-only, L2 + L3: the grade from the census's own dependency read equals one computed
    by a direct SQL query of each dependency's record at the canonical chart (else global), and none
    of the ten C2 assets reads PASS."""
    for layer in ("L2", "L3"):
        reg, _ = ac.registry(layer)
        deps = sorted({d for r in reg.values() for d in r["depends_on"]})
        deprec = ac.throughput("", deps)
        lit = ", ".join(f"'{d}'" for d in deps)
        state = {r[0]: r[1] for r in ac.psql(
            "SELECT DISTINCT ON (asset_id) asset_id, state FROM asset_throughput "
            f"WHERE asset_id IN ({lit}) AND (chart_id = '{CANONICAL}' OR chart_id IS NULL) "
            "ORDER BY asset_id, chart_id NULLS LAST")}
        for aid, r in reg.items():
            if not r["depends_on"]:
                continue
            got = ac._grade_dep_liveness(r["depends_on"], deprec, CANONICAL)["v"]
            st = [state.get(d) for d in r["depends_on"]]
            want = (ac.FAIL if any(s not in ("lit", "stale") for s in st)
                    else ac.PARTIAL if "stale" in st else ac.PASS)
            assert got == want, (aid, got, want, dict(zip(r["depends_on"], st)))
            if aid in _C2_ASSETS:
                assert got != ac.PASS, aid


# ─────────────────────────── D6 item 2: attempt-linked Earn/Cost timing ───────────────────────────

ERA = 1_788_000_000.0          # the first disposition='build' attempt (live: 2026-09-04)


class _EngineDB:
    """asset_throughput + build_run_assets/build_runs + asset_provenance_receipts as the engine at
    8edba0533 writes them, answering the census's three reads by evaluation. `column_1094` simulates
    migration 1094: when False, a query that NAMES duration_seconds fails exactly as PostgreSQL does."""

    def __init__(self, thru, attempts, column_1094=True):
        self.thru, self.attempts, self.col = thru, attempts, column_1094

    def psql(self, sql, sep="\x1f", timeout=None):
        if "FROM asset_throughput WHERE asset_id IN" in sql:
            if "duration_seconds" in sql and not self.col:
                raise ac.Unknown('ERROR:  column "duration_seconds" does not exist')
            ids = {x.strip().strip("'") for x in sql.split("asset_id IN (", 1)[1].split(")", 1)[0].split(",")}
            return [[t["asset"], t["state"], str(t["rw"]), "", "2026-09-27", t["chart"], t["built"], "",
                     (str(t["dur"]) if ("duration_seconds" in sql and t.get("dur") is not None) else "")]
                    for t in self.thru if t["asset"] in ids]
        if sql.startswith("SELECT DISTINCT ON (a.asset_id, r.chart_id)"):
            # Evaluated, not asserted: the started predicate applies only if the census sends it, and
            # DISTINCT ON keeps the first row of the order the census asks for.
            ids = {x.strip().strip("'") for x in sql.split("a.asset_id IN (", 1)[1].split(")", 1)[0].split(",")}
            started_only = "a.started_at IS NOT NULL" in sql
            newest_first = "r.created_at DESC" in sql
            best = {}
            for a in sorted(self.attempts, key=lambda a: (a["created"], a["run"]), reverse=newest_first):
                if a["asset"] in ids and (a.get("started", True) or not started_only):
                    best.setdefault((a["asset"], a["chart"]), a)
            return [[a["asset"], a["chart"], a["run"], a["state"], a.get("disp", ""), a.get("ended", ""),
                     str(a["created"]), "2026-09-20", "t" if a.get("receipt") else "f"] for a in best.values()]
        if "WHERE a.disposition = 'build'" in sql:
            eps = [a["created"] for a in self.attempts if a.get("disp") == "build"]
            return [[str(min(eps))]] if eps else []
        if "FROM build_run_assets a JOIN build_runs r" in sql:
            return []
        if sql.startswith("SELECT count(*)::text FROM build_runs"):
            return [["0"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")


def _timed(monkeypatch, ctrl, thru, attempts, present=True, column_1094=True, has_writer=True, aid="ph_x"):
    reg = {aid: w1._reg_row(aid, None, has_writer=has_writer, asset_kind="service")}
    w1._stub_layer(monkeypatch, ctrl, reg)
    db = _EngineDB(thru, attempts, column_1094)
    monkeypatch.setattr(ac, "psql", db.psql)
    monkeypatch.setattr(ac, "scalar", _scalar_via(db.psql))
    for n in ("throughput", "build_history"):
        monkeypatch.setattr(ac, n, _REAL[n])
    monkeypatch.setattr(ac, "latest_attempts", _REAL_LATEST_ATTEMPTS, raising=False)
    monkeypatch.setattr(ac._lint_module("build_window").WindowReader, "commit_epoch", lambda self, sha: 0)     # these synthetic eras are far before the real engine-deploy floor (DISPOSITION_ERA_COMMIT)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: present)
    c = ac.measure("L4")
    return w1._m(c, aid, "Earn.build_record"), w1._m(c, aid, "Cost.baseline"), c


_REAL_LATEST_ATTEMPTS = getattr(ac, "latest_attempts", None)   # absent before W2-2: the tests then fail, not error
T0 = 1_790_000_000.0


def _rec_row(chart=CANONICAL, built=T0, dur=2.5, rw=10, state="lit", asset="ph_x"):
    return dict(asset=asset, chart=chart, state=state, rw=rw, built=repr(built), dur=dur)


def _att(run, created, state="complete", disp="build", ended=None, chart=CANONICAL, **kw):
    return dict(asset=kw.pop("asset", "ph_x"), chart=chart, run=run, state=state, disp=disp,
                ended=("" if ended is None else repr(ended)), created=created, **kw)


def test_d6_2_a_linked_completion_write_grades_earn_pass_with_its_rate_and_cost_on_that_attempt(monkeypatch, tmp_path):
    """The engine's completion write: disposition='build', ended_at = last_built_at (one transaction's
    NOW()), duration 2.5 s over 10 rows. Earn PASS rate 4.0, Cost PASS naming the attempt. Fails
    without the fix: the call site was unwired and read "NO_DETECTOR — attempt linkage not wired"."""
    earn, cost, _ = _timed(monkeypatch, tmp_path, [_rec_row()], [_att("run-new-1", ERA + 10, ended=T0)])
    assert earn["v"] == ac.PASS and "duration=2.5s, rows_written=10, rate=4.0" in earn["measured"], earn
    assert cost["v"] == ac.PASS and "attempt run-new-" in cost["measured"], cost
    assert "latest attempt at chart 482012f1: run run-new- complete/build" in earn["measured"]


def test_d6_2_a_completion_whose_build_record_was_rewritten_later_is_not_linked(monkeypatch, tmp_path):
    """last_built_at moved after the attempt's completion (a later write): the duration on the row is
    not this attempt's. NO_DETECTOR, never PASS on a duration of unknown provenance."""
    earn, cost, _ = _timed(monkeypatch, tmp_path, [_rec_row(built=T0 + 60)], [_att("r1", ERA + 10, ended=T0)])
    assert earn["v"] == ac.NO_DET and "cannot be attributed" in earn["measured"], earn
    assert cost["v"] == ac.NO_DET


def test_d6_2_a_skip_keeps_earn_na_and_does_not_invent_a_baseline(monkeypatch, tmp_path):
    """skip_no_delta refreshes last_built_at without touching duration: Earn N/A (healthy
    non-execution); the lingering duration has no attributable attempt, so Cost is NO_DETECTOR —
    neither the closable PASS nor a false "none on record"."""
    earn, cost, _ = _timed(monkeypatch, tmp_path, [_rec_row(built=T0 + 90)],
                           [_att("r1", ERA + 10, ended=T0), _att("r2", ERA + 20, disp="skip_no_delta", ended=T0 + 90)])
    assert earn["v"] == ac.NA and "skip_no_delta" in earn["measured"], earn
    assert cost["v"] == ac.NO_DET and "not attributable" in cost["measured"], cost


@pytest.mark.parametrize("created, receipt, verdict", [
    (ERA + 30, True, ac.NA),        # derived probe-green: complete + no disposition + receipt, in the era
    (ERA - 30, True, ac.NO_DET),    # pre-era: a surviving receipt may be a writer build's (2 live)
    (ERA + 30, False, ac.NO_DET),   # no receipt: unclassified (e.g. a watchdog-completed row)
])
def test_d6_2_probe_green_is_derived_never_assumed(monkeypatch, tmp_path, created, receipt, verdict):
    """The engine never writes a `probe_green` disposition (wave-1 F11): it is DERIVED from complete +
    no disposition + a receipt naming the run, inside the disposition era. Anything else with no
    disposition is unclassified NO_DETECTOR — never the closable 'failed before completion' N/A."""
    # ph_x's only attempt is the no-disposition completion; the era is set by ANOTHER asset's first
    # 'build' attempt at ERA (the era is estate-wide, as in production).
    earn, _cost, _ = _timed(monkeypatch, tmp_path, [_rec_row(built=T0 + 5, dur=None)],
                            [_att("r0", ERA, ended=T0 - 1, asset="ph_other"),
                             _att("r2", created, disp="", ended=T0 + 5, receipt=receipt)])
    assert earn["v"] == verdict, earn
    if verdict == ac.NA:
        assert "probe_green" in earn["measured"]


def test_d6_2_failures_route_to_build_history_and_cost_fails_only_when_nothing_was_ever_measured(monkeypatch, tmp_path):
    earn, cost, _ = _timed(monkeypatch, tmp_path, [_rec_row(state="error", dur=None)],
                           [_att("r1", ERA + 10, state="error", disp="", ended=T0)])
    assert earn["v"] == ac.NA and "before completion; see Build.history" in earn["measured"], earn
    assert cost["v"] == ac.FAIL and "no sanctioned baseline" in cost["measured"], cost


def test_d6_2_attempts_only_on_another_chart_are_no_detector_for_this_scope(monkeypatch, tmp_path):
    earn, cost, _ = _timed(monkeypatch, tmp_path, [_rec_row()], [_att("r1", ERA + 10, ended=T0, chart=OTHER)])
    assert earn["v"] == ac.NO_DET and cost["v"] == ac.NO_DET and "elsewhere" in earn["measured"], earn


def test_d6_2_unstarted_rows_are_not_attempts(monkeypatch, tmp_path):
    """A queued leftover newer than the real completion is not the latest attempt (C1)."""
    earn, _cost, _ = _timed(monkeypatch, tmp_path, [_rec_row()],
                            [_att("r1", ERA + 10, ended=T0), _att("r2", ERA + 99, state="queued", disp="", started=False)])
    assert earn["v"] == ac.PASS, earn


def test_d6_2_a_global_build_record_links_the_latest_attempt_on_any_chart(monkeypatch, tmp_path):
    """An L0-style global build record (chart_id NULL) is written by a run on any chart."""
    earn, _cost, _ = _timed(monkeypatch, tmp_path, [_rec_row(chart="")],
                            [_att("r1", ERA + 10, ended=T0 - 50, chart=OTHER), _att("r2", ERA + 20, ended=T0, chart=CANONICAL)])
    assert earn["v"] == ac.PASS and "any chart (global build record)" in earn["measured"], earn


def test_d6_2_with_migration_1094_absent_both_stay_no_detector_and_the_column_is_never_named(monkeypatch, tmp_path):
    """Production today: the instrument is absent. The build-record read must not name the column (the
    simulated database raises if it does), and Earn/Cost read NO_DETECTOR "instrument absent" — now
    naming the attempt they would be linked to."""
    w1._open_gap(tmp_path, "ph_x", "Earn.build_record")
    earn, cost, c = _timed(monkeypatch, tmp_path, [_rec_row()], [_att("r1", ERA + 10, ended=T0)],
                           present=False, column_1094=False)
    for res in (earn, cost):
        assert res["v"] == ac.NO_DET and "instrument absent (migration 1094)" in res["measured"], res
        assert "latest attempt at chart 482012f1: run r1 complete/build" in res["measured"], res
    assert ac.emit_gaps(c)[2] == 0


@LIVE
def test_live_d6_2_every_latest_build_attempt_links_to_its_build_record_on_real_rows():
    """Live, read-only, all six layers: the instrument is absent (every Earn/Cost is NO_DETECTOR); and
    with the column SIMULATED on the real rows (a duration injected into each real build record), every
    asset whose latest attempt at its scope is a 'build' completion links — the ended_at =
    last_built_at key holds on production data — and nothing links that is not a 'build'."""
    assert ac.duration_instrument_present() is False, "migration 1094 is applied — re-grade the proof"
    linked = builds = 0
    for layer, cfg in ac.LAYERS.items():
        reg, _ = ac.registry(layer)
        ids = sorted(reg)
        thru = ac.throughput(cfg["prefix"], ids)
        atts, era = ac.latest_attempts(ids)
        for aid, r in reg.items():
            rec, scope = ac._build_record(thru.get(aid, {}), ac._chart_scoped(r["count_sql"]), ac.CHART_ID)
            if not rec:
                continue
            absent = ac._attempt_timing(atts.get(aid, {}), rec, scope, ac.CHART_ID, False, r["has_writer"], era)
            assert all(x["v"] == ac.NO_DET and "instrument absent" in x["measured"] for x in absent), (aid, absent)
            earn, _ = ac._attempt_timing(atts.get(aid, {}), dict(rec, duration=1.0), scope, ac.CHART_ID, True,
                                         r["has_writer"], era)
            is_build = "complete/build" in earn["measured"]
            builds += is_build
            linked += earn["v"] == ac.PASS
            assert (earn["v"] == ac.PASS) == (is_build and r["has_writer"]), (aid, earn)
    assert builds > 0 and linked == builds, (linked, builds)


# ─────────────────────────── R43: constant-indirection, package and shim-imported writers ───────────────────────────

_WRITER_BODY = '''
class {cls}(WriterBase):
    def run(self, ctx):
        ctx.db_conn.cursor().execute("DELETE FROM t_x WHERE chart_id = %s", (1,))
        return None
'''


def _writer_tree(tmp_path):
    side = tmp_path / "python-sidecar"
    w = side / "pipeline" / "orchestrator" / "writers"
    (w / "ph_pkg").mkdir(parents=True)
    (side / "services" / "ka_svc").mkdir(parents=True)
    (w / "__init__.py").write_text('"""framework: @register(\'mi_fake\') is only documented here"""\n')
    (w / "mi_const.py").write_text('from pipeline.orchestrator.writers import WriterBase, register\n'
                                   'ASSET_ID = "mi_const"\n@register(ASSET_ID)'
                                   + _WRITER_BODY.format(cls="MiConst"))
    (w / "mi_twice.py").write_text('from pipeline.orchestrator.writers import WriterBase, register\n'
                                   'ASSET_ID = "mi_twice"\nASSET_ID = "mi_other"\n@register(ASSET_ID)'
                                   + _WRITER_BODY.format(cls="MiTwice"))
    (w / "ph_pkg" / "__init__.py").write_text('from pipeline.orchestrator.writers import WriterBase, register\n'
                                              '@register("ph_pkg")' + _WRITER_BODY.format(cls="PhPkg"))
    (w / "ka_shim.py").write_text('"""@register(\'ka_svc\') fires in the service."""\n'
                                  'from services.ka_svc.writer import KaSvcWriter  # noqa: F401\n')
    (side / "services" / "ka_svc" / "__init__.py").write_text("")
    (side / "services" / "ka_svc" / "writer.py").write_text(
        'def _build():\n    from pipeline.orchestrator.writers import WriterBase, register\n\n'
        '    @register("ka_svc")\n    class KaSvcWriter(WriterBase):\n        def run(self, ctx):\n'
        '            ctx.db_conn.cursor().execute("DELETE FROM t_x WHERE chart_id = %s", (1,))\n'
        '    return KaSvcWriter\nKaSvcWriter = _build()\n')
    return side, w


def _use_tree(monkeypatch, tmp_path):
    side, w = _writer_tree(tmp_path)
    monkeypatch.setattr(ac, "WRITERS", w)
    monkeypatch.setattr(ac, "SIDECAR", side, raising=False)


def test_r43_a_module_constant_register_is_recognised_and_a_twice_assigned_name_is_not_guessed(monkeypatch, tmp_path):
    """`@register(ASSET_ID)` with `ASSET_ID = "mi_const"` registers mi_const. A name assigned twice is
    ambiguous and is NOT resolved. Fails without the fix: mi_const was not recognised at all."""
    _use_tree(monkeypatch, tmp_path)
    regd = ac.registered_ids("mi_")
    assert regd.get("mi_const") == ["mi_const.py"], regd
    assert "mi_twice" not in regd and "mi_other" not in regd and "mi_fake" not in regd, regd


def test_r43_package_and_shim_imported_writers_are_recognised(monkeypatch, tmp_path):
    """writers/ph_pkg/__init__.py registers ph_pkg; writers/ka_shim.py imports the service module whose
    factory registers ka_svc. Fails without the fix: neither was scanned."""
    _use_tree(monkeypatch, tmp_path)
    assert ac.registered_ids("ph_") == {"ph_pkg": ["ph_pkg/__init__.py"]}
    assert ac.registered_ids("ka_") == {"ka_svc": ["services/ka_svc/writer.py"]}


@pytest.mark.parametrize("aid, layer", [("mi_const", "L5"), ("ph_pkg", "L4"), ("ka_svc", "L3")])
def test_r43_the_resolved_writer_is_measured_not_no_detector(monkeypatch, tmp_path, aid, layer):
    """End to end through the REAL registered_ids()/contract_scan()/idem_scan(): the writer is
    registered, its contract is scanned (PASS: WriterBase, run(), no commit) and its idempotency
    pattern is read (PASS: DELETE FROM its own table t_x — since C-KSHETRA a counted DELETE must name the
    asset's table, so the fixture declares it). Fails without the fix: Build.registered FAIL "no
    @register found" and both scans NO_DETECTOR "never scanned"."""
    _use_tree(monkeypatch, tmp_path)
    reg = {aid: w1._reg_row(aid, "t_x", has_writer=True, asset_kind="service")}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "registered_ids", _REAL_REGISTERED_IDS)
    c = ac.measure(layer)
    assert w1._m(c, aid, "Build.registered")["v"] == ac.PASS, w1._m(c, aid, "Build.registered")
    assert w1._m(c, aid, "Build.contract")["v"] == ac.PASS, w1._m(c, aid, "Build.contract")
    assert w1._m(c, aid, "Idem.pattern")["v"] == ac.PASS, w1._m(c, aid, "Idem.pattern")


_REAL_REGISTERED_IDS = ac.registered_ids


@LIVE
def test_live_r43_every_writer_backed_active_asset_is_recognised():
    """Live, read-only: L4 registers 9 ids (ph_rectification, a package), L5 14 (mi_bhara, mi_sankalpa
    via ASSET_ID), and every active has_writer=true asset in all six layers is recognised."""
    counts = {}
    for layer, cfg in ac.LAYERS.items():
        reg, _ = ac.registry(layer)
        regd = ac.registered_ids(cfg["prefix"])
        counts[layer] = len(set(regd) & set(reg))
        missing = sorted(a for a, r in reg.items() if r["has_writer"] and a not in regd)
        assert not missing, (layer, missing)
    assert counts["L4"] == 9 and counts["L5"] == 14, counts


# ─────────────────────────── R46: a view asset is counted by the view ───────────────────────────

def _view_measure(monkeypatch, ctrl, view_rows, floor=None, relkind_view=True, cols=("chart_id", "n")):
    reg = {"bo_v": w1._reg_row("bo_v", "vw_x", count_sql="SELECT 0 AS count", target_floor=floor)}
    w1._stub_layer(monkeypatch, ctrl, reg, thru={"bo_v": {CANONICAL: w1._rec(1, state="stale")}})
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"vw_x"}, cols={"vw_x": list(cols)}, keys={},
                                                       views=({"vw_x"} if relkind_view else set())))
    seen = []
    fake = w1._pg_like_psql({"vw_x": lambda part: (seen.append(part), view_rows)[1]})
    monkeypatch.setattr(ac, "psql", fake)
    c = ac.measure("L2")
    return next(a for a in c["assets"] if a["asset_id"] == "bo_v"), seen


def test_r46_a_view_is_counted_by_the_view_chart_scoped(monkeypatch, tmp_path):
    """bo_samvada's shape: count_sql `SELECT 0 AS count` over a view that returns rows. live_rows is
    the view's count for the bound chart (5), not the constant 0; Build.completion says why the
    comparison cannot be made (NO_DETECTOR). Fails without the fix: live_rows read 0 (the constant)."""
    a, seen = _view_measure(monkeypatch, tmp_path, 5)
    assert a["live_rows"] == 5, a["live_rows"]
    assert any("FROM vw_x WHERE chart_id = '482012f1" in s for s in seen), seen
    bc = a["measurements"]["Build.completion"]
    assert bc["v"] == ac.NO_DET and "view: live=5" in bc["measured"], bc


@pytest.mark.parametrize("floor, verdict", [("3", ac.PASS), ("10", ac.FAIL)])
def test_r46_a_declared_floor_is_graded_against_the_view_count(monkeypatch, tmp_path, floor, verdict):
    """With the view counted, a declared floor is measured against it (it read NO_DETECTOR against
    the constant). Fails without the fix for both: Count.floor was NO_DETECTOR."""
    a, _ = _view_measure(monkeypatch, tmp_path, 5, floor=floor)
    assert a["measurements"]["Count.floor"]["v"] == verdict, a["measurements"]["Count.floor"]


def test_r46_an_empty_view_fails_emptiness(monkeypatch, tmp_path):
    """A view serving no rows for this chart FAILs (no floor=0 declaration). Fails without the fix:
    NO_DETECTOR (the constant could not be measured)."""
    a, _ = _view_measure(monkeypatch, tmp_path, 0)
    assert a["measurements"]["Build.completion"]["v"] == ac.FAIL, a["measurements"]["Build.completion"]


def test_r46_only_a_view_is_substituted_a_table_with_a_constant_stays_no_detector(monkeypatch, tmp_path):
    """Positive control on scope: a TABLE target with a constant count_sql is not re-counted."""
    a, seen = _view_measure(monkeypatch, tmp_path, 5, relkind_view=False)
    assert a["live_rows"] == 0 and not seen, (a["live_rows"], seen)
    assert a["measurements"]["Build.completion"]["v"] == ac.NO_DET


@LIVE
def test_live_r46_bo_samvada_is_counted_by_its_view():
    reg, _ = ac.registry("L2")
    cat = ac.catalog([reg["bo_samvada"]["target_table"]])
    assert "vw_chart_digest" in cat["views"]
    vc = {"bo_samvada": ac._view_count_sql("vw_chart_digest", cat["cols"]["vw_chart_digest"])}
    counts, errs = ac.live_counts({"bo_samvada": reg["bo_samvada"]}, CANONICAL, vc)
    direct = int(ac.scalar(f"SELECT count(*)::text FROM vw_chart_digest WHERE chart_id = '{CANONICAL}'"))
    assert not errs and counts["bo_samvada"] == direct > 0, (counts, errs, direct)


# ─────────────────────────── R50: attempt tallies reconcile with a direct count ───────────────────────────

def test_r50_a_line_that_is_not_one_whole_attempt_fails_the_read_instead_of_adding_a_run(monkeypatch):
    """One real attempt for ga_x, plus the tail of a split error whose last line is `ga_x` followed by
    the started flag — the shape that adds a phantom run to a REAL asset. Fails without the fix: the
    padded fragment was counted, ga_x read 2 runs for 1 row (the handverify's 108 against 107)."""
    rows = [["ga_x", "layer", "error", "", "2026-09-20", "Traceback (most recent call last):", "t"],
            ["ga_x", "t"]]

    def fake(sql, sep="\x1f", timeout=None):
        if "FROM build_run_assets a JOIN build_runs r" in sql:
            return [list(r) for r in rows]
        return [["0"]]
    monkeypatch.setattr(ac, "psql", fake)
    monkeypatch.setattr(ac, "scalar", _scalar_via(fake))
    with pytest.raises(ac.Unknown, match="did not parse into the 7 selected fields"):
        ac.build_history("ga_", ["ga_x"])


@LIVE
def test_live_r50_runs_and_executed_equal_direct_counts_on_every_layer():
    """Live, read-only, all six layers: build_history()'s `runs` and `executed` equal a direct
    count(*) / count(started_at) over build_run_assets ⋈ build_runs for every asset with rows."""
    for layer, cfg in ac.LAYERS.items():
        reg, _ = ac.registry(layer)
        per = ac.build_history(cfg["prefix"], sorted(reg))["per"]
        ids = ", ".join(f"'{a}'" for a in sorted(reg))
        direct = {r[0]: (int(r[1]), int(r[2])) for r in ac.psql(
            "SELECT a.asset_id, count(*)::text, count(a.started_at)::text FROM build_run_assets a "
            f"JOIN build_runs r ON r.id = a.run_id WHERE a.asset_id IN ({ids}) GROUP BY 1")}
        assert set(per) == set(direct), (layer, set(per) ^ set(direct))
        for aid, (runs, started) in direct.items():
            assert (per[aid]["runs"], per[aid]["executed"]) == (runs, started), (layer, aid)


# ─────────────────────────── R51: a serving module is one whose CODE references the table ───────────────────────────

def _caps_dir(tmp_path, files):
    d = tmp_path / "caps"
    d.mkdir()
    for name, body in files.items():
        (d / name).write_text(body, encoding="utf-8")
    return str(d)


_R51_FILES = {
    "index.ts": "/**\n *   query_x — ph_x (t_x, 150 rows)\n */\nexport * from './query_real'\n",
    "query_comment.ts": "// calibration is L5's job, and ph_x's leakage is t_x's\nexport const y = 1\n",
    "salience.ts": "/** `t_x.severity` — CHECK: critical | minor */\nexport const ORDER = ['critical']\n",
    # A `//` and a `/*` inside string literals must not be read as comments: the table reference that
    # follows them on the same line is code.
    "query_real.ts": ("const glob = '/api/*'\nexport const cap = {\n  run: () => query('https://host', "
                      "`SELECT * FROM t_x WHERE chart_id = $1`),\n}\nconst end = '*/'\n"),
}


def test_r51_a_module_that_only_mentions_the_table_in_a_comment_does_not_serve_it(tmp_path):
    """L4's three misattributions, reproduced: a catalogue header comment (index.ts), a `//` aside
    (query_predictive_anchors.ts), a JSDoc on a CHECK list (salience_order.ts). Only the module whose
    code queries the table serves it. Fails without the fix: all four were listed."""
    cap = ac.capability_scan(_caps_dir(tmp_path, _R51_FILES), ["t_x", "ph_x"])
    assert cap["modules"] == ["query_real.ts"], cap["modules"]


@LIVE
def test_live_r51_l4_modules_are_attributed_by_code():
    """Live source, L4: query_predictive_anchors.ts no longer serves ph_pramana / ph_sodhana, and
    index.ts no longer serves ph_rectification / ph_suddha_sodhana; the module that queries each
    table still does."""
    reg, _ = ac.registry("L4")
    caps = ac.LAYERS["L4"]["caps"]
    for aid, stray in (("ph_pramana", "query_predictive_anchors.ts"), ("ph_sodhana", "query_predictive_anchors.ts"),
                       ("ph_rectification", "index.ts"), ("ph_suddha_sodhana", "index.ts")):
        mods = ac.capability_scan(caps, [reg[aid]["target_table"], aid])["modules"]
        assert stray not in mods and "query_phala_calibration.ts" in mods, (aid, mods)


@pytest.mark.parametrize("files, verdict", [
    ({"index.ts": "// already-served-elsewhere t_x\nexport {}\n"}, ac.NO_DET),   # named, never attributed
    ({"index.ts": "export {}\n"}, ac.NA),                                        # genuinely unreferenced
])
def test_r51_stripping_comments_never_turns_a_named_asset_into_a_closable_na(monkeypatch, tmp_path, files, verdict):
    """§N.8 guard on R51: when comments name the table but no module's code references it, "not served"
    was never established — NO_DETECTOR, and an OPEN Dens.served gap stays OPEN (bg_dignity_reference,
    served by the generic MCP DB route; ga_strength, served through chart_facts). Only a directory that
    never names it reads N/A. Fails if the comment-only case falls through to the closable N/A."""
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    caps = _caps_dir(tmp_path, files)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: _REAL["capability_scan"](caps, t))
    w1._open_gap(tmp_path, "bg_x", "Dens.served")
    c = ac.measure("L0")
    ds = w1._m(c, "bg_x", "Dens.served")
    assert ds["v"] == verdict, ds
    # E6 fix 1: with no rule declared an N/A is not released: it closes nothing (REGISTRY_REVISION 9 declares the Dens rule in
    # production, so this undeclared path is forced here)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
    assert ac.emit_gaps(c)[2] == 0
    if verdict == ac.NA:
        # ... and it closes only under a declared, caused rule (the only way an N/A ever closes an OPEN gap)
        assert ds["cause"] == "no-served-surface", ds
        monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Dens.served#measured:no-served-surface": "N-22/test"})
        assert ac.emit_gaps(c)[2] == 1


# ─────────────────────────── R53: Build.target's FAIL is reachable ───────────────────────────

def _target(monkeypatch, ctrl, count_sql, kind="data", writer=True, owners=None):
    reg = {"bg_x": w1._reg_row("bg_x", None, has_writer=writer, count_sql=count_sql, asset_kind=kind)}
    w1._stub_layer(monkeypatch, ctrl, reg)
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_main": 7, "t_a": 1, "chart_facts": 3}))
    if isinstance(owners, Exception):
        def boom():
            raise owners
        monkeypatch.setattr(ac, "target_owners", boom, raising=False)
    else:
        monkeypatch.setattr(ac, "target_owners", lambda: dict(owners or {}), raising=False)
    return w1._m(ac.measure("L0"), "bg_x", "Build.target")


@pytest.mark.parametrize("count_sql, owners, verdict, text", [
    ("", {}, ac.FAIL, "nothing to aim at"),                                       # no table at all
    ("SELECT count(*) FROM t_main", {}, ac.FAIL, "declaration is missing"),        # T1 build_target_null
    ("SELECT (SELECT count(*) FROM t_main) + (SELECT count(*) FROM t_a) AS count", {}, ac.PASS, "multi-table"),
    ("SELECT count(*) FROM chart_facts WHERE chart_id = $1", {"chart_facts": ["ga_positions"]}, ac.PASS,
     "partition of chart_facts, the declared target of ga_positions"),
])
def test_r53_a_writer_backed_data_asset_without_a_target_is_graded_not_waved_through(
        monkeypatch, tmp_path, count_sql, owners, verdict, text):
    """Fails without the fix for every case: asset_kind is never empty (NOT NULL CHECK), so the old
    branch read the closable N/A "no target_table" for all of them and its FAIL was dead code."""
    bt = _target(monkeypatch, tmp_path, count_sql, owners=owners)
    assert bt["v"] == verdict and text in bt["measured"], bt


def test_r53_a_declared_service_and_a_writerless_asset_stay_na(monkeypatch, tmp_path):
    assert _target(monkeypatch, tmp_path, "", kind="service")["v"] == ac.NA
    assert _target(monkeypatch, tmp_path, "", writer=False)["v"] == ac.NA


def test_r53_an_unreadable_ownership_map_is_errored(monkeypatch, tmp_path):
    bt = _target(monkeypatch, tmp_path, "SELECT count(*) FROM t_main", owners=ac.Unknown("relation gone"))
    assert bt["v"] == ac.ERRORED, bt


@LIVE
def test_live_r53_no_writer_backed_data_asset_reads_the_closable_na():
    """Live, read-only: bg_prashna_rules (5-table count) and ga_strength / ga_structural (chart_facts
    partitions) read PASS by what their count_sql declares; no writer-backed data/artifact asset reads
    Build.target N/A anywhere."""
    owners = ac.target_owners()
    seen = {}
    for layer in ac.LAYERS:
        reg, _ = ac.registry(layer)
        for aid, r in reg.items():
            if r["target_table"] or r["asset_kind"] == "service" or not r["has_writer"]:
                continue
            seen[aid] = ac._grade_target_less(r, lambda: owners)["v"]
    assert seen == {"bg_prashna_rules": ac.PASS, "ga_strength": ac.PASS, "ga_structural": ac.PASS}, seen


# ─────────────────────────── R54: Vocab.alias severity below the verdict ───────────────────────────

def _alias(monkeypatch, ctrl, classes):
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    w1._stub_layer(monkeypatch, ctrl, reg, tables={"t_x": (["entity_class", "synonyms"], [])})
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_x": 741}))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: {k: dict(rows=r, no_alias=e) for k, (r, e) in classes.items()})
    return w1._m(ac.measure("L0"), "bg_x", "Vocab.alias")


def test_r54_the_plants_worsening_is_visible_below_the_verdict(monkeypatch, tmp_path):
    """T1 vocab_alias: 79/741 rows without an alias set, then all 741 emptied. Both FAIL; the measured
    fraction and `severity` show the worsening. Fails without the fix: no severity field, and the
    evidence carried no overall fraction (only per-class counts)."""
    before = _alias(monkeypatch, tmp_path, {"graha": (400, 40), "rasi": (341, 39)})
    after = _alias(monkeypatch, tmp_path, {"graha": (400, 400), "rasi": (341, 341)})
    assert before["v"] == after["v"] == ac.FAIL
    assert before["severity"] == round(79 / 741, 4) and after["severity"] == 1.0, (before, after)
    assert "79/741 row(s) lack an alias set (10.7%)" in before["measured"], before
    assert "741/741 row(s) lack an alias set (100.0%)" in after["measured"], after


def test_r54_a_clean_alias_census_passes_with_severity_zero(monkeypatch, tmp_path):
    v = _alias(monkeypatch, tmp_path, {"graha": (9, 0)})
    assert v["v"] == ac.PASS and v["severity"] == 0.0, v


# ─────────────────────────── R232: Dens.served reads a declared field, never a comment ───────────────────────────

# E6.1 (d): the served select carries a tier column, so a REAL declaration can reach PASS (contract AND tier column)
_SERVES = "export const cap = {\n  run: () => query(`SELECT id, tier FROM t_x`),\n"


@pytest.mark.parametrize("extra, declares", [
    ("  // TODO: no density_contract yet\n}\n", 0),                                   # review attack A4
    ("  /** density_contract: to be added (F-S1) */\n}\n", 0),                        # a JSDoc that looks declared
    ("  description: 'see the density_contract: docs',\n}\n", 0),                      # a string mention
    ("  note: `density_contract: pending`,\n}\n", 0),                                 # a template-literal mention
    ("  density_contract: { paginated: true, empty_reason: true },\n}\n", 1),         # the declared field
    ("  density_contract?: { paginated: false },\n}\n", 1),                          # an optional-property declaration
    ("  // density_contract is below\n  density_contract: { paginated: false },\n}\n", 1),  # mention AND declaration
])
def test_r232_only_a_declared_density_contract_counts(tmp_path, extra, declares):
    """Fails without the fix for the four mention cases: a substring match counted a comment or a
    string as a declaration (review A4: `// TODO: … no density_contract yet` read declaring 1). The
    three declaring cases are the positive control: a real property still counts."""
    cap = ac.capability_scan(_caps_dir(tmp_path, {"query_x.ts": _SERVES + extra}), ["t_x"])
    # E6.1 (d): `density` now counts capabilities that declare AND carry a tier column; this select carries one, so
    # a real declaration is dense and a mention is not — `declares` is unchanged, and reads the same.
    assert cap["modules"] == ["query_x.ts"] and cap["density"] == declares, cap


@pytest.mark.parametrize("extra, verdict, closed", [
    ("  // TODO: no density_contract yet\n}\n", ac.FAIL, 0),                         # F-S1 / A4: stays OPEN
    ("  density_contract: { paginated: true },\n}\n", ac.PASS, 1),                    # control: a real declaration closes
])
def test_r232_an_open_dens_served_gap_does_not_close_on_a_comment(monkeypatch, tmp_path, extra, verdict, closed):
    """W2-1_C1_REVIEW F-S1: after the first emit 59 Dens.served rows are open; a later emit must not
    close one because a comment mentions density_contract. Fails without the fix: the comment case read
    PASS and the OPEN gap CLOSED. The declared case is the control — the verdict can still read PASS."""
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    caps = _caps_dir(tmp_path, {"query_x.ts": _SERVES + extra})
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: _REAL["capability_scan"](caps, t))
    w1._open_gap(tmp_path, "bg_x", "Dens.served")
    c = ac.measure("L0")
    assert w1._m(c, "bg_x", "Dens.served")["v"] == verdict
    assert ac.emit_gaps(c)[2] == closed



# ─────────── C-KSHETRA (W2-2 gate review §4.1): Idem.pattern — a counted DELETE names the asset's own
# table and is reachable on a POPULATED rebuild; a refused rebuild never PASSes ───────────

_KSH_GUARD = '''
    def _prepare(self, conn, chart_id):
        populated = self._populated(conn, chart_id)
        if populated is not None:
            raise ReplacementHeld(f"held: output exists in {populated}")
        self._delete_prior(conn, chart_id)
'''
_KSH_NO_GUARD = '''
    def _prepare(self, conn, chart_id):
        self._delete_prior(conn, chart_id)
'''
_KSH_EMPTY_POLARITY = '''
    def _prepare(self, conn, chart_id):
        upstream = self._populated(conn, chart_id)
        if upstream is None:
            raise RuntimeError("upstream missing")
        self._delete_prior(conn, chart_id)
'''


def _ksh_writer(tmp_path, prepare, delete_sql='f"DELETE FROM {table} WHERE chart_id = %s"'):
    """A ka_kshetra-shaped writer: `_OWNED_TABLES` module sequence, an output-existence probe, a prepare
    step (the variant under test) and a per-table delete loop over `_OWNED_TABLES`."""
    w = tmp_path / "writers"
    w.mkdir(exist_ok=True)
    (w / "ka_x.py").write_text(
        "from pipeline.orchestrator.writers import WriterBase, register\n"
        "class ReplacementHeld(RuntimeError):\n    pass\n"
        "_OWNED_TABLES = (('t_owned_a', None), ('t_x', 'lel_derived = FALSE'))\n"
        '@register("ka_x")\nclass KaX(WriterBase):\n'
        "    def run(self, ctx):\n        self._prepare(ctx.db_conn, 1)\n"
        + prepare +
        "    @staticmethod\n    def _populated(conn, chart_id):\n"
        "        for table, predicate in _OWNED_TABLES:\n"
        "            conn.execute(f'SELECT EXISTS (SELECT 1 FROM {table} WHERE chart_id = %s LIMIT 1)', (chart_id,))\n"
        "        return None\n"
        "    @staticmethod\n    def _delete_prior(conn, chart_id):\n"
        "        for table, predicate in _OWNED_TABLES:\n"
        f"            conn.execute({delete_sql}, (chart_id,))\n"
        "        conn.execute('DELETE FROM build_substep_progress WHERE chart_id = %s', (chart_id,))\n",
        encoding="utf-8")
    return w


@pytest.mark.parametrize("prepare, verdict, text", [
    (_KSH_GUARD, ac.FAIL, "rebuild refused when target is populated: ka_x.py:"),       # the ka_kshetra shape
    (_KSH_NO_GUARD, ac.PASS, "t_x (ka_x.py:"),                                         # control: replaces on a populated chart
    (_KSH_EMPTY_POLARITY, ac.PASS, "t_x (ka_x.py:"),                                   # a raise on EMPTY upstream is no refusal
])
def test_ckshetra_a_rebuild_refused_on_a_populated_chart_never_passes(monkeypatch, tmp_path, prepare, verdict, text):
    """Through the REAL idem_scan(): the guarded writer reads FAIL naming the raise; without the guard the
    same loop-resolved delete-then-insert on its own table t_x PASSes. Fails without the fix: the guarded
    writer PASSed on 'DELETE FROM present' (build_substep_progress + the bare f-string fragment)."""
    monkeypatch.setattr(ac, "WRITERS", _ksh_writer(tmp_path, prepare))
    v, notes = ac.idem_scan("ka_x", ["ka_x.py"], "delete_then_insert", ["t_x"])
    assert v == verdict and text in notes[0], (v, notes)


@pytest.mark.parametrize("delete_sql, targets, verdict", [
    ("'DELETE FROM build_substep_progress WHERE chart_id = %s'", ["t_x"], ac.PARTIAL),  # sibling table only
    ('f"DELETE FROM {unresolved} WHERE chart_id = %s"', ["t_x"], ac.PARTIAL),            # a bare fragment names nothing
    ("'DELETE FROM public.t_x WHERE chart_id = %s'", ["t_x"], ac.PASS),                 # literal, schema-qualified, own table
    ('f"DELETE FROM {table} WHERE chart_id = %s"', [], ac.PARTIAL),                      # no declared table to check against
])
def test_ckshetra_a_counted_delete_must_name_the_assets_own_table(monkeypatch, tmp_path, delete_sql, targets, verdict):
    """(a): a DELETE counts only when it NAMES one of the asset's own tables (target_table ∪ count_sql
    tables) — literally or through a resolved constant / loop sequence. Fails without the fix: the
    sibling-only and fragment-only writers PASSed."""
    monkeypatch.setattr(ac, "WRITERS", _ksh_writer(tmp_path, _KSH_NO_GUARD, delete_sql))
    v, notes = ac.idem_scan("ka_x", ["ka_x.py"], "delete_then_insert", targets)
    assert v == verdict, (v, notes)


def test_ckshetra_an_open_idem_gap_does_not_close_on_a_refused_rebuild(monkeypatch, tmp_path):
    """measure() + emit_gaps() on a ledger copy: the guarded writer's OPEN Idem.pattern gap stays OPEN."""
    _use_tree(monkeypatch, tmp_path)
    monkeypatch.setattr(ac, "WRITERS", _ksh_writer(tmp_path, _KSH_GUARD))
    reg = {"ka_x": w1._reg_row("ka_x", "t_x", has_writer=True)}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {"ka_x": ["ka_x.py"]} if prefix == "ka_" else {})
    w1._open_gap(tmp_path, "ka_x", "Idem.pattern")
    c = ac.measure("L3")
    assert w1._m(c, "ka_x", "Idem.pattern")["v"] == ac.FAIL
    assert ac.emit_gaps(c)[2] == 0


def test_ckshetra_the_real_ka_kshetra_does_not_pass_and_a_real_replacing_writer_does():
    """Real source (no database; targets are the registry's, verified live 2026-09-27): ka_kshetra's
    writer raises KshetraReplacementHeld on any populated chart (services/ka_kshetra/writer.py
    _run_prepare_replace) — FAIL naming that file; ka_kota_chakra deletes kala_kota_chakra per chart
    before insert — PASS. Fails without the fix: ka_kshetra read PASS."""
    ks = ac.registered_ids("ka_")
    v, notes = ac.idem_scan("ka_kshetra", ks["ka_kshetra"], "delete_then_insert", ["kala_field"])
    assert v == ac.FAIL and "rebuild refused when target is populated: services/ka_kshetra/writer.py:" in notes[0], notes
    v2, notes2 = ac.idem_scan("ka_kota_chakra", ks["ka_kota_chakra"], "delete_then_insert", ["kala_kota_chakra"])
    assert v2 == ac.PASS and "kala_kota_chakra" in notes2[0], notes2
