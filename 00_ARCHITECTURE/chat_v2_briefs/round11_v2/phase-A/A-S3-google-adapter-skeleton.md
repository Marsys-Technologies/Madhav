---
canonical_id: R11A_A_S3
session_id: A-S3
title: Google (Gemini) adapter skeleton + manifest declaration
phase: R11.A — Foundation
depends_on: [A-S1]
flag: FLAGLESS
client_side: "no — server-side adapter"
authored: 2026-05-22
---

# A-S3 — Google (Gemini) Adapter Skeleton

## Context

Per-provider adapter for Google. Wraps the existing `gemini_observed.ts` SDK calls in the `CapabilityAdapter` shape (A-S1) and declares Gemini's `ProviderCapabilities` manifest (A-S0).

Gemini's distinctives: native multimodal (image + audio + video), `cachedContent` API, Google Search grounding, native `thinking` parts, 2M-token context (Gemini 2.5 Pro), Imagen for image generation.

## Files in Scope

### Add

- `platform/src/lib/providers/google/adapter.ts` — implements `CapabilityAdapter`. `chat()` wraps `gemini_observed.ts`; other methods throw `CapabilityUnsupportedError`.
- `platform/src/lib/providers/google/manifest.ts`:
  ```typescript
  export const GOOGLE_MANIFEST: ProviderCapabilities = {
    extendedThinking: 'native_budget',  // thinkingBudget: 24576
    promptCaching: 'cached_content_api',
    adaptiveToolLoop: 'finish_reason_function_calls',
    interleavedThinkingTool: true,  // Gemini 2.5 Pro
    smoothStreaming: true,
    webSearch: 'grounding',
    webFetch: null,
    codeExecution: 'first_party',
    nativeMemory: 'workspace',
    inputImage: true,
    inputAudio: true,
    inputVideo: true,
    inputPdf: 'files_api',
    outputVoice: 'live_api',
    outputImage: 'imagen',
    computerUse: null,
    structuredOutputs: 'response_schema',
    maxContextTokens: 2_000_000,  // Gemini 2.5 Pro
  };
  ```
- `platform/tests/providers/google/adapter.test.ts` — manifest match + chat ping-pong + unsupported-method throws.

### Modify

- `platform/src/lib/providers/google/index.ts` — re-export adapter + manifest

## Files MUST NOT Touch

- Existing `gemini_observed.ts` (wrap, don't modify)
- Existing `thinkingBudget` config in `registry.ts` (preserve verbatim)
- Other providers' adapters
- DeepSeek `<think>` middleware

## Acceptance Criteria

1. `GoogleAdapter` implements `CapabilityAdapter`.
2. Manifest declares all Gemini capabilities per CAPABILITY_MATRIX.
3. `chat()` wraps `gemini_observed.ts` and emits unified `ChatEvent`s.
4. Existing `thinkingBudget: 24576` from `registry.ts` is respected when the adapter's `thinking()` method is invoked (preserves R10-era Gemini path).
5. Native reasoning parts (Gemini `type: 'reasoning'` UIMessage parts) flow through the adapter unchanged into the unified ChatEvent stream.
6. Unsupported methods throw with phase pointer.
7. Tests pass.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/google/adapter.ts && echo "PASS"
test -f src/lib/providers/google/manifest.ts && echo "PASS"
grep -n "thinkingBudget\|thoughtsTokenCount" src/lib/providers/google/adapter.ts && echo "PASS: existing path preserved"
npx jest --testPathPattern="providers/google|A-S3" --passWithNoTests
```

## Commit Template

```
feat(providers): Google (Gemini) adapter skeleton + manifest (A-S3)

Implements CapabilityAdapter for Google. Manifest declares Gemini distinctives:
thinkingBudget integer thinking, cachedContent API, Google Search grounding,
native multimodal (image+audio+video), Live API voice, Imagen image gen,
2M context window.

chat() wraps existing gemini_observed.ts; thinkingBudget=24576 path from
registry.ts preserved verbatim. Unsupported methods throw with phase pointer.

Flagless per §M.16.
```

## Decision Log

*(Executor: confirm Gemini reasoning parts flow through unchanged; paste before/after of a sample reasoning-tagged response.)*
