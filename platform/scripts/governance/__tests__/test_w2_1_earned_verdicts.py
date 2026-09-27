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
# The real functions, captured at import before any test monkeypatches them.
_REAL = {n: getattr(ac, n) for n in ("depth_census", "capability_scan", "live_counts", "throughput")}


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
            mt = re.search(r"FROM ([a-z_]+)", part.split(",", 1)[1] if m else part)
            if mt is None:                                   # a constant count_sql: its literal
                v = re.search(r"\(SELECT (\d+)", part).group(1)
            else:
                v = values[mt.group(1)](part) if callable(values[mt.group(1)]) else values[mt.group(1)]
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


# ─────────────────────────── R223: a real client-side timeout degrades the check ───────────────────────────

@pytest.fixture
def sleeping_psql(tmp_path, monkeypatch):
    """A `psql` on PATH that never answers, and a 1 s client timeout: `subprocess.run` raises the
    REAL `subprocess.TimeoutExpired` — not a stand-in built from the census's own error type (the
    defect A_REVIEW2 G3 found in the R41 tests)."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "psql"
    fake.write_text("#!/bin/sh\nexec sleep 30\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setattr(ac, "PSQL_TIMEOUT_SECONDS", 1)
    return fake


def test_r223_psql_converts_the_real_timeout_expired(sleeping_psql):
    with pytest.raises(ac.Unknown) as ei:
        ac.psql("SELECT pg_sleep(60)")
    assert isinstance(ei.value, ac.CheckTimeout)
    assert isinstance(ei.value.__cause__, subprocess.TimeoutExpired), "must be the real exception, converted"
    assert "timeout after 1s" in str(ei.value)


def test_r223_a_real_timeout_in_one_check_grades_errored_and_the_layer_completes(sleeping_psql, monkeypatch, tmp_path):
    """measure() end to end: the depth query of one asset times out for real. Fails without the fix:
    `TimeoutExpired` escapes the per-check `except Unknown` and aborts measure() (exit 5 in main)."""
    reg = {"bg_x": _reg_row("bg_x", "bg_t", has_writer=False)}
    _stub_layer(monkeypatch, tmp_path, reg, tables={"bg_t": (["a"], [])})
    monkeypatch.setattr(ac, "depth_census", _REAL["depth_census"])   # the real query path
    c = ac.measure("L0")
    res = _m(c, "bg_x", "Complete.depth")
    assert res["v"] == ac.ERRORED and "timeout after 1s" in res["measured"], res
    assert _m(c, "bg_x", "Build.registered")["v"] == ac.NA, "the other checks must still be measured"



# ─────────────────────────── R222: the four latent unmeasured → closable paths (A_REVIEW2 G2) ───────────────────────────

def _open_gap(ctrl, aid, crit):
    (ctrl / "asset_gaps.jsonl").open("a", encoding="utf-8").write(json.dumps(dict(
        asset=aid, gap_id=f"{aid}-{crit}", kind="gap", criterion=crit, what="w", change="", detector="d",
        owner="asset_census", gate="g", state="OPEN", ts="t0")) + "\n")


def _emit_closes(ctrl, census) -> int:
    return ac.emit_gaps(census)[2]


def test_r222_n1_a_count_sql_returning_null_is_errored_and_closes_nothing(monkeypatch, tmp_path):
    """Fails without the fix: NULL mapped to `None` with no error, Build.completion read N/A "no
    count_sql" (false text) and the open gap CLOSED."""
    reg = {"bg_x": _reg_row("bg_x", "bg_t", count_sql="SELECT NULL::bigint")}
    _stub_layer(monkeypatch, tmp_path, reg, thru={"bg_x": {"": _rec(3)}})
    monkeypatch.setattr(ac, "psql", lambda sql, sep="\x1f", timeout=None: [["bg_x", ""]])
    _open_gap(tmp_path, "bg_x", "Build.completion")
    c = ac.measure("L0")
    res = _m(c, "bg_x", "Build.completion")
    assert res["v"] == ac.ERRORED and "returned NULL" in res["measured"], res
    assert "no count_sql" not in res["measured"]
    assert _emit_closes(tmp_path, c) == 0


