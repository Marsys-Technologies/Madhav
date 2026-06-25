---
subsystem: astrovastu
gate: Gate-2 IN PROGRESS
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Astrovastu Gate-2 Pass Notes

## Gate-1 → Gate-2 transition
- Gate-1 commit: 5b1784bc (Śilpī — 9 files, 24 tests)
- Spec-review verdict: SPEC_COMPLIANT_MINOR_GAPS → 5 real gaps

## Gap resolutions
1. **Gap 1 (ON CONFLICT idempotency)**: Removed ON CONFLICT DO UPDATE from ga_vastu INSERT — pure §N.3 delete-then-insert
2. **Gap 2 (autocommit)**: Changed seed_vastu_directions default autocommit=False (orchestrator owns transaction)
3. **Gap 4 (plan_substeps test missing)**: Added test_ga_vastu_plan_substeps_returns_five (25 tests now)
4. **Gap 5 (FORENSIC runtime)**: Added assert-and-halt guard in ga_vastu_writer — Sun direction_impact='weakened' + Saturn direction_impact='strengthened' for chart 482012f1
5. **Gap 6 (remedials idempotency)**: Added UNIQUE(direction, remedy_type) to bg_vastu_direction_remedials DDL + named ON CONFLICT target in migration 284 and l0_vastu_directions.py

## Notes on rejected reviewer gaps
- Gap 3 (layer_index='L0'): NOT a real gap — migration 252 uses 'L1' as text string and was merged/approved; 'L0' is correct for brahmagyan assets
- Gap 7 (WriterResult notes kwarg): NOT a real gap — WriterResult accepts notes; all other writers use it
- Gap 8 (count_sql compound): NOT a real gap — L0 global tables have no chart_id param; compound count_sql is the correct pattern (see prashna_l0 migration 262 same pattern)
- Gap 9 (Southwest citation): Non-empty classical_citation present; hard gate passes

## All fixes in commit: 85c89b2c — 25 tests pass

## PR
- PR #289: feature/subsystem-astrovastu → main
- CI: pending (Unit Tests + Governance + Build Check running)

## Gate-2 acceptance criteria
- [ ] CI green (25 tests pass)
- [ ] PR merged
- [ ] Surgical migration apply: 284 → 285 → 286 → 287
- Gate-3: ga_vastu cockpit tile lit for chart 482012f1 (45 rows = 9 grahas × 5 ayanamshas)
- Gate-3: FORENSIC Sun=weakened East, Saturn=strengthened West PASS
