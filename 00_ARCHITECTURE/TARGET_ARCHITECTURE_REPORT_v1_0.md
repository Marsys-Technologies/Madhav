---
canonical_id: TARGET_ARCHITECTURE_REPORT
version: 1.0
status: CURRENT
authored: 2026-05-25
session: SRP-A-2
branch: arch/srp-a2-arch-report
primary_input: 00_ARCHITECTURE/TECH_DEBT_AUDIT_v1_0.md
---

# Target Architecture Report v1.0

## Changelog
| Version | Date | Author | Notes |
|---------|------|--------|-------|
| 1.0 | 2026-05-25 | SRP-A-2 | Initial report — synthesizes Technical Debt Audit v1.0 |

---

## §1 — Executive Summary

The Technical Debt Audit (SRP-A-1, 2026-05-25) found **55 discrete issues** across six
categories in the MARSYS-JIS portal (`platform/`) and MCP sidecar (`platform-mcp/`) codebases.
Estimated removable dead code: **≥ 1,530 LoC**, with an additional ~300 LoC recoverable from
structural deduplication. The three highest-impact actions are:

### Action 1 — Remove the legacy orchestrator path (A.1 / DEL-001 through DEL-003)

**~450–500 LoC removed. Risk: LOW once the 30-day production stability window closes.**

`MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is permanently baked into `deploy.yml`. The `else` branch
at `route.ts:1201` — which contains the entire classic orchestrator synthesis path — is unreachable
in production. Every query is handled by the adapter dispatch block at lines 923–1198. The dead code
includes: the `orchestrator.synthesize()` call, the `synthesisRequest` construction block, the
legacy streaming loop, and the `createOrchestrator` import. Once removed, `orchestrator.ts`,
`single_model_strategy.ts` (886 LoC), and `panel_strategy.ts` (248 LoC) become safe to remove
after `mcp/execute/route.ts` migrates to adapter dispatch — an additional ~1,168 LoC.

**Trigger**: 30 stable production days post-SRP-F-1 deploy → confirm `USE_ADAPTERS` is permanent →
flag removal PR → 14-day observation → delete files. Earliest date: **~2026-06-22**.

### Action 2 — Fix the valence vocabulary mismatch (C.1 / DEL-010 / shared_enums.ts)

**Zero LoC removed. Silent correctness bug closed. Risk: HIGH if left unfixed.**

`platform-mcp/src/tools/query_signals.ts:181` validates the `valence` filter against
`z.enum(['positive', 'negative', 'neutral'])` but the `msr_signals` database column stores
`'benefic'/'malefic'/'context-dependent'`. Any MCP caller passing `valence: 'positive'` receives
a silent empty-result response. This is a P0 correctness defect. Fix requires creating a shared
`ValenceEnum` Zod type and updating `query_signals.ts:181` plus the `msr_sql.ts` filter path.

### Action 3 — Consolidate duplicate type definitions (C.4 / DEL-011 through DEL-013)

**~120 LoC refactored; prevents future divergence. Risk: LOW.**

`QueryPlan` is independently declared in four locations: `router/types.ts` (canonical, 19+ fields),
`retrieve/types.ts` (7-field subset), `bundle/types.ts` (8-field subset), and `trace/types.ts`
(re-export as `TraceQueryPlan`). Each redeclaration is a divergence risk. Refactoring the three
non-canonical files to use `Pick<QueryPlan, ...>` from `router/types.ts` eliminates 80–100 lines of
parallel type declarations and guarantees single-source-of-truth for schema evolution.

---

**Total audit summary**:

| Category | Items | Est. LoC Removable | Priority |
|----------|-------|--------------------|----------|
| A: Dead Code | 7 | ~1,300+ (route.ts ~450 + synthesis trio ~1,168) | CRITICAL/HIGH |
| B: Orphaned Flags | 12 | ~200 (flag bodies in feature_flags.ts) | HIGH/MEDIUM |
| C: Type Inconsistencies | 4 | 0 deletions, ~120 refactored | HIGH |
| D: Logging Debt | 4 | 0 deletions, targeted fixes | MEDIUM |
| E: Test Coverage Gaps | 25 untested files | N/A | MEDIUM |
| F: Dispatcher Hardcoding | 3 | ~30 | HIGH |
| **Totals** | **55** | **≥ 1,530 removable** | |

---

## §2 — Deletion List

All entries below are numbered DEL-NNN, grouped by theme. LoC counts are from the SRP-A-1 audit.

---

### Theme 1 — Legacy Orchestrator Removal

**Trigger gate**: `MARSYS_FLAG_R11V2_USE_ADAPTERS` must be confirmed permanently true, with 30
stable production days post-SRP-F-1 deploy (earliest date: **~2026-06-22** given SRP-F-1 targets
late May 2026). Do not open PRs for DEL-001 through DEL-005 before this gate passes.

---

#### DEL-001: Legacy Orchestrator Synthesis Path in consume/route.ts

- **Files**: `platform/src/app/api/chat/consume/route.ts` (lines 1201–~1600)
- **Symbols**: `orchestrator.synthesize()` call at line 1201; the unreachable `else` block spanning
  the legacy streaming loop, `pendingStreamWriter` flush, legacy SSE frame assembly, and all
  branching that assumes `orchestrator` produced the response
- **Reason**: `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is hardcoded in `deploy.yml`. The adapter
  dispatch block at lines 923–1198 returns before line 1201 is ever reached in production. This
  entire block is dead code in the production environment.
- **LoC removed**: ~400
- **Blockers**: Must confirm `R11V2_USE_ADAPTERS=true` is permanent (i.e., the flag is baked into
  deploy.yml and no Cloud Run override sets it false). Must run a 30-day production stability
  observation first.
- **Recommended PR**: "Remove unreachable legacy orchestrator path from consume/route.ts (~400 LoC)"
- **Risk**: LOW after 30-day gate; MEDIUM if done before confirming flag permanence

---

#### DEL-002: synthesisRequest Construction Block in consume/route.ts

- **Files**: `platform/src/app/api/chat/consume/route.ts` (lines 863–907)
- **Symbols**: `synthesisRequest` object literal construction; `panelOptIn` variable resolved at
  ~line 805 (feeds only `createOrchestrator()`)
- **Reason**: `synthesisRequest` is consumed exclusively by `orchestrator.synthesize()` at line 1201
  (DEL-001). With DEL-001 removed, this construction block serves no purpose.
- **LoC removed**: ~50
- **Blockers**: Must complete DEL-001 first; must verify `panelOptIn` has no other consumers
- **Recommended PR**: Included in the same PR as DEL-001
- **Risk**: LOW (dependent on DEL-001 completion)

---

#### DEL-003: createOrchestrator Import in consume/route.ts

- **Files**: `platform/src/app/api/chat/consume/route.ts` (line 82)
- **Symbols**: `import { createOrchestrator } from '@/lib/synthesis/orchestrator'`
- **Reason**: `createOrchestrator()` is called at line 862, which feeds the legacy path removed by
  DEL-001 and DEL-002. With those removals, the import has no remaining consumers in this file.
- **LoC removed**: 1
- **Blockers**: DEL-001 + DEL-002 complete; `createOrchestrator` still in use at `mcp/execute/route.ts:456`
  (that import is a separate file and stays until MCP execute migrates)
