---
canonical_id: R11A_A_S6
session_id: A-S6
title: NVIDIA NIM adapter skeleton + manifest declaration
phase: R11.A — Foundation
depends_on: [A-S1]
flag: FLAGLESS
client_side: "no — server-side adapter"
authored: 2026-05-22
---

# A-S6 — NVIDIA NIM Adapter Skeleton

## Context

Per-provider adapter for NVIDIA NIM. Wraps existing `nvidia.ts` and honors `NVIDIA_PLANNER_ENABLED=true`. NVIDIA NIM hosts many open-weight models; capabilities depend on which model is active.

NVIDIA distinctives: TensorRT-LLM optimized inference, model flexibility (different open-weight models via the same endpoint), currently used for the UQE planner per `NVIDIA_PLANNER_ENABLED=true`.

For R11.A, the manifest declares NVIDIA's capabilities at the lowest-common-denominator across hosted models (since model selection varies). Future R11 v2 phases may extend the manifest to be **model-aware** (e.g., declare per-model capabilities by querying the model id at request time).

## Files in Scope

### Add

- `platform/src/lib/providers/nvidia/adapter.ts` — implements `CapabilityAdapter`. `chat()` wraps `nvidia.ts`.
- `platform/src/lib/providers/nvidia/manifest.ts`:
  ```typescript
  export const NVIDIA_MANIFEST: ProviderCapabilities = {
    extendedThinking: null,  // depends on hosted model; conservative default
    promptCaching: null,
    adaptiveToolLoop: 'finish_reason_tool_calls',  // OpenAI-compat for most hosted models
    interleavedThinkingTool: false,
    smoothStreaming: true,
    webSearch: null,
    webFetch: null,
    codeExecution: null,
    nativeMemory: null,
    inputImage: false,  // depends on hosted model
    inputAudio: false,
    inputVideo: false,
    inputPdf: null,
    outputVoice: null,
    outputImage: null,
    computerUse: null,
    structuredOutputs: 'tool_force',
    maxContextTokens: 128_000,  // conservative default
  };
  ```
- `platform/tests/providers/nvidia/adapter.test.ts`

### Modify

- `platform/src/lib/providers/nvidia/index.ts`

## Files MUST NOT Touch

- Existing `nvidia.ts` (wrap)
- `NVIDIA_PLANNER_ENABLED` flag in `feature_flags.ts` (preserve true)
- Other providers
- Existing planner routing logic in `pipeline_planner.ts`

## Acceptance Criteria

1. `NvidiaAdapter` implements `CapabilityAdapter`.
2. Manifest declares conservative defaults; documented as "depends on hosted model" in inline comments.
3. `chat()` wraps `nvidia.ts` and emits unified ChatEvent.
4. `NVIDIA_PLANNER_ENABLED` path preserved — when active, the planner still routes UQE queries to NVIDIA via the adapter (no regression).
5. Unsupported methods throw with phase pointer + note about hosted-model variability.
6. Tests pass.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/nvidia/adapter.ts && echo "PASS"
grep -n "NVIDIA_PLANNER_ENABLED" src/lib/providers/nvidia/adapter.ts || echo "INFO: planner routing lives elsewhere — verify"
npx jest --testPathPattern="providers/nvidia|A-S6" --passWithNoTests
```

## Commit Template

```
feat(providers): NVIDIA NIM adapter skeleton + manifest (A-S6)

Implements CapabilityAdapter for NVIDIA NIM. Manifest declares conservative
capabilities (most null) since NIM hosts many open-weight models with varying
support. Future phases may extend to model-aware manifest.

chat() wraps existing nvidia.ts; NVIDIA_PLANNER_ENABLED path preserved
(planner routing unchanged).

Flagless per §M.16. Adapter substrate; behavior unchanged.
```

## Decision Log

*(Executor: confirm planner routing still flows NVIDIA-bound UQE queries through the new adapter; paste a sample planner trace.)*
