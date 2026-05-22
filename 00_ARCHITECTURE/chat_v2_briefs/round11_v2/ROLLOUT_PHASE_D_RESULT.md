---
artifact: ROLLOUT_PHASE_D_RESULT
version: 1.0
status: FINAL
created: 2026-05-23
session: R11V2-Phase-DE-Resume
---

# R11.D Production Flag Rollout — Phase D Final Result

## Summary

| Flag | Flipped | Verification | Result |
|---|---|---|---|
| `MARSYS_FLAG_R11D_PROMPT_LAYOUT` | ✅ true (deploy.yml + rev 356) | Layout visible in prod | **PASS** |
| `MARSYS_FLAG_R11D_ANTHROPIC_CACHE` | ✅ true (deploy.yml + rev 356) | D.2 waived by operator | **WAIVED** |
| `MARSYS_FLAG_R11D_GEMINI_CACHE` | ✅ true (rev 357) → **rolled back false** | NOT IMPLEMENTED | **ROLLBACK** |

## D.1 — MARSYS_FLAG_R11D_PROMPT_LAYOUT

**Result: PASS**

Flipped `true` in `deploy.yml` env_vars block via commit `fbe8ff32`. Live on revision
`amjis-web-00356-xxx`. Flag correctly enables the `prompt_assembler.ts` cache-aware prompt
layout path. No adverse effects observed.

## D.2 — MARSYS_FLAG_R11D_ANTHROPIC_CACHE

**Result: WAIVED**

Flipped `true` in `deploy.yml` env_vars block via commit `fbe8ff32`. Live on revision 356.
D.2 2-query cache verification waived by operator (prior session cache check not confirmed;
operator approved waiver per ROLLOUT_DE_RESUME_PREFLIGHT.md §3).

The Anthropic adapter's `cache()` method and `prompt_assembler.ts` 4-breakpoint
`cache_control` injection are correctly implemented. Cache metrics flow via
`extractAnthropicCacheMetrics()` to Observatory. The flag gates the prompt layout path
that injects breakpoints — with `PROMPT_LAYOUT=true`, cache_control markers are present
in the assembled prompt.

## D.3 — MARSYS_FLAG_R11D_GEMINI_CACHE

**Result: NOT IMPLEMENTED — ROLLED BACK**

### Finding

The flag was flipped `true` on revision `amjis-web-00357-7ng`. Operator sent 2 long-context
Google queries for cache verification. Log check returned no `cachedContentTokenCount` entries
for provider=google.

Root cause investigation confirmed: `MARSYS_FLAG_R11D_GEMINI_CACHE` is a **stub**.

Evidence:
1. `grep -rn "R11D_GEMINI_CACHE" platform/src/` → found ONLY in `feature_flags.ts` (declaration + default)
2. `grep -n "R11D_GEMINI_CACHE|gemini_cache|GEMINI_CACHE|adapter\.cache" route.ts` → **zero matches**
3. Route.ts adapter dispatch block (lines 905–988) calls only `adapter.chat(adapterChatReq)` —
   `adapter.cache()` is never called.
4. Google adapter `cache()` method (adapter.ts:148) returns a `CacheResponse` config object
   specifying `sdkMethod: 'genai.caches.create'`, but route.ts has no code to consume this
   return value or call `genai.caches.create()`.

### Architecture gap

The R11.D Phase D-S2 implementation established the Gemini adapter `cache()` method as a
spec/config layer. The corresponding route.ts integration — which would:
  1. Call `adapter.cache()` to get the CacheResponse
  2. Check the 32,768-token minimum threshold
  3. Call `genai.caches.create()` with the system prompt + RAG bundle
  4. Pass `cachedContent: "cachedContents/abc123"` to the model request
  5. Extract `cachedContentTokenCount` for Observatory

— was NOT implemented. The capability method exists but is not connected to the execution path.

### Disposition

Per rollout rules: FAIL → rollback `MARSYS_FLAG_R11D_GEMINI_CACHE=false`, HALT.

Rollback executed:
```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars MARSYS_FLAG_R11D_GEMINI_CACHE=false
```

Flag status on production: `false` (restored to default).

D.3 is recorded as a **deferred implementation item** for R11.D follow-up arc. The adapter
method spec is correct; only the route.ts integration layer is missing.

## E.1–E.4 — R11E_*_LOOP flags

**Result: ALL NOT IMPLEMENTED — DO NOT FLIP**

Same architecture gap extends to all E-phase flags. `adapter.loop()` methods exist on all
5 adapters and return `LoopResponse` config objects. Route.ts adapter dispatch block does
NOT call `adapter.loop()` — the agentic loop engine (`platform/src/lib/synthesis/agentic_loop.ts`)
exists but is not invoked from the dispatch path.

Evidence:
- `grep -rn "R11E_ANTHROPIC_LOOP|R11E_GEMINI_LOOP|R11E_DEEPSEEK_LOOP|R11E_NVIDIA_LOOP" route.ts` → **zero matches**
- `grep -rn "agentic_loop" platform/src/lib/providers/` → only in comments inside adapter files (not imports)
- Adapter imports: anthropic/adapter.ts imports only `streamText`, `anthropic as anthropicProvider`, `ANTHROPIC_MANIFEST` — no agentic_loop import

None of the E flags (E.1–E.4) were flipped. Correct decision — flipping would have no effect
and would mislead monitoring.

## Production state at close of Phase D rollout

| Flag | Value | Source |
|---|---|---|
| `MARSYS_FLAG_R11V2_USE_ADAPTERS` | `true` | deploy.yml env_vars |
| `MARSYS_FLAG_R11D_PROMPT_LAYOUT` | `true` | deploy.yml env_vars |
| `MARSYS_FLAG_R11D_ANTHROPIC_CACHE` | `true` | deploy.yml env_vars |
| `MARSYS_FLAG_R11D_GEMINI_CACHE` | `false` | rolled back via gcloud |
| `MARSYS_FLAG_R11E_ANTHROPIC_LOOP` | `false` | default (never flipped) |
| `MARSYS_FLAG_R11E_GEMINI_LOOP` | `false` | default (never flipped) |
| `MARSYS_FLAG_R11E_DEEPSEEK_LOOP` | `false` | default (never flipped) |
| `MARSYS_FLAG_R11E_NVIDIA_LOOP` | `false` | default (never flipped) |

## Deferred items

1. **D.3 Gemini cache route.ts integration** — implement the `adapter.cache()` → `genai.caches.create()`
   → pass `cachedContent` ID to model request flow in route.ts. Minimum token threshold check (32,768).
   Observable via `cachedContentTokenCount` in usage metadata.
2. **E.1–E.4 agentic loop route.ts integration** — implement `adapter.loop()` invocation from
   the dispatch block; integrate `agentic_loop.ts` engine into the adapter dispatch path for
   all 5 providers.

Both items are R11.F-arc work — not blockers for the R11.A–E substrate close.
