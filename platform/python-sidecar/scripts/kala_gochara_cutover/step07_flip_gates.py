#!/usr/bin/env python3
"""step07_flip_gates.py — WP10 runbook step 7 (plan §9): the four flip gates.

Runs the four functional flip gates (migration 527's gate set) as checks:

  1. provenance (P-1a) — the serving provenance for the candidate generation
     names ka_gochara, manifest-driven. TS-side gate (platform-mcp
     register_gochara_windows). This script verifies the DB substrate the gate
     reads: a candidate/published manifest exists for (chart, generation) with
     writer_asset_id='ka_gochara'. The route-level assertion is the TS test
     named below and is NOT_RUN here.
  2. coverage (P-1b) — computeGocharaCoverage equals the manifest. TS-side;
     DB substrate verified here: kala_gochara_coverage rows exist for the
     generation and their target counts are internally consistent
     (resolved + unresolved = requested).
  3. disclosure — deriveResolutionDisclosure. TS-side only; no DB substrate.
     NOT_RUN here; the gate test records the TS test name.
  4. rollback-through-adapters rehearsal — the ledger's own rollback() of a
     SCRATCH candidate (never the real candidate) is exercised against the
     target DB: contacts/coverage vanish, manifest reads rolled_back, and the
     writer refuses delete-then-insert afterwards.

Tranche 2 (PRODUCTION_TRANCHE_2_AUTHORIZED). Sheet A-3. A failed gate yields
a NEW CANDIDATE, never a patch (7.C).

TS gate tests (run with the platform suite at tranche time, recorded here so
the evidence file can name them):
  - P-1a/P-1b: platform-mcp register_gochara_windows manifest-driven
    provenance/coverage tests (packet P-1: '4.0' authority names ka_gochara,
    unchanged after a '4.1' republish).
  - disclosure: platform deriveResolutionDisclosure tests (packet P-1/P-2).

Usage:
    python3 step07_flip_gates.py --dsn postgresql://... --chart-id <uuid> \
        [--generation 4.0] [--evidence]

Exit codes: 0 all DB-substrate gates green; 3 cannot proceed;
4 production refusal; 7 at least one gate RED.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = step_parser(7, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.0")
    args = parser.parse_args()

    conn = connect(args.dsn, step=7)
    gates = {}

    with conn.cursor() as cur:
        # Gate 1 substrate: manifest exists for (chart, generation), written by
        # ka_gochara, in a servable state.
        cur.execute(
            "SELECT status, writer_asset_id FROM kala_gochara_publication "
            "WHERE chart_id = %s AND generation = %s "
            "ORDER BY created_at DESC LIMIT 1",
            (args.chart_id, args.generation))
        row = cur.fetchone()
        gates["provenance_p1a_substrate"] = {
            "pass": bool(row and row[1] == "ka_gochara"
                         and row[0] in ("candidate", "published")),
            "detail": f"manifest status={row[0] if row else None} "
                      f"writer={row[1] if row else None}",
            "ts_gate": "NOT_RUN (route test lives in platform-mcp; see module "
                       "docstring)",
        }

        # Gate 2 substrate: coverage rows exist and are count-consistent.
        cur.execute(
            "SELECT count(*), bool_and(targets_resolved + targets_unresolved "
            "= targets_requested) FROM kala_gochara_coverage "
            "WHERE chart_id = %s AND generation = %s",
            (args.chart_id, args.generation))
        n_cov, consistent = cur.fetchone()
        gates["coverage_p1b_substrate"] = {
            "pass": bool(n_cov and consistent),
            "detail": f"coverage rows={n_cov} count-consistent={consistent}",
            "ts_gate": "NOT_RUN (route test lives in platform-mcp)",
        }

        # Gate 3: disclosure is TS-only.
        gates["disclosure_derive_resolution"] = {
            "pass": None,
            "detail": "NOT_RUN: deriveResolutionDisclosure is a TS function; "
                      "no DB substrate. Run the platform test at tranche time.",
        }

    # Gate 4: rollback-through-adapters on a SCRATCH candidate generation —
    # never the real one. Uses the ledger's own lifecycle functions.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cutover_step07_ledger", SIDECAR / "services" / "gochara_kernel" / "ledger.py")
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)

    scratch_gen = f"{args.generation}-gate4-scratch"
    scratch_ok, scratch_detail = False, ""
    conn.autocommit = False
    try:
        cid = ledger.register_convention(conn, {
            "zodiac": "sidereal", "ayanamsha": "lahiri_chitrapaksha",
            "sidereal_method": "swe_flg_sidereal", "node_model": "mean",
            "node_source": "swiss_mean_node_flg_sidereal",
            "epoch_convention": "noon_ut_knot_abscissa",
            "time_scale": "ut_to_tt_swe_deltat", "house_system": "whole_sign",
            "ephemeris_mode": "flg_swieph", "method_version": "1.0.0",
        }, {"ephemeris_backend": "swieph", "retflag": 258})
        ledger.publish_candidate(conn, args.chart_id, scratch_gen, cid,
                                 {"gate": 4, "scratch": True},
                                 {"backend": "swieph", "retflag": 258},
                                 "[2026-01-01,2026-01-02)")
        ledger.write_coverage(conn, args.chart_id, scratch_gen, cid, [{
            "partition_kind": "body_target", "partition_key": "gate4:scratch",
            "requested_horizon": "[2026-01-01,2026-01-02)",
            "completed_horizon": "[2026-01-01,2026-01-02)",
            "resolution": 2.0, "relations_searched": ["conjunction"],
            "targets_requested": 0,
            "target_resolution_state_counts": {"resolved": 0, "unavailable": 0,
                                               "unqualified": 0},
            "unavailable_inputs": {}, "unsearched_reason": None,
        }], "wp10-gate4")
        ledger.rollback(conn, args.chart_id, scratch_gen)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM kala_gochara_coverage "
                "WHERE chart_id = %s AND generation = %s",
                (args.chart_id, scratch_gen))
            leftover = cur.fetchone()[0]
            cur.execute(
                "SELECT status FROM kala_gochara_publication "
                "WHERE chart_id = %s AND generation = %s",
                (args.chart_id, scratch_gen))
            status = cur.fetchone()[0]
        # Post-rollback, delete-then-insert against the rolled_back generation
        # must be refused (manifest is no longer a candidate).
        refused = False
        try:
            ledger.write_coverage(conn, args.chart_id, scratch_gen, cid, [],
                                  "wp10-gate4-post-rollback")
        except ledger.PublishedGenerationRefusal:
            refused = True
        conn.commit()
        scratch_ok = leftover == 0 and status == "rolled_back" and refused
        scratch_detail = (f"leftover coverage={leftover} manifest={status} "
                          f"post-rollback write refused={refused}")
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        scratch_detail = f"gate 4 raised: {exc}"
    finally:
        # Clean the scratch generation's manifest row so the gate is
        # re-runnable; the row is gate scaffolding, not data.
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM kala_gochara_publication "
                    "WHERE chart_id = %s AND generation = %s",
                    (args.chart_id, scratch_gen))
            conn.commit()
        except Exception:  # noqa: BLE001
            conn.rollback()
    conn.close()
    gates["rollback_through_adapters"] = {"pass": scratch_ok,
                                          "detail": scratch_detail}

    ok = all(g["pass"] for g in gates.values() if g["pass"] is not None)
    print(json.dumps(gates, indent=2, default=str))
    if args.evidence:
        write_evidence(7, "GREEN" if ok else "RED",
                       f"```json\n{json.dumps(gates, indent=2, default=str)}\n```")
    return 0 if ok else 7


if __name__ == "__main__":
    sys.exit(main())
