#!/usr/bin/env python3
"""special_lagna_offset_check.py -- W7 hand-check for lane special_lagna_offset (PR #2971).

The flip detector cannot see three things this lane changes: the CONTINUOUS longitude delta, the
near_* boundary-flag columns and formula_provenance_text. This script reads (SELECT only, same reader
convention as flip_detector.py) the 245 `special_lagna` rows of ONE chart before the S-L1 rebuild and
after it, and fails on any deviation from what the lane declared for the CANONICAL chart:

  C1  row counts: 245 before and after, exactly one row per (ayanamsha, subject, key)
  C2  ZERO CHANGE: sign, sign_lord, house_d1, nakshatra, nakshatra_lord, pada on ALL 7 subjects
  C3  INDU/SREE/VARNADA: every key EXACTLY unchanged (value, flags, provenance text) EXCEPT the
      longitude_sidereal NUMBER, which may move only inside its own declared ephemeris band
      (LONGITUDE_BAND_DEG below; the Moshier -> .se1 move shifts these three by a measured, tiny amount).
      Class values (sign, sign_lord, house_d1, nakshatra, nakshatra_lord, pada), flags and provenance
      stay exact: the band never loosens a class check
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
Refuses to run unless the session reports transaction_read_only = on (PGOPTIONS requests it, a SHOW-equivalent query proves it,
for FLIP_READER and plain psql alike). The W7 run of this script is REQUIRED: the flip detector alone is not sufficient.
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
# C3 ephemeris bands (deg), ONE PER SUBJECT, no shared band. The S-L1 rebuild runs on the pinned Swiss .se1
# files; the stored rows were built on Moshier. INDU, SREE and VARNADA are not moved by the lane (class values
# and flags stay exact) but their longitude NUMBER inherits the backend's shift of the inputs. Evidence:
# /Users/Dev/suvarna-evidence/Ephemeris/SE1_SHIFT_ANALYSIS.md (sha256 22564b863fc7cb3713e5d4b5d88ca5dc7376532fd93a9faa6461c99689ac3403)
# section 3 (input shifts: Moon -0.6646..-0.6648 arcsec on all five ayanamshas; Lagna/MC/cusps 0, True Chitra
# -0.0001 arcsec) and /Users/Dev/suvarna-evidence/Ephemeris/SPECIAL_LAGNA_AYA_CHECK.md section 3b (measured on
# the canonical chart, linux/amd64, all five ayanamshas, Moshier vs .se1, full precision).
#   INDU_LAGNA  follows the Moon one-for-one (INDU = Moon - 90 deg in the stored data): the Moon's shift is
#               0.6648 arcsec = 1.847e-4 deg; measured -0.00018460 .. -0.00018467 deg on all five. Band
#               +/-0.00025 deg (1.35x the Moon's shift; 0.001 deg would be 5.4x too loose).
#   SREE_LAGNA  amplifies the Moon's shift x27 (SE1_SHIFT_ANALYSIS.md: "Sree Lagna (27 x Moon fraction)"):
#               0.6648 arcsec x 27 = 17.95 arcsec = 0.004986 deg; measured -0.004984 .. -0.004986 deg.
#               Band +/-0.0055 deg (1.10x). Its class keys stay exact (the analysis found no pada edge
#               crossed: nearest margin ~0.005 deg for true_chitra at 203.3525, edge 203.3333).
#   VARNADA     longitude = the Lagna's degree in its sign (the Varnada SIGN comes from the Lagna and Hora
#               signs, which do not change). The Lagna moves 0 on Lahiri/Krishnamurti/Raman and -0.0001
#               arcsec (2.8e-8 deg) on True Chitra/Surya Siddhanta (the ayanamsha value itself shifts
#               -0.0055 / -0.00004 arcsec); measured -2.65e-8 (true_chitra) and +1.15e-8 (surya_siddhanta)
#               deg, exactly 0.0 on the other three. Band +/-1e-7 deg (3.6x the Lagna shift).
# A move beyond a band, or any change of a class key / flag / provenance, FAILS C3.
# SCOPE (SS ruling 2026-10-03): these bands are derived at the CANONICAL chart's birth instant (482012f1) and are
# UNMEASURED for any other chart. In the S-L1 window C3 runs on 482012f1 ONLY; 1c826d5a and cb73cd3d are out of scope.
# Measuring the Moshier -> .se1 shift at each chart's own birth instant (offline, like SE1_SHIFT_ANALYSIS) is a
# PRECONDITION for any future rebuild of those charts; until then a failure of the banded check on another chart means
# "band not derived for this chart", not "the rebuild is wrong".
LONGITUDE_BAND_DEG = {"INDU_LAGNA": 0.00025, "SREE_LAGNA": 0.0055, "VARNADA_LAGNA": 1e-7}
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


_READ_ONLY_VERIFIED = False
_RO_PGOPTIONS = "-c default_transaction_read_only=on"


class NotReadOnly(RuntimeError):
    """The database session is not read-only: the script refuses to run any query."""


def _run(sql: str) -> list[list[str]]:
    env = dict(os.environ)
    # Ask the server for a read-only session on the plain-psql path (an operator's own PGOPTIONS is kept).
    env["PGOPTIONS"] = (env.get("PGOPTIONS", "") + " " + _RO_PGOPTIONS).strip()
    reader = os.environ.get("FLIP_READER")
    cmd = [reader, sql] if reader else ["psql", "-X", "-A", "-t", "-F", "\t", "-c", sql]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env).stdout
    return [line.split("\t") for line in out.splitlines() if line.strip()]


def assert_read_only() -> None:
    """Refuse unless the session reports transaction_read_only = on (verified once per process).
    Read-only must not depend on the operator's connection: PGOPTIONS asks for it, this proves it."""
    global _READ_ONLY_VERIFIED
    if _READ_ONLY_VERIFIED:
        return
    rows = _run("select current_setting('transaction_read_only')")
    if rows != [["on"]]:
        raise NotReadOnly(f"database session is not read-only (transaction_read_only={rows!r}); refusing to run")
    _READ_ONLY_VERIFIED = True


