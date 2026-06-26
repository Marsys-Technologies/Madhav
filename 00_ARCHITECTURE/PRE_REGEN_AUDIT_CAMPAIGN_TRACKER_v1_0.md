---
artifact: PRE_REGEN_AUDIT_CAMPAIGN_TRACKER_v1_0.md
canonical_id: PRE_REGEN_AUDIT_CAMPAIGN_TRACKER
version: 1.2
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
purpose: Wave-by-wave status tracker for the Pre-Regeneration Full Audit Campaign. Updated at each wave close. Source of truth for campaign progress.
related: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0, PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0, PRE_REGEN_AUDIT_HARNESS_v1_0
changelog:
  - version: 1.2
    date: 2026-06-26
    change: "Wave 2 complete — 13 ga_* L1 assets audited; contamination fixes committed; 4 majors + 3 minors; 4 carry-over fixes for next session"
  - version: 1.1
    date: 2026-06-26
    change: "Wave 1 complete — 18 bg_* L0 assets audited; 2 majors + 1 minor"
  - version: 1.0
    date: 2026-06-26
    change: "Initial tracker — Wave 0 complete"
---

# Pre-Regeneration Audit Campaign Tracker

## Campaign status

| Wave | Layer | Scope | Status | Session | Findings register ref |
|------|-------|-------|--------|---------|----------------------|
| W0 | Shared compute + harness | pyjhora_adapter/compute.py, birth_params.py, panchanga_writer.py, pyhora.py, L0 files, jaimini engine/router, orchestrator adapters | ✅ COMPLETE | 2026-06-26 | §W0 of PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0 |
| W1 | L0 Brahmagyan (18 bg_* assets) | All bg_* orchestrator writers + l0_* source modules | ✅ COMPLETE | 2026-06-26 | §W1 of PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0 |
| W2 | L1 Gaṇita (13 ga_* assets) | ga_* writers + contamination fixes (9 W0 sites → all committed; 4 carry-over fixes remain) | ✅ COMPLETE (carry-overs pending) | 2026-06-26 | §W2 of PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0 |
| W3 | L2 Bodha (~11 bo_* assets) | bo_* writers, synthesis layer | ⏳ PENDING | — | — |
| W4 | L3 Kāla (~10 ka_* assets) + L4 Phala (~9 ph_* assets) | ka_* + ph_* writers | ⏳ PENDING | — | — |
| W5 | Cross-wave synthesis | Consolidate all findings; Fix Plan; campaign close | ⏳ PENDING | — | — |

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

`resolve_birth_params()` is live in `pipeline/orchestrator/birth_params.py`. Every writer should call it instead of inline native-fallback logic. The **9 remaining vulnerable sites** (7 or-fallback assignments + 2 signature defaults in ga_* writers) will be remediated in Wave 2. The CI test (`test_contamination_guard.py`) will stay red until they are all fixed.

## Wave 1 key findings

### Majors (2)
1. `l0_rules.py` line 1286 — `conn.rollback()` in exception handler (A3: FROZEN orchestrator contract violation; silently unwinds orchestrator transaction if bg_rules raises during a multi-asset build)
2. `l0_transit.py` — Venus gochara rules missing 6 of 9 BPHS Ch.29 favourable houses (C1 fail; L2 Bodha Venus transit synthesis will be materially incomplete)

### Minors (1)
3. `bg_dignity_reference` — no asset_registry entry in any migration; cockpit stats route cannot count this asset's rows (B1 fail)

### Review-Needed (non-blocking, 1)
4. `bg_remedies` — count_sql for brahma_remedy_corpus not confirmed in examined migrations; verify separately

### Clean (15/18)
All 18 bg_* assets pass A1 (CHART-INDEPENDENT — zero contamination risk). Zero generative LLM use anywhere in L0. §N.4 Deterministic-First upheld.

## Gate: regeneration pre-conditions

Regeneration (all layers, all charts) requires ALL of the following:
- [ ] All BLOCKER + MAJOR code findings fixed, committed, CI green
- [ ] Contamination structural guard live (✅ resolve_birth_params helper done)
- [ ] Grep CI test passes (currently 9 FAIL sites — Wave 2 must fix them)
- [ ] All waves W2–W5 findings registers complete and native-reviewed
- [ ] Fix Plan authored from consolidated register
- [ ] main == prod verified (web + job image == main HEAD, all fixes ancestral)

## Wave 2 key findings

### Blocker (pre-regen, 1)
1. `ga_vargas_writer.py` C1 — D9 Navamsha uses wrong formula (`_compute_general_varga()` instead of `_compute_divisional_sign()` trikona-start); incorrect varga assignments corrupt all downstream Bodha varga analysis

### Majors (3)
2. `ga_dashas_writer.py` A1 — NATIVE_BIRTH via local alias constants (`BIRTH_IST/LAT/LON`) — evades grep guard; functionally identical contamination class; `resolve_birth_params()` not called before `_get_moon_position()`
3. `ga_tajaka_writer.py` A1 — `compute_varsha()` unconditional `{**NATIVE_BIRTH}` hardcoding (unresolved after fix set 1; non-or-fallback form)
4. `ga_vargas_writer.py` A2/A3 — INVARIANT sentinel row accretion + telemetry violation in source module

### Minors (3)
5. `ga_sade_sati_writer.py` A3 — commit + asset_throughput in source module (guarded on orchestrator path)
6. `ga_yoga_writer.py` A7/C1 — silent per-row error swallowing + subject-norm coupling with no guard
7. `brahmagyan/ganita/engine.py` A7 — `write_positions()` returns phantom count

### Contamination carry-overs (extend grep guard)
The Wave 2 grep guard is green BUT `ga_dashas_writer.py` uses local-alias NATIVE_BIRTH constants. Widen `test_no_raw_native_birth_fallback` to also catch `or BIRTH_IST`, `or BIRTH_LAT`, `or BIRTH_LON` variants.

## Next session

Wave 2 carry-overs (4 fixes) then Wave 3 (L2 Bodha bo_* writers). Carry-overs:
1. Fix `ga_dashas_writer.py` local-alias contamination + widen grep guard
2. Fix `ga_tajaka_writer.py` `compute_varsha()` unconditional NATIVE_BIRTH + conn injection
3. Fix `ga_vargas_writer.py` D9 formula + INVARIANT sentinel + telemetry removal
4. Fix `ga_vargas_writer.py` INVARIANT sentinel accretion
