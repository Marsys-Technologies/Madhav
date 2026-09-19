/**
 * Bounded closure contract for query_temporal_activation.
 *
 * This is deliberately a handler-boundary suite. The route remains a capped
 * temporal-window read; the regression proves it tells the inquiry lifecycle
 * exactly when that cap leaves required evidence unresolved.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryTemporalActivationCapability } from './query_temporal_activation'
import { getCatalog } from '../../catalog'
import { compileCapabilityKnowledge } from '../../knowledge/compiler'
import type { SemanticCapabilityBinding } from '../../knowledge/types'
import { deriveInquiryPaginationReceipt } from '@/lib/vidhi/inquiry/pagination'
import { compileInquiryContract, finalizeInquiryContract, recordInquiryExecution } from '@/lib/vidhi/inquiry/compiler'
import type { ScopeTuple } from '@/lib/vidhi/types'

type Handler = (args: Record<string, unknown>, ctx?: unknown) => Promise<{
  content: Record<string, unknown>
  is_error?: boolean
}>

const handler = queryTemporalActivationCapability.handler as Handler
const CHART_ID = '11111111-1111-4111-8111-111111111111'

const ROWS = [
  { id: 'row-1', signal_id: 'sig-1', activation_start: '2026-01-01', activation_end: '2026-01-31', activation_peak_date: '2026-01-10', dasha_activation_proximity_score: 0.9, orb_strength: 0.5, domains_affected_array: ['wealth'] },
  { id: 'row-2', signal_id: 'sig-2', activation_start: '2026-02-01', activation_end: '2026-02-28', activation_peak_date: '2026-02-10', dasha_activation_proximity_score: 0.8, orb_strength: 0.4, domains_affected_array: ['wealth'] },
]

/** Route query mocks by source SQL rather than the handler's call order. */
function routeQueries(options: { activations: Record<string, unknown>[]; totalMatching: number; sourceTotal?: number; sourceDated?: number }) {
  queryMock.mockImplementation((sql: unknown) => {
    const text = typeof sql === 'string' ? sql : ''
    if (text.includes('FROM kala_activation_predicates')) return Promise.resolve({ rows: [] })
    if (text.includes('SELECT id, signal_id, ayanamsha_id, signature_class')) {
      return Promise.resolve({ rows: options.activations.map((row) => ({ ...row, total_matching: options.totalMatching })) })
    }
    if (text.includes('COUNT(*)::int AS total, COUNT(activation_start)::int AS dated')) {
      return Promise.resolve({ rows: [{ total: options.sourceTotal ?? 0, dated: options.sourceDated ?? 0 }] })
    }
    // Empty primary responses consult a bounded qualification and fallback
    // surface. Keep those facts explicit in the fixture instead of letting an
    // unmatched mock accidentally turn an honest empty into an exception.
    if (text.includes('FROM build_run_assets bra')) return Promise.resolve({ rows: [] })
    if (text.includes('FROM kala_bhavishya') && text.includes('SELECT id, signal_id')) return Promise.resolve({ rows: [] })
    if (text.includes('SELECT COUNT(*)::int AS total FROM kala_bhavishya')) return Promise.resolve({ rows: [{ total: 0 }] })
    if (!text) return Promise.resolve({ rows: [] })
    throw new Error(`unexpected query: ${text}`)
  })
}

function temporalBinding(): SemanticCapabilityBinding {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-17T00:00:00.000Z')
  return snapshot.scus.find((scu) => scu.scu_id === 'scu.kala.temporal_activation')!
    .bindings.find((binding) => binding.binding_id === 'registry:marsys://tool/L3/query_temporal_activation')!
}

