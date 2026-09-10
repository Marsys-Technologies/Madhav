#!/usr/bin/env python3
"""
flip_authority.py — PARIṢKĀRA MR-30 / MR-08 gochara authority flip tooling.

Flips kala_gochara_authority.authoritative_generation for a specific chart,
promoting it from the default v1 corpus to a named generation (e.g. '3.0').

CAMPAIGN CONTEXT
----------------
This script was authored as part of PARIṢKĀRA MR-30 (Evidence + worktree
hygiene). During GOCHARA-UTKARṢA W6.1–W6.3 the authority flip was performed
ad-hoc using chart-specific one-off dispatch scripts (utk-w61/
dispatch_utkarsha_w63_authority_flip_abhinandan.py). MR-08 requires these
operational scripts be committed as versioned, chart-agnostic tooling.

RELATIONSHIP TO MR-08
---------------------
MR-08's closure gate ("versioned flip/rollback/probe tooling in git") is
satisfied by this file + rollback_authority.py + probe_gochara.py. MR-08's
actual flip is performed by an operator calling this script with the target
chart-id and generation; MR-08's gate proof is a transcript from
probe_gochara.py (which calls the DEPLOYED MCP product, not direct SQL).

SCHEMA CONTRACT (migration 527)
--------------------------------
kala_gochara_authority: (chart_id UUID PRIMARY KEY, authoritative_generation,
flipped_at, flipped_by, evidence_ref).
ABSENT ROW = v1 authoritative (COALESCE contract).
Revert: run rollback_authority.py (DELETE, no data motion).

DB CONNECTION
-------------
Reads the Postgres connection string from the DATABASE_URL environment
variable. If DATABASE_URL is not set, falls back to fetching the secret
via gcloud:

    gcloud secrets versions access latest --secret=amjis-pipeline-db-url

and expects cloud-sql-proxy to be listening on 127.0.0.1:5433.

Usage:
    python3 flip_authority.py --chart-id <uuid> --generation <gen>
    python3 flip_authority.py --chart-id <uuid> --generation 3.0 --dry-run
    python3 flip_authority.py --help
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# DB connection helper
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Flip kala_gochara_authority.authoritative_generation for a chart. "
            "PARIṢKĀRA MR-30/MR-08 versioned tooling — replaces ad-hoc "
            "dispatch_utkarsha_w63_authority_flip_*.py one-offs."
        ),
    )
    parser.add_argument(
        "--chart-id", required=True,
        help="UUID of the chart to flip (e.g. 482012f1-710e-4a25-994a-93821f5871aa)",
    )
    parser.add_argument(
        "--generation", required=True,
        help="Target authoritative_generation value to set (e.g. '3.0')",
    )
    parser.add_argument(
        "--flipped-by", default="parishkara-mr08-operator",
        help="Identity string stored in kala_gochara_authority.flipped_by (default: parishkara-mr08-operator)",
    )
    parser.add_argument(
        "--evidence-ref", default=None,
        help="Evidence reference stored in kala_gochara_authority.evidence_ref "
             "(e.g. a close-report path or ruling id). Required for a production flip; "
             "optional in --dry-run mode.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without making any DB write.",
    )
    args = parser.parse_args(argv)

    chart_id: str = args.chart_id
    generation: str = args.generation
    flipped_by: str = args.flipped_by
    evidence_ref: str | None = args.evidence_ref
    dry_run: bool = args.dry_run

    if not dry_run and evidence_ref is None:
        print(
            "WARNING: --evidence-ref not supplied. For production flips an "
            "evidence reference is expected (close-report path or ruling id). "
            "Proceeding anyway — set --evidence-ref for a traceable flip.",
            file=sys.stderr,
        )

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

    # ── Read current state ───────────────────────────────────────────────────
    cur.execute(
        "SELECT authoritative_generation, flipped_at, flipped_by, evidence_ref "
        "FROM kala_gochara_authority WHERE chart_id = %s",
        (chart_id,),
    )
    existing = cur.fetchone()

    if existing is not None:
        current_gen = existing["authoritative_generation"]
        print(
            f"[flip_authority] chart {chart_id[:8]}… currently has "
            f"authoritative_generation={current_gen!r} "
            f"(flipped_at={existing['flipped_at']}, "
            f"flipped_by={existing['flipped_by']!r})",
            file=sys.stderr,
        )
        if current_gen == generation:
            print(
                f"[flip_authority] Already at generation={generation!r} — no-op. "
                f"Exiting 0."
            )
            conn.close()
            return 0
    else:
        print(
            f"[flip_authority] chart {chart_id[:8]}… has no authority row "
            f"(currently defaults to v1 via COALESCE).",
            file=sys.stderr,
        )

    if dry_run:
        if existing is not None:
            action = (
                f"UPDATE kala_gochara_authority SET authoritative_generation={generation!r}, "
                f"flipped_at=now(), flipped_by={flipped_by!r}, "
                f"evidence_ref={evidence_ref!r} WHERE chart_id={chart_id!r}"
            )
        else:
            action = (
                f"INSERT INTO kala_gochara_authority "
                f"(chart_id, authoritative_generation, flipped_at, flipped_by, evidence_ref) "
                f"VALUES ({chart_id!r}, {generation!r}, now(), {flipped_by!r}, {evidence_ref!r})"
            )
        print(f"[flip_authority] DRY RUN — would execute: {action}")
        conn.close()
        return 0

    # ── UPSERT ───────────────────────────────────────────────────────────────
    cur.execute(
        """
        INSERT INTO kala_gochara_authority
            (chart_id, authoritative_generation, flipped_at, flipped_by, evidence_ref)
        VALUES (%s, %s, now(), %s, %s)
        ON CONFLICT (chart_id) DO UPDATE
            SET authoritative_generation = EXCLUDED.authoritative_generation,
                flipped_at               = EXCLUDED.flipped_at,
                flipped_by               = EXCLUDED.flipped_by,
                evidence_ref             = EXCLUDED.evidence_ref
        """,
        (chart_id, generation, flipped_by, evidence_ref),
    )

    # ── Read-back verification ───────────────────────────────────────────────
    cur.execute(
        "SELECT authoritative_generation, flipped_at FROM kala_gochara_authority "
        "WHERE chart_id = %s",
        (chart_id,),
    )
    row = cur.fetchone()
    if row is None or row["authoritative_generation"] != generation:
        print(
            f"[flip_authority] ERROR: read-back after UPSERT returned unexpected "
            f"row={row}. Rolling back.",
            file=sys.stderr,
        )
        conn.rollback()
        conn.close()
        return 1

    conn.commit()
    conn.close()

    print(
        f"FLIP COMPLETE: chart {chart_id} -> generation {generation}"
    )
    print(
        f"  flipped_at={row['flipped_at']}  flipped_by={flipped_by!r}  "
        f"evidence_ref={evidence_ref!r}",
        file=sys.stderr,
    )
    print(
        f"  Rollback: python3 rollback_authority.py --chart-id {chart_id}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
