"""
services.ka_gochara_sweep — Lane G-4 "Forward sweep + serving" (D-5
Gochara-Chitra wave).

Chart-relative birth->birth+100y daily-grid sweep of G-3's lambda_e(t|chart)
engine, shape-aware (BRIEF_D5 §3) served rows into `kala_gochara_windows`.
Consumes G-1 (`gochara_resonance_map`), G-2 (`gochara_grammar`), and G-3
(`gochara_intensity`) read-only.

  shape_output.py — pure shape-dispatch row builders (unit-testable on
                     constructed fixtures, no DB/ephemeris).
  sweep.py         — live driver: resolves ontology metadata + calls G-3's
                      engine over a bounded horizon chunk.
  writer.py         — the orchestrator-facing HEAVY WriterBase subclass
                       (plan_substeps/run_substep, per event_class x decade).
                       RETIRED (MR-09): writer.py is preserved for forensic
                       reference but is no longer imported here so that
                       `@register('ka_gochara_sweep')` does NOT fire when
                       this package is imported as a dependency (e.g. from
                       services/w2g/materialize.py which only needs
                       shape_output + sweep, not the writer).

MR-09 DISCOVERABILITY NOTE:
  The `writer.py` import was removed from this __init__.py because
  `services/w2g/materialize.py` imports from this package (shape_output +
  sweep), which formerly caused @register('ka_gochara_sweep') to fire
  transitively even though the sweep writer is RETIRED.  Removing the
  writer import here gates discoverability at the source: the writer class
  exists in writer.py but is only reachable via an explicit
  `from services.ka_gochara_sweep.writer import KaGocharaSweepWriter`
  import — not via the package __init__.  The orchestrator shim
  (pipeline/orchestrator/writers/ka_gochara_sweep.py) was also updated
  to not import the writer (MR-09 Item 3).
"""
from __future__ import annotations

# NOTE: writer.py is intentionally NOT imported here (see MR-09 note above).
# Only the computation modules (shape_output, sweep) are re-exported, because
# they are used by services/w2g/materialize.py and must remain importable.
from .shape_output import build_rows_for_event_class, build_point_rows, build_interval_rows, build_chain_rows
from .sweep import sweep_event_class_chunk, fetch_ontology_meta

__all__ = [
    "build_rows_for_event_class",
    "build_point_rows",
    "build_interval_rows",
    "build_chain_rows",
    "sweep_event_class_chunk",
    "fetch_ontology_meta",
    # KaGocharaSweepWriter is NOT exported here — import directly from .writer
    # if needed (only for forensic reference; the writer is RETIRED).
]
