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

Run as a script:  python -m pipeline.orchestrator.kala_derivation_completeness_guard
                   (exit 1 on any hard completeness violation)
Used by:          tests/test_kala_derivation_completeness_guard.py
"""
from __future__ import annotations

import sys

from .db import connect

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

    return {
        "hard": evaluate(charts_by_table),
        "throughput_drift": evaluate_throughput_drift(throughput_and_live),
    }


def main() -> int:
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
    print("[kala_derivation_completeness_guard] OK — no derivation-completeness gaps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
