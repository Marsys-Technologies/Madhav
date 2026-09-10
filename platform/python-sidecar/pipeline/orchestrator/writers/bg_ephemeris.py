"""
pipeline/orchestrator/writers/bg_ephemeris.py
L0 Brahmagyan ephemeris writer — seeds ephemeris_daily via WriterBase.

Wraps the legacy bootstrap logic from brahmagyan.l0_ephemeris so that
"Rebuild All" via the orchestrator can regenerate the daily ephemeris
table without needing a separate bootstrap invocation.

L0 convergence: ON CONFLICT (date, body, ayanamsha_id) conditionally repairs
stale semantic columns. The full build period is 1900-01-01 → 2150-12-31
(~825,075 rows × 9 bodies). Exact rows are left untouched so rowcount reports
only inserted or genuinely repaired rows.

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
    computed via the pinned, file-backed Swiss Ephemeris corpus. A governed
    rebuild fails closed rather than accepting pyswisseph's analytic fallback.

    Idempotency: ON CONFLICT (date, body, ayanamsha_id) conditionally repairs
    stale values; restarts and partial rebuilds converge without rewriting
    already-exact rows.

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
            _resolve_ephe_path,
        )

        try:
            import swisseph as swe  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "bg_ephemeris requires pyswisseph and cannot rebuild without it"
            ) from exc

        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_ephemeris] dry_run=True — skipping INSERT")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        # Resolve ephemeris data path and initialise swisseph
        ephe_path = _resolve_ephe_path()
        if not ephe_path:
            raise RuntimeError(
                "bg_ephemeris requires the pinned Swiss Ephemeris .se1 corpus; "
                "refusing the analytic fallback"
            )
        from pipeline.orchestrator.writers.bg_sky_calendar import (
            _require_pinned_ephemeris_files,
            _require_swiss_file_backend,
        )
        _require_swiss_file_backend(swe, ephe_path)
        _require_pinned_ephemeris_files(ephe_path)

        conn = ctx.db_conn
        rows_inserted = 0
        current = BUILD_START

        try:
            with conn.cursor() as cur:
                while current <= BUILD_END:
                    # Accumulate one batch of days
                    batch_rows: list[dict[str, Any]] = []
                    for _ in range(self._BATCH_DAYS):
                        if current > BUILD_END:
                            break
                        day_rows = _compute_positions_for_date(current, swe, ephe_path)
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
                        ON CONFLICT (date, body, ayanamsha_id) DO UPDATE SET
                          tropical_longitude = EXCLUDED.tropical_longitude,
                          latitude = EXCLUDED.latitude,
                          speed_dps = EXCLUDED.speed_dps,
                          is_retrograde = EXCLUDED.is_retrograde,
                          source_citation = EXCLUDED.source_citation,
                          computed_at = EXCLUDED.computed_at
                        WHERE ROW(
                          ephemeris_daily.tropical_longitude,
                          ephemeris_daily.latitude,
                          ephemeris_daily.speed_dps,
                          ephemeris_daily.is_retrograde,
                          ephemeris_daily.source_citation
                        ) IS DISTINCT FROM ROW(
                          EXCLUDED.tropical_longitude,
                          EXCLUDED.latitude,
                          EXCLUDED.speed_dps,
                          EXCLUDED.is_retrograde,
                          EXCLUDED.source_citation
                        )
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
        except Exception as exc:
            logger.exception(
                "[bg_ephemeris] computation failed after %d inserted rows: %s",
                rows_inserted,
                exc,
            )
            raise

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
