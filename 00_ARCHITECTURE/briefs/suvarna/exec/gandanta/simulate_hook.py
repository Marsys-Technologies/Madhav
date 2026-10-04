#!/usr/bin/env python3
"""Offline simulation of the Gandanta lane through the class-flip detector (read-only; no database access).

Builds a "snapshot" state from the STORED `graha_gandanta` / `sensitive_degree_check.gandanta`
rows and a "current" state from what the new `ga_nakshatra` emitter would write (reconstructed from
the stored sidereal longitudes through `brahmagyan.gandanta`), then runs the detector's own pure
`compare_states` against the hook files in --hooks-dir. This is how the hook's `expected_count`
values were obtained.

Run (from platform/python-sidecar, so `brahmagyan` and `ga_writers` import):
  PYTHONPATH=. python3 ../../00_ARCHITECTURE/briefs/suvarna/exec/gandanta/simulate_hook.py \
      facts.json --detector-dir <dir holding flip_detector.py> --hooks-dir <dir holding *.json hooks>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter

from ga_writers.ga_nakshatra_compute import compute_gandanta, compute_gandanta_strict

CHARTS = {"482012f1-710e-4a25-994a-93821f5871aa": "canonical",
          "1c826d5a-41cb-4450-b4dc-59d440e5f75a": "abhinandan",
          "cb73cd3d-9eba-4220-9902-0de91566e980": "third"}


def num_text(x) -> str:
    return "" if x is None else str(x)


def rows_for(reading: dict) -> list[tuple]:
    """(key, text, num) rows the emitter writes for one reading."""
    out = [("is_gandanta", "true" if reading["is_gandanta"] else "false", None)]
    if reading["is_gandanta"]:
        out += [("arc_minutes_from_junction", None, reading["arc_minutes_from_junction"]),
                ("junction_type", reading["junction_type"], None),
                ("side", reading["side"], None)]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("facts")
    ap.add_argument("--detector-dir", required=True)
    ap.add_argument("--hooks-dir", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("flip_detector", os.path.join(a.detector_dir, "flip_detector.py"))
    fd = importlib.util.module_from_spec(spec)
    sys.modules["flip_detector"] = fd
    spec.loader.exec_module(fd)
    hooks, errors = fd.load_hooks(a.hooks_dir)
    if errors:
        print("HOOK ERRORS:", errors)
        return 2

    facts = json.load(open(a.facts, encoding="utf-8"))
    out = {}
    for chart_id, label in CHARTS.items():
        snap_rows, cur_rows = [], []
        lons = {}
        for f in facts:
            if f["chart_id"] != chart_id:
                continue
            if f["fact_category"] == "graha_position" and f["fact_key"] == "longitude_sidereal":
                lons[(f["ayanamsha_id"], f["fact_subject"])] = float(f["fact_value_num"])
            elif f["fact_category"] in ("graha_gandanta", "sensitive_degree_check"):
                row = [f["ayanamsha_id"], f["fact_category"], f["fact_subject"], f["fact_key"],
                       f["fact_value_text"] or "", num_text(f["fact_value_num"]),
                       f["verification_pass_status"] or ""]
                snap_rows.append(row)
                if f["fact_category"] == "sensitive_degree_check":
                    cur_rows.append(list(row))         # ga_sensitive_degree output is unchanged by I-22
        for (ay, subj), lon in sorted(lons.items()):
            for key, text, num in rows_for(compute_gandanta(lon)):               # canonical rows
                cur_rows.append([ay, "graha_gandanta", subj, key, text or "", num_text(num), "single"])
            for key, text, num in rows_for(compute_gandanta_strict(lon)):        # strict_0_48 variant rows
                cur_rows.append([ay, "graha_gandanta", subj, key, text or "", num_text(num), "single"])
        snap = {"chart_facts": snap_rows, "divisionals": [], "dashas": [], "daily": []}
        cur = {"chart_facts": cur_rows, "divisionals": [], "dashas": [], "daily": []}
        rep = fd.compare_states(snap, cur, hooks, chart_id, have_dash=False, have_daily=False)
        by = Counter((c["category"], c["fact_key"], c["change"]) for c in rep["changes"])
        out[label] = {
            "changes_total": rep["changes_total"], "unattributed": rep["unattributed"],
            "expectation_mismatches": rep["expectation_mismatches"],
            "expectations": rep["expectations"],
            "by_category_key_change": [[list(k), v] for k, v in sorted(by.items())],
        }
    text = json.dumps(out, indent=2, sort_keys=True)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
