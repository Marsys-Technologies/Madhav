---
artifact: PRE_REGEN_AUDIT_CAMPAIGN_TRACKER_v1_0.md
canonical_id: PRE_REGEN_AUDIT_CAMPAIGN_TRACKER
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
purpose: Wave-by-wave status tracker for the Pre-Regeneration Full Audit Campaign. Updated at each wave close. Source of truth for campaign progress.
related: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0, PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0, PRE_REGEN_AUDIT_HARNESS_v1_0
changelog:
  - version: 1.0
    date: 2026-06-26
    change: "Initial tracker — Wave 0 complete"
---

# Pre-Regeneration Audit Campaign Tracker

## Campaign status

| Wave | Layer | Scope | Status | Session | Findings register ref |
|------|-------|-------|--------|---------|----------------------|
| W0 | Shared compute + harness | pyjhora_adapter/compute.py, birth_params.py, panchanga_writer.py, pyhora.py, L0 files, jaimini engine/router, orchestrator adapters | ✅ COMPLETE | 2026-06-26 | §W0 of PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0 |
| W1 | L0 Brahmagyan (~22 bg_ assets) | bg_* writers, reference data, dignity/medical mappings | ⏳ PENDING | — | — |
| W2 | L1 Gaṇita (~16 ga_ assets) | ga_* writers (re-audit all), orchestrator adapters | ⏳ PENDING | — | — |
| W3 | L2 Bodha (~11 bo_ assets) | bo_* writers, synthesis layer | ⏳ PENDING | — | — |
| W4 | L3 Kāla (~11 ka_ assets) | ka_* writers, temporal layer | ⏳ PENDING | — | — |
| W5 | L4 Phala (~11 ph_ assets) | ph_* writers, applied/prediction layer | ⏳ PENDING | — | — |

## Wave 0 deliverables (complete)

- ✅ `PRE_REGEN_AUDIT_HARNESS_v1_0.md` — SQL query templates B1–B7, A1 grep command, contamination taxonomy, per-asset verdict template
- ✅ `PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0.md` — Wave 0 findings: 16 files × 3 axes (11 PASS, 4 FIX-REQUIRED, 1 REVIEW-NEEDED)
- ✅ `pipeline/orchestrator/birth_params.py` — structural guard: `resolve_birth_params()` helper added; "absent row" non-native path now raises instead of silent-None return
- ✅ `tests/test_contamination_guard.py` — CI grep gate: 5/6 tests pass; `test_no_raw_native_birth_fallback` intentionally red (7 remaining vulnerable sites in Wave 2 ga_writers scope)

## Wave 0 key findings

### Blockers (2)
1. `panchang_engine/jaimini_chara.py` — VULNERABLE: `NATIVE_FALLBACK_LONGITUDES` / `NATIVE_LAGNA_RASHI_INDEX` silent fallback for non-native charts
2. `routers/jaimini.py` — VULNERABLE: `/chara_dasha` endpoints accept non-native birth_date but always pass `planet_longitudes=None` → silently uses native longitudes

### Majors (2)
3. `pipeline/orchestrator/birth_params.py` — "absent row" path returned None silently for non-native → **FIXED in this wave** (raises ValueError now)
4. `pipeline/orchestrator/writers/ga_nakshatra.py` — wrong fallback pattern `ctx.config.get("birth_params", ctx.config)` instead of `ctx.config.get("birth_params")` → fix in Wave 2

### Minors (2)
5. `build_ephemeris_1900_2150.py` — hardcoded DB credentials
6. `pipeline/writers/panchanga_writer.py` — ON CONFLICT DO UPDATE instead of delete-then-insert (§N.3 deviation)

## Structural guard status

`resolve_birth_params()` is live in `pipeline/orchestrator/birth_params.py`. Every writer should call it instead of inline native-fallback logic. The 7 remaining vulnerable sites (4 ga_writers) will be remediated in Wave 2. The CI test (`test_contamination_guard.py`) will stay red until they are fixed.

## Gate: regeneration pre-conditions

Regeneration (all layers, all charts) requires ALL of the following:
- [ ] All BLOCKER + MAJOR code findings fixed, committed, CI green
- [ ] Contamination structural guard live (✅ resolve_birth_params helper done)
- [ ] Grep CI test passes (currently 7 FAIL sites — Wave 2 must fix them)
- [ ] All waves W1–W5 findings registers complete and native-reviewed
- [ ] Fix Plan authored from consolidated register
- [ ] main == prod verified (web + job image == main HEAD, all fixes ancestral)

## Next session

Wave 1 — L0 Brahmagyan (~22 bg_ assets). Audit all bg_* writers on all 3 axes. Focus: Axis B (data integrity of reference corpora), Axis C (classical-source fidelity of dignity/medical mappings).
