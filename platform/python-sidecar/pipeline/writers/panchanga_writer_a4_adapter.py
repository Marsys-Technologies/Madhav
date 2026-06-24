"""
pipeline.writers.panchanga_writer_a4_adapter — A4 Panchanga adapter.

Bridges the standard WRITER_REGISTRY write(build_id, chart_id, ayanamsha_id, chart_output, conn)
signature to the real panchanga_writer_a4.write_panchanga_limbs() which expects
(conn, chart_id, build_id, birth_date, chart_outputs_by_ayanamsha).

Falls back gracefully if birth_date cannot be determined.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    A4 Panchanga adapter: routes to real panchanga_writer_a4.write_panchanga_limbs.

    Extracts birth_date from chart_output and wraps chart_output in the
    {ayanamsha_id: chart_output} dict that write_panchanga_limbs expects.
    """
    birth_date = (
        chart_output.get('birth_date')
        or chart_output.get('date')
        or chart_output.get('birth_day')
    )

    if not birth_date:
        logger.warning(
            "A4 adapter: missing birth_date for chart=%s, skipping", chart_id
        )
        return 0

    # Normalise birth_date to YYYY-MM-DD string
    birth_date_str = str(birth_date)[:10]

    # Build the {ayanamsha_id: chart_output} dict that write_panchanga_limbs expects
    chart_outputs_by_ayanamsha = {ayanamsha_id: chart_output}

    try:
        from pipeline.writers.panchanga_writer_a4 import write_panchanga_limbs
        rows_written = write_panchanga_limbs(
            conn, chart_id, build_id, birth_date_str, chart_outputs_by_ayanamsha
        )
        logger.info(
            "A4 adapter complete: chart=%s ayanamsha=%s rows=%d",
            chart_id, ayanamsha_id, rows_written,
        )
        return rows_written
    except ValueError as exc:
        # No panchanga_daily row for this date — non-fatal, log and return 0
        logger.warning("A4 adapter: panchanga_daily miss for %s: %s", birth_date_str, exc)
        return 0
    except ImportError as exc:
        logger.error("A4 adapter: cannot import panchanga_writer_a4: %s", exc)
        return 0
    except Exception as exc:
        logger.error(
            "A4 adapter: write_panchanga_limbs failed for chart=%s ayanamsha=%s: %s",
            chart_id, ayanamsha_id, exc,
        )
        raise
