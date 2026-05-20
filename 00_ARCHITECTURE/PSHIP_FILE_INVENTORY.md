---
artifact: PSHIP_FILE_INVENTORY.md
type: PSHIP_CLASSIFICATION
version: 1.0
status: CURRENT
authored_by: Claude Code (PSHIP-S1)
authored_on: 2026-05-20
session_id: PSHIP-S1
merge_base: 47ccdbc792ffe800197cfd2b33daa1a2682c7413
source_branch: origin/feature/phase-4c-panchang
target_branch: feature/panchang-ship (cut from current main)
---

# PSHIP File Inventory — Classification of Panchang Source Files

Produced by PSHIP-S1. Every file on `feature/phase-4c-panchang` relative to its merge-base
with main is tagged:
- **A** — Added (new file, does NOT exist on current main; safe to transplant)
- **M** — Modified (EXISTS on current main; integration must wait for PSHIP-S2)
- **D** — Deleted on source branch (exists on main; leave alone — do NOT transplant)
- **A-SKIP** — Added on source branch but ALREADY on current branch (Conductor merge); skip transplant to avoid overwriting

Merge-base SHA: `47ccdbc792ffe800197cfd2b33daa1a2682c7413`

---

## Summary Counts

| Classification | Count |
|---|---|
| A — Transplant (additive, new) | 129 |
| A-SKIP — Already on branch (CONDUCTOR files, sealed) | 13 |
| A-RECLASSIFIED → M — Added on source vs merge-base, but exists on current main | 3 |
| M — Shared/modified (PSHIP-S2 only) | 22 |
| D — Deleted on source, kept on main | 1 |
| **Total** | **165** |

**Note on A-RECLASSIFIED → M:** Three files were A-classified on the source branch relative to the merge-base (they did not exist at the merge-base commit), but were independently added to main after the merge-base. Cross-checking with `git cat-file -e origin/main:<path>` reveals they exist on current main. Per the brief's cross-check rule, these are treated as M (shared files, PSHIP-S2 only). The source branch's versions were NOT transplanted — main's version is kept in place.

---

## A-RECLASSIFIED → M (3 files — exist on current main, treated as shared)

These files were A-classified on source (not at merge-base) but independently exist on
current main. The cross-check rule per §3 of the brief reclassifies them as M.
Treated identically to M files: DO NOT TOUCH in PSHIP-S1; integrate in PSHIP-S2.

| Path | Notes |
|---|---|
| `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` | Added by Phase 4A work on main; Panchang source has an updated version with 4C state. PSHIP-S2 must merge the 4C sub-phase state tracker additions. |
| `platform/src/lib/retrieve/__tests__/query_panchanga.test.ts` | Added by Phase 4C work already merged to main; source branch has a different version. PSHIP-S2 must reconcile. |
| `platform/src/lib/retrieve/query_panchanga.ts` | Added by Phase 4C work already merged to main; source branch has a more complete version. PSHIP-S2 must reconcile — critical diff: source has engine-direct path + full sidecar API calls; main has a simpler implementation. |

---

## A-SKIP — Already on current branch (DO NOT OVERWRITE — CONDUCTOR sealed)

These files are A-classified on the source branch (added vs merge-base) but are already
present on `feature/panchang-ship` from the Conductor merge. The brief explicitly marks
the CONDUCTOR directory as `must_not_touch`. Transplanting these would silently overwrite
the sealed Conductor state on the current branch.

| Path |
|---|
| `00_ARCHITECTURE/CONDUCTOR/CLAUDE_MD_AMENDMENT_PROPOSAL.md` |
| `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_HALT_LOG.md` |
| `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_LOG.md` |
| `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md` |
| `00_ARCHITECTURE/CONDUCTOR/README.md` |
| `00_ARCHITECTURE/CONDUCTOR/WAVE_2_MIGRATION_NOTE.md` |
| `00_ARCHITECTURE/CONDUCTOR/schemas/halt_entry_schema.json` |
| `00_ARCHITECTURE/CONDUCTOR/schemas/queue_entry_schema.json` |
| `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml` |
| `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_BRIEF_v1_0.md` |
| `00_ARCHITECTURE/CONDUCTOR/smoke/SMOKE_HEARTBEAT.md` |
| `00_ARCHITECTURE/CONDUCTOR/smoke/smoke_queue.yaml` |
| `00_ARCHITECTURE/CONDUCTOR/validate_queue.py` |

---

## A — Additive Files to Transplant (132 files)

### Architecture / Governance / Documentation

