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
"""
from __future__ import annotations

from .writer import KaGocharaSweepWriter
from .shape_output import build_rows_for_event_class, build_point_rows, build_interval_rows, build_chain_rows
from .sweep import sweep_event_class_chunk, fetch_ontology_meta

__all__ = [
    "KaGocharaSweepWriter",
    "build_rows_for_event_class",
    "build_point_rows",
    "build_interval_rows",
    "build_chain_rows",
    "sweep_event_class_chunk",
    "fetch_ontology_meta",
]
