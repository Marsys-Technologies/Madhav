"""
dispatch_utkarsha_w63_authority_flip_abhinandan.py — GOCHARA-UTKARṢA W6.3 authority flip.

Flips kala_gochara_authority for Abhinandan Mohanty (1c826d5a) from the default
v1 corpus to the empirically-calibrated generation='3.0' corpus built in W6.1/W6.2.

GATE CRITERIA (all must be satisfied before running this script):
  W6.2 CONDITIONAL_PASS ✓ — kala_gochara_windows has 60 rows for Abhinandan
                             with generation='3.0' AND calibration_state='empirically_calibrated'
  gochara_v3_calibration populated ✓ — fit_run_id present (weights fitted)
  I1 invariant ✓ — v1 rows for Abhinandan still intact (>= 19000)

IDEMPOTENCY: If kala_gochara_authority already has a row for Abhinandan,
this script prints the current state and exits 0 (no-op).

POST-FLIP PROBE: After inserting the authority row, the script queries
kala_gochara_windows through the COALESCE serving filter and verifies
generation='3.0', calibration_state='empirically_calibrated', count=60.
If the probe fails, the INSERT is rolled back and the script exits 1.

Rollback: run dispatch_utkarsha_w63_rollback_abhinandan.py

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_utkarsha_w63_authority_flip_abhinandan.py
"""
from __future__ import annotations

import os
import sys

ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
EXPECTED_V3_COUNT = 60
I1_V1_FLOOR = 19000
FLIPPED_BY = "utkarsha-w63-conductor"
EVIDENCE_REF = "GOCHARA-UTKARSA-W6.2-CONDITIONAL_PASS"

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
        print("[W6.3 ERROR] DATABASE_URL not set. Check platform/.env.local or environment.", file=sys.stderr)
        sys.exit(1)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # ── Pre-flight 1: W6.2 gate — 60 v3 empirically_calibrated rows ──────────
    cur.execute(
        """SELECT count(*) AS n
           FROM kala_gochara_windows
           WHERE chart_id = %s
             AND generation = '3.0'
             AND calibration_state = 'empirically_calibrated'""",
        (ABHINANDAN_CHART_ID,),
    )
    v3_count = cur.fetchone()["n"]
    if v3_count < EXPECTED_V3_COUNT:
        print(
            f"[W6.3 ERROR] W6.2 gate FAIL: kala_gochara_windows has {v3_count} rows for Abhinandan "
            f"with generation='3.0' AND calibration_state='empirically_calibrated'. "
            f"Expected {EXPECTED_V3_COUNT}. Run W6.1 + W6.2 first.",
            file=sys.stderr,
        )
        conn.close()
        sys.exit(1)
    print(f"[W6.3] W6.2 gate: kala_gochara_windows v3 empirically_calibrated rows={v3_count} ✓", file=sys.stderr)

    # ── Pre-flight 2: gochara_v3_calibration has fitted rows ─────────────────
    cur.execute("SELECT count(*) AS n FROM gochara_v3_calibration WHERE fit_run_id IS NOT NULL")
    cal_count = cur.fetchone()["n"]
    if cal_count == 0:
        print(
            "[W6.3 ERROR] gochara_v3_calibration has no rows with fit_run_id. "
            "W4.5 post-fit rebuild must run before authority flip.",
            file=sys.stderr,
        )
        conn.close()
        sys.exit(1)
    print(f"[W6.3] gochara_v3_calibration: {cal_count} fitted rows (fit_run_id present) ✓", file=sys.stderr)

    # ── Pre-flight 3: idempotency check ──────────────────────────────────────
    cur.execute(
        """SELECT authoritative_generation, flipped_at, flipped_by
           FROM kala_gochara_authority
           WHERE chart_id = %s""",
        (ABHINANDAN_CHART_ID,),
    )
    existing = cur.fetchone()
    if existing is not None:
        print(
            f"[W6.3] kala_gochara_authority already has a row for Abhinandan ({ABHINANDAN_CHART_ID[:8]}…).\n"
            f"  authoritative_generation={existing['authoritative_generation']}\n"
            f"  flipped_at={existing['flipped_at']}\n"
            f"  flipped_by={existing['flipped_by']}\n"
            f"Authority flip already applied — no-op. Exiting 0."
        )
        conn.close()
        sys.exit(0)
    print("[W6.3] idempotency check: no existing authority row for Abhinandan ✓", file=sys.stderr)

    # ── Pre-flight 4: I1 guard — v1 rows still intact ────────────────────────
    cur.execute(
        """SELECT count(*) AS n
           FROM kala_gochara_windows
           WHERE chart_id = %s
             AND generation = 'v1'""",
        (ABHINANDAN_CHART_ID,),
    )
    v1_count = cur.fetchone()["n"]
    if v1_count < I1_V1_FLOOR:
        print(
            f"[W6.3 WARN] I1 rail: kala_gochara_windows v1 rows for Abhinandan = {v1_count} "
            f"(expected >= {I1_V1_FLOOR}). v1 corpus may have been damaged. "
            f"Proceeding, but investigate I1 violation before trusting rollback path.",
            file=sys.stderr,
        )
    else:
        print(f"[W6.3] I1 rail: kala_gochara_windows v1 rows={v1_count} (>= {I1_V1_FLOOR}) ✓", file=sys.stderr)

    # ── Authority flip ────────────────────────────────────────────────────────
    cur.execute(
        """INSERT INTO kala_gochara_authority
               (chart_id, authoritative_generation, flipped_at, flipped_by, evidence_ref)
           VALUES (%s, '3.0', now(), %s, %s)""",
        (ABHINANDAN_CHART_ID, FLIPPED_BY, EVIDENCE_REF),
    )
    print(
        f"[W6.3] INSERT kala_gochara_authority: chart_id={ABHINANDAN_CHART_ID[:8]}… "
        f"authoritative_generation='3.0' evidence_ref={EVIDENCE_REF}",
        file=sys.stderr,
    )

    # ── Post-flip probe via COALESCE serving filter ───────────────────────────
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
    probe_rows = cur.fetchall()

    probe_ok = (
        len(probe_rows) == 1
        and probe_rows[0]["generation"] == "3.0"
        and probe_rows[0]["calibration_state"] == "empirically_calibrated"
        and probe_rows[0]["n"] == EXPECTED_V3_COUNT
    )

    if not probe_ok:
        print(
            f"[W6.3 ERROR] Post-flip probe FAILED. Expected 1 row "
            f"(generation='3.0', calibration_state='empirically_calibrated', count={EXPECTED_V3_COUNT}). "
            f"Got: {probe_rows}. Rolling back INSERT.",
            file=sys.stderr,
        )
        conn.rollback()
        conn.close()
        sys.exit(1)

    r = probe_rows[0]
    print(
        f"[W6.3] Post-flip probe: generation={r['generation']} "
        f"calibration_state={r['calibration_state']} count={r['n']} ✓",
        file=sys.stderr,
    )

    conn.commit()
    conn.close()

    print(
        f"W6.3 AUTHORITY FLIP COMPLETE for Abhinandan ({ABHINANDAN_CHART_ID[:8]}…). "
        f"authoritative_generation='3.0'. "
        f"Rollback: run dispatch_utkarsha_w63_rollback_abhinandan.py"
    )


if __name__ == "__main__":
    main()