def test_r222_n1_a_genuinely_absent_count_sql_is_na_only_when_nothing_is_built(monkeypatch, tmp_path):
    """The genuine N/A survives for a declared service with no target_table (the six live cases);
    a writer-backed data asset with no count_sql is NO_DETECTOR — completion unmeasurable."""
    reg = {"bg_svc": _reg_row("bg_svc", None, has_writer=True, asset_kind="service"),
           "bg_data": _reg_row("bg_data", "bg_t", has_writer=True, asset_kind="data")}
    _stub_layer(monkeypatch, tmp_path, reg)
    c = ac.measure("L0")
    assert _m(c, "bg_svc", "Build.completion")["v"] == ac.NA
    assert _m(c, "bg_data", "Build.completion")["v"] == ac.NO_DET


def test_r222_n2_an_unrecognised_writer_is_no_detector_and_closes_nothing(monkeypatch, tmp_path):
    """has_writer=true, no recognised @register: Build.contract / Idem.pattern were never scanned.
    Fails without the fix: both read N/A "no writer file" and the open Idem.pattern gap CLOSED."""
    reg = {"bg_reference": _reg_row("bg_reference", None, has_writer=True, asset_kind="service")}
    _stub_layer(monkeypatch, tmp_path, reg, writers={})
    _open_gap(tmp_path, "bg_reference", "Idem.pattern")
    _open_gap(tmp_path, "bg_reference", "Build.contract")
    c = ac.measure("L0")
    for crit in ("Build.contract", "Idem.pattern"):
        res = _m(c, "bg_reference", crit)
        assert res["v"] == ac.NO_DET and "never scanned" in res["measured"], (crit, res)
    assert _emit_closes(tmp_path, c) == 0


def test_r222_n2_no_writer_with_registry_agreement_stays_a_genuine_na(monkeypatch, tmp_path):
    reg = {"bg_svc": _reg_row("bg_svc", None, has_writer=False, asset_kind="service")}
    _stub_layer(monkeypatch, tmp_path, reg, writers={})
    c = ac.measure("L0")
    assert _m(c, "bg_svc", "Build.contract")["v"] == ac.NA
    assert _m(c, "bg_svc", "Idem.pattern")["v"] == ac.NA
    assert ac.contract_scan("bg_svc", [])[0] == ac.NO_DET, "the raw scan never claims N/A for itself"


def test_r222_n3_a_missing_capability_directory_is_no_detector_and_closes_nothing(monkeypatch, tmp_path):
    """The REAL capability_scan against a directory that does not exist. Fails without the fix:
    Dens.served read N/A and the open gap CLOSED (24 of them in A_REVIEW2's live run)."""
    reg = {"bg_x": _reg_row("bg_x", "bg_t", has_writer=False)}
    _stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "capability_scan", _REAL["capability_scan"])
    monkeypatch.setitem(ac.LAYERS["L0"], "caps", str(tmp_path / "no_such_caps_dir"))
    _open_gap(tmp_path, "bg_x", "Dens.served")
    c = ac.measure("L0")
    res = _m(c, "bg_x", "Dens.served")
    assert res["v"] == ac.NO_DET and "never scanned" in res["measured"], res
    assert _emit_closes(tmp_path, c) == 0


def test_r222_n3_a_scanned_directory_with_no_referencing_module_is_a_genuine_na(monkeypatch, tmp_path):
    caps = tmp_path / "caps"
    caps.mkdir()
    (caps / "other.ts").write_text("export const T = 'bg_unrelated';\n", encoding="utf-8")
    reg = {"bg_x": _reg_row("bg_x", "bg_t", has_writer=False)}
    _stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "capability_scan", _REAL["capability_scan"])
    monkeypatch.setitem(ac.LAYERS["L0"], "caps", str(caps))
    assert _m(ac.measure("L0"), "bg_x", "Dens.served")["v"] == ac.NA


