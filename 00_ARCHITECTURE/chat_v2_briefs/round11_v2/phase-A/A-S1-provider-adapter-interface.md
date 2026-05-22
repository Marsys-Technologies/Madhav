---
canonical_id: R11A_A_S1
session_id: A-S1
title: CapabilityAdapter interface — unified adapter contract across all providers
phase: R11.A — Foundation
depends_on: [A-S0]
flag: FLAGLESS
client_side: "no — type definitions"
authored: 2026-05-22
---

# A-S1 — Provider Adapter Interface

## Context

Now that the manifest exists (A-S0), this session defines the **`CapabilityAdapter` interface** — the unified contract every provider implements. The dispatcher (A-S7) routes capability calls into adapter methods; the migration adapter (A-S10) wraps the legacy pipeline as one of the adapter implementations.

Each capability gets one method on the interface. Method signatures are deliberately generic — they accept a typed request object and return a typed response. The actual provider-specific behavior lives in the adapter implementations (A-S2..A-S6 + A-S10).

## Files in Scope

### Add

- `platform/src/lib/providers/adapter.ts` — `CapabilityAdapter` interface. Methods:
  - `getManifest(): ProviderCapabilities`
  - `chat(request: ChatRequest): AsyncIterable<ChatEvent>` (streaming primary call)
  - `thinking(request: ThinkingRequest): ThinkingResponse` (configures thinking budget; called BEFORE chat)
  - `cache(request: CacheRequest): CacheResponse` (configures cache markers; called BEFORE chat)
  - `tools(request: ToolsRequest): ToolsResponse` (configures tool loop topology)
  - `webSearch(request: WebSearchRequest): Promise<WebSearchResult>` (server-side tool)
  - `webFetch(request: WebFetchRequest): Promise<WebFetchResult>`
  - `codeExecution(request: CodeExecutionRequest): Promise<CodeExecutionResult>`
  - `memory(request: MemoryRequest): Promise<MemoryResponse>` (read/write)
  - `multimodal(request: MultimodalRequest): MultimodalResponse` (modality routing)
  - `imageGeneration(request: ImageGenRequest): Promise<ImageGenResult>`
  - `computerUse(request: ComputerUseRequest): AsyncIterable<ComputerUseEvent>`
  - `structuredOutputs(request: StructuredOutputsRequest): StructuredOutputsResponse`
- `platform/src/lib/providers/types.ts` — typed request/response shapes for each capability (~12-15 small interface declarations)
- `platform/tests/providers/adapter-interface.test.ts` — type-only test that asserts the interface shape (TypeScript compile assertion)

## Files MUST NOT Touch

- Adapter implementations (A-S2..A-S6 own those)
- Existing model resolver

## Acceptance Criteria

1. `CapabilityAdapter` interface exists with all 13 methods above.
2. `types.ts` declares typed request/response shapes for each capability.
3. Methods that don't apply to a provider (e.g., a provider without server-side tools) accept the request but the implementation may throw `CapabilityUnsupportedError`. The interface itself remains contract-complete.
4. Streaming methods (`chat`, `computerUse`) return `AsyncIterable` for unified consumption.
5. Non-streaming methods (`webSearch`, `webFetch`, `codeExecution`, `memory`, `imageGeneration`) return `Promise<...>`.
6. Configuration methods (`thinking`, `cache`, `tools`, `multimodal`, `structuredOutputs`) return synchronous response objects (no async I/O).
7. Type-only test compiles cleanly.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/adapter.ts && echo "PASS"
test -f src/lib/providers/types.ts && echo "PASS"
npx tsc --noEmit 2>&1 | grep -E "error" | head -5
npx jest --testPathPattern="adapter-interface|A-S1" --passWithNoTests
```

## Commit Template

```
feat(providers): CapabilityAdapter interface (A-S1)

13-method interface that every provider adapter implements:
chat (streaming), thinking, cache, tools, webSearch, webFetch,
codeExecution, memory, multimodal, imageGeneration, computerUse,
structuredOutputs, getManifest.

Methods that don't apply to a provider throw CapabilityUnsupportedError;
the interface itself remains contract-complete.

Flagless per §M.16 (type definitions only).
```

## Decision Log

*(Executor: paste the final interface signature; document any method-shape choices made.)*
