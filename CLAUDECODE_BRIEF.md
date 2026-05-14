---
status: OPEN
session_id: AIOPS_AD_4
phase: AD.4
phase_name: "Call-site migration + legacy-path preservation + flag-off equivalence"
next_session: AIOPS_AD_5
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_AD_4
## AIOps Phase 2, Step 4 — Migrate every call site to runAdapter / streamAdapter

---

## §0 — Executor orientation

AD.4 migrates every direct `streamText` / `generateText` call to use
`runAdapter` / `streamAdapter`. Behind the flag `ADAPTERS_ENABLED` (default
false), the legacy path is preserved in `legacy_runAdapter.ts` and the
call sites short-circuit to it. With the flag on, the new path is active.

The win condition: 35+ flag-off equivalence tests pass byte-identically
between legacy and new paths (the same pattern Phase 1 used). Once that
gate is green, AD.5 flips the flag.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md §8
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/lib/adapters/ (AD.0-AD.3.5 deliverables — including new streamAdapterRaw, prepareRequest, new QueryRequest fields)
5. platform/src/lib/synthesis/single_model_strategy.ts
6. platform/src/lib/synthesis/panel/member_runner.ts
7. platform/src/lib/synthesis/panel/adjudicator.ts
8. platform/src/lib/synthesis/orchestrator.ts
9. platform/src/app/api/chat/consume/route.ts
10. platform/src/lib/aiops/probe/runner.ts (Phase 1 probe runner)
11. platform/scripts/aiops/cutover_smoke.ts (Phase 1)
12. platform/scripts/aiops/probe_health_cron.ts (Phase 1)
13. platform/scripts/eval/* — every eval entrypoint
14. platform/scripts/checkpoint/* — every checkpoint script
15. platform/src/lib/synthesis/think_block_filter.ts (will be DELETED at end of AD.4)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/adapters/legacy_runAdapter.ts # NEW — wraps existing streamText path
platform/src/lib/synthesis/**                  # migrate
platform/src/app/api/chat/consume/**           # migrate
platform/src/lib/aiops/probe/**                # migrate
platform/scripts/aiops/**                      # migrate
platform/scripts/eval/**                       # migrate
platform/scripts/checkpoint/**                 # migrate
platform/src/lib/models/resolver.ts            # thin deepseekProviderOptions / googleProviderOptions to pass-through wrappers
platform/src/lib/synthesis/think_block_filter.ts # DELETE
platform/src/lib/adapters/__tests__/equivalence/* # NEW
CLAUDECODE_BRIEF.md
```

### must_not_touch
- platform/src/components/consume/** — Phase 3
- platform/src/lib/components/observatory/** — sealed
- platform/src/lib/llm/providers/*_observed.ts — adapters CALL these; observed wrappers unchanged

---

## §3 — Work plan

### 3.1 — Inventory call sites

```bash
cd /Users/Dev/Vibe-Coding/Apps/madhav-phase-2-tmp
grep -rn "streamText\|generateText" platform/src platform/scripts | grep -v __tests__
```

Capture the full list in `00_ARCHITECTURE/aiops/phase_2/AD4_CALL_SITES_INVENTORY.md`.

### 3.2 — Author legacy_runAdapter

`platform/src/lib/adapters/legacy_runAdapter.ts`:

A drop-in replacement for `runAdapter` that uses the existing `streamText`
+ provider-options pattern. When `ADAPTERS_ENABLED=false`, this is what
runs. Implementation copies the logic from current call sites (DeepSeek
thinking, Gemini safety + thinking, etc.) into one function. After AD.5
flip stabilizes for 2 weeks, this file gets deleted (per flag-removal PR).

### 3.3 — Wire the flag

`platform/src/lib/adapters/run_adapter.ts` (already exists from AD.2):

```ts
import { isFeatureFlagEnabled } from '@/lib/config/feature_flags'
import { runAdapterNew } from './run_adapter_new'  // the AD.2 + AD.3 implementation
import { runAdapterLegacy } from './legacy_runAdapter'

export async function runAdapter(req: QueryRequest): Promise<ModelInteraction> {
  if (isFeatureFlagEnabled('ADAPTERS_ENABLED')) {
    return runAdapterNew(req)
  }
  return runAdapterLegacy(req)
}
```

Same pattern for `streamAdapter`.

### 3.4 — Migrate call sites

For each call site (mechanical):

**Before:**
```ts
const meta = getModelMeta(modelId)
const model = resolveModel(modelId)
const providerOpts = { ...deepseekProviderOptions(modelId, 'synthesis'), ...googleProviderOptions(modelId) }
const result = await streamText({ model, system, messages, providerOptions: providerOpts, maxOutputTokens, temperature, tools })
// ... custom <think> parsing via think_block_filter ...
```

**After:**
```ts
const interaction = await runAdapter({
  callType: 'synthesis',
  systemPrompt: system,
  messages,
  tools,
  maxOutputTokens,
  temperature,
  reasoning: 'auto',
})
// Use interaction.reasoning, interaction.finalText directly — no more <think> parsing
```

### Three adapter entry points — choose per call site type:

| Call site pattern | Entry point | Why |
|---|---|---|
| `generateText({ ... })` — single-shot non-streaming, with or without tools | `runAdapter(req)` | Collects the stream into a `ModelInteraction`. Synchronous-feeling API. |
| `streamText({ ... })` — single-shot streaming consumed by custom event handlers (not AI SDK UI) | `streamAdapter(req)` | Returns `ReadableStream<ModelInteractionEvent>` with typed events. |
| `streamText({ ... })` — agentic loop with `stopWhen: stepCountIs(N)`, OR streaming response piped via `result.toUIMessageStreamResponse()` to SSE | `streamAdapterRaw(req)` → `{ result, meta }` | Returns the AI SDK `StreamTextResult` directly. Caller uses `.toUIMessageStreamResponse()` (SSE) or reads `.fullStream` (custom multi-step handling). Provider quirks still applied by the adapter. |

#### Per-site migration pattern map:

| Call site | Entry point | Key options to pass |
|---|---|---|
| `synthesis/single_model_strategy.ts` (multi-step + audit) | `streamAdapterRaw` | `multiStep: { maxSteps: 5 }`, `smoothStream: true`, `onStepFinish`, `onFinish` |
| `synthesis/panel_strategy.ts` (panel verbatim passthrough) | `streamAdapterRaw` | `multiStep` as needed; caller pipes `result` to its own consumer |
| `synthesis/panel/member_runner.ts` (single panel member) | `runAdapter` | tools, temperature |
| `synthesis/panel/adjudicator.ts` (final adjudication) | `runAdapter` | tools (if any), responseSchema (if structured output) |
| `pipeline/pipeline_planner.ts` (tool-choice required) | `runAdapter` | `tools`, `toolChoice: 'required'` (or `{ type: 'tool', toolName }`) |
| `pipeline/planner_context_builder.ts` (single generateText for context) | `runAdapter` | no special options |
| `app/api/chat/consume/route.ts` (SSE pipe) | `streamAdapterRaw` | `multiStep` (synthesis under it), `onStepFinish`, `onFinish` for audit; then `return result.toUIMessageStreamResponse()` |
| `app/api/chat/build/route.ts` (SSE pipe) | `streamAdapterRaw` | same SSE pattern |
| `aiops/probe/runner.ts` | `runAdapter` | minimal — single call, no tools |
| `checkpoints/checkpoint_{4_5,5_5,8_5}.ts` | `runAdapter` | minimal |
| `conversations/title.ts` | `runAdapter` | minimal |
| `models/health.ts` | `runAdapter` | minimal |
| `scripts/retrieval/test_classify.ts` | `runAdapter` | as needed |

Migrate in this order (low-risk first):
1. `platform/src/lib/aiops/probe/runner.ts`
2. `platform/scripts/aiops/cutover_smoke.ts`
3. `platform/scripts/aiops/probe_health_cron.ts`
4. `platform/scripts/eval/*`
5. `platform/scripts/checkpoint/*`
6. `platform/src/lib/synthesis/single_model_strategy.ts`
7. `platform/src/lib/synthesis/panel/member_runner.ts`
8. `platform/src/lib/synthesis/panel/adjudicator.ts`
9. `platform/src/lib/synthesis/orchestrator.ts`
10. `platform/src/app/api/chat/consume/route.ts`

After each, run that area's tests. Don't continue to next site until tests
pass.

### 3.5 — Thin resolver.ts

`platform/src/lib/models/resolver.ts`:
- `resolveModel(id)` → keeps as-is (ID → LanguageModel). Some non-adapter
  consumers might still use it (rare; document).
- `deepseekProviderOptions(...)` → keep but mark deprecated. Used only by
  `legacy_runAdapter.ts` until flag removal.
- `googleProviderOptions(...)` → same.

### 3.6 — Delete think_block_filter.ts

After step 3.4 confirms no caller uses it. Run:
```bash
grep -r "think_block_filter" platform/src platform/scripts
```
Should return 0 hits. Then `git rm platform/src/lib/synthesis/think_block_filter.ts`
and its test file.

### 3.7 — Flag-off equivalence tests

`platform/src/lib/adapters/__tests__/equivalence/runtime_equivalence.test.ts`:

Parametrize across (stack × call_type × representative_prompt). For each:
- Run with `ADAPTERS_ENABLED=false` → legacy path → capture ModelInteraction.
- Run with `ADAPTERS_ENABLED=true` → new path → capture ModelInteraction.
- Assert: `modelId`, `finalText`, `reasoning?.text`, `finishReason`, `usage.inputTokens`, `usage.outputTokens` MATCH.

Use mocked SDK calls so the test is deterministic. ≥35 parametrized cases.

### 3.8 — Smoke

```bash
cd /Users/Dev/Vibe-Coding/Apps/madhav-phase-2-tmp
npm --prefix platform run typecheck 2>&1 | tail -5
npm --prefix platform run lint 2>&1 | tail -5
npm --prefix platform run test -- --run 2>&1 | tail -10
```

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD4.1 | Call-site inventory file exists | `test -f 00_ARCHITECTURE/aiops/phase_2/AD4_CALL_SITES_INVENTORY.md` |
| AC.AD4.2 | All inventoried sites migrated to runAdapter/streamAdapter | grep `streamText\\|generateText` in platform/src + scripts excluding tests + adapters/ + legacy returns 0 hits |
| AC.AD4.3 | legacy_runAdapter.ts exists and is the flag-off path | grep + integration test |
| AC.AD4.4 | think_block_filter.ts deleted | `! test -f platform/src/lib/synthesis/think_block_filter.ts` |
| AC.AD4.5 | Equivalence tests parametrize ≥35 cases | `npm run test -- equivalence` ≥35 |
| AC.AD4.6 | Every equivalence case passes | exit 0 |
| AC.AD4.7 | typecheck + lint + full suite green | exit 0 each |
| AC.AD4.8 | scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Final commit:
```
feat(aiops-AD.4): migrate all call sites to runAdapter / streamAdapter

- N call sites in platform/src + platform/scripts migrated (inventory in AD4_CALL_SITES_INVENTORY.md)
- legacy_runAdapter.ts preserves the old streamText+providerOptions path for flag-off behavior
- ADAPTERS_ENABLED flag controls which path runs; default still false through this commit
- think_block_filter.ts deleted (replaced by adapter_deepseek's MarkerBuffer)
- resolver.ts deepseekProviderOptions / googleProviderOptions marked deprecated; used only by legacy path
- 35+ equivalence tests assert byte-identical behavior flag-on vs flag-off
- Full suite green

AC summary: 8/8 PASS
```

Rotate brief → AD.5.

---

## §7 — BAIL OUT triggers

- Any equivalence test fails — the new path diverges from legacy. Investigate. Do NOT continue to AD.5 until parity.
- A call site requires deep refactoring that pulls in >5 unrelated files — bail and have native scope the change separately.
- Panel mode interaction with the new adapter produces unexpected ordering — bail.

---

*End of PHASE_AD_4_BRIEF.md*
