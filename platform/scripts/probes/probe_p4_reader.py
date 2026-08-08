#!/usr/bin/env python3
"""
probe_p4_reader.py — PRATIJÑĀ v4 Proof Ladder, Rung P4 (the Reader
acceptance gate).

Blocking gate before Lane B2 (the v4 engine). Per
PRATIJNA_V4_STATE.md / MASTER_PLAN_v1_0.md §5: "Reader answers ≡
probe_p2_tracer answers exactly, on both charts, plus non-empty fact_id
[provenance] per answer. GREEN before B2."

This probe re-derives probe_p2_tracer.py's three tracer questions
INDEPENDENTLY via `ChartReaderV4` (never by importing/re-using the probe's
own query code) and asserts byte-identical agreement with a FRESH live run
of probe_p2_tracer's own logic, on both canonical charts, plus non-empty
provenance on every Reader answer:

  (a) D1 occupants of house 7                (ChartReaderV4.occupants)
  (b) VEN's D9 sign                          (ChartReaderV4.sign_of — the
                                               Lane B1 API extension, see
                                               chart_reader_v4.py module
                                               docstring judgment call #2)
  (c) 7th lord and its D1 house              (ChartReaderV4.lord_of)

Usage: python3 probe_p4_reader.py
Requires DBURL (see probe_p1_identity.py header for the resolution
one-liner). Read-only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SIDECAR = REPO_ROOT / "platform" / "python-sidecar"
sys.path.insert(0, str(SIDECAR))

import psycopg  # noqa: E402
import psycopg.rows  # noqa: E402

from brahmagyan.chart_reader_v4 import ChartReaderV4, SIGN_LORD  # noqa: E402

CHARTS = {
    "482012f1": "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a": "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
}
AYANAMSHA = "lahiri_chitrapaksha"


def get_dburl() -> str:
    if os.environ.get("DBURL"):
        return os.environ["DBURL"]
    raise SystemExit("DBURL not set — see probe_p1_identity.py header for the resolution one-liner.")


def _sign_of_longitude(lon: float) -> int:
    return int(lon // 30) + 1


def _p2_seventh_lord(conn, chart_id: str) -> tuple[str, str]:
    """Independently reproduce probe_p2_tracer.py's own 7th-lord logic
    (direct SQL, NOT via the Reader) so this probe has a ground truth to
    compare the Reader's answer against that isn't just re-running the
    Reader against itself."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT graha, house FROM chart_divisionals
               WHERE chart_id=%s AND varga='D1' AND ayanamsha_id=%s
                 AND fact_category='varga_house_lord' AND house=7""",
            (chart_id, AYANAMSHA),
        )
        lord_row = cur.fetchone()
    if lord_row:
        return lord_row["graha"], "direct chart_divisionals.varga_house_lord row"
    with conn.cursor() as cur:
        cur.execute(
            """SELECT fact_value_num FROM chart_facts
               WHERE chart_id=%s AND fact_category='bhava_cusps' AND fact_subject='BHAVA_07'
                 AND fact_key='sripati_madhya' AND ayanamsha_id=%s""",
            (chart_id, AYANAMSHA),
        )
        madhya = cur.fetchone()["fact_value_num"]
    h7_sign = _sign_of_longitude(float(madhya))
    return SIGN_LORD[h7_sign], f"derived fallback via sripati_madhya={madhya}"


def main() -> int:
    dburl = get_dburl()
    conn = psycopg.connect(dburl, row_factory=psycopg.rows.dict_row)
    conn.read_only = True
    ok = True

    print("=" * 78)
    print("RUNG P4 — Chart Reader acceptance (Reader answers ≡ probe_p2_tracer, +provenance)")
    print("=" * 78)

    for label, chart_id in CHARTS.items():
        print(f"\n{'#' * 78}\n# CHART {label} ({chart_id})\n{'#' * 78}")
        reader = ChartReaderV4(conn, ayanamsha=AYANAMSHA)

        # ── (a) D1 occupants of house 7 ─────────────────────────────────
        reader_occ = reader.occupants(chart_id, house=7, varga="D1")
        reader_names = sorted(r["graha"] for r in reader_occ)

        with conn.cursor() as cur:
            cur.execute(
                """SELECT graha FROM chart_divisionals
                   WHERE chart_id=%s AND varga='D1' AND ayanamsha_id=%s
                     AND fact_category='varga_house_occupant' AND house=7
                   ORDER BY graha""",
                (chart_id, AYANAMSHA),
            )
            p2_names = [r["graha"] for r in cur.fetchall()]

        match_a = reader_names == p2_names
        prov_a_ok = all(r["provenance"] and r["provenance"][0]["id"] for r in reader_occ)
        ok = ok and match_a and prov_a_ok
        print(f"\n(a) D1 occupants of house 7:")
        print(f"    Reader:          {reader_names}")
        print(f"    probe_p2_tracer: {p2_names}")
        print(f"    MATCH: {match_a}  |  non-empty provenance on every row: {prov_a_ok}")
        for r in reader_occ:
            print(f"      {r['graha']}: provenance={r['provenance']}")

        # ── (b) VEN's D9 sign ────────────────────────────────────────────
        reader_sign = reader.sign_of(chart_id, "VEN", varga="D9")

        with conn.cursor() as cur:
            cur.execute(
                """SELECT DISTINCT sign, sign_number FROM chart_divisionals
                   WHERE chart_id=%s AND varga='D9' AND graha='Venus' AND ayanamsha_id=%s
                     AND fact_category='varga_position'""",
                (chart_id, AYANAMSHA),
            )
            p2_rows = cur.fetchall()
        p2_sign = p2_rows[0]["sign"] if len(p2_rows) == 1 else f"AMBIGUOUS: {p2_rows}"

        match_b = reader_sign["sign"] == p2_sign
        prov_b_ok = bool(reader_sign["provenance"] and reader_sign["provenance"][0]["id"])
        ok = ok and match_b and prov_b_ok
        print(f"\n(b) VEN's D9 sign:")
        print(f"    Reader:          {reader_sign['sign']} (sign_number={reader_sign['sign_number']})")
        print(f"    probe_p2_tracer: {p2_sign}")
        print(f"    MATCH: {match_b}  |  non-empty provenance: {prov_b_ok}")
        print(f"      provenance={reader_sign['provenance']}")

        # ── (c) 7th lord and its D1 house ────────────────────────────────
        reader_lord = reader.lord_of(chart_id, house=7, varga="D1")
        p2_lord, p2_lord_source = _p2_seventh_lord(conn, chart_id)

        match_c_lord = reader_lord["lord"] == p2_lord
        # Cross-check the lord's own D1 house against a direct query too.
        with conn.cursor() as cur:
            cur.execute(
                """SELECT house FROM chart_divisionals
                   WHERE chart_id=%s AND varga='D1' AND graha=%s AND ayanamsha_id=%s
                     AND fact_category='varga_house_occupant'""",
                (chart_id, p2_lord, AYANAMSHA),
            )
            p2_lord_house_row = cur.fetchone()
        p2_lord_house = p2_lord_house_row["house"] if p2_lord_house_row else None
        match_c_house = reader_lord["lord_own_house"] == p2_lord_house
        prov_c_ok = bool(reader_lord["provenance"]) and all(p["id"] for p in reader_lord["provenance"])

        ok = ok and match_c_lord and match_c_house and prov_c_ok
        print(f"\n(c) 7th lord and its D1 house:")
        print(f"    Reader:          lord={reader_lord['lord']}, house={reader_lord['lord_own_house']}")
        print(f"    probe_p2_tracer: lord={p2_lord} ({p2_lord_source}), house={p2_lord_house}")
        print(f"    MATCH (lord): {match_c_lord}  MATCH (house): {match_c_house}  "
              f"|  non-empty provenance: {prov_c_ok}")
        print(f"      dignity_state={reader_lord['dignity_state']!r}, source={reader_lord['source']}")
        for p in reader_lord["provenance"]:
            print(f"      provenance={p}")

    conn.close()
    print("\n" + "=" * 78)
    print(f"RUNG P4 RESULT: {'PASS' if ok else 'FAIL'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
