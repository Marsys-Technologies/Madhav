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
