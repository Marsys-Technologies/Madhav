"""
writer.py — Self-test WriterBase subclass for ka_dasha_kala.

Registered as @register('ka_dasha_kala').

The writer does NOT insert rows into chart_dashas or any L1/L2 table.
It runs a self-test against the native's chart (482012f1-...) and
writes `service_health` + `selftest_detail` to asset_registry.

Contract adherence:
  - Uses ctx.db_conn (caller-owned) for all DB access
  - NEVER calls ctx.db_conn.commit() or ctx.db_conn.rollback()
  - NEVER writes asset_throughput
  - Returns WriterResult(rows_written=0) -- service asset, no data rows
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)

# Canonical chart for self-test
_CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_CANONICAL_AYANAMSHA = "lahiri"
_EXPECTED_SYSTEMS = frozenset({
    "vimshottari", "yogini", "ashtottari", "chara_karaka",
    "naisargika", "mudda", "kalachakra",
})


def _run_selftest(conn) -> tuple[bool, str]:
    """
    Run service self-test.  Returns (ok: bool, detail: str).

    Assertions:
      1. chart_dashas has all 7 expected systems for the native's chart.
      2. A query window returns non-empty results with valid intervals
         (start_date < end_date).
      3. 7 systems are confirmed present.
    """
    from .service import KaDashaKalaService

    svc = KaDashaKalaService(db_conn=conn)

    # Assertion 1: 7 systems present
    sys_counts = svc.confirm_systems_present(_CANONICAL_CHART_ID, _CANONICAL_AYANAMSHA)
    missing = _EXPECTED_SYSTEMS - set(sys_counts.keys())
    if missing:
        return False, f"Missing systems in chart_dashas: {sorted(missing)}"

    # Assertion 2: Non-empty result for a known query window
    # Use Saturn/Rahu as target lords (they appear prominently in Vimshottari for this chart)
    result = svc.query(
        chart_id=_CANONICAL_CHART_ID,
        ayanamsha_id=_CANONICAL_AYANAMSHA,
        target_lords={"Saturn", "Rahu"},
        related_lords={"Mercury", "Venus"},
        date_start=date(2010, 1, 1),
        date_end=date(2030, 12, 31),
        max_level=2,   # AD level — fast enough for self-test
        prana_grain=False,
    )

    if not result.windows:
        return False, "Self-test query returned 0 windows for Saturn/Rahu in 2010-2030"

    # Assertion 3: All intervals have start < end
    invalid = [
        w for w in result.windows
        if w.start_date >= w.end_date
    ]
    if invalid:
        return False, f"{len(invalid)} intervals have start_date >= end_date"

    detail = json.dumps({
        "systems_found": sorted(sys_counts.keys()),
        "systems_expected": sorted(_EXPECTED_SYSTEMS),
        "windows_returned": result.total_windows,
        "high_agreement_count": result.high_agreement_count,
        "systems_queried": result.systems_queried,
    })
    return True, detail


def _update_registry_health(conn, ok: bool, detail: str) -> None:
    """Update asset_registry service_health + selftest_detail for ka_dasha_kala."""
    health = "healthy" if ok else "degraded"
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE asset_registry
            SET service_health    = %s,
                last_selftest_at  = %s,
                selftest_detail   = %s
            WHERE asset_id = 'ka_dasha_kala'
            """,
            [health, now, detail],
        )
    logger.info("[ka_dasha_kala writer] service_health=%s", health)


# ---------------------------------------------------------------------------
# WriterBase subclass (imported inline to avoid circular imports at module level)
# ---------------------------------------------------------------------------

def _build_writer_class():
    """Return the KaDashaKalaWriter class, importing WriterBase at call time."""
    from pipeline.orchestrator.writers import WriterBase, ContextSpec, WriterResult, register

    @register("ka_dasha_kala")
    class KaDashaKalaWriter(WriterBase):
        """
        Self-test writer for ka_dasha_kala service asset.

        Rows written: 0 (service asset -- no data rows emitted).
        Side effect: updates asset_registry.service_health.
        """
        asset_id = "ka_dasha_kala"

        def run(self, ctx: ContextSpec) -> WriterResult:
            conn = ctx.db_conn

            if ctx.dry_run:
                logger.info("[ka_dasha_kala writer] dry_run=True -- skipping self-test")
                return WriterResult(
                    asset_id=self.asset_id,
                    rows_inserted=0,
                    notes="dry_run=True",
                )

            build_chart_id = ctx.config.get('chart_id', '')
            if build_chart_id and build_chart_id != _CANONICAL_CHART_ID:
                logger.warning(
                    "[ka_dasha_kala writer] build chart_id=%s is not the canonical chart; "
                    "self-test runs against %s and health reflects only that chart",
                    build_chart_id, _CANONICAL_CHART_ID,
                )

            ok, detail = _run_selftest(conn)
            _update_registry_health(conn, ok, detail)

            if not ok:
                logger.error("[ka_dasha_kala writer] self-test FAILED: %s", detail)
            else:
                logger.info("[ka_dasha_kala writer] self-test PASSED")

            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"service_health={'healthy' if ok else 'degraded'}; {detail[:200]}",
            )

    return KaDashaKalaWriter


# Trigger registration when this module is imported by the orchestrator
KaDashaKalaWriter = _build_writer_class()
