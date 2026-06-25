---
subsystem: yoga
gate: Gate-2 IN PROGRESS
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Yoga Gate-2 Pass Notes

## Gate-1 → Gate-2 transition
- Commit: 6507b321 (Śilpī Gate-1 build) + 0b9e86d7 (spec-review gap fixes)
- Spec-review verdict: SPEC_COMPLIANT_MINOR_GAPS → all 3 gaps resolved

## Gap resolutions
1. **has_substeps=true**: Added to migration 240 asset_registry INSERT + ON CONFLICT DO UPDATE
2. **FORENSIC test**: Added `test_forensic_budha_aditya_fires_on_native_chart()` — Sun+Mercury in Capricorn, 13° apart, guarded by CANONICAL_CHART_ID
3. **seed_yogas autocommit**: Changed default from `True` to `False` (orchestrator owns transaction)

## PR
- PR #284: feature/subsystem-yoga → main
- https://github.com/amonty84/Madhav/pull/284
- Status: CI pending

## Gate-2 acceptance criteria
- [ ] CI green (42 tests pass)
- [ ] PR merged
- [ ] Surgical migration apply: 239, then 240
- Gate-3: ga_yoga cockpit tile lit for chart 482012f1
