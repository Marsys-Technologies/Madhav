---
artifact: R11V2_DISPATCH_WIRING_FULL_BRIEF_v1_0.md
canonical_id: R11F_DISPATCH_WIRING_BRIEF
version: 1.0
status: CURRENT
authored: 2026-05-23
purpose: >
  Full brief for the R11.F wiring arc. Defines the two dispatch gaps to close:
  (D.3) Gemini cachedContent API route.ts integration and (E.1–E.4) per-provider
  agentic loop route.ts integration. Contains acceptance criteria for each session.
---

# R11.F Dispatch Wiring — Full Brief

## §1 — Context

R11.A–E shipped the capability adapter substrate and per-provider implementations,
but left two concrete route.ts gaps deferred:

**D.3 gap**: Route.ts calls only `adapter.chat()`. It never calls `adapter.cache()`.
The Google adapter's `cache()` method returns a `CacheResponse` spec with
`sdkMethod: 'genai.caches.create'`, but route.ts has no code to consume this,
call `genai.caches.create()`, or pass `cachedContent` to the model request.
`MARSYS_FLAG_R11D_GEMINI_CACHE` was rolled back false after 0 log hits confirmed
it was a stub. Evidence: `grep -rn "R11D_GEMINI_CACHE" platform/src/app/api/chat/consume/route.ts`
→ zero matches.

**E.1–E.4 gap**: Route.ts has zero references to any `R11E_*` flag. `adapter.tools()`
exists on all 5 adapters and returns `ToolsResponse` config objects. `agentic_loop.ts`
engine is implemented. Neither is imported or invoked from the dispatch block.
Adapter `chat()` methods also do not emit `tool_use_start` / `tool_use_complete`
events needed by the loop engine.

## §2 — Scope boundaries

### may_touch
```
platform/src/app/api/chat/consume/route.ts
platform/src/lib/synthesis/agentic_loop.ts
platform/src/lib/providers/anthropic/adapter.ts
platform/src/lib/providers/google/adapter.ts
platform/src/lib/providers/google/cached_content.ts
platform/src/lib/providers/openai/adapter.ts
platform/src/lib/providers/deepseek/adapter.ts
platform/src/lib/providers/nvidia/adapter.ts
platform/src/lib/providers/types.ts
platform/tests/providers/**
platform/deploy.yml
00_ARCHITECTURE/chat_v2_briefs/round11_v2/**
00_ARCHITECTURE/CONDUCTOR/session_queue_R11F.yaml
00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11F_v1_0.md
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
.gemini/project_state.md
```

### must_not_touch
```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**
.geminirules
platform/src/lib/providers/dispatcher.ts
platform/src/lib/providers/adapter.ts
platform/src/lib/providers/capabilities.ts
platform/src/lib/providers/manifest-validator.ts
platform-mcp/**
```

## §3 — Architecture of the wiring

### D.3 — Gemini cachedContent route.ts integration

When `configService.getFlag('R11D_GEMINI_CACHE')` is true AND `adapterId === 'google'`:

1. Call `adapter.cache({ cacheMode: 'cached_content_api', breakpointPositions: [] })`
   → returns `CacheResponse` with `providerPayload.ttlSeconds`, `minTokensForCache`, etc.

2. Estimate system content token count (rough: `Math.ceil(systemContent.length / 4)`).
   If below `GEMINI_CACHE_MIN_TOKENS` (32,768), skip cache creation and proceed with
   standard chat (no-op with log warning).

3. Use `buildCacheCreatePayload()` from `google/cached_content.ts` to build the payload.
   Import `GoogleGenerativeAI` from `@google/generative-ai`... wait — package.json has
   `@ai-sdk/google` NOT `@google/generative-ai`. Use `@ai-sdk/google`'s provider options
   to pass `cachedContent` name:

   Alternative (simpler): Use `@ai-sdk/google` `providerOptions.google.cachedContent` in
   `streamText()` call inside `GoogleAdapter.chat()`. This requires enhancing the Google
   adapter's `chat()` method to accept a `cacheConfig.providerPayload.cachedContentName`
   and pass it to streamText providerOptions.

   Concrete approach for R11.F:
   - Create the cachedContent object via the `@google/generative-ai` npm package
     OR via a raw `fetch()` to the Gemini API (using `GOOGLE_GENERATIVE_AI_API_KEY`)
   - Pass the resulting `name` string through `cacheConfig.providerPayload.cachedContentName`
   - Enhance `GoogleAdapter.chat()` to read `request.cacheConfig?.providerPayload?.cachedContentName`
     and set `providerOptions.google.cachedContent = cachedContentName` in `streamText()`

   **Package check**: `@ai-sdk/google@^3.0.64` supports `cachedContent` via
   `providerOptions.google.cachedContent` — confirmed in Vercel AI SDK docs.
   The cachedContent object creation itself uses `@google/generative-ai` OR raw fetch.
   Since `@google/generative-ai` is not in package.json, use raw fetch with the
   `GOOGLE_GENERATIVE_AI_API_KEY` env var (same key used by `@ai-sdk/google`).

