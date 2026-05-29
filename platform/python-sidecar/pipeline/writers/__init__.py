# pipeline.writers — pluggable writer implementations (IBuildWriter)
"""
MARSYS-JIS per-chart asset writers.
Stub implementations — real writers added by streams F, G1, G2, G3, G4.

C-07: WRITER_REGISTRY added — maps 13 asset_ids (A2–A14) to stub write() callables.

Note: chart_facts_writer and sade_sati_writer carry heavy Phase-14B imports (psycopg,
jsonschema, gcs) at module level. WRITER_REGISTRY imports their write() stubs via
lazy import to avoid pulling in those heavy deps when the registry is used in contexts
without those packages (e.g. build_chart pipeline on minimal install).
"""
import logging
from typing import Optional

_log = logging.getLogger(__name__)

from .forensic_writer import write as write_forensic
from .panchanga_writer import write as write_panchanga
from .sensitive_points_writer import write as write_sensitive_points
from .vargas_writer import write as write_vargas
from .dashas_writer import write as write_dashas
from .t1_structural_writer import write as write_t1_structural
from .msr_writer import write as write_msr
from .cdlm_writer import write as write_cdlm
from .cgm_writer import write as write_cgm
from .rm_writer import write as write_rm
from .ucn_digest_writer import write as write_ucn_digest


# chart_facts_writer (A3) and sade_sati_writer (A9) carry heavy Phase-14B
# module-level imports (psycopg, jsonschema, google-cloud-storage).  We wrap
# their stubs in lightweight closures so that importing WRITER_REGISTRY does
# not drag in those heavy deps on minimal installs (e.g. CI, tests, build_chart).

def _write_chart_facts(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: Optional[dict] = None,
) -> int:
    """Stub writer for A3 Chart Facts (build_chart dispatch registry)."""
    _log.info(
        "[STUB] Chart Facts (L1 Structured): chart=%s ayanamsha=%s build=%s",
        chart_id, ayanamsha_id, build_id,
    )
    return 0


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
    'A4_panchanga':        write_panchanga,
    'A5_sensitive_points': write_sensitive_points,
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
