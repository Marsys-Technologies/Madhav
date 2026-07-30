"""
services.ka_kshetra — ṢAḌ-DARŚANA W2 "the field as science" pipeline.

This package holds the ten-stage point-process pipeline's per-stage modules.
Lane A (this package's initial contribution) owns stage0_kinematics.py,
stage1_symbolization.py, stage2_promise.py, and the shared contracts.py.
Lanes B/C/D/E add their own stage modules (stage3_clocks.py, stage4_field.py,
hazard.py, integrator.py, stage5_null.py, stage6_salience.py, submodular.py,
cohort_client.py, stage65_insights.py, stage8_spec.py) in their own PRs — see
KALA_W2_FIELD_DESIGN_v1_0.md §0 for the full lane table.

The orchestration shim (`pipeline/orchestrator/writers/ka_kshetra.py`,
`@register('ka_kshetra')`) is written ONCE by Lane C and is NOT part of this
package — it imports from here, never the reverse.
"""
from __future__ import annotations

__all__: list[str] = []
