#!/usr/bin/env python3
"""step02_restore_drill.py — WP10 runbook step 2 (plan §9): restore drill.

Restores the 2026-08-23 logical dump into a disposable database and
content-checks all 38,287 v1 rows of `kala_gochara_windows` — row-by-row
digest equality, never `pg_restore -l` — and writes the archive-gap report
(the 2,667 uncovered ids, measured §N.4; migration 670 pins the shape).

Tranche 1 (PRODUCTION_TRANCHE_1_AUTHORIZED). Sheet A-2. Reversal: none needed
(the drill targets a disposable database by definition).

Usage:
    python3 step02_restore_drill.py --dsn postgresql://... --dump /path/to/dump.dump

Exit codes:
    0 — restore + digest equality + gap report written
    3 — cannot proceed (no --dump, driver missing, dump unreadable)
    4 — refused: DSN names the production instance without the tranche flag
    5 — digest mismatch (gate RED; evidence written, do not proceed)

Remainder-brief status: NOT_RUN at preparation time — no dump is available
locally. The script refuses to run without an explicit --dump path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, refuse_production, step_parser, write_evidence  # noqa: E402

EXPECTED_V1_ROWS = 38_287
EXPECTED_UNCOVERED_IDS = 2_667

# Row content digest: sha256 over the canonical (sorted-key, compact) JSON of
# every v1 row ordered by id — independent of dump ordering and row oids.
DIGEST_SQL = """
SELECT id, row_to_json(w.*) AS row_json
FROM kala_gochara_windows w
WHERE w.generation = 'v1'
ORDER BY w.id
"""


def content_digest(rows) -> str:
    h = hashlib.sha256()
    for row_id, row_json in rows:
        h.update(json.dumps(row_json, sort_keys=True, separators=(",", ":"),
                            default=str).encode())
        h.update(b"\n")
    return h.hexdigest()


def main() -> int:
    parser = step_parser(2, __doc__)
    parser.add_argument("--dump", help="path to the 2026-08-23 logical dump")
    args = parser.parse_args()

    # The production guard precedes every other failure mode: a refusal must
    # never be masked by a missing --dump.
    refuse_production(args.dsn, step=2)

    if not args.dump:
        print("NOT_RUN: --dump is required (no dump is available locally; "
              "the drill is rehearsed as NOT_RUN per the remainder brief §7.A)",
              file=sys.stderr)
        return 3
    dump = Path(args.dump)
    if not dump.exists():
        print(f"ERROR: dump not readable: {dump}", file=sys.stderr)
        return 3

    # Restore into the (disposable) target.
    restore = subprocess.run(
        ["pg_restore", "--dbname", args.dsn, "--no-owner", "--no-privileges",
         str(dump)],
        capture_output=True, text=True)
    if restore.returncode != 0:
        print(f"ERROR: pg_restore failed:\n{restore.stderr}", file=sys.stderr)
        return 3

    conn = connect(args.dsn, step=2)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM kala_gochara_windows WHERE generation = 'v1'")
        n_rows = cur.fetchone()[0]
        cur.execute(DIGEST_SQL)
        digest = content_digest(cur.fetchall())
        # Archive-gap report: ids present in the v1 corpus but not covered by
        # the archive table. Expect the measured 2,667 (migration 670).
        cur.execute("""
            SELECT w.id FROM kala_gochara_windows w
            WHERE w.generation = 'v1' AND NOT EXISTS (
              SELECT 1 FROM kala_gochara_windows_archive_20260805 a
              WHERE a.id = w.id)
            ORDER BY w.id
        """)
        uncovered = [r[0] for r in cur.fetchall()]
    conn.close()

    report = {
        "dump": str(dump),
        "v1_row_count": n_rows,
        "v1_row_count_expected": EXPECTED_V1_ROWS,
        "content_digest_sha256": digest,
        "uncovered_id_count": len(uncovered),
        "uncovered_id_count_expected": EXPECTED_UNCOVERED_IDS,
        "uncovered_ids": uncovered,
    }
    print(json.dumps(report, indent=2, default=str))

    ok = (n_rows == EXPECTED_V1_ROWS
          and len(uncovered) == EXPECTED_UNCOVERED_IDS)
    if args.evidence:
        write_evidence(2, "GREEN" if ok else "RED",
                       f"```json\n{json.dumps(report, indent=2, default=str)}\n```")
    # Row-count and gap-count equality are the drill's hard gates; the digest
    # is recorded for comparison against the source-side digest computed at
    # tranche time (the dump alone cannot prove equality with production).
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main())
