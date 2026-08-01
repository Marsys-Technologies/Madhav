"""
pipeline/orchestrator/writers/ka_kota_chakra.py
Orchestrator registration shim for ka_kota_chakra (ṢAḌ-DARŚANA W3, registry
item 16 — Kota-Chakra fort chart).

The @register('ka_kota_chakra') decorator fires on import of this module,
which discover_all() triggers when iterating
pipeline/orchestrator/writers/. All implementation logic lives in
services/ka_kota_chakra/{logic,writer}.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_kota_chakra') → WriterBase subclass (services/ka_kota_chakra/writer.py)
  - LIGHT writer: single run(ctx) call (small data volume — see writer.py docstring)
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart delete-then-insert (§N.3)

Layer: L3 Kāla · Asset: ka_kota_chakra (per_chart data writer)
Depends on: ga_positions (natal Moon longitude), bg_ephemeris (transiting
positions), bg_kota_chakra_rings (ring partition — ADJUDICATION-9,
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md; moved off an inline writer-code
dict onto this versioned L0 asset).
"""
from services.ka_kota_chakra.writer import KaKotaChakraWriter  # noqa: F401

__all__ = ["KaKotaChakraWriter"]
