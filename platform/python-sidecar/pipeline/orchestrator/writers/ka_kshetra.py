"""
pipeline/orchestrator/writers/ka_kshetra.py
Orchestrator registration shim for ka_kshetra (L3 Kāla — ṢAḌ-DARŚANA W2,
"the field as science").

The @register('ka_kshetra') decorator fires on import of this module, which
discover_all() triggers when iterating pipeline/orchestrator/writers/. ALL
implementation logic lives in services/ka_kshetra/ — this file is the side-effect
import and nothing else, exactly as ka_gochara_sweep.py is today.

WRITTEN ONCE, BY LANE C (KALA_W2_FIELD_DESIGN_v1_0.md §0): "The orchestration
shim `pipeline/orchestrator/writers/ka_kshetra.py` is written ONCE by Lane C (it
owns stage 4, the pipeline's centre of gravity) and consists of nothing but the
`@register('ka_kshetra')` side-effect import." Lanes A, B, D and E extend the
PIPELINE by adding `services/ka_kshetra/stage*.py` modules that the writer
discovers by name — never by editing this file or the orchestrator.

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE
§2 / CLAUDE.md §N.2):
  - @register('ka_kshetra') → WriterBase subclass (services/ka_kshetra/writer.py)
  - HEAVY writer: plan_substeps(ctx) + run_substep(ctx, step) — stage-4 decade
    slices, stage-5 replicate blocks, a per-class finalize, and a terminal
    snapshot substep
  - NEVER commits, rolls back or closes ctx.db_conn (orchestrator owns the
    transaction + savepoint per substep)
  - NEVER writes asset_throughput (orchestrator is the sole build-state writer)
  - Idempotent per-chart delete-then-insert (§N.3), performed exactly ONCE in
    plan_substeps, with cross-attempt substep resumption via
    build_substep_progress (migration 436 — untouchable; used, not changed)

Layer: L3 Kāla · Asset: ka_kshetra (per_chart data writer) · Registry seed row +
depends_on: migration 480.

Depends on (the EIGHT edges of §9.1, and exactly those eight): ka_dasha_kala,
ka_gochara_sweep (read-only cross-check corpus), ka_gochara_resonance,
ga_panchanga, bo_pratijna, bo_sangati, bo_upaya, bg_cohort.
  · NOT bg_sky_calendar — the W3 edge-staging rule (§9.1); W3 adds it in the same
    PR that lands that asset's seed row.
  · NOT mi_bhara — the acyclicity rule (§7.5); that edge would form the cycle
    ka_kshetra → mi_bhara → ka_kshetra and break EVERY chart build. The
    calibration loop closes across builds by weights-version pin instead
    (migration 476 seeds v0_classical so the very first build finds an active
    version).

CIRCULARITY GUARD (§8.3, a hard campaign gate): this writer and every module it
imports are on the stage 0–8 code path and NEVER read the life-event log. Both
halves of the detector live in
tests/l3/ka_kshetra/test_circularity_guard.py.
"""
from services.ka_kshetra.writer import KaKshetraWriter  # noqa: F401

__all__ = ["KaKshetraWriter"]