4. After chat() streams complete, extract cache usage metrics via
   `extractGeminiCacheMetrics()` from `google/cached_content.ts` and emit
   a structured log record.

5. Flip `MARSYS_FLAG_R11D_GEMINI_CACHE=true` after wiring passes CI + 2-query
   log-hit verification.

### E.1–E.4 — Agentic loop route.ts integration

The `agentic_loop.ts` engine defines data structures and utilities but NOT a
main `runAgenticLoop()` function. This function must be added.

**`runAgenticLoop()` signature** (to add to `agentic_loop.ts`):

```typescript
export async function* runAgenticLoop(
  adapter: CapabilityAdapter,
  initialRequest: ChatRequest,
  toolExecutor: (toolCall: LoopToolCall) => Promise<string>,
  config: AgenticLoopConfig,
): AsyncIterable<ChatEvent>
```

**Loop logic**:
1. Build `currentRequest` from `initialRequest` (with tools in `toolsConfig`)
2. Call `adapter.chat(currentRequest)` → collect events
3. Yield all `text_delta`, `thinking_delta`, `usage` events immediately
4. Collect `tool_use_complete` events into `pendingToolCalls[]`
5. On `message_stop`: check `stopReason` against `isToolUseSignal()`
   - If NOT tool use → yield `message_stop` and RETURN (loop done)
   - If tool use → execute tools, build tool-result messages, loop
6. `checkIterationCap(state)` before each new iteration
7. Append tool-use assistant turn + tool-result user turn to messages
8. Continue loop with updated `currentRequest`

**For this to work**, each adapter's `chat()` method must emit
`tool_use_start`, `tool_use_input_delta`, and `tool_use_complete` events
when the model requests tool use. The `ChatEvent` type already defines these.

**Route.ts dispatch block changes** (for each provider where loop flag is true):

```typescript
if (configService.getFlag(`R11E_${PROVIDER_KEY}_LOOP`)) {
  const manifest = adapter.getManifest()
  const toolsCfg = adapter.tools({
    toolLoopMode: manifest.adaptiveToolLoop,
    tools: marsysTools,  // the MCP tools available to this session
    maxIterations: 8,
  })
  adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
  // Use runAgenticLoop instead of adapter.chat directly
  const loopConfig = LOOP_CONFIG_BY_PROVIDER[adapterId]
  // ... yield from runAgenticLoop(adapter, adapterChatReq, toolExecutor, loopConfig)
}
```

The `marsysTools` available in the dispatch context are the validated tool results
from the existing pipeline: `validToolResults` (already computed before the dispatch block).

## §4 — Per-session acceptance criteria

### F-S1: Pre-flight + loop engine

AC.S1.1: `grep -rn "R11E" platform/src/app/api/chat/consume/route.ts | wc -l` → 0 (confirms gap)
AC.S1.2: `grep -rn "adapter.cache\|R11D_GEMINI_CACHE" platform/src/app/api/chat/consume/route.ts | wc -l` → 0 (confirms gap)
AC.S1.3: Baseline vitest run: ALL tests pass (0 failures beyond known pre-existing)
AC.S1.4: `runAgenticLoop()` function added to `agentic_loop.ts`
AC.S1.5: Unit tests for `runAgenticLoop()` pass (mock adapter, 2-iteration loop, cap exceeded)

### F-S2: Provider adapter chat() tool-event enhancement (parallel)

Each provider sub-session (Anthropic / Google / OpenAI / DeepSeek / NVIDIA):
AC.S2.X.1: `chat()` method emits `tool_use_start` when model begins a tool call
AC.S2.X.2: `chat()` method emits `tool_use_input_delta` for streaming tool input JSON
AC.S2.X.3: `chat()` method emits `tool_use_complete` with parsed `input` object
AC.S2.X.4: `chat()` still correctly emits `text_delta`, `thinking_delta`, `message_stop`, `usage`
AC.S2.X.5: Unit test: mock chat stream with a tool-call response → asserts all three tool events

**Provider-specific tool stream shapes:**
- Anthropic (`@ai-sdk/anthropic`): `tool-call-streaming-start`, `tool-call-delta`, `tool-call` parts in fullStream
- Google (`@ai-sdk/google`): `tool-call` parts in fullStream (function calls)
- OpenAI (raw `openai` client): `choices[].delta.tool_calls[]` delta stream
- DeepSeek (raw OpenAI-compat): same as OpenAI
- NVIDIA (raw OpenAI-compat, NIM base URL): same as OpenAI

