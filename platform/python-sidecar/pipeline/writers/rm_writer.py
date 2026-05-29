"""
rm_writer.py — MARSYS-JIS A13 RM Resonance Map writer
STUB: Emits build events but writes no data.
Real implementation in Stream G4 sessions.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ASSET_ID = "A13_rm"
ASSET_LABEL = "RM Resonance Map"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """
    Stub writer for A13 RM Resonance Map.
    Returns rows_written = 0 (stub — no data written).
    Real implementation: Stream G4 sessions.
    """
    logger.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0
