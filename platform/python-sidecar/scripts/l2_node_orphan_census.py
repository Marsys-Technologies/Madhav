#!/usr/bin/env python3
"""
l2_node_orphan_census.py -- read-only orphan census for bo_karanajala's cross-asset node writes

Track I item TI-L2-17 (A.L2 brief ``bo_karanajala_ELEVATION_BRIEF_v1_0.md`` FD-1, cross-asset fix
CF-12 / CF-19; both on the A.L2 PRs #2831/#2841, which may not be merged).

Why it exists. ``bo_karanajala`` inserts ``arudha`` and ``special_lagna`` rows into
``bodha_cgm_nodes`` with ``ON CONFLICT (node_id) DO NOTHING``; ``replace_prior_cgm_nodes``
(``bodha_writers/_idempotency.py``) deletes only ``bhava``, ``domain``, ``dosha``, ``graha`` and
``yoga`` nodes. Nothing ever deletes an arudha/special_lagna node, so a node whose L1 fact has
since gone (or been renamed) stays. A passing Idem check on the delete says nothing about this
accretion. This census finds them.

What it does. For one chart (and each ayanamsha), it computes the node keys the builder WOULD
produce from L1 right now, by calling the writer's own ``_fetch_arudha_special_lagna_facts``
(never a re-implementation), and compares them with the live ``arudha`` / ``special_lagna`` nodes
in ``bodha_cgm_nodes``:

  * orphan  = live node whose key the builder would not produce  (stale; a prune candidate)
  * missing = key the builder would produce that has no live node (unbuilt; informational)

Exit status: 0 when there are no orphans, 1 when there are (a FAIL naming each), 2 on usage or
connection error. It only ever SELECTs, inside a transaction forced read-only. It does not prune:
a scoped prune is a writer change (FD-1) and a data change, held for the one L2 rebuild.

    DATABASE_URL=... python3 scripts/l2_node_orphan_census.py --chart-id <uuid> [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The node types bo_karanajala writes into a table another asset owns, and the only ones this
# census looks at (never the five types bo_bimba owns and deletes).
CROSS_ASSET_NODE_TYPES = ("arudha", "special_lagna")
SNAPSHOT_TYPE = "static_natal"  # bo_karanajala.SNAPSHOT_TYPE; asserted equal below when importable
CANONICAL_AYAS = (
    "lahiri_chitrapaksha", "raman", "krishnamurti", "surya_siddhanta_classical", "true_chitra",
)


def compare_node_keys(
    expected: set[tuple[str, str]], live: set[tuple[str, str]],
) -> dict[str, list[tuple[str, str]]]:
    """Pure comparison of (node_type, node_subject) sets. Both lists are sorted."""
    return {
        "orphans": sorted(live - expected),
        "missing": sorted(expected - live),
    }


def expected_node_keys(conn: Any, chart_id: str, ayanamsha_id: str) -> set[tuple[str, str]]:
    """Keys the builder would write now, via the writer's own L1 fact reader."""
    from pipeline.orchestrator.writers.bo_karanajala import _fetch_arudha_special_lagna_facts
    facts = _fetch_arudha_special_lagna_facts(conn, chart_id, ayanamsha_id)
    return {k for k in facts.keys() if k[0] in CROSS_ASSET_NODE_TYPES}


def live_node_keys(conn: Any, chart_id: str, ayanamsha_id: str) -> set[tuple[str, str]]:
    rows = conn.execute(
        """SELECT node_type, node_subject
             FROM bodha_cgm_nodes
            WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
              AND node_type = ANY(%s)""",
        [chart_id, ayanamsha_id, SNAPSHOT_TYPE, list(CROSS_ASSET_NODE_TYPES)],
    ).fetchall()
    out: set[tuple[str, str]] = set()
    for r in rows:
        out.add((r["node_type"], r["node_subject"]) if isinstance(r, dict) else (r[0], r[1]))
    return out


def run_census(
    conn: Any, chart_id: str, ayanamshas: tuple[str, ...] = CANONICAL_AYAS,
) -> dict[str, Any]:
    """Per-ayanamsha result plus totals. ``passed`` is False iff any orphan exists."""
    per_aya: dict[str, Any] = {}
    n_orphans = n_missing = n_live = n_expected = 0
    for aya in ayanamshas:
        exp = expected_node_keys(conn, chart_id, aya)
        live = live_node_keys(conn, chart_id, aya)
        cmp = compare_node_keys(exp, live)
        per_aya[aya] = {
            "expected": len(exp), "live": len(live),
            "orphans": [list(k) for k in cmp["orphans"]],
            "missing": [list(k) for k in cmp["missing"]],
        }
        n_orphans += len(cmp["orphans"])
        n_missing += len(cmp["missing"])
        n_live += len(live)
        n_expected += len(exp)
    return {
        "chart_id": chart_id,
        "node_types": list(CROSS_ASSET_NODE_TYPES),
        "ayanamshas": per_aya,
        "totals": {"expected": n_expected, "live": n_live, "orphans": n_orphans, "missing": n_missing},
        "passed": n_orphans == 0,
    }


def _connect_read_only(url: str):
    import psycopg
    import psycopg.rows
    return psycopg.connect(
        url, row_factory=psycopg.rows.dict_row,
        options="-c default_transaction_read_only=on -c statement_timeout=60000",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--chart-id", required=True)
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = ap.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set", file=sys.stderr)
        return 2
    try:
        conn = _connect_read_only(url)
    except Exception as exc:  # noqa: BLE001
        print(f"connection failed: {exc}", file=sys.stderr)
        return 2
    try:
        result = run_census(conn, args.chart_id, CANONICAL_AYAS)
    finally:
        conn.rollback()
        conn.close()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        t = result["totals"]
        print(f"chart {args.chart_id}: expected {t['expected']}, live {t['live']}, "
              f"orphans {t['orphans']}, missing {t['missing']} -> {'PASS' if result['passed'] else 'FAIL'}")
        for aya, r in result["ayanamshas"].items():
            for nt, ns in r["orphans"]:
                print(f"  ORPHAN {aya} {nt} {ns}")
            for nt, ns in r["missing"]:
                print(f"  missing {aya} {nt} {ns}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
