---
subsystem: yoga
gate: Gate-1 DONE → spec-review in progress
timestamp: 2026-06-17
tier: Tier-1 (pending spec-review verdict)
---

# Yoga Gate-1 Pass Notes (draft — pending spec-review)

## What was built (per Śilpī report)
- Extended `brahma_yoga_catalog` with `bhanga_rules_jsonb`, `partial_formation_threshold`, `strength_formula_ref`, `result_class` columns
- NEW: `yoga_families` table (15 entries: mahapurusha, raja, dhana, nabhasa + 4 sub-families, chandra, surya, arishta, sannyasa, specialized)
- NEW: `yoga_family_members` table (membership join)
- NEW: `yoga_interaction_rules` table (explicitly-cited yoga interactions)
- Existing 81-core yogas preserved intact (all Nabhasa-32 confirmed as already present in catalog)
- NEW: `ga_yoga_firings` table (per-chart, per-ayanamsha yoga evaluation results)
- NEW: `ga_yoga_writer.py` (1,100-line deterministic evaluation engine)
- NEW: `writers/ga_yoga.py` (orchestrator adapter: heavy writer, 5 ayanamshas via plan_substeps)
- Tests: 41 tests passing

## Migrations used
- 239: yoga_families + yoga_family_members + yoga_interaction_rules + brahma_yoga_catalog column ALTERs
- 240: ga_yoga_firings table + asset_registry entry (count_sql=ga_yoga_firings, depends_on=[ga_structural,ga_dashas], target_floor=50, has_substeps=true)

## Key decisions
- yoga_strength_formula_v1: cites BPHS Ch.75 weighting principles
- Budha-Aditya: combust gate at 3° (yoga fails even with conjunction if combust)
- Complex house-lord yogas reference ga_structural rather than recompute (L1-authority)
- Uncited strength → null (hard gate enforced in tests)

## Spec-review status: RUNNING (will update)
## Gate-2 status: pending spec-review pass
