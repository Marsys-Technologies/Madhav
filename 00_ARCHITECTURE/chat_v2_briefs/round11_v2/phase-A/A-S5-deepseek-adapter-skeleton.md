---
canonical_id: R11A_A_S5
session_id: A-S5
title: DeepSeek adapter skeleton + manifest declaration
phase: R11.A — Foundation
depends_on: [A-S1]
flag: FLAGLESS
client_side: "no — server-side adapter"
authored: 2026-05-22
---

# A-S5 — DeepSeek Adapter Skeleton

## Context

Per-provider adapter for DeepSeek. Wraps existing `deepseek_observed.ts` and **preserves the `extractReasoningMiddleware` from `resolver.ts`** that extracts `<think>...</think>` inline reasoning blocks into unified reasoning parts.

DeepSeek distinctives: inline `<think>` blocks (transparent CoT), OpenAI-compatible API, implicit prompt caching, low cost. Few server-side tools natively.

## Files in Scope

### Add

- `platform/src/lib/providers/deepseek/adapter.ts` — implements `CapabilityAdapter`. `chat()` wraps `deepseek_observed.ts` with the existing `extractReasoningMiddleware` from `resolver.ts` applied. Reasoning parts flow through unified ChatEvent stream.
- `platform/src/lib/providers/deepseek/manifest.ts`:
  ```typescript
  export const DEEPSEEK_MANIFEST: ProviderCapabilities = {
    extendedThinking: 'inline_blocks',  // <think>...</think>
    promptCaching: 'implicit',
    adaptiveToolLoop: 'finish_reason_tool_calls',  // OpenAI-compat
    interleavedThinkingTool: false,
    smoothStreaming: true,
    webSearch: null,
    webFetch: null,
    codeExecution: null,
    nativeMemory: null,
    inputImage: false,
    inputAudio: false,
    inputVideo: false,
    inputPdf: null,
    outputVoice: null,
    outputImage: null,
    computerUse: null,
    structuredOutputs: 'tool_force',
    maxContextTokens: 128_000,  // DeepSeek V3
  };
  ```
- `platform/tests/providers/deepseek/adapter.test.ts` — manifest match + chat ping-pong + verify `<think>` middleware still extracts reasoning.

### Modify

- `platform/src/lib/providers/deepseek/index.ts`

## Files MUST NOT Touch

- `platform/src/lib/models/resolver.ts` `extractReasoningMiddleware` setup (preserve verbatim — A-S5 USES this middleware, doesn't replace it)
- Existing `deepseek_observed.ts` (wrap)
- Other providers

## Acceptance Criteria

1. `DeepSeekAdapter` implements `CapabilityAdapter`.
2. Manifest declares DeepSeek capabilities (mostly limited — only thinking, basic chat, OpenAI-compat tool calls).
3. `chat()` wraps `deepseek_observed.ts` with `extractReasoningMiddleware` applied; `<think>` blocks extracted into unified reasoning parts.
4. Unsupported methods throw with phase pointer.
5. Tests verify reasoning extraction still works.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/deepseek/adapter.ts && echo "PASS"
grep -n "extractReasoningMiddleware\|<think>" src/lib/providers/deepseek/adapter.ts && echo "PASS: middleware preserved"
npx jest --testPathPattern="providers/deepseek|A-S5" --passWithNoTests
```

## Commit Template

```
feat(providers): DeepSeek adapter skeleton + manifest (A-S5)

Implements CapabilityAdapter for DeepSeek. Manifest declares DeepSeek
distinctives: inline <think> reasoning blocks, implicit prompt caching,
OpenAI-compatible tool calls, 128K context. Most server-side capabilities
declared null (no native server tools / no multimodal / no computer use).

chat() wraps existing deepseek_observed.ts WITH extractReasoningMiddleware
preserved verbatim from resolver.ts — reasoning extraction still works.

Flagless per §M.16.
```

## Decision Log

*(Executor: paste sample DeepSeek R1 response showing <think> extraction still works after the adapter wraps the call.)*
