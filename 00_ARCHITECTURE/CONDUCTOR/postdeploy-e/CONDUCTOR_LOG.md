# Stream E Conductor Log
Wave: postdeploy-e
Stream: postdeploy-e-multi-school
Branch: feature/postdeploy-e-multi-school
Status: COMPLETE
Tag: postdeploy-e-multi-school-v1-3 @ b37c9835f70d9267c7497fec125a3191b9b32dcf
Authored: 2026-06-05
Autonomy tier: TIER-1 (zero human gates)

## Session Results

| Session | Status | Artifact | Commit |
|---------|--------|----------|--------|
| e1-schema-design | PASS | `00_ARCHITECTURE/V1_3_MULTI_SCHOOL_SCHEMA.md` v1.0 | `3d022288` |
| e2-migration | PASS | `platform/migrations/brahma_multi_school_dual_ayanamsha.sql` | `1c83904a` |
| e3-writer-changes | PASS | `engine.py` ALL_AYANAMSHAS + run_ganita() multi-aya; 18 tests PASS | `8026d2dc` |
| e4-l2-rederivation | PASS | `bo22.py` detect_ayanamsha_dependent_edges(); 16 tests PASS | `ff0e9cb2` |
| e5-concordance-c3 | PASS | `concordance_writer.py` AYANAMSHA_DEPENDENT; concordance v1.1; 25 tests PASS | `b37c9835` |
| e-wave-close | PASS | tag pushed; CONDUCTOR_LOG written | — |

## Key Findings (Investigation)

### What already existed (no DDL change needed)
- `ganita_positions` table has `ayanamsha_id TEXT NOT NULL` discriminator column
  with `UNIQUE(chart_id, ayanamsha_id, planet)` — schema was already correct
- `bodha_graph` table has `ayanamsha_id TEXT NOT NULL DEFAULT 'lahiri'` — already present
- `seed_bodha_graph()` already accepted `ayanamsha_id` parameter
- `l1_positions.py` already computed all 5 ayanamshas but wrote to `chart_facts` not `ganita_positions`

### C3 Concordance Flag Clarification
The conductor brief described C3 as "KP-vs-Lahiri orthogonality". The WS-3 YAML
defines C3 as "House cusp convention — SYSTEM-DEFINING" (Parashari equal-house vs
KP Placidus vs Jaimini rashi vs Tajaka Varsha Lagna). This is a house-system
orthogonality, NOT an ayanamsha-offset orthogonality. However, there IS a genuine
ayanamsha-dependency problem embedded within C3: for planets near sign/nakshatra
boundaries, Lahiri (~23.85°) and KP (~23.86°) offsets can differ enough to change
the planet's sign/nakshatra assignment. This sub-problem is now properly classified
as AYANAMSHA_DEPENDENT.

## Deliverables Summary

1. **V1_3_MULTI_SCHOOL_SCHEMA.md** — Full schema design + investigation findings.
   Confirms discriminator-column approach (already in place). Documents writer gaps
   and C3 clarification.

2. **brahma_multi_school_dual_ayanamsha.sql** — Migration adds
   `concordance_ayanamsha_flags` table with 5-class enum including new
   `ayanamsha_dependent` class. Seeds 2 C3-adjacent records.

3. **engine.py** (writer changes):
   - `ALL_AYANAMSHAS = ['lahiri', 'kp', 'raman', 'true_citra', 'yukteshwar']`
   - `run_ganita()` gains `ayanamshas: list[str] | None` parameter
   - Default (None) → all 5 ayanamshas written to `ganita_positions`
   - Backward compatible: `ayanamsha=str` param kept

4. **bo22.py** (L2 re-derivation):
   - `detect_ayanamsha_dependent_edges()` — cross-references `ganita_positions`
     to find edges involving planets within 0.30° of sign/nakshatra boundaries
   - `_GRAHA_TO_SIGNAL` + `_distance_to_nearest_boundary()` helpers

5. **concordance_writer.py** (new — C3 resolution):
   - `ConcordanceClass` enum with `AYANAMSHA_DEPENDENT` (new in v1.1)
   - `C3_AYANAMSHA_DEPENDENT_RECORDS`: 3 records (SIGN_BOUNDARY, NAKSHATRA_BOUNDARY, DASHA_LORD)
   - `seed_c3_resolution()` populates `concordance_ayanamsha_flags`

6. **brahmagyan_concordance.yaml v1.0 → v1.1**:
   - New class documented; C3 note updated

## Tests

| Test file | Tests | Status |
|-----------|-------|--------|
| `tests/test_ganita_engine_multi_ayanamsha.py` | 18 | ALL PASS |
| `tests/l2/test_bo22_ayanamsha_context.py` | 16 | ALL PASS |
| `tests/test_concordance_writer.py` | 25 | ALL PASS |
| **Total** | **59** | **ALL PASS** |

## Operator Actions Required (post-merge)

1. Apply migration `brahma_multi_school_dual_ayanamsha.sql` to production DB
2. Run `seed_c3_resolution()` to populate C3 AYANAMSHA_DEPENDENT records
   (`python -m brahmagyan.mimamsa.concordance_writer seed-c3`)
3. Trigger chart rebuild for native chart (chart_id 362f9f17-...) to populate
   `ganita_positions` with all 5 ayanamsha rows (run `run_ganita()` without
   `ayanamsha=` restriction — new default runs all 5)
4. Optional: verify boundary detection by running
   `python -m brahmagyan.bodha.bo22 query --chart-id 362f9f17-...`

## Tier-2 Smriti Log

No Tier-2 (confidence < 0.6) dispositions needed. All decisions had clear evidence
from codebase investigation. Key auto-resolved items:
- Schema already correct → confirmed discriminator-column (no DDL change for ganita_positions/bodha_graph)
- C3 flag clarification → documented in schema design + concordance; AYANAMSHA_DEPENDENT class resolves
- No concordance_writer.py existed → created new module in mimamsa (correct location per project structure)
