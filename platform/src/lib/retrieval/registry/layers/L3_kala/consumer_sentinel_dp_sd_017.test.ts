/**
 * DP-SD-017 / L3-U05 consumer sentinel contracts.
 *
 * These tests lock two fail-closed serving properties:
 *   1. kala_bhavishya fallback filters and failure/empty states remain explicit;
 *   2. projection rows never imply an accepted generation/build binding that the
 *      physical kala_bhavishya schema cannot prove.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import { queryTemporalActivationCapability } from './query_temporal_activation'
import { queryProjectionsCapability } from './query_projections'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const SIGNAL_ID = '22222222-bbbb-4bbb-bbbb-bbbbbbbbbbbb'

type HandlerResult = { content: Record<string, unknown>; is_error?: boolean }

function temporalMock(options: {
  fallbackRows?: Array<Record<string, unknown>>
  fallbackError?: Error
  fallbackSourceCount?: number
  buildRows?: Array<Record<string, unknown>>
}) {
  queryMock.mockImplementation((sqlValue: unknown) => {
    const sql = String(sqlValue)
    if (/FROM kala_activation\s+WHERE/.test(sql) && !/COUNT\(/.test(sql)) {
      return Promise.resolve({ rows: [] })
    }
    if (/COUNT\(\*\)::int AS total, COUNT\(activation_start\)::int AS dated/.test(sql)) {
      return Promise.resolve({ rows: [{ total: 12, dated: 12 }] })
    }
    if (/FROM build_run_assets bra/.test(sql)) {
      return Promise.resolve({ rows: options.buildRows ?? [] })
    }
    if (/SELECT id, signal_id, domain, probability_tier/.test(sql)) {
      if (options.fallbackError) return Promise.reject(options.fallbackError)
      return Promise.resolve({ rows: options.fallbackRows ?? [] })
    }
    if (/SELECT COUNT\(\*\)::int AS total FROM kala_bhavishya/.test(sql)) {
      return Promise.resolve({ rows: [{ total: options.fallbackSourceCount ?? 0 }] })
    }
    return Promise.resolve({ rows: [] })
  })
}

function projectionMock(options: {
  projectionRows?: Array<Record<string, unknown>>
  familyRows?: Array<Record<string, unknown>>
  sourceCount?: number
  buildRows?: Array<Record<string, unknown>>
}) {
  queryMock.mockImplementation((sqlValue: unknown) => {
    const sql = String(sqlValue)
    if (/FROM build_run_assets bra/.test(sql)) {
      return Promise.resolve({ rows: options.buildRows ?? [] })
    }
    if (/SELECT COUNT\(\*\)::int AS total FROM kala_bhavishya/.test(sql)) {
      return Promise.resolve({ rows: [{ total: options.sourceCount ?? 0 }] })
    }
    if (/GROUP BY window_start, window_end, domain/.test(sql)) {
      return Promise.resolve({ rows: options.familyRows ?? [] })
    }
    if (/FROM kala_bhavishya/.test(sql)) {
      return Promise.resolve({ rows: options.projectionRows ?? [] })
    }
    return Promise.resolve({ rows: [] })
  })
}

beforeEach(() => {
  queryMock.mockReset()
})

describe('L3-U05 — temporal fallback filter honesty', () => {
  it('applies signal_ids and domain to kala_bhavishya and reports requested/effective filters separately', async () => {
    temporalMock({
      fallbackRows: [{
        id: 'projection-1',
        signal_id: SIGNAL_ID,
        domain: 'career',
        window_start: '2028-01-01',
        window_end: '2028-02-01',
      }],
    })

    const response = await queryTemporalActivationCapability.handler({
      chart_id: CHART_ID,
      date_from: '2028-01-01',
      date_to: '2028-12-31',
      signal_ids: [SIGNAL_ID],
      domain: 'career',
    }, undefined) as HandlerResult

    const fallbackCall = queryMock.mock.calls.find(([sql]) => /SELECT id, signal_id, domain, probability_tier/.test(String(sql)))
    expect(fallbackCall).toBeDefined()
    expect(String(fallbackCall?.[0])).toMatch(/signal_id IN \(\$\d+\)/)
    expect(String(fallbackCall?.[0])).toMatch(/domain = \$\d+/)
    expect(fallbackCall?.[1]).toContain(SIGNAL_ID)
    expect(fallbackCall?.[1]).toContain('career')

    const status = response.content['forward_window_status'] as Record<string, unknown>
    expect(status['state']).toBe('served_unqualified')
    expect(status['incompatible_filters']).toEqual([])
    expect((status['requested_filters'] as Record<string, unknown>)['signal_ids']).toEqual([SIGNAL_ID])
    expect((status['effective_filters'] as Record<string, unknown>)['signal_ids']).toEqual([SIGNAL_ID])
    expect((status['effective_filters'] as Record<string, unknown>)['domain']).toBe('career')
    expect((status['effective_filters'] as Record<string, unknown>)['ayanamsha_id']).toBeNull()
    expect(status['data_qualification']).toMatchObject({
      state: 'unqualified',
      build_observation: { state: 'absent', build_id: null, physically_bound_to_rows: false },
      acceptance: { state: 'unavailable', accepted_current: null },
    })
  })

  it.each([
    [[], 'absent'],
    [[{
      build_id: '33333333-cccc-4ccc-cccc-cccccccccccc',
      build_state: 'running',
      asset_state: 'building',
      build_ended_at: null,
      asset_ended_at: null,
    }], 'incomplete_observed'],
    [[{
      build_id: '44444444-dddd-4ddd-dddd-dddddddddddd',
      build_state: 'completed',
      asset_state: 'complete',
      build_ended_at: '2026-09-15T00:00:00Z',
      asset_ended_at: '2026-09-15T00:00:00Z',
    }], 'completed_observed'],
  ])('serves fallback rows as unqualified with a %s build observation', async (buildRows, expectedBuildState) => {
    temporalMock({ fallbackRows: [{ id: 'projection-1' }], buildRows })

    const response = await queryTemporalActivationCapability.handler({
      chart_id: CHART_ID,
      date_from: '2028-01-01',
      date_to: '2028-12-31',
    }, undefined) as HandlerResult

    const status = response.content['forward_window_status'] as Record<string, unknown>
    expect(status['state']).toBe('served_unqualified')
    expect(status['data_qualification']).toMatchObject({
      state: 'unqualified',
      build_observation: { state: expectedBuildState, physically_bound_to_rows: false },
      acceptance: { state: 'unavailable', accepted_current: null },
    })
  })

  it.each([
    [{ ayanamsha_id: 'raman' }, 'ayanamsha_id'],
    [{ min_activation_strength: 0.6 }, 'min_activation_strength'],
  ])('closes an incompatible fallback instead of silently dropping %s', async (extra, incompatible) => {
    temporalMock({ fallbackRows: [{ id: 'must-not-serve' }] })

    const response = await queryTemporalActivationCapability.handler({
      chart_id: CHART_ID,
      date_from: '2028-01-01',
      date_to: '2028-12-31',
      ...extra,
    }, undefined) as HandlerResult

    expect(queryMock.mock.calls.some(([sql]) => /SELECT id, signal_id, domain, probability_tier/.test(String(sql)))).toBe(false)
    expect(response.content['forward_windows']).toEqual([])
    const status = response.content['forward_window_status'] as Record<string, unknown>
    expect(status['state']).toBe('incompatible_filters')
    expect(status['incompatible_filters']).toContain(incompatible)
    expect(status['effective_filters']).toBeNull()
  })

  it('distinguishes fallback DB failure from a successful empty search', async () => {
    temporalMock({ fallbackError: new Error('fallback unavailable') })

    const response = await queryTemporalActivationCapability.handler({
      chart_id: CHART_ID,
      date_from: '2028-01-01',
      date_to: '2028-12-31',
    }, undefined) as HandlerResult

    const status = response.content['forward_window_status'] as Record<string, unknown>
    expect(status['state']).toBe('db_failure')
    expect(String(status['error'])).toContain('fallback unavailable')
    expect(response.content['forward_windows']).toEqual([])
  })

  it.each([
    [0, 'source_empty'],
    [9, 'searched_empty'],
  ])('classifies an empty fallback with source count %i as %s', async (sourceCount, expectedState) => {
    temporalMock({ fallbackRows: [], fallbackSourceCount: sourceCount })

    const response = await queryTemporalActivationCapability.handler({
      chart_id: CHART_ID,
      date_from: '2028-01-01',
      date_to: '2028-12-31',
    }, undefined) as HandlerResult

    const status = response.content['forward_window_status'] as Record<string, unknown>
    expect(status['state']).toBe(expectedState)
    expect(status['source_row_count']).toBe(sourceCount)
  })

  it('keeps a legitimately zero-row completed build source_empty rather than inferring unbuilt', async () => {
    temporalMock({
      fallbackRows: [],
      fallbackSourceCount: 0,
      buildRows: [{
        build_id: '55555555-eeee-4eee-eeee-eeeeeeeeeeee',
        build_state: 'completed',
        asset_state: 'complete',
        build_ended_at: '2026-09-15T00:00:00Z',
        asset_ended_at: '2026-09-15T00:00:00Z',
      }],
    })

    const response = await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined) as HandlerResult
    const status = response.content['forward_window_status'] as Record<string, unknown>
    expect(status).toMatchObject({
      state: 'source_empty',
      source_row_count: 0,
      data_qualification: {
        state: 'unqualified',
        build_observation: { state: 'completed_observed', physically_bound_to_rows: false },
      },
    })
  })
})

describe('L3-U05 — projection source and qualification honesty', () => {
  it('serves rows but leaves accepted-current and generation qualification explicitly unavailable', async () => {
    projectionMock({
      projectionRows: [{
        id: 'projection-1', signal_id: SIGNAL_ID, domain: 'career',
        probability_tier: 'tier_1_high', effective_score: 0.8,
      }],
      familyRows: [],
      buildRows: [{
        build_id: '33333333-cccc-4ccc-cccc-cccccccccccc',
        build_state: 'completed',
        asset_state: 'complete',
        build_ended_at: '2026-09-15T00:00:00Z',
        asset_ended_at: '2026-09-15T00:00:00Z',
      }],
    })

    const response = await queryProjectionsCapability.handler({ chart_id: CHART_ID }, undefined) as HandlerResult

    expect(response.content['source_status']).toMatchObject({ state: 'served', source_table: 'kala_bhavishya' })
    const qualification = response.content['data_qualification'] as Record<string, unknown>
    expect(qualification['state']).toBe('unqualified')
    expect(qualification['generation']).toMatchObject({ state: 'unavailable', generation_id: null })
    expect(qualification['build_observation']).toMatchObject({
      state: 'completed_observed',
      physically_bound_to_rows: false,
    })
    expect(qualification['acceptance']).toMatchObject({ state: 'unavailable', accepted_current: null })
  })

  it.each([
    [0, 'source_empty'],
    [7, 'searched_empty'],
  ])('distinguishes empty source count %i as %s', async (sourceCount, expectedState) => {
    projectionMock({ projectionRows: [], familyRows: [], sourceCount })

    const response = await queryProjectionsCapability.handler({
      chart_id: CHART_ID,
      domain: 'career',
    }, undefined) as HandlerResult

    expect(response.content['source_status']).toMatchObject({
      state: expectedState,
      source_row_count: sourceCount,
    })
  })

  it('reports source_empty when a valid completed build legitimately produced zero rows', async () => {
    projectionMock({
      projectionRows: [],
      familyRows: [],
      sourceCount: 0,
      buildRows: [{
        build_id: '66666666-ffff-4fff-ffff-ffffffffffff',
        build_state: 'completed',
        asset_state: 'complete',
        build_ended_at: '2026-09-15T00:00:00Z',
        asset_ended_at: '2026-09-15T00:00:00Z',
      }],
    })

    const response = await queryProjectionsCapability.handler({ chart_id: CHART_ID }, undefined) as HandlerResult
    expect(response.content['source_status']).toMatchObject({ state: 'source_empty', source_row_count: 0 })
    expect(response.content['data_qualification']).toMatchObject({
      state: 'unqualified',
      build_observation: { state: 'completed_observed', physically_bound_to_rows: false },
      acceptance: { state: 'unavailable', accepted_current: null },
    })
  })

  it('preserves served rows while reporting a qualification lookup failure', async () => {
    projectionMock({ projectionRows: [{ id: 'projection-1' }], familyRows: [] })
    queryMock.mockImplementation((sqlValue: unknown) => {
      const sql = String(sqlValue)
      if (/FROM build_run_assets bra/.test(sql)) return Promise.reject(new Error('build ledger unavailable'))
      if (/GROUP BY window_start, window_end, domain/.test(sql)) return Promise.resolve({ rows: [] })
      if (/FROM kala_bhavishya/.test(sql)) return Promise.resolve({ rows: [{ id: 'projection-1' }] })
      return Promise.resolve({ rows: [] })
    })

    const response = await queryProjectionsCapability.handler({ chart_id: CHART_ID }, undefined) as HandlerResult
    expect(response.is_error).toBe(false)
    expect(response.content['projections']).toHaveLength(1)
    const qualification = response.content['data_qualification'] as Record<string, unknown>
    expect(qualification['build_observation']).toMatchObject({ state: 'unavailable', physically_bound_to_rows: false })
    expect(String((qualification['build_observation'] as Record<string, unknown>)['error'])).toContain('build ledger unavailable')
    expect(qualification['acceptance']).toMatchObject({ state: 'unavailable', accepted_current: null })
  })

  it('reports a projection-table DB failure distinctly and makes all qualification unavailable', async () => {
    queryMock.mockImplementation((sqlValue: unknown) => {
      const sql = String(sqlValue)
      if (/FROM build_run_assets bra/.test(sql)) return Promise.resolve({ rows: [] })
      if (/FROM kala_bhavishya/.test(sql)) return Promise.reject(new Error('projection table unavailable'))
      return Promise.resolve({ rows: [] })
    })

    const response = await queryProjectionsCapability.handler({ chart_id: CHART_ID }, undefined) as HandlerResult
    expect(response.is_error).toBe(true)
    expect(response.content['source_status']).toMatchObject({
      state: 'db_failure',
      source_table: 'kala_bhavishya',
      source_row_count: null,
    })
    expect(response.content['data_qualification']).toMatchObject({
      state: 'unavailable',
      acceptance: { state: 'unavailable', accepted_current: null },
    })
  })
})