function mutableRecord(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} fixture is not an object`)
  return value as Record<string, unknown>
}

function mutableContent(raw: Record<string, unknown>): Record<string, unknown> {
  return mutableRecord(raw['content'], 'content')
}

function mutableClosure(raw: Record<string, unknown>): Record<string, unknown> {
  return mutableRecord(mutableContent(raw)['temporal_closure'], 'temporal closure')
}

const wealthScope: ScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'panoramic',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: false,
  entitlement: 'native',
}

beforeEach(() => queryMock.mockReset())

describe('query_temporal_activation bounded temporal closure', () => {
  it('returns the first ranked page with an exact filter-bound closure basis', async () => {
    routeQueries({ activations: ROWS, totalMatching: 2 })

    const result = await handler({
      chart_id: CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      date_from: '2026-01-01',
      date_to: '2026-12-31',
      signal_ids: ['sig-2', 'sig-1', 'sig-1'],
      domain: 'wealth',
      top_k: 2,
    })

    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({
      activation_count: 2,
      total_matching: 2,
      more_available: false,
      truncated: false,
      temporal_closure: {
        state: 'complete_within_stated_window',
        collection: 'activations',
        exhaustive_within_stated_window: true,
        filters: {
          temporal_filter: { mode: 'range', date_from: '2026-01-01', date_to: '2026-12-31' },
          signal_ids: ['sig-1', 'sig-2'],
          domain: 'wealth',
        },
        limit: { effective_top_k: 2, maximum_top_k: 500, returned: 2, total_matching: 2 },
        continuation: { supported: false, next: null },
      },
    })
    const activationSql = String(queryMock.mock.calls.find(([sql]) => String(sql).includes('SELECT id, signal_id, ayanamsha_id, signature_class'))![0])
    expect(activationSql).toMatch(/ORDER BY dasha_activation_proximity_score DESC NULLS LAST,\s*orb_strength DESC NULLS LAST, activation_start ASC, id ASC/)
    expect(activationSql).toContain('COUNT(*) OVER()::int AS total_matching')
    expect(activationSql).toContain('activation_end >=')
    expect(activationSql).toContain('activation_start <=')
    expect(queryMock.mock.calls.some(([sql]) => sql === undefined)).toBe(false)
    expect((result.content['activations'] as Array<Record<string, unknown>>)[0]).not.toHaveProperty('total_matching')
    expect(temporalBinding().pagination_contract?.deterministic_order).toEqual([
      'dasha_activation_proximity_score DESC NULLS LAST',
      'orb_strength DESC NULLS LAST',
      'activation_start ASC',
      'id ASC',
    ])
  })

  it('marks a capped response incomplete instead of equating page length with exhaustion', async () => {
    routeQueries({ activations: ROWS, totalMatching: 3 })
    const result = await handler({ chart_id: CHART_ID, date_from: '2026-01-01', date_to: '2026-12-31', top_k: 2 })

    expect(result.content).toMatchObject({ total_matching: 3, more_available: true, truncated: true })
    expect(result.content['temporal_closure']).toMatchObject({
      state: 'bounded_window_incomplete',
      exhaustive_within_stated_window: false,
      continuation: { supported: false, next: null },
    })
    expect(String(((result.content['temporal_closure'] as Record<string, unknown>).continuation as Record<string, unknown>).reason))
      .toContain('required inquiry must remain unresolved')
  })

  it('admits only a complete, exact handler closure as bounded-window exhaustion', async () => {
    routeQueries({ activations: ROWS, totalMatching: 2 })
    const rawResult = await handler({
      chart_id: CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      date_from: '2026-01-01',
      date_to: '2026-12-31',
      signal_ids: ['sig-2', 'sig-1'],
      min_activation_strength: 0.4,
      domain: 'wealth',
      top_k: 2,
    })
    const binding = temporalBinding()

    expect(binding).toMatchObject({ bounded_window_closure: {
      receipt_path: 'content.temporal_closure',
      closure_version: 'temporal-activation-closure-v1',
      collection: 'activations',
    } })
    expect(deriveInquiryPaginationReceipt(binding, rawResult, {
      chart_id: CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      date_from: '2026-01-01',
      date_to: '2026-12-31',
      signal_ids: ['sig-2', 'sig-1'],
      min_activation_strength: 0.4,
      domain: 'wealth',
      top_k: 2,
    })).toEqual({ semantics: 'bounded_unverified', exhausted: true, next: null })
  })

  it.each([
    ['a truncated window', (raw: Record<string, unknown>) => {
      const content = mutableContent(raw)
      const closure = mutableClosure(raw)
      content['more_available'] = true
      content['truncated'] = true
      closure['state'] = 'bounded_window_incomplete'
      closure['exhaustive_within_stated_window'] = false
      mutableRecord(closure['limit'], 'temporal closure limit')['total_matching'] = 3
    }],
    ['an absent closure', (raw: Record<string, unknown>) => { delete mutableContent(raw)['temporal_closure'] }],
    ['a malformed closure', (raw: Record<string, unknown>) => { mutableContent(raw)['temporal_closure'] = 'not-a-receipt' }],
    ['inconsistent collection totals', (raw: Record<string, unknown>) => { mutableContent(raw)['total_matching'] = 3 }],
    ['a foreign query identity', (raw: Record<string, unknown>) => { mutableClosure(raw)['query_identity'] = 'sha256:foreign' }],
    ['a mismatched temporal window', (raw: Record<string, unknown>) => {
      const filters = mutableRecord(mutableClosure(raw)['filters'], 'temporal closure filters')
      mutableRecord(filters['temporal_filter'], 'temporal filter')['date_to'] = '2027-12-31'
    }],
  ])('keeps a required temporal frontier for %s', async (_caseName, mutate) => {
    routeQueries({ activations: ROWS, totalMatching: 2 })
    const rawResult = await handler({
      chart_id: CHART_ID,
      date_from: '2026-01-01',
      date_to: '2026-12-31',
      top_k: 2,
    })
    const tampered = JSON.parse(JSON.stringify(rawResult)) as Record<string, unknown>
    mutate(tampered)

    expect(deriveInquiryPaginationReceipt(temporalBinding(), tampered, {
      chart_id: CHART_ID,
      date_from: '2026-01-01',
      date_to: '2026-12-31',
      top_k: 2,
    })).toEqual({ semantics: 'bounded_unverified', exhausted: false, next: 'unproven' })
  })

  it('reports an empty exact window as complete within that window, not as an unbuilt source', async () => {
    routeQueries({ activations: [], totalMatching: 0, sourceTotal: 7, sourceDated: 7 })
    const result = await handler({ chart_id: CHART_ID, date_from: '2040-01-01', date_to: '2040-12-31', top_k: 2 })

    expect(result.is_error).toBe(false)
    expect(result.content).toMatchObject({ activation_count: 0, total_matching: 0, more_available: false, truncated: false })
    expect(result.content['temporal_closure']).toMatchObject({
      state: 'complete_within_stated_window',
      exhaustive_within_stated_window: true,
    })
    expect(String(result.content['empty_reason'])).toContain('No activation windows overlap the requested date range 2040-01-01..2040-12-31')
  })

  it('changes the bound query identity when the stated temporal window changes', async () => {
    routeQueries({ activations: ROWS, totalMatching: 2 })
    const first = await handler({ chart_id: CHART_ID, date_from: '2026-01-01', date_to: '2026-12-31', top_k: 2 })
    routeQueries({ activations: ROWS, totalMatching: 2 })
    const second = await handler({ chart_id: CHART_ID, date_from: '2027-01-01', date_to: '2027-12-31', top_k: 2 })

    const firstClosure = first.content['temporal_closure'] as Record<string, unknown>
    const secondClosure = second.content['temporal_closure'] as Record<string, unknown>
    expect(secondClosure['filter_identity']).not.toBe(firstClosure['filter_identity'])
    expect(secondClosure['query_identity']).not.toBe(firstClosure['query_identity'])
  })

  it('normalizes blank optional filters before SQL predicates, echoes, and closure fingerprints', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-17T00:00:00.000Z'))
    try {
      routeQueries({ activations: ROWS, totalMatching: 2 })
      const blank = await handler({
        chart_id: CHART_ID,
        ayanamsha_id: '   ',
        date_from: '  ',
        date_to: '',
        domain: '   ',
        top_k: 2,
      })
      routeQueries({ activations: ROWS, totalMatching: 2 })
      const omitted = await handler({ chart_id: CHART_ID, top_k: 2 })

      const blankClosure = blank.content['temporal_closure'] as Record<string, unknown>
      const omittedClosure = omitted.content['temporal_closure'] as Record<string, unknown>
      expect(blank.content['date_filter']).toMatchObject({ range_defaulted: true })
      expect(blank.content['filters']).toMatchObject({ domain: null })
      expect(blankClosure['filters']).toMatchObject({ domain: null })
      expect(blankClosure['filter_identity']).toBe(omittedClosure['filter_identity'])
      expect(blankClosure['query_identity']).toBe(omittedClosure['query_identity'])
      expect(JSON.stringify(blank.content)).not.toContain('   ')
      const activationCalls = queryMock.mock.calls.filter(([sql]) => String(sql).includes('COUNT(*) OVER()::int AS total_matching'))
      expect(activationCalls).toHaveLength(2)
      for (const [, params] of activationCalls) {
        expect((params as unknown[])[1]).toBe('lahiri_chitrapaksha')
      }
      const activationSql = String(activationCalls[0]![0])
      expect(activationSql).not.toContain('domains_affected_array))')

      // A blank ayanamsha must also remain compatible with the forward-window
      // fallback. Treating it as explicit would incorrectly close the fallback
      // behind `incompatible_filters` even though SQL used the default variant.
      queryMock.mockClear()
      routeQueries({ activations: [], totalMatching: 0, sourceTotal: 7, sourceDated: 7 })
      const blankFallback = await handler({ chart_id: CHART_ID, ayanamsha_id: '   ', top_k: 2 })
      queryMock.mockClear()
      routeQueries({ activations: [], totalMatching: 0, sourceTotal: 7, sourceDated: 7 })
      const omittedFallback = await handler({ chart_id: CHART_ID, top_k: 2 })
      expect(blankFallback.content['forward_window_status']).toMatchObject({ state: 'source_empty', incompatible_filters: [] })
      expect(omittedFallback.content['forward_window_status']).toMatchObject({ state: 'source_empty', incompatible_filters: [] })
    } finally {
      vi.useRealTimers()
    }
  })

  it('keeps a required temporal result unresolved in the inquiry lifecycle when the bounded window is trimmed', async () => {
    routeQueries({ activations: ROWS, totalMatching: 3 })
    const rawResult = await handler({ chart_id: CHART_ID, date_from: '2026-01-01', date_to: '2026-12-31', top_k: 2 })
    const binding = temporalBinding()
    const pagination = deriveInquiryPaginationReceipt(binding, rawResult, { top_k: 2 })
    expect(pagination).toEqual({ semantics: 'bounded_unverified', exhausted: false, next: 'unproven' })

    const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-17T00:00:00.000Z')
    const initial = compileInquiryContract({
      snapshot,
      chart_id: CHART_ID,
      question: 'Complete wealth timing outlook',
      scope_tuple: wealthScope,
      temporal_anchor_date: '2026-09-17',
      max_iterations: 1,
    })
    const temporalItem = initial.plan_items.find((item) => item.scu_id === 'scu.kala.temporal_activation')!
    const observed = recordInquiryExecution(initial, {
      item_id: temporalItem.item_id,
      disposition: 'served',
      evidence_refs: ['test:bounded-temporal-window'],
      pagination,
    })
    expect(observed.material_frontier).toContainEqual(expect.objectContaining({
      scu_id: 'scu.kala.temporal_activation', materiality: 'required', disposition: 'capped',
    }))
    expect(finalizeInquiryContract(observed).status).toBe('BLOCKED')
  })
})
