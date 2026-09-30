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
_REAL = {n: getattr(ac, n) for n in ("depth_census", "capability_scan", "live_counts", "throughput",
                                     "build_history")}


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
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))   # W2-2 D6 item 2: the attempt read
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)  # W2-3 R21: the DAG read
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="", scanned=True))
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
    monkeypatch.setattr(ac, "CAPS_ROOTS", (str(tmp_path / "no_such_caps_dir"),))   # E6.1(d): the scan reads CAPS_ROOTS
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
    monkeypatch.setattr(ac, "CAPS_ROOTS", (str(caps),))                           # E6.1(d): the scan reads CAPS_ROOTS
    monkeypatch.setattr(ac, "DENS_OUTSIDE_ROOTS", ())
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
    """The REAL measure() with `duration_instrument_present` forced True (migration 1094 applied).
    W2-1 pinned "NO_DETECTOR — attempt linkage not wired" here; W2-2 (D6 item 2) wires the linkage,
    so the call site now grades by the attempt read — and R225's safety property is kept where it
    matters: when the attempt read FAILED (the attempts are unknown, not absent), both Earn and Cost
    read NO_DETECTOR and an open Earn gap does not close. Fails if a failed attempt read is taken as
    "never attempted" (the closable N/A) — the same F1/G1 defect one layer down."""
    reg = {"bg_x": _reg_row("bg_x", None, has_writer=True, asset_kind="service")}
    _stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: True)

    def failed_read(ids):
        raise ac.Unknown("ERROR:  relation \"build_run_assets\" does not exist")
    monkeypatch.setattr(ac, "latest_attempts", failed_read)
    _open_gap(tmp_path, "bg_x", "Earn.build_record")
    c = ac.measure("L0")
    for crit in ("Earn.build_record", "Cost.baseline"):
        res = _m(c, "bg_x", crit)
        assert res["v"] == ac.NO_DET and "attempt read failed" in res["measured"], (crit, res)
    assert _emit_closes(tmp_path, c) == 0


def test_r225_the_default_is_the_safe_value():
    earn, cost = ac._grade_earn_cost(attempt=None, instrument_present=True, baseline=None)
    assert earn["v"] == ac.NO_DET and cost["v"] == ac.NO_DET


# ─────────────────────────── R42: Build.completion compares, like with like ───────────────────────────

_KULA_SQL = ("SELECT (SELECT count(*) FROM mimamsa_signal_families) + "
             "(SELECT count(*) FROM mimamsa_negative_controls) AS count")


def _completion(monkeypatch, tmp_path, count_sql, live, rec, target="t_main", depth_rows=3, floor=None,
                has_writer=True):
    reg = {"mi_x": _reg_row("mi_x", target, count_sql=count_sql, target_floor=floor, has_writer=has_writer)}
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


# ─────────────────────────── R52: emptying a table never flips Build.completion to PASS ───────────────────────────

@pytest.mark.parametrize("floor", [None, "5", "164575"])
@pytest.mark.parametrize("rows_written", [0, 8579])
def test_r52_emptying_a_table_never_reads_pass(monkeypatch, tmp_path, floor, rows_written):
    """The T1 plant, offline, over every build-record shape: bg_muhurta_lattice (target_floor
    164575, rows_written=0) truncated from 8579 rows to 0. Fails without the fix for
    rows_written=0: the two sides AGREED on 0 and the check read PASS ('empty by design')."""
    c = _completion(monkeypatch, tmp_path, "SELECT COUNT(*) FROM t_main", 0, _rec(rows_written), floor=floor)
    res = _m(c, "mi_x", "Build.completion")
    assert res["v"] == ac.FAIL, res
    assert "empty: live=0" in res["measured"], res


def test_r52_the_truncate_plant_flips_toward_fail_never_toward_pass(monkeypatch, tmp_path):
    before = _m(_completion(monkeypatch, tmp_path, "SELECT COUNT(*) FROM t_main", 8579, _rec(0), floor="164575"),
                "mi_x", "Build.completion")
    after = _m(_completion(monkeypatch, tmp_path, "SELECT COUNT(*) FROM t_main", 0, _rec(0), floor="164575"),
               "mi_x", "Build.completion")
    assert before["v"] == ac.FAIL and after["v"] == ac.FAIL, (before, after)