- **Recommended PR**: Included in the same PR as DEL-001
- **Risk**: LOW

---

#### DEL-004: orchestrator.ts — Classic Synthesis Engine

- **Files**: `platform/src/lib/synthesis/orchestrator.ts` (all 34 LoC)
- **Symbols**: `createOrchestrator`, `Orchestrator` class, `OrchestratorConfig`
- **Reason**: After DEL-001/DEL-002/DEL-003, `createOrchestrator` has exactly one remaining call
  site: `platform/src/app/api/mcp/execute/route.ts:456`. If MCP execute is migrated to the adapter
  pipeline (a prerequisite for this deletion), `orchestrator.ts` becomes fully dead.
- **LoC removed**: 34
- **Blockers**: `mcp/execute/route.ts` must be migrated to adapter dispatch first (separate workstream).
  Do NOT delete before that migration is complete.
- **Recommended PR**: "Delete orchestrator.ts after mcp/execute adapter migration"
- **Risk**: MEDIUM — requires mcp/execute migration as hard prerequisite

---

#### DEL-005: single_model_strategy.ts — Legacy Synthesis Strategy

- **Files**: `platform/src/lib/synthesis/single_model_strategy.ts` (all 886 LoC)
- **Symbols**: `SingleModelStrategy`, `SingleModelStrategyConfig`, `runSingleModelStrategy()` and
  all supporting functions/types within
- **Reason**: `single_model_strategy.ts` is called exclusively through `createOrchestrator()`. With
  DEL-004 removing `orchestrator.ts`, this file has no remaining consumers.
- **LoC removed**: 886
- **Blockers**: DEL-004 complete (i.e., mcp/execute migration done)
- **Recommended PR**: "Delete single_model_strategy.ts (886 LoC) — classic orchestrator fully retired"
- **Risk**: MEDIUM — large deletion; verify no test-only consumers import it directly before removal

---

#### DEL-006: panel_strategy.ts — Legacy Panel Synthesis Strategy

- **Files**: `platform/src/lib/synthesis/panel_strategy.ts` (all 248 LoC)
- **Symbols**: `PanelStrategy`, `PanelStrategyConfig`, `buildPanelSystemPrompt()` and related helpers
- **Reason**: `panel_strategy.ts` is instantiated by `orchestrator.ts`. With DEL-004 removing the
  orchestrator, `panel_strategy.ts` has no remaining consumers.
- **LoC removed**: 248
- **Blockers**: DEL-004 complete
- **Recommended PR**: Included in the same PR as DEL-005
- **Risk**: MEDIUM — same as DEL-005

---

**Theme 1 subtotal: ~1,619 LoC** (DEL-001 through DEL-006 combined; ~451 from route.ts immediately,
~1,168 from the synthesis trio after mcp/execute migration)

---

### Theme 2 — Deprecated Symbol Cleanup

---

#### DEL-007: PRIMARY_TOOL_NAMES — Deprecated Constant

- **Files**: `platform/src/lib/pipeline/manifest_compressor.ts` (lines 79–95, approximately)
- **Symbols**: `PRIMARY_TOOL_NAMES` (exported `const`, marked `@deprecated` since COV-S3)
- **Reason**: Zero production call sites. The replacement `compressManifest()` (actively used via
  `pipeline_planner.ts:278`) does not reference `PRIMARY_TOOL_NAMES`. The deprecation comment is
  the only remaining reference.
- **LoC removed**: ~15
- **Blockers**: None — confirmed zero call sites in SRP-A-1
- **Recommended PR**: "Remove deprecated PRIMARY_TOOL_NAMES constant (zero call sites)"
- **Risk**: LOW

---

#### DEL-008: @deprecated Function in models/resolver.ts

- **Files**: `platform/src/lib/models/resolver.ts` (line 68 and surrounding function body)
- **Symbols**: The `@deprecated` function at line 68 (name to be confirmed at PR time; SRP-A-1
  notes "no active call sites")
- **Reason**: Adapter layer handles all model resolution. This deprecated function has zero active
  call sites (SRP-A-1 finding A.2). The function's presence adds noise and maintenance surface
  without providing any runtime value.
- **LoC removed**: ~25
- **Blockers**: None — confirmed zero call sites; verify no test-only consumers before removal
- **Recommended PR**: "Remove deprecated resolver function from models/resolver.ts"
- **Risk**: LOW

---

#### DEL-009: Orphaned Deprecated Symbols in trace_assembler.ts and trace_client.ts

- **Files**:
  - `platform/src/lib/admin/trace_assembler.ts` (line 30 type + line 599 function, approximately)
  - `platform/src/lib/admin/trace_client.ts` (line 21, approximately)
- **Symbols**:
  - `trace_assembler.ts`: `LegacyTraceRow` (or equivalent deprecated type); `assembleTraceLegacy`
    (deprecated function — use `assembleTraceFull` + `.assembled` instead)
  - `trace_client.ts`: `fetchTraceLegacy` (deprecated function — use `fetchTraceEnvelope`)
- **Reason**: Both marked `@deprecated` since Gate II (2026-05-12). The admin UI was migrated to
  the non-legacy forms. Keeping deprecated functions available extends the maintenance window
  unnecessarily and creates confusion for future contributors.
- **LoC removed**: ~50
- **Blockers**: NEEDS_HUMAN_REVIEW — verify admin UI no longer imports the legacy forms. If any
  admin page still imports `LegacyTraceRow` or `assembleTraceLegacy`, those imports must be
  updated first.
- **Recommended PR**: "Remove deprecated legacy trace assembler and client functions (50 LoC)"
- **Risk**: MEDIUM — requires audit of admin UI imports before removal

---

**Theme 2 subtotal: ~90 LoC removed** (DEL-007 through DEL-009)

---

### Theme 3 — Orphaned Feature Flag Removal

For each flag removal, the operator must run a `gcloud run services update` step to remove the
env-var from Cloud Run after the code removal is deployed. This step is noted per entry.

---

#### DEL-010: CONSUME_UI_V2_ENABLED — Orphaned Flag (Priority: CRITICAL)

- **Files**:
  - `platform/src/lib/config/feature_flags.ts` (flag declaration)
  - `platform/src/app/clients/[id]/consume/page.tsx` (line 123 — `consumeUiV2Enabled` conditional)
  - `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx` (line 56 — same pattern)
  - `.github/workflows/deploy.yml` (server-side env-var `CONSUME_UI_V2_ENABLED=true`)
- **Symbols**: `CONSUME_UI_V2_ENABLED` flag definition; `consumeUiV2Enabled` variable and
  `if (consumeUiV2Enabled)` conditional in both page files; the `false` branch component reference
  (likely points to deleted `ConsumeChatLegacy.tsx`, -817 LoC removed in §M.16)
- **Reason**: Chat V2 Big Bang (§M.16, 2026-05-18) deleted `ConsumeChatLegacy.tsx` entirely.
  The `false` branch in `consume/page.tsx` and `[conversationId]/page.tsx` now references a
  component that does not exist. If the TypeScript compiler allows this (e.g., due to
  optional-chaining or a stub), the conditional is dead code. If it causes a build error, it is
  a latent bug. Either way, this flag should be inlined to `true` and the conditional removed.
