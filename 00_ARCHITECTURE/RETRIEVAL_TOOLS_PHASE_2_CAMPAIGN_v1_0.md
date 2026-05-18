---
artifact: RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
canonical_id: RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN
version: 1.0
status: ACTIVE
authored: 2026-05-17
author: Claude (Cowork session — analysis/backend-data-pipeline-perf-audit)
predecessor: da140c8 (Phase 1 — planner-blind RCS fix for 4 tools)
parent_audit: 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md
branch: analysis/backend-data-pipeline-perf-audit
post_deploy_eval_policy: DEFERRED — consolidated answer:eval runs once at the end of the campaign per project_retrieval_tools_consolidated_eval.md
---

# Retrieval Tools — Phase 2 Campaign Plan

Phase 1 (commit `da140c8`) closed the planner-blind gap for 4 tools (`lel_query`, `query_signal_state`, `query_kp_ruling_planets`, `query_varshaphala`). Phase 2 closes the remaining items from the audited view in `MACROPHASE_AND_DATA_AUDIT_v1_0.md §F`:

- **F.PIPE.1** — M9 tools 27 + 28 not wired (BLOCKER)
- **F.DATA.2** — L9 DB_SEED_DEFERRED + GCS_UPLOAD_DEFERRED
- **F.M8.6** — Classical attribution coverage 76/573 (13.3%)
- **signal_states data freshness** — table likely empty for 2024-2028 date range
- **`temporal` SLA probe** — workhorse tool has no SLA measurement
- **`cross_varga_dignity_query` unit tests** — missing test coverage

## §A — Sub-phase structure

| Sub-phase | Scope | Type | Brief | Estimated effort |
|---|---|---|---|---|
| **2A** | M9 wiring (code) + L9 data ship | code + data | `00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md` | 1 session + 0.5 session data |
| **2B** | Classical attribution expansion (M8) + signal_states activation (M3-B) | data | `00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2B_DATA_BACKFILL_BRIEF_v1_0.md` (to be authored) | 1 session (multi-hour wall clock) |
| **2C** | `temporal` SLA probe + `cross_varga_dignity_query` unit tests | code | `00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2C_HYGIENE_BRIEF_v1_0.md` (to be authored) | 0.5 session |

Each sub-phase ships as its own PR on the audit branch. Per `feedback_two_stream_branch_policy.md`, all work stays on `analysis/backend-data-pipeline-perf-audit` and merges to `main` via PR.

## §B — Phase 2A scope (M9 wiring + L9 data ship)

**Code work:**

1. Create `platform/src/lib/retrieve/multi_school_signal_lookup_tool.ts` — RetrievalTool wrapper around `platform/src/lib/tools/multi_school_signal_lookup.ts` (M8 wrapper pattern: `classical_text_search_tool.ts` is the canonical example).
2. Create `platform/src/lib/retrieve/convergence_score_lookup_tool.ts` — same pattern.
3. Register both in `platform/src/lib/retrieve/index.ts` → `RETRIEVAL_TOOLS` array.
4. Add both to `platform/src/lib/trace/types.ts` → `ALL_21_RETRIEVAL_TOOLS` (rename comment but not constant — backwards compatibility).
5. Update `platform/src/app/api/chat/consume/route.ts:73` → `toolStepType()` to map both as `'sql'`.
6. Update `inferLayer` in `consume/route.ts` to map both as `'L2.5'` (M9 outputs are L9 nominally but consumed at L2.5 boundary).
7. Author 5 unit tests per tool under `platform/src/lib/retrieve/__tests__/` (mocked storage, mirror `lel_query.test.ts` pattern).
8. Update `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` regression assertions if count needs bumping (24→26).

**Data work:**

1. Spin local Cloud SQL Auth Proxy.
2. Run `platform/scripts/m9/run_multi_school_analysis.py --write-db` to seed `school_signal_coverage`, `school_analysis_runs`, `convergence_scores`, `school_disagreements`.
3. Upload 7 per-school analyses + `convergence_scores.json` + `school_disagreement_register.json` to `gs://madhav-marsys-sources/L9/` per `GCS_LAYOUT_v1_0.md`.
4. Verify row counts + GCS object existence.

**Acceptance:**

