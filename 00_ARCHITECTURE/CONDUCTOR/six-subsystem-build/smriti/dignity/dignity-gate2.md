---
subsystem: dignity
gate: Gate-2 IN PROGRESS
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Dignity Gate-2 Pass Notes

## Gate-1 → Gate-2 transition
- Gate-1 commit: 35a8ed43 (Śilpī — 2,251 lines)
- Spec-review verdict: SPEC_COMPLIANT_MINOR_GAPS → 6 gaps

## Gap resolutions
1. **Gap 1 (Rahu/Ketu citations)**: `Classical_Rahu_Maitri/Ketu_Maitri` → `UK Ch.4 (Uttara Kalamrita)`; combustion orbs → `BPHS Ch.3` (commit a67fc400)
2. **Gap 2 (test threshold)**: `test_exalted_planet_scores_high` assertion `>= 0.9` → `>= 0.80`; added formula comment noting max=0.85 non-combust (commit a67fc400)
3. **Gap 3 (depends_on)**: Added `'ga_dashas'` to migration 252 `depends_on` ARRAY (commit a67fc400)
4. **Gap 4 (type annotation)**: `rows: list[dict] = {}` → `rows: dict[str, dict] = {}` (commit a67fc400)
5. **Gap 5 (dry_run test)**: Added `test_run_substep_dry_run_returns_zero_rows` (commit a67fc400)
6. **Gap 6 (FORENSIC Saturn)**: Added Saturn=Libra=exalted assertion in build path (commit a67fc400)

## Pre-existing test failure resolved
- `test_mercury_moolatrikona_virgo_in_range` was failing because exaltation check ran before moolatrikona check
- Fix: moved moolatrikona degree-range check BEFORE exaltation sign check
- Classical authority: moolatrikona range takes precedence over generic sign-level exaltation when signs overlap (Mercury=Virgo)
- Commit: f61d6a20
- All 74 tests now pass

## PR
- PR #286: feature/subsystem-dignity → main
- CI status: Governance✓, TypeScript✓, ICR✓, Coverage✓, Naming✓, Planner✓, Secret✓ — Unit Tests + Build Check pending

## Gate-2 acceptance criteria
- [ ] CI green (74 tests pass)
- [ ] PR merged
- [ ] Surgical migration apply: 250 → 251 → 252 in order
- Gate-3: ga_condition cockpit tile lit for chart 482012f1 (45 rows = 9 grahas × 5 ayanamshas)
- Gate-3: FORENSIC 2/2 PASS (Sun≠dignified in Capricorn; Saturn=exalted in Libra)
