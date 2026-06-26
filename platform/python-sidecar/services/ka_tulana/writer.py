"""
writer.py — Self-test WriterBase subclass for ka_tulana (L3 Kāla — cross-pattern prioritization service).

Registered as @register('ka_tulana').

The writer does NOT insert rows into any data table.
It runs a self-test (rank two synthetic WindowInputs; assert stable order)
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
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)


def _run_selftest() -> tuple[bool, str]:
    """
    Run service self-test.  Returns (ok: bool, detail_json: str).

    Test: a rare high-convergence window must outrank a common low-convergence
    window when ranked by I-11 composite weights.
    """
    from services.ka_tulana.ranker import KaTulanaService, WindowInput

    svc = KaTulanaService()

    a = WindowInput(
        window_id="t_a",
        mode="A",
        peak_date=date(2027, 1, 1),
        convergence_score=0.9,
        confidence_label="high",
        rarity_years=30.0,
        domains=["career"],
    )
    b = WindowInput(
        window_id="t_b",
        mode="A",
        peak_date=date(2027, 1, 1),
        convergence_score=0.4,
        confidence_label="moderate",
        rarity_years=2.0,
        domains=["wealth"],
    )

    ranked = svc.rank_windows([a, b], reference_date=date(2026, 1, 1))
    ok = len(ranked) == 2 and ranked[0].window.window_id == "t_a"
    detail = json.dumps({
        "test": "tulana_rank_order",
        "top": ranked[0].window.window_id if ranked else None,
        "n": len(ranked),
    })
    return ok, detail


def _update_registry_health(conn, ok: bool, detail: str) -> None:
    """Update asset_registry service_health + selftest_detail for ka_tulana."""
    health = "healthy" if ok else "degraded"
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        UPDATE asset_registry
        SET service_health   = %s,
            last_selftest_at = %s,
            selftest_detail  = %s
        WHERE asset_id = 'ka_tulana'
        """,
        [health, now, detail],
    )
    logger.info("[ka_tulana writer] service_health=%s", health)
    # DO NOT call conn.commit() -- orchestrator owns the transaction


def _build_writer_class():
    """Return the KaTulanaWriter class, importing WriterBase at call time."""
    from pipeline.orchestrator.writers import WriterBase, ContextSpec, WriterResult, register

    @register("ka_tulana")
    class KaTulanaWriter(WriterBase):
        """
        Self-test writer for ka_tulana service asset.

        Rows written: 0 (service asset -- no data rows emitted).
        Side effect: updates asset_registry.service_health.
        """
        asset_id = "ka_tulana"

        def run(self, ctx: ContextSpec) -> WriterResult:
            conn = ctx.db_conn

            if ctx.dry_run:
                logger.info("[ka_tulana writer] dry_run=True -- skipping self-test")
                return WriterResult(
                    asset_id=self.asset_id,
                    rows_inserted=0,
                    notes="dry_run=True",
                )

            ok, detail = _run_selftest()
            _update_registry_health(conn, ok, detail)

            if not ok:
                logger.error("[ka_tulana writer] self-test FAILED: %s", detail)
            else:
                logger.info("[ka_tulana writer] self-test PASSED")

            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"service_health={'healthy' if ok else 'degraded'}; {detail[:200]}",
            )

    return KaTulanaWriter


# Trigger registration when this module is imported by the orchestrator
KaTulanaWriter = _build_writer_class()
