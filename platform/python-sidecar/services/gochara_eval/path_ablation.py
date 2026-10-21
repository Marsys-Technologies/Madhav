"""The six per-path ablation runs of a governed generation — the producer of the report's `path_ablations` disclosure
(EVALUATION_PROTOCOL_v2_3 §10: "per-mechanism attribution and per-path ablations (the sealed doctrine's Tier 3) are diagnostics the B5.4 report
must carry; they are not gates"; `qualification_report._disclosure` lists P1..P6 as missing until this output is supplied).

(I) INTERPRETATION — the protocol names the ablation but not its procedure. Here it is LEAVE-ONE-PATH-OUT: for each path Pk of P1..P6, every
window the generation's path Pk built is removed from the sealed extract (the rows carry `path_id`), the remaining windows are re-merged
(§4.2 dedup) and re-scored by the SAME candidate scorer under the SAME frozen registry and enumeration budget, and the endpoint figures are set
beside the full-generation figures. Alternative (not built): a path-ALONE run (only Pk's windows kept). Both read the same stored rows; they answer
"what does Pk add" and "what does Pk do on its own".

Honest limits of what this measures, stated in the output:
  * it re-scores STORED windows. A window that exists because two paths agree is removed with either; a re-run of the sweep without Pk (which
    could admit different windows) is a different experiment, not run here;
  * a path with NO window in the extract is not "ablated": removing nothing changes nothing, and a zero delta would read as "the path does not
    matter". Its record says `path_absent_from_extract` and carries no figures and no delta (a null with its reason, never a 0);
  * a delta is reported only where both figures are known numbers; a range figure (an unknown competitor makes the verdict a range) keeps both
    ends and its delta is taken end by end.
  * it is a diagnostic, never a gate, and the endpoints it recomputes are not re-verdicts of the generation.

The full-generation re-score is compared with the recorded measurement result when one is supplied (`reproduces_recorded_result`): an ablation
set whose own baseline does not reproduce the measured figures is not evidence of anything.

    python -m services.gochara_eval.path_ablation --registry R --extract E --stage1 F1 --stage2 F2 --base-result RESULT.json --out-dir D --output O
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from .candidate import load_candidate_extract_bytes, score_candidate
from .dump_extract import CANONICAL_COMMAND
from .extract import InputRejected
from .freeze import FreezeRefused, bind_scoring_run, require_stage1, require_stage2, sha256_file
from .registry import RegistryError, load_registry
from .unknowns import DEFAULT_BUDGET

PATHS = ("P1", "P2", "P3", "P4", "P5", "P6")
SCHEMA = "ky.path_ablations/1"
MODE = "leave_one_path_out"
#: the result blocks a re-score must reproduce for the full generation (the endpoints; the per-event detail is not compared)
ENDPOINT_BLOCKS = ("t_cover", "t_time", "t_rank", "t_fp", "t_fp_gain", "t_fp_overall", "t_honesty")
ABSENT = ("path_absent_from_extract: the extract holds no window built by this path, so removing it changes nothing and no ablation was run "
          "(a zero delta would read as 'the path does not matter')")
LIMITS = ("leave-one-path-out over STORED windows, re-merged and re-scored under the frozen registry and budget; a re-run of the sweep without the "
          "path could admit different windows and is not measured; a diagnostic, never a gate (protocol §10)")
_PREDICATE = re.compile(r"^(?:public\.)?ka_gochara_eval_window where chart_id='([^']+)' and generation='([^']+)'$")


class AblationRefused(RuntimeError):
    """The extract cannot be ablated honestly (named, never defaulted)."""


def identity_of(doc: dict) -> tuple[str, str]:
    """(chart_id, generation) from the extract header's exact predicate — an ablation only runs on a governed-window extract."""
    m = _PREDICATE.match(str(doc.get("predicate", "")))
    if not m:
        raise AblationRefused(f"the extract's predicate {doc.get('predicate')!r} is not a ka_gochara_eval_window extract: only a governed "
                              "generation's rows carry the path that built them")
    return m.group(1), m.group(2)


