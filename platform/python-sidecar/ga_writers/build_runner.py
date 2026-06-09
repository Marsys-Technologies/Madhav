"""
build_runner.py — GA3–GA9 build orchestrator
=============================================
Runs the full L1 Gaṇita build for chart_id = 482012f1-710e-4a25-994a-93821f5871aa:
  1. ga_positions  → ganita_positions + chart_facts
  2. ga_strength   → chart_facts (shadbala + ashtakavarga + bhava_bala)
  3. Refresh GA3 materialized views (synchronous)
  4. Run all gate-validators
  5. ga_sade_sati  → chart_facts (~875 rows, 15 categories; GA9 — final step)
     Requires GA3/GA4/GA6/GA7/GA8 rows present (Step 0 upstream verification).
  6. Emit FINAL_SUMMARY dict

Usage:
    python -m ga_writers.build_runner [--chart_id UUID] [--build_id UUID]
    # or import and call: build_runner.run(chart_id, build_id)

Environment:
    DATABASE_URL (or DIRECT_DATABASE_URL / POSTGRES_URL) — Postgres connection string.
    SWISSEPH_EPHE_PATH — path to Swiss Ephemeris data files (default: /usr/share/ephe).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

# Configure logging before imports that use it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from ga_writers.ga_positions_writer import build_ga_positions, CANONICAL_CHART_ID, _conn
from ga_writers.ga_strength_writer import build_ga_strength
from ga_writers.ga_sade_sati_writer import build_ga_sade_sati
from ga_writers.gates import run_all_gates


# ── MV refresh ───────────────────────────────────────────────────────────────

MATERIALIZED_VIEWS = [
    "mv_chart_planet_summary",
    "mv_chart_shadbala_summary",
    "mv_chart_ashtakavarga_summary",
    "mv_chart_bhava_bala_summary",
    "mv_cross_ayanamsha_consensus",
]


def refresh_materialized_views(conn: Any) -> dict[str, str]:
    """
    Refresh all GA3 MVs synchronously.
    Returns {mv_name: 'OK'|'SKIP'|'ERROR'}.
    Per A3 §10: build_state does not flip to 'complete' until MVs refresh.
    """
    results = {}
    for mv in MATERIALIZED_VIEWS:
        try:
            conn.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv}")
            results[mv] = "OK"
            logger.info("[build_runner] MV refreshed: %s", mv)
        except Exception as exc:
            # Non-concurrent refresh as fallback (may lock briefly)
            try:
                conn.execute(f"REFRESH MATERIALIZED VIEW {mv}")
                results[mv] = "OK"
                logger.info("[build_runner] MV refreshed (non-concurrent): %s", mv)
            except Exception as exc2:
                results[mv] = f"ERROR: {exc2}"
                logger.warning("[build_runner] MV refresh failed %s: %s", mv, exc2)
    conn.commit()
    return results


# ── Full build ────────────────────────────────────────────────────────────────

def run(
    chart_id: str = CANONICAL_CHART_ID,
    build_id: str | None = None,
    *,
    birth_params: dict[str, Any] | None = None,
    skip_strength: bool = False,
    skip_sade_sati: bool = False,
) -> dict[str, Any]:
    """
    Run full GA3 build: positions + strength + MVs + gates.
    Returns comprehensive summary dict.
    Raises on FORENSIC gate failure or two-pass divergence.
    """
    if build_id is None:
        build_id = str(uuid.uuid4())

    started_at = datetime.now(timezone.utc).isoformat()
    logger.info(
        "[build_runner] GA3 build starting: chart_id=%s build_id=%s",
        chart_id, build_id,
    )

    summary: dict[str, Any] = {
        "session_id": "ga3-chart-facts",
        "chart_id": chart_id,
        "build_id": build_id,
        "started_at": started_at,
        "steps": {},
        "gate_results": {},
        "status": "IN_PROGRESS",
    }

    # ── Step 1: ga_positions ─────────────────────────────────────────────────
    logger.info("[build_runner] Step 1: ga_positions")
    try:
        pos_summary = build_ga_positions(
            chart_id=chart_id,
            build_id=build_id,
            birth_params=birth_params,
        )
        summary["steps"]["ga_positions"] = {
            "status": "PASS",
            "ganita_positions_rows": pos_summary["total_ganita_positions_rows"],
            "chart_facts_rows": pos_summary["total_chart_facts_rows"],
            "forensic_pass": pos_summary["forensic_pass"],
        }
        logger.info(
            "[build_runner] ga_positions PASS: gp=%d cf=%d",
            pos_summary["total_ganita_positions_rows"],
            pos_summary["total_chart_facts_rows"],
        )
    except Exception as exc:
        summary["steps"]["ga_positions"] = {"status": "FAIL", "error": str(exc)}
        summary["status"] = "FAIL"
        logger.error("[build_runner] ga_positions FAIL: %s", exc)
        return summary  # Halt — GA3 is load-bearing

    # ── Step 2: ga_strength ──────────────────────────────────────────────────
    if not skip_strength:
        logger.info("[build_runner] Step 2: ga_strength")
        try:
            str_summary = build_ga_strength(
                chart_id=chart_id,
                build_id=build_id,
                birth_params=birth_params,
            )
            summary["steps"]["ga_strength"] = {
                "status": "PASS",
                "chart_facts_rows": str_summary["total_chart_facts_rows"],
                "forensic_pass": str_summary["forensic_pass"],
                "two_pass_verified": str_summary["two_pass_verified"],
            }
            logger.info(
                "[build_runner] ga_strength PASS: cf=%d two_pass=%s",
                str_summary["total_chart_facts_rows"],
                str_summary["two_pass_verified"],
            )
        except Exception as exc:
            summary["steps"]["ga_strength"] = {"status": "FAIL", "error": str(exc)}
            summary["status"] = "FAIL"
            logger.error("[build_runner] ga_strength FAIL: %s", exc)
            return summary

    # ── Step 3: Refresh MVs ───────────────────────────────────────────────────
    logger.info("[build_runner] Step 3: Refresh materialized views")
    try:
        with _conn() as conn:
            mv_results = refresh_materialized_views(conn)
        failed_mvs = [k for k, v in mv_results.items() if "ERROR" in str(v)]
        summary["steps"]["mv_refresh"] = {
            "status": "FAIL" if failed_mvs else "PASS",
            "results": mv_results,
            "failed": failed_mvs,
        }
        if failed_mvs:
            logger.warning("[build_runner] Some MVs failed: %s", failed_mvs)
        else:
            logger.info("[build_runner] All MVs refreshed OK")
    except Exception as exc:
        summary["steps"]["mv_refresh"] = {"status": "FAIL", "error": str(exc)}
        logger.warning("[build_runner] MV refresh failed (non-fatal): %s", exc)

    # ── Step 4: Run all gates ─────────────────────────────────────────────────
    logger.info("[build_runner] Step 4: Gate validation")
    try:
        with _conn() as conn:
            gate_results = run_all_gates(conn, chart_id, build_id)
        summary["gate_results"] = gate_results
        overall = gate_results.get("overall", "FAIL")
        if overall == "FAIL":
            logger.warning("[build_runner] Gate validation FAIL")
        else:
            logger.info("[build_runner] All gates PASS")
    except Exception as exc:
        summary["gate_results"] = {"overall": "FAIL", "error": str(exc)}
        logger.error("[build_runner] Gate validation exception: %s", exc)

    # ── Step 5: GA9 — ga_sade_sati (final step; requires all upstreams) ───────
    if not skip_sade_sati:
        logger.info("[build_runner] Step 5: ga_sade_sati (GA9 — Sade Sati cycles)")
        try:
            ss_summary = build_ga_sade_sati(
                chart_id=chart_id,
                build_id=build_id,
                birth_params=birth_params,
            )
            summary["steps"]["ga_sade_sati"] = {
                "status": "PASS",
                "chart_facts_rows": ss_summary["total_chart_facts_rows"],
                "two_pass_verified": ss_summary["two_pass_verified"],
                "divergent_flagged": ss_summary["divergent_flagged"],
                "ayanamshas": ss_summary.get("ayanamshas", {}),
            }
            logger.info(
                "[build_runner] ga_sade_sati PASS: cf=%d two_pass=%s",
                ss_summary["total_chart_facts_rows"],
                ss_summary["two_pass_verified"],
            )
        except Exception as exc:
            summary["steps"]["ga_sade_sati"] = {"status": "FAIL", "error": str(exc)}
            summary["status"] = "FAIL"
            logger.error("[build_runner] ga_sade_sati FAIL: %s", exc)
            return summary

    # ── Compute totals ────────────────────────────────────────────────────────
    pos_step = summary["steps"].get("ga_positions", {})
    str_step = summary["steps"].get("ga_strength", {})
    total_gp = pos_step.get("ganita_positions_rows", 0)
    total_cf = (
        pos_step.get("chart_facts_rows", 0)
        + str_step.get("chart_facts_rows", 0)
    )

    ss_step = summary["steps"].get("ga_sade_sati", {})
    total_cf += ss_step.get("chart_facts_rows", 0)

    summary["totals"] = {
        "ganita_positions_rows": total_gp,
        "chart_facts_rows": total_cf,
    }

    gate_overall = summary.get("gate_results", {}).get("overall", "FAIL")
    all_steps_pass = all(
        s.get("status") == "PASS"
        for s in summary["steps"].values()
        if isinstance(s, dict)
    )
    summary["status"] = "PASS" if (all_steps_pass and gate_overall == "PASS") else "FAIL"
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()

    return summary


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GA3 chart_facts build runner")
    parser.add_argument(
        "--chart_id",
        default=CANONICAL_CHART_ID,
        help=f"Chart UUID (default: canonical native {CANONICAL_CHART_ID})",
    )
    parser.add_argument(
        "--build_id",
        default=None,
        help="Build UUID (auto-generated if not supplied)",
    )
    parser.add_argument(
        "--skip_strength",
        action="store_true",
        help="Skip ga_strength writer (positions only)",
    )
    parser.add_argument(
        "--skip_sade_sati",
        action="store_true",
        help="Skip ga_sade_sati writer (GA9 — Sade Sati cycles)",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output full summary as JSON to stdout",
    )
    args = parser.parse_args()

    result = run(
        chart_id=args.chart_id,
        build_id=args.build_id,
        skip_strength=args.skip_strength,
        skip_sade_sati=args.skip_sade_sati,
    )

    if args.output_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = result.get("status", "UNKNOWN")
        gp_rows = result.get("totals", {}).get("ganita_positions_rows", 0)
        cf_rows = result.get("totals", {}).get("chart_facts_rows", 0)
        gate_overall = result.get("gate_results", {}).get("overall", "UNKNOWN")

        print(f"\n{'='*60}")
        print(f"GA3 BUILD COMPLETE")
        print(f"  Status:              {status}")
        print(f"  chart_id:            {result.get('chart_id')}")
        print(f"  build_id:            {result.get('build_id')}")
        print(f"  ganita_positions:    {gp_rows} rows")
        print(f"  chart_facts:         {cf_rows} rows")
        print(f"  Gate overall:        {gate_overall}")
        print(f"{'='*60}")

        # Print gate details
        for gate_name, gate_result in result.get("gate_results", {}).get("gates", {}).items():
            gstatus = gate_result.get("result", "?")
            findings = gate_result.get("findings", [])
            print(f"  [{gstatus}] {gate_name}: {len(findings)} findings")
            for f in findings[:3]:
                print(f"       {f}")

    sys.exit(0 if result.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()
