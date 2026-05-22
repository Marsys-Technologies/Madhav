---
canonical_id: R11A_A_S7
session_id: A-S7
title: Capability dispatcher — central registry routing calls to adapters
phase: R11.A — Foundation
depends_on: [A-S2, A-S3, A-S4, A-S5, A-S6]
flag: MARSYS_FLAG_R11V2_USE_ADAPTERS
flag_default: true
client_side: "no — server-side dispatcher"
authored: 2026-05-22
---

# A-S7 — Capability Dispatcher

## Context

All 5 provider adapters exist (A-S2..A-S6). This session builds the **dispatcher** — the central registry that the chat surface calls. The chat surface never imports a specific adapter; it imports the dispatcher and asks for the active provider's capability.

The dispatcher:
1. Reads the active stack id from `runtime_config.ts` (existing per-request resolution path)
2. Looks up the corresponding adapter in a registry
3. Routes the capability call to the adapter
4. If the active stack throws `CapabilityUnsupportedError`, the dispatcher catches it and re-raises with provider/capability context for the UI to surface a "switch stack" hint

Gated by `MARSYS_FLAG_R11V2_USE_ADAPTERS` (default true). When flag=false, the chat surface bypasses the dispatcher and calls the legacy single-shot pipeline directly (rollback path). The migration adapter (A-S10) provides the legacy bridge.

## Files in Scope

### Add

- `platform/src/lib/providers/dispatcher.ts`:
  ```typescript
  import { ANTHROPIC_MANIFEST, AnthropicAdapter } from './anthropic';
  import { GOOGLE_MANIFEST, GoogleAdapter } from './google';
  // ...
  
  const ADAPTERS = {
    anthropic: { adapter: new AnthropicAdapter(), manifest: ANTHROPIC_MANIFEST },
    google: { adapter: new GoogleAdapter(), manifest: GOOGLE_MANIFEST },
    openai: { adapter: new OpenAIAdapter(), manifest: OPENAI_MANIFEST },
    deepseek: { adapter: new DeepSeekAdapter(), manifest: DEEPSEEK_MANIFEST },
    nvidia: { adapter: new NvidiaAdapter(), manifest: NVIDIA_MANIFEST },
  };
  
  export function getAdapter(stackId: StackId): CapabilityAdapter {
    return ADAPTERS[stackId].adapter;
  }
  
  export function getManifest(stackId: StackId): ProviderCapabilities {
    return ADAPTERS[stackId].manifest;
  }
  
  export async function dispatch<T>(
    capability: keyof CapabilityAdapter,
    request: any,
    stackId: StackId
  ): Promise<T> {
    const adapter = getAdapter(stackId);
    try {
      // @ts-ignore — runtime dispatch
      return await adapter[capability](request);
    } catch (e) {
      if (e instanceof CapabilityUnsupportedError) {
        // Re-raise with dispatch context for UI hint
        throw new CapabilityUnsupportedOnStackError(capability, stackId, e.message);
      }
      throw e;
    }
  }
  ```
- `platform/tests/providers/dispatcher.test.ts` — tests dispatch routes correctly per stack id; throws on unknown stack; surfaces unsupported-capability errors with stack context.

### Modify

- `platform/src/app/api/chat/consume/route.ts` — gate the chat call: when `MARSYS_FLAG_R11V2_USE_ADAPTERS=true`, call `dispatch('chat', request, stackId)`; when false, call legacy path. (Legacy path stays the default until A-S10 verifies migration adapter preserves behavior.)
- `platform/src/lib/config/feature_flags.ts` — confirm `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` declaration from A-S0.

## Files MUST NOT Touch

- Individual adapters (A-S2..A-S6 own them; this session uses them)
- Legacy pipeline code (A-S10 wraps it)
- UI components

## Acceptance Criteria

1. `dispatcher.ts` exports `getAdapter()`, `getManifest()`, `dispatch()`.
2. The registry maps all 5 stack ids to their adapters.
3. `dispatch()` routes calls to the active adapter's method and re-raises unsupported errors with stack context.
4. `route.ts` gates on `MARSYS_FLAG_R11V2_USE_ADAPTERS` — both code paths (dispatcher vs legacy) are reachable and tested.
5. Flag default `true`: dispatcher path active. Tests assert this.
6. Flag=false fallback: legacy path returns byte-identical responses (regression test).
7. Tests pass.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/dispatcher.ts && echo "PASS"
grep -n "MARSYS_FLAG_R11V2_USE_ADAPTERS" src/app/api/chat/consume/route.ts && echo "PASS: route gated"
grep -rn "NEXT_PUBLIC.*USE_ADAPTERS" src --include="*.ts*" && echo "FAIL: should be server-side" || echo "PASS"
npx jest --testPathPattern="dispatcher|A-S7" --passWithNoTests
```

## Commit Template

```
feat(providers): capability dispatcher with 5-adapter registry (A-S7)

Dispatcher routes capability calls to the active stack's adapter. Re-raises
CapabilityUnsupportedError with stack context so UI can surface "switch
stack" hints.

route.ts gated on MARSYS_FLAG_R11V2_USE_ADAPTERS (default true; server-side).
Legacy single-shot path preserved as flag=false rollback.

Flag guard: with flag=false, route.ts uses legacy path verbatim (regression
tests verify byte-identical responses).
```

## Decision Log

*(Executor: paste dispatch trace for a sample query showing routing through Anthropic adapter; confirm legacy path still works with flag=false.)*