def test_r52_zero_rows_pass_only_under_the_registry_declaration(monkeypatch, tmp_path):
    """target_floor=0 is the registry's (and the engine's) declaration that zero rows is a complete
    build — but (R99, this wave: the previously-uncovered third case, ga_prashna's own shape) that
    declaration alone is only enough for PASS when the asset has no writer at all (has_writer=false
    — bg_sarvatobhadra_grid's shape, genuinely empty by design, nothing ever attempted). A
    writer-backed asset (has_writer=true — the default `_reg_row`/mi_x shape here, and ga_prashna's
    own shape) that has actually run and still produced zero rows is indistinguishable from a
    writer that has never worked, and reads the honest PARTIAL R99 introduces instead."""
    res = _m(_completion(monkeypatch, tmp_path, "SELECT COUNT(*) FROM t_main", 0, _rec(0), floor="0",
                        has_writer=False),
             "mi_x", "Build.completion")
    assert res["v"] == ac.PASS and "declared complete by target_floor=0" in res["measured"], res
    res = _m(_completion(monkeypatch, tmp_path, "SELECT COUNT(*) FROM t_main", 0, _rec(0), floor="0",
                        has_writer=True),
             "mi_x", "Build.completion")
    assert res["v"] == ac.PARTIAL and "has_writer=true" in res["measured"], (
        "R99: a writer-backed data asset that ran and produced zero rows is PARTIAL, not the R52-era "
        "blanket PASS — target_floor=0 alone is not a layer-plan claim that the emptiness is by design"
    )
    res = _m(_completion(monkeypatch, tmp_path, "SELECT COUNT(*) FROM t_main", 0, _rec(5), floor="0"),
             "mi_x", "Build.completion")
    assert res["v"] == ac.FAIL, "a declared-empty asset whose build wrote rows that are now gone still fails"


# ─────────────────────────── R56: parameterised / multi-table count_sql always yields a verdict ───────────────────────────

def test_r56_an_unmeasurable_parameterised_count_emits_errored_not_absent(monkeypatch, tmp_path):
    """A chart-scoped count_sql that cannot be bound (a second parameter) with a declared floor.
    Fails without the fix: Count.floor was silently absent whenever the count was None."""
    sql = "SELECT count(*) FROM ga_t WHERE chart_id = $1 AND k = $2"
    reg = {"ga_x": _reg_row("ga_x", "ga_t", count_sql=sql, target_floor="100")}
    _stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "psql", _pg_like_psql({"ga_t": 1}))
    c = ac.measure("L1")
    cf = _m(c, "ga_x", "Count.floor")
    assert cf is not None, "Count.floor must never be silently absent where a floor is declared"
    assert cf["v"] == ac.ERRORED and "$2" in cf["measured"] and "floor=100" in cf["measured"], cf
    assert _m(c, "ga_x", "Build.completion")["v"] == ac.ERRORED


def test_r56_a_multi_table_chart_scoped_count_is_graded_against_the_floor(monkeypatch, tmp_path):
    sql = ("SELECT (SELECT count(*) FROM bo_a WHERE chart_id = $1) + "
           "(SELECT count(*) FROM bo_b WHERE chart_id = $1) AS count")
    reg = {"bo_x": _reg_row("bo_x", "bo_a", count_sql=sql, target_floor="60000")}
    _stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "psql", _pg_like_psql({"bo_a": 7409}))
    cf = _m(ac.measure("L2"), "bo_x", "Count.floor")
    assert cf == dict(v=ac.FAIL, measured="count_sql total=7409, floor=60000, delta=-52591"), cf