- tsc: 0 errors project-wide
- vitest: existing tests pass + 10 new unit tests pass
- Live SLA probe: extend `sla_probe_planner_blind_tools.ts` with 3-4 scenarios per new tool OR author a separate `sla_probe_m9_tools.ts`
- Planner-only smoke: add `eval:planner-blind-fix-m9` covering the 3 GT.050-052 multi_school_triangulation entries already in `planner_golden_set.json`
- L9 DB rows present: `SELECT count(*) FROM school_signal_coverage` ≥ 4011 (per audit §C.5), `SELECT count(*) FROM convergence_scores` ≥ 5 (one per domain)
- L9 GCS objects present at `gs://madhav-marsys-sources/L9/school_analyses/*.json` (7 files) + `gs://madhav-marsys-sources/L9/convergence/*.json` (2 files)

**Closes:** F.PIPE.1, F.DATA.2 (the two highest-severity findings from the audit).

## §C — Phase 2B scope (Classical + signal_states data backfill)

**Will be detailed in the 2B brief when 2A closes. Outline:**

- **Classical attribution expansion**: Update `platform/scripts/run_attribution_pass.py` to iterate over MSR v5.0 (573 signals) vs M8-E's 510. Run with 4 parallel Vertex workers against the 13 classical text corpora. Expected wall clock ~4 hours. Updates `classical_attributions` DB table + `CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md` + `.json`. Targets: ≥300/573 attribution coverage (vs 76/573 today).
- **signal_states activation**: Run `platform/scripts/temporal/signal_activator.py` for the native chart across 2024-01-01 → 2028-12-31. Populates `signal_states` table with lit/dormant/ripening per signal per day.

**Acceptance for 2B**: classical_attributions row count ≥ 1500, signal_states row count > 0 for any date in window. No code changes; one commit updates the registry .md docs only.

## §D — Phase 2C scope (Hygiene round)

**Will be detailed in the 2C brief when 2B closes. Outline:**

- Author `platform/scripts/sla_probe_temporal.ts` covering 5 scenarios (one per sub-mode: dasha, transit, eclipse, retrograde, sade_sati). Mirror `sla_probe_planner_blind_tools.ts` structure. SLA budgets: dasha 200ms, transit 400ms, eclipse 150ms, retrograde 150ms, sade_sati 100ms.
- Author `platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts` — 5 unit tests mirroring saham_query pattern.
- npm scripts: `sla:probe-temporal`, no new package.json entry needed for the test file.

**Acceptance for 2C**: tsc clean, all temporal SLA scenarios within budget, 5 new unit tests pass.

## §E — Post-campaign — consolidated answer:eval

After **all three sub-phases ship to main and deploy**, signal me to run:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npm run answer:eval 2>&1 | tee /tmp/answer_eval_post_phase_2.log
```

Compare against `results_gemini_baseline_20260511.json`. Tracking memory: `project_retrieval_tools_consolidated_eval.md` §"Queued tools shipped" — append each PR as it lands.

## §F — Hard rules across the campaign

1. **Branch discipline**: every sub-phase starts with `git checkout analysis/backend-data-pipeline-perf-audit`. Per `feedback_two_stream_branch_policy.md`, never touch Chat V2 branches.
2. **Pre-commit verification per PR**: tsc + relevant vitest + (where applicable) SLA probe + (where applicable) planner smoke. No `answer:eval` per-PR — that's consolidated.
3. **Regression baseline sync**: any extension to `planner_golden_set.json` REQUIRES paired extension of `tests/eval/fixtures/regression_baseline.json` (lesson from da140c8).
4. **PLANNER_PROMPT R-rule discipline**: any new tool added to RCS requires an R-rule + worked example. Use imperative "ALWAYS include" + keyword triggers (lesson from R30 v2).
5. **`toolStepType` + `inferLayer` mapping**: every new tool registered in `RETRIEVAL_TOOLS` needs corresponding entries in `consume/route.ts:73` and `consume/route.ts:80` so the trace UI categorizes them correctly.
6. **Production planner uses gemini-2.5-flash**: all smoke tests default to flash. Do NOT default to gemini-2.5-pro (rejects thinkingBudget:0 as of 2026-05-17).

## §G — Predecessor and successor pointers

- **Predecessor**: `da140c8` (Phase 1 — 4 planner-blind tools wired)
- **Successor**: `main` consolidated eval run + native review

---

*End RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md. Living document — updated as sub-phases close. Brief 2A is authored at campaign open; 2B and 2C are stubbed and authored when their turn comes.*
