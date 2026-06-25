---
subsystem: medical
gate: Gate-2 IN PROGRESS
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Medical Gate-2 Pass Notes

## Gate-1 → Gate-2 transition
- Gate-1 commit: 5aeeae54 (Śilpī — 10 files, 38 tests)
- Spec-review verdict: SPEC_VIOLATION → 4 CRITICAL + 4 MAJOR gaps

## Gap resolutions

### CRITICAL fixes
1. **Gap 1 (ON CONFLICT idempotency)**: Removed ON CONFLICT DO UPDATE from ga_medical L1 INSERT — pure §N.3 delete-then-insert
2. **Gap 3 (wrong ayanamsha IDs)**: Fixed in ga_medical_writer.py, ga_medical.py, and tests:
   - `kp` → `krishnamurti`
   - `yukteshwar` → `surya_siddhanta_classical`
   These match CANONICAL_AYANAMSHAS in ga_positions_writer.py exactly.

### MAJOR fixes
3. **Gap 4 (has_substeps missing)**: Added `has_substeps=true` to migration 280 asset_registry INSERT and ON CONFLICT DO UPDATE
4. **Gap 5 (depends_on wrong)**: Fixed in migration 280:
   - `ga_condition` → `ga_condition_composite` (actual table queried)
   - Added `bg_medical_mappings` and `bg_nakshatra_medical` (L0 tables the writer reads)
5. **Gap 6 (FORENSIC log-only)**: Changed to assert-and-halt for Sun (debilitated=strong) and Saturn (exalted=mild) for chart 482012f1

## Notes on rejected/inapplicable gaps
- Gap 2 (autocommit): l0_medical.py already had `autocommit: bool = False` as default — reviewer was wrong; no change needed
- Gap 4 (layer_index='L0'/'L1'): NOT a real gap — migration 252 uses 'L1' as text and works; same pattern
- Gap 9 (inspect.getsource test): Skipped — the ON CONFLICT removal is the actual fix; static inspection test is over-engineering
- Gap 10 (ga_medical_writer not a writer class): Correct design pattern (delegation to implementation module, adapter in writers/)
- Gap 11 (L0 count_sql no $1): Correct — L0 global tables have no per-chart scoping

## All fixes in commit: 75737782 — 38 tests pass

## PR
- PR #290: feature/subsystem-medical → main
- CI: pending (Unit Tests + Governance + Build Check running)

## Gate-2 acceptance criteria
- [ ] CI green (38 tests pass)
- [ ] PR merged
- [ ] Surgical migration apply: 276 → 277 → 278 → 279 → 280
- Gate-3: ga_medical cockpit tile lit for chart 482012f1 (45 rows = 9 grahas × 5 ayanamshas)
- Gate-3: FORENSIC Sun=debilitated→strong; Saturn=exalted→mild; Moon=PurvaBhadrapada→left_side PASS
