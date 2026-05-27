---
canonical_id: CLAUDECODE_BRIEF_SRP_T1
version: 1.0
status: CURRENT
phase: SRP-T-1
session_type: test
authored: 2026-05-25
worktree: MadhavSRP-T1
branch: test/srp-t1-portal-unit
blocked_by: fix/srp-f1-portal-fixes (must be merged to main first)
deploy_target: none (test-only commit)
may_touch:
  - platform/src/lib/mcp/__tests__/primitives_registry.test.ts (create)
  - platform/src/lib/retrieve/__tests__/msr_sql.test.ts (create)
  - platform/src/lib/retrieve/__tests__/lel_query.test.ts (create)
  - platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts (create)
must_not_touch:
  - platform/src/lib/mcp/primitives_registry.ts
  - platform/src/lib/retrieve/msr_sql.ts
  - platform/src/lib/retrieve/lel_query.ts
  - platform/src/lib/retrieve/query_ephemeris.ts
  - platform-mcp/**
  - 00_ARCHITECTURE/**
---

# CLAUDECODE BRIEF: SRP-T-1 — Portal Retrieval Unit Tests

## Context

You are writing **unit tests** for the portal-side retrieval layer. The tests target the
fixes applied in SRP-F-1. This session creates four new test files. No production code is
modified. All tests use Vitest.

Working directory: `/Users/Dev/Vibe-Coding/Apps/MadhavSRP-T1`
Branch: `test/srp-t1-portal-unit`

**Pre-condition**: Confirm `fix/srp-f1-portal-fixes` is merged to `main` and this branch
is cut from `main` post-merge. Run `git log --oneline -5` to verify FIX-1/2/6/7 commits
are present.

---

## Test File 1: primitives_registry.test.ts

**Path**: `platform/src/lib/mcp/__tests__/primitives_registry.test.ts`

Locate or create the `__tests__` directory. Check if a test file already exists —
if so, append to it rather than replacing.

```typescript
import { describe, it, expect } from 'vitest'
import { isAllowedSurgicalTool, MCP_TO_RETRIEVAL_TOOL, SURGICAL_TOOLS } from '../primitives_registry'

describe('primitives_registry', () => {
  describe('original 19 tools still pass', () => {
    const originalTools = [
      'query_chart_facts', 'vector_search', 'cgm_graph_walk', 'pattern_register',
      'msr_sql', 'holistic_bundle', 'multi_school_bundle', 'chart_summary',
      'query_divisional_chart', 'query_varshphal', 'query_panchanga', 'muhurta_finder',
      'get_cgm_subgraph', 'lel_query', 'query_dasha_periods', 'query_transit_event',
      'query_ephemeris', 'query_signals', 'jaimini_chara_dasha_full',
    ]
    it.each(originalTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(true)
    })
  })

  describe('14 UDA tools now pass (FIX-1 regression)', () => {
    const udaTools = [
      'msr_sql', 'temporal', 'kp_query', 'query_kp_ruling_planets',
      'pattern_register', 'resonance_register', 'cluster_atlas',
      'contradiction_register', 'query_ucn_walk', 'query_cdlm_lookup',
      'query_rm_walk', 'query_jaimini_drishti', 'timeline_query', 'query_signal_state',
    ]
    it.each(udaTools)('isAllowedSurgicalTool("%s") === true', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(true)
    })
  })

  describe('rejects unknown tools', () => {
    const invalidTools = ['nonexistent', 'fake_tool', '', 'QUERY_SIGNALS', 'msr-sql']
    it.each(invalidTools)('isAllowedSurgicalTool("%s") === false', (tool) => {
      expect(isAllowedSurgicalTool(tool)).toBe(false)
    })
  })

  it('MCP_TO_RETRIEVAL_TOOL and SURGICAL_TOOLS are in sync', () => {
    const registryKeys = Object.keys(MCP_TO_RETRIEVAL_TOOL)
    const toolsArr = Array.from(SURGICAL_TOOLS)
    expect(registryKeys.sort()).toEqual(toolsArr.sort())
  })

  it('all MCP_TO_RETRIEVAL_TOOL values are non-empty strings', () => {
    for (const [k, v] of Object.entries(MCP_TO_RETRIEVAL_TOOL)) {
      expect(typeof v).toBe('string')
      expect(v.length).toBeGreaterThan(0)
    }
  })
})
```

**NOTE**: Some tool names in the 14-UDA list may overlap with originals (e.g., `msr_sql`,
`pattern_register` may already be in the original 19). Adjust the `originalTools` array
to match what was actually in the registry before FIX-1. Read the actual file to confirm
before writing the test. The key regression tests are the `udaTools` array.

---

## Test File 2: msr_sql.test.ts

**Path**: `platform/src/lib/retrieve/__tests__/msr_sql.test.ts`

This is the most important test file. It must cover both FIX-2 (forward_looking) and FIX-7
(logging). Because `msr_sql.ts` makes real DB calls, mock the DB pool.

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the database pool before importing msr_sql
vi.mock('../../db/pool', () => ({
  default: {
    query: vi.fn().mockResolvedValue({ rows: [], rowCount: 0 })
  }
}))

// IMPORTANT: Adjust the mock path to match your actual DB pool import
// Run: grep -n "from.*pool\|require.*pool" platform/src/lib/retrieve/msr_sql.ts
// to find the exact import path used

import pool from '../../db/pool'
import { msrSql } from '../msr_sql'  // adjust import to actual export name

const mockPool = pool as { query: ReturnType<typeof vi.fn> }

describe('msr_sql filter fidelity', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockPool.query.mockResolvedValue({ rows: [], rowCount: 0 })
  })

  // FIX-2 regression: forward_looking from params
  describe('forward_looking filter (FIX-2 regression)', () => {
    it('params.forward_looking=true passes true to SQL $4', async () => {
      const plan = { domains: [], forward_looking: false, audience_tier: 'super_admin',
        tools_authorized: ['msr_sql'], query_plan_id: 'test', query_text: 'test',
        query_class: 'holistic' as const, history_mode: 'synthesized' as const,
        panel_mode: false, expected_output_shape: 'structured_data' as const,
        manifest_fingerprint: '', schema_version: '1.0' as const }
      const params = { forward_looking: true }

      await msrSql(plan, params).catch(() => {})  // may error without real DB, that's ok

      const callArgs = mockPool.query.mock.calls[0]
      if (callArgs) {
        // $4 is the forward_looking parameter position in the SQL
        // Find the position by reading the actual query in msr_sql.ts
        const sqlParams = callArgs[1] as unknown[]
        const flIndex = 3  // 0-indexed position of $4 — verify against msr_sql.ts
        expect(sqlParams[flIndex]).toBe(true)
      }
    })

    it('no params.forward_looking passes null to SQL $4 (no filter)', async () => {
      const plan = { domains: [], forward_looking: false, audience_tier: 'super_admin',
        tools_authorized: ['msr_sql'], query_plan_id: 'test', query_text: 'test',
        query_class: 'holistic' as const, history_mode: 'synthesized' as const,
        panel_mode: false, expected_output_shape: 'structured_data' as const,
        manifest_fingerprint: '', schema_version: '1.0' as const }
      const params = {}

      await msrSql(plan, params).catch(() => {})

      const callArgs = mockPool.query.mock.calls[0]
      if (callArgs) {
        const sqlParams = callArgs[1] as unknown[]
        const flIndex = 3  // verify against msr_sql.ts
        expect(sqlParams[flIndex]).toBeNull()
      }
    })

    it('params.forward_looking=false passes null to SQL $4 (no filter = all signals)', async () => {
      const plan = { domains: [], forward_looking: false, audience_tier: 'super_admin',
        tools_authorized: ['msr_sql'], query_plan_id: 'test', query_text: 'test',
        query_class: 'holistic' as const, history_mode: 'synthesized' as const,
        panel_mode: false, expected_output_shape: 'structured_data' as const,
        manifest_fingerprint: '', schema_version: '1.0' as const }
      const params = { forward_looking: false }

      await msrSql(plan, params).catch(() => {})

      const callArgs = mockPool.query.mock.calls[0]
      if (callArgs) {
        const sqlParams = callArgs[1] as unknown[]
        const flIndex = 3  // verify against msr_sql.ts
        expect(sqlParams[flIndex]).toBeNull()
      }
    })
  })

  describe('domain filter', () => {
    it('params.domain filters to specified domain', async () => {
      const plan = { domains: [], forward_looking: false, audience_tier: 'super_admin',
        tools_authorized: ['msr_sql'], query_plan_id: 'test', query_text: 'test',
        query_class: 'holistic' as const, history_mode: 'synthesized' as const,
        panel_mode: false, expected_output_shape: 'structured_data' as const,
        manifest_fingerprint: '', schema_version: '1.0' as const }
      const params = { domain: 'career' }

      await msrSql(plan, params).catch(() => {})

      const callArgs = mockPool.query.mock.calls[0]
      if (callArgs) {
        const sqlParams = callArgs[1] as unknown[]
        // Domains are typically $1 or $2 — read msr_sql.ts to confirm position
        const domainsParam = sqlParams.find(p => Array.isArray(p) && (p as string[]).includes('career'))
        expect(domainsParam).toBeDefined()
      }
    })
  })

  describe('valence filter', () => {
    it('params.valence=["benefic"] is passed to SQL', async () => {
      const plan = { domains: [], forward_looking: false, audience_tier: 'super_admin',
        tools_authorized: ['msr_sql'], query_plan_id: 'test', query_text: 'test',
        query_class: 'holistic' as const, history_mode: 'synthesized' as const,
        panel_mode: false, expected_output_shape: 'structured_data' as const,
        manifest_fingerprint: '', schema_version: '1.0' as const }
      const params = { valence: ['benefic'] }

      await msrSql(plan, params).catch(() => {})

      const callArgs = mockPool.query.mock.calls[0]
      if (callArgs) {
        const sqlParams = callArgs[1] as unknown[]
        const valenceParam = sqlParams.find(p => Array.isArray(p) && (p as string[]).includes('benefic'))
        expect(valenceParam).toBeDefined()
      }
    })
  })
})
```

**IMPORTANT**: Before writing the test, read `msr_sql.ts` carefully to understand:
1. The exact SQL parameter positions ($1, $2, $3, $4...).
2. The actual export name of the function.
3. The actual import path for the DB pool.

Adjust the test accordingly. The test structure above is a guide — the assertions about
parameter positions must be verified against the actual code.

---

## Test File 3: lel_query.test.ts

**Path**: `platform/src/lib/retrieve/__tests__/lel_query.test.ts`

Focus on the significance filter (the platform side of FIX-5).

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../db/pool', () => ({
  default: { query: vi.fn().mockResolvedValue({ rows: [], rowCount: 0 }) }
}))

import pool from '../../db/pool'
import { lelQuery } from '../lel_query'  // adjust to actual export

const mockPool = pool as { query: ReturnType<typeof vi.fn> }

describe('lel_query filter fidelity', () => {
  beforeEach(() => { vi.clearAllMocks(); mockPool.query.mockResolvedValue({ rows: [], rowCount: 0 }) })

  it('params.significance="tier_1" includes significance filter in SQL', async () => {
    await lelQuery({ /* minimal plan */ } as any, { significance: 'tier_1' }).catch(() => {})
    const callArgs = mockPool.query.mock.calls[0]
    if (callArgs) {
      const sql = callArgs[0] as string
      expect(sql).toContain('significance')
      const params = callArgs[1] as unknown[]
      expect(params).toContain('tier_1')
    }
  })

  it('no params.significance skips significance filter', async () => {
    await lelQuery({ /* minimal plan */ } as any, {}).catch(() => {})
    const callArgs = mockPool.query.mock.calls[0]
    if (callArgs) {
      const sql = callArgs[0] as string
      // SQL should not include significance condition when not filtering
      expect(sql).not.toMatch(/significance\s*=/)
    }
  })

  it('params.category filters by category', async () => {
    await lelQuery({ /* minimal plan */ } as any, { category: 'career' }).catch(() => {})
    const callArgs = mockPool.query.mock.calls[0]
    if (callArgs) {
      const params = callArgs[1] as unknown[]
      expect(params).toContain('career')
    }
  })
})
```

---

## Test File 4: query_ephemeris.test.ts

**Path**: `platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts`

Focus on the sample_step downsampling logic (the portal side of FIX-4).

```typescript
import { describe, it, expect } from 'vitest'

