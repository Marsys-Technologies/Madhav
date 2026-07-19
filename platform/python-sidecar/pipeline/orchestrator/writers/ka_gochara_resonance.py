"""
pipeline/orchestrator/writers/ka_gochara_resonance.py
Orchestrator registration shim for ka_gochara_resonance (L3 Kāla — D-5 Lane G-1
Resonance Map).

The @register('ka_gochara_resonance') decorator fires on import of this
module, which discover_all() triggers when iterating
pipeline/orchestrator/writers/. All implementation logic lives in
services/ka_gochara_resonance/writer.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_gochara_resonance') → WriterBase subclass (done in
    services/ka_gochara_resonance/writer.py)
  - run(ctx) → WriterResult(rows_inserted=<N>)
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart delete-then-insert (§N.3)

Layer: L3 Kāla · Asset: ka_gochara_resonance (per_chart data writer)
Do NOT confuse with ka_gochara — a separate, unrelated service-health
self-test asset. This is a fresh asset_set addition, not a modification of
ka_gochara.
"""
from services.ka_gochara_resonance.writer import KaGocharaResonanceWriter  # noqa: F401

__all__ = ["KaGocharaResonanceWriter"]
