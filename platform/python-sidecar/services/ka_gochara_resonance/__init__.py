"""
ka_gochara_resonance — Resonance Map (D-5 Lane G-1, L3 Kāla).

Public API
----------
    from services.ka_gochara_resonance.writer import KaGocharaResonanceWriter

Populates `gochara_resonance_map`: per-chart x event-class classical-prior-
weighted target sets (bhavas, lords, karakas, bg_transit_rules mechanism
nodes, sensitive degrees, arudhas, yoga constituents, dasha-lord
portfolios), consumed read-only by D-5 Lane G-3's transit-intensity engine.
"""
from .writer import KaGocharaResonanceWriter, build_resonance_rows

__all__ = ["KaGocharaResonanceWriter", "build_resonance_rows"]
