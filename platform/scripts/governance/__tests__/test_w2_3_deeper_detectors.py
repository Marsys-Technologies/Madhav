"""test_w2_3_deeper_detectors.py — Nikaṣa wave 2, packet W2-3: deeper detectors.

One section per register row (R242, R20 with R240, R241, R21, R23). Every test drives the REAL census
code path — a writer tree on disk read by the real `idem_scan`, the real `measure()` with only the
database answered by a stub (W2-1's `_stub_layer` harness, imported), the real `emit_gaps` on a ledger
copy — or, in the `live_` tests, the real read-only database and the real writer sources. No test here
greps source text.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_w2_3_deeper_detectors.py -v
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

LIVE = w1.LIVE


# ─────────────────────────── R242: target_owners() read once per measure() ───────────────────────────

def _target_less_layer(monkeypatch, ctrl, owners_map):
    """Three writer-backed data assets with no target_table, each reaching Build.target's ownership
    branch (one table in its count_sql). Returns the census and the number of target_owners() reads."""
    reg = {"bg_a": w1._reg_row("bg_a", None, count_sql="SELECT count(*) FROM t_main"),
           "bg_b": w1._reg_row("bg_b", None, count_sql="SELECT count(*) FROM chart_facts"),
           "bg_c": w1._reg_row("bg_c", None, count_sql="SELECT count(*) FROM chart_facts")}
    w1._stub_layer(monkeypatch, ctrl, reg)
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_main": 7, "chart_facts": 3}))
    calls = []

    def owners():
        calls.append(1)
        return dict(owners_map)
    monkeypatch.setattr(ac, "target_owners", owners, raising=False)
    return ac.measure("L0"), calls


def test_r242_the_ownership_map_is_read_once_per_measure_and_the_verdicts_are_unchanged(monkeypatch, tmp_path):
    """Three assets need the registry-wide ownership map; it is read ONCE. The verdicts are exactly the
    per-asset grading of that map (bg_a's table has no declaring owner -> FAIL; bg_b / bg_c write a
    partition of chart_facts, declared by ga_positions -> PASS). Fails without the fix: 3 reads (the
    `setdefault` argument was evaluated on every call)."""
    c, calls = _target_less_layer(monkeypatch, tmp_path, {"chart_facts": ["ga_positions"]})
    assert len(calls) == 1, calls
    got = {a: (w1._m(c, a, "Build.target")["v"], w1._m(c, a, "Build.target")["measured"]) for a in ("bg_a", "bg_b", "bg_c")}
    expect = {a: (lambda g: (g["v"], g["measured"]))(ac._grade_target_less(
        dict(asset_id=a, count_sql=f"SELECT count(*) FROM {t}"), lambda: {"chart_facts": ["ga_positions"]}))
        for a, t in (("bg_a", "t_main"), ("bg_b", "chart_facts"), ("bg_c", "chart_facts"))}
    assert got == expect, (got, expect)
    assert got["bg_a"][0] == ac.FAIL and got["bg_b"][0] == got["bg_c"][0] == ac.PASS, got


def test_r242_an_unreadable_map_is_not_cached_as_empty(monkeypatch, tmp_path):
    """A read that raises is not cached as an empty map (which would turn the next asset's partition
    PASS into a false FAIL): each asset that needs it reads ERRORED."""
    reg = {"bg_b": w1._reg_row("bg_b", None, count_sql="SELECT count(*) FROM chart_facts"),
           "bg_c": w1._reg_row("bg_c", None, count_sql="SELECT count(*) FROM chart_facts")}
    w1._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"chart_facts": 3}))

    def boom():
        raise ac.Unknown("relation gone")
    monkeypatch.setattr(ac, "target_owners", boom, raising=False)
    c = ac.measure("L0")
    assert {w1._m(c, a, "Build.target")["v"] for a in ("bg_b", "bg_c")} == {ac.ERRORED}
