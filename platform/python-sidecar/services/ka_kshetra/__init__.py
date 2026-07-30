"""
services.ka_kshetra — the W2 field pipeline (ṢAḌ-DARŚANA campaign, wave W2).

Built by five parallel lanes, each owning disjoint files (see
KALA_W2_FIELD_DESIGN_v1_0.md §0). This `__init__.py` is shared, additive
territory: each lane exports its own published symbols here without
importing (or depending on the presence of) another lane's module, so a
lane landing before or after another never breaks import.

Lane B (this PR) owns `stage3_clocks.py` (Law-1 applicability, item 12)
and `uncertainty.py` (the uncertainty budget + interval propagation, item
24-full).
"""
from __future__ import annotations

from . import stage3_clocks
from . import uncertainty

__all__ = ["stage3_clocks", "uncertainty"]
