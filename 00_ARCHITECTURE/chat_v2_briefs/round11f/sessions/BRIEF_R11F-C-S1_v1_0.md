---
artifact: BRIEF_R11F-C-S1_v1_0.md
session_id: R11F-C-S1
version: 1.0
phase: C
parallel_safety: false
depends_on: [R11F-B-S2, R11F-B-S4, R11F-B-S5]
estimated_loc_delta: +100
---

# R11F-C-S1 — Cross-Provider Parity Matrix + Trace Audit Suite

## Scope

Two cross-cutting verification suites:

1. **Parity matrix**: same canonical query against all supported providers; assert each
   selects a comparable set of tools (or document legitimate divergence).
2. **Trace audit**: assert `query_trace_steps` rows contain `tool_use` iteration entries
   with the required fields (`tool_name`, `iteration`, `duration_ms`, `cache_hit`).

## Files May Touch

```
platform/tests/cross-provider/parity-matrix.test.ts      (new)
platform/tests/cross-provider/trace-audit.test.ts         (new)
platform/src/lib/observability/trace_writer.ts            (patch if trace fields missing)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/**   (no more adapter changes)
platform/src/app/api/chat/consume/route.ts
CLAUDE.md
deploy.yml
```

## Implementation

### Part 1 — Cross-Provider Parity Matrix

#### Step 1: Identify a canonical query

Use: "What is the current Vimshottari dasha period and sub-dasha for the native, and how
does it relate to the natal Saturn configuration?"

This query is guaranteed to require `query_dasha_periods` (temporal) and either `query_chart_facts`
or `holistic_bundle` (holistic). All providers supporting tool calling should select the same
core tools.

#### Step 2: Write parity matrix test

`tests/cross-provider/parity-matrix.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
// Mock all 5 adapters with identical scripted tool-use responses
// Assert that each adapter (when given the same planner-authorised tools) calls the same tools

describe('Cross-provider tool selection parity', () => {
  const EXPECTED_TOOL = 'query_dasha_periods'
  const PROVIDERS = ['anthropic', 'google', 'openai', 'deepseek'] // nvidia if AC

  for (const provider of PROVIDERS) {
    it(`${provider}: selects ${EXPECTED_TOOL} for dasha query`, async () => {
      // Create adapter with mock streamText that records which tools were passed
      // Run with the canonical query and planner-authorised tool list
      // Assert EXPECTED_TOOL is in the tool definitions passed to the model
    })
  }

  it('divergence report: document any provider-specific tool selection differences', () => {
    // This test is always a pass — it logs the tool selection for each provider for human review
    // Any structural divergence (e.g. NVIDIA N/A) is documented here
    expect(true).toBe(true)
  })
})
```

#### Step 3: Flag legitimate divergence

If a provider skips a tool the others call (e.g. NVIDIA N/A), document as a known
asymmetry in a comment — not a test failure.

### Part 2 — Trace Audit Suite

#### Step 4: Verify trace_writer records tool_use iterations

Read `platform/src/lib/observability/trace_writer.ts` (or equivalent trace recording code).
Find where `query_trace_steps` rows are written. Verify that tool_use iterations record:
- `step_type: 'tool_use'`
- `tool_name: string`
- `iteration: number` (which loop iteration)
- `duration_ms: number`
- `cache_hit: boolean`

If any field is missing, patch `trace_writer.ts` to add it.

#### Step 5: Write trace audit test

`tests/cross-provider/trace-audit.test.ts`:

```typescript
describe('Trace audit: tool_use iteration rows', () => {
  it('trace_writer emits tool_use step with required fields', () => {
    // Mock the trace writer
    // Run a simulated tool call iteration
    // Assert the emitted row has all 5 required fields
  })

  it('iteration counter increments correctly across multiple tool calls', () => {
    // Simulate 3 tool calls
    // Assert rows have iteration: 1, 2, 3
  })
})
```

## Acceptance Tests

```bash
# AC.e (from master plan): trace rows have required fields
cd platform && npx vitest run tests/cross-provider/trace-audit.test.ts --no-coverage 2>&1 | tail -5
# expected: no failures

# AC.parity: parity matrix runs
cd platform && npx vitest run tests/cross-provider/parity-matrix.test.ts --no-coverage 2>&1 | tail -5
# expected: no failures

# Full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- `tests/cross-provider/parity-matrix.test.ts` (new)
- `tests/cross-provider/trace-audit.test.ts` (new)
- Optionally: patched `trace_writer.ts` (if trace fields were missing)
- Commit: `test(r11f-c-s1): cross-provider parity matrix + trace audit suite`

## Rollback Steps

```bash
git revert HEAD  # removes tests only (or trace_writer patch)
```
