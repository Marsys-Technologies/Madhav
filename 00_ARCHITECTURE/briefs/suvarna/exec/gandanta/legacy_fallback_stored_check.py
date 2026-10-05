#!/usr/bin/env python3
"""Read-only check: can the raising legacy dosha fallback in ga_structural throw on data that exists today?

Reconstructs, for each of the three charts x five ayanamshas, the `chart_output` the writer would
hand `_build_dosha_rows` (grahas with `name`, `longitude` = stored sidereal longitude, whole-sign
`house`, `sign`; ascendant `sign_id`) from the STORED `graha_position` facts (SELECT-only dump, see
offline_old_vs_new.py for the dump's columns), and runs the REAL legacy path
(`dosha_catalog=None`) end to end with a stub connection. Reports every (chart, ayanamsha) that raises.

Run from platform/python-sidecar:  PYTHONPATH=. python3 <this file> facts.json
"""
import json
import sys
from unittest.mock import MagicMock

from ga_writers import ga_structural_writer as struct

CHARTS = {"482012f1-710e-4a25-994a-93821f5871aa": "canonical",
          "1c826d5a-41cb-4450-b4dc-59d440e5f75a": "abhinandan",
          "cb73cd3d-9eba-4220-9902-0de91566e980": "third"}
NAMES = {"SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury", "JUP": "Jupiter",
         "VEN": "Venus", "SAT": "Saturn", "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu"}
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def main() -> int:
    facts = json.load(open(sys.argv[1], encoding="utf-8"))
    lon = {}
    for f in facts:
        if f["fact_category"] == "graha_position" and f["fact_key"] == "longitude_sidereal":
            lon[(f["chart_id"], f["ayanamsha_id"], f["fact_subject"])] = float(f["fact_value_num"])
    ran = failed = 0
    fired_rows = []
    for chart_id, label in CHARTS.items():
        for ay in sorted({k[1] for k in lon if k[0] == chart_id}):
            lagna = lon[(chart_id, ay, "LAGNA")]
            lsign = int((lagna % 360) // 30) % 12
            grahas = []
            for subj, name in NAMES.items():
                L = lon[(chart_id, ay, subj)]
                sn = int((L % 360) // 30) % 12
                grahas.append({"name": name, "longitude": L, "house": (sn - lsign) % 12 + 1, "sign": SIGNS[sn]})
            chart_output = {"grahas": grahas, "ascendant": {"longitude": lagna, "sign": SIGNS[lsign],
                                                            "sign_id": lsign + 1}}
            ran += 1
            try:
                rows = struct._build_dosha_rows(MagicMock(), chart_output, chart_id, "b", ay,
                                                "2026-10-02T00:00:00+00:00", "check", dosha_catalog=None)
                fired_rows += [(label, ay, r["fact_subject"]) for r in rows
                               if r["fact_subject"] in ("GANDANTA_DOSHA", "MRITYU_BHAGA_DOSHA")]
            except Exception as exc:  # report, do not hide
                failed += 1
                print("RAISED", label, ay, type(exc).__name__, exc)
    print(f"legacy fallback run on {ran} (chart x ayanamsha) reconstructions: {failed} raised")
    print("GANDANTA/MRITYU dosha_fires rows produced:", fired_rows)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
