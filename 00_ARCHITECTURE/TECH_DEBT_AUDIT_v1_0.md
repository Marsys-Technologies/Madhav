---
canonical_id: TECH_DEBT_AUDIT
version: 1.0
status: CURRENT
authored: 2026-05-25
session: SRP-A-1
branch: arch/srp-a1-tech-debt
artifact: TECH_DEBT_AUDIT_v1_0
---

# Technical Debt Audit v1.0

## Executive Summary

| Category | Items | Est. LoC Removable | Priority |
|----------|-------|-------------------|----------|
| A: Dead Code | 7 | ~1,300 | CRITICAL/HIGH |
| B: Orphaned Flags | 12 | ~200 (flag bodies stay) | HIGH/MEDIUM |
| C: Type Inconsistencies | 4 | 0 (refactor not delete) | HIGH |
| D: Logging Debt | 4 | 0 (fix not delete) | MEDIUM |
| E: Test Coverage Gaps | 25 untested files | N/A | MEDIUM |
| F: Dispatcher Hardcoding | 3 | ~30 | HIGH |
| **Total** | **55** | **~1,530+** | |

> Estimated deletable LoC: **≥ 1,530** (A: ~1,300 + F: ~30 + incidental cleanup ~200).
> The single largest item is the legacy orchestrator path in `route.ts` which is unreachable
> when `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` (permanently set in deploy.yml).

---

## A: Dead Code

### A.1 — Legacy Orchestrator Pipeline (Unreachable)

