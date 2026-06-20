---
canonical_id: CLAUDECODE_BRIEF_SRP_T2
version: 1.0
status: CURRENT
phase: SRP-T-2
session_type: test
authored: 2026-05-25
worktree: MadhavSRP-T2
branch: test/srp-t2-mcp-unit
blocked_by: fix/srp-f2-mcp-fixes (must be merged to main first)
deploy_target: none (test-only commit)
may_touch:
  - platform-mcp/src/tools/__tests__/query_signals.test.ts (create)
  - platform-mcp/src/tools/__tests__/query_ephemeris.test.ts (create)
  - platform-mcp/src/tools/__tests__/lel_query.test.ts (create)
must_not_touch:
  - platform-mcp/src/tools/query_signals.ts
  - platform-mcp/src/tools/query_ephemeris.ts
  - platform-mcp/src/tools/lel_query.ts
  - platform-mcp/src/server.ts
  - platform/src/**
  - 00_ARCHITECTURE/**
---

# CLAUDECODE BRIEF: SRP-T-2 — MCP Tool Unit Tests

## Context

You are writing **unit tests** for the MCP sidecar tool param-translation layer. These tests
confirm that the MCP tools translate caller arguments correctly before calling `callPlatformPrimitive`.
The tests mock `callPlatformPrimitive` and assert on the arguments it receives.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-T2`
Branch: `test/srp-t2-mcp-unit`

**Pre-condition**: Confirm `fix/srp-f2-mcp-fixes` is merged to `main` and this branch
is cut from `main` post-merge.

**Key testing pattern**: Mock `callPlatformPrimitive` and use `vi.fn()` to capture the
`params` argument passed to it. Assert the correct translated values arrive.

```typescript
// Standard mock setup for all three test files:
import { vi } from 'vitest'

vi.mock('../callPlatformPrimitive', () => ({
  callPlatformPrimitive: vi.fn().mockResolvedValue({ success: true, data: [] })
}))
// Adjust path based on actual import in each tool file:
// grep "from.*callPlatformPrimitive" platform-mcp/src/tools/query_signals.ts
```

---

## Test File 1: query_signals.test.ts

**Path**: `platform-mcp/src/tools/__tests__/query_signals.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { callPlatformPrimitive } from '../callPlatformPrimitive'  // adjust path

vi.mock('../callPlatformPrimitive', () => ({  // adjust path
  callPlatformPrimitive: vi.fn().mockResolvedValue({ success: true, data: [] })
}))

const mockCallPlatform = callPlatformPrimitive as ReturnType<typeof vi.fn>

// Import the actual handler function — read query_signals.ts to find its export name
// It may be the default export of a tool registration object with a handler() method
// or a named function. Adjust accordingly.
// Pattern: the tool registers via { name: 'query_signals', handler: async (args) => {...} }
// You may need to call the handler directly.

describe('query_signals param translation', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // FIX-3 regression: valence vocabulary
  describe('valence (FIX-3 regression)', () => {
    it('valence="benefic" is passed as ["benefic"] to platform', async () => {
      await callQuerySignals({ valence: 'benefic' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.valence).toEqual(['benefic'])
    })

    it('valence="malefic" is passed as ["malefic"] to platform', async () => {
      await callQuerySignals({ valence: 'malefic' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.valence).toEqual(['malefic'])
    })

    it('valence="context-dependent" is passed correctly', async () => {
      await callQuerySignals({ valence: 'context-dependent' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.valence).toEqual(['context-dependent'])
    })

    it('old vocabulary "positive" does NOT exist in schema', () => {
      // Confirm the Zod schema rejects old vocabulary
      // Read the actual Zod schema definition from query_signals.ts and test it:
      // import { querySignalsSchema } from '../query_signals'
      // expect(() => querySignalsSchema.parse({ valence: 'positive' })).toThrow()
      // Placeholder — implement by importing the actual schema
      expect(true).toBe(true)  // Replace with actual schema validation test
    })

    it('no valence arg passes no valence to platform', async () => {
      await callQuerySignals({ planet: 'Sun' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.valence).toBeUndefined()
    })
  })

  describe('domain filter', () => {
    it('domain="career" is passed correctly to platform', async () => {
      await callQuerySignals({ domain: 'career' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.domain).toBe('career')
    })
  })

  describe('planet filter', () => {
    it('planet="Saturn" is passed correctly to platform', async () => {
      await callQuerySignals({ planet: 'Saturn' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      // Check how planet is mapped — may be planet or planets array
      const planetVal = platformParams?.planet ?? platformParams?.planets
      expect(JSON.stringify(planetVal)).toContain('Saturn')
    })
  })

  describe('forward_looking filter', () => {
    it('forward_looking=true is passed to platform', async () => {
      await callQuerySignals({ forward_looking: true })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.forward_looking).toBe(true)
    })
  })
})

// Helper: find the actual handler invocation pattern from query_signals.ts
// and implement this function accordingly
async function callQuerySignals(args: Record<string, unknown>) {
  // Pattern A — if tool exports a handler function directly:
  // return querySignalsHandler(args)
  // Pattern B — if tool exports a tool object with .handler:
  // return querySignalsTool.handler(args)
  // Implement after reading query_signals.ts export pattern
  throw new Error('Implement callQuerySignals based on query_signals.ts export pattern')
}
```

---

## Test File 2: query_ephemeris.test.ts

**Path**: `platform-mcp/src/tools/__tests__/query_ephemeris.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { callPlatformPrimitive } from '../callPlatformPrimitive'  // adjust path

vi.mock('../callPlatformPrimitive', () => ({
  callPlatformPrimitive: vi.fn().mockResolvedValue({ success: true, data: [] })
}))

const mockCallPlatform = callPlatformPrimitive as ReturnType<typeof vi.fn>

describe('query_ephemeris param translation', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // FIX-4 regression: sample_step type
  describe('sample_step (FIX-4 regression)', () => {
    it('sample_step="7d" is converted to number 7', async () => {
      await callQueryEphemeris({ planet: 'Moon', start_date: '2026-01-01', end_date: '2026-12-31', sample_step: '7d' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.sample_step).toBe(7)
      expect(typeof platformParams?.sample_step).toBe('number')
    })

    it('sample_step="30d" is converted to number 30', async () => {
      await callQueryEphemeris({ planet: 'Moon', start_date: '2026-01-01', end_date: '2026-12-31', sample_step: '30d' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.sample_step).toBe(30)
    })

    it('sample_step="1d" is converted to number 1', async () => {
      await callQueryEphemeris({ planet: 'Moon', start_date: '2026-01-01', end_date: '2026-12-31', sample_step: '1d' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.sample_step).toBe(1)
    })

    it('no sample_step defaults to number 1 (not string "1d")', async () => {
      await callQueryEphemeris({ planet: 'Moon', start_date: '2026-01-01', end_date: '2026-12-31' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      // May be 1 or undefined depending on implementation — both acceptable
      if (platformParams?.sample_step !== undefined) {
        expect(typeof platformParams.sample_step).toBe('number')
      }
    })

    it('sample_step sent to platform is NEVER a string', async () => {
      for (const step of ['1d', '7d', '30d']) {
        vi.clearAllMocks()
        await callQueryEphemeris({ planet: 'Moon', start_date: '2026-01-01', end_date: '2026-01-31', sample_step: step })
        const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
        if (platformParams?.sample_step !== undefined) {
          expect(typeof platformParams.sample_step).toBe('number')
        }
      }
    })
  })

  describe('date range', () => {
    it('start_date and end_date are passed through to platform', async () => {
      await callQueryEphemeris({ planet: 'Jupiter', start_date: '2026-01-01', end_date: '2026-06-30', sample_step: '1d' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.start_date).toBe('2026-01-01')
      expect(platformParams?.end_date).toBe('2026-06-30')
    })
  })
})

async function callQueryEphemeris(args: Record<string, unknown>) {
  // Implement based on query_ephemeris.ts export pattern (same as query_signals above)
  throw new Error('Implement callQueryEphemeris based on query_ephemeris.ts export pattern')
}
```

---

## Test File 3: lel_query.test.ts

**Path**: `platform-mcp/src/tools/__tests__/lel_query.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { callPlatformPrimitive } from '../callPlatformPrimitive'  // adjust path

vi.mock('../callPlatformPrimitive', () => ({
  callPlatformPrimitive: vi.fn().mockResolvedValue({ success: true, data: [] })
}))

const mockCallPlatform = callPlatformPrimitive as ReturnType<typeof vi.fn>

describe('lel_query param translation', () => {
  beforeEach(() => { vi.clearAllMocks() })

  // FIX-5 regression: significance field name
  describe('significance (FIX-5 regression)', () => {
    it('significance_tier="tier_1" sends significance="tier_1" to platform', async () => {
      await callLelQuery({ significance_tier: 'tier_1' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.significance).toBe('tier_1')
    })

    it('significance_tier="tier_2" sends significance="tier_2" to platform', async () => {
      await callLelQuery({ significance_tier: 'tier_2' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.significance).toBe('tier_2')
    })

    it('significance_tier sends NO min_significance key to platform (FIX-5 regression)', async () => {
      await callLelQuery({ significance_tier: 'tier_1' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.min_significance).toBeUndefined()
    })

    it('no significance_tier sends no significance to platform', async () => {
      await callLelQuery({ category: 'career' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.significance).toBeUndefined()
    })
  })

  // FIX-6 regression: source_version annotation
  describe('source_version (FIX-6 regression)', () => {
    it('response includes source_version: "1.7"', async () => {
      const result = await callLelQuery({})
      // The response object should include source_version in metadata
      // Adjust to actual response shape from lel_query.ts
      const str = JSON.stringify(result)
      expect(str).toContain('"1.7"')
      expect(str).not.toContain('"1.6"')
    })
  })

  describe('category filter', () => {
    it('category is passed to platform', async () => {
      await callLelQuery({ category: 'career' })
      const platformParams = mockCallPlatform.mock.calls[0]?.[1] as Record<string, unknown>
      expect(platformParams?.category).toBe('career')
    })
  })
})

async function callLelQuery(args: Record<string, unknown>) {
  // Implement based on lel_query.ts export pattern
  throw new Error('Implement callLelQuery based on lel_query.ts export pattern')
}
```

---

## Implementation Notes

For all three test files, the `callXxx` helper functions need to be implemented by reading
the actual export pattern of each tool file. Common patterns in MCP tools:

**Pattern A** — Default export of a tool registration object:
```typescript
// In query_signals.ts:
export default { name: 'query_signals', schema: z.object({...}), handler: async (args) => {...} }
// Test calls: await tool.handler(args)
```

**Pattern B** — Named export of handler:
```typescript
// In query_signals.ts:
export async function querySignalsHandler(args: QuerySignalsArgs) {...}
// Test calls: await querySignalsHandler(args)
```

**Pattern C** — The MCP SDK registration pattern (tool registered on server, no direct export):
In this case, refactor the handler into a separately-exportable function in the source file
(minimum change: `export const handleQuerySignals = async (args) => {...}` extracted from
the `server.setRequestHandler` or `server.tool()` callback).

Read the actual tool files before choosing the test approach. Do not mock the entire module —
test the actual handler logic.

---

## Acceptance Criteria

- [ ] ≥ 30 test cases across the 3 files.
- [ ] FIX-3 valence regression: old vocabulary causes Zod parse error OR is mapped correctly.
- [ ] FIX-4 sample_step regression: string enum always converted to number.
- [ ] FIX-5 significance regression: `min_significance` key never sent to platform.
- [ ] FIX-6 source_version regression: response contains `"1.7"`, not `"1.6"`.
- [ ] `npx vitest run platform-mcp/src/tools/__tests__/` shows 0 failures.
- [ ] PR opened from `test/srp-t2-mcp-unit`.

## Session Close

Commit message:
```
test(srp-t2): MCP tool unit tests — query_signals, query_ephemeris, lel_query param translation

Regression coverage for FIX-3 (valence vocabulary), FIX-4 (sample_step type),
FIX-5 (significance field name), FIX-6 (lel source_version).
≥30 test cases across 3 new test files. All callPlatformPrimitive calls verified.
```