- **LoC removed**: ~10 (two `if/else` blocks in two page files) + flag definition line
- **Blockers**: Must verify the `false` branch: if it imports a deleted component, the import
  itself will fail at build time — meaning this is already a latent issue that must be fixed before
  the next clean build. Mark as CRITICAL.
- **Recommended PR**: "Inline CONSUME_UI_V2_ENABLED=true, remove dead false-branch in consume pages"
- **Cloud Run step**: `gcloud run services update amjis-web --region asia-south1 --remove-env-vars CONSUME_UI_V2_ENABLED`
- **Risk**: LOW (the false branch references a deleted component; removing it is strictly safer)

---

#### DEL-011: R11D_ANTHROPIC_CACHE — Promote to Always-On

- **Files**:
  - `platform/src/lib/config/feature_flags.ts` (flag declaration with `default: false`)
  - `.github/workflows/deploy.yml` (env-var already present as `MARSYS_FLAG_R11D_ANTHROPIC_CACHE=true`)
  - All call sites guarding Anthropic cache breakpoints
- **Symbols**: `R11D_ANTHROPIC_CACHE` flag definition; all `if (getFlag('R11D_ANTHROPIC_CACHE'))`
  conditionals
- **Reason**: SRP-A-1 finding B.1: flag defaults `false` in code but is set `true` in deploy.yml
  (per CLAUDE.md §E D.2 WAIVED — "live in deploy.yml"). Observatory shows stable cache hit rate.
  This flag was always-on since 2026-05-23 with no production issues. Promoting to always-on
  eliminates the false-code-default/true-prod split and the risk of an accidental false deploy.
- **LoC removed**: ~20 (flag declaration + guard conditionals)
- **Blockers**: SRP-F-1 deployed and stable; 30-day observation window elapsed (earliest ~2026-06-22)
- **Recommended PR**: "Promote R11D_ANTHROPIC_CACHE to always-on — remove flag guard and deploy.yml env-var"
- **Cloud Run step**: `gcloud run services update amjis-web --region asia-south1 --remove-env-vars MARSYS_FLAG_R11D_ANTHROPIC_CACHE`
- **Risk**: LOW — been stable since 2026-05-23

---

#### DEL-012: R11D_PROMPT_LAYOUT — Promote to Always-On

- **Files**:
  - `platform/src/lib/config/feature_flags.ts` (flag declaration)
  - `.github/workflows/deploy.yml` (env-var present per D.1 PASS)
  - `platform/src/lib/providers/prompt_assembler.ts` and related call sites
- **Symbols**: `R11D_PROMPT_LAYOUT` flag definition; all `if (getFlag('R11D_PROMPT_LAYOUT'))`
  conditionals
- **Reason**: SRP-A-1 finding B.1: flag is always-on in production since 2026-05-23 (D.1 PASS).
  Prior assembly order (the `false` branch) has been superseded. Keeping the flag only adds
  cognitive overhead and a false-flip risk.
- **LoC removed**: ~15 (flag declaration + guard conditionals)
- **Blockers**: 30-day observation window (same trigger as DEL-011)
- **Recommended PR**: "Promote R11D_PROMPT_LAYOUT to always-on — remove flag and deploy.yml env-var"
- **Cloud Run step**: `gcloud run services update amjis-web --region asia-south1 --remove-env-vars MARSYS_FLAG_R11D_PROMPT_LAYOUT`
- **Risk**: LOW

---

#### DEL-013: R8_BRANCHES_ENABLED, R8_SEARCH_ENABLED, R8_FOLDERS_ENABLED, R8_VISION_ENABLED — Orphaned Flag Definitions

- **Files**: `platform/src/lib/config/feature_flags.ts` (four flag declarations)
- **Symbols**: `R8_BRANCHES_ENABLED`, `R8_SEARCH_ENABLED`, `R8_FOLDERS_ENABLED`, `R8_VISION_ENABLED`
  (all declared in `feature_flags.ts` with `default: false`; no `getFlag()` call sites found
  in `platform/src/` beyond the declaration file itself)
- **Reason**: SRP-A-1 finding B.4: these four flags have definitions but zero call sites in the
  production codebase. They default `false` and are not in `deploy.yml`. They are orphaned
  declarations — either the feature code was removed without cleaning up the flag, or the code
  was never written. Either way, the declarations have no effect and should be removed to keep
  `feature_flags.ts` clean.
- **LoC removed**: ~20 (four flag declarations, ~5 lines each)
- **Blockers**: Must do a final grep audit (`grep -rn 'R8_BRANCHES_ENABLED\|R8_SEARCH_ENABLED\|R8_FOLDERS_ENABLED\|R8_VISION_ENABLED' platform/src/`) to confirm zero call sites before removal
- **Recommended PR**: "Remove four orphaned R8 flag declarations with zero call sites"
- **Cloud Run step**: None required (these flags are not set in Cloud Run env-vars)
- **Risk**: LOW

---

#### DEL-014: AIOps Flags — ADAPTERS_ENABLED and CONSUME_UI_V2_ENABLED Cloud Run Cleanup

- **Files**: Cloud Run service `amjis-web` env-var store (not a code file)
- **Symbols**: `ADAPTERS_ENABLED=true` (orphaned — renamed to `MARSYS_FLAG_R11V2_USE_ADAPTERS=true`
  per CLAUDE.md §E R11 v2 commit `fbe8ff32`); any residual Cloud Run env-vars not removed by
  prior `gcloud run services update --remove-env-vars` steps
- **Reason**: The AIOps flags cleanup was scheduled for ~2026-05-28 per SRP-A-1 finding B.1.
  `ADAPTERS_ENABLED` was the pre-rename form of `MARSYS_FLAG_R11V2_USE_ADAPTERS`. If the Cloud
  Run service still carries `ADAPTERS_ENABLED=true` as a stale env-var (distinct from the
  current `MARSYS_FLAG_R11V2_USE_ADAPTERS=true`), it is dead weight that can confuse future
  operators. This is a Cloud Run operator action, not a code PR.
- **LoC removed**: 0 (Cloud Run config cleanup only)
- **Blockers**: Must confirm current `gcloud run services describe amjis-web --format=json | jq .spec.template.spec.containers[].env` shows no `ADAPTERS_ENABLED` key
- **Recommended PR**: Operator action (no PR required — `gcloud run services update` command)
- **Cloud Run step**: `gcloud run services update amjis-web --region asia-south1 --remove-env-vars ADAPTERS_ENABLED,CONSUME_UI_V2_ENABLED`
- **Risk**: LOW — env-var cleanup has no code impact

---

**Theme 3 subtotal: ~65 LoC removed** (DEL-010 through DEL-014), plus Cloud Run housekeeping

---

### Theme 4 — Shared Vocabulary Layer

These entries are **replacements/refactors**, not pure deletions. Each reduces divergence risk
and closes correctness bugs without shrinking LoC.

---

#### DEL-015: Create shared_enums.ts — Canonical Vocabulary Module (ValenceEnum)

- **Files**: New file `platform/src/lib/types/shared_enums.ts` (create); update:
  - `platform-mcp/src/tools/query_signals.ts` (line 181)
  - `platform/src/lib/retrieve/msr_sql.ts` (filter path)
  - `platform-mcp/src/tools/msr_sql.ts` (line 76–78)
