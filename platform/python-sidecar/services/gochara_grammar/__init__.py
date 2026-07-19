"""
services.gochara_grammar — Lane G-2 "Configuration grammar" (D-5 Gochara-Chitra wave).

12 contact-primitive families + 6 composition operators over the resonance-map
targets G-1's `gochara_resonance_map` table supplies. Pure service module — no
orchestrator writer (BRIEF_D5 §9: "G-1/G-2/G-3 are pure service/schema work
consumed at query time, no orchestrator asset").

All ephemeris scanning is delegated to `pipeline.transit_search` (the FROZEN
low-level transit-detection primitive) -- this package never re-implements
swe.calc_ut / bisection search. See `primitives.py` module docstring for the
per-family mapping onto `transit_search` functions.

Citation discipline (B.10 / BRIEF_D5 §6, hard rule): every emitted
`ConfigurationSentence` / `CompositionSentence` carries EITHER a
`classical_citation` string reused verbatim from an already-attested codebase
source (never invented chapter/verse numbers) OR an explicit
`uncited_extension=True` flag. `models.py`'s dataclasses enforce this
mechanically in `__post_init__` -- construction fails loudly rather than
silently emitting an uncited-and-unflagged sentence.
"""
from __future__ import annotations

from .models import (
    ResonanceTarget,
    ConfigurationSentence,
    CompositionSentence,
    CitationDisciplineError,
)
from . import primitives
from . import composition
from . import sarvatobhadra
from . import resonance_map
from . import dasha_data

__all__ = [
    "ResonanceTarget",
    "ConfigurationSentence",
    "CompositionSentence",
    "CitationDisciplineError",
    "primitives",
    "composition",
    "sarvatobhadra",
    "resonance_map",
    "dasha_data",
]
