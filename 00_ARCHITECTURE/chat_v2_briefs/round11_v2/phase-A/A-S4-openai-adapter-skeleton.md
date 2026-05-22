---
canonical_id: R11A_A_S4
session_id: A-S4
title: OpenAI adapter skeleton + manifest declaration
phase: R11.A — Foundation
depends_on: [A-S1]
flag: FLAGLESS
client_side: "no — server-side adapter"
authored: 2026-05-22
---

# A-S4 — OpenAI Adapter Skeleton

## Context

Per-provider adapter for OpenAI. Wraps the existing `openai_observed.ts` calls (which uses both Chat Completions + Responses APIs) in the `CapabilityAdapter` shape and declares OpenAI's manifest.

OpenAI distinctives: automatic prompt caching (no markers), Code Interpreter, `web_search_preview` tool via Responses API, Computer Use Agent (CUA), DALL-E / gpt-image-1 image gen, structured outputs with strict JSON schema.

## Files in Scope

### Add

- `platform/src/lib/providers/openai/adapter.ts` — implements `CapabilityAdapter`. `chat()` wraps `openai_observed.ts`; other methods throw until phase ships.
- `platform/src/lib/providers/openai/manifest.ts`:
  ```typescript
  export const OPENAI_MANIFEST: ProviderCapabilities = {
    extendedThinking: 'polyfill_cot',  // o-series removed from codebase; CoT polyfill via system prompt
    promptCaching: 'automatic',
    adaptiveToolLoop: 'finish_reason_tool_calls',
    interleavedThinkingTool: false,  // Responses API supports loop but not interleaved thinking
    smoothStreaming: true,
    webSearch: 'preview_api',
    webFetch: null,
    codeExecution: 'first_party',
    nativeMemory: 'product_only',  // Memory exists in ChatGPT, not OpenAI API
    inputImage: true,
    inputAudio: true,  // Audio Preview models
    inputVideo: false,  // partial; frame-by-frame only
    inputPdf: 'files_api',
    outputVoice: 'tts_streaming',
    outputImage: 'gpt_image',  // or 'dalle' depending on model
    computerUse: 'cua_responses',
    structuredOutputs: 'json_schema_strict',
    maxContextTokens: 200_000,  // GPT-4.1
  };
  ```
- `platform/tests/providers/openai/adapter.test.ts`

### Modify

- `platform/src/lib/providers/openai/index.ts`

## Files MUST NOT Touch

- Existing `openai_observed.ts` (wrap)
- Other providers
- The Responses API integration (if used elsewhere — preserve)

## Acceptance Criteria

1. `OpenAIAdapter` implements `CapabilityAdapter`.
2. Manifest declares OpenAI distinctives per CAPABILITY_MATRIX.
3. `chat()` wraps `openai_observed.ts` and emits unified ChatEvent.
4. Stream-options injection (`stream_options.include_usage=true`) preserved from existing adapter behavior.
5. Unsupported methods throw with phase pointer.
6. Tests pass.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/openai/adapter.ts && echo "PASS"
test -f src/lib/providers/openai/manifest.ts && echo "PASS"
grep -n "stream_options\|include_usage" src/lib/providers/openai/adapter.ts && echo "PASS: usage-include preserved"
npx jest --testPathPattern="providers/openai|A-S4" --passWithNoTests
```

## Commit Template

```
feat(providers): OpenAI adapter skeleton + manifest (A-S4)

Implements CapabilityAdapter for OpenAI. Manifest declares OpenAI distinctives:
automatic prompt caching (no markers), Code Interpreter, web_search_preview
(Responses API), CUA computer use, gpt-image-1 generation, json_schema strict
structured outputs, 200K context.

extendedThinking declared as 'polyfill_cot' since o-series was removed from
codebase; future R11.C may add CoT system-prompt nudge.

chat() wraps existing openai_observed.ts; stream-options usage-include
preserved. Unsupported methods throw with phase pointer.

Flagless per §M.16.
```

## Decision Log

*(Executor: confirm o-series removal status; document the CoT polyfill design choice.)*