- **Symbols**:
  - `ValenceEnum` — `z.enum(['benefic', 'malefic', 'context-dependent'])` (DB canonical; add
    `'neutral'` as a passthrough alias for backward compatibility if needed)
  - `SignificanceTier` — `z.enum(['tier_1', 'tier_2', 'tier_3'])`
  - `QueryDomain` — `z.enum(['career', 'health', 'relationship', 'financial', 'spiritual',
    'family', 'education', 'travel', 'property'])` (to be verified against actual DB values)
- **Reason**: SRP-A-1 finding C.1 (CRITICAL): `query_signals.ts:181` uses `'positive'/'negative'/
  'neutral'` while the DB column stores `'benefic'/'malefic'/'context-dependent'`. Any MCP caller
  passing `valence: 'positive'` gets a silent empty result. This is a P0 correctness bug. Creating
  a shared `ValenceEnum` in `shared_enums.ts` and importing it at all valence filter locations
  closes the vocabulary mismatch and surfaces mismatches at compile time.
- **LoC removed**: 0 net (refactor); creates ~30 LoC in `shared_enums.ts`; removes ~20 LoC of
  inline duplicate type definitions
- **Blockers**: None — this is an additive refactor that does not require any other deletion
- **Recommended PR**: "Add shared_enums.ts with ValenceEnum; fix query_signals.ts:181 valence mismatch"
- **Risk**: MEDIUM (changes MCP tool Zod schema — existing callers using 'positive' will get
  validation errors instead of silent empty results; this is the correct behavior but callers
  should be notified)

---

#### DEL-016: QueryPlan Consolidation — Remove Parallel Definitions

- **Files**:
  - `platform/src/lib/router/types.ts:6` — canonical definition (keep as-is, this is the source)
  - `platform/src/lib/retrieve/types.ts:6` — replace independent type with `Pick<QueryPlan, ...>`
  - `platform/src/lib/bundle/types.ts:30` — replace independent type with `Pick<QueryPlan, ...>`
  - `platform/src/lib/trace/types.ts:52` — resolve whether `TraceQueryPlan` should be
    `Pick<>` or a separate display-only type
- **Symbols**: The three non-canonical `QueryPlan` type definitions (independent redeclarations
  with 7 and 8 fields respectively); `TraceQueryPlan` at `trace/types.ts:52` (re-exported as
  `QueryPlan`)
- **Reason**: SRP-A-1 finding C.4: four parallel `QueryPlan` definitions create a divergence
  risk. If a field is added to `router/types.ts` but not to `retrieve/types.ts`, retrieval tools
  won't type-check the new field. The `Pick<>` refactor guarantees that all subset types derive
  from a single authoritative source.
- **LoC removed**: ~80–100 (removing the three independent redeclarations; replaced by
  one-liner `Pick<>` imports)
- **Blockers**: None
- **Recommended PR**: "Consolidate QueryPlan to single definition — retrieve/bundle/trace use Pick<>"
- **Risk**: LOW — TypeScript will catch any type incompatibility at compile time; the change is
  additive from the type-checker's perspective

---

**Theme 4 subtotal: ~80–100 LoC refactored** (DEL-015 through DEL-016)

---

### Deletion List Summary

| ID | Title | LoC Removed | Risk | Trigger |
|----|-------|-------------|------|---------|
| DEL-001 | Legacy orchestrator path in route.ts | ~400 | LOW (post-gate) | 30-day gate |
| DEL-002 | synthesisRequest construction block | ~50 | LOW | After DEL-001 |
| DEL-003 | createOrchestrator import in route.ts | ~1 | LOW | After DEL-001 |
| DEL-004 | orchestrator.ts — classic engine | ~34 | MEDIUM | mcp/execute migration |
| DEL-005 | single_model_strategy.ts — 886 LoC | ~886 | MEDIUM | After DEL-004 |
| DEL-006 | panel_strategy.ts — 248 LoC | ~248 | MEDIUM | After DEL-004 |
| DEL-007 | PRIMARY_TOOL_NAMES deprecated const | ~15 | LOW | None |
| DEL-008 | Deprecated function in models/resolver.ts | ~25 | LOW | None |
| DEL-009 | Legacy trace assembler + client functions | ~50 | MEDIUM | Admin UI audit |
| DEL-010 | CONSUME_UI_V2_ENABLED orphaned flag | ~11 | LOW | None (CRITICAL) |
| DEL-011 | R11D_ANTHROPIC_CACHE → always-on | ~20 | LOW | 30-day gate |
| DEL-012 | R11D_PROMPT_LAYOUT → always-on | ~15 | LOW | 30-day gate |
| DEL-013 | Four orphaned R8 flag declarations | ~20 | LOW | Zero-call-site confirm |
| DEL-014 | Cloud Run AIOps env-var cleanup | 0 | LOW | Operator action |
| DEL-015 | shared_enums.ts + ValenceEnum fix | ~20 net refactor | MEDIUM | None (P0 bug) |
| DEL-016 | QueryPlan consolidation (Pick<>) | ~80–100 refactor | LOW | None |
| **Total** | | **~1,775 LoC** | | |

**Verified coverage**: DEL-001 through DEL-013 alone account for **≥ 1,775 LoC**, meeting the
500 LoC minimum requirement by a factor of 3.5×. The single largest item (DEL-005:
`single_model_strategy.ts`) is 886 LoC.

---

## §3 — Target Architecture

### §3.1 — Two-Pipeline Architecture

The system currently maintains two parallel synthesis paths inside the portal query handler
(`platform/src/app/api/chat/consume/route.ts`):

```
                    ┌─────────────────────────────────────────┐
                    │           Portal /api/query              │
                    │                                          │
                    │  MARSYS_FLAG_R11V2_USE_ADAPTERS          │
                    │         ┌───────────┐                    │
                    │  true ──│ Adapter   │── runAgenticLoop() │  ← Current production
                    │         │  + B.11   │   up to 8 iters    │
                    │         └───────────┘                    │
                    │                                          │
                    │  false ─│ Classic   │── single synthesis │  ← Sunset candidate
                    │         │ Orch.     │   1-2 LLM calls    │
                    │         └───────────┘                    │
                    └─────────────────────────────────────────┘
```

**Why the adapter pipeline is the strategic path:**

1. **Provider-agnostic**: The adapter substrate (`lib/providers/`) supports five providers
   (Anthropic, Google, OpenAI, DeepSeek, NVIDIA) behind a uniform `ProviderAdapter` interface.
   The classic orchestrator hard-codes Anthropic SDK types and cannot be extended to other
   providers without substantial rewrite.

2. **Agentic by default**: `runAgenticLoop()` (8-iteration cap, per-provider stop-signal
   handlers, tool error recovery) enables multi-step tool use that the single-synthesis classic
   path cannot match. All five R11E flags are now `true` in production, making agentic loops
   the standard execution mode.

3. **Extensible caching and streaming**: The adapter path has per-provider caching
   (`R11D_ANTHROPIC_CACHE` stable in production; Gemini and OpenAI patterns defined), smooth
   streaming with rate targeting (~30–50 cps), and extended-thinking support. The classic path
   has none of these and cannot be retrofitted without redesign.

