"""
pipeline.orchestrator.kala_derivation_completeness_guard
=========================================================

BA Full Asset Audit #6/#7: `ka_vighnakara` (kala_obstruction), `ka_kala_darshana`
(kala_darshana), and `ka_bhavishya_lekha` (kala_bhavishya) all read from
`kala_convergence` (ka_sangam's output) and correctly early-return 0 rows when
their own upstream slice is empty for a chart — that is legitimate, gated
behavior, not a bug.

The actual audit finding is different: for a chart where `kala_convergence` HAS
rows, a 0-row derived table is a genuine build gap (the derivation writer never
ran, or crashed silently, or its own upstream slice was unexpectedly empty in a
way worth surfacing) — not something to discover by chance later. This guard
makes that failure loud and immediate instead of silent.

`asset_registry.asset_throughput` is informational only (per §N.4 ratified build
principles — floors are aspirational, not gates) and can go stale relative to
live row counts; this guard also flags charts where the registry's last-recorded
throughput disagrees with a live count, as a drift warning (not a hard failure).

WHAT THIS GUARD MEASURES, EXACTLY (SAMĀPTI B-N8-SWEEPFIX, F-03 — read before
citing it). For each of the THREE hardcoded (upstream, derived) pairs below, it
compares two sets of chart_ids and reports charts present in the upstream table
and absent from the derived one. That is a **chart-presence** check: one row in the
derived table satisfies it. It does NOT measure row counts, expected counts, or
substep-plan completion, and it does NOT cover L3's other nine `ka_*` assets. The
emitted verdict states that bound verbatim — the module name is broader than what
it checks, and a CI log reader sees the verdict, not this docstring (CLAUDE.md
§N.8: a signal must not assert more than its detector measures).

HOW IT IS ACTUALLY INVOKED (F-02 — the previous docstring implied automation that
did not exist; `grep -rn kala_derivation_completeness .` found no workflow, script,
Makefile, hook or scheduler entry anywhere):
  * `--self-test`  — DB-free. Proves the detector by mutation: a clean fixture must
    come back clean AND a fixture with one seeded gap must be caught. Wired as a
    hard gate in `.github/workflows/ci.yml`. This gate proves the DETECTOR works;
    it says nothing about the live database.
  * live scan (`python -m pipeline.orchestrator.kala_derivation_completeness_guard`,
    exit 1 on any hard violation) — needs `DATABASE_URL` and per-chart kala_* rows.
    Wired into `.github/workflows/fresh_chart_smoke.yml` AFTER the fixture-chart
    build, which is the only automated context in this repo with both. Push/PR CI
    has no database, so the live scan does NOT run per-commit, and this guard makes
    no claim to catch live drift "the moment" it appears.
  * The verdict reports `charts_checked`. A run over zero upstream charts prints an
    explicit NO-COVERAGE line, never an unqualified OK — a scan of nothing is not a
    clean result.

Used by:          tests/test_kala_derivation_completeness_guard.py
"""
from __future__ import annotations

import argparse
import sys

# NOTE: `.db` (and its psycopg dependency) is imported lazily inside analyze() —
# NOT at module level. The `--self-test` path is a DB-free CI hard gate whose job
# (`governance-gates` in .github/workflows/ci.yml) installs only pyyaml + pytest;
# a module-level DB import would make that step die with ModuleNotFoundError at
# import time, before running a single check. Keep this import deferred.

# (upstream_table, derived_table, asset_id) — ka_kala_darshana and
# ka_bhavishya_lekha are chained (bhavishya_lekha depends on kala_darshana,
# which depends on kala_convergence), but each is checked directly against
# kala_convergence per the audit finding: "kala_convergence has rows but the
# derived table is empty" for that specific derived table.
DERIVATION_CHECKS = (
    ("kala_convergence", "kala_obstruction", "ka_vighnakara"),
    ("kala_convergence", "kala_darshana", "ka_kala_darshana"),
    ("kala_convergence", "kala_bhavishya", "ka_bhavishya_lekha"),
)


def evaluate(charts_by_table: dict[str, set[str]]) -> list[str]:
    """Pure core (no I/O): given {table: {chart_id, ...}} for every table named in
    DERIVATION_CHECKS, return hard violations — a chart with upstream rows but an
    empty derived table for that specific derivation."""
    hard: list[str] = []
    for upstream_table, derived_table, asset_id in DERIVATION_CHECKS:
        upstream_charts = charts_by_table.get(upstream_table, set())
        derived_charts = charts_by_table.get(derived_table, set())
        missing = upstream_charts - derived_charts
        for chart_id in sorted(missing):
            hard.append(
                f"{asset_id}: chart {chart_id} has {upstream_table} rows but "
                f"{derived_table} is empty — derivation gap, not a legitimate "
                f"upstream-empty early-return"
            )
    return sorted(set(hard))


def evaluate_throughput_drift(throughput_and_live: dict[str, tuple[int | None, int]]) -> list[str]:
    """Pure core: given {asset_id: (registry_asset_throughput_or_None, live_count)},
    return informational drift warnings (§N.4 — never a hard failure)."""
    drift: list[str] = []
    for asset_id, (registered, live_count) in throughput_and_live.items():
        if registered is None:
            continue
        if int(registered) != int(live_count):
            derived_table = next(d for _u, d, a in DERIVATION_CHECKS if a == asset_id)
            drift.append(
                f"{asset_id}: asset_registry.asset_throughput={registered} "
                f"but live {derived_table} count={live_count}"
            )
    return sorted(set(drift))


