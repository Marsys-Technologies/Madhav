"""MB-7 draft report from a verified MB-3 export and bound observations.

Reports retain every missing prerequisite. A draft, even with no formatting
refusals, never constitutes independent acceptance or permission to teardown.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import math
from pathlib import Path
import re
import sys

from . import measuring_capture as mc
from . import measuring_report as mr

CANNOT_ESTABLISH = (
    "Nothing about the eight ND-H classes beyond P2; nothing about K-B, karakatva, natal-Sun target, DVI, "
    "the 40% guard's decision (final-rules candidate); no near-miss storage; no scoring, endpoints, "
    "retrodiction or 3.0 comparison; nothing about sealing, publication, serving, 1236, rollback, "
    "1984-1998; no final run length (lower bound); no verification rows; nothing about 1305-1308.")
RECOUNT_LIMIT = ("Group-I recount shares contact_reconstruct.band_intervals with the certifier (common-mode limit); "
                 "excursions shorter than 60 s are not excluded. A recount that finds nothing is not complete.")
VARIANTS = ("P1_base", "P1_with_karakatva", "P2", "P3_fast", "P3_slow", "P3_union",
            "P4_without_dvi", "P4_with_dvi", "class_union", "kb_only")


class DeliveryRefused(ValueError):
    """Input is not a report for this exact export."""


def _load(directory, name):
    text = (Path(directory) / name).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()] if name.endswith(".jsonl") else json.loads(text)


def _grid(records, windows, horizon=None):
    report = (mr.class_share_report(records, windows, horizon) if horizon is not None
              else mr.scored_share_report(records, windows))
    # Absence in the captured tables means zero rows, not an omitted class.
    for cls in sorted(mr.SCORED_CLASSES):
        if cls not in report["classes"]:
            report["classes"][cls] = {"admitted_days": dict.fromkeys(VARIANTS, 0),
                                      "admitted_share": dict.fromkeys(VARIANTS, 0.0), "per_agent": {},
                                      "window_lengths_days": {p: mr.length_distribution([]) for p in mr.PATHS},
                                      "P4_joint": {"without_dvi_days": 0, "with_dvi_days": 0}}
    return report


def build_report(golden, observations):
    receipt = mc.verify_bundle(golden)
    digests = _load(golden, "digests.json")
    if (observations.get("binding") != digests["binding"]
            or observations.get("golden_manifest_sha256") != receipt["manifest_sha256"]):
        raise DeliveryRefused("report_evidence_binding_mismatch")
    raw_records, raw_windows = _load(golden, "records.jsonl"), _load(golden, "windows.jsonl")
    records = []
    census = Counter()
    for row in raw_records:
        key = json.loads(row["gkey"])
        census[(key["event_class"], key["path_id"])] += 1
        if row["admission_state"] == "admitted" and row["operator_role"] == "scored":
            if key["rule_version"] not in mr.ALLOWED_RULE_VERSIONS:
                raise mr.MeasuringReportError("rule_version_not_in_scope")
            records.append(mr.SupportRecord(key["event_class"], key["path_id"], key["agent"],
                           tuple(tuple(datetime.fromisoformat(t) for t in span) for span in row["supports"])))
    windows = [(w["event_class"], w["path_id"], datetime.fromisoformat(w["lo"]), datetime.fromisoformat(w["hi"]))
               for w in raw_windows]
    horizon = digests["informational"]["horizon"]
    build, scored = _grid(records, windows, horizon), _grid(records, windows)
    numbers = {}

    def add(n, group, data, convention=None):
        numbers[str(n)] = {"group": group, "convention": convention, "data": data}

    add(1, "S", observations.get("timings"))
    add(2, "S", observations.get("runtime"))
    add(3, "S", {"observed": observations.get("row_counts"),
                  "captured": {"ka_gochara_contact": len(_load(golden, "contacts.jsonl")),
                               "ka_gochara_relationship_record": len(raw_records), "ka_gochara_eval_window": len(raw_windows)},
                  "records_by_class_path": [{"event_class": c, "path": p, "count": n} for (c, p), n in sorted(census.items())]})
    add(4, "I", build, "UTC-HO")
    add(5, "I", scored, "IST-INC")
    add(6, "I", {c: v["window_lengths_days"] for c, v in build["classes"].items()}, "UTC-HO")
    add(7, "I", {c: v["per_agent"] for c, v in build["classes"].items()}, "UTC-HO")
    add(8, "I/R", {"observed": observations.get("sink_recount"), "limit": RECOUNT_LIMIT,
                   "emitted_records": len(_load(golden, "stretch_sink.jsonl")), "independent_recount_performed_by_exporter": False})
    add(9, "I", {c: {p: census[c, p] for p in mr.PATHS} for c in sorted(mr.EXCLUDED_EIGHT)})
    add(10, "I", {"basis": _load(golden, "horizon_basis.json"), "observed": observations.get("horizon_readback")})
    add(11, "I", {**receipt, "binding": digests["binding"], "golden_commit": observations.get("golden_commit")})
    add(12, "S", observations.get("teardown"))
    add(13, "I", {"cannot_establish": CANNOT_ESTABLISH, "observed": observations.get("acceptance")})
    add(14, "I", {"scored_share": scored["classes"]["bereavement"]["admitted_share"]["class_union"],
                   "budget_share": .0261, "label": "structural-saturation finding, not a decision"}, "IST-INC")
    report = {"schema": "ky.measuring_report_draft/1", "binding": digests["binding"],
              "golden_manifest_sha256": receipt["manifest_sha256"], "numbers": numbers,
              "status": "DRAFT_AWAITING_INDEPENDENT_ACCEPTANCE", "independent_acceptance": None,
              "source_commit_attested": None}
    report["refusals"] = report_refusals(report)
    return report


def report_refusals(report):
    """MB-7 completeness/ratio checks; these do not attest steward observations."""
    numbers = report.get("numbers", {})
    refusals = []
    for n in range(1, 15):
        item = numbers.get(str(n), {})
        data = item.get("data")
        if data is None or (str(n) in {"3", "8", "10", "13"} and data.get("observed") is None):
            refusals.append(f"report_number_missing:{n}")
    for n, label, grid_label, denominator, horizon in (
            ("4", "UTC-HO", "utc_half_open", 31446, ["1998-01-01", "2084-02-05"]),
            ("5", "IST-INC", "ist_inclusive", 10334, ["1998-01-01", "2026-04-17"])):
        item = numbers.get(n, {})
        data = item.get("data")
        if not isinstance(data, dict):
            continue
        if (item.get("convention") != label or data.get("convention") != grid_label
                or data.get("horizon_days") != denominator or data.get("horizon") != horizon):
            refusals.append("report_convention_mixed")
            continue
        if set(data.get("classes", {})) != mr.SCORED_CLASSES:
            refusals.append(f"report_number_missing:{n}")
        for cls in data.get("classes", {}).values():
            if set(cls.get("admitted_days", {})) != set(VARIANTS) or set(cls.get("admitted_share", {})) != set(VARIANTS):
                refusals.append(f"report_number_missing:{n}")
            for key, days in cls.get("admitted_days", {}).items():
                share = cls.get("admitted_share", {}).get(key)
                if (type(days) is not int or not 0 <= days <= denominator or not isinstance(share, (int, float))
                        or not math.isfinite(share) or not math.isclose(share, days / denominator, rel_tol=0, abs_tol=1e-15)):
                    refusals.append("report_ratio_mismatch")
    if numbers.get("13", {}).get("data", {}).get("cannot_establish") != CANNOT_ESTABLISH:
        refusals.append("report_scope_statement_missing")
    if numbers.get("8", {}).get("data", {}).get("limit") != RECOUNT_LIMIT:
        refusals.append("report_recount_limit_missing")
    timing = numbers.get("1", {}).get("data")
    timing_fields = {"run_seconds", "asset_seconds", "by_phase", "by_class_substep"}
    if not isinstance(timing, dict) or not timing_fields <= timing.keys() or any(
            not isinstance(timing[k], dict) or not timing[k] for k in ("by_phase", "by_class_substep") if k in (timing or {})):
        refusals.append("report_number_missing:1")
    else:
        seconds = [timing["run_seconds"], timing["asset_seconds"], *timing["by_phase"].values(), *timing["by_class_substep"].values()]
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in seconds):
            refusals.append("report_timing_invalid")
    runtime = numbers.get("2", {}).get("data")
    if runtime is not None:
        refusals.extend(mr._runtime_refusals(runtime, status="candidate", stored_scope="test_slice"))
        if (not isinstance(runtime, dict) or type(runtime.get("planned_substeps")) is not int
                or runtime.get("planned_substeps") != 298):
            refusals.append("substep_plan_incomplete")
    commit = numbers.get("11", {}).get("data", {}).get("golden_commit")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        refusals.append("golden_commit_not_recorded")
    rows = numbers.get("3", {}).get("data", {})
    if isinstance(rows.get("observed"), dict):
        if any(type(rows["observed"].get(t)) is not int or rows["observed"].get(t) != count for t, count in rows["captured"].items()):
            refusals.append("report_row_counts_mismatch")
    teardown = numbers.get("12", {}).get("data")
    if not isinstance(teardown, dict) or teardown.get("outcome") != "COMMITTED_AWAITING_ABSENCE":
        refusals.append("teardown_not_executed")
    elif not teardown.get("independent_absence_receipt"):
        refusals.append("teardown_independent_absence_missing")
    acceptance = numbers.get("13", {}).get("data", {}).get("observed")
    if not isinstance(acceptance, dict) or not acceptance.get("independent_review"):
        refusals.append("acceptance_not_independently_reviewed")
    return list(dict.fromkeys(refusals))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--golden", required=True)
    report = sub.add_parser("report")
    report.add_argument("--golden", required=True)
    report.add_argument("--observations", required=True)
    report.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(mc.canonical(mc.verify_bundle(args.golden)))
        else:
            result = build_report(args.golden, json.loads(Path(args.observations).read_text(encoding="utf-8")))
            # No replace of reviewed evidence. A draft with missing observations
            # is useful, but its explicit refusals and null acceptance remain.
            with Path(args.output).open("x", encoding="utf-8") as out:
                out.write(mc.canonical(result) + "\n")
        return 0
    except (mc.CaptureRefused, DeliveryRefused, mr.MeasuringReportError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
