---
canonical_id: R11A_A_S8
session_id: A-S8
title: UI capability-availability surface — manifest reader + "switch stack" hint affordance
phase: R11.A — Foundation
depends_on: [A-S7]
flag: FLAGLESS
client_side: "yes — additive UI component"
authored: 2026-05-22
---

# A-S8 — UI Capability-Availability Surface

## Context

The dispatcher (A-S7) raises `CapabilityUnsupportedOnStackError` when the active stack doesn't support a capability. This session builds the **UI affordance reader** — a small component that consumes the active provider's manifest and either:

1. **Renders the feature button** (when the manifest declares support)
2. **Hides the button + shows a tooltip** ("This stack doesn't support web search — switch to Anthropic, Google, or OpenAI to use this.") (when manifest declares null)

Per `NATIVE_RULINGS §8`-equivalent fallback policy locked 2026-05-22.

This session builds the component but doesn't wire it to any feature button yet — feature wiring happens in later phases (R11.B for visual affordances, R11.F for server-tool buttons, R11.I for multimodal buttons). A-S8 establishes the pattern.

## Files in Scope

### Add

- `platform/src/components/chat/CapabilityHint.tsx`:
  ```tsx
  interface CapabilityHintProps {
    capability: keyof ProviderCapabilities;
    activeStack: StackId;
    children: React.ReactNode;  // The feature button or affordance
  }
  
  export function CapabilityHint({ capability, activeStack, children }: CapabilityHintProps) {
    const manifest = useProviderManifest(activeStack);  // Hook below
    const supported = manifest[capability] !== null && manifest[capability] !== false;
    if (supported) return <>{children}</>;
    // Hide affordance; show small chip with switch-stack hint
    const supportingStacks = getStacksSupporting(capability);  // Static helper
    return (
      <div className="capability-hint-chip" role="status">
        <span>Switch to {supportingStacks.join(' or ')} to use this</span>
      </div>
    );
  }
  ```
- `platform/src/lib/chat-v2/useProviderManifest.ts` — React hook that reads the active stack id from existing context and returns the manifest from the dispatcher.
- `platform/src/lib/providers/manifest-helpers.ts` — utility `getStacksSupporting(capability)` that iterates the 5 manifests at module load and returns the supporting stacks for any capability.
- `platform/tests/components/chat/CapabilityHint.test.tsx` — parent-context tests:
  - When manifest declares support, `children` render.
  - When manifest declares null, chip renders with "Switch to <list>" text.
  - When manifest has 1 supporter, chip says "Switch to <stack> to use this".
  - When manifest has multiple supporters, chip says "Switch to A, B, or C".

### Modify

- `platform/src/app/globals.css` — add `.capability-hint-chip` style block inside `.consume-shell` scope: small pill, Marsys gold-hairline border, muted text. Per `NATIVE_RULINGS §1` preserve Marsys palette.

## Files MUST NOT Touch

- Any feature button (no wiring yet)
- `.consume-shell` block structure (we add a sub-style; we don't restructure)
- Phase 4C files

## Acceptance Criteria

1. `CapabilityHint` component exists and passes through children when supported.
2. When unsupported, renders the chip with correct copy.
3. `useProviderManifest` reads the active stack id from existing context and returns the right manifest.
4. `.capability-hint-chip` style matches Marsys palette (gold-hairline border + muted text + small padding).
5. Tests cover all 4 paths (supported / 1-supporter / multi-supporter / none).
6. Click-path documented: feature wired in later phases will wrap its button in `<CapabilityHint capability="webSearch" activeStack={stack}>{webSearchButton}</CapabilityHint>` and the hint logic handles visibility.
7. Parent-context integration test mounts component inside `ConsumeChatV2` simulated context with varied stack ids; asserts correct render.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/components/chat/CapabilityHint.tsx && echo "PASS"
test -f src/lib/chat-v2/useProviderManifest.ts && echo "PASS"
test -f src/lib/providers/manifest-helpers.ts && echo "PASS"
grep -n "capability-hint-chip" src/app/globals.css && echo "PASS: style declared"
npx jest --testPathPattern="CapabilityHint|useProviderManifest|A-S8" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): CapabilityHint UI surface + manifest reader hook (A-S8)

CapabilityHint passes through children when active stack supports the
capability; renders a small "Switch to <stack>" pill when not. Reads
manifest via useProviderManifest hook backed by dispatcher (A-S7).

Style block scoped to .consume-shell with Marsys gold-hairline border;
palette preserved per NATIVE_RULINGS §1.

Flagless per §M.16 (additive UI component; no feature wiring yet —
later phases wrap their buttons).
```

## Decision Log

*(Executor: paste before/after screenshot of a feature button wrapped in CapabilityHint with manifest=null. Document the chip copy chosen.)*