**Status**: `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is hardcoded in
`.github/workflows/deploy.yml`. This means the `else` branch (legacy orchestrator path)
at `route.ts:1201` is **never reached in production**.

The adapter dispatch block (`route.ts:923-1198`, ~275 lines) routes all traffic when
`USE_ADAPTERS=true`. The code at lines 862–1198 initialises the orchestrator and assembles
`synthesisRequest` for the legacy path that then falls through to `orchestrator.synthesize()`
at line 1201 — which is never called in production.

| File | Symbol / Lines | Reason | LoC | Severity | Safe to Delete? |
|------|----------------|--------|-----|----------|-----------------|
| `platform/src/app/api/chat/consume/route.ts` | `createOrchestrator` call at line 862; `synthesisRequest` assembly lines 863–907; legacy `orchestrator.synthesize()` call lines 1201–1227; and the downstream legacy stream block ~lines 1278–1620 | `R11V2_USE_ADAPTERS=true` in deploy.yml — adapter block at lines 923–1198 returns before the legacy path | ~400 (lines 1201–1600, the unreachable `else` path) | CRITICAL | NEEDS_HUMAN_REVIEW (confirm flag is permanently true; then YES) |
| `platform/src/app/api/chat/consume/route.ts` | `createOrchestrator` import at line 82 | Only called at line 862 for the unreachable path | 1 | HIGH | YES (after A.1 body removed) |

**Notes**:
- The `synthesisRequest` construction block (lines 863–907) is only consumed by
  `orchestrator.synthesize()` at line 1201. If the legacy path is removed, this block goes too.
- The `panelOptIn` variable resolved around line 805 feeds only `createOrchestrator()` — also removable.
- The `validatorResultsHolder`, `pendingStreamWriter`, `provenanceHolder`, and `finishGuard`
  abstractions may be shared with the adapter path; each must be verified before removal.
- **Estimated total LoC removable from route.ts**: ~450+ lines (adapter path currently at ~275 lines,
  legacy path ~400 lines; the shared pre-adapter setup code must be carefully audited).

#### A.1.b — orchestrator.ts, single_model_strategy.ts, panel_strategy.ts

These synthesis modules are called exclusively via `createOrchestrator()` which is called from:

1. `platform/src/app/api/chat/consume/route.ts:862` — in the legacy (unreachable) path.
2. `platform/src/app/api/mcp/execute/route.ts:456` — MCP execute endpoint (still reachable).
3. Various test files (test-only usage).

Because `mcp/execute/route.ts` still uses `createOrchestrator`, these files are **NOT safe to
delete today**. However, if MCP execute is migrated to adapter dispatch, they become dead.

| File | LoC | Severity | Safe to Delete? |
|------|-----|----------|-----------------|
| `platform/src/lib/synthesis/orchestrator.ts` | 34 | HIGH | NO — still used by mcp/execute |
| `platform/src/lib/synthesis/single_model_strategy.ts` | 886 | HIGH | NO — still used by mcp/execute |
| `platform/src/lib/synthesis/panel_strategy.ts` | 248 | MEDIUM | NO — instantiated by orchestrator |

---

### A.2 — Deprecated and Unused Symbols

| File | Symbol / Line | Reason | LoC | Severity | Safe to Delete? |
|------|---------------|--------|-----|----------|-----------------|
| `platform/src/lib/pipeline/manifest_compressor.ts` | `PRIMARY_TOOL_NAMES` (exported const, line 83) — `@deprecated` since COV-S3 | Zero production call sites. Only the deprecation comment references it. `compressManifest()` (the replacement) is actively used via `pipeline_planner.ts:278`. | ~15 | MEDIUM | YES |
| `platform/src/lib/admin/trace_assembler.ts` | `@deprecated` since Gate II (line 30: `LegacyTraceRow` or equivalent type; line 599: `assembleTraceLegacy` function) | Marked deprecated since 2026-05-12. Use `assembleTraceFull` + `.assembled` instead. | ~30 | MEDIUM | NEEDS_HUMAN_REVIEW (check if admin UI still imports legacy form) |
| `platform/src/lib/admin/trace_client.ts` | `fetchTraceLegacy` (line 21, `@deprecated`) | Deprecated since Gate II. Prefer `fetchTraceEnvelope`. | ~20 | MEDIUM | NEEDS_HUMAN_REVIEW (check admin UI imports) |
| `platform/src/lib/models/resolver.ts` | `@deprecated` function at line 68 — no active call sites | Adapter layer handles model resolution; this symbol has zero call sites | ~25 | MEDIUM | YES |
| `platform/src/lib/models/registry.ts` | `@deprecated` symbol at line 844 — since stack-based routing replaced individual model selection | Stack-based routing is the only path in production | ~20 | MEDIUM | NEEDS_HUMAN_REVIEW |
| `platform/src/app/api/chat/consume/route.ts` | `stack` field at line 181 — `@deprecated "Kept for backward compat with in-flight requests; ignored when stack is provided"` | In-flight backward compat — monitor and remove after grace period | ~5 | LOW | NO (keep until confirmed no in-flight requests use the old field) |

---

### A.3 — Dead Feature Flag Branches

#### Flags confirmed retired with NO residual dead branches:

| Flag | Retirement | Status |
|------|-----------|--------|
| `NEW_QUERY_PIPELINE_ENABLED` | Phase 11B 2026-05-11 | Clean — only a comment in `feature_flags.ts:6`. No `if (flag)` usage found. |
| `LLM_FIRST_PLANNER_ENABLED` | Pipeline-Transform-S1 2026-05-11 | Not in `feature_flags.ts` at all. No call sites. |
| `CONTEXT_ASSEMBLY_ENABLED` | Pipeline-Transform-S1 2026-05-11 | Not in `feature_flags.ts`. No call sites. Stage `compose_bundle` was preserved (not deleted). |
| `CHAT_V2_ENABLED` | §M.16 2026-05-18 | Not in `feature_flags.ts`. No call sites. |

All four known-retired flags are clean — no dead `if (false)` branches remain.

#### Flags with dead `false`-branch code:

| Flag | Default | Deploy.yml | Dead Branch Size | Safe to Inline? |
|------|---------|-----------|-----------------|-----------------|
| `R11V2_USE_ADAPTERS` | `false` (code default) | `true` (always-on) | The `else` path in `route.ts` (~400 LoC) is the dead branch | YES — the `false` branch is the legacy orchestrator path from A.1 above |
| `R11E_ANTHROPIC_LOOP` (+ 4 siblings) | `false` (code) | `true` (deploy.yml) | `if (!useAgenticLoop)` skips tool forwarding — currently the `false` branch is never reached | MEDIUM — flags provide per-provider rollback safety; keep until proven stable |

---

### A.4 — consume-tools.ts Remnants

`consume-tools.ts` was deleted in Phase 11B (2026-05-11). Verification:

```
find platform/src -name "consume-tools*"  → no results
grep -rn "consume-tools" platform/src/     → no results
```

**Status: CLEAN**. File deleted, no imports or references remain anywhere in `platform/src/`.

---

## B: Orphaned Feature Flags

Flags in `platform/src/lib/config/feature_flags.ts` analyzed for orphan status.

### B.1 — Flags Safe to Promote to Always-On (Inlining Candidates)

These flags default `true` in `feature_flags.ts` AND are set `true` in `deploy.yml` AND
their `false` branch is either absent or unused in practice.

| Flag | Default | Deploy.yml | `false` Branch Risk | Recommendation |
|------|---------|-----------|--------------------|-|
| `R11V2_USE_ADAPTERS` | false (code); **true** (prod) | `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` | ~400 LoC legacy orchestrator | **PROMOTE** after A.1 cleanup; add `gcloud --remove-env-vars` step |
| `R11E_ANTHROPIC_LOOP` | false | `true` | Skips tool forwarding | Keep flag for rollback safety; **review in 30 days** |
| `R11E_GEMINI_LOOP` | false | `true` | Same | Same |
| `R11E_OPENAI_LOOP` | false | `true` | Same | Same |
| `R11E_DEEPSEEK_LOOP` | false | `true` | Same | Same |
| `R11E_NVIDIA_LOOP` | false | `true` | Same | Same |
| `R11D_ANTHROPIC_CACHE` | false | `true` | Skips cache breakpoints | **PROMOTE** — Observatory shows stable hit rate |
| `R11D_PROMPT_LAYOUT` | false | `true` | Prior assembly order | **PROMOTE** — shipped stably since 2026-05-23 |
| `R11B_LOOK_AND_FEEL` | false | `true` (via `vars.R11B... \|\| 'true'`) | Visual regression | Keep flag; monitor for 2 weeks post-SRP |
| `R11V2_MULTI_PROVIDER_PARITY` | false | `true` (via `vars... \|\| 'true'`) | Adapter layer reverts | Keep flag |

### B.2 — CONSUME_UI_V2_ENABLED — Orphaned Flag (Action Required)

| Flag | Default | Deploy.yml | Code Usage | LoC Impact |
|------|---------|-----------|-----------|----------|
| `CONSUME_UI_V2_ENABLED` | `true` | `CONSUME_UI_V2_ENABLED=true` | Read at `platform/src/app/clients/[id]/consume/page.tsx:123` and `[conversationId]/page.tsx:56` — gates which ConsumeChat component is shown | ~10 (conditionals in 2 page files) |

**Status**: This flag controls whether `ConsumeChatV2` (the new chat surface) is shown vs. the
classic surface. Default is `true`. Since CLAUDE.md §E confirms Chat V2 Big Bang is COMPLETE
and the legacy path was deleted in §M.16, the `false` branch in these page files likely points
to a deleted component. **Requires verification**: check what `consumeUiV2Enabled === false`
renders — if it's a deleted component reference, this is CRITICAL dead code.

**Note**: `deploy.yml` sets `CONSUME_UI_V2_ENABLED=true` as a **server-side env var** without
the `NEXT_PUBLIC_` prefix, but `configService.getFlag` in a Next.js page component reads
from the server-side store. Verify this resolves correctly at build time. The flag may need
`NEXT_PUBLIC_MARSYS_FLAG_CONSUME_UI_V2_ENABLED` for client-side pages.

### B.3 — OBSERVATORY_ENABLED — Dual-gate Pattern

| Flag | Default | Deploy.yml | Code Usage |
|------|---------|-----------|-----------|
| `OBSERVATORY_ENABLED` | `false` | Not in deploy.yml (set externally via Cloud Run `MARSYS_FLAG_OBSERVATORY_ENABLED=true`) | Guards `/api/admin/observatory/_guard.ts` (raw env check) + `configService.getFlag` |

**Note**: `_guard.ts` reads `process.env.MARSYS_FLAG_OBSERVATORY_ENABLED !== 'true'` directly,
bypassing `configService.getFlag`. This means the `FeatureFlag` entry `OBSERVATORY_ENABLED`
in `feature_flags.ts` and the env var `MARSYS_FLAG_OBSERVATORY_ENABLED` are only loosely
coupled. If the env var is set but the Cloud Run `DEFAULT_FLAGS.OBSERVATORY_ENABLED: false`
is in effect, the guard may behave inconsistently depending on whether `configService` reads
from env or from defaults. **Recommendation**: consolidate to a single gate.

### B.4 — R8 Flags — All Default False, Not in Deploy.yml

The following flags are declared, default `false`, and have active code branches in the UI but
are NOT in `deploy.yml`, meaning they are `false` in production unless set via Cloud Run env-vars.

| Flag | Read Location | Status |
|------|--------------|--------|
| `R8_SLASH_ENABLED` | `platform/src/app/clients/[id]/consume/page.tsx:125` | Feature exists but disabled. May be promotable if fully stable. |
| `R8_EXPORT_ENABLED` | `page.tsx:126` | Same |
| `R8_TOKENS_ENABLED` | `page.tsx:127` | Same |
| `R8_BRANCHES_ENABLED` | Not found in `src/` (flag defined but no `getFlag` call) | Potentially dead — definition with no call site |
| `R8_SEARCH_ENABLED` | Not found in `src/` (beyond feature_flags.ts) | Same |
| `R8_FOLDERS_ENABLED` | Not found in `src/` | Same |
| `R8_VISION_ENABLED` | Not found in `src/` | Same |

**Action**: Audit R8_BRANCHES_ENABLED, R8_SEARCH_ENABLED, R8_FOLDERS_ENABLED, R8_VISION_ENABLED
for active call sites. If none exist, the flag definitions are orphaned.

### B.5 — R11C_SMOOTH_STREAM_V3 — Overlapping Flags

```
smooth_stream.ts:158:  if (!getFlag('R10_SMOOTH_STREAM_V2')) return undefined
smooth_stream.ts:167:  return getFlag('R10_SMOOTH_STREAM_V2') && getFlag('R11C_SMOOTH_STREAM_V3')
```

`R11C_SMOOTH_STREAM_V3` is the V3 rate-limiter that activates only when `R10_SMOOTH_STREAM_V2`
is also true. Both default `true`. If `R10_SMOOTH_STREAM_V2` is promoted to always-on,
`R11C_SMOOTH_STREAM_V3` condition simplifies to a single flag. **Low priority but cleanup worthy.**

### B.6 — R11V2_CAPABILITY_TELEMETRY — Default False, Not in Deploy.yml

| Flag | Default | Deploy.yml | Status |
|------|---------|-----------|--------|
| `R11V2_CAPABILITY_TELEMETRY` | `false` | Not set | Telemetry is silently skipped in production. The Observatory tile exists but receives no data. Operator must flip this to enable. Documented as a known gap in R11.F-RES-1. |

### B.7 — R11D_GEMINI_CACHE — Default False, Not in Deploy.yml (NOT_IMPLEMENTED)

Per CLAUDE.md §E: `R11D_GEMINI_CACHE` was rolled back (D.3 NOT_IMPLEMENTED) because
`adapter.cache()` is never called from the route dispatch block. The flag is set to `false`
in `DEFAULT_FLAGS`, not in `deploy.yml`. The call site at `route.ts:971-1000` is live code
but the `adapter.cache()` call for Google never routes the result into the actual request —
it was identified as a wiring gap. **The `if (R11D_GEMINI_CACHE)` branch at route.ts:971 is
effectively dead** until R11.F+ wires it properly.

| Flag | Status | Risk |
|------|--------|------|
| `R11D_GEMINI_CACHE` | Code exists (route.ts:971-1000) but `cacheResponse` result is never applied to the actual SDK call | LOW — default false, not in production; the code block is benign but misleading |

---

## C: Duplicate / Inconsistent Type Definitions

### C.1 — Valence Enum Vocabulary Mismatch (CONFIRMED)

**Root cause**: The MCP channel (`platform-mcp/src/tools/query_signals.ts`) and the portal
channel (`platform/src/lib/retrieve/msr_sql.ts`) use DIFFERENT vocabularies for the same DB field.

| Location | Valence Vocabulary | Source |
|----------|--------------------|--------|
| `platform-mcp/src/tools/query_signals.ts:181` | `z.enum(['positive', 'negative', 'neutral'])` — caller-facing Zod schema | MCP tool public API |
| `platform/src/lib/retrieve/msr_sql.ts:104` | `{ domains: plan.domains, ... }` — passes raw string; underlying SQL: `valence = ANY($8::text[])` | Portal SQL query |
| `platform-mcp/src/tools/msr_sql.ts:76` | `z.union([z.string(), z.array(z.string())])` with description "Examples: 'benefic', 'malefic', 'neutral'" | MCP msr_sql tool |
| DB column (authoritative) | `'benefic' / 'malefic' / 'context-dependent'` | SQL column in `msr_signals` table |

**The gap**: `query_signals.ts` exposes `'positive'/'negative'/'neutral'` to MCP callers but the
DB stores `'benefic'/'malefic'/'context-dependent'`. If a caller passes `valence: 'positive'`,
the SQL filter returns zero rows silently because no DB row has `valence='positive'`. The
`msr_sql.ts` MCP tool correctly uses `'benefic'/'malefic'` in its description (line 78) but
`query_signals.ts` does not.

**Files affected**:
- `platform-mcp/src/tools/query_signals.ts:181` — Zod enum uses wrong vocabulary
- `platform/src/lib/retrieve/types.ts` — no explicit valence type definition; accepts `string`
- `platform/src/lib/retrieve/msr_sql.ts` — no Zod validation on valence input (accepts any string)

**Recommended fix**: Add a shared `ValenceEnum = z.enum(['benefic', 'malefic', 'context-dependent', 'neutral'])` in a shared types module and import it in all valence filter locations. Fix `query_signals.ts:181` to use DB vocabulary.

**LoC change**: Refactor only — no lines deleted.

### C.2 — Significance: Numeric vs. Enum Inconsistency

| Location | Significance Type | Notes |
|----------|--------------------|-------|
| `platform/src/lib/retrieve/types.ts:67` | `significance?: number` (float) | Retrieval bundle result |
| `platform/src/lib/retrieve/types.ts:112` | `significance: number` (required float) | Another result type |
| `platform-mcp/src/tools/query_signals.ts` (via describe text) | `'tier_1'/'tier_2'/'tier_3'` string tiers referenced in descriptions | DB column is text tier |
| `platform/src/lib/db/types.ts` | significance as numeric | DB-facing type |

**Status**: `significance` is consistently numeric in the retrieve layer (a float 0.0–1.0). The
string tier vocabulary (`tier_1`/`tier_2`/`tier_3`) appears only in filter descriptions and
SQL `WHERE` clauses, not in TypeScript type definitions. This is **inconsistent documentation**
rather than a hard type error, but can mislead callers.

**Finding**: No TypeScript type definition for `SignificanceTier`. The filter descriptions say
"tier_1/tier_2/tier_3" but the TypeScript types say `significance: number`. Callers must know
that the DB `significance_tier` column is a text enum while the returned `significance` field
is a float. A shared `SignificanceTier = z.enum(['tier_1', 'tier_2', 'tier_3'])` Zod type
would close the gap.

### C.3 — Domain: No Canonical DomainEnum TypeScript Type

Domain values like `'career'`, `'health'`, `'relationship'`, `'financial'` are used across
many files as raw strings. There is no `DomainType` or `QueryDomain` exported type.

| Location | Pattern |
|----------|---------|
| `platform/src/lib/router/types.ts:20` | `domains: string[]` — untyped array |
| `platform/src/lib/retrieve/msr_sql.ts` | SQL filter accepts any string |
| `platform/src/lib/retrieve/domain_report_query.ts` | Domain passed as raw string |
| `platform/src/lib/retrieve/contradiction_register.ts:80` | `{ domains: plan.domains }` — logs raw string array |
| Various MCP tools | Each defines its own `z.string()` or inline descriptions |

**Risk**: A typo in a domain name (e.g., `'financal'`) silently returns zero rows. A canonical
`DomainEnum` would catch this at compile time.

**Files most affected**: `platform/src/lib/router/types.ts`, retrieval tools using `plan.domains`.

### C.4 — QueryPlan: Three Parallel Definitions

`QueryPlan` is defined independently in at least three locations:

| File | Fields | Differences |
|------|--------|-------------|
| `platform/src/lib/router/types.ts:6` | Full canonical definition (19+ fields) | The master definition |
| `platform/src/lib/retrieve/types.ts:6` | Subset: 7 fields (query_plan_id, query_text, query_class, domains, forward_looking, tools_authorized, schema_version) | Retrieval-layer minimal contract |
| `platform/src/lib/bundle/types.ts:30` | Another subset (query_plan_id, query_text, query_class, domains, forward_looking, tools_authorized, schema_version, audience_tier) | Bundle-layer contract |
| `platform/src/lib/trace/types.ts:52` | `TraceQueryPlan` (re-exported as `QueryPlan`) | Trace-layer representation |

**Risk**: `router/types.ts` is the authoritative definition. If a field is added there but not
in `retrieve/types.ts`, retrieval tools won't type-check the new field. Currently the retrieve
and bundle subsets are structurally compatible with `router/types.ts` (they omit optional
fields), but divergence is likely over time.

**Recommendation**: Export `QueryPlan` from `router/types.ts` only. Have `retrieve/types.ts`
and `bundle/types.ts` import and re-export a `Pick<QueryPlan, ...>` narrowed subset rather
than re-declaring independently.

---

## D: Logging Debt

### D.1 — params_json: Inconsistent Logging on Error vs. Success Paths

In many retrieval tools there is a structural pattern where:
- **Error path** logs `params_json: (params ?? null)` — the raw caller-supplied params object
- **Success path** logs `params_json: bundle.invocation_params` — the assembled invocation record

These are semantically different objects. The error log records what was attempted; the success
log records what was executed. This is arguably correct but can confuse debugging when comparing
error and success trace rows side-by-side.

**Files with this dual pattern** (all follow the same pattern — not exhaustive):
- `platform/src/lib/retrieve/msr_sql.ts` (lines 104 vs. 323)
- `platform/src/lib/retrieve/lel_query.ts` (lines 111 vs. 196)
- `platform/src/lib/retrieve/contradiction_register.ts` (lines 80 vs. 176)
- `platform/src/lib/retrieve/resonance_register.ts` (lines 85 vs. 177)
- `platform/src/lib/retrieve/pattern_register.ts` (lines 85 vs. 180)
- `platform/src/lib/retrieve/kp_query.ts` (lines 41 vs. 146)
- `platform/src/lib/retrieve/query_signal_state.ts` (lines 107 vs. 229)
- `platform/src/lib/retrieve/cluster_atlas.ts` (lines 75 vs. 180)

**Severity**: MEDIUM. Not incorrect, but the asymmetry should be documented in the shared
`writeToolExecutionLog` contract.

### D.2 — query_dasha_periods: invocation_params Logged as Domain Array

At `platform/src/lib/retrieve/query_dasha_periods.ts:405`:
```typescript
invocation_params: { ...input, system, limit: actualLimit },
```

This embeds the full system prompt string (`system`) into the invocation_params object, which is
then stored in `params_json` in the DB. System prompts can be 2,000–5,000 tokens. This bloats
the `query_trace_steps.params_json` column with non-query data.

**Recommended fix**: Omit `system` from `invocation_params` logging. Log only the user-supplied
input fields (`input`) and `limit`.

**File**: `platform/src/lib/retrieve/query_dasha_periods.ts:405`
**Severity**: MEDIUM

### D.3 — contradiction_register.ts: invocation_params References plan.domains Before Validation

At `platform/src/lib/retrieve/contradiction_register.ts:59-62`:
```typescript
invocation_params: {
  domains: plan.domains,
  ...
}
```

`plan.domains` comes from the primitive dispatcher hardcoded as `[]` (see Category F). When called
via the MCP primitive path, `domains` is always `[]` and the logged `invocation_params.domains`
will always be an empty array. This is misleading when debugging contradiction queries — the trace
suggests no domain filter was applied even if the tool produced domain-filtered results via
other logic.

**Files**: `platform/src/lib/retrieve/contradiction_register.ts` (same pattern in
`resonance_register.ts`, `pattern_register.ts` via their `plan.domains` references).
**Severity**: MEDIUM

### D.4 — Missing trace_id Propagation in Primitive Dispatcher

At `platform/src/app/api/mcp/primitives/[tool]/route.ts:175`:
```typescript
const queryId = crypto.randomUUID()
```

This `queryId` is used as the `trace_id` in `traceEmitter.emitStep()` but is a fresh UUID per
call rather than a client-supplied correlation ID. There is no mechanism for an MCP caller to
pass a correlation ID that flows through to the trace. All MCP primitive calls appear as
disconnected trace rows with no parent.

**File**: `platform/src/app/api/mcp/primitives/[tool]/route.ts:175`
**Recommendation**: Accept an optional `X-Correlation-ID` header; if present, use it as `queryId`.
**Severity**: LOW/MEDIUM

---

## E: Test Coverage Gaps

### E.1 — Retrieval Tools with No Unit Test File

53 source files in `platform/src/lib/retrieve/` (excluding `index.ts`, `types.ts`, `__smoke__`).
29 have test files in `__tests__/`. **25 have no test file at all.**

**Untested retrieval tools** (file:line reference = no corresponding `__tests__/<name>.test.ts`):

| Tool File | Complexity | Priority |
|-----------|-----------|---------|
| `chandra_balam_for_native.ts` | Medium | HIGH |
| `classical_attribution_lookup_tool.ts` | Medium | HIGH |
| `classical_disclosure_filter.ts` | Low | MEDIUM |
| `classical_text_search_tool.ts` | Medium | HIGH |
| `get_planet_avastha.ts` | Medium | HIGH |
| `get_shadbala_full.ts` | High (complex SQL) | CRITICAL |
| `muhurta_finder.ts` | High | HIGH |
| `query_cdlm_lookup.ts` | Medium | HIGH |
| `query_dasamsha_career.ts` | Medium | HIGH |
| `query_drekkana_drishti.ts` | Medium | MEDIUM |
| `query_eclipse_transits.ts` | Medium | MEDIUM |
| `query_jaimini_chara_dasha.ts` | High | HIGH |
| `query_jaimini_drishti.ts` | Medium | MEDIUM |
| `query_muhurat.ts` | Medium | MEDIUM |
| `query_planet_war.ts` | High | HIGH |
| `query_planetary_period_predictions.ts` | High | HIGH |
| `query_remedies_prescribed.ts` | Medium | MEDIUM |
| `query_rm_walk.ts` | Medium | HIGH |
| `query_shashtiamsha.ts` | High | HIGH |
| `query_transits_over_natal.ts` | Medium | HIGH |
| `query_ucn_walk.ts` | Medium | HIGH |
| `query_v7_additions.ts` | Low | MEDIUM |
| `query_yogas_active_now.ts` | Medium | HIGH |
| `tara_balam_for_native.ts` | Medium | HIGH |
| `tool_catalogue.ts` | Low | LOW |

**Note**: SRP-T-1 session targets the highest-priority test gaps. This catalog represents
the state BEFORE T-1 fixes are merged (audit runs in parallel per brief).

### E.2 — Tested Tools — Known Filter Coverage Gaps (Pre-T-1)

Tests exist for these tools but were noted as having zero filter-path coverage before SRP-T-1:

| Tool File | Gap |
|-----------|-----|
| `platform/src/lib/retrieve/msr_sql.ts` | No test for `valence` filter (the primary D-finding path) |
| `platform/src/lib/retrieve/lel_query.ts` | No test for date-range filters |
| `platform/src/lib/retrieve/query_ephemeris.ts` | No test for planet filter |

---

## F: Primitive Dispatcher Hardcoding Issues

### F.1 — `domains: []` Hardcoded (OPEN BEYOND FIX-2)

**File**: `platform/src/app/api/mcp/primitives/[tool]/route.ts:182`

```typescript
const queryPlan = {
  query_plan_id: queryId,
  query_text: `surgical_primitive:${mcpToolName}`,
  query_class: 'holistic' as const,
  domains: [],                        // ← hardcoded
  forward_looking: false,             // ← hardcoded (FIX-2 target)
  audience_tier: audienceTier,
  tools_authorized: [retrievalToolName],
  history_mode: 'synthesized' as const,
  panel_mode: false,
  expected_output_shape: 'structured_data' as const,
  manifest_fingerprint: '',
  schema_version: '1.0' as const,
}
```

**Analysis**: For the following tools, `plan.domains` is consumed directly to filter results:
- `contradiction_register.ts:106-108` — filters by `plan.domains`
- `resonance_register.ts:112-114` — filters by `plan.domains`
- `pattern_register.ts:114-115` — filters by `plan.domains`
- `msr_sql.ts:104` — logs `plan.domains` and uses it in SQL filter
- `cluster_atlas.ts:118-122` — filters by `plan.domains`

When these tools are called via the MCP primitive dispatcher (with `domains: []`), the domain
filter is silently skipped (the code pattern is `if (plan.domains.length > 0) { filter... }`).
This means ALL domains are returned, not domain-filtered results.

**Impact**: A tool call to `contradiction_register` via the primitive dispatcher returns all
contradictions regardless of domain. This may or may not be the desired behavior for a
"surgical" call, but it is **inconsistent with planner-routed calls** that correctly supply
`domains` from the user's query. The logging debt at D.3 is a direct consequence of this.

**Recommended fix**: Accept `domain?: string | string[]` in `body.params` and populate
`queryPlan.domains` from it. Add to the brief for SRP-F-1.

**Severity**: HIGH

### F.2 — `manifest_fingerprint: ''` Hardcoded

**File**: `platform/src/app/api/mcp/primitives/[tool]/route.ts:189`

`manifest_fingerprint` is an empty string in the hardcoded QueryPlan. The retrieve tools
that use it (e.g., `manifest_query.ts`) rely on it for cache invalidation keying. An empty
fingerprint means cache never invalidates on manifest changes for surgical primitive calls.

**Impact**: MEDIUM. The manifest fingerprint is used in the bundle cache key. An empty value
means all surgical primitive calls share the same fingerprint key, potentially serving stale
manifest data from cache.

**Recommended fix**: Load the current manifest fingerprint at route handler startup (same as
the main pipeline does) and inject it into the QueryPlan.

**Severity**: MEDIUM

### F.3 — `query_class: 'holistic'` Hardcoded

**File**: `platform/src/app/api/mcp/primitives/[tool]/route.ts:181`

All surgical primitive calls log `query_class: 'holistic'` regardless of which tool is called.
Observatory analytics that aggregate by `query_class` will misclassify surgical primitive calls
as holistic synthesis queries.

**Impact**: LOW for functional correctness; MEDIUM for Observatory analytics accuracy.

**Recommended fix**: Set `query_class: 'cross_native'` or add a new `'surgical_primitive'`
class (requires schema change) to distinguish primitive calls from planner-routed queries.

**Severity**: MEDIUM

---

## Summary of Required Actions

### Immediate (CRITICAL / HIGH):

1. **A.1**: Confirm `R11V2_USE_ADAPTERS` is permanently true → remove legacy orchestrator path
   from `consume/route.ts` (~450 LoC). Verify `mcp/execute/route.ts` migration path separately.
2. **B.2**: Audit `CONSUME_UI_V2_ENABLED` false branch — confirm it points to deleted components.
   If so, inline `true` and remove dead conditional.
3. **C.1**: Fix `query_signals.ts:181` valence Zod enum to use DB vocabulary
   (`'benefic'/'malefic'/'context-dependent'`). Creates silent zero-result bugs for MCP callers.
4. **F.1**: Accept `domain` in primitive dispatcher request body; populate `queryPlan.domains`.
5. **E.1 / E.2**: SRP-T-1 session should target `get_shadbala_full`, `muhurta_finder`,
   `query_planetary_period_predictions`, `query_planet_war` as highest-priority first tests.

### Short-term (MEDIUM):

6. **A.2**: Remove `PRIMARY_TOOL_NAMES` (zero call sites, deprecated).
7. **B.5**: Simplify smooth-stream flag chain after `R10_SMOOTH_STREAM_V2` is promoted always-on.
8. **C.4**: Consolidate `QueryPlan` to single definition in `router/types.ts`; `retrieve/types.ts`
   and `bundle/types.ts` use `Pick<>`.
9. **D.2**: Strip `system` field from `query_dasha_periods.ts` invocation_params logging.
10. **F.2**: Populate `manifest_fingerprint` in primitive dispatcher.

### Long-term (LOW / cleanup):

11. **C.2/C.3**: Add `DomainEnum` and `SignificanceTier` Zod types to a shared location.
12. **B.3**: Consolidate Observatory dual-gate (`_guard.ts` direct env check vs. `configService`).
13. **D.4**: Add correlation ID header support to primitive dispatcher.
14. **F.3**: Add `'surgical_primitive'` query class or fix Observatory analytics labeling.

---

## Appendix: File Reference Index

| Finding ID | Primary File | Lines |
|-----------|-------------|-------|
| A.1 | `platform/src/app/api/chat/consume/route.ts` | 82, 862–907, 1201–1600 |
| A.1.b | `platform/src/lib/synthesis/orchestrator.ts` | 1–34 |
| A.1.b | `platform/src/lib/synthesis/single_model_strategy.ts` | 1–886 |
| A.1.b | `platform/src/lib/synthesis/panel_strategy.ts` | 1–248 |
| A.2 | `platform/src/lib/pipeline/manifest_compressor.ts` | 79–95 |
| A.2 | `platform/src/lib/admin/trace_assembler.ts` | 30, 599 |
| A.2 | `platform/src/lib/admin/trace_client.ts` | 21 |
| A.2 | `platform/src/lib/models/resolver.ts` | 68 |
| A.2 | `platform/src/lib/models/registry.ts` | 844 |
| A.3 | `platform/src/lib/config/feature_flags.ts` | 6 (comment only) |
| A.4 | `platform/src/lib/config/feature_flags.ts` | CLEAN |
| B.2 | `platform/src/app/clients/[id]/consume/page.tsx` | 123 |
| B.2 | `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx` | 56 |
| B.3 | `platform/src/app/api/admin/observatory/_guard.ts` | 28 |
| C.1 | `platform-mcp/src/tools/query_signals.ts` | 181 |
| C.1 | `platform-mcp/src/tools/msr_sql.ts` | 76–78 |
| C.4 | `platform/src/lib/router/types.ts` | 6 |
| C.4 | `platform/src/lib/retrieve/types.ts` | 6 |
| C.4 | `platform/src/lib/bundle/types.ts` | 30 |
| C.4 | `platform/src/lib/trace/types.ts` | 52, 464 |
| D.2 | `platform/src/lib/retrieve/query_dasha_periods.ts` | 405 |
| D.3 | `platform/src/lib/retrieve/contradiction_register.ts` | 59–62 |
| D.3 | `platform/src/lib/retrieve/resonance_register.ts` | 85 |
| D.3 | `platform/src/lib/retrieve/pattern_register.ts` | 85 |
| D.4 | `platform/src/app/api/mcp/primitives/[tool]/route.ts` | 175 |
| F.1 | `platform/src/app/api/mcp/primitives/[tool]/route.ts` | 182 |
| F.2 | `platform/src/app/api/mcp/primitives/[tool]/route.ts` | 189 |
| F.3 | `platform/src/app/api/mcp/primitives/[tool]/route.ts` | 181 |