def _empty_table_psql(sql, sep="\x1f", timeout=None):
    if sql.startswith("SELECT count(*)::text FROM bg_t"):
        return [["0"]]
    if "HAVING count(*) > 1)::text" in sql:
        return [["f"]]                                        # no duplicate group — on no rows
    if sql.startswith("SELECT EXISTS(SELECT 1 FROM bg_t)"):
        return [["f"]]
    raise AssertionError(f"unexpected query: {sql[:100]}")


def test_r222_n5_an_empty_table_is_no_detector_on_depth_and_closes_nothing(monkeypatch, tmp_path):
    """The REAL depth_census over a table with 0 rows. Fails without the fix: Complete.depth read
    PASS ("table empty") and the open gap CLOSED — truncating a table 'fixed' its depth."""
    reg = {"bg_x": _reg_row("bg_x", "bg_t", has_writer=False)}
    _stub_layer(monkeypatch, tmp_path, reg, tables={"bg_t": (["a", "b"], [["a", "b"]])})
    monkeypatch.setattr(ac, "depth_census", _REAL["depth_census"])
    monkeypatch.setattr(ac, "psql", _empty_table_psql)
    _open_gap(tmp_path, "bg_x", "Complete.depth")
    _open_gap(tmp_path, "bg_x", "Vocab.identity")
    c = ac.measure("L0")
    res = _m(c, "bg_x", "Complete.depth")
    assert res["v"] == ac.NO_DET and "0 rows" in res["measured"], res
    ident = _m(c, "bg_x", "Vocab.identity")
    assert ident["v"] == ac.NO_DET and "vacuous" in ident["measured"], ident
    assert _emit_closes(tmp_path, c) == 0


def test_r222_n5_identity_on_an_empty_table_probes_when_depth_errored(monkeypatch, tmp_path):
    """With the depth census errored there is no row count in hand; the identity check probes
    emptiness itself rather than reading '0 duplicates' on a table it never saw a row of."""
    reg = {"bg_x": _reg_row("bg_x", "bg_t", has_writer=False)}
    _stub_layer(monkeypatch, tmp_path, reg, tables={"bg_t": (["a", "b"], [["a", "b"]])})
    monkeypatch.setattr(ac, "depth_census", lambda t, c: (_ for _ in ()).throw(ac.Unknown("SIMULATED")))
    monkeypatch.setattr(ac, "psql", _empty_table_psql)
    c = ac.measure("L0")
    assert _m(c, "bg_x", "Complete.depth")["v"] == ac.ERRORED
    assert _m(c, "bg_x", "Vocab.identity")["v"] == ac.NO_DET


# ─────────────────────────── R225: the measure() call site, with the instrument present ───────────────────────────

def test_r225_measure_with_the_instrument_present_reads_no_detector_and_closes_nothing(monkeypatch, tmp_path):
    """The REAL measure() with `duration_instrument_present` forced True (migration 1094 applied):
    both Earn.build_record and Cost.baseline must read `NO_DETECTOR — attempt linkage not wired`,
    and an open Earn gap must not close. Fails if the call site passes `attempt_linkage_wired=True`
    (or, before the safe default, merely omits it) — the G1 mutation F1b that no test caught."""
    reg = {"bg_x": _reg_row("bg_x", None, has_writer=True, asset_kind="service")}
    _stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: True)
    _open_gap(tmp_path, "bg_x", "Earn.build_record")
    c = ac.measure("L0")
    for crit in ("Earn.build_record", "Cost.baseline"):
        res = _m(c, "bg_x", crit)
        assert res == dict(v=ac.NO_DET, measured="NO_DETECTOR — attempt linkage not wired"), (crit, res)
    assert _emit_closes(tmp_path, c) == 0


