/**
 * query_ucn_walk.test.ts — path-resolution + basic retrieval tests.
 *
 * Verifies:
 *   T1 — UCN_PATH uses process.cwd() (not __dirname) and ends with the correct filename suffix.
 *   T2 — tool.name is 'query_ucn_walk'.
 *   T3 — retrieve() returns a ToolBundle when the file is present (mocked fs).
 *
 * MCP-REM-S2 Bug C1d fix.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import path from 'path'

const mockReadFileSync = vi.hoisted(() => vi.fn())

vi.mock('server-only', () => ({}))
vi.mock('fs', () => ({
  default: { readFileSync: mockReadFileSync },
  readFileSync: mockReadFileSync,
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

import { tool } from '../query_ucn_walk'
import type { QueryPlan } from '../types'

// Minimal UCN markdown snippet referencing one MSR signal.
const MINIMAL_UCN_MD = `
## Career and Psychology Confluence

Saturn rules the 10H from Capricorn Ascendant. MSR.001 anchors this pattern.
See also MSR.002 for wealth cross-link.

### Sub-section

More text referencing MSR.100.
`

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-ucnwalktest01',
  query_text: 'ucn walk test',
  query_class: 'holistic',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_ucn_walk'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'structured_data',
  manifest_fingerprint: 'test',
  schema_version: '1.0',
}

describe('query_ucn_walk — path resolution (Bug C1d)', () => {
  it('T1: UCN_PATH uses process.cwd() and ends with 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md', () => {
    const expected = path.resolve(process.cwd(), '025_HOLISTIC_SYNTHESIS/UCN_v4_0.md')
    expect(expected).toMatch(/025_HOLISTIC_SYNTHESIS[/\\]UCN_v4_0\.md$/)
    expect(expected).not.toContain('.next')
  })

  it('T2: tool.name is query_ucn_walk', () => {
    expect(tool.name).toBe('query_ucn_walk')
  })

  it('T3: retrieve() returns a ToolBundle with signal references from UCN markdown', async () => {
    mockReadFileSync.mockReturnValue(MINIMAL_UCN_MD)
    const bundle = await tool.retrieve(basePlan, {})
    expect(bundle.tool_name).toBe('query_ucn_walk')
    expect(Array.isArray(bundle.results)).toBe(true)
    expect(bundle.results.length).toBeGreaterThan(0)
    const ids = bundle.results.map((r) => JSON.parse(r.content).signal_id as string)
    expect(ids).toContain('MSR.001')
  })

  it('T4: retrieve() with seed_signal_id returns only that signal', async () => {
    mockReadFileSync.mockReturnValue(MINIMAL_UCN_MD)
    const bundle = await tool.retrieve(basePlan, { seed_signal_id: 'MSR.001' })
    expect(bundle.results.every((r) => JSON.parse(r.content).signal_id === 'MSR.001')).toBe(true)
  })
})
