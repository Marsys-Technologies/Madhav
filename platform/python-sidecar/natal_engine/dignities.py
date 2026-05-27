"""
dignities.py — Dignity refinement layer.

The scaffold computes exaltation / debilitation / own-sign in `positions.py`
inline. This module exists as a placeholder for unit 1.2's full dignity table
(temporal friendship, compound friendship, pancha-dha-maitri) so that the
shape of the engine is correct from day one. Today it's a passthrough.
"""

from __future__ import annotations

from .schema import GrahaState


def refine_dignities(grahas: list[GrahaState]) -> list[GrahaState]:
    """No-op passthrough. Unit 1.2 will compute pancha-dha-maitri here."""
    return grahas
