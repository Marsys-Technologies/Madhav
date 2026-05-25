/**
 * query_chandra_balam.test.ts — R2-T1 integration tests for query_chandra_balam retrieval engine.
 *
 * Verifies:
 *   T1 — getTool('query_chandra_balam') resolves to a non-null tool.
 *   T2 — tool.name is 'query_chandra_balam' (canonical MCP name, not 'chandra_balam_for_native').
 *   T3 — retrieve() returns bundle.tool_name = 'query_chandra_balam' (alias fix).
 *   T4 — native birth date 1984-02-05: Moon in Pisces (natal sign) → position=1 (Sama Rashi).
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
import { tool } from '../query_chandra_balam'
import type { QueryPlan } from '../types'

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-r2t1chan0001',
  query_text: 'query_chandra_balam integration test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_chandra_balam'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'test',
  schema_version: '1.0',
}

/**
 * ephemeris_daily row for native birth date 1984-02-05.
 * Moon in Pisces per FORENSIC §3 (birth Moon sign = Pisces, sign_id=12).
 * chandra_balam_for_native queries ephemeris_daily first (primary source).
 */
const BIRTH_DATE_EPHEMERIS_ROW = {
  sign: 'Pisces',
  nakshatra: 'Purva Bhadrapada',
  sidereal_longitude: '335.00',
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Unit tier (always runs) ───────────────────────────────────────────────────

describe('query_chandra_balam — unit tier (R2-T1)', () => {
  it('T1: getTool("query_chandra_balam") resolves to a non-null tool', () => {
    const resolved = getTool('query_chandra_balam')
    expect(resolved).toBeDefined()
    expect(resolved).not.toBeNull()
  })

  it('T2: tool.name is "query_chandra_balam" (canonical MCP name, not chandra_balam_for_native)', () => {
    expect(tool.name).toBe('query_chandra_balam')
  })

  it('T3: retrieve() returns bundle.tool_name = "query_chandra_balam" (alias fix)', async () => {
    mockQuery.mockResolvedValue({ rows: [BIRTH_DATE_EPHEMERIS_ROW], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })

    expect(bundle.tool_name).toBe('query_chandra_balam')
    expect(bundle.results.length).toBeGreaterThanOrEqual(1)
  })

  it('T4: native birth date 1984-02-05 → position=1 Sama Rashi (Moon in natal sign Pisces)', async () => {
    mockQuery.mockResolvedValue({ rows: [BIRTH_DATE_EPHEMERIS_ROW], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })
    const payload = JSON.parse(bundle.results[0]!.content) as {
      position_from_birth_moon: number
      chandra_bala_score: number
    }

    // Native birth Moon sign = Pisces (id=12). Transit Moon on 1984-02-05 also Pisces.
    // position = ((12 - 12 + 12) % 12) + 1 = 0 + 1 = 1 (Sama Rashi).
    expect(payload.position_from_birth_moon).toBe(1)
    expect(payload.chandra_bala_score).toBe(0.80)
  })

  it('T5: returned payload includes epistemics.surgical = true', async () => {
    mockQuery.mockResolvedValue({ rows: [BIRTH_DATE_EPHEMERIS_ROW], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })
    const payload = JSON.parse(bundle.results[0]!.content) as {
      epistemics?: { surgical?: boolean }
    }

    expect(payload.epistemics?.surgical).toBe(true)
  })
})

// ── DB integration tier (skip without DATABASE_URL) ───────────────────────────

const SKIP_DB = !process.env['DATABASE_URL']

describe.skipIf(SKIP_DB)('query_chandra_balam — DB integration tier (R2-T1)', () => {
  it('DB-T1: retrieve() against live DB for 1984-02-05 returns position=1 (Sama Rashi)', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '1984-02-05' })
    expect(bundle.tool_name).toBe('query_chandra_balam')
    expect(bundle.results.length).toBe(1)

    const payload = JSON.parse(bundle.results[0]!.content) as {
      position_from_birth_moon: number
    }
    expect(payload.position_from_birth_moon).toBe(1)
  }, 15_000)
})
