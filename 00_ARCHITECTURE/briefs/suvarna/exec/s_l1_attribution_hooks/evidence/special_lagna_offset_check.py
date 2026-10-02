#!/usr/bin/env python3
"""special_lagna_offset_check.py -- W7 hand-check for lane special_lagna_offset (PR #2971).

The flip detector cannot see three things this lane changes: the CONTINUOUS longitude delta, the
near_* boundary-flag columns and formula_provenance_text. This script reads (SELECT only, same reader
convention as flip_detector.py) the 245 `special_lagna` rows of ONE chart before the S-L1 rebuild and
after it, and fails on any deviation from what the lane declared for the CANONICAL chart:

  C1  row counts: 245 before and after, exactly one row per (ayanamsha, subject, key)
  C2  ZERO CHANGE: sign, sign_lord, house_d1, nakshatra, nakshatra_lord, pada on ALL 7 subjects
  C3  ZERO CHANGE: INDU/SREE/VARNADA every key (value, flags, provenance text)
  C4  longitude_sidereal of BHAVA/GHATI/HORA/VIGHATI x 5 ayanamshas (20 rows): delta == -0.23243 deg
      within +/-0.001 deg (the Sun's motion over the +5.5 h timezone offset on the birth date)
  C5  near_nakshatra_boundary_flag flips on exactly 5 points x 7 keys, in the declared direction;
      near_sign_boundary_flag and vargottama_flag_at_point never change
  C6  formula_provenance_text changed on all 140 rows of the 4 subjects, unchanged on the other 105

Usage (read-only; FLIP_READER = executable taking the SQL as argv[1], tab-separated rows, no header):
  special_lagna_offset_check.py --snapshot <chart-uuid> [--out snapshot.json]
  special_lagna_offset_check.py --compare  snapshot.json <chart-uuid>     # exit 0 pass, 2 fail
Only the CANONICAL chart has a computed expectation; for any other chart --compare runs C1 and C3 plus
a |delta| <= 1 deg sanity bound and PRINTS (never fails) the class changes for review.
Stores derived chart facts only (no birth data). The snapshot file is evidence: keep it OUTSIDE the repo.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

CANONICAL = "482012f1-710e-4a25-994a-93821f5871aa"
MOVED = ("BHAVA_LAGNA", "GHATI_LAGNA", "HORA_LAGNA", "VIGHATI_LAGNA")
STILL = ("INDU_LAGNA", "SREE_LAGNA", "VARNADA_LAGNA")
CLASS_KEYS = ("sign", "sign_lord", "house_d1", "nakshatra", "nakshatra_lord", "pada")
ALL_KEYS = CLASS_KEYS + ("longitude_sidereal",)
EXPECTED_DELTA_DEG = -0.23243
DELTA_TOL_DEG = 0.001
# (subject, ayanamsha) -> (before, after) of near_nakshatra_boundary_flag on all 7 keys
EXPECTED_NAK_FLAG_FLIPS = {
    ("BHAVA_LAGNA", "surya_siddhanta_classical"): ("t", "f"),
    ("GHATI_LAGNA", "krishnamurti"): ("f", "t"),
    ("GHATI_LAGNA", "lahiri_chitrapaksha"): ("f", "t"),
    ("GHATI_LAGNA", "true_chitra"): ("f", "t"),
    ("VIGHATI_LAGNA", "raman"): ("t", "f"),
}
COLS = ("ayanamsha_id", "fact_subject", "fact_key", "fact_value_text", "fact_value_num",
        "near_sign_boundary_flag", "near_nakshatra_boundary_flag", "vargottama_flag_at_point",
        "formula_provenance_text")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _query(sql: str) -> list[list[str]]:
    assert re.match(r"^\s*select\b", sql, re.I) and ";" not in sql, "SELECT only"
    reader = os.environ.get("FLIP_READER")
    cmd = [reader, sql] if reader else ["psql", "-X", "-A", "-t", "-F", "\t", "-c", sql]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    return [line.split("\t") for line in out.splitlines() if line.strip()]


def read_rows(chart_id: str) -> list[dict]:
    chart_id = chart_id.strip().lower()
    assert _UUID.match(chart_id), "chart id must be a UUID"
    sql = ("select ayanamsha_id, fact_subject, fact_key, coalesce(fact_value_text,''), "
           "coalesce(fact_value_num::text,''), near_sign_boundary_flag::text, "
           "near_nakshatra_boundary_flag::text, vargottama_flag_at_point::text, "
           "replace(replace(coalesce(formula_provenance_text,''), E'\\t', ' '), E'\\n', ' ') "
           f"from chart_facts where chart_id='{chart_id}' and fact_category='special_lagna'")
    return [dict(zip(COLS, r + [""] * (len(COLS) - len(r)))) for r in _query(sql)]


def _index(rows):
    out = {}
    for r in rows:
        k = (r["ayanamsha_id"], r["fact_subject"], r["fact_key"])
        out.setdefault(k, []).append(r)
    return out


def _flag(v):
    return {"true": "t", "t": "t", "false": "f", "f": "f"}.get(v.lower(), v)


def _sdelta(a: float, b: float) -> float:
    return ((b - a + 180.0) % 360.0) - 180.0


def check_states(before: list[dict], after: list[dict], chart_id: str = CANONICAL) -> dict:
    """Pure function. Returns {"failures": [...], "info": [...]}; empty failures == pass."""
    canonical = chart_id.strip().lower() == CANONICAL
    fails, info = [], []
    bi, ai = _index(before), _index(after)
    for label, idx in (("before", bi), ("after", ai)):
        if len(before if label == "before" else after) != 245:
            fails.append(f"C1 {label}: {len(before if label == 'before' else after)} special_lagna rows, expected 245")
        dup = [k for k, v in idx.items() if len(v) != 1]
        if dup:
            fails.append(f"C1 {label}: {len(dup)} (ayanamsha, subject, key) with !=1 row, e.g. {dup[0]}")
    if set(bi) != set(ai):
        fails.append(f"C1 key set differs: {len(set(bi) - set(ai))} disappeared, {len(set(ai) - set(bi))} appeared")
    common = sorted(set(bi) & set(ai))
    one = lambda idx, k: idx[k][0]  # noqa: E731

    def val(r):
        return (r["fact_value_text"], r["fact_value_num"])

    for k in common:
        b, a = one(bi, k), one(ai, k)
        aya, subj, key = k
        if subj in STILL and canonical:  # C3
            for col in COLS[3:]:
                if b[col] != a[col]:
                    fails.append(f"C3 {k}: {col} changed ({b[col][:40]!r} -> {a[col][:40]!r})")
        if key in CLASS_KEYS and val(b) != val(a):
            msg = f"C2 {k}: class value changed {val(b)} -> {val(a)}"
            (fails if canonical else info).append(msg)
        if subj in MOVED and key == "longitude_sidereal":  # C4
            try:
                d = _sdelta(float(b["fact_value_num"]), float(a["fact_value_num"]))
            except ValueError:
                fails.append(f"C4 {k}: non-numeric longitude")
                continue
            if canonical and abs(d - EXPECTED_DELTA_DEG) > DELTA_TOL_DEG:
                fails.append(f"C4 {k}: delta {d:+.5f} deg, expected {EXPECTED_DELTA_DEG:+.5f} +/- {DELTA_TOL_DEG}")
            if not canonical and abs(d) > 1.0:
                fails.append(f"C4 {k}: |delta| {abs(d):.4f} deg exceeds the 1 deg sanity bound")
        if subj in STILL and key == "longitude_sidereal" and not canonical:
            if b["fact_value_num"] != a["fact_value_num"]:
                fails.append(f"C3 {k}: longitude of a non-moved subject changed")
        if canonical:  # C5 / C6
            if _flag(b["near_sign_boundary_flag"]) != _flag(a["near_sign_boundary_flag"]):
                fails.append(f"C5 {k}: near_sign_boundary_flag changed")
            if _flag(b["vargottama_flag_at_point"]) != _flag(a["vargottama_flag_at_point"]):
                fails.append(f"C5 {k}: vargottama_flag_at_point changed")
            exp = EXPECTED_NAK_FLAG_FLIPS.get((subj, aya))
            bf, af = _flag(b["near_nakshatra_boundary_flag"]), _flag(a["near_nakshatra_boundary_flag"])
            if exp:
                if (bf, af) != exp:
                    fails.append(f"C5 {k}: near_nakshatra_boundary_flag {bf}->{af}, expected {exp[0]}->{exp[1]}")
            elif bf != af:
                fails.append(f"C5 {k}: near_nakshatra_boundary_flag changed {bf}->{af} on an undeclared point")
            changed_prov = b["formula_provenance_text"] != a["formula_provenance_text"]
            if subj in MOVED and not changed_prov:
                fails.append(f"C6 {k}: formula_provenance_text unchanged (expected the corrected citation)")
            if subj in STILL and changed_prov:
                fails.append(f"C6 {k}: formula_provenance_text changed on an unmoved subject")
    return {"failures": fails, "info": info, "rows_compared": len(common)}


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "--snapshot":
        rows = read_rows(argv[1])
        out = argv[argv.index("--out") + 1] if "--out" in argv else f"special_lagna_{argv[1][:8]}.json"
        json.dump({"chart_id": argv[1].lower(), "rows": rows}, open(out, "w"))
        print(f"snapshot: {len(rows)} special_lagna rows -> {out}")
        return 0 if len(rows) == 245 else 2
    if len(argv) == 3 and argv[0] == "--compare":
        snap = json.load(open(argv[1]))
        chart = argv[2]
        if snap["chart_id"] != chart.lower():
            print(f"snapshot is for {snap['chart_id']}, not {chart}")
            return 2
        res = check_states(snap["rows"], read_rows(chart), chart)
        for line in res["info"]:
            print("INFO", line)
        for line in res["failures"]:
            print("FAIL", line)
        print(f"{'FAIL' if res['failures'] else 'PASS'}: {len(res['failures'])} failure(s), {res['rows_compared']} rows compared")
        return 2 if res["failures"] else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
