"""
pipeline/orchestrator/writers/ka_sudarshana_varsha.py
Orchestrator registration shim for ka_sudarshana_varsha (ṢAḌ-DARŚANA W3,
registry item 17 — Sudarśana-Chakra year-wheel triple-lagna progression).

BINDING NAMING RULING (do not revisit): this asset is `ka_sudarshana_varsha`,
never bare `sudarshana` — `bo_sudarshana` (L2 Bodha) is a confirmed
namesake-only collision, different layer, different (static, non-temporal)
computation. See services/ka_sudarshana_varsha/logic.py's module docstring
for the full distinction.

The @register('ka_sudarshana_varsha') decorator fires on import of this
module, which discover_all() triggers when iterating
pipeline/orchestrator/writers/. All implementation logic lives in
services/ka_sudarshana_varsha/{logic,writer}.py.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - @register('ka_sudarshana_varsha') → WriterBase subclass
    (services/ka_sudarshana_varsha/writer.py)
  - LIGHT writer: single run(ctx) call (120 rows/chart, pure arithmetic)
  - NEVER commits or closes ctx.db_conn (orchestrator owns the transaction)
  - NEVER writes asset_throughput
  - Idempotent per-chart delete-then-insert (§N.3)

Layer: L3 Kāla · Asset: ka_sudarshana_varsha (per_chart data writer)
Depends on: ga_positions (natal LAGNA/MOON/SUN sign facts).
"""
from services.ka_sudarshana_varsha.writer import KaSudarshanaVarshaWriter  # noqa: F401

__all__ = ["KaSudarshanaVarshaWriter"]
