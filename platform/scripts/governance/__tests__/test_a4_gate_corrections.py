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
    return []  # every later layer-wide read sees an empty estate — what a zero population measures


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


# ─────────────────────────── offline measure() harness ───────────────────────────

def _reg_row(aid, target_table=None, has_writer=False):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql="",
                has_integrity=False, depends_on=[], target_floor=None, catalog_status="", asset_kind="")


def _stub_layer(monkeypatch, ctrl, reg, tables=None):
    """Replace every layer-wide DB read measure() makes with fixed values, so the REAL measure()
    runs offline. `tables` maps table -> (columns, declared keys). Per-asset queries that are not
    stubbed here reach `ac.psql`, which each test stubs for the query under test."""
    tables = tables or {}
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=3, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def _measured(census, aid, crit):
    return next(a for a in census["assets"] if a["asset_id"] == aid)["measurements"][crit]


# ─────────────────────────── F8: a registered detector's exit code and vocabulary ───────────────────────────

def _detector(ctrl, aid, body):
    d = ctrl / "detectors"
    d.mkdir(exist_ok=True)
    (d / f"{aid}_D1.py").write_text(body, encoding="utf-8")


def test_f8_a_detector_that_crashes_after_printing_pass_is_not_a_pass(monkeypatch, tmp_path):
    """Fails without the fix: the census adopted the last stdout line (`PASS`) and ignored exit 1."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x")})
    _detector(tmp_path, "bg_x", 'import json, sys\n'
                                'print(json.dumps({"verdict": "PASS", "measured": "looked fine"}))\n'
                                'sys.exit("crashed after printing")\n')
    res = _measured(ac.measure("L0"), "bg_x", "Carr.detector")
    assert res["v"] == ac.NO_DET, res
    assert "exited 1" in res["measured"] and "crashed after printing" in res["measured"]


def test_f8_a_verdict_outside_the_closed_set_is_not_adopted(monkeypatch, tmp_path):
    """Fails without the fix: `GREEN` (or any string) was adopted as the verdict verbatim."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x")})
    _detector(tmp_path, "bg_x", 'import json\nprint(json.dumps({"verdict": "GREEN", "measured": "ok"}))\n')
    res = _measured(ac.measure("L0"), "bg_x", "Carr.detector")
    assert res["v"] == ac.NO_DET, res
    assert "'GREEN'" in res["measured"] and "outside the closed set" in res["measured"]


def test_f8_a_clean_detector_verdict_is_still_adopted(monkeypatch, tmp_path):
    """Positive control: the fix must not blind a detector that ran cleanly."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x")})
    _detector(tmp_path, "bg_x", 'import json\nprint(json.dumps({"verdict": "FAIL", "measured": "3 mismatches"}))\n')
    res = _measured(ac.measure("L0"), "bg_x", "Carr.detector")
    assert res == dict(v=ac.FAIL, measured="bg_x_D1.py: 3 mismatches")


# ─────────────────────────── F9: Vocab.identity states its duplicate figure ───────────────────────────

_T = {"bg_t": (["id", "a", "b", "v"], [["id"], ["a", "b"]])}


def _identity_psql(exists: str, count_row=None, count_raises=False):
    def fake(sql, sep="\x1f", timeout=None):
        if "SELECT EXISTS(SELECT 1 FROM bg_t GROUP BY a, b HAVING count(*) > 1)" in sql:
            return [[exists]]
        if "HAVING count(*) > 1) d" in sql:
            if count_raises:
                raise ac.Unknown("SIMULATED: statement timeout")
            return [count_row]
        raise AssertionError(f"unexpected query in F9 stub: {sql[:80]}")
    return fake


def test_f9_identity_fail_states_the_duplicate_count(monkeypatch, tmp_path):
    """Fails without the fix: the measurement read "duplicate group(s) exist" with no figure."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x", "bg_t")}, _T)
    monkeypatch.setattr(ac, "psql", _identity_psql("t", ["2", "7"]))
    res = _measured(ac.measure("L0"), "bg_x", "Vocab.identity")
    assert res == dict(v=ac.FAIL, measured="declared key (a, b): 7 duplicate(s) in 2 duplicate group(s)")


def test_f9_identity_pass_states_zero_and_never_runs_the_count(monkeypatch, tmp_path):
    """The clean case keeps R40's cost: the count query is never issued (the stub would count it),
    and the figure is the explicit 0 the pre-R40 text carried."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x", "bg_t")}, _T)
    monkeypatch.setattr(ac, "psql", _identity_psql("f"))
    res = _measured(ac.measure("L0"), "bg_x", "Vocab.identity")
    assert res == dict(v=ac.PASS, measured="declared key (a, b): 0 duplicate(s)")


def test_f9_a_count_that_errors_keeps_the_probe_fail(monkeypatch, tmp_path):
    """The verdict is the probe's; a failed count must neither turn it ERRORED nor hide the defect."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x", "bg_t")}, _T)
    monkeypatch.setattr(ac, "psql", _identity_psql("t", count_raises=True))
    res = _measured(ac.measure("L0"), "bg_x", "Vocab.identity")
    assert res["v"] == ac.FAIL
    assert "the count errored (SIMULATED: statement timeout)" in res["measured"]


# ─────────────────────────── F12: the R41 scope limit is disclosed where it bites ───────────────────────────

def test_f12_a_failed_layer_wide_read_names_itself_and_the_r41_limit(monkeypatch, tmp_path, capsys):
    """R41 isolates per-asset checks only; a layer-wide read failing still aborts the layer. That is
    fail-closed (exit 4) but was silent about its scope: the message did not say which read failed or
    that the WHOLE layer (and, under several layers, every later layer) went unmeasured. Fails
    without the fix: the output carries neither the read's name nor the scope line."""
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x")})

    def boom(prefix, *a, **k):
        raise ac.Unknown("SIMULATED: canceling statement due to statement timeout")

    monkeypatch.setattr(ac, "build_history", boom)
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0,L1", "--out", str(tmp_path / "c.json")])
    rc = ac.main()
    out = capsys.readouterr().out
    assert rc == 4
    assert "layer L0: layer-wide read 'build_history' failed: SIMULATED" in out, out
    assert "R41 isolates per-asset checks only" in out and "stops every layer after it" in out, out
    assert not (tmp_path / "c.json").exists()
