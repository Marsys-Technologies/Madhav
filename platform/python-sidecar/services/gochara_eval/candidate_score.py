"""CLI for the candidate scoring pass (Stage-1 scorer). Two modes, no third:

  MEASUREMENT      --stage1 F1 --stage2 F2 --extract E   — verifies BOTH freeze stages and the extract hash, then scores.
  BASELINE DRY RUN --baseline-dry-run --declared-pin P   — scores the pinned '3.0' extract ONLY; refuses any extract whose header
                                                           names another generation (so it cannot be used to read a candidate).

The candidate extract is never opened before the Stage-2 check passes. Result JSON: same top-level blocks as `score.py` plus
`unknown_competitors`, `freeze`, and range-valued si-dependent endpoints.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .candidate import load_candidate_extract, score_candidate
from .controls import ControlsMismatch, verify_controls_file
from .dump_extract import CANONICAL_COMMAND
from .extract import InputRejected
from .freeze import FreezeRefused, bind_scoring_run, require_stage1, require_stage2, sha256_file
from .registry import RegistryError, load_registry
from .score import PROTOCOL, RESULT_VERSION

BASELINE_PREDICATE_MARK = "generation='3.0'"


def run(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="candidate_score")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--controls")
    ap.add_argument("--output", required=True)
    ap.add_argument("--stage1")
    ap.add_argument("--stage2")
    ap.add_argument("--inputs-root", help="directory the Stage-1 input paths are relative to (default: Stage-1's directory)")
    ap.add_argument("--baseline-dry-run", action="store_true")
    ap.add_argument("--declared-pin")
    ap.add_argument("--budget", type=int, default=None)
    args = ap.parse_args(argv)
    out = Path(args.output)
    result: dict = {"artifact": "rerun_result", "version": RESULT_VERSION, "protocol": PROTOCOL,
                    "registry": Path(args.registry).name, "extract": Path(args.extract).name}

    def refuse(block: dict, msg: str) -> int:
        result.update(block)
        out.write_text(json.dumps(result, indent=1))
        print(msg, file=sys.stderr)
        return 1

    if args.baseline_dry_run:
        header = json.loads(Path(args.extract).read_text())
        pred = str(header.get("predicate", ""))
        if BASELINE_PREDICATE_MARK not in pred:
            return refuse({"mode": "REFUSED"}, f"REFUSED: --baseline-dry-run reads only the '3.0' baseline extract, not {pred!r}")
        if not args.declared_pin:
            return refuse({"mode": "REFUSED"}, "REFUSED: the dry run needs --declared-pin (the pinned '3.0' extract hash)")
        result["mode"] = "BASELINE_DRY_RUN"
        result["generation"] = "3.0"
    else:
        if not (args.stage1 and args.stage2):
            return refuse({"mode": "REFUSED"}, "REFUSED: a measurement needs --stage1 and --stage2 (no measurement without both stages)")
        try:
            root = args.inputs_root or str(Path(args.stage1).resolve().parent)
            s1 = require_stage1(args.stage1, root, CANONICAL_COMMAND)
            require_stage2(args.stage2, args.stage1, s1, args.extract)
        except FreezeRefused as exc:
            return refuse({"mode": "REFUSED", "freeze": {"status": "REFUSED", "problems": exc.problems}}, str(exc))
        result["mode"] = "MEASUREMENT"
        result["generation"] = s1["generation"]
        frozen_doc, frozen_root = s1, root
        result["freeze"] = {"status": "VERIFIED", "run_id": s1["run_id"], "stage1_sha256": sha256_file(args.stage1),
                            "stage2_sha256": sha256_file(args.stage2)}

    try:
        cext = load_candidate_extract(args.extract, declared_pin=args.declared_pin)
    except InputRejected as exc:
        return refuse({"input_adapter": {"status": "INPUT_REJECTED", "reason": exc.reason,
                                         **({"examples": exc.offending_rows} if exc.offending_rows else {})}},
                      f"INPUT_REJECTED: {exc.reason}")
    result["extract_sha256"] = cext.sha256
    result["input_adapter"] = {"status": "PASS", "raw_valence_domain": cext.valence_domain, "raw_row_count": cext.row_count,
                               "unknown_si_rows": cext.unknown_rows,
                               "rule": "known raw si >= 0 and finite; unknown si is an explicit null and stays in the candidate set"}
    result["dedup_table"] = cext.dedup_table
    try:
        registry = load_registry(args.registry)
    except RegistryError as exc:
        return refuse({"source_reconciliation": {"status": "MISMATCH", "detail": str(exc)}}, str(exc))
    result["source_reconciliation"] = registry.reconciliation
    if result["mode"] == "MEASUREMENT":           # the freeze is BOUND to what this run actually uses
        bind = bind_scoring_run(frozen_doc, Path(frozen_root), registry_path=args.registry, controls_path=args.controls,
                                extract_path=args.extract, extract_header_predicate=str(cext.meta.get("predicate", "")),
                                registry_held_out=len(registry.held), budget=args.budget)
        if bind:
            return refuse({"mode": "REFUSED", "freeze": {"status": "NOT_BOUND", "problems": bind}},
                          "FREEZE REFUSED: the run does not match the freeze: " + "; ".join(bind))
        kw = {"budget": frozen_doc["tolerances_and_conversions"]["enumeration_budget"]}
    else:
        kw = {} if args.budget is None else {"budget": args.budget}
    result.update(score_candidate(registry, cext, **kw))
    if args.controls:
        try:
            result["random_controls"] = verify_controls_file(args.controls, registry, cext)
        except ControlsMismatch as exc:
            return refuse({"random_controls": {"status": "REJECTED", "reason": str(exc)}}, f"CONTROLS REJECTED: {exc}")
    out.write_text(json.dumps(result, indent=1))
    tc, tt, tr = result["t_cover"], result["t_time"], result["t_rank"]
    print(f"[{result['mode']}] T-cover {tc['hits']}/{tc['total']}; T-time {tt['capped_median_range']} d (pass={tt['pass']}); "
          f"T-rank {tr['status']}; T-FP overall pass={result['t_fp_overall']['pass']}; T-honesty {result['t_honesty']['status']}; "
          f"unknown rows {cext.unknown_rows}")
    print(f"result written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
