"""
cdlm_writer.py — MARSYS-JIS A11 CDLM Cross-Domain Links writer
STUB: Emits build events but writes no data.
Real implementation in Stream G2 sessions.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A11_cdlm"
ASSET_LABEL = "CDLM Cross-Domain Links"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Stub writer for A11 CDLM Cross-Domain Links.
    Returns rows_written = 0 (stub — no data written).
    Real implementation: Stream G2 sessions.
    """
    logger.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0
