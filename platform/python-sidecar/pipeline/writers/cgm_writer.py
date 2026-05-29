"""
cgm_writer.py — MARSYS-JIS A12 CGM Graph Nodes + Edges writer
STUB: Emits build events but writes no data.
Real implementation in Stream G3 sessions.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A12_cgm"
ASSET_LABEL = "CGM Graph Nodes + Edges"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Stub writer for A12 CGM Graph Nodes + Edges.
    Returns rows_written = 0 (stub — no data written).
    Real implementation: Stream G3 sessions.
    """
    logger.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0