def ablate_doc(doc: dict, path_id: str) -> tuple[dict, int]:
    """(the extract with every window built by `path_id` removed, how many)."""
    rows = doc["rows"]
    if any("path_id" not in r for r in rows):
        raise AblationRefused("extract rows without `path_id`: the path that built a window is not recorded, so a path cannot be removed")
    keep = [r for r in rows if r["path_id"] != path_id]
    body = {k: v for k, v in doc.items() if k not in ("rows", "row_count")}
    return {**body, "row_count": len(keep), "ablation": {"mode": MODE, "removed_path": path_id, "source_row_count": len(rows),
                                                          "rows_removed": len(rows) - len(keep)}, "rows": keep}, len(rows) - len(keep)


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def figures(res: dict) -> dict:
    """The endpoint figures an ablation compares: numbers where the scorer produced them, statuses and verdicts as recorded, None otherwise."""
    tc, tt, tr, tf, th = (res.get(k) or {} for k in ("t_cover", "t_time", "t_rank", "t_fp_overall", "t_honesty"))
    t_rng = tt.get("capped_median_range") or [None, None]
    r_rng = tr.get("median_range") or ([tr["median_percentile"]] * 2 if tr.get("median_percentile") is not None else [None, None])
    return {"t_cover": {"hits": tc.get("hits"), "total": tc.get("total"), "pass": tc.get("pass")},
            "t_time": {"median_lo": t_rng[0], "median_hi": t_rng[1], "status": tt.get("status"), "pass": tt.get("pass")},
            "t_rank": {"median_lo": r_rng[0], "median_hi": r_rng[1], "eligible": tr.get("eligible"), "status": tr.get("status"),
                       "pass": tr.get("pass")},
            "t_fp_overall": {"pass": tf.get("pass")},
            "t_honesty": {"status": th.get("status"), "pass": th.get("pass")}}


def delta(base: dict, ablated: dict) -> dict:
    """ablated - full for every numeric figure known on both sides (None otherwise); verdict fields only say whether they changed."""
    out: dict = {}
    for endpoint, fig in base.items():
        out[endpoint] = {}
        for key, was in fig.items():
            now = ablated[endpoint][key]
            if key in ("pass", "status"):
                out[endpoint][key] = {"full": was, "ablated": now, "changed": was != now}
            else:
                out[endpoint][key] = (now - was) if _num(was) is not None and _num(now) is not None else None
    return out


def _endpoint_blocks(res: dict) -> dict:
    return {k: json.loads(json.dumps(res.get(k))) for k in ENDPOINT_BLOCKS}


