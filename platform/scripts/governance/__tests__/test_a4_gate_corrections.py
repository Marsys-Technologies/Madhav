"""test_a4_gate_corrections.py — Lane A gate corrections F6–F9 and F12
(`00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/A_REVIEW.md` §3), each a behavioural test that
fails without its fix. No test here greps source text or exercises a helper defined in this file in
place of the real code path (the defect class F3 named).

Two offline harnesses:

- `_FakePsycopg2` backs the tracker's `psycopg2` import with an in-memory SQLite database, so the
  tracker's REAL SQL text is executed by a real SQL engine with real three-valued NULL logic. A
  population predicate that is missing, or that falls into the `NOT dead_flag` NULL trap, returns the
  wrong rows here exactly as it would on PostgreSQL.
- `_stub_layer` replaces the census's layer-wide database reads (registry, catalog, throughput,
  build history, …) with fixed values so the REAL `measure()` runs end to end offline; the per-asset
  query under test is then answered by a stubbed `psql`.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_a4_gate_corrections.py -v
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sqlite3
import sys
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

REPO = HERE.parents[3]
TRACKER_PATH = REPO / "00_ARCHITECTURE" / "control" / "asset_elevation_tracker.py"


def _load_tracker(monkeypatch, ctrl: pathlib.Path):
    """Import the tracker fresh with NIKASHA_CONTROL_DIR pointed at a temp dir, so its module-level
    ledger/output paths never resolve to the production control directory."""
    monkeypatch.setenv("NIKASHA_CONTROL_DIR", str(ctrl))
    spec = importlib.util.spec_from_file_location("asset_elevation_tracker_under_test", TRACKER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────── F6: tracker population scoping ───────────────────────────

class _FakeCursor:
    def __init__(self, db: sqlite3.Connection):
        self._c = db.cursor()

    def execute(self, sql, params=()):
        self._c.execute(sql.replace("%s", "?"), tuple(params))

    def fetchall(self):
        return self._c.fetchall()

    def fetchone(self):
        return self._c.fetchone()

    def close(self):
        self._c.close()


class _FakeConn:
    def __init__(self, db):
        self._db = db

    def set_session(self, **_kw):
        pass

    def cursor(self):
        return _FakeCursor(self._db)

    def rollback(self):
        pass

    def close(self):
        pass


def _fake_psycopg2(rows):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE asset_registry (asset_id TEXT, layer TEXT, target_table TEXT, storage_type TEXT,"
               " scope TEXT, is_active BOOLEAN, dead_flag BOOLEAN, catalog_status TEXT, has_writer BOOLEAN,"
               " depends_on TEXT, count_sql TEXT, integrity_check_sql TEXT, sort_order INTEGER)")
    for i, (aid, is_active, dead_flag) in enumerate(rows):
        db.execute("INSERT INTO asset_registry VALUES (?,?,NULL,NULL,NULL,?,?,'',1,'',NULL,NULL,?)",
                   (aid, "brahmagyan", is_active, dead_flag, i))
    mod = types.ModuleType("psycopg2")
    mod.connect = lambda dsn: _FakeConn(db)
    return mod


# dead_flag is NULL on every production row today; one row of each shape here.
_REGISTRY_ROWS = [
    ("bg_live_null_dead", True, None),    # active — the production shape (dead_flag NULL)
    ("bg_live_false_dead", True, False),  # active
    ("bg_retired", False, None),          # inactive — excluded
    ("bg_dead", True, True),              # explicitly dead — excluded
]


def test_f6_tracker_counts_only_the_active_population_and_states_it(monkeypatch, tmp_path):
    """F6: before the fix the tracker applied no population filter and counted every registry row
    (129 registry-wide, 23 in L3) where the census counts the 127 (21) active ones. Fails without the
    fix: 4 assets instead of 2 and no population figure. Fails under the NULL-trap mutation
    (`is_active AND NOT dead_flag`): 1 asset, because SQLite, like PostgreSQL, drops the NULL row."""
    tr = _load_tracker(monkeypatch, tmp_path)
    monkeypatch.setitem(sys.modules, "psycopg2", _fake_psycopg2(_REGISTRY_ROWS))
    monkeypatch.setenv("DATABASE_URL", "fake://")
    rows, reason, population = tr.registry(None, "L0")
    assert reason is None
    assert sorted(rows) == ["bg_live_false_dead", "bg_live_null_dead"]
    assert population["registry_total"] == 4
    assert population["active"] == 2
    assert population["excluded_inactive"] == ["bg_dead", "bg_retired"]

    out = tr.scan(["L0"], None)
    layer = out["layers"]["L0"]
    assert layer["n_assets"] == 2
    assert layer["population"]["active"] + len(layer["population"]["excluded_inactive"]) \
        == layer["population"]["registry_total"]


# ─────────────────────────── F7: a zero-active population is UNKNOWN, never exit 0 ───────────────────────────

def _registry_psql_with_nothing_active(sql, sep="\x1f", timeout=None):
    """asset_registry holds 5 rows for the prefix and none of them is active — the shape the
    `NOT dead_flag` NULL trap (M9) produces on production, where every row's dead_flag is NULL."""
    if sql.startswith("SELECT count(*)::text FROM asset_registry"):
        return [["5"]]
    if "NOT (is_active AND NOT coalesce(dead_flag,false))" in sql:
        return [[f"bg_{i}", "t", ""] for i in range(5)]
    if "json_agg" in sql:
        return [["[]"]]
    raise AssertionError(f"unexpected query in F7 stub: {sql[:80]}")


def test_f7_registry_raises_unknown_on_zero_active_rows(monkeypatch):
    """Fails without the fix: registry() returned ({}, population) and measure() ran on nothing."""
    monkeypatch.setattr(ac, "psql", _registry_psql_with_nothing_active)
    with pytest.raises(ac.Unknown, match="zero active bg_"):
        ac.registry("L0")


def test_f7_main_exits_4_with_a_message_on_zero_active_rows(monkeypatch, tmp_path, capsys):
    """End to end through main(): a census that finds zero active assets must exit 4 (UNKNOWN) and
    say why. Fails without the fix: main() printed "0 assets" and returned 0 (clean)."""
    monkeypatch.setattr(ac, "psql", _registry_psql_with_nothing_active)
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--out", str(tmp_path / "c.json")])
    rc = ac.main()
    out = capsys.readouterr().out
    assert rc == 4, out
    assert "UNKNOWN" in out and "zero active bg_" in out and "5 registry row(s)" in out
