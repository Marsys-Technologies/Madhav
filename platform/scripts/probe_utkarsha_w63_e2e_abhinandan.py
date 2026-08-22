"""
probe_utkarsha_w63_e2e_abhinandan.py — GOCHARA-UTKARṢA W6.3 E2E probe.

Probes the full serving stack for Abhinandan Mohanty (1c826d5a):
  1. Reads current authority state from kala_gochara_authority.
  2. Resolves authoritative_generation via COALESCE (mirrors production serving logic).
  3. Queries kala_gochara_windows through that filter.
  4. Verifies expected row counts for the active generation.
  5. Independently checks v1 corpus integrity (I1 rail).
  6. Prints a structured PASS/FAIL summary.

Expected outcomes:
  FLIPPED state  → 60 rows, generation='3.0', calibration_state='empirically_calibrated'
  DEFAULT state  → rows gen='v1' (I1 corpus intact)
  I1 rail        → v1 rows >= 19000 regardless of authority state

Usage:
  cd <repo-root>/platform
  python3 scripts/probe_utkarsha_w63_e2e_abhinandan.py
"""
from __future__ import annotations

import os
import sys

ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
EXPECTED_V3_COUNT = 60
EXPECTED_V3_GENERATION = "3.0"
EXPECTED_V3_CALIBRATION_STATE = "empirically_calibrated"
I1_V1_FLOOR = 19000

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[W6.3-PROBE ERROR] DATABASE_URL not set. Check platform/.env.local or environment.", file=sys.stderr)
        sys.exit(1)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = True  # read-only probe; no writes
    cur = conn.cursor()

    failures: list[str] = []

    # ── 1. Read authority state ───────────────────────────────────────────────
    cur.execute(
        """SELECT authoritative_generation, flipped_at, flipped_by
           FROM kala_gochara_authority
           WHERE chart_id = %s""",
        (ABHINANDAN_CHART_ID,),
    )
    authority_row = cur.fetchone()

    is_flipped = authority_row is not None
    authoritative_gen = authority_row["authoritative_generation"] if is_flipped else "v1"

    if is_flipped:
        authority_state_label = f"FLIPPED→{authoritative_gen}"
    else:
        authority_state_label = "DEFAULT→v1"

    # ── 2. Query served rows via COALESCE filter ──────────────────────────────
    cur.execute(
        """SELECT generation, calibration_state, count(*) AS n
           FROM kala_gochara_windows
           WHERE chart_id = %s
             AND generation = COALESCE(
                 (SELECT authoritative_generation
                  FROM kala_gochara_authority
                  WHERE chart_id = %s),
                 'v1'
             )
           GROUP BY generation, calibration_state""",
        (ABHINANDAN_CHART_ID, ABHINANDAN_CHART_ID),
    )
    served_rows = cur.fetchall()

    # Summarise served result
    if len(served_rows) == 1:
        served_gen = served_rows[0]["generation"]
        served_cal = served_rows[0]["calibration_state"]
        served_count = served_rows[0]["n"]
        served_summary = f"{served_count} (generation={served_gen}, calibration_state={served_cal})"
    elif len(served_rows) == 0:
        served_gen = None
        served_cal = None
        served_count = 0
        served_summary = "0 (no rows returned)"
    else:
        # Multiple groups — flatten for reporting
        served_gen = served_rows[0]["generation"]
        served_cal = "MIXED"
        served_count = sum(r["n"] for r in served_rows)
        served_summary = f"{served_count} across {len(served_rows)} groups (UNEXPECTED)"

    # ── 3. Verify served rows match expected state ────────────────────────────
    if is_flipped:
        # Expect 60 rows gen='3.0' empirically_calibrated
        if not (
            len(served_rows) == 1
            and served_gen == EXPECTED_V3_GENERATION
            and served_cal == EXPECTED_V3_CALIBRATION_STATE
            and served_count == EXPECTED_V3_COUNT
        ):
            failures.append(
                f"FLIPPED state probe FAIL: expected 1 group "
                f"(generation='{EXPECTED_V3_GENERATION}', "
                f"calibration_state='{EXPECTED_V3_CALIBRATION_STATE}', "
                f"count={EXPECTED_V3_COUNT}). "
                f"Got: {served_rows}"
            )
    else:
        # DEFAULT state — expect generation='v1' rows
        if not (len(served_rows) >= 1 and served_gen == "v1"):
            failures.append(
                f"DEFAULT state probe FAIL: expected generation='v1' rows via COALESCE fallback. "
                f"Got: {served_rows}"
            )

    # ── 4. I1 rail — v1 rows intact regardless of authority state ────────────
    cur.execute(
        """SELECT count(*) AS n
           FROM kala_gochara_windows
           WHERE chart_id = %s
             AND generation = 'v1'""",
        (ABHINANDAN_CHART_ID,),
    )
    v1_count = cur.fetchone()["n"]
    v1_intact = v1_count >= I1_V1_FLOOR

    if not v1_intact:
        failures.append(
            f"I1 rail FAIL: kala_gochara_windows v1 rows={v1_count} < floor {I1_V1_FLOOR}. "
            f"v1 corpus may have been damaged."
        )

    i1_label = f"{v1_count} (I1 rail {'✓' if v1_intact else 'FAIL — below floor'})"

    conn.close()

    # ── 5. Print structured summary ───────────────────────────────────────────
    probe_verdict = "PASS" if not failures else f"FAIL — {'; '.join(failures)}"

    print("E2E PROBE RESULT:")
    print(f"  authority_state:   {authority_state_label}")
    print(f"  served_rows:       {served_summary}")
    print(f"  v1_rows_intact:    {i1_label}")
    print(f"  probe_verdict:     {probe_verdict}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
