"""
services/ka_kshetra — ṢAḌ-DARŚANA Wave W2, "the field as science".

The ten-stage point-process pipeline behind the `ka_kshetra` asset. Built BESIDE
the legacy L3 writers (strangler-fig): `ka_gochara_sweep`, `ka_sangam`,
`ka_yojaka`, `ka_kalasutra` and `ka_taranga` keep running and keep serving
through W2, and this package writes ZERO rows to any legacy table.

MODULE MAP (lane ownership per KALA_W2_FIELD_DESIGN_v1_0.md §0):
  contracts.py       shared dataclasses that cross lane boundaries (owned by
                     nobody; frozen by the design, edited only by a cross-lane PR)
  hazard.py          §5.1 the hazard formula                          Lane C
  integrator.py      §5.2 log-linear segments + exact integration     Lane C
  stage4_field.py    §5.2-§5.4 field assembly + provenance            Lane C
  stage5_null.py     §5.5-§5.6 circular-shift null + robustness       Lane C
  writer.py          the @register('ka_kshetra') WriterBase subclass  Lane C
  stage0_kinematics.py / stage1_symbolization.py / stage2_promise.py  Lane A
  stage3_clocks.py / uncertainty.py                                   Lane B
  stage6_salience.py / submodular.py / cohort_client.py /
    stage65_insights.py                                               Lane D
  stage8_spec.py                                                      Lane E

This `__init__.py` is shared, additive territory: each lane exports its own
published symbols here without importing (or depending on the presence of)
another lane's module, so a lane landing before or after another never breaks
import. A lane with nothing to pre-export (e.g. Lane C's modules are imported
directly by the orchestration shim, not re-exported here) adds none.

THE CIRCULARITY GUARD (section 8.3 - a HARD, unsoftenable campaign gate, peer of
LAW ZERO): stages 0-8 NEVER read the life-event log. The field is a pure function
of (chart, corpus_pin, config_pin, weights_version, cohort_version); only stage 9
(`mi_bhara`, Lane E) may see lived outcomes. The invariant is stated over the
field CONTENT hash and is enforced by two independent detectors - a static source
census and a dynamic hash-invariance test under LEL mutation - in
tests/l3/ka_kshetra/test_circularity_guard.py.

The orchestration shim (`pipeline/orchestrator/writers/ka_kshetra.py`,
`@register('ka_kshetra')`) is written ONCE by Lane C and is NOT part of this
package — it imports from here, never the reverse.
"""
from __future__ import annotations

from . import stage3_clocks
from . import uncertainty

__all__ = ["stage3_clocks", "uncertainty"]
