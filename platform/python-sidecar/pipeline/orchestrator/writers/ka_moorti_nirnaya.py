"""
pipeline/orchestrator/writers/ka_moorti_nirnaya.py
Orchestrator registration shim for ka_moorti_nirnaya (ṢAḌ-DARŚANA W3,
registry item 4 — Moorti-nirṇaya per ingress per chart).

The @register('ka_moorti_nirnaya') decorator fires on import of this module,
which discover_all() triggers when iterating
pipeline/orchestrator/writers/. All implementation logic lives in
services/ka_moorti_nirnaya/{logic,writer}.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_moorti_nirnaya') → WriterBase subclass
    (services/ka_moorti_nirnaya/writer.py)
  - LIGHT writer: single run(ctx) call
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart delete-then-insert (§N.3)

Layer: L3 Kāla · Asset: ka_moorti_nirnaya (per_chart data writer)
Depends on: ga_positions (natal MOON longitude fact), bg_ephemeris
(ephemeris_daily), bg_transit_rules (bg_transit_moorti reference table).
"""
from services.ka_moorti_nirnaya.writer import KaMoortiNirnayaWriter  # noqa: F401

__all__ = ["KaMoortiNirnayaWriter"]
