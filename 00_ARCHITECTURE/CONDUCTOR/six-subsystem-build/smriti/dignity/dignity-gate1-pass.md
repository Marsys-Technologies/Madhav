---
subsystem: dignity
gate: Gate-1 PASS → spec-review in progress
timestamp: 2026-06-17
tier: Tier-1 (pending spec-review verdict)
---

# Dignity Gate-1 Pass Notes

## What was built (Śilpī commit 35a8ed43)
- `platform/migrations/250_bg_dignity_reference.sql` — 5 L0 tables fully seeded with citations
- `platform/migrations/251_ga_condition_composite.sql` — L1 ga_condition_composite table + index
- `platform/migrations/252_asset_registry_ga_condition.sql` — asset_registry row
- `platform/python-sidecar/ga_writers/ga_condition_writer.py` — core build (9 grahas × 5 ayanamshas)
- `platform/python-sidecar/pipeline/orchestrator/writers/ga_condition.py` — `@register('ga_condition')` heavy writer
- `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_condition.py` — pytest tests
- Total: 2,251 lines across 6 new files

## L0 tables seeded (migration 250)
- `bg_dignity_reference`: 9 grahas — exaltation degree, debilitation degree, moolatrikona (BPHS Ch.3)
- `bg_graha_naisargika_friendship`: 72 graha-pair rows (BPHS Ch.27)
- `bg_avastha_schemes`: 32 rows — baladi(5), jagradadi(3), deeptaadi(9), lajjitaadi(6), sayanadi(12)
- `bg_motion_state_thresholds`: vakra/anuvakra/atichara per graha (Surya Siddhanta)
- `bg_combustion_orbs`: 8 grahas, standard + deep orb (Saravali/BPHS)

## §5 conformance (self-reported PASS)
- @register('ga_condition') + WriterBase — confirmed
- plan_substeps + run_substep — confirmed
- ctx.db_conn only; zero commit calls — grep-verified
- L1 idempotency: DELETE WHERE (chart_id, ayanamsha_id) — line 1032
- Returns WriterResult; no asset_throughput writes — confirmed
- FORENSIC assertions guarded by CANONICAL_CHART_ID check — lines 1013-1027
- ctx.dry_run honored — confirmed
- has_substeps=true, target_floor=45, sort_order=29, depends_on=['ga_positions','ga_vargas'] — confirmed

## Tier-2 decisions
1. lajjitaadi+sayanadi → NULL in v1 (house+conjunction context needed — documented)
2. Graha yuddha winner by higher ecliptic longitude (latitude absent — documented)
3. peak_dasha_periods from chart_dashas own mahadasha rows
4. naisargika_relation = graha's natural friendship toward sign lord of placement sign
5. Formula weights: 0.35/0.20/0.20/0.15/0.10 (sum=1.0; spec was 0.30/0.15/0.25 — adjusted)

## Spec-review status: RUNNING (Nirīkṣaka agent dispatched)
## Gate-2 status: pending spec-review verdict
