"""
dispatch_utkarsha_w63_rollback_abhinandan.py — GOCHARA-UTKARṢA W6.3 authority rollback.

Rolls back the kala_gochara_authority row for Abhinandan Mohanty (1c826d5a),
reverting serving to the default v1 corpus (COALESCE fallback path).

IDEMPOTENCY: If no authority row exists for Abhinandan, prints "Already rolled back"
and exits 0.

POST-ROLLBACK VERIFICATION: After deleting the authority row, queries
kala_gochara_windows through the COALESCE serving filter and verifies serving
falls back to generation='v1' rows.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_utkarsha_w63_rollback_abhinandan.py

To re-apply the flip after rollback:
  python3 scripts/dispatch_utkarsha_w63_authority_flip_abhinandan.py
"""
from __future__ import annotations

import os
import sys

ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

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
        print("[W6.3-ROLLBACK ERROR] DATABASE_URL not set. Check platform/.env.local or environment.", file=sys.stderr)
        sys.exit(1)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # ── Idempotency check ─────────────────────────────────────────────────────
    cur.execute(
        """SELECT authoritative_generation, flipped_at, flipped_by, evidence_ref
           FROM kala_gochara_authority
           WHERE chart_id = %s""",
        (ABHINANDAN_CHART_ID,),
    )
    existing = cur.fetchone()
    if existing is None:
        print(
            f"[W6.3-ROLLBACK] kala_gochara_authority has no row for Abhinandan ({ABHINANDAN_CHART_ID[:8]}…). "
            f"Already rolled back. Exiting 0."
        )
        conn.close()
        sys.exit(0)

    print(
        f"[W6.3-ROLLBACK] Found authority row for Abhinandan ({ABHINANDAN_CHART_ID[:8]}…):\n"
        f"  authoritative_generation={existing['authoritative_generation']}\n"
        f"  flipped_at={existing['flipped_at']}\n"
        f"  flipped_by={existing['flipped_by']}\n"
        f"  evidence_ref={existing['evidence_ref']}\n"
        f"Proceeding with DELETE.",
        file=sys.stderr,
    )

    # ── Delete the authority row ──────────────────────────────────────────────
    cur.execute(
        "DELETE FROM kala_gochara_authority WHERE chart_id = %s",
        (ABHINANDAN_CHART_ID,),
    )
    print(
        f"[W6.3-ROLLBACK] DELETE kala_gochara_authority WHERE chart_id={ABHINANDAN_CHART_ID[:8]}… — done.",
        file=sys.stderr,
    )

    # ── Post-rollback verification via COALESCE serving filter ────────────────
    # After DELETE, COALESCE(authority_generation, 'v1') should return 'v1'.
    cur.execute(
        """SELECT generation, count(*) AS n
           FROM kala_gochara_windows
           WHERE chart_id = %s
             AND generation = COALESCE(
                 (SELECT authoritative_generation
                  FROM kala_gochara_authority
                  WHERE chart_id = %s),
                 'v1'
             )
           GROUP BY generation""",
        (ABHINANDAN_CHART_ID, ABHINANDAN_CHART_ID),
    )
    probe_rows = cur.fetchall()

    # Expect at least one row with generation='v1'
    v1_rows = [r for r in probe_rows if r["generation"] == "v1"]
    if not v1_rows:
        print(
            f"[W6.3-ROLLBACK ERROR] Post-rollback probe FAILED: COALESCE filter returned no v1 rows. "
            f"Got: {probe_rows}. Rolling back DELETE to preserve current state.",
            file=sys.stderr,
        )
        conn.rollback()
        conn.close()
        sys.exit(1)

    v1_count = v1_rows[0]["n"]
    print(
        f"[W6.3-ROLLBACK] Post-rollback probe: serving falls back to generation='v1', rows={v1_count} ✓",
        file=sys.stderr,
    )

    conn.commit()
    conn.close()

    print(
        f"W6.3 ROLLBACK COMPLETE for Abhinandan ({ABHINANDAN_CHART_ID[:8]}…). "
        f"kala_gochara_authority row deleted. Serving now defaults to generation='v1' "
        f"({v1_count} rows via COALESCE fallback). "
        f"To re-apply flip: run dispatch_utkarsha_w63_authority_flip_abhinandan.py"
    )


if __name__ == "__main__":
    main()
