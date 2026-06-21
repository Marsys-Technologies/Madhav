"""
writer.py — Self-test WriterBase subclass for ka_gochara (L3 K2 wave).

Registered as @register('ka_gochara').

The writer does NOT insert rows into any data table.
It runs a self-test (Jupiter transiting through Capricorn sidereal in 2020)
and writes `service_health` + `selftest_detail` to asset_registry.

Contract adherence:
  - Uses ctx.db_conn (caller-owned) for all DB access
  - NEVER calls ctx.db_conn.commit() or ctx.db_conn.rollback()
  - NEVER writes asset_throughput
  - Returns WriterResult(rows_inserted=0) -- service asset, no data rows
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _run_selftest() -> tuple[bool, str]:
    """
    Run service self-test.  Returns (ok: bool, detail_json: str).

    Test: Find Jupiter transiting through sidereal Capricorn (270 deg)
    as a conjunction/aspect event in 2020.  Jupiter entered sidereal
    Capricorn (Makara) around late 2020.
    """
    import swisseph as swe
    from pipeline.transit_search import find_aspect_events

    start_jd = swe.julday(2020, 1, 1, 0.0)
    end_jd = swe.julday(2021, 6, 1, 0.0)

    # Conjunction of Jupiter with 270 deg (Capricorn ingress point) with 2 deg orb
    events = find_aspect_events(swe, "Jupiter", 270.0, [0], 2.0, start_jd, end_jd)

    ok = len(events) >= 1
    detail = json.dumps({
        "test": "jupiter_capricorn_transit_2020",
        "events_found": len(events),
        "first_event_ist": events[0].event_datetime_ist if events else None,
    })
    return ok, detail


def _update_registry_health(conn, ok: bool, detail: str) -> None:
    """Update asset_registry service_health + selftest_detail for ka_gochara."""
    health = "healthy" if ok else "degraded"
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        UPDATE asset_registry
        SET service_health   = %s,
            last_selftest_at = %s,
            selftest_detail  = %s
        WHERE asset_id = 'ka_gochara'
        """,
        [health, now, detail],
    )
    logger.info("[ka_gochara writer] service_health=%s", health)
    # DO NOT call conn.commit() -- orchestrator owns the transaction


def _build_writer_class():
    """Return the KaGocharaWriter class, importing WriterBase at call time."""
    from pipeline.orchestrator.writers import WriterBase, ContextSpec, WriterResult, register

    @register("ka_gochara")
    class KaGocharaWriter(WriterBase):
        """
        Self-test writer for ka_gochara service asset.

        Rows written: 0 (service asset -- no data rows emitted).
        Side effect: updates asset_registry.service_health.
        """
        asset_id = "ka_gochara"

        def run(self, ctx: ContextSpec) -> WriterResult:
            conn = ctx.db_conn

            if ctx.dry_run:
                logger.info("[ka_gochara writer] dry_run=True -- skipping self-test")
                return WriterResult(
                    asset_id=self.asset_id,
                    rows_inserted=0,
                    notes="dry_run=True",
                )

            ok, detail = _run_selftest()
            _update_registry_health(conn, ok, detail)

            if not ok:
                logger.error("[ka_gochara writer] self-test FAILED: %s", detail)
            else:
                logger.info("[ka_gochara writer] self-test PASSED")

            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"service_health={'healthy' if ok else 'degraded'}; {detail[:200]}",
            )

    return KaGocharaWriter


# Trigger registration when this module is imported by the orchestrator
KaGocharaWriter = _build_writer_class()
