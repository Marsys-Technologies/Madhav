/**
 * query_tara_balam.test.ts — R2-T1 integration tests for query_tara_balam retrieval engine.
 *
 * Verifies:
 *   T1 — getTool('query_tara_balam') resolves to a non-null tool.
 *   T2 — tool.name is 'query_tara_balam' (canonical MCP name, not 'tara_balam_for_native').
 *   T3 — retrieve() returns bundle.tool_name = 'query_tara_balam' (alias fix).
 *   T4 — native birth date 1984-02-05: Moon in PBh (natal nak) → tara_count=1 (Janma).
 *   T5 — returned payload includes epistemics.surgical = true.
 *
 * DB tests skip when DATABASE_URL is absent (CI-safe).
 * GISMCP Remediation R2-T1.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Hoisted mock helpers (must precede vi.mock calls) ─────────────────────────

const mockQuery = vi.hoisted(() => vi.fn())

vi.mock('server-only', () => ({}))
vi.mock('@/lib/storage', () => ({
  getStorageClient: () => ({
    query: mockQuery,
    transaction: vi.fn(),
    readObject: vi.fn(),
    writeObject: vi.fn(),
    objectExists: vi.fn(),
    readFile: vi.fn(),
    fileExists: vi.fn(),
    listFiles: vi.fn(),
  }),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

import { getTool } from '../index'
import { tool } from '../query_tara_balam'
import type { QueryPlan } from '../types'

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-r2t1tara0001',
  query_text: 'query_tara_balam integration test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_tara_balam'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'test',
  schema_version: '1.0',
}

/** Moon in Purva Bhadrapada (index 25) on native birth date 1984-02-05 per FORENSIC §3. */
const BIRTH_DATE_PANCHANGA_ROW = {
  moon_nakshatra: 'Purva Bhadrapada',
  moon_nakshatra_index: 25,
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Unit tier (always runs) ───────────────────────────────────────────────────

describe('query_tara_balam — unit tier (R2-T1)', () => {
  it('T1: getTool("query_tara_balam") resolves to a non-null tool', () => {
    const resolved = getTool('query_tara_balam')
    expect(resolved).toBeDefined()
    expect(resolved).not.toBeNull()
  })

  it('T2: tool.name is "query_tara_balam" (canonical MCP name, not tara_balam_for_native)', () => {
    expect(tool.name).toBe('query_tara_balam')
  })

  it('T3: retrieve() returns bundle.tool_name = "query_tara_balam" (alias fix)', async () => {
    mockQuery.mockResolvedValue({ rows: [BIRTH_DATE_PANCHANGA_ROW], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })

    expect(bundle.tool_name).toBe('query_tara_balam')
    expect(bundle.results.length).toBeGreaterThanOrEqual(1)
  })

  it('T4: native birth date 1984-02-05 → tara_count=1 (Janma — Moon in natal nak)', async () => {
    mockQuery.mockResolvedValue({ rows: [BIRTH_DATE_PANCHANGA_ROW], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })
    const payload = JSON.parse(bundle.results[0]!.content) as {
      tara_count: number
      tara_name: string
      score: number
    }

    // Native natal Moon nak = PBh (index 25); transit Moon on birth date also PBh (index 25).
    // tara_count = ((25 - 25 + 27) % 27) % 9 + 1 = 0 % 9 + 1 = 1 (Janma).
    expect(payload.tara_count).toBe(1)
    expect(payload.tara_name).toBe('Janma')
  })

  it('T5: returned payload includes epistemics.surgical = true', async () => {
    mockQuery.mockResolvedValue({ rows: [BIRTH_DATE_PANCHANGA_ROW], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })
    const payload = JSON.parse(bundle.results[0]!.content) as {
      epistemics?: { surgical?: boolean }
    }

    expect(payload.epistemics?.surgical).toBe(true)
  })
})

// ── DB integration tier (skip without DATABASE_URL) ───────────────────────────

const SKIP_DB = !process.env['DATABASE_URL']

describe.skipIf(SKIP_DB)('query_tara_balam — DB integration tier (R2-T1)', () => {
  it('DB-T1: retrieve() against live DB for 1984-02-05 returns tara_count=1 (Janma)', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })
    expect(bundle.tool_name).toBe('query_tara_balam')
    expect(bundle.results.length).toBe(1)

    const payload = JSON.parse(bundle.results[0]!.content) as {
      tara_count: number
      tara_name: string
    }
    expect(payload.tara_count).toBe(1)
    expect(payload.tara_name).toBe('Janma')
  }, 15_000)
})
