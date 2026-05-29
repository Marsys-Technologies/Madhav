"""
pipeline.writers.sade_sati_writer — Write sade sati phases to sade_sati_phases_staging.
Phase 14C Stream E.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import psycopg

from pipeline.writers.base import IBuildWriter, SwapResult, ValidationResult, WriteResult

log = logging.getLogger(__name__)

# ── C-07 stub dispatch constants ───────────────────────────────────────────────
ASSET_ID = "A9_sade_sati"
ASSET_LABEL = "Sade-Sati Phases"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: "Optional[dict]" = None,
) -> int:
    """
    Stub writer for A9 Sade-Sati Phases (build_chart dispatch registry).
    Returns rows_written = 0 (stub — no data written).
    Real implementation wires SadeSatiWriter below; stub until Stream F.
    """
    log.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0


TABLE_STAGING = "sade_sati_phases_staging"
TABLE_LIVE = "sade_sati_phases"

_INSERT_SQL = f"""
INSERT INTO {TABLE_STAGING}
  (cycle_number, phase, start_date, end_date, saturn_sign_at_start,
   notes, source_section, build_id)
VALUES
  (%(cycle_number)s, %(phase)s, %(start_date)s, %(end_date)s,
   %(saturn_sign_at_start)s, %(notes)s, %(source_section)s, %(build_id)s)
ON CONFLICT (cycle_number, phase, start_date) DO UPDATE SET
  end_date             = EXCLUDED.end_date,
  saturn_sign_at_start = EXCLUDED.saturn_sign_at_start,
  notes                = EXCLUDED.notes,
  source_section       = EXCLUDED.source_section,
  build_id             = EXCLUDED.build_id
"""


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


class SadeSatiWriter(IBuildWriter):
    """Write sade sati phase rows from sade_sati_extractor into sade_sati_phases_staging."""

    def write_to_staging(self, rows: list[Any], build_id: str) -> WriteResult:
        if not rows:
            return WriteResult(chunk_count=0, errors=["No rows provided"])

        errors: list[str] = []
        written = 0

        with psycopg.connect(_db_url()) as conn:
            for row in rows:
                params = {**row, "build_id": build_id}
                try:
                    conn.execute(_INSERT_SQL, params)
                    written += 1
                except Exception as exc:
                    errors.append(f"{row.get('notes', '?')}: {exc}")
            conn.commit()

        log.info("sade_sati_phases_staging written: %d rows, %d errors", written, len(errors))
        return WriteResult(chunk_count=written, errors=errors)

    def validate_staging(self, build_id: str) -> ValidationResult:
        with psycopg.connect(_db_url()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM sade_sati_phases_staging WHERE build_id = %s", (build_id,)
            ).fetchone()
            count = int(row[0]) if row else 0

        valid = 20 <= count <= 80
        issues = [] if valid else [
            f"sade_sati_phases_staging count {count} outside 20–80 for build_id={build_id}"
        ]
        log.info("sade_sati validate_staging: build_id=%s count=%d valid=%s", build_id, count, valid)
        return ValidationResult(valid=valid, chunk_count=count, issues=issues)

    def swap_to_live(self, build_id: str) -> SwapResult:
        with psycopg.connect(_db_url()) as conn:
            live_count = int(
                (conn.execute("SELECT COUNT(*) FROM sade_sati_phases").fetchone() or [0])[0]
            )
            staging_count = int(
                (conn.execute(
                    "SELECT COUNT(*) FROM sade_sati_phases_staging WHERE build_id = %s", (build_id,)
                ).fetchone() or [0])[0]
            )

        if live_count > 0 and staging_count < (0.5 * live_count):
            msg = (
                f"ABORT: staging={staging_count}, live={live_count} — "
                "below 50% safety threshold."
            )
            log.error(msg)
            return SwapResult(success=False, promoted_chunk_count=0, message=msg)

        with psycopg.connect(_db_url(), autocommit=False) as conn:
            with conn.transaction():
                conn.execute("DELETE FROM sade_sati_phases")
                conn.execute(
                    """
                    INSERT INTO sade_sati_phases
                      (cycle_number, phase, start_date, end_date,
                       saturn_sign_at_start, notes, source_section, build_id)
                    SELECT cycle_number, phase, start_date, end_date,
                           saturn_sign_at_start, notes, source_section, build_id
                    FROM sade_sati_phases_staging
                    WHERE build_id = %s
                    """,
                    (build_id,),
                )
                conn.execute("TRUNCATE sade_sati_phases_staging")
                try:
                    conn.execute(
                        "UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=%s",
                        (build_id,),
                    )
                except Exception as exc:
                    log.warning("build_manifests update skipped: %s", exc)

        log.info("sade_sati swap_to_live: promoted %d rows for build_id=%s", staging_count, build_id)
        return SwapResult(
            success=True,
            promoted_chunk_count=staging_count,
            message=f"sade_sati_phases live: {staging_count} rows (build_id={build_id})",
        )
