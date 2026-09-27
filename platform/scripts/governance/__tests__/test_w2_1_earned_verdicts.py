"""test_w2_1_earned_verdicts.py — Nikaṣa wave 2, packet W2-1: no unearned closure, no silent absence.

One section per register row (R224, R231, R223, R222, R225, R42, R52, R56, R48). Every test drives the
REAL census code path — `registry()`, `live_counts()`, `psql()`, `measure()` — with only the database
answered by a stub (or, in the `live_` tests, by the real read-only database). No test here greps
source text.

Two offline harnesses are reused from `test_a4_gate_corrections.py`'s discipline:

- `_FakeRegistryDB` answers the census's registry/throughput SQL by EVALUATING the scope predicate the
  census actually sent (a `layer = '…'` equality, an `asset_id LIKE '…%'` prefix, or an
  `asset_id IN (…)` list) against a fixed row set — so a census that asks the wrong question gets the
  wrong rows, exactly as PostgreSQL would give it.
- `_stub_layer` (below) replaces the census's layer-wide reads with fixed values so the REAL
  `measure()` grades each asset offline.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_w2_1_earned_verdicts.py -v
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

CANONICAL = "482012f1-710e-4a25-994a-93821f5871aa"


def _db_reachable() -> bool:
    try:
        ac.scalar("SELECT 1")
        return True
    except Exception:
        return False


LIVE = pytest.mark.skipif(not _db_reachable(), reason="no live DB in this environment (PGHOST/PGPORT/etc.)")


# ─────────────────────────── offline harnesses ───────────────────────────

class _FakeRegistryDB:
    """A registry of (asset_id, layer, is_active) rows that answers `registry()` / `throughput()` /
    `build_history()` by evaluating whichever asset-scope predicate the census's SQL carries."""

    def __init__(self, rows):
        self.rows = rows  # list of dict(asset_id, layer, is_active)

    def _admit(self, sql):
        m = re.search(r"layer = '([a-z_]+)'", sql)
        if m:
            return lambda r: r["layer"] == m.group(1)
        m = re.search(r"asset_id LIKE '([a-z_]+)%'", sql)
        if m:
            return lambda r: r["asset_id"].startswith(m.group(1).replace("\\", ""))
        m = re.search(r"asset_id IN \(([^)]*)\)", sql)
        if m:
            ids = {x.strip().strip("'") for x in m.group(1).split(",")}
            return lambda r: r["asset_id"] in ids
        raise AssertionError(f"query carries no asset scope the fake understands: {sql[:120]}")

    def psql(self, sql, sep="\x1f", timeout=None):
        admit = self._admit(sql)
        rows = [r for r in self.rows if admit(r)]
        if sql.startswith("SELECT count(*)::text FROM asset_registry"):
            return [[str(len(rows))]]
        if "NOT (is_active AND NOT coalesce(dead_flag,false))" in sql:
            return [[r["asset_id"], "f", ""] for r in rows if not r["is_active"]]
        if "json_agg" in sql:
            return [[json.dumps([dict(asset_id=r["asset_id"], has_writer=False, target_table=None,
                                      count_sql="", has_integrity=False, depends_on=[], target_floor=None,
                                      catalog_status="", asset_kind="data")
                                 for r in sorted(rows, key=lambda r: r["asset_id"]) if r["is_active"]])]]
        if "FROM asset_throughput" in sql:
            return [[r["asset_id"], "lit", "7", "", "2026-09-27", ""] for r in rows]
        raise AssertionError(f"unexpected query: {sql[:120]}")


_MIMAMSA = [dict(asset_id="mi_kula", layer="mimamsa", is_active=True),
            dict(asset_id="lel_events", layer="mimamsa", is_active=True),
            dict(asset_id="mi_retired", layer="mimamsa", is_active=False),
            dict(asset_id="ph_other", layer="phala", is_active=True)]


def _use_fake(monkeypatch, db):
    monkeypatch.setattr(ac, "psql", db.psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: (lambda r: r[0][0] if r and r[0] else None)(db.psql(sql)))


# ─────────────────────────── R224: population by asset_registry.layer ───────────────────────────

def test_r224_registry_measures_an_active_asset_outside_the_prefix(monkeypatch):
    """`lel_events` is layer='mimamsa' with no `mi_` prefix. Fails without the fix: the prefix-scoped
    registry() returned mi_kula only (active 1 of 2 registry rows), and lel_events was never measured."""
    _use_fake(monkeypatch, _FakeRegistryDB(_MIMAMSA))
    reg, pop = ac.registry("L5")
    assert sorted(reg) == ["lel_events", "mi_kula"], sorted(reg)
    assert pop["active"] == 2 and pop["registry_total"] == 3
    assert [x["asset_id"] for x in pop["excluded_inactive"]] == ["mi_retired"]


def test_r224_build_record_is_read_for_the_measured_population_not_the_prefix(monkeypatch):
    """The per-layer reads follow the measured population: lel_events' build record is read. Fails
    without the fix: throughput() selected `asset_id LIKE 'mi_%'` and never returned lel_events."""
    _use_fake(monkeypatch, _FakeRegistryDB(_MIMAMSA))
    reg, _ = ac.registry("L5")
    thru = ac.throughput("mi_", sorted(reg))
    assert "lel_events" in thru and "ph_other" not in thru


@LIVE
def test_live_r224_population_is_127_and_includes_lel_events():
    """Live, read-only: the six layers' active populations sum to the registry-wide active count
    (127 on 2026-09-27) — the tracker's figure — and L5 includes lel_events."""
    total = int(ac.scalar("SELECT count(*)::text FROM asset_registry WHERE is_active AND dead_flag IS NOT TRUE"))
    per = {k: ac.registry(k) for k in ac.LAYERS}
    assert sum(p["active"] for _r, p in per.values()) == total
    assert "lel_events" in per["L5"][0]


