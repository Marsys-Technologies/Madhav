---
canonical_id: R11A_A_S12
session_id: A-S12
title: Foundation E2E tests — 5-provider smoke + capability manifest validation
phase: R11.A — Foundation
depends_on: [A-S11]
flag: FLAGLESS
client_side: "no — test infrastructure"
authored: 2026-05-22
---

# A-S12 — Foundation E2E Tests

## Context

R11.A is complete only if the substrate works end-to-end on **all 5 providers**. This session writes:

1. **Adapter-contract test** — every adapter implements the full `CapabilityAdapter` interface (TypeScript compile + runtime method-existence check)
2. **Manifest-validation test** — every adapter's declared manifest passes `validateManifest()`
3. **5-provider smoke test** — for each stack id, a real adapter dispatch (against a mocked SDK or staging endpoint) returns the expected ChatEvent shape
4. **Hide-and-hint integration test** — `CapabilityHint` renders correctly given each manifest
5. **Telemetry integration test** — `logCapabilityPath()` fires on every dispatch and the SSE part is emitted

This is the gate that flips `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` confidently and that gates R11A-MERGE.

## Files in Scope

### Add

- `platform/tests/providers/foundation-smoke.test.ts` — 5-provider smoke. Each stack:
  - dispatch a `chat()` call with a fixed prompt
  - assert ChatEvent stream returns
  - assert manifest is readable
  - assert telemetry record was written
- `platform/tests/providers/adapter-contract.test.ts` — for each adapter, verify all 13 methods exist and have the correct signature (`typeof adapter.chat === 'function'`, etc.).
- `platform/tests/providers/manifest-validation.test.ts` — every manifest passes `validateManifest()`; manifest fields match CAPABILITY_MATRIX expectations (single source of truth match-up).
- `platform/tests/components/chat/CapabilityHint.integration.test.tsx` — render CapabilityHint with each of the 5 manifests; verify supported-vs-hidden behavior.
- `platform/tests/observatory/capability_telemetry.integration.test.ts` — dispatch a call; assert `logCapabilityPath()` was invoked and SSE part emitted.

### Modify

- `platform/jest.config.ts` (or equivalent) — confirm the new test paths are included in the default run; add a `--testPathPattern="providers|capabilityHint|capability_telemetry"` script for targeted runs.

## Files MUST NOT Touch

- Adapter implementations (A-S2..A-S6 + A-S10 own those)
- Production code

## Acceptance Criteria

1. All 5 adapter-contract tests pass.
2. All 5 manifest-validation tests pass; declared manifests match CAPABILITY_MATRIX values.
3. 5-provider smoke test passes on at minimum mocked SDKs; if staging endpoint access is available, integration smoke runs against staging.
4. CapabilityHint integration test passes (hides correctly per each manifest).
5. Telemetry integration test passes (record written + SSE part emitted).
6. Test suite reports: "R11.A foundation: 5/5 stacks PASS, capability manifests valid, telemetry firing, hide-and-hint working."
7. **Gate:** `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is confirmed-safe by this session. If any of the 5 smoke tests fails, A-S12 HALTS — R11A-MERGE cannot proceed.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
# All five adapters present + contracts satisfied
for p in anthropic google openai deepseek nvidia; do
  test -f src/lib/providers/$p/adapter.ts && test -f src/lib/providers/$p/manifest.ts && echo "PASS: $p adapter+manifest"
done
# Tests pass
npx jest --testPathPattern="providers|capability_telemetry|CapabilityHint" --passWithNoTests
# Final smoke
npx jest --testPathPattern="foundation-smoke" --passWithNoTests
```

## Commit Template

```
test(providers): R11.A foundation E2E tests — 5-provider smoke (A-S12)

5 test suites:
- adapter-contract: every adapter implements full CapabilityAdapter
- manifest-validation: every manifest validates + matches CAPABILITY_MATRIX
- foundation-smoke: 5-provider ChatEvent round-trip (mocked SDKs)
- CapabilityHint.integration: hide-and-hint across all 5 manifests
- capability_telemetry.integration: dispatch fires telemetry + emits SSE

Gates R11A-MERGE: if any smoke test fails, the phase halts.
```

## Decision Log

*(Executor: paste full test report — 5 stacks × 5 test suites. If any failures, document remediation before R11A-MERGE proceeds.)*