@LIVE
def test_live_r56_the_differentials_three_breaches_are_reported():
    """Live, read-only, canonical chart: the three breaches the T1 differential found and the
    inspector never reported now read Count.floor FAIL (figures are the canonical chart's, not the
    sandbox's whole-table counts the differential used)."""
    for layer, aid in (("L1", "ga_vargas"), ("L2", "bo_laksana"), ("L4", "ph_sankrama")):
        reg, _ = ac.registry(layer)
        counts, errored = ac.live_counts({aid: reg[aid]}, CANONICAL)
        cf = ac._grade_count_floor(reg[aid], counts[aid], errored.get(aid), ac._count_tables(reg[aid]["count_sql"]))
        assert cf is not None and cf["v"] == ac.FAIL, (aid, cf)


# ─────────────────────────── R48: Count.floor on every asset that declares target_floor ───────────────────────────

def test_r48_a_declared_floor_without_a_count_sql_is_no_detector_not_absent(monkeypatch, tmp_path):
    """Fails without the fix: the criterion was simply absent — a declared obligation with no
    verdict and no gap."""
    reg = {"ka_x": _reg_row("ka_x", "kala_t", count_sql="", target_floor="83")}
    _stub_layer(monkeypatch, tmp_path, reg)
    cf = _m(ac.measure("L3"), "ka_x", "Count.floor")
    assert cf is not None and cf["v"] == ac.NO_DET and "target_floor=83" in cf["measured"], cf


def test_r48_a_zero_floor_is_a_declaration_not_a_vacuous_pass(monkeypatch, tmp_path):
    """target_floor=0 cannot be breached; a PASS on `live >= 0` could never read false (§N.8)."""
    reg = {"ka_svc": _reg_row("ka_svc", None, count_sql="", target_floor="0", asset_kind="service"),
           "ka_d": _reg_row("ka_d", "kala_t", count_sql="SELECT COUNT(*) FROM kala_t", target_floor="0")}
    _stub_layer(monkeypatch, tmp_path, reg, thru={"ka_d": {"": _rec(4)}})
    monkeypatch.setattr(ac, "psql", _pg_like_psql({"kala_t": 4}))
    c = ac.measure("L3")
    for aid in ("ka_svc", "ka_d"):
        cf = _m(c, aid, "Count.floor")
        assert cf is not None and cf["v"] == ac.NA and "no floor to breach" in cf["measured"], (aid, cf)


def test_r48_a_non_integer_floor_is_no_detector():
    r = _reg_row("ka_x", "kala_t", count_sql="SELECT COUNT(*) FROM kala_t", target_floor="12.5")
    cf = ac._grade_count_floor(r, 20, None, ["kala_t"])
    assert cf["v"] == ac.NO_DET and "12.5" in cf["measured"], cf


def test_r48_an_undeclared_floor_stays_absent(monkeypatch, tmp_path):
    reg = {"ka_x": _reg_row("ka_x", "kala_t", count_sql="", target_floor=None)}
    _stub_layer(monkeypatch, tmp_path, reg)
    assert _m(ac.measure("L3"), "ka_x", "Count.floor") is None


@LIVE
def test_live_r48_every_l3_asset_declaring_a_floor_gets_a_verdict():
    reg, _ = ac.registry("L3")
    counts, errored = ac.live_counts(reg, CANONICAL)
    declared = [a for a, r in reg.items() if r["target_floor"] is not None]
    assert len(declared) >= 19, declared
    for aid in declared:
        cf = ac._grade_count_floor(reg[aid], counts.get(aid), errored.get(aid), ac._count_tables(reg[aid]["count_sql"]))
        assert cf is not None and cf["v"] in (ac.PASS, ac.FAIL, ac.NA, ac.NO_DET, ac.ERRORED), (aid, cf)


# ─────────────────────────── C1 (W2-1_REVIEW §2 A8): a queued row is not an execution ───────────────────────────

REPO = HERE.parents[3]
PROD_LEDGER = REPO / "00_ARCHITECTURE" / "control" / "asset_gaps.jsonl"


def _history_psql(rows):
    """Answers build_history()'s own three reads: the attempts (7 columns, the last being
    `started_at IS NOT NULL`), the global-run counts, and the lit set."""
    def fake(sql, sep="\x1f", timeout=None):
        if "FROM build_run_assets a JOIN build_runs r" in sql:
            return [list(r) for r in rows]
        if sql.startswith("SELECT count(*)::text FROM build_runs"):
            return [["0"]]
        if "FROM asset_throughput WHERE state='lit'" in sql:
            return []
        raise AssertionError(f"unexpected query: {sql[:100]}")
    return fake


