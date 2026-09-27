"""test_a3_fault_isolation_and_population.py — R41 (per-check fault isolation) and R220 (active
population scoping) for the Nikaṣa wave-1 census port.

R41: one check raising (timeout, missing relation) must degrade THAT check's verdict to ERRORED
for that asset — never abort the whole layer census. Tested end-to-end through `measure()` with a
monkeypatched `psql`/`scalar` that raises `Unknown` for exactly one query shape, proving the other
per-asset criteria still get measured (this is the case that fails today without the fix: before
R41, any raised `Unknown` from inside the per-asset loop propagates out of `measure()` uncaught).

R220: `asset_registry` for a layer has more rows than the ACTIVE population the census should
measure (129 total vs 127 active registry-wide, 2 retired L3 rows — measured 2026-09-27). The
register's own phrasing `is_active AND NOT dead_flag` returns ZERO rows when `dead_flag` is NULL
(NULL propagation, not false) rather than 127 — the exact trap this test guards against.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py -v
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import asset_census as ac  # noqa: E402


# ── R41: per-check fault isolation ──

def test_contract_scan_exception_degrades_to_errored_not_layer_abort(monkeypatch):
    """F3 (A_REVIEW.md): the previous version of this test asserted that the monkeypatch itself
    raises, then grepped measure()'s SOURCE TEXT for the guard — a mutation that makes the guard
    RE-RAISE instead of catching (M8 in the gate review's mutation table) survives that check,
    because the source text is unchanged; only the behaviour breaks. `_measure_contract` was
    extracted from measure()'s inline try/except specifically so this test can call it directly
    and assert on the RETURN VALUE, which a re-raising guard cannot produce (it raises instead of
    returning at all — caught below as a test failure, not silently passed)."""
    def _boom(asset_id, files):
        raise ac.Unknown("bg_broken.py: unparseable (SyntaxError)")
    monkeypatch.setattr(ac, "contract_scan", _boom)
    result = ac._measure_contract("bg_broken", ["bg_broken.py"])
    assert result["v"] == ac.ERRORED, f"expected ERRORED, got {result}"
    assert "unparseable" in result["measured"]


def test_idem_scan_exception_degrades_to_errored_not_layer_abort(monkeypatch):
    """Same proof as above, for `_measure_idem` / Idem.pattern."""
    def _boom(asset_id, files, convention):
        raise ac.Unknown("bg_broken.py: unparseable (SyntaxError)")
    monkeypatch.setattr(ac, "idem_scan", _boom)
    result = ac._measure_idem("bg_broken", ["bg_broken.py"], "upsert")
    assert result["v"] == ac.ERRORED, f"expected ERRORED, got {result}"


def test_measure_calls_the_extracted_guarded_helpers(monkeypatch):
    """Locks in that measure() actually calls `_measure_contract`/`_measure_idem` (rather than a
    re-inlined, ungrappable try/except) so a future edit that reverts the extraction is caught
    here rather than silently reintroducing the untestable shape F3 fixes."""
    import inspect
    src = inspect.getsource(ac.measure)
    assert 'm["Build.contract"] = _measure_contract(aid, files)' in src
    assert 'm["Idem.pattern"] = _measure_idem(aid, files, cfg["idem"])' in src


def test_errored_never_closes_a_gap_and_never_opens_one(tmp_path, monkeypatch):
    """ERRORED must behave like NOT_GENERIC in emit_gaps — in neither FAILING nor CLOSABLE, so a
    check that errors out neither opens nor closes a gap; the ledger keeps whatever it last knew."""
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    assert ac.ERRORED not in ac.FAILING
    assert ac.ERRORED not in ac.CLOSABLE
    census = dict(layer="L0", assets=[dict(asset_id="bg_x",
                                           measurements={"Foo.bar": dict(v=ac.ERRORED, measured="check errored: timeout")})])
    added, skipped, closed, reopened = ac.emit_gaps(census)
    assert (added, skipped, closed, reopened) == (0, 0, 0, 0)
    ledger = tmp_path / "asset_gaps.jsonl"
    assert not ledger.exists() or ledger.read_text() == ""


def _db_reachable() -> bool:
    try:
        ac.scalar("SELECT 1")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _db_reachable(), reason="no live DB in this environment (PGHOST/PGPORT/etc.)")
def test_live_e2e_one_simulated_query_timeout_degrades_not_aborts(monkeypatch):
    """The strongest form of this proof: run the REAL `measure('L1')` against a REAL (read-only)
    database with exactly one query shape (the Vocab.identity duplicate probe) monkeypatched to
    raise `Unknown`, simulating a live statement-timeout. Confirms live, 2026-09-27 against
    production: the fixed census measures all 19 L1 assets with the affected criterion degraded
    to ERRORED, while the SAME monkeypatch against the pre-A3 code (no per-check guard) aborts
    `measure()` outright — reproduced here against `_naive_measure_has_no_guard` below, a
    transcription of the pre-fix call site, so the failing-without-the-fix half of this proof
    does not depend on git history being available in whatever environment runs this suite.

    Note (post-F2 fix, discovered running this test live): L1's own `count_sql` values are
    chart-scoped (`WHERE chart_id = $1`, a real parameter placeholder — confirmed live against
    every L1 asset's registered `count_sql`), which `live_counts()` cannot bind when run
    standalone, so EVERY L1 asset's `Build.completion` also (and correctly, per F2) grades
    ERRORED here, independent of the simulated Vocab.identity fault. That is F2 doing its job —
    a real, pre-existing masked defect (count_sql that cannot run this way was previously
    silently reported as N/A "no count_sql"), not a regression this test should paper over. This
    test's actual claim is narrower: the SIMULATED fault must degrade only Vocab.identity, and
    must never blind Build.registered (or anything else) for the SAME asset."""
    real_psql = ac.psql

    def flaky_psql(sql, sep="\x1f", timeout=None):
        if "GROUP BY" in sql and "HAVING count(*) > 1" in sql:
            raise ac.Unknown("SIMULATED: statement timeout")
        return real_psql(sql, sep, timeout)

    monkeypatch.setattr(ac, "psql", flaky_psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: (lambda r: r[0][0] if r and r[0] else None)(flaky_psql(sql)))

    c = ac.measure("L1")
    errored = [(a["asset_id"], k) for a in c["assets"] for k, v in a["measurements"].items() if v["v"] == ac.ERRORED]
    assert c["n_assets"] > 0, "the layer must still be fully measured, not aborted"
    identity_errored = [(aid, k) for aid, k in errored if k == "Vocab.identity"]
    assert identity_errored, "at least one asset must show the simulated failure as ERRORED, not silently PASS"
    # Every OTHER criterion that degrades here must be independently explained (F2's own
    # Build.completion finding, confirmed above) — the simulated fault itself must degrade only
    # Vocab.identity, never spill into an unrelated criterion for the same asset.
    unexplained = [(aid, k) for aid, k in errored if k not in ("Vocab.identity", "Build.completion")]
    assert not unexplained, f"the simulated fault spilled into an unrelated criterion: {unexplained}"
    # Every asset that errored on Vocab.identity must still have OTHER criteria measured normally.
    errored_ids = {aid for aid, _ in identity_errored}
    for a in c["assets"]:
        if a["asset_id"] in errored_ids:
            others = {k: v["v"] for k, v in a["measurements"].items() if k != "Vocab.identity"}
            assert others.get("Build.registered") in (ac.PASS, ac.FAIL, ac.NA), (
                f"{a['asset_id']}: Build.registered was not measured — the failure blinded more than "
                "its own criterion"
            )


def test_depth_census_timeout_does_not_block_vocab_or_ldgr_checks_from_running():
    """Weaker structural backstop only (kept as a fast, DB-free smoke check) — the actual
    behavioural proof is `test_live_e2e_depth_census_failure_does_not_blind_identity_for_the_same_
    asset` below, run against a real database."""
    import inspect
    src = inspect.getsource(ac.measure)
    assert src.count("except Unknown as exc:") >= 4  # depth, identity, alias, ldgr (contract/idem now extracted)


@pytest.mark.skipif(not _db_reachable(), reason="no live DB in this environment (PGHOST/PGPORT/etc.)")
def test_live_e2e_depth_census_failure_does_not_blind_identity_for_the_same_asset(monkeypatch):
    """F3 (A_REVIEW.md): the previous version of this test only counted `except Unknown as exc:`
    occurrences in measure()'s source text — a mutation that merges the four independent
    try/except blocks into one (so a depth_census failure swallows identity/alias/ldgr for the
    SAME asset too) does not change that count and survives. This runs measure('L0') for REAL
    twice: once clean (baseline), once with `depth_census` monkeypatched to raise for exactly one
    asset's target table. That asset's Complete.depth must degrade to ERRORED while its
    Vocab.identity verdict is UNCHANGED from the baseline — proving the failure did not blind the
    sibling check for the same asset, which a merged-guard mutation would."""
    baseline = ac.measure("L0")
    candidate = next(
        (a for a in baseline["assets"]
         if a["measurements"].get("Vocab.identity", {}).get("v") in (ac.PASS, ac.FAIL)
         and a["target_table"]),
        None,
    )
    assert candidate is not None, "need at least one L0 asset with a measured Vocab.identity to run this proof"
    target_table = candidate["target_table"]
    baseline_identity = candidate["measurements"]["Vocab.identity"]

    real_depth_census = ac.depth_census

    def flaky_depth_census(table, cols):
        if table == target_table:
            raise ac.Unknown("SIMULATED: depth_census timeout")
        return real_depth_census(table, cols)

    monkeypatch.setattr(ac, "depth_census", flaky_depth_census)
    c = ac.measure("L0")
    patched = next(a for a in c["assets"] if a["asset_id"] == candidate["asset_id"])
    assert patched["measurements"]["Complete.depth"]["v"] == ac.ERRORED
    assert patched["measurements"]["Vocab.identity"] == baseline_identity, (
        "the simulated depth_census failure must not change (let alone blind) the SAME asset's "
        "Vocab.identity result"
    )


# ── F2 (A_REVIEW.md): an errored count_sql must never be read as "no count_sql" ──

def test_live_counts_distinguishes_errored_query_from_no_count_sql(monkeypatch):
    """A failing count_sql must be reported in a distinct `errored` map, never collapsed into the
    same `None` a genuinely-absent count_sql produces. Pre-fix, `live_counts` returned a single
    dict, and both cases mapped to `out[aid] = None` — measure() then wrote
    `Build.completion = N/A "no count_sql"` for a query that in fact raised, and N/A is CLOSABLE
    (a live demonstration on bg_ephemeris closed the gap on exactly this path, per A_REVIEW.md F2).
    This test fails today (before the fix) because `live_counts` returns one value, not a
    (counts, errored) pair — unpacking it as a 2-tuple raises."""
    reg = {
        "bg_ok": dict(count_sql="SELECT 1"),
        "bg_no_count_sql": dict(count_sql=""),
        "bg_broken": dict(count_sql="SELECT boom_this_relation_does_not_exist"),
    }

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "UNION ALL" in sql:
            raise ac.Unknown("SIMULATED: batch query failed")
        if "boom_this_relation_does_not_exist" in sql:
            raise ac.Unknown("SIMULATED: relation \"boom_this_relation_does_not_exist\" does not exist")
        return [["1"]]

    monkeypatch.setattr(ac, "psql", fake_psql)
    counts, errored = ac.live_counts(reg)
    assert counts["bg_no_count_sql"] is None
    assert "bg_no_count_sql" not in errored, "a genuinely-absent count_sql must never appear in errored"
    assert counts["bg_broken"] is None
    assert "bg_broken" in errored and "does not exist" in errored["bg_broken"]
    assert counts["bg_ok"] == 1
    assert "bg_ok" not in errored


def _db_reachable_f2() -> bool:
    try:
        ac.scalar("SELECT 1")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _db_reachable_f2(), reason="no live DB in this environment (PGHOST/PGPORT/etc.)")
def test_live_e2e_a_broken_count_sql_grades_errored_not_na(monkeypatch):
    """Live reproduction of A_REVIEW.md F2's bg_ephemeris demonstration, via monkeypatch rather
    than depending on production having a broken count_sql at run time: force one asset's
    live_counts entry into the errored path and confirm Build.completion grades ERRORED, never
    the closable N/A."""
    real_live_counts = ac.live_counts
    picked: dict[str, str] = {}

    def broken(reg):
        counts, errored = real_live_counts(reg)
        target = next(iter(reg), None)
        if target is not None:
            counts[target] = None
            errored[target] = "SIMULATED: count_sql query failed (F2 reproduction)"
            picked["id"] = target
        return counts, errored

    monkeypatch.setattr(ac, "live_counts", broken)
    c = ac.measure("L0")
    assert "id" in picked, "live_counts was never called — the layer must have at least one asset"
    target = next(a for a in c["assets"] if a["asset_id"] == picked["id"])
    assert target["measurements"]["Build.completion"]["v"] == ac.ERRORED
    assert target["measurements"]["Build.completion"]["v"] not in ac.CLOSABLE


# ── R220: active population scoping ──

def test_population_filter_null_trap_illustration():
    """Illustrative only (kept for the reasoning, not as the proof): the register's literal
    phrasing `is_active AND NOT dead_flag` is a NULL trap — with `dead_flag` NULL (not false) on
    every row, SQL's `NOT NULL` is NULL and `is_active AND NULL` is NULL, so a naive
    implementation of that exact expression matches ZERO rows, not the true active population.
    This does NOT call `asset_census.registry()` — see `test_live_registry_l3_excludes_the_two_
    retired_rows` below for the actual behavioural proof against real production data (F3,
    A_REVIEW.md: this hand-built-helper form is exactly what the gate review flagged as unable to
    fail — reverting registry()'s real filter does not touch these local functions at all)."""
    rows = [
        dict(asset_id="x1", is_active=True, dead_flag=None),
        dict(asset_id="x2", is_active=True, dead_flag=None),
        dict(asset_id="x3", is_active=False, dead_flag=None),   # retired, should be excluded
        dict(asset_id="x4", is_active=True, dead_flag=True),    # explicitly dead, should be excluded
    ]

    def naive_filter(r):
        if r["dead_flag"] is None:
            return None  # NULL propagates — this row matches neither True nor False in SQL
        return r["is_active"] and not r["dead_flag"]

    def fixed_filter(r):
        return r["is_active"] and not (r["dead_flag"] if r["dead_flag"] is not None else False)

    naive_matches = [r for r in rows if naive_filter(r) is True]
    fixed_matches = [r for r in rows if fixed_filter(r)]
    assert len(naive_matches) == 0, "the naive NULL-unsafe phrasing matches nothing — the bug R220 names"
    assert [r["asset_id"] for r in fixed_matches] == ["x1", "x2"]


@pytest.mark.skipif(not _db_reachable_f2(), reason="no live DB in this environment (PGHOST/PGPORT/etc.)")
def test_live_registry_l3_excludes_the_two_retired_rows():
    """F3/M9 (A_REVIEW.md): the actual behavioural proof, against the REAL `registry()` and REAL
    production data — 23 L3 registry rows total, 21 active (2 retired; `dead_flag` is NULL, not
    false, on every one of the 129 account-wide rows, confirmed 2026-09-27). Reverting
    `registry()`'s SQL from `is_active AND NOT coalesce(dead_flag,false)` back to the register's
    literal `is_active AND NOT dead_flag` wording (mutation M9) makes real PostgreSQL apply NULL
    propagation and return ZERO active rows for every layer, not 21 — this test would then fail
    on `population["active"] == 21`, unlike the illustrative helper-function test above, which
    would keep passing unchanged because it never calls `registry()` at all."""
    reg, population = ac.registry("L3")
    assert population["registry_total"] == 23, population
    assert population["active"] == 21, (
        f"expected 21 active of 23 registry rows; got {population['active']} — if this reads 0, "
        "the NULL-trap filter has regressed to the register's literal (unsafe) wording"
    )
    assert len(reg) == 21
    excluded_ids = {x["asset_id"] for x in population["excluded_inactive"]}
    assert excluded_ids == {"ka_gochara_sweep", "ka_gochara_v3_century_materialize"}, excluded_ids


def test_registry_returns_population_tuple_shape():
    """`registry()` must return (rows, population) — a caller that unpacks a bare dict (the
    pre-R220 shape) would raise, which is exactly how this change was applied."""
    import inspect
    sig = inspect.signature(ac.registry)
    src = inspect.getsource(ac.registry)
    assert "return out, population" in src
    assert "registry_total" in src and "excluded_inactive" in src


def test_measure_states_the_population_never_silently_drops_it():
    import inspect
    src = inspect.getsource(ac.measure)
    assert "population_active" in src and "population_registry_total" in src and "population_excluded_inactive" in src
