"""
pipeline/orchestrator/writers/ka_tithi_pravesha.py
Orchestrator registration shim for ka_tithi_pravesha (ṢAḌ-DARŚANA W3,
registry item 13 — Tithi-Praveśa lunar-return annual chart).

The @register('ka_tithi_pravesha') decorator fires on import of this module,
which discover_all() triggers when iterating pipeline/orchestrator/writers/.
All implementation logic lives in services/ka_tithi_pravesha/{logic,writer}.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_tithi_pravesha') → WriterBase subclass
    (services/ka_tithi_pravesha/writer.py)
  - LIGHT writer: single run(ctx) call (120 rows/chart; real ephemeris
    root-find + annual-chart cast per row, benchmarked ~3.4ms/row)
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart delete-then-insert (§N.3)

Layer: L3 Kāla · Asset: ka_tithi_pravesha (per_chart data writer)
Depends on: ga_positions (natal MOON longitude_sidereal fact).
"""
from services.ka_tithi_pravesha.writer import KaTithiPraveshaWriter  # noqa: F401

__all__ = ["KaTithiPraveshaWriter"]
