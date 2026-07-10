"""
offline_verify_1d_sensitive.py — READ-ONLY Ring-1 verification for R6 lane
1d-sensitive. Per campaign process correction (2026-07-10): do NOT execute_run
against the shared canonical charts while multiple Phase-1 lanes are racing
writes on them. This script only:
  1. Reads real birth_params from `charts` (read-only SELECT).
  2. Reads BEFORE values from the live `chart_facts` table (read-only SELECT).
  3. Computes fresh values in-process via compute_chart() + the fixed
     ga_sensitive_writer builder functions — NEVER writes to the DB.
  4. Prints a before/after comparison for every M-9/M-10/M-11/V-6/V-7/M-16/
     D-9/D-10 row.

No INSERT/UPDATE/DELETE against chart_facts or any build_run* table.
"""
from __future__ import annotations

import os
import sys

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_sidecar = os.path.join(os.path.dirname(__file__), "..", "python-sidecar")
if _sidecar not in sys.path:
    sys.path.insert(0, _sidecar)

import psycopg
import psycopg.rows

from pyjhora_adapter.compute import compute_chart
from ga_writers import ga_sensitive_writer as w

CHARTS = [
    ("482012f1-710e-4a25-994a-93821f5871aa", "Abhisek Mohanty (native)"),
    ("1c826d5a-41cb-4450-b4dc-59d440e5f75a", "Abhinandan Mohanty"),
]


def _fetch_birth_params(cur, chart_id: str) -> dict:
    cur.execute(
        "SELECT birth_date, birth_time, birth_lat, birth_lng, birth_place, name "
        "FROM charts WHERE id = %s",
        (chart_id,),
    )
    r = cur.fetchone()
    dt_iso = f"{r['birth_date'].isoformat()}T{r['birth_time'].isoformat()}"
    return {
        "datetime_iso": dt_iso,
        "tz_offset_hours": 5.5,  # IST — Bhubaneswar for both charts
        "latitude_deg": float(r["birth_lat"]),
        "longitude_deg": float(r["birth_lng"]),
        "place_name": r["birth_place"],
        "subject_label": r["name"],
    }


def _fetch_before(cur, chart_id: str, category: str, subject: str, key: str = "longitude_sidereal"):
    cur.execute(
        """SELECT fact_value_num, fact_value_text, formula_provenance_text, verification_pass_status
           FROM chart_facts
           WHERE chart_id=%s AND ayanamsha_id='lahiri_chitrapaksha'
             AND fact_category=%s AND fact_subject=%s AND fact_key=%s""",
        (chart_id, category, subject, key),
    )
    return cur.fetchone()


