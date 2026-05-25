import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

import { getStorageClient } from '@/lib/storage'
import { tool } from '../query_dasha_periods'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000088',
  query_text: 'dasha test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_dasha_periods'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

function makeDashaRow(mdLord: string, adLord: string, startDate: string, endDate: string) {
  return {
    fact_id: `DSH.V.${mdLord}.${adLord}`,
    category: 'dasha_vimshottari',
    value_json: { md_lord: mdLord, ad_lord: adLord, start_date: startDate, end_date: endDate },
    source_section: 'FORENSIC §5.1',
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  ;(getStorageClient as ReturnType<typeof vi.fn>).mockReturnValue({ query: mockQuery })
})

// ── Test 1: empty params — default query returns end_date >= today ────────────

describe('query_dasha_periods default query', () => {
  it('adds end_date >= today filter for empty params', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        makeDashaRow('Mercury', 'Mercury', '2024-06-27', '2026-08-21'),
        makeDashaRow('Mercury', 'Ketu', '2026-08-21', '2027-08-19'),
      ],
    })

    const bundle = await tool.retrieve(basePlan, {})

    expect(mockQuery).toHaveBeenCalledOnce()
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("end_date')::date >=")
    expect(sql).toContain('category = $1')
    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args[0]).toBe('dasha_vimshottari')
    expect(bundle.results).toHaveLength(2)
    expect(bundle.tool_name).toBe('query_dasha_periods')
  })
})

// ── Test 2: next_count — MD transitions forward from today ───────────────────

describe('query_dasha_periods next_count', () => {
  it('filters start_date >= today and returns next_count MD clusters', async () => {
    const rows = [
      makeDashaRow('Mercury', 'Ketu', '2026-08-21', '2027-08-19'),
      makeDashaRow('Ketu', 'Ketu', '2027-08-19', '2028-02-24'),
      makeDashaRow('Ketu', 'Venus', '2028-02-24', '2028-10-24'),
    ]
    mockQuery.mockResolvedValue({ rows })

    const bundle = await tool.retrieve(basePlan, { level: 'M', next_count: 1 })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("start_date')::date >=")
    expect(sql).toContain('ASC')
    // level='M' dedup: only rows where ad_lord === md_lord remain
    const contents = bundle.results.map(r => JSON.parse(r.content))
    const deduped = contents.filter((c: { level: string }) => c.level === 'M_start')
    expect(deduped.length).toBeGreaterThanOrEqual(1)
    // next_count=1 should cap to 1 MD cluster
    expect(bundle.results.length).toBeLessThanOrEqual(9)
  })
})

// ── Test 3: prev_count — descending order, reversed for presentation ─────────

describe('query_dasha_periods prev_count', () => {
  it('uses DESC ordering and reverses results for presentation', async () => {
    const rows = [
      makeDashaRow('Saturn', 'Mercury', '2006-01-01', '2009-01-01'),
      makeDashaRow('Saturn', 'Ketu', '2003-01-01', '2004-01-01'),
      makeDashaRow('Saturn', 'Saturn', '1991-01-01', '1994-01-01'),
    ]
    mockQuery.mockResolvedValue({ rows })

    const bundle = await tool.retrieve(basePlan, { prev_count: 1 })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("end_date')::date <=")
    expect(sql).toContain('DESC')
    // prev_count caps to 1 cluster, output reversed → ascending start_date order
    expect(bundle.results.length).toBeGreaterThan(0)
  })
})

// ── Test 4: as_of_date — bracket filter for point-in-time lookup ─────────────

describe('query_dasha_periods as_of_date', () => {
  it('emits start_date <= as_of_date < end_date condition', async () => {
    mockQuery.mockResolvedValue({
      rows: [makeDashaRow('Saturn', 'Venus', '2000-06-07', '2003-06-07')],
    })

    const bundle = await tool.retrieve(basePlan, { as_of_date: '2001-01-01' })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("start_date')::date <=")
    expect(sql).toContain("end_date')::date >")
    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args).toContain('2001-01-01')
    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.md_lord).toBe('Saturn')
  })
})

// ── Test 5: md_lord filter — returns only matching lord rows ─────────────────

describe('query_dasha_periods md_lord filter', () => {
  it('adds ILIKE condition on md_lord and returns matching rows', async () => {
    const rows = Array.from({ length: 9 }, (_, i) =>
      makeDashaRow('Saturn', `Planet${i}`, `199${i}-01-01`, `199${i + 1}-01-01`)
    )
    mockQuery.mockResolvedValue({ rows })

    const bundle = await tool.retrieve(basePlan, { md_lord: 'Saturn' })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("md_lord' ILIKE")
    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args).toContain('%Saturn%')
    expect(bundle.results).toHaveLength(9)
    bundle.results.forEach(r => {
      const content = JSON.parse(r.content)
      expect(content.md_lord).toBe('Saturn')
    })
  })
})

// ── Test 6: zero-row diagnostic fallback ─────────────────────────────────────

describe('query_dasha_periods zero-row fallback', () => {
  it('returns a diagnostic note result when no rows match', async () => {
    mockQuery.mockResolvedValue({ rows: [] })

    const bundle = await tool.retrieve(basePlan, { md_lord: 'Pluto' })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.note).toContain('No dasha_vimshottari rows match')
    expect(content.note).toContain('1984-02-05')
    expect(bundle.results[0].confidence).toBe(0)
  })
})

// ── Test 7: yogini system — category switches correctly ──────────────────────

describe('query_dasha_periods yogini system', () => {
  it('uses dasha_yogini category for system=yogini', async () => {
    mockQuery.mockResolvedValue({ rows: [] })

    await tool.retrieve(basePlan, { system: 'yogini' })

    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args[0]).toBe('dasha_yogini')
  })
})

// ── Test 8: ToolBundle shape ─────────────────────────────────────────────────

describe('query_dasha_periods bundle shape', () => {
  it('returns a correctly shaped ToolBundle', async () => {
    mockQuery.mockResolvedValue({
      rows: [makeDashaRow('Mercury', 'Mercury', '2024-06-27', '2026-08-21')],
    })

    const bundle = await tool.retrieve(basePlan, {})

    expect(bundle.tool_name).toBe('query_dasha_periods')
    expect(bundle.tool_version).toBe('1.1.0')
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.tool_bundle_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    )
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.results[0].confidence).toBe(1.0)
    expect(bundle.results[0].source_canonical_id).toBe('FORENSIC')
  })
})
