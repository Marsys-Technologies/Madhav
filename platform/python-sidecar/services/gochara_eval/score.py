"""Full scoring pass: registry + extract + controls → machine-readable result.

Result JSON carries the same top-level fields as rerun_result_v2_3.json so
figures compare directly. INPUT_REJECTED stops write the result file with the
rejection block and exit non-zero (protocol §4.5 / §9.1).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .controls import ControlsMismatch, verify_controls_file
from .extract import InputRejected, load_extract
from .metrics import score_generation
from .registry import RegistryError, load_registry

RESULT_VERSION = "2.3"
PROTOCOL = "EVALUATION_PROTOCOL_v2_3"


def run_scoring_pass(registry_path: str | Path,
                     extract_path: str | Path,
                     controls_path: str | Path | None,
                     output_path: str | Path,
                     declared_pin: str | None = None,
                     generation: str | None = None) -> dict:
    """Run one scoring pass; write the result file; return the result dict.

    On INPUT_REJECTED / reconciliation halt / controls mismatch, the partial
    result (with the machine-readable rejection block) is still written and a
    SystemExit(1) is raised.
    """
    result: dict = {"artifact": "rerun_result", "version": RESULT_VERSION,
                    "protocol": PROTOCOL,
                    "registry": Path(registry_path).name,
                    "extract": Path(extract_path).name}
    if generation is not None:
        result["generation"] = generation
    output_path = Path(output_path)

    def bail(block: dict, msg: str) -> None:
        result.update(block)
        output_path.write_text(json.dumps(result, indent=1))
        raise SystemExit(msg)

    try:
        extract = load_extract(extract_path, declared_pin=declared_pin)
    except InputRejected as exc:
        block = {"status": "INPUT_REJECTED", "reason": exc.reason}
        if exc.offending_rows:
            block["offending_rows"] = len(exc.offending_rows)
            block["examples"] = exc.offending_rows
        bail({"input_adapter": block}, f"INPUT_REJECTED: {exc.reason}")
    result["extract_sha256"] = extract.sha256
    result["input_adapter"] = {
        "status": "PASS",
        "rule": "all raw si >= 0 (valence domain {gain,loss,mixed,neutral} is "
                "descriptive; convention is on si sign)",
        "raw_valence_domain": extract.valence_domain,
        "raw_row_count": extract.row_count}
    result["dedup_table"] = extract.dedup_table

    try:
        registry = load_registry(registry_path)
    except RegistryError as exc:
        reason = str(exc)
        key = ("source_reconciliation" if reason.startswith("SOURCE-RECONCILIATION")
               else "input_adapter")
        status = "MISMATCH" if key == "source_reconciliation" else "INPUT_REJECTED"
        bail({key: {"status": status, "detail": reason}}, reason)
    result["source_reconciliation"] = registry.reconciliation

    scored = score_generation(registry, extract)
    result.update(scored)

    if controls_path is not None:
        try:
            result["random_controls"] = verify_controls_file(
                controls_path, registry, extract)
        except ControlsMismatch as exc:
            bail({"random_controls": {"status": "REJECTED", "reason": str(exc)}},
                 f"CONTROLS REJECTED: {exc}")

    output_path.write_text(json.dumps(result, indent=1))
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gochara_eval",
        description="B5.3 retrodiction harness — score one generation extract "
                    "under EVALUATION_PROTOCOL_v2_3.")
    ap.add_argument("--registry", required=True, help="event registry JSON path")
    ap.add_argument("--extract", required=True, help="scored extract JSON path")
    ap.add_argument("--controls", default=None,
                    help="materialised random-controls JSON to verify (§7)")
    ap.add_argument("--output", required=True, help="result JSON output path")
    ap.add_argument("--declared-pin", default=None,
                    help="declared extract sha256 pin (§9.1; measured hash is "
                         "compared against it, INPUT_REJECTED on mismatch)")
    ap.add_argument("--generation", default=None,
                    help="generation label recorded in the result file")
    args = ap.parse_args(argv)

    try:
        result = run_scoring_pass(args.registry, args.extract, args.controls,
                                  args.output, declared_pin=args.declared_pin,
                                  generation=args.generation)
    except SystemExit as exc:
        print(exc.code if isinstance(exc.code, str) else exc, file=sys.stderr)
        return 1

    tc, tt, tr = result["t_cover"], result["t_time"], result["t_rank"]
    print(f"T-cover {tc['hits']}/{tc['total']} (pass={tc['pass']}); "
          f"T-time capped median {tt['capped_median_days']} d "
          f"(misses={tt['misses']}, uncapped={tt['uncapped_hits']}); "
          f"T-rank {tr['status']}; "
          f"T-FP overall pass={result['t_fp_overall']['pass']}; "
          f"T-honesty {result['t_honesty']['status']}")
    if "random_controls" in result:
        rc = result["random_controls"]
        print(f"random controls {rc['status']}: "
              f"{rc.get('total_hits')}/{rc.get('total_draws')}")
    print(f"result written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
