"""
pipeline/orchestrator/writers/ka_vedha_gochara.py
Orchestrator registration shim for ka_vedha_gochara (ṢAḌ-DARŚANA W3,
registry item 5 — Vedha application + Sarvatobhadra chakra grid, closes
defect R-19).

The @register('ka_vedha_gochara') decorator fires on import of this module,
which discover_all() triggers when iterating
pipeline/orchestrator/writers/. All implementation logic lives in
services/ka_vedha_gochara/{logic,writer}.py — read that module's docstring
FIRST for the full R-19 honesty disclosure (what this writer does and does
not close).

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_vedha_gochara') → WriterBase subclass
    (services/ka_vedha_gochara/writer.py)
  - LIGHT writer: single run(ctx) call
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart delete-then-insert (§N.3)

Layer: L3 Kāla · Asset: ka_vedha_gochara (per_chart data writer)
Depends on: ga_positions (natal MOON longitude fact), bg_ephemeris
(ephemeris_daily), bg_transit_rules (house-vedha reference rules).
"""
from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter  # noqa: F401

__all__ = ["KaVedhaGocharaWriter"]