| Path |
|---|
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_CONDUCTOR_S0_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_0_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_3_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_4_S1_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_4_S2_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_4_S3_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_4_S4_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_5_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_6_S1_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_6_S2_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_6_S3_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_6_S4_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_7_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_8_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_9_v1_0.md` |
| `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4C_1_CLOSE_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4C_4_CLOSE_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4C_6_CLOSE_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4C_CLOSE_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4C_FOLLOWUPS_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` |
| `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` |
| `00_ARCHITECTURE/RED_TEAM/RT_4C_1_FINDING.md` |
| `00_ARCHITECTURE/RED_TEAM/RT_4C_2_FINDING.md` |
| `00_ARCHITECTURE/RED_TEAM/RT_4C_3_FINDING.md` |
| `00_ARCHITECTURE/RED_TEAM/RT_4C_4_FINDING.md` |
| `00_ARCHITECTURE/RED_TEAM/RT_4C_5_FINDING.md` |
| `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` |
| `HANDOFF.md` |
| `HANDOFF_WAVE_1.md` |

### Python Panchang Engine (sidecar)

| Path |
|---|
| `platform/python-sidecar/panchang_engine/README.md` |
| `platform/python-sidecar/panchang_engine/__init__.py` |
| `platform/python-sidecar/panchang_engine/angas.py` |
| `platform/python-sidecar/panchang_engine/ayanamsha.py` |
| `platform/python-sidecar/panchang_engine/config/muhurat_weights.yaml` |
| `platform/python-sidecar/panchang_engine/config_loader.py` |
| `platform/python-sidecar/panchang_engine/exceptions.py` |
| `platform/python-sidecar/panchang_engine/muhurat.py` |
| `platform/python-sidecar/panchang_engine/planets.py` |
| `platform/python-sidecar/panchang_engine/serialize.py` |
| `platform/python-sidecar/panchang_engine/shastra_tables.py` |
| `platform/python-sidecar/panchang_engine/special_yogas.py` |
| `platform/python-sidecar/panchang_engine/tara_bala.py` |
| `platform/python-sidecar/panchang_engine/timings.py` |
| `platform/python-sidecar/panchang_engine/types.py` |
| `platform/python-sidecar/panchang_engine/tests/__init__.py` |
| `platform/python-sidecar/panchang_engine/tests/conftest.py` |
| `platform/python-sidecar/panchang_engine/tests/fixtures/.gitkeep` |
| `platform/python-sidecar/panchang_engine/tests/fixtures/drik_panchang_v1.json` |
| `platform/python-sidecar/panchang_engine/tests/fixtures/drik_panchang_v2.json` |
| `platform/python-sidecar/panchang_engine/tests/test_angas.py` |
| `platform/python-sidecar/panchang_engine/tests/test_config_loader.py` |
| `platform/python-sidecar/panchang_engine/tests/test_drik_parity.py` |
| `platform/python-sidecar/panchang_engine/tests/test_muhurat.py` |
| `platform/python-sidecar/panchang_engine/tests/test_muhurat_scoring.py` |
| `platform/python-sidecar/panchang_engine/tests/test_planets.py` |
| `platform/python-sidecar/panchang_engine/tests/test_serialize.py` |
| `platform/python-sidecar/panchang_engine/tests/test_special_yogas.py` |
| `platform/python-sidecar/panchang_engine/tests/test_timings.py` |
| `platform/python-sidecar/routers/muhurat.py` |
| `platform/python-sidecar/routers/panchang.py` |

### Next.js API Routes (new — additive)

| Path |
|---|
| `platform/src/app/api/compute/muhurat/route.ts` |
| `platform/src/app/api/panchang/charts/route.ts` |
| `platform/src/app/api/panchang/feed.ics/route.ts` |
| `platform/src/app/api/panchang/feed/revoke/route.ts` |
| `platform/src/app/api/panchang/feed/subscribe/route.ts` |
| `platform/src/app/api/panchang/ics/route.ts` |
| `platform/src/app/api/panchanga/route.ts` |

### Next.js Panchang Page (new)

| Path |
|---|
| `platform/src/app/panchang/__tests__/AskMadhavLink.test.tsx` |
| `platform/src/app/panchang/__tests__/ChoghadiyaPanel.test.tsx` |
| `platform/src/app/panchang/__tests__/HoraPanel.test.tsx` |
| `platform/src/app/panchang/__tests__/MuhuratFinderModal.test.tsx` |
| `platform/src/app/panchang/__tests__/PanchangContextInjection.test.ts` |
| `platform/src/app/panchang/__tests__/PanchangHeader.test.tsx` |
| `platform/src/app/panchang/__tests__/PrimaryStrip.test.tsx` |
| `platform/src/app/panchang/__tests__/SpecialYogasList.test.tsx` |
| `platform/src/app/panchang/components/ActionBar.tsx` |
| `platform/src/app/panchang/components/AskMadhavLink.tsx` |
| `platform/src/app/panchang/components/ChoghadiyaPanel.tsx` |
| `platform/src/app/panchang/components/HoraPanel.tsx` |
| `platform/src/app/panchang/components/MuhuratFinderModal.tsx` |
| `platform/src/app/panchang/components/MuhuratResultsList.tsx` |
| `platform/src/app/panchang/components/PanchangClientView.tsx` |
| `platform/src/app/panchang/components/PanchangHeader.tsx` |
| `platform/src/app/panchang/components/PlanetaryGrid.tsx` |
| `platform/src/app/panchang/components/PrimaryStrip.tsx` |
| `platform/src/app/panchang/components/SpecialYogasList.tsx` |
| `platform/src/app/panchang/components/TimingsPanel.tsx` |
| `platform/src/app/panchang/error.tsx` |
| `platform/src/app/panchang/hooks/useChartList.ts` |
| `platform/src/app/panchang/hooks/useMuhuratFinder.ts` |
| `platform/src/app/panchang/hooks/usePanchangDay.ts` |
| `platform/src/app/panchang/layout.tsx` |
| `platform/src/app/panchang/loading.tsx` |
| `platform/src/app/panchang/page.tsx` |

### UI Components (new — additive)

| Path |
|---|
| `platform/src/components/ui/collapsible.tsx` |
| `platform/src/components/ui/icons/zodiac/index.ts` |
| `platform/src/components/ui/star-rating.tsx` |

### Observatory Panchang Panels (new — additive)

| Path |
|---|
| `platform/src/lib/components/observatory/panchang/PanchangCachePanel.tsx` |
| `platform/src/lib/components/observatory/panchang/PanchangLatencyPanel.tsx` |
| `platform/src/lib/components/observatory/panchang/index.ts` |

### Panchang Client Libraries (new — additive)

| Path |
|---|
| `platform/src/lib/format/dms.ts` |
| `platform/src/lib/panchang/__tests__/chandra_bala.test.ts` |
| `platform/src/lib/panchang/__tests__/ics_builder.test.ts` |
| `platform/src/lib/panchang/__tests__/tara_bala.test.ts` |
| `platform/src/lib/panchang/chandra_bala.ts` |
| `platform/src/lib/panchang/feed_revocations.ts` |
| `platform/src/lib/panchang/ics_builder.ts` |
| `platform/src/lib/panchang/ics_client.ts` |
| `platform/src/lib/panchang/sidecar_mapper.ts` |
| `platform/src/lib/panchang/tara_bala.ts` |
| `platform/src/lib/retrieve/__tests__/query_panchanga.test.ts` |
| `platform/src/lib/retrieve/query_panchanga.ts` |
| `platform/src/lib/security/__tests__/sign_url.test.ts` |
| `platform/src/lib/security/sign_url.ts` |

### Test Artifacts (new — additive)

| Path |
|---|
| `platform/tests/components/panchang/PlanetaryGrid.test.tsx` |
| `platform/tests/components/panchang/TimingsPanel.test.tsx` |
| `platform/tests/integration/test_muhurat_finder_e2e.test.ts` |
| `platform/tests/integration/test_query_panchanga_e2e.test.ts` |
| `platform/tests/lib/dms.test.ts` |
| `platform/tests/perf/4C4_baseline.md` |
| `platform/tests/perf/4C6_S1_muhurat_latency.md` |
| `platform/tests/perf/4C6_S4_perf.md` |
| `platform/tests/planner/panchang_probe_set.json` |
| `platform/tests/planner/panchang_routing.test.ts` |
| `platform/tests/visual/4C4_S2_drik_compare.md` |
| `platform/tests/visual/4C4_close_report.md` |
| `platform/tests/visual/4C6_S3_review.md` |
| `platform/tests/visual/4C6_acharya_review.md` |

---

## M — Shared Files (Modified on source branch — PSHIP-S2 only)

These files EXIST on current main AND were modified on the source branch.
**DO NOT TOUCH in PSHIP-S1.** Handled exclusively in PSHIP-S2.

| Path |
|---|
| `.gemini/project_state.md` |
| `.geminirules` |
| `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` |
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` |
| `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` |
| `00_ARCHITECTURE/SESSION_LOG.md` |
| `CLAUDE.md` |
| `platform/.env.example` |
| `platform/.env.local.example` |
| `platform/package-lock.json` |
| `platform/package.json` |
| `platform/python-sidecar/main.py` |
| `platform/src/app/clients/[id]/consume/page.tsx` |
| `platform/src/components/shared/AppShellRail.tsx` |
| `platform/src/components/shared/MobileNavSheet.tsx` |
| `platform/src/lib/claude/system-prompts.ts` |
| `platform/src/lib/components/observatory/pages/OverviewClient.tsx` |
| `platform/src/lib/retrieve/index.ts` |
| `platform/src/test-setup.ts` |

**Count: 19 shared files**

---

## D — Deleted on source branch (1 file)

These were deleted on the source branch but exist on current main. Leave them in place.

| Path | Notes |
|---|---|
| `CLAUDECODE_BRIEF.md` | Deleted on source branch (Wave 1 workflow artifact). Exists on main. Do not transplant deletion. |

---

*End PSHIP_FILE_INVENTORY.md v1.0 — produced PSHIP-S1, 2026-05-20*