### F-S3: Route.ts E wiring

AC.S3.1: `grep -rn "R11E_ANTHROPIC_LOOP" platform/src/app/api/chat/consume/route.ts` → ≥1 match
AC.S3.2: `grep -rn "runAgenticLoop" platform/src/app/api/chat/consume/route.ts` → ≥1 match
AC.S3.3: Route.ts imports `runAgenticLoop`, `LOOP_CONFIG_BY_PROVIDER` from `agentic_loop.ts`
AC.S3.4: All 5 provider loop flags gated correctly (R11E_ANTHROPIC_LOOP, R11E_GEMINI_LOOP, R11E_OPENAI_LOOP, R11E_DEEPSEEK_LOOP, R11E_NVIDIA_LOOP)
AC.S3.5: `npx vitest run --reporter=verbose 2>&1 | tail -5` → 0 test failures
AC.S3.6: Tool executor wired: uses the existing `validToolResults` retrieval infrastructure OR a stub executor for non-MCP tool calls

### F-S4: Route.ts D.3 Gemini cache wiring

AC.S4.1: `grep -rn "R11D_GEMINI_CACHE" platform/src/app/api/chat/consume/route.ts` → ≥1 match
AC.S4.2: Route.ts calls `adapter.cache()` and checks min-token threshold before API call
AC.S4.3: `GoogleAdapter.chat()` reads `request.cacheConfig?.providerPayload?.cachedContentName` and passes it as `providerOptions.google.cachedContent` to `streamText()`
AC.S4.4: Cache miss path (below 32,768 tokens) falls back to standard chat gracefully
AC.S4.5: `npx vitest run --reporter=verbose 2>&1 | tail -5` → 0 test failures
AC.S4.6: Unit test: mock `buildCacheCreatePayload()` call verifies payload structure

### F-S5: CI validation

AC.S5.1: `cd platform && npx vitest run 2>&1 | tail -10` → all pass, 0 failures
AC.S5.2: `npx tsc --noEmit 2>&1 | wc -l` → 0 TypeScript errors
AC.S5.3: Test count ≥ previous baseline (no test regressions)

### F-S6: PR + merge + deploy

AC.S6.1: `git push -u origin feature/r11f-wiring-arc` succeeds
AC.S6.2: PR created with title matching `feat(r11f): wire adapter.cache() + adapter.tools() into route.ts dispatch`
AC.S6.3: CI passes on PR (GitHub Actions)
AC.S6.4: PR auto-merged via `gh pr merge --squash --delete-branch --admin`
AC.S6.5: Cloud Run deploy triggered (deploy.yml push-to-main CI)

### F-S7: Governance close-out

AC.S7.1: `ROLLOUT_PHASE_R11F_RESULT.md` authored with per-flag gcloud flip commands
AC.S7.2: `STREAM_R11V2_COMPLETE.md §7` deferred items marked as COMPLETE
AC.S7.3: `CURRENT_STATE_v1_0.md` version bumped with R11.F arc completion note
AC.S7.4: `SESSION_LOG.md` entry appended
AC.S7.5: `.gemini/project_state.md` mirror updated (MP.2)
AC.S7.6: Deploy YAML updated: `MARSYS_FLAG_R11D_GEMINI_CACHE=true` added to `env_vars:`

## §5 — Hard constraints

1. NO MCP server touches (`platform-mcp/**` is must_not_touch).
2. NO changes to `adapter.ts` interface or `types.ts` ChatEvent definitions (already correct).
3. NO changes to `dispatcher.ts` or `capabilities.ts`.
4. Gemini cache creation uses raw `fetch()` to Gemini REST API (no new npm packages).
   OR uses `@ai-sdk/google` provider options if the SDK supports it natively.
5. Tool executor in route.ts uses the EXISTING MCP tool infrastructure — no new tool dispatch layer.
6. NO PR to main before Session 6. All work on `feature/r11f-wiring-arc`.
7. NO production flag flips — Session 7 surfaces commands only; operator flips manually.
8. `R11E_OPENAI_LOOP` is deferred if the OpenAI Responses API wiring is too complex.
   Ship Anthropic + Gemini + DeepSeek + NVIDIA loops; OpenAI can be a follow-up.

## §6 — Session 7 rollout surface

Session 7 authors `ROLLOUT_PHASE_R11F_RESULT.md` with:

```bash
# D.3 — Gemini cache (flip after 2-query log verification)
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11D_GEMINI_CACHE=true

# After verifying cachedContentTokenCount in logs:
# E.1 — Anthropic loop
gcloud run services update amjis-web --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11E_ANTHROPIC_LOOP=true
# 15-min watch, then E.2...
```

---
*R11V2_DISPATCH_WIRING_FULL_BRIEF_v1_0.md — authored 2026-05-23*