def _with_real_history(monkeypatch, rows):
    monkeypatch.setattr(ac, "build_history", _REAL["build_history"])
    fake = _history_psql(rows)
    monkeypatch.setattr(ac, "psql", fake)
    monkeypatch.setattr(ac, "scalar", lambda sql: (lambda r: r[0][0] if r and r[0] else None)(fake(sql)))


def test_c1_a_queued_only_asset_is_neither_exercised_nor_history_pass(monkeypatch, tmp_path):
    """(a) The REAL build_history() fed three never-started `queued` rows. Fails without the fix:
    Build.exercised read PASS "3 run(s)" and Build.history PASS "0 complete, no error or abort"."""
    reg = {"bg_x": _reg_row("bg_x", None, has_writer=True, asset_kind="service")}
    _stub_layer(monkeypatch, tmp_path, reg)
    _with_real_history(monkeypatch, [("bg_x", "layer", "queued", "", f"2026-09-2{i}", "", "f") for i in range(3)])
    c = ac.measure("L0")
    ex, hi = _m(c, "bg_x", "Build.exercised"), _m(c, "bg_x", "Build.history")
    assert ex["v"] == ac.FAIL and "none ever started" in ex["measured"], ex
    assert hi["v"] == ac.NO_DET and "0 complete" in hi["measured"], hi
    assert ex["v"] not in ac.CLOSABLE and hi["v"] not in ac.CLOSABLE


def test_c1_history_never_passes_with_zero_completions():
    h = dict(runs=2, error=0, aborted=0, complete=0, queued=2, skipped=0, blocked=0, last_state="queued",
             last_when="2026-09-27", last_disposition="", sample_error="", sample_blocked="")
    assert ac._grade_build_history(h)["v"] == ac.NO_DET


def test_c1_an_executed_row_still_exercises(monkeypatch, tmp_path):
    """Positive control: one started, completed row keeps Build.exercised PASS and history PASS; the
    queued leftover beside it is reported, not counted."""
    reg = {"bg_x": _reg_row("bg_x", None, has_writer=True, asset_kind="service")}
    _stub_layer(monkeypatch, tmp_path, reg)
    _with_real_history(monkeypatch, [("bg_x", "layer", "complete", "build", "2026-09-20", "", "t"),
                                     ("bg_x", "global", "queued", "", "2026-09-21", "", "f")])
    c = ac.measure("L0")
    ex = _m(c, "bg_x", "Build.exercised")
    assert ex["v"] == ac.PASS and "1 executed run(s) of 2" in ex["measured"], ex
    assert _m(c, "bg_x", "Build.history")["v"] == ac.PASS