def _charts_with_rows(conn, table: str) -> set[str]:
    rows = conn.execute(f"SELECT DISTINCT chart_id FROM {table}").fetchall()
    return {str(r["chart_id"]) for r in rows}


def analyze() -> dict:
    """I/O shell: pull live data, delegate to the pure evaluate()/evaluate_throughput_drift()."""
    from .db import connect  # deferred: keeps --self-test free of the psycopg dependency

    with connect() as conn:
        tables = sorted({t for u, d, _a in DERIVATION_CHECKS for t in (u, d)})
        charts_by_table = {t: _charts_with_rows(conn, t) for t in tables}

        throughput_and_live: dict[str, tuple[int | None, int]] = {}
        for _upstream_table, derived_table, asset_id in DERIVATION_CHECKS:
            reg_row = conn.execute(
                "SELECT asset_throughput FROM asset_registry WHERE asset_id = %s",
                [asset_id],
            ).fetchone()
            registered = reg_row["asset_throughput"] if reg_row else None
            live_row = conn.execute(f"SELECT count(*) AS n FROM {derived_table}").fetchone()
            live_count = live_row["n"] if live_row else 0
            throughput_and_live[asset_id] = (registered, live_count)

    # F-03: report the COVERAGE the verdict is entitled to claim. Without this a
    # scan over an empty database prints the same OK as a scan over the fleet.
    upstream_charts = set()
    for upstream_table, _d, _a in DERIVATION_CHECKS:
        upstream_charts |= charts_by_table.get(upstream_table, set())

    return {
        "hard": evaluate(charts_by_table),
        "throughput_drift": evaluate_throughput_drift(throughput_and_live),
        "charts_checked": len(upstream_charts),
        "derivations_checked": len(DERIVATION_CHECKS),
    }


# ── DB-free self-test (the CI hard gate) ──────────────────────────────────────

def run_self_test() -> int:
    """Prove the detector by mutation, with no database.

    Exits 0 iff BOTH hold:
      (a) a fixture where every upstream chart has a derived row comes back CLEAN;
      (b) a fixture with ONE seeded gap is CAUGHT, naming the right asset and chart.
    (b) is the half that matters: without it a detector that always returns [] —
    the failure mode this guard is being audited for — would still pass (a).

    Honest bound: this proves `evaluate()`'s logic. It does NOT prove anything
    about the live DAG or the live database; that is the `analyze()` path, which
    needs DATABASE_URL. See the module docstring.
    """
    clean = {
        "kala_convergence": {"chart-a", "chart-b"},
        "kala_obstruction": {"chart-a", "chart-b"},
        "kala_darshana": {"chart-a", "chart-b"},
        "kala_bhavishya": {"chart-a", "chart-b"},
    }
    res_clean = evaluate(clean)
    ok_clean = res_clean == []

    seeded = {**clean, "kala_obstruction": {"chart-a"}}  # chart-b's derivation missing
    res_seeded = evaluate(seeded)
    ok_seeded = any("ka_vighnakara" in h and "chart-b" in h for h in res_seeded)

    print(f"[kala_derivation_completeness_guard --self-test] clean fixture -> "
          f"{len(res_clean)} violation(s) (expected 0): {'PASS' if ok_clean else 'FAIL'}")
    print(f"[kala_derivation_completeness_guard --self-test] seeded-gap fixture -> "
          f"{len(res_seeded)} violation(s) (expected >=1 naming ka_vighnakara/chart-b): "
          f"{'PASS' if ok_seeded else 'FAIL'}")
    if ok_clean and ok_seeded:
        print("[kala_derivation_completeness_guard --self-test] OK — the detector "
              "both stays quiet on clean input and fires on a seeded gap")
        return 0
    print("[kala_derivation_completeness_guard --self-test] FAILED — the detector "
          "does not discriminate; it cannot be relied on as a gate")
    return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="Run the DB-free fixture mutation self-test (the CI hard gate).")
    args = ap.parse_args(argv)
    if args.self_test:
        return run_self_test()

    res = analyze()
    if res["throughput_drift"]:
        print(f"[kala_derivation_completeness_guard] {len(res['throughput_drift'])} "
              f"asset_throughput drift warning(s) (informational, §N.4):")
        for d in res["throughput_drift"]:
            print(f"  ~ {d}")
    if res["hard"]:
        print(f"[kala_derivation_completeness_guard] {len(res['hard'])} derivation-gap "
              f"violation(s):")
        for h in res["hard"]:
            print(f"  ✗ {h}")
        return 1

    # F-03: the verdict states exactly what was measured and over how much.
    # It never reads as an unqualified "the Kāla derivations are complete".
    if res["charts_checked"] == 0:
        print("[kala_derivation_completeness_guard] NO COVERAGE — 0 charts have rows "
              "in any upstream table, so nothing was checked. This is NOT a pass.")
        return 0
    print(f"[kala_derivation_completeness_guard] OK — no empty-derived-table gaps "
          f"for the {res['derivations_checked']} checked derivations "
          f"({', '.join(d for _u, d, _a in DERIVATION_CHECKS)}) "
          f"across {res['charts_checked']} chart(s). "
          f"Scope: chart PRESENCE in the derived table only — not row counts, not "
          f"expected counts, not substep-plan completion, and not L3's other assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
