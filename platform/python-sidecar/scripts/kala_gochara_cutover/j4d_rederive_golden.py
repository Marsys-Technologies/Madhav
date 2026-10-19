"""J-4d (c), SR-EDGES-PROOF: re-derive the slice classes' golden cells locally, from the old golden's own inputs, with the fixed solver.

The measuring golden was captured with the pre-fix span-edge derivation (PR #3770 moves every solved point contact's `t_in` / `t_out`). This script
rebuilds the golden's cells for the slice classes on a local lane database from nothing but the old golden's own inputs (its chart, generation and horizon),
by driving the writer's real plan under the MEASURING rules (the default profile; the golden's rule set), and writes the result in the golden's own bundle
format (`measuring_capture.make_bundle`, so a bundle written here is loaded and verified by `j4d_slice_qualify.load_golden`).

Two things are then measured and printed:

  * the re-derived cells equal the old golden in every stored field except the point-contact edges (`equality_proof(all_cells=True)`, the same
    proof the qualification runs), so the re-derivation is the golden's cells and not a different build;
  * with `--solver prefix` (the pre-fix edge derivation, the control) the re-derivation must equal the old golden BYTE FOR BYTE, edges included
    (`strict_edges=True`): a re-derivation that cannot reproduce the old golden with the old solver proves nothing about the new one.

The slice build under the FINAL rules (`j4d_slice_qualify.py qualify --rederived <this bundle>`) must then equal the `--solver fixed` bundle byte for byte
on every unchanged cell, edges included.

Lane database only (127.0.0.1:55433); never production, never a commit. The output directory must not exist.
"""
from __future__ import annotations

import argparse
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from scripts.kala_gochara_cutover import j4d_slice_qualify as q
from services.gochara_kernel import measuring_capture as mc

SOLVERS = ("fixed", "prefix")


def rederive(conn: Any, golden: dict, classes: list[str], *, ephe_path: str, solver: str = "fixed", **build_kw: Any) -> dict:
    """Build the slice classes under the measuring rules on `conn` and return {'bundle', 'build', 'equality_with_old_golden'}."""
    if solver not in SOLVERS:
        raise q.SliceRefused(f"unknown_solver: {solver!r}")
    binding = golden["binding"]
    with (q.prefix_edge_derivation() if solver == "prefix" else nullcontext()):
        build = q.build_slice(conn, chart_id=binding["chart_id"], horizon=golden["horizon"], classes=classes, ephe_path=ephe_path,
                              final_rules=False, **build_kw)
    raw = q.read_slice_raw(conn, chart_id=binding["chart_id"], classes=classes, generation=binding["generation"])
    informational = {"horizon": [h.isoformat() for h in golden["horizon"]], "input_vector": {}, "rederived": True, "solver": solver,
                     "classes": sorted(classes), "rules": "measuring (default profile)", "old_golden_manifest_sha256": golden["receipt"]["manifest_sha256"]}
    bundle = mc.make_bundle(binding={**binding, "run_id": f"rederived-{solver}-{binding['run_id']}"}, contacts=raw["contacts"], records=raw["records"],
                            windows=raw["windows"], horizon_basis={"schema": "ky.j4d_rederived_horizon/1", "old_golden_manifest_sha256": informational["old_golden_manifest_sha256"]},
                            stretch_sink=[], informational=informational)
    sliced = {"records": bundle["records.jsonl"], "windows": bundle["windows.jsonl"], "contacts": bundle["contacts.jsonl"]}
    equality = q.equality_proof(golden, sliced, classes, strict_edges=solver == "prefix", all_cells=True)
    return {"bundle": bundle, "build": build, "equality_with_old_golden": equality}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--golden", required=True, help="the old (measuring) golden bundle directory")
    parser.add_argument("--dsn", required=True, help="a fresh lane database (127.0.0.1:55433) holding the golden's inputs; the build writes into it")
    parser.add_argument("--classes", help="comma-separated class ids")
    parser.add_argument("--ruled-slice", action="store_true", help="the SR-EDGES-PROOF slice: " + ", ".join(q.RULED_SLICE_CLASSES))
    parser.add_argument("--ephe-path", required=True)
    parser.add_argument("--solver", choices=SOLVERS, default="fixed", help="fixed = the current edge derivation; prefix = the pre-fix control")
    parser.add_argument("--output", required=True, help="the re-derived bundle directory (must not exist)")
    args = parser.parse_args(argv)
    try:
        choice = q.choose_slice(classes=[c for c in args.classes.split(",") if c] if args.classes else None, ruled=args.ruled_slice)
        import psycopg
        golden = q.load_golden(args.golden)
        with psycopg.connect(args.dsn, autocommit=True, connect_timeout=5) as conn:
            got = rederive(conn, golden, choice["classes"], ephe_path=args.ephe_path, solver=args.solver)
        report = {"solver": args.solver, "classes": choice["classes"], "build": {"substeps_run": len(got["build"]["steps"]), "defects": got["build"]["defects"]},
                  "equality_with_old_golden": got["equality_with_old_golden"]}
        ok = not got["build"]["defects"] and bool(got["build"]["steps"]) and got["equality_with_old_golden"]["passed"]
        mc.write_bundle(args.output, got["bundle"])
        print(mc.canonical(report))
        return 0 if ok else 3
    except (q.SliceRefused, mc.CaptureRefused, OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
