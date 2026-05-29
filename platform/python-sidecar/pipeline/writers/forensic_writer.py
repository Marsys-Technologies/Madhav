"""
forensic_writer.py — MARSYS-JIS A2 FORENSIC.md render writer
STUB: Emits build events but writes no data.
Real implementation in Stream F sessions.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A2_forensic_render"
ASSET_LABEL = "FORENSIC.md Render"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Stub writer for A2 FORENSIC render.
    Returns rows_written = 0 (stub — no data written).
    Real implementation: Stream F sessions F-01 through F-14.
    """
    logger.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0
