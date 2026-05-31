"""
pyjhora_adapter — PyJHora-backed natal chart engine.

Sole chart computation engine for the MARSYS-JIS sidecar (native decision).
Public surface: `compute_chart(inputs, engine_version, ayanamsha_id) -> dict`.

Headless import discipline: this package NEVER does `import jhora` at module
load — it imports only PyJHora's calculation submodules (panchanga.drik,
horoscope.chart.charts, horoscope.dhasa.graha.vimsottari) via ._jhora, which do
not pull PyQt6. See ._jhora for the rationale.
"""
from __future__ import annotations

from .compute import compute_chart
from .l25_builder import build_all, canonical_jsonl
from .version import ENGINE_VERSION

__all__ = ["compute_chart", "ENGINE_VERSION", "build_all", "canonical_jsonl"]