@pytest.mark.skipif(not PROD_LEDGER.exists(), reason="production ledger not present in this checkout")
def test_c1_b_reviewer_reproduction_the_open_bg_sign_medical_gap_stays_open(monkeypatch, tmp_path):
    """(b) W2-1_REVIEW A8, exactly: a COPY of the production ledger (holding the OPEN
    bg_sign_medical-Build.exercised gap), the REAL build_history()/measure()/emit_gaps(), and one
    `queued` row for bg_sign_medical. Fails without the fix: emit_gaps CLOSED the gap on a row that
    never executed. The production ledger itself is never opened for writing."""
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    (ctrl / "asset_gaps.jsonl").write_bytes(PROD_LEDGER.read_bytes())
    gid = "bg_sign_medical-Build.exercised"
    latest = [json.loads(l) for l in (ctrl / "asset_gaps.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip() and json.loads(l).get("gap_id") == gid]
    assert latest and latest[-1]["state"] == "OPEN", "the reproduction needs the gap OPEN on the copy"
    reg = {"bg_sign_medical": _reg_row("bg_sign_medical", "bg_sign_medical", has_writer=True)}
    _stub_layer(monkeypatch, ctrl, reg)
    # The real capability scan over the real L0 directory — the stub's "scanned, no module" N/A would
    # close the (also OPEN) bg_sign_medical-Dens.served gap, an artefact of the harness, not of C1.
    monkeypatch.setattr(ac, "capability_scan", _REAL["capability_scan"])
    _with_real_history(monkeypatch, [("bg_sign_medical", "layer", "queued", "", "2026-09-28", "", "f")])
    c = ac.measure("L0")
    assert _m(c, "bg_sign_medical", "Build.exercised")["v"] == ac.FAIL
    assert _m(c, "bg_sign_medical", "Build.history")["v"] not in ac.CLOSABLE
    added, skipped, closed, reopened = ac.emit_gaps(c)
    assert closed == 0, "a never-executed queued row must not close the open Build.exercised gap"
    rows = [json.loads(l) for l in (ctrl / "asset_gaps.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert [r for r in rows if r.get("gap_id") == gid][-1]["state"] == "OPEN"


# ─────────────────────────── C4 (W2-1_C1_REVIEW §7): pin the executed marker to started_at ───────────────────────────

def _column_evaluating_psql(rows):
    """build_history()'s attempt read answered by EVALUATING whichever `(a.<col> IS NOT NULL)` the
    census's SQL asks for against row dicts that carry both `started_at` and `ended_at` — so a census
    that tests the wrong column (or a state list) gets the wrong answer, exactly as PostgreSQL would."""
    def fake(sql, sep="\x1f", timeout=None):
        if "FROM build_run_assets a JOIN build_runs r" in sql:
            m = re.search(r"\(a\.(\w+) IS NOT NULL\)", sql)
            assert m, "build_history() must select an IS NOT NULL execution marker"
            col = m.group(1)
            return [[r["asset_id"], "layer", r["state"], r.get("disposition", ""), "2026-09-28",
                     r.get("error", ""), "t" if r.get(col) is not None else "f"] for r in rows]
        if sql.startswith("SELECT count(*)::text FROM build_runs"):
            return [["0"]]
        if "FROM asset_throughput WHERE state='lit'" in sql:
            return []
        raise AssertionError(f"unexpected query: {sql[:100]}")
    return fake


_UNSTARTED = [
    dict(asset_id="bg_sign_medical", state="aborted", started_at=None, ended_at="2026-09-28T01:00",
         error="guardian_cleanup"),
    dict(asset_id="bg_sign_medical", state="error", started_at=None, ended_at="2026-09-28T02:00",
         error="BLOCKED: upstream dependency(ies) bg_x did not complete in this run; skipped"),
]


def _measure_with_rows(monkeypatch, ctrl, rows):
    reg = {"bg_sign_medical": _reg_row("bg_sign_medical", "bg_sign_medical", has_writer=True)}
    _stub_layer(monkeypatch, ctrl, reg)
    monkeypatch.setattr(ac, "capability_scan", _REAL["capability_scan"])
    monkeypatch.setattr(ac, "build_history", _REAL["build_history"])
    fake = _column_evaluating_psql(rows)
    monkeypatch.setattr(ac, "psql", fake)
    monkeypatch.setattr(ac, "scalar", lambda sql: (lambda r: r[0][0] if r and r[0] else None)(fake(sql)))
    return ac.measure("L0")


@pytest.mark.skipif(not PROD_LEDGER.exists(), reason="production ledger not present in this checkout")
def test_c4_a_unstarted_aborted_and_blocked_error_rows_do_not_exercise_or_close(monkeypatch, tmp_path):
    """(a) Only an `aborted` row (terminalised from queued) and a BLOCKED `error` row, both with
    started_at NULL. Fails under the state-list design ({complete, error, aborted} = executed —
    mutation C4-M2): Build.exercised reads PASS and the OPEN bg_sign_medical-Build.exercised gap on
    the ledger COPY closes."""
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    (ctrl / "asset_gaps.jsonl").write_bytes(PROD_LEDGER.read_bytes())
    c = _measure_with_rows(monkeypatch, ctrl, _UNSTARTED)
    ex = _m(c, "bg_sign_medical", "Build.exercised")
    assert ex["v"] == ac.FAIL and "none ever started" in ex["measured"], ex
    added, skipped, closed, reopened = ac.emit_gaps(c)
    assert closed == 0
    gid = "bg_sign_medical-Build.exercised"
    rows = [json.loads(l) for l in (ctrl / "asset_gaps.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert [r for r in rows if r.get("gap_id") == gid][-1]["state"] == "OPEN"


def test_c4_b_an_ended_but_never_started_row_is_not_executed(monkeypatch, tmp_path):
    """(b) A row with ended_at set and started_at NULL, beside one genuinely started row. Only the
    started row counts. Fails if build_history() reads ended_at (mutation C4-M5): both would count."""
    rows = [dict(asset_id="bg_sign_medical", state="aborted", started_at=None, ended_at="2026-09-28T01:00"),
            dict(asset_id="bg_sign_medical", state="complete", started_at="2026-09-27T01:00",
                 ended_at="2026-09-27T01:05", disposition="build")]
    monkeypatch.setattr(ac, "build_history", _REAL["build_history"])
    fake = _column_evaluating_psql(rows)
    monkeypatch.setattr(ac, "psql", fake)
    monkeypatch.setattr(ac, "scalar", lambda sql: (lambda r: r[0][0] if r and r[0] else None)(fake(sql)))
    h = ac.build_history("bg_", ["bg_sign_medical"])["per"]["bg_sign_medical"]
    assert h["runs"] == 2 and h["executed"] == 1, h


def _live_started_counts(layer, prefix):
    reg, _ = ac.registry(layer)
    hist = ac.build_history(prefix, sorted(reg))["per"]
    ids = ", ".join(f"'{a}'" for a in sorted(reg))
    direct = {r[0]: (int(r[1]), int(r[2])) for r in ac.psql(
        "SELECT a.asset_id, count(a.started_at)::text, count(a.ended_at)::text FROM build_run_assets a "
        f"JOIN build_runs r ON r.id = a.run_id WHERE a.asset_id IN ({ids}) GROUP BY 1")}
    return hist, direct


@LIVE
def test_live_c4_executed_equals_the_started_at_count():
    """Live, read-only: for every L4 asset, build_history()'s executed tally equals a direct count of
    build_run_assets rows with started_at set — over EVERY row (R233 made the read newline-safe; before
    it this test was restricted to the rows parsed intact) — and at least one asset has
    ended-but-unstarted rows, so reading ended_at or counting by state would disagree."""
    hist, direct = _live_started_counts("L4", "ph_")
    assert any(s != e for s, e in direct.values()), "need an asset whose ended and started counts differ"
    for aid, (started, _ended) in direct.items():
        assert hist[aid]["executed"] == started, (aid, hist[aid]["executed"], started)


@LIVE
def test_live_c4_executed_equals_the_started_at_count_over_all_rows():
    """R233 (W2-2; was a strict xfail documenting F-C4). Over EVERY row — multi-line tracebacks
    included — build_history()'s executed tally equals a direct started_at count, and no traceback
    fragment appears as a per-asset key. Fails without the fix: build_history() read
    left(a.error,200) raw, psql() split one row into several lines on the newlines, the started flag
    landed on a fragment (ph_sodhana 39 against 41 started, 2026-09-27) and fragments became keys."""
    reg, _ = ac.registry("L4")
    hist, direct = _live_started_counts("L4", "ph_")
    assert set(hist) <= set(reg), f"phantom per-asset keys: {sorted(set(hist) - set(reg))[:5]}"
    multi = int(ac.scalar("SELECT count(*)::text FROM build_run_assets WHERE asset_id LIKE 'ph\\_%' "
                          "AND error ~ E'[\\n\\r]'"))
    assert multi > 0, "the proof needs at least one multi-line error row in L4"
    for aid, (started, _ended) in direct.items():
        assert hist[aid]["executed"] == started, (aid, hist[aid]["executed"], started)
    assert hist["ph_sodhana"]["executed"] == direct["ph_sodhana"][0]
