"""
writer.py — Self-test WriterBase subclass for ka_tulana (L3 Kāla — cross-pattern prioritization service).

Registered as @register('ka_tulana').

The writer does NOT insert rows into any data table.
It compares two synthetic forecaster windows against pinned Pareto relations
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
    """Keep the (ok, JSON detail) interface; independently pin Pareto relations."""
    from services.ka_tulana.ranker import KaTulanaService
    windows = [
        dict(chart_id="fixture", field_snapshot_id="fixture", window_id="A",
             window_start="2026-10-20", window_end="2026-11-30", confidence_tier="structural_prior"),
        dict(chart_id="fixture", field_snapshot_id="fixture", window_id="B",
             window_start="2026-11-02", window_end="2026-11-30", confidence_tier="concurrent")]
    try:
        result = KaTulanaService().compare_windows(windows, date_from="2026-10-13", date_to="2027-01-11")
        pair = result["comparisons"][0]
        ok = (result["ordered"] == ["B", "A"] and result["front"] == ["A", "B"]
              and pair["relation"] == "incomparable" and pair["reason"] == "unavailable"
              and {k:v["relation"] for k,v in pair["axes"].items()} ==
                  {"nearest":"A_better", "strongest":"unavailable", "most_robust":"B_better"})
        return ok, json.dumps({"test":"tulana_pareto", "result":result})
    except Exception as exc:
        return False, json.dumps({"test":"tulana_pareto", "error":str(exc)})


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
                # NIRMĀṆA L3-W3 M11 (§N.8): a returned WriterResult is treated as SUCCESS by
                # the orchestrator regardless of its notes, so a degraded self-test used to leave
                # the asset promoted to 'lit' while asset_registry.service_health said otherwise —
                # a green build signal with no detector behind it. Raising is the only path that
                # reaches mark_asset_error. This mirrors ka_muhurta_seva, which already did it
                # correctly and documents why.
                raise RuntimeError(
                    f"ka_tulana self-test failed (service_health=degraded): {detail[:400]}"
                )

            logger.info("[ka_tulana writer] self-test PASSED")

            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"service_health=healthy; {detail[:200]}",
            )

    return KaTulanaWriter


# Trigger registration when this module is imported by the orchestrator
KaTulanaWriter = _build_writer_class()
