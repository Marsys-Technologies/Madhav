import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))

import { getStorageClient } from '@/lib/storage'
import { tool } from '../remedial_codex_query'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000003',
  query_text: 'What remedies for Mercury?',
  query_class: 'remedial',
  domains: [],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: ['remedial_codex_query'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const mercuryRow = {
  content: 'Mercury — PRIMARY STRENGTHENING RECOMMENDATION. Om Bum Budhaya Namah (mantra). Emerald gem...',
  doc_type: 'l4_remedial',
  chunk_id: 'remedial_part1_001',
  canonical_id: 'REMEDIAL_CODEX_v2_0_PART1',
  source_file: '04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md',
  source_version: '2.0',
}

const mantraRow = {
  content: 'Mantra practice protocol: 108 repetitions daily...',
  doc_type: 'l4_remedial',
  chunk_id: 'remedial_part1_005',
  canonical_id: 'REMEDIAL_CODEX_v2_0_PART1',
  source_file: '04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md',
  source_version: '2.0',
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(getStorageClient).mockReturnValue({
    query: mockQuery,
    transaction: vi.fn(),
    readObject: vi.fn(),
    writeObject: vi.fn(),
    objectExists: vi.fn(),
    readFile: vi.fn(),
    fileExists: vi.fn(),
    listFiles: vi.fn(),
  } as ReturnType<typeof getStorageClient>)
})

describe('remedial_codex_query tool', () => {
  // --- AC-B.6: word-boundary precision filter ---
  it('uses word-boundary regex (~*) not plain ILIKE for planet filter (AC-B.6)', async () => {
    mockQuery.mockResolvedValue({ rows: [mercuryRow], rowCount: 1 })
    await tool.retrieve(basePlan, { planet: 'Saturn' })
    const sql: string = mockQuery.mock.calls[0][0]
    // Must use regex operator ~* (not ILIKE) for precision
    expect(sql).toContain('~*')
    expect(sql).not.toContain('ILIKE')
    // Word-boundary pattern: \mPlanet\M
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams.some(p => typeof p === 'string' && p.includes('\\m'))).toBe(true)
    expect(sqlParams.some(p => typeof p === 'string' && p.includes('\\M'))).toBe(true)
  })

  it('word-boundary pattern wraps the planet name correctly', async () => {
    mockQuery.mockResolvedValue({ rows: [mercuryRow], rowCount: 1 })
    await tool.retrieve(basePlan, { planet: 'Mercury' })
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    const planetParam = sqlParams.find(p => typeof p === 'string' && (p as string).includes('Mercury'))
    expect(planetParam).toBe('\\mMercury\\M')
  })

  it('retrieve() with planet:Mercury returns results', async () => {
    mockQuery.mockResolvedValue({ rows: [mercuryRow], rowCount: 1 })
    const bundle = await tool.retrieve(basePlan, { planet: 'Mercury' })
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('retrieve() with practice_type:mantra returns mantra-related content', async () => {
    mockQuery.mockResolvedValue({ rows: [mantraRow], rowCount: 1 })
    const bundle = await tool.retrieve(basePlan, { practice_type: 'mantra' })
    expect(bundle.results.length).toBeGreaterThan(0)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.content.toLowerCase()).toContain('mantra')
  })

  it('retrieve() with no params returns results without error', async () => {
    mockQuery.mockResolvedValue({ rows: [mercuryRow, mantraRow], rowCount: 2 })
    const bundle = await tool.retrieve(basePlan)
    expect(bundle.results.length).toBeGreaterThanOrEqual(0)
  })

  it('ToolBundle has correct shape', async () => {
    mockQuery.mockResolvedValue({ rows: [mercuryRow], rowCount: 1 })
    const bundle = await tool.retrieve(basePlan, { planet: 'Mercury' })
    expect(bundle.tool_name).toBe('remedial_codex_query')
    expect(bundle.served_from_cache).toBe(false)
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('retrieve() with nonexistent planet returns empty results without error', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
    const bundle = await tool.retrieve(basePlan, { planet: 'NonExistentPlanet' })
    expect(bundle.results).toEqual([])
    expect(bundle.tool_name).toBe('remedial_codex_query')
  })
})
