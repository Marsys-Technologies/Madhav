"""
dashas_writer.py — MARSYS-JIS A7 Dasha / Sub-Dasha Chains writer
STUB: Emits build events but writes no data.
Real implementation in Stream F sessions.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A7_dashas"
ASSET_LABEL = "Dasha / Sub-Dasha Chains"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Stub writer for A7 Dasha / Sub-Dasha Chains.
    Returns rows_written = 0 (stub — no data written).
    Real implementation: Stream F sessions.
    """
    logger.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0
