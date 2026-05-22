---
canonical_id: R11A_A_S2
session_id: A-S2
title: Anthropic adapter skeleton + manifest declaration
phase: R11.A — Foundation
depends_on: [A-S1]
flag: FLAGLESS
client_side: "no — server-side adapter"
authored: 2026-05-22
---

# A-S2 — Anthropic Adapter Skeleton

## Context

First per-provider adapter. Implements the `CapabilityAdapter` interface (A-S1) for Anthropic, declares its `ProviderCapabilities` manifest (A-S0), and wraps the existing `anthropic_observed.ts` SDK calls in the new adapter shape.

This is a **skeleton** — actual capability implementations (cache, thinking, tools, server-tools) are added incrementally by later phases (R11.D, R11.E, R11.F, etc.). For R11.A, the adapter must expose the manifest correctly and route `chat()` calls to the existing observed wrapper. Other methods throw `CapabilityUnsupportedError` with a clear message until their phase ships.

## Files in Scope

### Add

- `platform/src/lib/providers/anthropic/adapter.ts` — implements `CapabilityAdapter`. Methods:
  - `getManifest()` returns the declared manifest (see Add below)
  - `chat(request)` wraps `anthropic_observed.ts` SDK call; emits unified `ChatEvent` shape
  - All other capability methods throw `CapabilityUnsupportedError` with phase pointer (e.g., "Anthropic prompt caching ships in R11.D")
- `platform/src/lib/providers/anthropic/manifest.ts` — declares the Anthropic `ProviderCapabilities`:
  ```typescript
  export const ANTHROPIC_MANIFEST: ProviderCapabilities = {
    extendedThinking: 'native_effort',  // Opus 4.6+ / Sonnet 4.6+
    promptCaching: 'explicit_4bp',
    adaptiveToolLoop: 'stop_reason',
    interleavedThinkingTool: true,
    smoothStreaming: true,
    webSearch: 'first_party',
    webFetch: 'first_party',
    codeExecution: 'first_party',
    nativeMemory: 'memory_tool',  // Claude 4.5+
    inputImage: true,
    inputAudio: false,
    inputVideo: false,
    inputPdf: 'files_api',
    outputVoice: null,
    outputImage: null,
    computerUse: 'computer_use_api',
    structuredOutputs: 'tool_force',
    maxContextTokens: 1_000_000,  // Sonnet 4.6 / Opus 4.7 Enterprise
  };
  ```
- `platform/tests/providers/anthropic/adapter.test.ts` — asserts manifest matches CAPABILITY_MATRIX, asserts `chat()` ping-pong works against a mocked SDK, asserts unsupported methods throw the expected error.

### Modify

- `platform/src/lib/providers/anthropic/index.ts` — re-export adapter + manifest (or create if doesn't exist)

## Files MUST NOT Touch

- Existing `anthropic_observed.ts` (preserve verbatim; the adapter WRAPS it)
- Other providers' adapter directories (A-S3..A-S6 own those)
- The legacy single-shot pipeline (A-S10 owns that)

## Acceptance Criteria

1. `AnthropicAdapter` class implements `CapabilityAdapter`.
2. Manifest matches CAPABILITY_MATRIX cells for Anthropic — every field declared with the documented value.
3. `chat()` successfully wraps `anthropic_observed.ts`; a mocked stream round-trip returns expected `ChatEvent`s.
4. Unsupported methods throw `CapabilityUnsupportedError` with a message that names the future phase (e.g., "Anthropic prompt caching ships in R11.D").
5. `validateManifest(ANTHROPIC_MANIFEST)` passes at module load.
6. Tests pass.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/anthropic/adapter.ts && echo "PASS"
test -f src/lib/providers/anthropic/manifest.ts && echo "PASS"
grep -n "validateManifest" src/lib/providers/anthropic/manifest.ts && echo "PASS"
npx jest --testPathPattern="providers/anthropic|A-S2" --passWithNoTests
```

## Commit Template

```
feat(providers): Anthropic adapter skeleton + manifest (A-S2)

Implements CapabilityAdapter for Anthropic. Manifest declares all
capabilities per CAPABILITY_MATRIX cells (extendedThinking=native_effort,
promptCaching=explicit_4bp, adaptiveToolLoop=stop_reason, all server tools,
1M context, computer use, etc.).

chat() wraps existing anthropic_observed.ts SDK call; unsupported methods
throw CapabilityUnsupportedError until their future phase ships.

Flagless per §M.16 (foundational substrate).
```

## Decision Log

*(Executor: paste final manifest. Document any cells that differ from CAPABILITY_MATRIX with rationale.)*
