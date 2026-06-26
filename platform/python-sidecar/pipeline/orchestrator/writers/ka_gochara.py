"""
pipeline/orchestrator/writers/ka_gochara.py
Orchestrator registration shim for ka_gochara (L3 Kāla K2 — transit-search service).

The @register('ka_gochara') decorator fires on import of this module, which
discover_all() triggers when iterating pipeline/orchestrator/writers/.
All implementation logic lives in services/ka_gochara/writer.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_gochara') → WriterBase subclass (done in services/ka_gochara/writer.py)
  - run(ctx) → WriterResult(rows_inserted=0)
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput

Layer: L3 Kāla · Asset: ka_gochara (service)
"""
from services.ka_gochara.writer import KaGocharaWriter  # noqa: F401

__all__ = ["KaGocharaWriter"]
