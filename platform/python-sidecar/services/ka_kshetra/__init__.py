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

THE CIRCULARITY GUARD (section 8.3 - a HARD, unsoftenable campaign gate, peer of
LAW ZERO): stages 0-8 NEVER read the life-event log. The field is a pure function
of (chart, corpus_pin, config_pin, weights_version, cohort_version); only stage 9
(`mi_bhara`, Lane E) may see lived outcomes. The invariant is stated over the
field CONTENT hash and is enforced by two independent detectors - a static source
census and a dynamic hash-invariance test under LEL mutation - in
tests/l3/ka_kshetra/test_circularity_guard.py.
"""
