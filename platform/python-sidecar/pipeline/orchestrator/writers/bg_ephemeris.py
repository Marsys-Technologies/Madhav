"""
pipeline/orchestrator/writers/bg_ephemeris.py
L0 Brahmagyan ephemeris writer — seeds ephemeris_daily via WriterBase.

Wraps the legacy bootstrap logic from brahmagyan.l0_ephemeris so that
"Rebuild All" via the orchestrator can regenerate the daily ephemeris
table without needing a separate bootstrap invocation.

L0 idempotency: ON CONFLICT (date, body, ayanamsha_id) DO NOTHING (as in
the brahmagyan module). The full build period is 1900-01-01 → 2150-12-31
(~825,075 rows × 9 bodies). Existing rows are left in place; only missing
rows are inserted. This is safe for orchestrator-owned transactions because
each batch's rowcount is tracked and returned without committing.

ZERO LLM use. Pure deterministic pyswisseph / algorithmic computation.

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2):
- uses ctx.db_conn exclusively (never opens, commits, or closes it)
- returns WriterResult with actual rows_inserted
- honours ctx.dry_run
"""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    WriterBase,
    WriterResult,
    register,
)

logger = logging.getLogger(__name__)


@register("bg_ephemeris")
class BgEphemerisWriter(WriterBase):
    """
    Seeds ephemeris_daily (9 bodies × date range 1900-01-01 → 2150-12-31).

    L0 writer — chart-agnostic daily planetary positions (tropical longitudes)
    computed via pyswisseph DE441. Falls back to algorithmic approximation when
    pyswisseph is unavailable (dry_run / test contexts).

    Idempotency: ON CONFLICT (date, body, ayanamsha_id) DO NOTHING — restarts
    and partial rebuilds are safe; only rows not yet present are inserted.

    This writer wraps the legacy brahmagyan.l0_ephemeris bootstrap logic so
    that "Rebuild All" via the orchestrator can regenerate the ephemeris table.
    The legacy standalone build_ephemeris() function opens its own connection
    and commits internally — it CANNOT be reused here. The INSERT logic is
    reproduced below using ctx.db_conn (orchestrator-owned, no commit).
    """

    asset_id = "bg_ephemeris"

    # Batch size: balance memory vs. round-trips. 100 days × 9 bodies = 900 rows.
    _BATCH_DAYS = 100

    def run(self, ctx: ContextSpec) -> WriterResult:
        from brahmagyan.l0_ephemeris import (
            BUILD_END,
            BUILD_START,
            AYANAMSHA_ID,
            SOURCE_CITATION,
            _compute_positions_for_date,
        )

        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_ephemeris] dry_run=True — skipping INSERT")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        conn = ctx.db_conn
        rows_inserted = 0
        current = BUILD_START

        with conn.cursor() as cur:
            while current <= BUILD_END:
                # Accumulate one batch of days
                batch_rows: list[dict[str, Any]] = []
                for _ in range(self._BATCH_DAYS):
                    if current > BUILD_END:
                        break
                    day_rows = _compute_positions_for_date(current)
                    batch_rows.extend(day_rows)
                    current += timedelta(days=1)

                if not batch_rows:
                    break

                cur.executemany(
                    """
                    INSERT INTO ephemeris_daily
                      (date, body, ayanamsha_id, tropical_longitude, latitude,
                       speed_dps, is_retrograde, source_citation, computed_at)
                    VALUES
                      (%(date)s, %(body)s, %(ayanamsha_id)s, %(tropical_longitude)s,
                       %(latitude)s, %(speed_dps)s, %(is_retrograde)s,
                       %(source_citation)s, %(computed_at)s)
                    ON CONFLICT (date, body, ayanamsha_id) DO NOTHING
                    """,
                    batch_rows,
                )
                rows_inserted += cur.rowcount

                # Log progress every 10 batches (~1 000 days)
                total_days = (BUILD_END - BUILD_START).days or 1
                done_days = (current - BUILD_START).days
                if done_days % (self._BATCH_DAYS * 10) < self._BATCH_DAYS:
                    pct = 100.0 * done_days / total_days
                    logger.info(
                        "[bg_ephemeris] %.1f%% (%s) — %d rows inserted so far",
                        pct, current, rows_inserted,
                    )

        elapsed = round(time.time() - t0, 2)
        logger.info(
            "[bg_ephemeris] complete — %d rows inserted in %.1fs",
            rows_inserted, elapsed,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
            duration_seconds=elapsed,
            notes=(
                f"period={BUILD_START.isoformat()}→{BUILD_END.isoformat()}; "
                f"bodies=9; source={SOURCE_CITATION}"
            ),
        )
