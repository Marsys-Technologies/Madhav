# Known Pre-Existing Test Failures

**v1.7 — 9 excluded (2026-06-03)**
Branch: main (HEAD: post-PR#188 CI-remediation commit)
Excluded from vitest via `vitest.config.ts`: 9 files
Root cause: PR #187 `feat: Legacy teardown — clean slate for Layer-0 rebuild` (`30640c96`, 2026-06-02) cleared `RETRIEVAL_TOOLS=[]` and `CONTRACT_CATALOG=[]` as a deliberate precondition for the Layer-0→3 Build-Guarantor arc.

| File | Failures | Re-enable trigger |
|---|---|---|
| `src/lib/gateway/__tests__/gateway.test.ts` | 13 | CONTRACT_CATALOG repopulated (L0 Gate-1) |
| `src/lib/contract/__tests__/unified_contract.test.ts` | 4 | CONTRACT_CATALOG repopulated (L0 Gate-1) |
| `tests/governance/sla_probe_new_tools.test.ts` | 7 | RETRIEVAL_TOOLS≥33 tools re-registered (L1–L3, per-layer) |
| `src/__tests__/integration/mcp_stub_engines.integration.test.ts` | 5 | RETRIEVAL_TOOLS aliases re-registered (L1–L2) |
| `tests/synthesis/tool_catalogue_schema_normalization.test.ts` | 3 | RETRIEVAL_TOOLS non-empty (any layer) |
| `tests/retrieval/tool_catalogue.test.ts` | 1 | RETRIEVAL_TOOLS non-empty (any layer) |
| `src/lib/db/__tests__/observatory_schema.test.ts` | 2 | Rewrite to assert against `001_baseline.sql`; remove refs to archived migrations 008+038 |
| `src/app/api/build/__tests__/e2e.test.ts` | 2 | New build job wired in Build-Guarantor Gate-2 |
| `src/app/api/build/__tests__/start_route.test.ts` | 1 | New build job wired in Build-Guarantor Gate-2 |

The Build-Guarantor swarm charter (`00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md`) governs re-enablement: each exclusion is lifted as the layer/asset it guards is re-authored and its contract verified.

---

**v1.6 — 0 pre-existing failures (2026-05-31)**
Branch: main (HEAD: 206d6370)
Total pre-existing failures: **0** (platform: 0, platform-mcp: 0)
Test suite: platform vitest + platform-mcp vitest

> **All 35 v1.5 failures are resolved.** Platform-mcp 22 failures resolved by `837fbf07` (2026-05-30). Platform 13 failures resolved by `6fffa50a` (2026-05-26), `49a83571`, `f7d0eeda`, `ef2e4c05` (all 2026-05-30). See changelog for per-group fix mapping.

---

## Changelog

- **v1.6 (2026-05-31):** All 35 v1.5 failures resolved. Platform package: 0 failures (was 13). Platform-mcp package: 0 failures (was 22). Resolving commits: `6fffa50a` (2026-05-26, Groups 2a+2b — ToolBundle shape assertions); `49a83571` (2026-05-30, Groups 1, 3b, 4, 5 — spec gap, MSR path, trace-audit param indices, ICR gate); `f7d0eeda` (2026-05-30, Group 3a — msr_parser count 514→573 + relative path); `ef2e4c05` (2026-05-30, Group 3c — frontmatter_check field assertion); `837fbf07` (2026-05-30, Groups 6+9 — MCP wrapper shapes, query_signal_state Zod limit). Groups 7+8 (tool catalog count drift + live-DB CI guard) resolved by Multi-Ayanamsha arc commits between `649aa92a` and `837fbf07`.
- **v1.5 (2026-05-26, SRP-DEPLOY):** Corrects v1.4 false-zero claim. Documents 35 pre-existing failures: 13 in platform (UDA-1 spec gap, tooling-remediation, MSR count drift, RCS trace-audit, ICR resolution) and 22 in platform-mcp (tooling-remediation wrappers, tool catalog count, live-DB integration, signal-state schema). All 35 failures introduced by upstream commits after v1.4 was authored (UDA-1 PR #161 + tooling-remediation PR #159 + MARSYS-JIS tooling work, all on main before SRP merges). SRP introduced 0 new failures.
- **v1.4 (2026-05-24):** All 18 pre-existing failures from v1.3 resolved. Final suite: **0 failures**. (This claim was correct at v1.4 authoring time; 35 new failures were subsequently introduced by upstream PRs before the SRP-DEPLOY session.)
- **v1.3 (2026-05-23):** 18 pre-existing failures across 10 files (R11.B chrome, M5 Coverage, MCPT v3.1, Phase 4C, R11.F). All non-regression.
- **v1.2 (2026-05-20):** 0 failures — all 9 previously-failing files resolved.
- **v1.1 (2026-05-20):** 16 failures / 9 files (post-R10 merge).
- **v1.0 (2026-05-19):** 21 failures (pre-R7 baseline).

---

## v1.6 Resolution Summary

| v1.5 Group | Tests | Fix commit | Date |
|---|---|---|---|
| G1 — RETRIEVAL_CAPABILITY_SPEC gap | 2 | `49a83571` | 2026-05-30 |
| G2a — chart_facts_query TC.10 ToolBundle shape | 1 | `6fffa50a` | 2026-05-26 |
| G2b — query_dasha_periods tool_version | 1 | `6fffa50a` | 2026-05-26 |
| G3a — msr_parser signal count (514→573) + path | 1 | `49a83571` + `f7d0eeda` | 2026-05-30 |
| G3b — auto_deriver MSR_v3_0→MSR_v5_0 path | 1 | `49a83571` | 2026-05-30 |
| G3c — frontmatter_check field assertion + REPO_ROOT depth | 1 | `f7d0eeda` + `ef2e4c05` | 2026-05-30 |
| G4 — trace-audit positional param indices (×5) | 5 | `49a83571` | 2026-05-30 |
| G5 — ICR DIS.013 PROPOSED→RESOLVED gate | 1 | `49a83571` | 2026-05-30 |
| G6 — MCP tool wrapper callPlatformPrimitive shape (×15) | 15 | `837fbf07` | 2026-05-30 |
| G7 — tool_descriptions catalog count (22→40) | 2 | Multi-Ayanamsha arc | 2026-05-30 |
| G8 — live-DB CI guard (chart_summary, cross_scenario) | 4 | Multi-Ayanamsha arc | 2026-05-30 |
| G9 — query_signal_state Zod limit max 500→200 | 1 | `837fbf07` | 2026-05-30 |
| **TOTAL** | **35** | | |

---

## v1.5 Detail (archived — all resolved)

**ARCHIVED — all 35 failures resolved. "Fix path:" labels below have been converted to "Resolved by:" for audit trail. No action is pending in this section.**

### Platform package — 13 failures across 8 files

### Group 1 — UDA-1 RETRIEVAL_CAPABILITY_SPEC gap — 2 failures, 1 file

UDA-1 (PR #161, `0a2447f3`) added 15 tools to `RETRIEVAL_TOOLS` (channel mcp→both) without updating `RETRIEVAL_CAPABILITY_SPEC`. The spec coverage test enforces 1:1 parity between runtime tools and planner spec entries.

| File | Failures | Root cause |
|------|----------|------------|
| `src/lib/router/__tests__/retrieval_capability_spec.test.ts` | 2 | RETRIEVAL_TOOLS has 15 new tools with no matching spec entries |

Specific failing test names:
- `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > every runtime tool has a planner spec entry`
- `RETRIEVAL_CAPABILITY_SPEC × RETRIEVAL_TOOLS coverage > spec entry count matches runtime tool count exactly`

Resolved by: commit 49a83571 (2026-05-30) — 15 UDA-1 tools added to RETRIEVAL_CAPABILITY_SPEC.

---

### Group 2 — Tooling-remediation arc (ToolBundle parameter shape) — 2 failures, 2 files

Tooling-remediation (PR #159, `bace7b45`) changed how tools return ToolBundle shapes and how `callPlatformPrimitive` parameters are passed. Tests assert the pre-remediation shape.

| File | Failures | Root cause |
|------|----------|------------|
| `src/lib/retrieve/__tests__/chart_facts_query.test.ts` | 1 | Empty-filter path returns changed post-remediation |
| `src/lib/retrieve/__tests__/query_dasha_periods.test.ts` | 1 | ToolBundle shape assertion mismatch post-remediation |

Specific failing test names:
- `chart_facts_query tool > returns empty results for impossible filter without error`
- `query_dasha_periods bundle shape > returns a correctly shaped ToolBundle`

Resolved by: commit 6fffa50a (2026-05-26) — ToolBundle shape assertions updated for both test files.

---

### Group 3 — MSR count / manifest version drift — 3 failures, 3 files

MSR signal count and manifest version strings changed during UDA-4 (50 citation scaffolds added to MSR) and MCPT v3.2 (MSR_v3_0.md schema changes). Tests assert prior values.

| File | Failures | Root cause |
|------|----------|------------|
| `src/scripts/etl/__tests__/msr_parser.test.ts` | 1 | Test asserts 514 signals but MSR count changed (UDA-4 scaffolds + MCPT grounding) |
| `src/scripts/manifest/__tests__/auto_deriver.test.ts` | 1 | `expose_to_chat` flag derivation from MSR entry changed in MCPT v3.2 schema |
| `src/scripts/manifest/__tests__/frontmatter_check.test.ts` | 1 | `MSR_v3_0.md` frontmatter fields changed in MCPT v3.2 |

Specific failing test names:
- `parseMsrSignals > parses 514 signals`
- `deriveManifest > MSR entry has expose_to_chat true`
- `frontmatter discipline (Stream E verification) > MSR_v3_0.md has required frontmatter fields`

Resolved by: commits 49a83571 + f7d0eeda (Group 3a — msr_parser count 514→573 + relative path), 49a83571 (Group 3b — MSR_v3_0→MSR_v5_0 path), f7d0eeda + ef2e4c05 (Group 3c — frontmatter fields + REPO_ROOT depth). All 2026-05-30.

---

### Group 4 — RCS trace-audit positional param schema — 5 failures, 1 file

A commit in the RCS (Retrieval-Calibration-System) arc changed `writeTraceStep()` positional parameter positions/types. Tests assert the pre-RCS positional param contract.

| File | Failures | Root cause |
|------|----------|------------|
| `tests/cross-provider/trace-audit.test.ts` | 5 | `writeTraceStep()` positional params ($6, $10, $11, $12) shape changed; test asserts old positions |

Specific failing test names:
- `trace-audit: writeTraceStep() persists required tool_use fields > TA-1.2: step_type field is persisted (positional param $6)`
- `trace-audit: writeTraceStep() persists required tool_use fields > TA-1.4: latency_ms (duration_ms) is persisted (positional param $10)`
- `trace-audit: writeTraceStep() persists required tool_use fields > TA-1.5: parallel_group (tool_fetch marker) is persisted (positional param $11)`
- `trace-audit: writeTraceStep() persists required tool_use fields > TA-1.6: data_summary.tool_name is persisted in JSON payload (param $12)`
- `trace-audit: writeTraceStep() persists required tool_use fields > TA-1.7: all five required tool_use fields present in a single call`

Resolved by: commit 49a83571 (2026-05-30) — positional param indices corrected in trace-audit test.

---

### Group 5 — ICR DIS.013 resolution (PROPOSED→RESOLVED move) — 1 failure, 1 file

DIS.013 (Muntha Libra 7H conflict) was resolved at ICR-S3/S4 and the proposed-patch YAML was promoted from `PROPOSED/` to `RESOLVED/`. The ICR gate test checks for the PROPOSED location.

| File | Failures | Root cause |
|------|----------|------------|
| `tests/icr/propose_patch.test.ts` | 1 | `DIS.013_MSR.377_proposed.yaml` now in `CONFLICT_PATCHES/RESOLVED/` not `CONFLICT_PATCHES/PROPOSED/` |

Specific failing test name:
- `munta_propose_patch_emitted gate (ICR-S4) > DIS.013_MSR.377_proposed.yaml exists in PROPOSED/`

Resolved by: commit 49a83571 (2026-05-30) — ICR gate updated to check RESOLVED/ path.

---

## Platform-MCP package — 22 failures across 8 files

### Group 6 — Tooling-remediation arc (MCP wrapper callPlatformPrimitive signature) — 15 failures, 4 files

Tooling-remediation (PR #159, `bace7b45`) changed `callPlatformPrimitive` parameter passing conventions for tool wrappers. Four MCP tool wrapper test files assert the pre-remediation call signature.

| File | Failures | Root cause |
|------|----------|------------|
| `src/tools/muhurta_finder.test.ts` | 4 | `callPlatformPrimitive` call params changed; tests assert pre-remediation param order/names |
| `src/tools/query_divisional_chart.test.ts` | 4 | Same — `varga` param mapping changed |
| `src/tools/query_remedial_mantras.test.ts` | 5 | Same — `keyword` composition + `planet` param mapping changed |
| `src/tools/query_varshphal.test.ts` | 2 | Same — `year` + `chart_id` param passing changed |

Specific failing test names:
- `muhurta_finder > passes activity_type as event param to callPlatformPrimitive`
- `muhurta_finder > defaults chart_id to NATIVE_CHART_ID when not provided`
- `muhurta_finder > returns error result when date_from is after date_to`
- `muhurta_finder > returns error result when date range exceeds 30 days`
- `query_divisional_chart > passes varga param as the division value to callPlatformPrimitive`
- `query_divisional_chart > defaults chart_id to NATIVE_CHART_ID when not provided`
- `query_divisional_chart > handles D1 (Rasi) division correctly`
- `query_divisional_chart > handles D60 (Shashtiamsha) division correctly`
- `query_remedial_mantras > passes planet param to callPlatformPrimitive`
- `query_remedial_mantras > composes keyword from house when provided`
- `query_remedial_mantras > composes keyword from condition when provided`
- `query_remedial_mantras > composes keyword from both house and condition`
- `query_remedial_mantras > passes default limit of 8`
- `query_varshphal > passes year param to callPlatformPrimitive`
- `query_varshphal > passes custom chart_id when provided`

---

### Group 7 — Tool catalog count drift — 2 failures, 1 file

Test asserts 22 tools in the MCP catalog. Actual tool count changed (UDA-2 added 14 wrappers, bringing MCP to 40 tools; tool_descriptions test was not updated).

| File | Failures | Root cause |
|------|----------|------------|
| `test/tool_descriptions.test.ts` | 2 | Test expects 22 tools in CATALOG; actual count is 40 after UDA-2 additions |

Specific failing test names:
- `MCPT v3.2 Phase 3 — Tool description lint gate > CATALOG covers all 22 tools`
- `MCPT v3.2 Phase 3 — Tool description lint gate > every description starts with a disambiguator sentence`

Resolved by: Multi-Ayanamsha arc (2026-05-30) — tool catalog count updated to 40, description lint assertions regenerated.

---

### Group 8 — Live DB / integration tests (no CI database) — 4 failures, 2 files

These tests require a live Supabase connection. They pass locally with credentials but fail in CI (no DB env vars). No CI env guard (`skipIf` / `process.env` check) was added.

| File | Failures | Root cause |
|------|----------|------------|
| `test/chart_summary.test.ts` | 2 | Live Supabase query (`chart_facts` table) — no CI guard |
| `test/accuracy/cross_scenario.test.ts` | 2 | Live Supabase + MCP path comparison — no CI guard |

Specific failing test names:
- `MCPT v3.2 P4c — chart_summary: canonical bundle returns ≥50 rows > chart_summary({divisional_charts:["D1","D9","D10"]}) returns ≥50 fact rows`
- `MCPT v3.2 P4c — chart_summary: fixture parity vs query_chart_facts > chart_summary row-by-row: planet rows preserve all fields from query_chart_facts`
- `MCPT v3.2 P9a — Cross-Scenario Equivalence: MCP path vs direct path > chart_summary(D1 only) and query_chart_facts per-category return same claims`
- `MCPT v3.2 P9a — Cross-Scenario Equivalence: MCP path vs direct path > chart_summary with D1+D9 collects all divisional rows without duplication`

Resolved by: tests confirmed fixture-backed (offline simulation mode); no guard needed. Multi-Ayanamsha arc (2026-05-30).

---

### Group 9 — query_signal_state Zod limit validation — 1 failure, 1 file

The `query_signal_state` Zod schema changed after the AC.16 test was written; the `limit > 200` rejection path no longer triggers as expected.

| File | Failures | Root cause |
|------|----------|------------|
| `src/tools/query_signal_state.test.ts` | 1 | AC.16 limit > 200 Zod rejection no longer fires at schema level |

Specific failing test name:
- `query_signal_state — MCP tool wrapper > AC.16 — limit > 200 is rejected by Zod schema`

---

## SRP fix verification (on main, HEAD 649aa92a)

All 6 SRP fixes are present in the codebase and verified correct. The 35 failures above are entirely pre-existing and unrelated to SRP.

| Fix | Location | Status |
|-----|----------|--------|
| FIX-1: primitives_registry whitelists 37 tools (was 23) | `platform/src/lib/retrieve/primitives_registry.ts` | ✓ GREEN |
| FIX-2: forward_looking reads from request params | `platform/src/app/api/chat/consume/route.ts` | ✓ GREEN |
| FIX-3: valence enum matches DB schema | `platform-mcp/src/tools/lel_query.ts` | ✓ GREEN |
| FIX-4: sample_step cast to integer | `platform-mcp/src/tools/query_ephemeris.ts` | ✓ GREEN |
| FIX-5: significance field name + type corrected | `platform-mcp/src/tools/lel_query.ts` | ✓ GREEN |
| FIX-6: lel_query source_version annotation → v1.7 | `platform-mcp/src/tools/lel_query.ts` | ✓ GREEN |

SRP test PRs pending merge review as of v1.5 (2026-05-26); resolution status not confirmed in governance docs — check git log or GitHub for current state (test-suite branches, non-blocking for production):
- PR #166 — T-1 portal unit tests (24 tests)
- PR #167 — T-2 MCP unit tests (27 tests)
- PR #168 — T-3 integration tests
- PR #169 — T-4 system tests

---

## Historical baselines

- **v1.0** (2026-05-19, pre-R7): 21 failures
- **v1.1** (2026-05-20, post-R10 merge): 16 failures / 9 files
- **v1.2** (2026-05-20, closeout-residuals): 0 failures — all resolved
- **v1.3** (2026-05-23, R11.G-S4 refresh): 18 failures / 10 files — all pre-existing, 0 R11.G regressions
- **v1.4** (2026-05-24): 0 failures at authoring time — 35 new failures subsequently introduced by UDA-1 PR #161 + tooling-remediation PR #159; corrected by v1.5
- **v1.5** (2026-05-26, SRP-DEPLOY): 35 failures — 13 platform + 22 platform-mcp; all pre-existing; 0 SRP regressions
- **v1.6** (2026-05-31): 0 failures — all 35 resolved by commits on 2026-05-26 and 2026-05-30; see Resolution Summary table above.

*v1.6 authored 2026-05-31. main HEAD: 206d6370. Both packages at 0 failures.*
