"""
ka_muhurta_seva — Panchāṅga-Muhūrta Service (L3 Kāla)
=======================================================
Orchestrator-registered WriterBase shim for the ka_muhurta_seva service asset.

This thin file registers the writer under the orchestrator registry.
All implementation logic lives in:
  services/ka_muhurta_seva/writer.py  (FORENSIC self-test + health write)
  services/ka_muhurta_seva/service.py (score / find_windows public API)

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_muhurta_seva') → WriterBase subclass
  - run(ctx) → WriterResult(rows_inserted=0, rows_updated=0)
  - NEVER calls ctx.db_conn.commit() / rollback() / close()
  - NEVER writes asset_throughput
  - Honors ctx.dry_run

Layer: L3 Kāla · Asset: ka_muhurta_seva (service)
"""
# Import the writer from the services package; the @register decorator fires on import.
from services.ka_muhurta_seva.writer import KaMuhurtaSevaWriter  # noqa: F401

__all__ = ["KaMuhurtaSevaWriter"]
