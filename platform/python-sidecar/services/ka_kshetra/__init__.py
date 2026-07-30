"""
`ka_kshetra` (Kāla Kṣetra — "the field of time") — the ṢAḌ-DARŚANA W2 ten-stage point-process
pipeline, L3 Kāla-seated, built BESIDE the legacy Kāla writers (strangler-fig; brief §7 rail
2 — `kala_gochara_windows` data, `build_substep_progress` and the sealed harness are
untouchable, and `ka_gochara_sweep` / `ka_sangam` / `ka_yojaka` / `ka_kalasutra` / `ka_taranga`
keep running and keep serving through W2).

This package is built by FIVE PARALLEL LANES with disjoint file ownership
(`KALA_W2_FIELD_DESIGN_v1_0.md` §0):

    Lane A  stage0_kinematics.py · stage1_symbolization.py · stage2_promise.py
    Lane B  stage3_clocks.py · uncertainty.py
    Lane C  stage4_field.py · hazard.py · integrator.py · stage5_null.py
    Lane D  stage6_salience.py · submodular.py · cohort_client.py · stage65_insights.py
    Lane E  stage8_spec.py                                              ← this lane's only file

A lane never reads another lane's CODE; it reads another lane's TABLE (or calls its one
published function). This `__init__.py` is therefore deliberately inert — no re-exports, no
imports — so that adding a module to the package can never, by itself, create a cross-lane
import edge.

CIRCULARITY GUARD (brief §7 rail, peer of LAW ZERO): stages 0–8 NEVER read the LEL. The field
is a pure function of `(chart, corpus_pin, config_pin, weights_version, cohort_version)`.
Stage 9 (`services/mi_bhara/`) is the only stage that may see it. Both halves of the guard —
a static census over this package's source, and an empirical LEL-mutation invariance proof —
are enforced by `tests/l5/test_mi_bhara_circularity_guard_w2.py` and by
`.github/workflows/shad-darshana-circularity-guard.yml`.
"""