# ─────────────────────────── offline measure() harness ───────────────────────────

def _reg_row(aid, target_table=None, has_writer=True, count_sql="", target_floor=None, asset_kind="data"):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql=count_sql,
                has_integrity=bool(count_sql), depends_on=[], target_floor=target_floor, catalog_status="",
                asset_kind=asset_kind)


def _stub_layer(monkeypatch, ctrl, reg, tables=None, thru=None, writers=None):
    """Every layer-wide read measure() makes, fixed. `live_counts` is NOT stubbed: each test either
    stubs `ac.psql` (so the real live_counts runs its real binding/fallback logic) or overrides it."""
    tables = tables or {}
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix, *a, **k: dict(writers or {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: dict(thru or {}))
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0,
                                                                          global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t: dict(modules=[], density=0, note="", scanned=True))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=3, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "_run_carriage_detector", lambda aid: dict(v=ac.NO_DET, measured="stub"))


def _m(census, aid, crit):
    return next(a for a in census["assets"] if a["asset_id"] == aid)["measurements"].get(crit)


def _rec(rows_written, state="lit"):
    return dict(state=state, rows_written=str(rows_written), rps="", last_built="2026-09-27")


def _pg_like_psql(values: dict):
    """Answers count queries the way PostgreSQL would: an unbound `$1` is an error ("there is no
    parameter $1"); otherwise the value keyed by the first table named after FROM."""
    def fake(sql, sep="\x1f", timeout=None):
        if re.search(r"\$\d", sql):
            raise ac.Unknown("ERROR:  there is no parameter $1")
        out = []
        for part in sql.split(" UNION ALL "):
            m = re.search(r"SELECT '([^']+)' a,", part)
            tbl = re.search(r"FROM ([a-z_]+)", part.split(",", 1)[1] if m else part).group(1)
            v = values[tbl](part) if callable(values[tbl]) else values[tbl]
            out.append([m.group(1), str(v)] if m else [str(v)])
        return out
    return fake


# ─────────────────────────── R231: bind the canonical chart to $1 ───────────────────────────

def test_r231_chart_scoped_count_sql_is_bound_and_measured(monkeypatch, tmp_path):
    """A `WHERE chart_id = $1` count_sql is bound to the canonical chart and graded against THAT
    chart's build record. Fails without the fix: the unbound `$1` errors and Build.completion reads
    ERRORED (the 78 L1–L5 readings of A_REVIEW2 G4)."""
    reg = {"ga_x": _reg_row("ga_x", "ga_t", count_sql="SELECT count(*) FROM ga_t WHERE chart_id = $1")}
    thru = {"ga_x": {CANONICAL: _rec(5), "cb73cd3d-9eba-4220-9902-0de91566e980": _rec(9)}}
    _stub_layer(monkeypatch, tmp_path, reg, thru=thru)
    seen = []

    def count(part):
        seen.append(part)
        return 5 if f"chart_id = '{CANONICAL}'" in part else 999
    monkeypatch.setattr(ac, "psql", _pg_like_psql({"ga_t": count}))
    res = _m(ac.measure("L1"), "ga_x", "Build.completion")
    assert res["v"] == ac.PASS, res
    assert "live=5" in res["measured"] and "rows_written=5" in res["measured"], res
    assert "chart 482012f1" in res["measured"], "the verdict must name the chart it measured"
    assert seen and all(CANONICAL in s for s in seen)


def test_r231_the_build_record_is_the_bound_charts_not_another_charts(monkeypatch, tmp_path):
    """The count for the canonical chart is compared with the canonical chart's rows_written, never
    another chart's. Fails without the fix: throughput() kept one arbitrary row per asset."""
    reg = {"ga_x": _reg_row("ga_x", "ga_t", count_sql="SELECT count(*) FROM ga_t WHERE chart_id = $1")}
    thru = {"ga_x": {"cb73cd3d-9eba-4220-9902-0de91566e980": _rec(5)}}   # only ANOTHER chart was built
    _stub_layer(monkeypatch, tmp_path, reg, thru=thru)
    monkeypatch.setattr(ac, "psql", _pg_like_psql({"ga_t": 5}))
    res = _m(ac.measure("L1"), "ga_x", "Build.completion")
    assert res["v"] == ac.FAIL and "no build record" in res["measured"], res


def test_r231_an_unbindable_parameter_is_errored_not_run_half_bound(monkeypatch):
    reg = {"ga_x": dict(count_sql="SELECT count(*) FROM ga_t WHERE chart_id = $1 AND k = $2")}
    monkeypatch.setattr(ac, "psql", _pg_like_psql({"ga_t": 1}))
    counts, errored = ac.live_counts(reg, CANONICAL)
    assert counts["ga_x"] is None and "$2" in errored["ga_x"]


def test_r231_the_phantom_chart_is_refused():
    with pytest.raises(ac.Unknown, match="phantom"):
        ac._bind_chart("SELECT count(*) FROM t WHERE chart_id = $1", "362f9f17-0000-0000-0000-000000000000")


@LIVE
def test_live_r231_every_l4_count_sql_is_measured_for_the_canonical_chart():
    """Live, read-only: all nine L4 count_sql are chart-scoped; bound to the canonical chart, every
    one returns an integer (before R231 all nine errored)."""
    reg, _ = ac.registry("L4")
    counts, errored = ac.live_counts(reg, CANONICAL)
    assert not errored, errored
    assert all(isinstance(counts[a], int) for a in reg), counts
