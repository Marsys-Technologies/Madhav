"""
msr_writer.py — MARSYS-JIS A10 MSR Signal Store writer
STUB: Emits build events but writes no data.
Real implementation in Stream G1 sessions.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A10_msr"
ASSET_LABEL = "MSR Signal Store"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Stub writer for A10 MSR Signal Store.
    Returns rows_written = 0 (stub — no data written).
    Real implementation: Stream G1 sessions.
    """
    logger.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0
