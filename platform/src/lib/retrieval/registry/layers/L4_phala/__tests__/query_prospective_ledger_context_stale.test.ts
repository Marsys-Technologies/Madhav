/**
 * query_prospective_ledger (standing_predictions_read) — chart-context
 * staleness (Jātaka Phase-A3, item 2).
 *
 * The current-serving "standing predictions" surface excludes a row a
 * correction has marked chart_context_stale_at (migration 1123) by default; a
 * new include_stale input discloses it with explicit historical-context
 * metadata — never silently indistinguishable from a current row.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, params: unknown[]) => mockQuery(sql, params) }))

import { queryProspectiveLedgerCapability } from '../query_prospective_ledger'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [] })
})

describe('query_prospective_ledger — default view excludes context-stale rows', () => {
  it('scopes the query to chart_context_stale_at IS NULL', async () => {
    await queryProspectiveLedgerCapability.handler({ chart_id: CHART }, undefined)
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})

describe('query_prospective_ledger — include_stale discloses stale rows with explicit metadata', () => {
  it('drops the exclusion and stamps each row chart_context', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        {
          prediction_id: 'p1', chart_id: CHART, claim: 'x', event_class: 'career_change', claim_shape: 'point',
          observation_window: null, milestone_set: null, model: 'm', formula_version: 'v1', confidence: 0.5,
          falsifier: 'f', as_of: '2026-01-01', generator_class: 'reading_synthesis', configuration_signature: null,
          lifecycle_status: 'open', matched_event_id: null, matched_at: null, match_note: null,
          filed_by: 'x', filing_method: 'auto', source_citation: 'c', created_at: '2026-01-01',
          ontology_domain: null,
          chart_context_stale_at: '2026-09-27T00:00:00Z', chart_context_stale_reason: 'chart_details_changed', chart_context_superseded_by_run_id: 'run-1',
        },
      ],
    })
    const result = await queryProspectiveLedgerCapability.handler({ chart_id: CHART, include_stale: true }, undefined)
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).not.toMatch(/chart_context_stale_at\s+IS\s+NULL/)
    const content = (result as { content: { predictions: Array<Record<string, unknown>> } }).content
    expect(content.predictions[0]).toMatchObject({
      chart_context: { current: false, stale_reason: 'chart_details_changed', superseded_by_run_id: 'run-1' },
    })
  })
})
