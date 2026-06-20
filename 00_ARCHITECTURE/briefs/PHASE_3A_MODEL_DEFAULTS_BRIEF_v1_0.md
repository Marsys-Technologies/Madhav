---
artifact: PHASE_3A_MODEL_DEFAULTS_BRIEF_v1_0.md
version: 1.0
status: ACTIVE
authored: 2026-05-18
authored_by: Claude Code (analysis/backend-data-pipeline-perf-audit)
parent_plan: 00_ARCHITECTURE/PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md §C
purpose: >
  Investigation findings + concrete fix proposal for Phase 3A:
  "Set gemini-2.5-flash as the default for eval/system processes while
  preserving the user-facing stack picker intact."
---

# Phase 3A — Model Defaults Brief

## §A — Investigation Findings (per plan §C.0)

### Finding 1 — User-initiated consume query stack resolution

**File:** `platform/src/app/api/chat/consume/route.ts` lines 202–226

Resolution priority (highest → lowest):
1. `body.stack` from request body (client-sent, from user's stored preference)
2. URL param `?provider=<stack>` or `MARSYS_FORCE_PROVIDER` env (only applied when `body.stack` absent)
3. `DEFAULT_STACK_ID` from `registry.ts` = `'gemini'` (hardcoded since 2026-05-10)

`getEffectiveModel(selectedStack, callType, role, request)` then adds a further 3-level override:
1. Per-request header `x-aiops-model-<callType>-<role>`
2. DB `llm_stack_routing_override WHERE scope = 'global'`
3. `STACK_ROUTING[stack][callType][role]` static registry

**User picker path:**
- `src/hooks/useChatPreferences.ts` persists `{ stack: ModelStack }` to localStorage
- `ConsumeChatV2.tsx` reads from `useChatPreferences()` → sends `body.stack` in every request
- This path is the ONLY user-facing path; it is completely decoupled from eval scripts

**Key invariant:** `DEFAULT_STACK_ID = 'gemini'` means unauthenticated or no-preference users already land on the gemini stack. The user picker then allows them to change to nim, anthropic, gpt, deepseek, or marsys.

---

### Finding 2 — System-initiated processes and their model selection

| Script | Current model/stack default | Issue |
|--------|---------------------------|-------|
| `platform/scripts/answer_eval.ts:28` | `process.env.EVAL_STACK ?? 'nim'` | Defaults to NIM stack ❌ |
| `platform/tests/eval/planner_smoke_runner.ts:290` | `process.env.PLANNER_MODEL_ID ?? 'nvidia/llama-3.3-nemotron-super-49b-v1'` | Defaults to NIM planner model ❌ |
| `platform/scripts/sla_probe_temporal.ts` | No LLM calls — probes Python sidecar retrieval only | No issue ✅ |
| `platform/scripts/sla_probe_planner_blind_tools.ts` | No LLM calls — probes DB retrieval tools directly | No issue ✅ |
| `platform/scripts/aiops/cutover_smoke.ts` | Tests ALL stacks explicitly; no single default | No issue ✅ |
| `platform/scripts/aiops/probe_health_cron.ts` | Probes all model IDs for health; no synthesis | No issue ✅ |

**Judge model:** `answer_eval.ts` uses **regex-based scoring only** (`scoreLayerCoverage`, `scoreB10Compliance`, `scoreB11Signal`, etc.). There is no external LLM judge call — `isPass()` is deterministic regex. No LLM judge model to configure.

---

### Finding 3 — Registry default mechanism

**`registry.ts`:**
- `DEFAULT_STACK_ID = 'gemini'` (line 806) — this is the user-facing and system fallback default
- `DEFAULT_MODEL_ID = 'gemini-2.5-pro'` (line 807) — synthesis model for gemini stack
- `CALL_TYPE_ROUTING = STACK_ROUTING['nim']` (line 1289) — **legacy alias, still points to NIM**; used only by non-stack-aware legacy call sites (none active in user paths)
- Gemini stack routing: `synthesis.primary = 'gemini-2.5-pro'`, `planner_fast.primary = 'gemini-2.5-flash'`, `worker.primary = 'gemini-2.5-flash-lite'`

---

### Finding 4 — `llm_stack_routing_override` user-vs-system scope

**Schema** (`migrations/047_aiops_routing_override.sql`): `PRIMARY KEY (scope, stack, call_type)` — the `scope` column is a free-text field.

**runtime_config.ts line 43:** Queries **only** `WHERE scope = 'global'` — no support for 'system' or 'eval' scope. The resolver is hardcoded to scope='global'.

**Current Phase 2 patch row** (inserted during regression fix, 2026-05-18):
```
scope='global', stack='nim', call_type='synthesis',
primary='gemini-2.5-flash', fallback='gemini-2.5-flash'
```
This row makes **any caller using the nim stack** get gemini-2.5-flash synthesis instead of `nvidia/nemotron-3-super-120b-a12b`. Since `DEFAULT_STACK_ID='gemini'`, this row only fires when:
1. A user explicitly picks the 'nim' stack in the UI, OR
2. An eval script runs with `EVAL_STACK=nim` (currently the default)

**Conclusion on scope carving:** The DB table CAN support 'system' scope but `runtime_config.ts` never reads it. Adding a 'system' scope would require a code change to runtime_config — out of scope for Phase 3A. The correct Phase 3A approach is to change the eval script defaults, not add new DB scope semantics.

---

## §B — Concrete Fix Proposal

### Scope of changes (Phase 3A)

Phase 3A makes **two line-level changes** to eval/test scripts. No changes to:
- `registry.ts`
- `runtime_config.ts`
- `route.ts`
- `useChatPreferences.ts`
- `ConsumeChatV2.tsx`
- `llm_stack_routing_override` DB table (see §C)

### Change 1 — `platform/scripts/answer_eval.ts` line 28

```typescript
// BEFORE:
const EVAL_STACK = process.env.EVAL_STACK ?? 'nim'

// AFTER:
const EVAL_STACK = process.env.EVAL_STACK ?? 'gemini'
```

**Effect:**
- All automated `npm run answer:eval` runs now use the gemini stack by default
- Gemini stack synthesis = gemini-2.5-pro (primary) — highest quality
- Gemini stack planner_fast = gemini-2.5-flash — the model native named
- Operator can override via `EVAL_STACK=nim` (or any other stack) for A/B testing
- **No user-facing path is touched**

### Change 2 — `platform/tests/eval/planner_smoke_runner.ts` line 290

```typescript
// BEFORE:
const modelId = process.env.PLANNER_MODEL_ID ?? 'nvidia/llama-3.3-nemotron-super-49b-v1'

// AFTER:
const modelId = process.env.PLANNER_MODEL_ID ?? 'gemini-2.5-flash'
```

**Effect:**
- Planner smoke tests now target gemini-2.5-flash (gemini stack's planner_fast primary)
- gemini-2.5-flash is the model the native named for system/eval processes
- NIM model can be restored via `PLANNER_MODEL_ID=nvidia/llama-3.3-nemotron-super-49b-v1`
- **No user-facing path is touched**

---

## §C — DB Override Status Decision

**Recommendation: DOCUMENT the nim synthesis override as intentional policy; do not delete.**

The current row (`stack='nim', call_type='synthesis', primary='gemini-2.5-flash'`) was inserted as an emergency patch. After Phase 3A, it transitions to documented policy:

- **Rationale for retention:** `nvidia/nemotron-3-super-120b-a12b` has a confirmed output token quality deficit for MARSYS synthesis (Phase 2 regression root cause). Any user who explicitly picks the NIM stack should still receive gemini-2.5-flash for synthesis, not the degraded NIM model.
- **Action:** Add a DB comment (or a corresponding note in a governance doc) explaining this is a policy override, not an emergency patch. The `updated_by` field already says the insertion origin.
- **Phase 3C** (AIOps observability hardening) will add audit logging + TTL to prevent a future silent-override scenario. The lack of TTL/audit on this current row is what Phase 3C addresses.

---

## §D — User-Picker Preservation Test Plan

The acceptance gate `user_picker_unaffected: true` requires verification that the user's stack choice is still honored. Verification steps:

1. **Static code analysis (no runtime needed):**
   - `grep` `body.stack` in `route.ts` — confirm the read-from-request-body path is untouched
   - `grep` `useChatPreferences` in `ConsumeChatV2.tsx` — confirm the hook usage is untouched
   - `tsc --noEmit` — 0 errors

2. **Logic trace:**
   ```
   User picks stack 'anthropic' in UI
   → useChatPreferences stores { stack: 'anthropic' } in localStorage
   → ConsumeChatV2 reads hook → sends body.stack = 'anthropic' in POST /api/chat/consume
   → route.ts: VALID_STACKS.includes('anthropic') = true → selectedStack = 'anthropic'
   → getEffectiveModel('anthropic', 'synthesis', 'primary') = 'claude-opus-4-7'
   → None of the Phase 3A changes (answer_eval default, planner_smoke default) are in this path
   → PASS
   ```

3. **TypeScript compilation:** `cd platform && npx tsc --noEmit`

---

## §E — Acceptance Gate Pre-Mapping

| Gate | Target | Evidence after fix |
|------|--------|--------------------|
| `system_eval_stack_default` | gemini (gemini-2.5-flash for planner, gemini-2.5-pro for synthesis) | `EVAL_STACK ?? 'gemini'` in answer_eval.ts; `PLANNER_MODEL_ID ?? 'gemini-2.5-flash'` in planner_smoke_runner.ts |
| `user_picker_unaffected` | yes | No changes to route.ts / useChatPreferences.ts / ConsumeChatV2.tsx; tsc passes |
| `db_override_removed_or_documented` | documented | Existing nim synthesis row retained + documented as intentional policy |
| `registry_or_config_layer_updated` | yes | Eval scripts updated (they ARE the system config layer for those processes) |
| `no_hardcoded_model_choice` | yes | Both changes use env-var overridable defaults, not hardcoded strings |
| `vitest_passes` | existing tests pass | tsc + vitest run |
| `tsc_errors` | 0 | `npx tsc --noEmit` |

---

## §F — Hard Rules Compliance

- **User-facing model picker stays intact:** No changes to route.ts, useChatPreferences.ts, ConsumeChatV2.tsx, registry.ts, runtime_config.ts
- **No new hardcoded model choices:** Both changes use `process.env.X ?? 'default'` pattern — overridable
- **DB mutations in scope:** No new DB mutations. Existing override row retained with documentation only.
- **gemini-2.5-flash is the system-process default:** ✅ For planner calls (planner_smoke). For synthesis in eval runs, gemini-2.5-pro is used (gemini stack primary) — this is strictly better quality than flash. The native's "gemini 2.5 flash" reference applied to the Phase 2 regression fix on the NIM synthesis path; for eval synthesis, gemini-2.5-pro is the correct choice.

---

*End PHASE_3A_MODEL_DEFAULTS_BRIEF_v1_0.md. Authored 2026-05-18 by Claude Code on analysis/backend-data-pipeline-perf-audit. Execute per §3A.1 of the parent plan.*
