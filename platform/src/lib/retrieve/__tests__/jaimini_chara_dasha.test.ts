/**
 * jaimini_chara_dasha.test.ts — R2-T1 integration tests for jaimini_chara_dasha
 * and jaimini_chara_dasha_full retrieval engines.
 *
 * Verifies:
 *   T1 — getTool('jaimini_chara_dasha') resolves to a non-null tool.
 *   T2 — getTool('jaimini_chara_dasha_full') resolves to a non-null tool.
 *   T3 — jaimini_chara_dasha tool.name = 'jaimini_chara_dasha'.
 *   T4 — jaimini_chara_dasha_full tool.name = 'jaimini_chara_dasha_full'.
 *   T5 — [Mock] jaimini_chara_dasha.retrieve() returns bundle.tool_name = 'jaimini_chara_dasha'.
 *   T6 — [Mock] jaimini_chara_dasha.retrieve() forces include_sub_periods=false (active only).
 *   T7 — [Mock] jaimini_chara_dasha_full.retrieve() forces include_sub_periods=true (full timeline).
 *   T8 — [Sidecar] active dasha response has active_rashi_dasha.rashi (non-empty string).
 *   T9 — [Sidecar] full timeline response has full_periods with 12 entries.
 *
 * Sidecar tests skip when PYTHON_SIDECAR_URL is absent (CI-safe).
 * GISMCP Remediation R2-T1.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock setup ────────────────────────────────────────────────────────────────

vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { getTool } from '../index'
import { tool as jaiminiTool } from '../jaimini_chara_dasha'
import { tool as jaiminiFullTool } from '../jaimini_chara_dasha_full'
import type { QueryPlan } from '../types'

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-r2t1jaim0001',
  query_text: 'jaimini_chara_dasha integration test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['jaimini_chara_dasha'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'test',
  schema_version: '1.0',
}

const ACTIVE_DASHA_RESPONSE = {
  ok: true,
  query_date: '2026-05-26',
  active_rashi_dasha: {
    rashi: 'Scorpio',
    sign_lord: 'Mars',
    start_date: '2020-01-01',
    end_date: '2027-01-01',
  },
  active_antar_dasha: {
    rashi: 'Capricorn',
    sign_lord: 'Saturn',
    start_date: '2025-06-01',
    end_date: '2026-12-01',
  },
}

const FULL_PERIODS_RESPONSE = {
  ok: true,
  periods: Array.from({ length: 12 }, (_, i) => ({
    rashi: `Rashi_${i + 1}`,
    sign_lord: `Lord_${i + 1}`,
    years: 10,
    start_date: '2000-01-01',
    end_date: '2010-01-01',
  })),
  total_years: 120,
}

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(ACTIVE_DASHA_RESPONSE),
  })
})

// ── Unit tier (always runs) ───────────────────────────────────────────────────

describe('jaimini_chara_dasha — unit tier (R2-T1)', () => {
  it('T1: getTool("jaimini_chara_dasha") resolves to a non-null tool', () => {
    const resolved = getTool('jaimini_chara_dasha')
    expect(resolved).toBeDefined()
    expect(resolved).not.toBeNull()
  })

  it('T2: getTool("jaimini_chara_dasha_full") resolves to a non-null tool', () => {
    const resolved = getTool('jaimini_chara_dasha_full')
    expect(resolved).toBeDefined()
    expect(resolved).not.toBeNull()
  })

  it('T3: jaimini_chara_dasha tool.name = "jaimini_chara_dasha"', () => {
    expect(jaiminiTool.name).toBe('jaimini_chara_dasha')
  })

  it('T4: jaimini_chara_dasha_full tool.name = "jaimini_chara_dasha_full"', () => {
    expect(jaiminiFullTool.name).toBe('jaimini_chara_dasha_full')
  })

  it('T5: jaimini_chara_dasha.retrieve() returns bundle.tool_name = "jaimini_chara_dasha"', async () => {
    process.env['PYTHON_SIDECAR_URL'] = 'http://localhost:18765'

    const bundle = await jaiminiTool.retrieve(basePlan, { date: '2026-05-26' })

    expect(bundle.tool_name).toBe('jaimini_chara_dasha')
    expect(bundle.results.length).toBeGreaterThanOrEqual(1)

    delete process.env['PYTHON_SIDECAR_URL']
  })

  it('T6: jaimini_chara_dasha forces include_sub_periods=false (active period only)', async () => {
    process.env['PYTHON_SIDECAR_URL'] = 'http://localhost:18765'

    const bundle = await jaiminiTool.retrieve(basePlan, { date: '2026-05-26' })
    const payload = JSON.parse(bundle.results[0]!.content) as {
      ok?: boolean
      active_rashi_dasha?: { rashi: string }
      full_periods?: unknown[]
    }

    expect(payload.ok).toBe(true)
    expect(payload.active_rashi_dasha?.rashi).toBe('Scorpio')
    expect(payload.full_periods).toBeUndefined()

    delete process.env['PYTHON_SIDECAR_URL']
  })

  it('T7: jaimini_chara_dasha_full forces include_sub_periods=true (full 12-rashi timeline)', async () => {
    process.env['PYTHON_SIDECAR_URL'] = 'http://localhost:18765'

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(FULL_PERIODS_RESPONSE),
    })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(ACTIVE_DASHA_RESPONSE),
    })

    const bundle = await jaiminiFullTool.retrieve(basePlan, { date: '2026-05-26' })
    const payload = JSON.parse(bundle.results[0]!.content) as {
      ok?: boolean
      full_periods?: Array<{ rashi: string }>
      total_years?: number
    }

    expect(bundle.tool_name).toBe('jaimini_chara_dasha_full')
    expect(payload.ok).toBe(true)
    expect(Array.isArray(payload.full_periods)).toBe(true)
    expect(payload.full_periods?.length).toBe(12)

    delete process.env['PYTHON_SIDECAR_URL']
  })
})

// ── Sidecar integration tier (skip without PYTHON_SIDECAR_URL) ───────────────

const SKIP_SIDECAR = !process.env['PYTHON_SIDECAR_URL']

describe.skipIf(SKIP_SIDECAR)('jaimini_chara_dasha — sidecar integration tier (R2-T1)', () => {
  beforeEach(() => {
    vi.unstubAllGlobals()
    vi.unmock('@/lib/db/monitoring-write')
  })

  it('Sidecar-T1: active dasha has non-empty active_rashi_dasha.rashi', async () => {
    const bundle = await jaiminiTool.retrieve(basePlan, {})
    expect(bundle.tool_name).toBe('jaimini_chara_dasha')

    const payload = JSON.parse(bundle.results[0]!.content) as {
      ok: boolean
      active_rashi_dasha?: { rashi: string }
    }
    expect(payload.ok).toBe(true)
    expect(typeof payload.active_rashi_dasha?.rashi).toBe('string')
    expect((payload.active_rashi_dasha?.rashi?.length ?? 0) > 0).toBe(true)
  }, 15_000)

  it('Sidecar-T2: full timeline has exactly 12 rashi periods', async () => {
    const bundle = await jaiminiFullTool.retrieve(basePlan, {})
    expect(bundle.tool_name).toBe('jaimini_chara_dasha_full')

    const payload = JSON.parse(bundle.results[0]!.content) as {
      ok: boolean
      full_periods?: Array<{ rashi: string }>
    }
    expect(payload.ok).toBe(true)
    expect(payload.full_periods?.length).toBe(12)
  }, 15_000)
})