def run_ablations(registry, raw_extract: bytes, *, budget: int = DEFAULT_BUDGET, paths=PATHS, out_dir: str | Path | None = None,
                  recorded_result: dict | None = None) -> dict:
    """The ablation record of every path in `paths` over the extract. `out_dir`: the ablated extracts are written there (their sha256 is
    recorded either way, so each run is reproducible from the sealed extract and this code)."""
    doc = json.loads(raw_extract)
    chart_id, generation = identity_of(doc)
    full_cext = load_candidate_extract_bytes(raw_extract)
    full = score_candidate(registry, full_cext, budget=budget)
    reproduces = None if recorded_result is None else _endpoint_blocks(full) == _endpoint_blocks(recorded_result)
    base = figures(full)
    records: dict = {}
    for path_id in paths:
        ablated, removed = ablate_doc(doc, path_id)
        if removed == 0:
            records[path_id] = {"path_id": path_id, "status": "path_absent_from_extract", "rows_removed": 0, "rows_remaining": len(doc["rows"]),
                                "figures": None, "delta_vs_full": None, "null_reason": ABSENT, "extract_sha256": None}
            continue
        blob = json.dumps(ablated, indent=1).encode()
        res = score_candidate(registry, load_candidate_extract_bytes(blob), budget=budget)
        if out_dir is not None:
            Path(out_dir, f"ablated_extract_{path_id}.json").write_bytes(blob)
        fig = figures(res)
        records[path_id] = {"path_id": path_id, "status": "MEASURED", "rows_removed": removed, "rows_remaining": len(ablated["rows"]),
                            "figures": fig, "delta_vs_full": delta(base, fig), "null_reason": None,
                            "unknown_competitors": res["unknown_competitors"],
                            "extract_sha256": hashlib.sha256(blob).hexdigest()}
    return {"schema": SCHEMA, "chart_id": chart_id, "generation": generation, "mode": MODE, "non_gating": True,
            "enumeration_budget": budget,
            "base": {"source_row_count": len(doc["rows"]), "figures": base, "reproduces_recorded_result": reproduces,
                     "extract_sha256": hashlib.sha256(raw_extract).hexdigest()},
            "limits": LIMITS, "paths": records}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gochara_eval.path_ablation", description=__doc__.splitlines()[0])
    ap.add_argument("--registry", required=True)
    ap.add_argument("--extract", required=True, help="the SEALED governed extract the measurement scored")
    ap.add_argument("--stage1", required=True)
    ap.add_argument("--stage2", required=True)
    ap.add_argument("--inputs-root")
    ap.add_argument("--controls", help="the random-controls file (default: the one the freeze names, only to satisfy the freeze binding)")
    ap.add_argument("--base-result", required=True, help="the MEASUREMENT result of that extract (the ablation baseline must reproduce it)")
    ap.add_argument("--out-dir", required=True, help="where the ablated extracts are written")
    ap.add_argument("--output", required=True)
    ap.add_argument("--budget", type=int, default=None)
    args = ap.parse_args(argv)
    try:
        root = args.inputs_root or str(Path(args.stage1).resolve().parent)
        s1 = require_stage1(args.stage1, root, CANONICAL_COMMAND)
        require_stage2(args.stage2, args.stage1, s1, args.extract)
        raw = Path(args.extract).read_bytes()
        recorded = json.loads(Path(args.base_result).read_text())
        if recorded.get("mode") != "MEASUREMENT" or recorded.get("freeze", {}).get("status") != "VERIFIED":
            raise AblationRefused("--base-result is not a verified MEASUREMENT result")
        if recorded.get("extract_sha256", {}).get("measured") != sha256_file(args.extract):
            raise AblationRefused("--base-result did not score this extract (its measured extract sha256 differs)")
        header = json.loads(raw)
        registry = load_registry(args.registry)
        bind = bind_scoring_run(s1, Path(root), registry_path=args.registry, controls_path=args.controls or _controls_of(s1, root),
                                extract_path=args.extract, extract_header_predicate=str(header.get("predicate", "")),
                                registry_held_out=len(registry.held), budget=args.budget)
        if bind:
            raise AblationRefused("the run does not match the freeze: " + "; ".join(bind))
        budget = s1["tolerances_and_conversions"]["enumeration_budget"]
        Path(args.out_dir).mkdir(parents=True, exist_ok=True)
        result = run_ablations(registry, raw, budget=budget, out_dir=args.out_dir, recorded_result=recorded)
    except (FreezeRefused, AblationRefused, InputRejected, RegistryError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    Path(args.output).write_text(json.dumps(result, indent=1, sort_keys=True))
    ran = [p for p, r in result["paths"].items() if r["status"] == "MEASURED"]
    print(f"ablations written: {args.output} (measured {ran}; absent {[p for p in result['paths'] if p not in ran]}; "
          f"baseline reproduces the recorded result: {result['base']['reproduces_recorded_result']})")
    return 0


def _controls_of(s1: dict, root) -> str | None:
    """The frozen random-controls file (the freeze binds it; an ablation does not use it, but the binding check needs the same file)."""
    ent = s1["inputs"]["random_controls"]
    return str(Path(root) / ent["path"])


if __name__ == "__main__":
    raise SystemExit(main())
