"""
pipeline.writers.msr_signals_writer — Write MSR signals to l25_msr_signals_staging.
Phase 14D Stream B.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import psycopg

from pipeline.writers.base import IBuildWriter, SwapResult, ValidationResult, WriteResult

log = logging.getLogger(__name__)

TABLE_STAGING = "l25_msr_signals_staging"
TABLE_LIVE = "l25_msr_signals"
EXPECTED_COUNT = 573

_INSERT_SQL = f"""
INSERT INTO {TABLE_STAGING}
  (signal_id, signal_number, name, category, valence, weight,
   planets_involved, houses_involved, signs_involved,
   description, source_section, build_id, provenance)
VALUES
  (%(signal_id)s, %(signal_number)s, %(name)s, %(category)s, %(valence)s,
   %(weight)s, %(planets_involved)s, %(houses_involved)s, %(signs_involved)s,
   %(description)s, %(source_section)s, %(build_id)s, %(provenance)s::jsonb)
ON CONFLICT (signal_id) DO UPDATE SET
  signal_number    = EXCLUDED.signal_number,
  name             = EXCLUDED.name,
  category         = EXCLUDED.category,
  valence          = EXCLUDED.valence,
  weight           = EXCLUDED.weight,
  planets_involved = EXCLUDED.planets_involved,
  houses_involved  = EXCLUDED.houses_involved,
  signs_involved   = EXCLUDED.signs_involved,
  description      = EXCLUDED.description,
  source_section   = EXCLUDED.source_section,
  build_id         = EXCLUDED.build_id,
  provenance       = EXCLUDED.provenance
"""


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


class MSRSignalsWriter(IBuildWriter):
    """
    Writes MSR signal rows (from msr_extractor.extract_msr_signals) to
    l25_msr_signals_staging, with staging-then-swap lifecycle.
    """

    def write_to_staging(self, rows: list[Any], build_id: str) -> WriteResult:
        """
        Write MSR signal dicts to l25_msr_signals_staging.

        Args:
            rows: list[dict] from extract_msr_signals().
            build_id: The active build identifier.

        Returns:
            WriteResult with chunk_count = number of rows written.
        """
        if not rows:
            return WriteResult(chunk_count=0, errors=["No rows provided"])

        errors: list[str] = []
        written = 0

        with psycopg.connect(_db_url()) as conn:
            for row in rows:
                params = {
                    "signal_id": row["signal_id"],
                    "signal_number": row["signal_number"],
                    "name": row["name"],
                    "category": row["category"],
                    "valence": row["valence"],
                    "weight": row["weight"],
                    "planets_involved": row["planets_involved"],
                    "houses_involved": row["houses_involved"],
                    "signs_involved": row["signs_involved"],
                    "description": row.get("description"),
                    "source_section": row["source_section"],
                    "build_id": build_id,
                    "provenance": json.dumps(row["provenance"]),
                }
                try:
                    conn.execute(_INSERT_SQL, params)
                    written += 1
                except Exception as exc:
                    errors.append(f"{row['signal_id']}: {exc}")
            conn.commit()

        log.info("msr_signals_staging written: %d rows, %d errors", written, len(errors))
        return WriteResult(chunk_count=written, errors=errors)

    def validate_staging(self, build_id: str) -> ValidationResult:
        """
        Verify that l25_msr_signals_staging has exactly 573 rows for this build_id.

        Returns:
            ValidationResult(valid=True, chunk_count=573) on success.
        """
        with psycopg.connect(_db_url()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM l25_msr_signals_staging WHERE build_id = %s",
                (build_id,),
            ).fetchone()
            count = int(row[0]) if row else 0

        valid = count == EXPECTED_COUNT
        issues = [] if valid else [
            f"Expected {EXPECTED_COUNT} rows in staging for build_id={build_id}, found {count}"
        ]
        log.info("msr_signals validate_staging: build_id=%s count=%d valid=%s", build_id, count, valid)
        return ValidationResult(valid=valid, chunk_count=count, issues=issues)

    def swap_to_live(self, build_id: str) -> SwapResult:
        """
        Promote l25_msr_signals_staging → l25_msr_signals in a single transaction.

        Safety gate: staging must have >= 0.5 × live count. If live is empty, skip gate.
        Steps: DELETE live; INSERT from staging; TRUNCATE staging — all atomic.
        """
        with psycopg.connect(_db_url()) as conn:
            live_count = int(
                (conn.execute("SELECT COUNT(*) FROM l25_msr_signals").fetchone() or [0])[0]
            )
            staging_count = int(
                (
                    conn.execute(
                        "SELECT COUNT(*) FROM l25_msr_signals_staging WHERE build_id = %s",
                        (build_id,),
                    ).fetchone()
                    or [0]
                )[0]
            )

        # 0.5× safety gate — skip if live is empty
        if live_count > 0 and staging_count < (0.5 * live_count):
            msg = (
                f"ABORT: staging has {staging_count} rows but live has {live_count} — "
                "below 50% safety threshold. Swap aborted; live tables untouched."
            )
            log.error(msg)
            return SwapResult(success=False, promoted_chunk_count=0, message=msg)

        with psycopg.connect(_db_url(), autocommit=False) as conn:
            with conn.transaction():
                conn.execute("DELETE FROM l25_msr_signals")
                conn.execute(
                    """
                    INSERT INTO l25_msr_signals
                      (signal_id, signal_number, name, category, valence, weight,
                       planets_involved, houses_involved, signs_involved,
                       description, source_section, build_id, provenance)
                    SELECT
                      signal_id, signal_number, name, category, valence, weight,
                      planets_involved, houses_involved, signs_involved,
                      description, source_section, build_id, provenance
                    FROM l25_msr_signals_staging
                    WHERE build_id = %s
                    """,
                    (build_id,),
                )
                conn.execute("TRUNCATE l25_msr_signals_staging")

                # Best-effort build_manifests update — skip if table/FK not present
                try:
                    conn.execute(
                        "UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=%s",
                        (build_id,),
                    )
                except Exception as exc:
                    log.warning("build_manifests update skipped: %s", exc)

        log.info("msr_signals swap_to_live: promoted %d rows for build_id=%s", staging_count, build_id)
        return SwapResult(
            success=True,
            promoted_chunk_count=staging_count,
            message=f"l25_msr_signals live: {staging_count} rows (build_id={build_id})",
        )