def test_r225_the_default_is_the_safe_value():
    earn, cost = ac._grade_earn_cost(attempt=None, instrument_present=True, baseline=None)
    assert earn["v"] == ac.NO_DET and cost["v"] == ac.NO_DET


# ─────────────────────────── R42: Build.completion compares, like with like ───────────────────────────

_KULA_SQL = ("SELECT (SELECT count(*) FROM mimamsa_signal_families) + "
             "(SELECT count(*) FROM mimamsa_negative_controls) AS count")


def _completion(monkeypatch, tmp_path, count_sql, live, rec, target="t_main", depth_rows=3, floor=None):
    reg = {"mi_x": _reg_row("mi_x", target, count_sql=count_sql, target_floor=floor)}
    _stub_layer(monkeypatch, tmp_path, reg, tables={target: (["a"], [])} if target else None,
                thru={"mi_x": {"": rec}} if rec is not None else {})
    monkeypatch.setattr(ac, "depth_census",
                        lambda t, c: dict(columns=1, rows=depth_rows, full=["a"], never=[], note=""))
    first = (ac._count_tables(count_sql) or ["none"])[0]
    monkeypatch.setattr(ac, "psql", _pg_like_psql({first: live}))
    return ac.measure("L5")


def test_r42_a_disagreeing_build_record_fails(monkeypatch, tmp_path):
    """rows_written=15 against a live count of 11 on a single-table asset. Fails without the fix:
    the final branch read PASS for any rows_written > 0 — it never compared."""
    c = _completion(monkeypatch, tmp_path, "SELECT count(*) FROM t_main", 11, _rec(15))
    res = _m(c, "mi_x", "Build.completion")
    assert res["v"] == ac.FAIL and "rows_written=15 disagrees with live=11" in res["measured"], res


def test_r42_multi_table_compares_the_total_like_for_like_and_states_the_target_alone(monkeypatch, tmp_path):
    """mi_kula's shape: count_sql sums two tables (11 + 4); the writer reports the same two-table
    total (15). Like-for-like they agree — and the verdict says so, naming both tables and the
    target table's own 11 rows as context, so '15' is never presented as the target's rows."""
    c = _completion(monkeypatch, tmp_path, _KULA_SQL, 15, _rec(15), target="mimamsa_signal_families",
                    depth_rows=11)
    res = _m(c, "mi_x", "Build.completion")
    assert res["v"] == ac.PASS, res
    assert "count_sql total over 2 table(s): mimamsa_signal_families, mimamsa_negative_controls" in res["measured"]
    assert "mimamsa_signal_families alone: 11 row(s)" in res["measured"], res
    a = next(x for x in c["assets"] if x["asset_id"] == "mi_x")
    assert a["count_sql_tables"] == ["mimamsa_signal_families", "mimamsa_negative_controls"]


def test_r42_multi_table_disagreement_fails(monkeypatch, tmp_path):
    c = _completion(monkeypatch, tmp_path, _KULA_SQL, 11, _rec(15), target="mimamsa_signal_families",
                    depth_rows=11)
    assert _m(c, "mi_x", "Build.completion")["v"] == ac.FAIL


def test_r42_a_constant_count_sql_measures_nothing(monkeypatch, tmp_path):
    """bo_samvada's `SELECT 0 AS count` reads no table; it cannot disagree with any build record."""
    c = _completion(monkeypatch, tmp_path, "SELECT 0 AS count", 0, _rec(1), target="vw_x")
    res = _m(c, "mi_x", "Build.completion")
    assert res["v"] == ac.NO_DET and "reads no table" in res["measured"], res


def test_r42_rows_left_by_a_failed_build_are_not_a_completion(monkeypatch, tmp_path):
    """A build record in state 'error' whose rows_written happens to equal the live count is not a
    completed build agreeing with the data."""
    c = _completion(monkeypatch, tmp_path, "SELECT count(*) FROM t_main", 7, _rec(7, state="error"))
    res = _m(c, "mi_x", "Build.completion")
    assert res["v"] == ac.FAIL and "state='error'" in res["measured"], res
