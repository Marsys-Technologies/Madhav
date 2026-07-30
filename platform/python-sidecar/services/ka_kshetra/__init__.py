"""
services.ka_kshetra — ṢAḌ-DARŚANA W2 "the field as science" pipeline.

This package holds the ten-stage point-process pipeline's per-stage modules.
Lane A owns stage0_kinematics.py, stage1_symbolization.py, stage2_promise.py,
and the shared contracts.py. Lane B (this contribution) owns stage3_clocks.py
(Law-1 applicability, item 12) and uncertainty.py (the uncertainty budget +
interval propagation, item 24-full). Lanes C/D/E add their own stage modules
(stage4_field.py, hazard.py, integrator.py, stage5_null.py, stage6_salience.py,
submodular.py, cohort_client.py, stage65_insights.py, stage8_spec.py) — see
KALA_W2_FIELD_DESIGN_v1_0.md §0 for the full lane table.

This `__init__.py` is shared, additive territory: each lane exports its own
published symbols here without importing (or depending on the presence of)
another lane's module, so a lane landing before or after another never breaks
import.

The orchestration shim (`pipeline/orchestrator/writers/ka_kshetra.py`,
`@register('ka_kshetra')`) is written ONCE by Lane C and is NOT part of this
package — it imports from here, never the reverse.
"""
from __future__ import annotations

from . import stage3_clocks
from . import uncertainty

__all__ = ["stage3_clocks", "uncertainty"]
