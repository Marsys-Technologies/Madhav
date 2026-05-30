# pipeline.writers — pluggable writer implementations (IBuildWriter)
"""
MARSYS-JIS per-chart asset writers.

C-07: WRITER_REGISTRY added — maps 13 asset_ids (A2–A14) to write() callables.
Phase A (UX overhaul): A3, A4, A5 upgraded from stubs to real implementations.

Note: chart_facts_writer_a3 and sade_sati_writer carry heavy imports (psycopg,
jsonschema, gcs) at module level. WRITER_REGISTRY imports their write() callables
via lazy import to avoid pulling in those heavy deps on minimal installs
(e.g. CI, tests, build_chart without full dep set).
"""
import logging
from typing import Optional

_log = logging.getLogger(__name__)

from .forensic_writer import write as write_forensic
from .vargas_writer import write as write_vargas
from .dashas_writer import write as write_dashas
from .t1_structural_writer import write as write_t1_structural
from .msr_writer import write as write_msr
from .cdlm_writer import write as write_cdlm
from .cgm_writer import write as write_cgm
from .rm_writer import write as write_rm
from .ucn_digest_writer import write as write_ucn_digest


# ── A3 Chart Facts — real writer (chart_facts_writer_a3) ─────────────────────

def _write_chart_facts(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """Real writer for A3 Chart Facts — Mula-Lakshana structured facts.

    Falls back to stub (returns 0) when conn is None or lacks cursor
    (e.g. in unit tests that pass conn=None).
    """
    if conn is None:
        _log.info(
            "[STUB/NO-CONN] Chart Facts: chart=%s ayanamsha=%s build=%s",
            chart_id, ayanamsha_id, build_id,
        )
        return 0
    try:
        from pipeline.writers.chart_facts_writer_a3 import write as _real_write
        return _real_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)
    except ImportError:
        pass
    try:
        from .chart_facts_writer_a3 import write as _real_write
        return _real_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)
    except ImportError:
        _log.warning("[FALLBACK] chart_facts_writer_a3 not importable; A3 stub active")
        _log.info(
            "[STUB] Chart Facts (L1 Structured): chart=%s ayanamsha=%s build=%s",
            chart_id, ayanamsha_id, build_id,
        )
        return 0


# ── A4 Panchanga — real writer (panchanga_writer_a4_adapter) ─────────────────

def _write_panchanga(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """Real writer for A4 Panchanga — routes to panchanga_writer_a4 via adapter."""
    try:
        from pipeline.writers.panchanga_writer_a4_adapter import write as _real_write
        return _real_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)
    except ImportError:
        pass
    try:
        from .panchanga_writer_a4_adapter import write as _real_write
        return _real_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)
    except ImportError:
        _log.warning("[FALLBACK] panchanga_writer_a4_adapter not importable; A4 stub active")
        from .panchanga_writer import write as _stub_write
        return _stub_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)


# ── A5 Sensitive Points — real writer (sensitive_points_writer_a5_adapter) ────

def _write_sensitive_points(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """Real writer for A5 Marma-Bindu — routes to sensitive_points_writer_a5 via adapter."""
    try:
        from pipeline.writers.sensitive_points_writer_a5_adapter import write as _real_write
        return _real_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)
    except ImportError:
        pass
    try:
        from .sensitive_points_writer_a5_adapter import write as _real_write
        return _real_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)
    except ImportError:
        _log.warning("[FALLBACK] sensitive_points_writer_a5_adapter not importable; A5 stub active")
        from .sensitive_points_writer import write as _stub_write
        return _stub_write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra)


# ── A9 Sade-Sati — stub (real implementation pending) ────────────────────────

def _write_sade_sati(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """Stub writer for A9 Sade-Sati Phases (build_chart dispatch registry)."""
    _log.info(
        "[STUB] Sade-Sati Phases: chart=%s ayanamsha=%s build=%s",
        chart_id, ayanamsha_id, build_id,
    )
    return 0


WRITER_REGISTRY = {
    'A2_forensic_render':  write_forensic,
    'A3_chart_facts':      _write_chart_facts,
    'A4_panchanga':        _write_panchanga,
    'A5_sensitive_points': _write_sensitive_points,
    'A6_vargas':           write_vargas,
    'A7_dashas':           write_dashas,
    'A8_t1_structural':    write_t1_structural,
    'A9_sade_sati':        _write_sade_sati,
    'A10_msr':             write_msr,
    'A11_cdlm':            write_cdlm,
    'A12_cgm':             write_cgm,
    'A13_rm':              write_rm,
    'A14_ucn_digest':      write_ucn_digest,
}

__all__ = ['WRITER_REGISTRY']