def _query(sql: str) -> list[list[str]]:
    assert re.match(r"^\s*select\b", sql, re.I) and ";" not in sql, "SELECT only"
    assert_read_only()
    return _run(sql)


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


def _longitude_band_failure(subject: str, before: str, after: str) -> str:
    """'' when the longitude of an unmoved subject is inside its declared ephemeris band, else a reason.
    Identical text passes (including both NULL); a NULL/non-numeric on one side only fails."""
    if before == after:
        return ""
    band = LONGITUDE_BAND_DEG[subject]
    try:
        d = _sdelta(float(before), float(after))
    except ValueError:
        return f"longitude not comparable ({before[:20]!r} -> {after[:20]!r})"
    if abs(d) > band:
        return (f"longitude moved {d:+.9f} deg, outside the declared ephemeris band +/-{band} deg "
                f"(Moshier -> .se1 shift, SE1_SHIFT_ANALYSIS.md)")
    return ""


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
                if col == "fact_value_num" and key == "longitude_sidereal":
                    msg = _longitude_band_failure(subj, b[col], a[col])
                    if msg:
                        fails.append(f"C3 {k}: {msg}")
                elif b[col] != a[col]:
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
            msg = _longitude_band_failure(subj, b["fact_value_num"], a["fact_value_num"])
            if msg:
                fails.append(f"C3 {k}: {msg} (bands are the canonical chart's; read the derivation at LONGITUDE_BAND_DEG)")
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
    try:
        return _main(argv)
    except NotReadOnly as exc:
        print(f"REFUSED: {exc}")
        return 2


def _main(argv: list[str]) -> int:
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