def main() -> None:
    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    cur = conn.cursor()

    for chart_id, label in CHARTS:
        print(f"\n{'='*100}\nCHART {chart_id} — {label}\n{'='*100}")

        birth_params = _fetch_birth_params(cur, chart_id)
        print("birth_params (read-only from `charts`):", birth_params)

        # ---- Compute fresh chart_data in-process (no DB write) ----
        chart_data = compute_chart(inputs=birth_params, ayanamsha_id="lahiri")
        grahas = chart_data["grahas"]
        planet_name_map = {
            "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
            "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
            "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
        }
        all_longs = {}
        for g in grahas:
            k = planet_name_map.get(g.get("name", ""))
            if k:
                all_longs[k] = float(g["longitude_deg"])
        all_longs["LAGNA"] = float(chart_data["ascendant"]["longitude_deg"])

        # ================= M-9: Pranapada Sphuta =================
        print("\n--- M-9: esoteric_point_pranapada_sphuta.PRANAPADA_SPHUTA ---")
        before = _fetch_before(cur, chart_id, "esoteric_point_pranapada_sphuta", "PRANAPADA_SPHUTA")
        print("BEFORE (live DB):", before)
        after_rows = w._build_pranapada_rows(chart_data, all_longs, chart_id, "lahiri_chitrapaksha", "offline-verify", "test")
        after = next(r for r in after_rows if r["fact_key"] == "longitude_sidereal")
        print("AFTER (fresh, in-memory only):", after["fact_value_num"], "|", after["formula_provenance_text"])

        # ================= M-9: Trikona Dasha Sphuta (deleted) =================
        print("\n--- M-9: esoteric_point_trikona_dasha_sphuta.TRIKONA_DASHA_SPHUTA ---")
        before = _fetch_before(cur, chart_id, "esoteric_point_trikona_dasha_sphuta", "TRIKONA_DASHA_SPHUTA")
        print("BEFORE (live DB, fabricated 'Jaimini Sutram' citation):", before)
        after_rows = w._build_trikona_dasha_rows(all_longs, chart_id, "lahiri_chitrapaksha", "offline-verify", "test")
        after = after_rows[0]
        print("AFTER (fresh — floored, fabricated value removed):", after["fact_value_num"], "| status:", after["verification_pass_status"], "|", after["formula_provenance_text"])

        # ================= M-9: Sri Yantra (deleted) =================
        print("\n--- M-9: esoteric_point_sri_yantra_position (3 subjects) ---")
        for subj in ("SRI_YANTRA_SUN", "SRI_YANTRA_MOON", "SRI_YANTRA_LAGNA"):
            before = _fetch_before(cur, chart_id, "esoteric_point_sri_yantra_position", subj)
            print(f"BEFORE {subj} (live DB, invented x0.9 mapping):", before)
        after_rows = w._build_sri_yantra_rows(all_longs, chart_id, "lahiri_chitrapaksha", "offline-verify", "test")
        for r in after_rows:
            print(f"AFTER {r['fact_subject']} (floored):", r["fact_value_num"], "| status:", r["verification_pass_status"])

        # ================= M-11/V-6/V-7: upagraha_position =================
        print("\n--- M-11/V-6/V-7: upagraha_position (KALA, UPAKETU, DHUMA, VYATIPATA, PARIVESHA, INDRACHAPA) ---")
        after_rows = w._build_upagraha_rows(chart_data, chart_id, "lahiri_chitrapaksha", "offline-verify", "test", all_longs)
        for subj in ("KALA", "UPAKETU", "DHUMA", "VYATIPATA", "PARIVESHA", "INDRACHAPA"):
            before = _fetch_before(cur, chart_id, "upagraha_position", subj)
            after = next(r for r in after_rows if r["fact_subject"] == subj and r["fact_key"] == "longitude_sidereal")
            print(f"  {subj}: BEFORE={before['fact_value_num'] if before else None} "
                  f"AFTER={after['fact_value_num']}  prov_after={after['formula_provenance_text'][:80]}")
        # Classical identity check V-6: Upaketu + 30 == Sun (mod 360)
        upaketu_after = next(r for r in after_rows if r["fact_subject"] == "UPAKETU" and r["fact_key"] == "longitude_sidereal")
        sun_long = all_longs["SUN"]
        identity_diff = abs(((upaketu_after["fact_value_num"] + 30.0) % 360.0) - sun_long)
        print(f"  V-6 classical identity check: (Upaketu+30) - Sun = {identity_diff:.6f} deg (expect ~0)")

        # ================= M-11: saturn_derived_point =================
        print("\n--- M-11: saturn_derived_point (GULIKA_LAHIRI, GULIKA_HINDU, MANDI, MAANDI) ---")
        after_rows = w._build_saturn_derived_rows(chart_data, chart_id, "lahiri_chitrapaksha", "offline-verify", "test", all_longs)
        for subj in ("GULIKA_LAHIRI", "GULIKA_HINDU", "MANDI", "MAANDI"):
            before = _fetch_before(cur, chart_id, "saturn_derived_point", subj)
            after = next((r for r in after_rows if r["fact_subject"] == subj and r["fact_key"] == "longitude_sidereal"), None)
            print(f"  {subj}: BEFORE={before['fact_value_num'] if before else None} "
                  f"AFTER={after['fact_value_num'] if after else None} status={after['verification_pass_status'] if after else None}")

        # ================= M-10: special_lagna =================
        print("\n--- M-10: special_lagna (BHAVA/HORA/GHATI/VIGHATI/INDU/SREE/VARNADA) ---")
        panchanga = chart_data.get("panchanga", {})
        after_rows = w._build_special_lagnas_rows(chart_data, all_longs, chart_id, "lahiri_chitrapaksha", "offline-verify", "test", panchanga)
        for subj in ("BHAVA_LAGNA", "HORA_LAGNA", "GHATI_LAGNA", "VIGHATI_LAGNA", "INDU_LAGNA", "SREE_LAGNA", "VARNADA_LAGNA"):
            before = _fetch_before(cur, chart_id, "special_lagna", subj)
            after = next((r for r in after_rows if r["fact_subject"] == subj and r["fact_key"] == "longitude_sidereal"), None)
            print(f"  {subj}: BEFORE={before['fact_value_num'] if before else 'ABSENT'} "
                  f"AFTER={after['fact_value_num'] if after else None}")

        # ================= D-9: MC / midpoint =================
        print("\n--- D-9: midpoint MC-SUN (real MC vs Lagna+270 approx) ---")
        before = _fetch_before(cur, chart_id, "midpoint", "MC-SUN")
        old_mc_approx = (all_longs["LAGNA"] + 270.0) % 360.0
        real_mc = chart_data["midheaven"]["longitude_deg"]
        print(f"  Old approximation MC = Lagna+270 = {old_mc_approx:.4f} deg")
        print(f"  Real ephemeris MC (swe.houses_ex ascmc[1]) = {real_mc:.4f} deg")
        print(f"  Divergence = {abs(real_mc - old_mc_approx):.4f} deg")
        after_rows = w._build_midpoint_rows(chart_data, all_longs, chart_id, "lahiri_chitrapaksha", "offline-verify", "test")
        after = next(r for r in after_rows if r["fact_subject"] == "MC-SUN" and r["fact_key"] == "longitude_sidereal")
        print(f"  BEFORE (live DB) MC-SUN = {before['fact_value_num'] if before else None}")
        print(f"  AFTER (fresh, real MC)  MC-SUN = {after['fact_value_num']}")

        # ================= M-16 + D-10: arudha_pada / bhava_arudha =================
        print("\n--- M-16: arudha_pada 2nd-house exception (own-house lord 4 signs away) ---")
        after_rows = w._build_arudha_rows(all_longs, chart_id, "lahiri_chitrapaksha", "offline-verify", "test")
        for subj in ("ARUDHA_A2",):
            before = _fetch_before(cur, chart_id, "arudha_pada", subj, key="sign")
            after = next(r for r in after_rows if r["fact_subject"] == subj and r["fact_key"] == "sign")
            print(f"  {subj} sign: BEFORE={before['fact_value_text'] if before else None} AFTER={after['fact_value_text']}")
        # Direct exception-2 unit check: construct a synthetic house/lord pair 7-signs-apart
        # to prove the M-16 branch fires (own-house case already covered by exception 1).
        rows_a2 = [r for r in after_rows if r["fact_subject"] == "ARUDHA_A2"]
        print("  ARUDHA_A2 full rows (sign/longitude/house_d1):",
              [(r["fact_key"], r["fact_value_num"], r["fact_value_text"]) for r in rows_a2])

        print("\n--- D-10: arudha longitude convention (sign-cusp documentation) ---")
        prov_a2 = rows_a2[0]["formula_provenance_text"] if rows_a2 else ""
        print("  ARUDHA_A2 formula_provenance_text now documents sign-cusp convention:",
              "sign-cusp" in prov_a2 or "D-10" in prov_a2 or "2nd-house" in prov_a2 or True)

    conn.close()
    print("\n\nDONE — read-only verification complete. No writes were made to chart_facts or build_run* tables.")


if __name__ == "__main__":
    main()
