#!/usr/bin/env python3
"""Offline old-vs-new Gandanta reconstruction for S-L1 lane I-22 (read-only; no database access here).

INPUT  a JSON array of stored chart_facts rows (SELECT-only dump made as the read-only reader):
         chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_text,
         fact_value_num, verification_pass_status, formula_id, build_id
       for (a) graha_position.longitude_sidereal, (b) graha_gandanta, (c)
       sensitive_degree_check.gandanta, (d) dosha_fires with a gandanta subject.
OUTPUT a JSON report (stdout or --out) and a short text summary.

METHOD
  1. RECONSTRUCTION CHECK. Re-run the OLD ga_nakshatra algorithm (0 deg 48 min; verbatim copy
     below) on the stored sidereal longitudes and compare it with the stored `graha_gandanta`
     rows (is_gandanta, arc_minutes_from_junction, junction_type, side). Same for the OLD
     ga_sensitive_degree `check_gandanta` against the stored `sensitive_degree_check.gandanta`
     rows. Any mismatch is reported, not hidden: it bounds how far the reconstruction can be
     trusted.
  2. NEW values from the same longitudes through the shared module `brahmagyan.gandanta`:
     canonical (3 deg 20 min) `graha_gandanta` rows; the `strict_0_48` variant rows.
  3. COUNT per chart x ayanamsha: canonical rows whose value changes / appear / disappear, variant
     rows added; `sensitive_degree_check.gandanta` rows that would change (expected 0).

Run:  cd platform/python-sidecar && PYTHONPATH=. python3 \
        ../../00_ARCHITECTURE/briefs/suvarna/exec/gandanta/offline_old_vs_new.py facts.json --out report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from brahmagyan.gandanta import check_gandanta, locate_gandanta, locate_gandanta_strict

CHARTS = {
    "482012f1-710e-4a25-994a-93821f5871aa": "canonical",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a": "abhinandan",
    "cb73cd3d-9eba-4220-9902-0de91566e980": "third",
}


def old_nakshatra(longitude: float) -> dict:
    """ga_nakshatra_compute.compute_gandanta as it was before I-22 (orb 48 arcmin), verbatim."""
    long_mod = longitude % 360.0
    best_dist = best_junction = best_side = None
    for jdeg in (0.0, 120.0, 240.0):
        d_approach = (jdeg - long_mod) % 360.0
        d_depart = (long_mod - jdeg) % 360.0
        for dist_deg, side in [(d_approach, "approaching"), (d_depart, "departing")]:
            dist_am = dist_deg * 60.0
            if dist_am <= 48.0:
                if best_dist is None or dist_am < best_dist:
                    best_dist, best_junction, best_side = dist_am, f"water_fire_{int(jdeg)}", side
    return {
        "is_gandanta": best_dist is not None,
        "arc_minutes_from_junction": round(best_dist, 2) if best_dist is not None else None,
        "junction_type": best_junction,
        "side": best_side,
    }


def new_canonical(longitude: float) -> dict:
    r = locate_gandanta(longitude)
    return {"is_gandanta": r["fired"], "arc_minutes_from_junction": r["arc_minutes_from_junction"],
            "junction_type": r["junction_type"], "side": r["side"]}


def new_strict(longitude: float) -> dict:
    r = locate_gandanta_strict(longitude)
    return {"is_gandanta": r["fired"], "arc_minutes_from_junction": r["arc_minutes_from_junction"],
            "junction_type": r["junction_type"], "side": r["side"]}


def rows_of(reading: dict) -> dict[str, object]:
    """The fact_key -> value rows a reading produces (is_gandanta always; detail only when true)."""
    out: dict[str, object] = {"is_gandanta": "true" if reading["is_gandanta"] else "false"}
    if reading["is_gandanta"]:
        out["arc_minutes_from_junction"] = reading["arc_minutes_from_junction"]
        out["junction_type"] = reading["junction_type"]
        out["side"] = reading["side"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("facts")
    ap.add_argument("--out")
    args = ap.parse_args()
    facts = json.load(open(args.facts, encoding="utf-8"))

    lon: dict[tuple, float] = {}
    stored_gg: dict[tuple, dict] = defaultdict(dict)      # (chart, ay, subject) -> key -> value
    stored_sd: dict[tuple, tuple] = {}                    # (chart, ay, subject) -> (text, num)
    stored_dosha = 0
    formula_rows_present = 0
    for f in facts:
        k = (f["chart_id"], f["ayanamsha_id"], f["fact_subject"])
        if f["fact_category"] == "graha_position" and f["fact_key"] == "longitude_sidereal":
            lon[k] = float(f["fact_value_num"])
        elif f["fact_category"] == "graha_gandanta":
            if f.get("formula_id"):
                formula_rows_present += 1
            val = f["fact_value_text"] if f["fact_value_text"] is not None else f["fact_value_num"]
            stored_gg[k][f["fact_key"]] = val
        elif f["fact_category"] == "sensitive_degree_check":
            stored_sd[k] = (f["fact_value_text"], f["fact_value_num"])
        elif f["fact_category"] == "dosha_fires":
            stored_dosha += 1

    report: dict = {"charts": {}, "stored_dosha_fires_gandanta_rows": stored_dosha,
                    "stored_graha_gandanta_variant_rows_already_present": formula_rows_present}
    recon_total = recon_bad = 0
    sd_total = sd_bad = 0
    detail_mismatches: list = []

    for chart_id, label in CHARTS.items():
        c = {"label": label, "by_ayanamsha": {}, "totals": defaultdict(int), "changed_subjects": []}
        ays = sorted({k[1] for k in lon if k[0] == chart_id})
        for ay in ays:
            a = defaultdict(int)
            subjects = sorted(s for (cid, y, s) in lon if cid == chart_id and y == ay)
            for s in subjects:
                key = (chart_id, ay, s)
                L = lon[key]
                old_calc = old_nakshatra(L)
                stored = stored_gg.get(key, {})
                # 1. reconstruction check against what is stored
                recon_total += 1
                want = rows_of(old_calc)
                got = {kk: stored.get(kk) for kk in want}
                if any(str(want[kk]) != str(got[kk]) and not (
                        isinstance(want[kk], float) and got[kk] is not None and abs(float(got[kk]) - want[kk]) < 0.011)
                        for kk in want) or set(stored) - set(want):
                    recon_bad += 1
                    detail_mismatches.append({"chart": label, "ay": ay, "subject": s, "lon": L,
                                              "reconstructed": want, "stored": stored})
                # 2. new canonical + strict
                new_c, new_s = new_canonical(L), new_strict(L)
                old_rows, new_rows = rows_of(old_calc), rows_of(new_c)
                # canonical is_gandanta value change
                if old_rows["is_gandanta"] != new_rows["is_gandanta"]:
                    a["is_gandanta_value_changes"] += 1
                    c["changed_subjects"].append({"ay": ay, "subject": s, "longitude": L,
                                                  "old_is_gandanta": old_rows["is_gandanta"],
                                                  "new_is_gandanta": new_rows["is_gandanta"],
                                                  "new_arc_minutes": new_c["arc_minutes_from_junction"],
                                                  "new_junction": new_c["junction_type"], "new_side": new_c["side"]})
                # detail rows: appear / disappear / value change
                for kk in ("arc_minutes_from_junction", "junction_type", "side"):
                    o, n = old_rows.get(kk), new_rows.get(kk)
                    if o is None and n is not None:
                        a["detail_rows_appear"] += 1
                    elif o is not None and n is None:
                        a["detail_rows_disappear"] += 1
                    elif o is not None and n is not None and o != n:
                        a["detail_rows_value_change"] += 1
                # variant rows (all new)
                srows = rows_of(new_s)
                a["variant_rows_added"] += len(srows)
                a["variant_is_gandanta_true"] += 1 if new_s["is_gandanta"] else 0
                # strict reading must reproduce the OLD stored reading
                if rows_of(new_s) != rows_of(old_calc):
                    a["strict_variant_differs_from_old_reading"] += 1
                a["canonical_true_new"] += 1 if new_c["is_gandanta"] else 0
                a["old_true"] += 1 if old_calc["is_gandanta"] else 0
                a["subjects"] += 1
                # sensitive_degree_check.gandanta: stored vs shared-module recomputation
                sk = stored_sd.get(key)
                if sk is not None:
                    sd_total += 1
                    sn, deg = int((L % 360.0) // 30.0) % 12, (L % 360.0) % 30.0
                    g = check_gandanta(sn, deg)
                    want_text = "gandanta" if g["fired"] else "not_gandanta"
                    if sk[0] != want_text:
                        sd_bad += 1
                        a["sensitive_degree_rows_that_would_change"] += 1
                    a["sensitive_degree_gandanta_stored"] += 1 if sk[0] == "gandanta" else 0
                    # the two L1 assets' agreement on the same (chart, ayanamsha, graha), old vs new
                    a["sensitive_vs_nakshatra_compared"] += 1
                    if old_calc["is_gandanta"] != (sk[0] == "gandanta"):
                        a["sensitive_vs_nakshatra_disagree_OLD"] += 1
                    if new_c["is_gandanta"] != (sk[0] == "gandanta"):
                        a["sensitive_vs_nakshatra_disagree_NEW"] += 1
            c["by_ayanamsha"][ay] = dict(a)
            for kk, vv in a.items():
                c["totals"][kk] += vv
        c["totals"] = dict(c["totals"])
        report["charts"][label] = c

    report["reconstruction_check"] = {
        "graha_gandanta_subject_readings_compared": recon_total,
        "mismatches_vs_stored": recon_bad,
        "mismatch_detail": detail_mismatches,
        "sensitive_degree_check_gandanta_rows_compared": sd_total,
        "sensitive_degree_check_rows_that_differ_from_shared_module": sd_bad,
    }
    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
