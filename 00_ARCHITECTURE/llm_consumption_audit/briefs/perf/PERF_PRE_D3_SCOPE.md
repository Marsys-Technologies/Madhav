---
artifact: PERF_PRE_D3_SCOPE
type: SCOPED SESSION NOTE (not a doctrine-wave brief; standalone perf work between D-2 close and D-3 open)
status: ACTIVE
opened: 2026-07-17
governing: this note only. Does NOT touch CONDUCTOR_PROTOCOL.md, BRIEF_D3.md, or any wave's
  FROZEN §F1/§F2/§G. D-3 has not opened; this work is orthogonal to it (verified: neither D2 nor
  D3-prep touched ga_strength_writer.py, ga_vargas writer, or bo_samskara.py).

## Goal
Speed up the L1/L2 heavy-writer critical path (ga_strength row-by-row insert, ga_vargas row-by-row
insert, bo_samskara re-embeds every rebuild, orchestrator worker-limit oversubscription vs job vCPU)
without changing any writer's computed output. Motivated by CLAUDE.md §N.4 (deterministic-first) and
the invoice cost-optimization session that traced ~74 rebuilds/day driving Artifact Registry + Vertex
API cost.

## may_touch
- platform/python-sidecar/ga_writers/ga_strength_writer.py (insert path only)
- platform/python-sidecar/ga_writers/ga_vargas_writer.py (insert path only, if same pattern found)
- platform/python-sidecar/pipeline/orchestrator/writers/bo_samskara.py (embedding-reuse + insert path)
- platform/python-sidecar/pipeline/orchestrator/runner.py (ORCHESTRATOR_WORKER_LIMIT read-path only,
  no contract change)
- Cloud Run Job env var `ORCHESTRATOR_WORKER_LIMIT` on brahma-build-pipeline-job (config only)
- test files colocated with the above writers

## must_not_touch
- FROZEN orchestrator contract (WriterBase, register, run/plan_substeps/run_substep signatures)
- Any file inside 00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/ (D-2/D-3/D-4 briefs,
  CONDUCTOR_PROTOCOL.md, STATE_*.md ledgers)
- Abhisek's canonical chart (482012f1) — verification runs ONLY against the test chart
  (Abhinandan, 1c826d5a) per this note; 482012f1 is not touched until D-3 rebuilds it post-verify
- Any writer/asset outside the 3 named above
- chart_facts / chart_dashas / bodha_signal_embeddings schemas (no migration in this scope)

## Verification gate (must pass before deploy is considered final)
1. Local: pytest (sidecar suite per CONDUCTOR_PROTOCOL §8.6), tsc/lint N/A (Python-only change)
2. Run A (baseline, current deployed code) vs Run B (optimized) on test chart 1c826d5a:
   substantive-value hash parity per asset (chart_facts / chart_dashas / bodha_signal_embeddings
   rows for ga_strength, ga_vargas, bo_samskara — excluding surrogate cols fact_id/embedding_id/
   computed_at/build_id) + FORENSIC-equivalent sanity + ga_strength two-pass invariants
   (shadbala sub-sums, ashtakavarga sarva=337) + speedup measured via build_run_assets timings
3. Gate: parity clean -> ship. Not clean -> fix or roll back to the pinned pre-change image.

## Close condition
This note is superseded/archived once the optimized image is verified + deployed and D-3 opens
(D-3's own gate becomes the second, independent verification on the canonical chart).
