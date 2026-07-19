"""
pipeline/orchestrator/writers/ka_gochara_sweep.py
Orchestrator registration shim for ka_gochara_sweep (L3 Kāla — D-5 Lane G-4
Forward sweep + serving).

The @register('ka_gochara_sweep') decorator fires on import of this module,
which discover_all() triggers when iterating
pipeline/orchestrator/writers/. All implementation logic lives in
services/ka_gochara_sweep/{writer,sweep,shape_output}.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_gochara_sweep') → WriterBase subclass (services/ka_gochara_sweep/writer.py)
  - HEAVY writer: plan_substeps(ctx) + run_substep(ctx, step) — one substep
    per (populated gochara_resonance_map event_class x decade) — a
    birth->birth+100y daily grid is far too large for a single-substep
    (light-writer) run (BRIEF_D5 §1 G-4 row: "the one lane in this wave
    explicitly expected to need real sub-stepping").
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart, per-event-class delete-then-insert (§N.3), with
    cross-attempt substep resumption via build_substep_progress (migration 436).

Layer: L3 Kāla · Asset: ka_gochara_sweep (per_chart data writer)
Depends on: ka_gochara_resonance (G-1's gochara_resonance_map).
"""
from services.ka_gochara_sweep.writer import KaGocharaSweepWriter  # noqa: F401

__all__ = ["KaGocharaSweepWriter"]
