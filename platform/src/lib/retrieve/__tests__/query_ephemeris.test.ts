import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool } from '../query_ephemeris'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000099',
  query_text: 'ephemeris test',
  query_class: 'holistic',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_ephemeris'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const marsRow = {
  date: '2008-04-15',
  planet: 'mars',
  longitude_deg: '298.42',
  latitude_deg: '0.54',
  speed_deg_per_day: '0.62',
  is_retrograde: false,
  sign: 'capricorn',
  sign_degree: '28.42',
  nakshatra: 'uttara_ashadha',
  nakshatra_pada: 4,
  ayanamsha: 'lahiri',
  ephemeris_version: '2.10.03',
  // Phase 4B derived columns
  dignity_d1: 'exalted',
  is_combust: false,
  combust_orb_deg: '142.3000',
  vargottama_today: false,
  sign_ingress_today: false,
  whole_sign_house: 10,
  graha_yuddha_with: null,
  // Phase 4 §6.6 Bhava-Chalit
  bhava_chalit_house: 10,
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
  })
})

describe('query_ephemeris tool', () => {
  it('default params: SQL uses CURRENT_DATE and no planet filter', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.planet).toBe('mars')

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('CURRENT_DATE')
    expect(sql).not.toContain('planet = ANY')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams).toHaveLength(0)
  })

  it('single date + single planet: SQL uses $1::date and planet = ANY($2::text[])', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    await tool.retrieve(basePlan, { date: '2008-04-15', planet: 'Saturn' })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('date = $1::date')
    expect(sql).toContain('planet = ANY($2::text[])')
    expect(sql).not.toContain('CURRENT_DATE')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('2008-04-15')
    expect(sqlParams[1]).toEqual(['saturn'])
  })

  it('date range + multiple planets: SQL uses >= $1 and <= $2 date bounds', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    await tool.retrieve(basePlan, {
      start_date: '2019-01-01',
      end_date: '2019-01-31',
      planets: ['Mercury', 'Saturn'],
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('date >= $1::date')
    expect(sql).toContain('date <= $2::date')
    expect(sql).toContain('planet = ANY($3::text[])')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('2019-01-01')
    expect(sqlParams[1]).toBe('2019-01-31')
    expect(sqlParams[2]).toEqual(['mercury', 'saturn'])
  })

  it('planet name is normalized to lowercase regardless of input case', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    await tool.retrieve(basePlan, { date: '2026-05-19', planet: 'SATURN' })

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[1]).toEqual(['saturn'])
  })

  it('empty result returns diagnostic row with confidence=0 and note field', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, { date: '1800-01-01' })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.note).toContain('ephemeris_daily empty or out-of-range')
    expect(bundle.results[0].confidence).toBe(0)
    expect(bundle.results[0].significance).toBe(0)
  })

  it('surfaces dignity field in response by default', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '2008-04-15', planet: 'mars' })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.dignity).toBe('exalted')
  })

  it('surfaces combust + orb in response by default', async () => {
    const combustRow = { ...marsRow, is_combust: true, combust_orb_deg: '10.5000' }
    mockQuery.mockResolvedValue({ rows: [combustRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    const content = JSON.parse(bundle.results[0].content)
    expect(content.is_combust).toBe(true)
    expect(content.combust_orb_deg).toBeCloseTo(10.5)
  })

  it('surfaces whole_sign_house in response by default', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    const content = JSON.parse(bundle.results[0].content)
    expect(content.whole_sign_house).toBe(10)
  })

  it('derived_fields:[] opts out — response omits all 6 derived keys', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { derived_fields: [] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.dignity).toBeUndefined()
    expect(content.is_combust).toBeUndefined()
    expect(content.combust_orb_deg).toBeUndefined()
    expect(content.vargottama).toBeUndefined()
    expect(content.sign_ingress).toBeUndefined()
    expect(content.whole_sign_house).toBeUndefined()
    expect(content.graha_yuddha_with).toBeUndefined()
  })

  it('derived_fields:[dignity] returns only dignity — other derived keys absent', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { derived_fields: ['dignity'] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.dignity).toBe('exalted')
    expect(content.is_combust).toBeUndefined()
    expect(content.whole_sign_house).toBeUndefined()
  })

  it('DB error rethrows (does not degrade) and logs via writeToolExecutionLog', async () => {
    mockQuery.mockRejectedValueOnce(new Error('db_connection_timeout'))

    await expect(tool.retrieve(basePlan)).rejects.toThrow('db_connection_timeout')

    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({
        tool_name: 'query_ephemeris',
        status: 'error',
        error_code: 'db_connection_timeout',
      }),
    )
  })

  it('returns valid ToolBundle shape on success', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('query_ephemeris')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('EPHEMERIS_DAILY')
    expect(bundle.results[0].confidence).toBe(1.0)
  })

  it('surfaces bhava_chalit_house in response by default (house_bc in ALL_DERIVED_FIELDS)', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    const content = JSON.parse(bundle.results[0].content)
    expect(content.bhava_chalit_house).toBe(10)
  })

  it('derived_fields:["house_bc"] returns bhava_chalit_house and omits whole_sign_house', async () => {
    mockQuery.mockResolvedValue({ rows: [marsRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { derived_fields: ['house_bc'] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.bhava_chalit_house).toBe(10)
    expect(content.whole_sign_house).toBeUndefined()
  })
})