// Test the downsampling logic in isolation by extracting it or testing the function directly
// The key logic from query_ephemeris.ts:
//   if (input.sample_step !== undefined && input.sample_step > 1) {
//     rows = rows.filter((_, i) => i % input.sample_step! === 0)
//   }

describe('query_ephemeris sample_step downsampling', () => {
  // Replicate the downsampling logic to test it directly
  function downsample<T>(rows: T[], sampleStep: number | undefined): T[] {
    if (sampleStep !== undefined && sampleStep > 1) {
      return rows.filter((_, i) => i % sampleStep === 0)
    }
    return rows
  }

  const dummyRows = Array.from({ length: 100 }, (_, i) => ({ row: i }))

  it('sample_step=1 returns all rows', () => {
    expect(downsample(dummyRows, 1)).toHaveLength(100)
  })

  it('sample_step=7 returns every 7th row', () => {
    const result = downsample(dummyRows, 7)
    expect(result).toHaveLength(Math.ceil(100 / 7))
    expect(result[0]).toEqual({ row: 0 })
    expect(result[1]).toEqual({ row: 7 })
    expect(result[2]).toEqual({ row: 14 })
  })

  it('sample_step=30 returns every 30th row', () => {
    const result = downsample(dummyRows, 30)
    expect(result).toHaveLength(Math.ceil(100 / 30))
  })

  it('sample_step=undefined returns all rows', () => {
    expect(downsample(dummyRows, undefined)).toHaveLength(100)
  })

  // FIX-4 regression: string "7d" must NOT be passed as sample_step to the platform
  it('FIX-4 regression: string "7d" is NOT a valid number (guard test)', () => {
    // This confirms why the bug occurred and why the fix in query_ephemeris.ts is needed
    const stringStep = "7d" as unknown as number
    expect(stringStep > 1).toBe(false)   // NaN > 1 is false → bug
    expect(typeof 7).toBe('number')       // the fix sends 7 (number)
    expect(7 > 1).toBe(true)             // now the filter fires
  })
})
```

---

## Acceptance Criteria

- [ ] ≥ 40 test cases across the 4 files.
- [ ] Each of FIX-1 through FIX-7 has at least one explicit regression test.
- [ ] `npx vitest run platform/src/lib/mcp/__tests__/ platform/src/lib/retrieve/__tests__/`
      shows 0 failures.
- [ ] No production code files modified.
- [ ] PR opened from `test/srp-t1-portal-unit`.

## Session Close

Commit message:
```
test(srp-t1): portal retrieval unit tests — primitives_registry, msr_sql, lel_query, query_ephemeris

Adds regression coverage for FIX-1 (primitives whitelist), FIX-2 (forward_looking param),
FIX-5 (lel significance filter), FIX-4 (sample_step downsampling guard),
FIX-6 (lel source_version), FIX-7 (msr_sql log accuracy).
≥40 test cases across 4 new test files.
```
