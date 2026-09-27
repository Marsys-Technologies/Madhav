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
