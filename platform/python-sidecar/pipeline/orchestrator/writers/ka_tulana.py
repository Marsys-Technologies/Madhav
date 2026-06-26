"""
pipeline/orchestrator/writers/ka_tulana.py
Orchestrator registration shim for ka_tulana (L3 Kāla — cross-pattern prioritization service).

The @register('ka_tulana') decorator fires on import of this module, which
discover_all() triggers when iterating pipeline/orchestrator/writers/.
All implementation logic lives in services/ka_tulana/writer.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_tulana') → WriterBase subclass (done in services/ka_tulana/writer.py)
  - run(ctx) → WriterResult(rows_inserted=0)
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput

Layer: L3 Kāla · Asset: ka_tulana (service)
"""
from services.ka_tulana.writer import KaTulanaWriter  # noqa: F401

__all__ = ["KaTulanaWriter"]
