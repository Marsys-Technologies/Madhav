"""FORENSIC 7/7 gate for the Elevation Campaign β.D rebuild.

Queries the 7 birth anchors for a canonical chart and compares to the frozen
baseline captured pre-rebuild. Exits 0 on 7/7 PASS, 1 on any mismatch. The β.D
writers (ga_sensitive/ga_structural/ga_vargas) produce none of these anchors, so
a mismatch would indicate an unexpected side effect and MUST halt the rebuild.

USAGE
  DATABASE_URL=... python forensic_check_elev_beta_d.py <chart_id>
"""
from __future__ import annotations

import os
import sys

EXPECTED = {
    "482012f1-710e-4a25-994a-93821f5871aa": {
        "sun_sign": "Capricorn", "moon_nakshatra": "Purva Bhadrapada",
        "tithi": "Shukla Tritiya", "vara": "Ravivara", "yoga": "Shiva",
        "karana": "Garaja", "lagna_all5": "Aries",
    },
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a": {
        "sun_sign": "Aquarius", "moon_nakshatra": "Ardra",
        "tithi": "Shukla Dashami", "vara": "Shanivara", "yoga": "Ayushman",
        "karana": "Garaja", "lagna_all5": "Aries",
    },
}


def main() -> None:
    chart_id = sys.argv[1]
    exp = EXPECTED.get(chart_id)
    if exp is None:
        print(f"FORENSIC: no baseline for chart {chart_id}"); sys.exit(1)

    import psycopg
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    def one(sql, args=()):
        cur.execute(sql, args)
        r = cur.fetchone()
        return r[0] if r else None

    got = {}
    got["sun_sign"] = one(
        "SELECT fact_value_text FROM chart_facts WHERE chart_id=%s AND ayanamsha_id='lahiri_chitrapaksha'"
        " AND fact_category='graha_position' AND fact_subject='SUN' AND fact_key='sign'", (chart_id,))
    got["moon_nakshatra"] = one(
        "SELECT fact_value_text FROM chart_facts WHERE chart_id=%s AND ayanamsha_id='lahiri_chitrapaksha'"
        " AND fact_category='graha_position' AND fact_subject='MOON' AND fact_key='nakshatra'", (chart_id,))
    got["tithi"] = one(
        "SELECT fact_value_text FROM chart_facts WHERE chart_id=%s AND fact_category='panchanga_tithi' AND fact_key='name'", (chart_id,))
    got["vara"] = one(
        "SELECT fact_value_text FROM chart_facts WHERE chart_id=%s AND fact_category='panchanga_vara' AND fact_key='name'", (chart_id,))
    got["yoga"] = one(
        "SELECT fact_value_text FROM chart_facts WHERE chart_id=%s AND fact_category='panchanga_yoga' AND fact_key='name'", (chart_id,))
    got["karana"] = one(
        "SELECT fact_value_text FROM chart_facts WHERE chart_id=%s AND fact_category='panchanga_karana' AND fact_key='name'", (chart_id,))
    # Lagna sign across all 5 ayanamshas must all equal the expected sign.
    cur.execute(
        "SELECT DISTINCT ayanamsha_id, fact_value_text FROM chart_facts WHERE chart_id=%s"
        " AND fact_category='graha_position' AND fact_subject='LAGNA' AND fact_key='sign'"
        " AND ayanamsha_id != 'INVARIANT'", (chart_id,))
    lagna_rows = cur.fetchall()
    lagna_signs = {r[1] for r in lagna_rows}
    conn.close()

    fails = []
    for k in ("sun_sign", "moon_nakshatra", "tithi", "vara", "yoga", "karana"):
        if got[k] != exp[k]:
            fails.append(f"{k}: got {got[k]!r} expected {exp[k]!r}")
    n_ayan = len(lagna_rows)
    if lagna_signs != {exp["lagna_all5"]}:
        fails.append(f"lagna: signs {lagna_signs} across {n_ayan} ayanamshas, expected all {exp['lagna_all5']!r}")

    anchors_ok = 7 - len(fails)
    print(f"FORENSIC chart {chart_id}: {anchors_ok}/7 anchors")
    for k in ("sun_sign", "moon_nakshatra", "tithi", "vara", "yoga", "karana"):
        print(f"  {k} = {got[k]}")
    print(f"  lagna = {sorted(lagna_signs)} across {n_ayan} ayanamsha rows")
    if fails:
        print("FORENSIC FAIL:")
        for f in fails:
            print(f"  ✗ {f}")
        sys.exit(1)
    print("FORENSIC 7/7 PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