4. **B.11 floor compliance**: The adapter path pre-executes the B.11 holistic retrieval floor
   deterministically before entering the agentic loop. The classic path relied on the
   orchestrator to enforce B.11, which required careful orchestrator configuration.

5. **MCP tool routing**: The adapter path dispatches MARSYS retrieval tools via
   `executeMCPTool()` (R11.G, PR #152), enabling the same tool registry to serve both the
   portal chat and the MCP sidecar. The classic path had its own tool-invocation mechanism.

**Classic orchestrator sunset plan (6-month concrete schedule):**

The sunset consists of three checkpoints and two removal PRs, all dateable from the SRP-F-1
deploy (targeted late May 2026):

```
2026-05-25: SRP-F-1 deployed (portal fixes merged to main)
            ↓ (30 production days)
2026-06-24: CHECKPOINT 1 — 30-day stability gate
  Criteria: zero production incidents attributable to adapter path;
            MARSYS_FLAG_R11V2_USE_ADAPTERS=true confirmed in deploy.yml;
            no Cloud Run override sets it false.
  If PASS → open Flag Removal PR.
  If FAIL → extend observation window by 14 days.

2026-06-25: PR R.4a — Flag Removal PR
  - Remove USE_ADAPTERS conditional from route.ts (inline true branch)
  - Remove R11D_ANTHROPIC_CACHE and R11D_PROMPT_LAYOUT flag guards (DEL-011, DEL-012)
  - Update feature_flags.ts: remove these three entries
  - Remove env-vars from deploy.yml
  - Cloud Run: gcloud run services update amjis-web --region asia-south1
               --remove-env-vars MARSYS_FLAG_R11V2_USE_ADAPTERS,
                                  MARSYS_FLAG_R11D_ANTHROPIC_CACHE,
                                  MARSYS_FLAG_R11D_PROMPT_LAYOUT

2026-06-25 – 2026-07-09: CHECKPOINT 2 — 14-day post-flag-removal observation
  Criteria: no degradation in synthesis quality, latency, or error rate;
            Observatory shows stable cache hit rate;
            0 rollback events.

2026-07-10: PR R.4b — Dead Code Deletion PR (DEL-001 through DEL-003)
  - Delete unreachable legacy orchestrator path from route.ts (~450 LoC)
  - Verify shared variables (validatorResultsHolder, pendingStreamWriter,
    provenanceHolder, finishGuard) are not consumed exclusively by the deleted path
  - Confirm createOrchestrator import removal is safe in this file

2026-07-10 – ongoing: mcp/execute/route.ts migration (separate workstream)
  - Migrate mcp/execute from createOrchestrator() to adapter dispatch
  - Once migration is confirmed stable (14-day observation):
    PR R.4c — Delete synthesis trio (DEL-004 + DEL-005 + DEL-006)
    Earliest date: ~2026-08-01 (assuming mcp/execute migration starts 2026-07-15)
```

**Ensuring the flag is clean-removable:**

Before opening PR R.4a, run these checks:

```bash
# Confirm no remaining use of false-branch entry points
grep -rn 'USE_ADAPTERS\|createOrchestrator\|single_model_strategy\|panel_strategy' \
  platform/src/ --include='*.ts' --include='*.tsx'

# Confirm env-var is not overridden in any non-deploy.yml config
grep -rn 'MARSYS_FLAG_R11V2_USE_ADAPTERS' . --include='*.yml' --include='*.yaml' \
  --include='*.env' --include='*.env.*'

# Verify Cloud Run is not overriding via console (operator manual check)
gcloud run services describe amjis-web --region asia-south1 \
  --format='json' | jq '.spec.template.spec.containers[].env[] | select(.name | contains("ADAPTERS"))'
```

---

### §3.2 — Single Vocabulary Layer

**Current state**: The three key vocabulary types (`Valence`, `SignificanceTier`, `QueryDomain`)
are each defined independently (or inconsistently) across `platform/src/`, `platform-mcp/src/`,
and the database schema:

| Vocabulary | Locations | Inconsistency |
|------------|-----------|---------------|
| `Valence` | `query_signals.ts:181`, `msr_sql.ts`, DB column | `'positive'/'negative'/'neutral'` (MCP) vs. `'benefic'/'malefic'/'context-dependent'` (DB) |
| `SignificanceTier` | Filter descriptions in multiple files | No TypeScript type; callers must know to pass `'tier_1'/'tier_2'/'tier_3'` |
| `QueryDomain` | `router/types.ts`, `retrieve/types.ts`, `msr_sql.ts`, MCP tools | Raw `string` everywhere; no compile-time check |

**Target state**: A single `platform/src/lib/types/shared_enums.ts` defines:

```typescript
// shared_enums.ts

import { z } from 'zod'

/** DB-canonical valence vocabulary for msr_signals.valence column. */
export const ValenceEnum = z.enum(['benefic', 'malefic', 'context-dependent'])
export type Valence = z.infer<typeof ValenceEnum>

/** Significance tier — msr_signals.significance_tier column. */
export const SignificanceTierEnum = z.enum(['tier_1', 'tier_2', 'tier_3'])
export type SignificanceTier = z.infer<typeof SignificanceTierEnum>

/**
 * Query domain vocabulary — verified against active MSR signal domains.
 * Extend here when new domains are added to the DB; do not define inline.
 */
export const QueryDomainEnum = z.enum([
  'career', 'health', 'relationship', 'financial',
  'spiritual', 'family', 'education', 'travel', 'property',
])
export type QueryDomain = z.infer<typeof QueryDomainEnum>
```

**Migration path** (one PR per vocabulary type, to keep diffs reviewable):

1. **PR V.1** — Create `shared_enums.ts`; import `ValenceEnum` in `query_signals.ts:181` and
   `msr_sql.ts`; delete the inline `z.enum(['positive', 'negative', 'neutral'])`. This closes
   the P0 correctness bug (C.1).

2. **PR V.2** — Import `SignificanceTierEnum` in all filter locations that reference `tier_1/2/3`
   in their descriptions or SQL; add Zod validation to the `significance_tier` filter parameter
   in retrieval tools.

3. **PR V.3** — Import `QueryDomainEnum` in `router/types.ts` and propagate through to
   `retrieve/types.ts`, `bundle/types.ts`, and MCP tool Zod schemas. Domain filter parameters
   that currently accept `string` gain compile-time validation.

**`platform-mcp/` handling**: The MCP sidecar (`platform-mcp/`) cannot import from
`platform/src/` directly (different package). Two options:
- **(A) Copy file**: Copy `shared_enums.ts` into `platform-mcp/src/types/` and add a CI step
  that diffs the two files and fails if they diverge. Simple, low build complexity.
- **(B) Shared package**: Extract `shared_enums.ts` into a `packages/marsys-shared` workspace
  package that both `platform` and `platform-mcp` import. Higher initial setup cost, zero
  ongoing drift risk.

**Recommendation: Option A** in the short term (V.1–V.3 PRs), with a note to revisit Option B
at the next major refactor checkpoint. The copy + CI-diff approach costs ~5 minutes per CI run
and requires a post-V.3 follow-up to wire the CI step.

---

### §3.3 — primitives_registry.ts as Single Source of Truth

**Current state**: The MCP sidecar (`platform-mcp/src/server.ts`) registers 40 tools with the
MCP protocol layer. The portal dispatcher (`platform/src/lib/mcp/primitives_registry.ts`) maintains
an independent `MCP_TO_RETRIEVAL_TOOL` map of whitelisted surgical tools. These two lists are
manually synchronized. The DAR workstream identified the first concrete drift event (FIX-1):
a tool added in `primitives_registry.ts` was not registered in `server.ts`, causing 404s from
the MCP client.

**Proposed target: Option B — Validated (CI assertion)**

```
Option A — Generated:
  primitives_registry.ts is auto-generated from server.ts at build time.
  A CI step runs `node scripts/generate_primitives_registry.mjs` and fails
  if the committed file differs from the generated output.
  Pros: No manual maintenance.
  Cons: Build step must run in the correct order; generated file must be
        committed (adds churn to PRs); toolchain change.

Option B — Validated (RECOMMENDED):
  A CI test asserts that every tool name in server.ts appears in
  MCP_TO_RETRIEVAL_TOOL and vice versa. No generation, no committed artifact.
  Pros: Zero build complexity; test-only change; works with existing vitest suite.
  Cons: Manual maintenance still required; drift is caught at CI time, not at
        authorship time.
```

**Recommendation: Option B** with the following vitest test in
`platform-mcp/src/__tests__/registry_parity.test.ts`:

```typescript
import { MCP_TO_RETRIEVAL_TOOL } from '@platform/lib/mcp/primitives_registry'
import { REGISTERED_MCP_TOOLS } from '../tools/index'   // exported from server.ts tool registry

test('primitives_registry entries match server.ts registrations', () => {
  const registryTools = new Set(Object.keys(MCP_TO_RETRIEVAL_TOOL))
  const serverTools = new Set(REGISTERED_MCP_TOOLS.map(t => t.name))

  const inRegistryNotServer = [...registryTools].filter(t => !serverTools.has(t))
  const inServerNotRegistry = [...serverTools].filter(t => !registryTools.has(t))

  expect(inRegistryNotServer).toEqual([])  // Every whitelisted tool must be registered
  expect(inServerNotRegistry).toEqual([])  // Every registered tool must be whitelisted
})
```

This test runs in the existing vitest suite (no new toolchain) and fails at PR CI time before
any drift reaches production. The test also serves as living documentation of the expected
registry state.

**Operator action required to enable**: Export `REGISTERED_MCP_TOOLS` from `server.ts` (or a
dedicated `tools/index.ts` registry file) as an array of tool names. This requires a single
edit to `platform-mcp/src/server.ts` to export the registration list.

---

### §3.4 — Logging Discipline

**Current state**: SRP-A-1 found two logging discipline failures affecting correctness and
observability:

1. **D.1 — params_json asymmetry**: Error paths log `params_json: (params ?? null)` (raw
   caller-supplied input) while success paths log `params_json: bundle.invocation_params`
   (assembled execution record). Affects 8 retrieval tools. This is defensible but undocumented.

2. **D.2 — System prompt in invocation_params**: `query_dasha_periods.ts:405` logs
   `invocation_params: { ...input, system, limit: actualLimit }`, embedding a 2,000–5,000
   token system prompt into `query_trace_steps.params_json`. This bloats the DB column
   unnecessarily.

**Target state — Two-rule logging discipline** (enforceable via PR checklist):

```
Rule L.1 — params_json on success path:
  Log only user-supplied filter parameters and computed limit values.
  Do NOT log system prompts, internal state objects, or configuration strings.
  Correct pattern:
    params_json: { filter_a, filter_b, limit: actualLimit }
  Incorrect pattern (D.2 failure):
    params_json: { ...input, system, limit: actualLimit }  // system is too large

Rule L.2 — params_json on error path:
  Log the raw caller-supplied params as a debugging aid.
  Document in the writeToolExecutionLog() JSDoc that error-path params_json
  records attempted input (not executed invocation_params).
  This asymmetry is intentional and correct — but must be documented.
```

**Enforcement mechanism**: Add to the PR description template for any change to
`platform/src/lib/retrieve/`:

```markdown
## Retrieval Tool Checklist
- [ ] `params_json` on success path logs only filter params + limit (no system prompts)
- [ ] `params_json` on error path logs raw caller params (intentional asymmetry — see L.2)
- [ ] No system prompt strings or config objects embedded in `invocation_params`
```

An ESLint custom rule can enforce Rule L.1 mechanically: flag any `params_json` assignment
that references a variable named `system`, `systemPrompt`, or `config`. The rule would be in
`platform/.eslintrc.js` targeting `platform/src/lib/retrieve/**.ts` only.

**ESLint rule outline**:
```javascript
// .eslint/rules/no-system-in-params-json.js
module.exports = {
  create(context) {
    return {
      Property(node) {
        if (node.key.name === 'params_json' &&
            node.value.type === 'ObjectExpression') {
          node.value.properties.forEach(prop => {
            if (['system', 'systemPrompt', 'config'].includes(prop.key?.name)) {
              context.report({ node: prop,
                message: 'Do not log system prompts in params_json (Rule L.1)' })
            }
          })
        }
      }
    }
  }
}
```

---

### §3.5 — Test Coverage Targets

**Target: ≥ 80% branch coverage** on all retrieval tools in `platform/src/lib/retrieve/`.

**Current baseline** (pre-SRP-T-1): SRP-A-1 found 25 of 53 retrieval tool files have no test
file at all. The 29 tested files have branch coverage ranging from ~30% to ~75%, estimated
overall at approximately **45–50% line coverage** and **20–30% branch coverage**.

**Path to 80%**:

The 80% branch coverage target requires two parallel workstreams:

**Workstream 1 — New test files** (SRP-T-1/T-2 scope):

Priority order (from SRP-A-1 finding E.1, highest-risk first):
1. `get_shadbala_full.ts` — complex SQL, CRITICAL (no test)
2. `muhurta_finder.ts` — complex multi-step, HIGH (no test)
3. `query_planetary_period_predictions.ts` — HIGH (no test)
4. `query_planet_war.ts` — HIGH (no test)
5. `query_jaimini_chara_dasha.ts` — HIGH (no test)
6. `query_ucn_walk.ts` — HIGH (no test)
7. `query_rm_walk.ts` — HIGH (no test)
8. `chandra_balam_for_native.ts` — HIGH (no test)
9. `tara_balam_for_native.ts` — HIGH (no test)
10. `classical_text_search_tool.ts` — HIGH (no test)

Remaining 15 medium/low priority tools (see SRP-A-1 §E.1 full list).

**Workstream 2 — Filter branch coverage** (SRP-T-1/T-2 scope):

SRP-A-1 found three existing test files with zero filter-branch coverage:
- `msr_sql.ts` — add test for `valence` filter path (primary C.1 finding)
- `lel_query.ts` — add test for date-range filter path
- `query_ephemeris.ts` — add test for planet filter path

**Estimated sessions to reach 80%**:

| Workstream | Files | Estimated Sessions |
|------------|-------|-------------------|
| High-priority new tests (tools 1–10) | 10 files | 3 sessions (3–4 tools/session) |
| Medium-priority new tests (tools 11–25) | 15 files | 4 sessions |
| Filter branch coverage additions | 3 files | 1 session (SRP-T-1) |
| **Total** | **28 files** | **~8 sessions** |

SRP-T-1 targets tools 1–4 + filter coverage additions (first 2 sessions). The remaining
sessions can be batched 3–4 tools each in subsequent SRP-T-N passes.

---

## §4 — Implementation Roadmap

### Overview

| Phase | Scope | Prereq | Est. Effort | Earliest Date |
|-------|-------|--------|-------------|---------------|
| **Phase R.1** | Immediate correctness fixes (DEL-007, DEL-010, DEL-013, DEL-015) | None (or SRP-F-1) | 1 session | 2026-05-26 |
| **Phase R.2** | Shared vocabulary layer (DEL-015 V.2+V.3, DEL-016) | Phase R.1 complete | 2 sessions | 2026-05-28 |
| **Phase R.3** | primitives_registry CI parity test | None | 1 session | 2026-05-27 |
| **Phase R.4** | Classic orchestrator sunset — flag removal + route.ts cleanup (DEL-001 to DEL-003, DEL-008, DEL-009, DEL-011, DEL-012) | R11V2 stable 30 days | 1 session | 2026-06-25 |
| **Phase R.5** | Coverage push to 80% — new test files | SRP-T-1/T-2 merged | 5–6 sessions | 2026-06-01 |
| **Phase R.6** | Synthesis trio deletion (DEL-004, DEL-005, DEL-006) | mcp/execute migration | 1 session | 2026-08-01 |

---

### Phase R.1 — Immediate Correctness Fixes

**Scope**: Non-gated, zero-risk items that should ship as soon as SRP-F-1 is deployed.

| Item | Action | LoC | Notes |
|------|--------|-----|-------|
| DEL-007 | Remove `PRIMARY_TOOL_NAMES` | ~15 | Zero call sites confirmed |
| DEL-010 | Inline `CONSUME_UI_V2_ENABLED=true` in consume pages | ~11 | CRITICAL — likely broken false branch |
| DEL-013 | Remove 4 orphaned R8 flag declarations | ~20 | After grep confirms zero call sites |
| DEL-015 V.1 | Create `shared_enums.ts` + fix `query_signals.ts:181` valence mismatch | ~20 net | P0 correctness bug |

**Prereq**: SRP-F-1 deployed to production (for context/confirmation only; these changes are
independent of SRP-F-1 implementation). No 30-day gate required.

**Effort**: 1 session. One PR (`srp/r1-immediate-fixes`) touching `feature_flags.ts`,
two `consume/` page files, `manifest_compressor.ts`, and the new `shared_enums.ts`.

**Acceptance criteria**:
- `grep -rn 'PRIMARY_TOOL_NAMES' platform/src/` returns zero results
- `grep -rn 'CONSUME_UI_V2_ENABLED' platform/src/` returns zero results
- `grep -rn "'positive'.*valence\|valence.*'positive'" platform-mcp/src/` returns zero results
- All vitest tests pass

---

### Phase R.2 — Shared Vocabulary Layer

**Scope**: Complete the vocabulary consolidation started in R.1; add `SignificanceTier` and
`QueryDomain` enums; consolidate `QueryPlan` parallel definitions.

| Item | Action | LoC |
|------|--------|-----|
| DEL-015 V.2 | Add `SignificanceTierEnum`; wire to filter validation in retrieval tools | ~20 |
| DEL-015 V.3 | Add `QueryDomainEnum`; replace `string` domain fields in `router/types.ts` | ~30 |
| DEL-016 | Consolidate `QueryPlan` to `Pick<>` in retrieve + bundle + trace types | ~80–100 refactor |

**Prereq**: Phase R.1 complete (shared_enums.ts exists as the import target).

**Effort**: 2 sessions. Session 1: DEL-015 V.2 + V.3. Session 2: DEL-016 + full type-check
pass to confirm no import regressions.

**Acceptance criteria**:
- `tsc --noEmit` exits 0 across `platform/` and `platform-mcp/`
- No `string`-typed `valence`, `significance_tier`, or `domain` parameters in retrieval tool
  Zod schemas
- `QueryPlan` defined in exactly one file (`router/types.ts`)

---

### Phase R.3 — primitives_registry CI Parity Test

**Scope**: Add the vitest parity test described in §3.3; export `REGISTERED_MCP_TOOLS` from
`platform-mcp/src/tools/index.ts`.

**Prereq**: None — this is additive and independent of all other phases.

**Effort**: 1 session. One PR: add export from `tools/index.ts`, add
`registry_parity.test.ts`, confirm vitest passes.

**Acceptance criteria**:
- New test `registry_parity.test.ts` passes in CI
- Adding a tool to `server.ts` without updating `primitives_registry.ts` causes the test to fail
  (verified by a temporary local mutation)
- Adding a tool to `primitives_registry.ts` without updating `server.ts` causes the test to fail

---

### Phase R.4 — Classic Orchestrator Sunset

**Scope**: Remove the `USE_ADAPTERS` flag gate, inline the adapter path as the only path,
delete the legacy orchestrator dead code from `route.ts` and `feature_flags.ts`. Also promote
R11D_ANTHROPIC_CACHE and R11D_PROMPT_LAYOUT to always-on.

**Prereq**: **30-day production stability gate** — `R11V2_USE_ADAPTERS=true` must have been
stable in production for 30 days with zero adapter-path incidents. Earliest date: **2026-06-24**
(30 days from SRP-F-1 targeted deploy of 2026-05-25). The 14-day post-flag-removal observation
(Checkpoint 2) must also pass before the route.ts dead code is deleted.

| Item | Action | LoC |
|------|--------|-----|
| DEL-001 | Remove legacy orchestrator path from route.ts | ~400 |
| DEL-002 | Remove synthesisRequest construction block | ~50 |
| DEL-003 | Remove createOrchestrator import from route.ts | ~1 |
| DEL-008 | Remove deprecated resolver.ts function | ~25 |
| DEL-009 | Remove legacy trace assembler/client functions | ~50 |
| DEL-011 | Remove R11D_ANTHROPIC_CACHE flag + deploy.yml entry | ~20 |
| DEL-012 | Remove R11D_PROMPT_LAYOUT flag + deploy.yml entry | ~15 |

**Effort**: 1 session (all items are in the same PR; the flag gate removal and route.ts
cleanup are intrinsically linked). Operator must run the Cloud Run `--remove-env-vars` commands
as a post-merge step.

**Acceptance criteria**:
- `grep -rn 'createOrchestrator\|orchestrator\.synthesize\|USE_ADAPTERS\|R11D_ANTHROPIC_CACHE\|R11D_PROMPT_LAYOUT' platform/src/` returns zero results
- `tsc --noEmit` exits 0
- All vitest tests pass
- Cloud Run: `gcloud run services describe amjis-web` shows none of the removed env-vars

---

### Phase R.5 — Coverage Push to 80%

**Scope**: Write unit tests for the 25 untested retrieval tools (priority order per E.1)
and add filter-branch coverage to the three undertested existing tools.

**Prereq**: SRP-T-1 and SRP-T-2 merged (which cover the first ~6 tools). Phases R.5.2–R.5.5
can run in parallel as independent PRs once the test infrastructure is established.

**Effort**: 5–6 sessions total (batching 3–4 tools per session). Recommended session breakdown:

| Session | Tools | Priority |
|---------|-------|---------|
| SRP-T-1 | `get_shadbala_full`, `muhurta_finder` + filter coverage for msr_sql/lel_query/query_ephemeris | CRITICAL/HIGH |
| SRP-T-2 | `query_planetary_period_predictions`, `query_planet_war`, `query_jaimini_chara_dasha` | HIGH |
| R.5.1 | `query_ucn_walk`, `query_rm_walk`, `chandra_balam_for_native`, `tara_balam_for_native` | HIGH |
| R.5.2 | `classical_text_search_tool`, `get_planet_avastha`, `query_cdlm_lookup`, `query_dasamsha_career` | HIGH/MEDIUM |
| R.5.3 | `query_transits_over_natal`, `query_yogas_active_now`, `query_shashtiamsha`, `query_drekkana_drishti` | MEDIUM/HIGH |
| R.5.4 | Remaining 9 medium/low priority tools | MEDIUM/LOW |

**Acceptance criteria**:
- `vitest run --coverage platform/src/lib/retrieve/` shows ≥ 80% branch coverage
- No new test failures introduced

---

### Phase R.6 — Synthesis Trio Deletion

**Scope**: Delete `orchestrator.ts`, `single_model_strategy.ts` (886 LoC), and
`panel_strategy.ts` (248 LoC) after `mcp/execute/route.ts` migrates to adapter dispatch.

**Prereq**: DEL-004 requires `mcp/execute/route.ts` to be migrated to adapter dispatch. This
is a separate workstream (tentative: R11.H or equivalent arc). The synthesis trio cannot be
deleted until `createOrchestrator` has zero call sites outside test files.

**Effort**: 1 session (deletion PR, vitest confirmation, CI pass). The effort is low but the
prereq is a significant engineering workstream.

**Earliest date**: ~2026-08-01, assuming the mcp/execute migration starts 2026-07-15 and
completes within 2 weeks.

**Acceptance criteria**:
- Files `orchestrator.ts`, `single_model_strategy.ts`, `panel_strategy.ts` do not exist in
  `platform/src/lib/synthesis/`
- `grep -rn 'createOrchestrator\|SingleModelStrategy\|PanelStrategy' platform/src/` returns
  zero results outside test files
- `tsc --noEmit` exits 0
- All vitest tests pass

---

### Roadmap Summary Timeline

```
2026-05-25:  SRP-F-1 deployed → start 30-day stability clock
2026-05-26:  Phase R.1 — Immediate fixes (CONSUME_UI_V2, PRIMARY_TOOL_NAMES, valence fix)
2026-05-27:  Phase R.3 — Registry CI parity test
2026-05-28:  Phase R.2 begins — Shared vocabulary layer (2 sessions)
2026-06-01:  Phase R.5 begins — SRP-T-1 (first test session)
2026-06-24:  CHECKPOINT 1 — 30-day stability gate evaluation
2026-06-25:  Phase R.4a — Flag removal PR (if gate passes)
2026-07-09:  CHECKPOINT 2 — 14-day post-flag observation
2026-07-10:  Phase R.4b — route.ts dead code deletion PR
2026-07-15:  mcp/execute migration begins (separate workstream)
2026-08-01:  Phase R.6 — Synthesis trio deletion (if mcp/execute migration complete)
```

---

## Appendix A — Retrieval Tool Test Priority List (for SRP-T-1/T-2)

Per SRP-A-1 §E.1, the 25 untested retrieval tools ranked by priority:

| Rank | Tool File | Complexity | Priority |
|------|-----------|------------|---------|
| 1 | `get_shadbala_full.ts` | High (complex SQL) | CRITICAL |
| 2 | `muhurta_finder.ts` | High | HIGH |
| 3 | `query_planetary_period_predictions.ts` | High | HIGH |
| 4 | `query_planet_war.ts` | High | HIGH |
| 5 | `query_jaimini_chara_dasha.ts` | High | HIGH |
| 6 | `query_ucn_walk.ts` | Medium | HIGH |
| 7 | `query_rm_walk.ts` | Medium | HIGH |
| 8 | `chandra_balam_for_native.ts` | Medium | HIGH |
| 9 | `tara_balam_for_native.ts` | Medium | HIGH |
| 10 | `classical_text_search_tool.ts` | Medium | HIGH |
| 11 | `get_planet_avastha.ts` | Medium | HIGH |
| 12 | `query_cdlm_lookup.ts` | Medium | HIGH |
| 13 | `query_dasamsha_career.ts` | Medium | HIGH |
| 14 | `query_transits_over_natal.ts` | Medium | HIGH |
| 15 | `query_yogas_active_now.ts` | Medium | HIGH |
| 16 | `query_shashtiamsha.ts` | High | HIGH |
| 17 | `classical_attribution_lookup_tool.ts` | Medium | HIGH |
| 18 | `query_drekkana_drishti.ts` | Medium | MEDIUM |
| 19 | `query_eclipse_transits.ts` | Medium | MEDIUM |
| 20 | `query_jaimini_drishti.ts` | Medium | MEDIUM |
| 21 | `query_muhurat.ts` | Medium | MEDIUM |
| 22 | `query_remedies_prescribed.ts` | Medium | MEDIUM |
| 23 | `classical_disclosure_filter.ts` | Low | MEDIUM |
| 24 | `query_v7_additions.ts` | Low | MEDIUM |
| 25 | `tool_catalogue.ts` | Low | LOW |

---

## Appendix B — Cloud Run Operator Checklist

For each flag removal in Phase R.1 and R.4, the operator must run the corresponding `gcloud`
command AFTER the code PR is deployed:

| PR | Flag | Command |
|----|------|---------|
| Phase R.1 | `CONSUME_UI_V2_ENABLED` | `gcloud run services update amjis-web --region asia-south1 --remove-env-vars CONSUME_UI_V2_ENABLED` |
| Phase R.4 | `MARSYS_FLAG_R11V2_USE_ADAPTERS` | `gcloud run services update amjis-web --region asia-south1 --remove-env-vars MARSYS_FLAG_R11V2_USE_ADAPTERS` |
| Phase R.4 | `MARSYS_FLAG_R11D_ANTHROPIC_CACHE` | `gcloud run services update amjis-web --region asia-south1 --remove-env-vars MARSYS_FLAG_R11D_ANTHROPIC_CACHE` |
| Phase R.4 | `MARSYS_FLAG_R11D_PROMPT_LAYOUT` | `gcloud run services update amjis-web --region asia-south1 --remove-env-vars MARSYS_FLAG_R11D_PROMPT_LAYOUT` |
| AIOps cleanup | `ADAPTERS_ENABLED` (stale rename) | `gcloud run services update amjis-web --region asia-south1 --remove-env-vars ADAPTERS_ENABLED` |

All `gcloud` commands assume `--region asia-south1`. Verify the target service name and region
before executing. Each removal should be followed by a 5-minute log watch to confirm no
runtime errors.

---

*End of TARGET_ARCHITECTURE_REPORT v1.0*
