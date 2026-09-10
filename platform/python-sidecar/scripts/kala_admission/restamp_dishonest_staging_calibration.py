#!/usr/bin/env python3
"""
restamp_dishonest_staging_calibration.py -- PARIṢKĀRA MR-37(b) audited restamp.

CONTEXT
-------
MR-37 found w45_post_fit_rebuild.py's §N.8 calibration-stamping gate checked
row EXISTENCE in gochara_v3_calibration, not EARNED signal (a genuinely
non-zero weight from an engine-wired mechanism). Before the gate was fixed
(this same PR), the unsound gate had already fired for real, at least once,
via an out-of-band mechanism: 107 rows in the staging surface
(kala_gochara_windows_v2, era_slice_key LIKE 'g3_%') were sitting at
calibration_state='empirically_calibrated' with no earned signal behind them.

This script is the committed, audited restamp tool for that disposition:
UPDATE kala_gochara_windows_v2 SET calibration_state='structural_prior'
WHERE calibration_state='empirically_calibrated' AND era_slice_key LIKE
'g3_%' AND chart_id IN (native, abhinandan) -- i.e. undo exactly what an
unsound w45 run could have done, restoring the honest default state.

staging is UNPROTECTED (migration 566's guard trigger only covers
kala_gochara_windows, never kala_gochara_windows_v2) -- no
app.allow_protected_sweep_rewrite override is needed or used here.

WHY THIS SCRIPT MAY FIND ZERO ROWS TO FIX
------------------------------------------
THE ONE authorized gen-3.0 corpus rebuild (2026-08-11, same PARIṢKĀRA
session) ran the real writer (ka_gochara_v3_century_materialize.py) for both
canonical charts. Per §N.3 (per-chart delete-then-insert, never accrete),
that rebuild's writer pass on kala_gochara_windows_v2 (the calibration/
staging surface, W3.4 original target) DELETE-then-INSERTed every g3_utkarsha
row from scratch, and every freshly-inserted row starts at
calibration_state='structural_prior' (the writer's own default -- only
w45's post-fit stamper, never the writer itself, sets
'empirically_calibrated'). This incidentally already overwrote the 107
dishonest rows as a side effect, verified live (2026-08-11, this script's
own pre-check): 0 rows currently sit at 'empirically_calibrated' anywhere in
kala_gochara_windows_v2 (174/174 rows are 'structural_prior',
max(computed_at) matches the rebuild's own timestamp). This script still
runs its real UPDATE against live production -- honest 0 rows affected is a
reported result, not a skipped check (§N.8: a detector that never fires
because there is truly nothing to find is not the same defect as a detector
that never fires because it cannot fire).

Usage:
    python3 restamp_dishonest_staging_calibration.py
    python3 restamp_dishonest_staging_calibration.py --dry-run
    python3 restamp_dishonest_staging_calibration.py --help
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
CHART_IDS = (NATIVE_CHART_ID, ABHINANDAN_CHART_ID)

TABLE_WINDOWS_V2 = "kala_gochara_windows_v2"
STATE_STRUCTURAL_PRIOR = "structural_prior"
STATE_EMPIRICALLY_CALIBRATED = "empirically_calibrated"


def _resolve_db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest",
             "--secret=amjis-pipeline-db-url"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        url = result.stdout.strip()
        if url:
            return url
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(
            f"ERROR: DATABASE_URL not set and gcloud fallback failed: {exc}\n"
            "Set DATABASE_URL or ensure gcloud is authenticated and "
            "cloud-sql-proxy is running on 127.0.0.1:5433."
        ) from exc
    raise SystemExit(
        "ERROR: DATABASE_URL not set and gcloud returned empty output.\n"
        "Set DATABASE_URL or ensure gcloud is authenticated."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "PARIṢKĀRA MR-37(b): restamp any staging (kala_gochara_windows_v2) "
            "row dishonestly marked 'empirically_calibrated' with no earned "
            "signal behind it, back to 'structural_prior'. Staging is "
            "unprotected -- no GUC override used or needed."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without making any DB write.",
    )
    args = parser.parse_args(argv)
    dry_run: bool = args.dry_run

    db_url = _resolve_db_url()

    try:
        import psycopg
        import psycopg.rows
    except ImportError as exc:
        raise SystemExit(
            f"ERROR: psycopg not available: {exc}\n"
            "Install via: pip install 'psycopg[binary]'"
        ) from exc

    conn = psycopg.connect(db_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # ── Pre-state: full calibration_state census (not scoped, for honesty) ──
    cur.execute(
        f"SELECT calibration_state, COUNT(*) AS n FROM {TABLE_WINDOWS_V2} "
        f"GROUP BY calibration_state ORDER BY calibration_state"
    )
    pre_census = cur.fetchall()
    print("[restamp] PRE-STATE census (kala_gochara_windows_v2, all rows):", file=sys.stderr)
    for row in pre_census:
        print(f"  {row['calibration_state']!r}: {row['n']}", file=sys.stderr)

    # ── Scoped target count ──────────────────────────────────────────────────
    cur.execute(
        f"""
        SELECT COUNT(*) AS n FROM {TABLE_WINDOWS_V2}
         WHERE chart_id = ANY(%s)
           AND era_slice_key LIKE 'g3_%%'
           AND calibration_state = %s
        """,
        (list(CHART_IDS), STATE_EMPIRICALLY_CALIBRATED),
    )
    target_count = cur.fetchone()["n"]
    print(
        f"[restamp] Scoped target (chart IN native/abhinandan, era_slice_key "
        f"LIKE 'g3_%', calibration_state='empirically_calibrated'): "
        f"{target_count} row(s)",
        file=sys.stderr,
    )

    if dry_run:
        print(
            f"[restamp] DRY RUN -- would UPDATE {target_count} row(s) "
            f"'{STATE_EMPIRICALLY_CALIBRATED}' -> '{STATE_STRUCTURAL_PRIOR}'"
        )
        conn.close()
        return 0

    # ── UPDATE ───────────────────────────────────────────────────────────────
    cur.execute(
        f"""
        UPDATE {TABLE_WINDOWS_V2}
           SET calibration_state = %s
         WHERE chart_id = ANY(%s)
           AND era_slice_key LIKE 'g3_%%'
           AND calibration_state = %s
        """,
        (STATE_STRUCTURAL_PRIOR, list(CHART_IDS), STATE_EMPIRICALLY_CALIBRATED),
    )
    updated = cur.rowcount

    # ── Post-state: re-run the same census ───────────────────────────────────
    cur.execute(
        f"SELECT calibration_state, COUNT(*) AS n FROM {TABLE_WINDOWS_V2} "
        f"GROUP BY calibration_state ORDER BY calibration_state"
    )
    post_census = cur.fetchall()

    conn.commit()
    conn.close()

    print(f"RESTAMP COMPLETE: {updated} row(s) restamped '{STATE_STRUCTURAL_PRIOR}'.")
    print("[restamp] POST-STATE census (kala_gochara_windows_v2, all rows):", file=sys.stderr)
    for row in post_census:
        print(f"  {row['calibration_state']!r}: {row['n']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
