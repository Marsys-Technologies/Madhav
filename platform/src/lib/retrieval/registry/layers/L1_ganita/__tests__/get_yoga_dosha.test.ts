/**
 * get_yoga_dosha.test.ts — D-1.5b Lane B-6 (item 5, B9 dosha gate) unit tests.
 * No live DB required — `query` is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getYogaDoshaCapability } from '../get_yoga_dosha'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getYogaDoshaCapability (backs ganita_yogas_get) — B9 dosha gate', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('excludes catalog-only dosha_label (fire_reason=requires_pass) rows from SQL by default', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })   // countResult
    mockQuery.mockResolvedValueOnce({ rows: [] })                  // result (paged rows)
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })    // firingsCountResult
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })    // doshaGatedCountResult

    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)

    // Both the count query and the paged SELECT must carry the gate clause when all is not set.
    const countSql = mockQuery.mock.calls[0][0] as string
    const rowsSql = mockQuery.mock.calls[1][0] as string
    expect(countSql).toMatch(/NOT \(fact_category = 'dosha_label'/)
    expect(rowsSql).toMatch(/NOT \(fact_category = 'dosha_label'/)

    const content = result.content as Record<string, unknown>
    const gate = content['dosha_label_gate'] as Record<string, unknown>
    expect(gate['applied']).toBe(true)
    expect(gate['all']).toBe(false)
    expect(gate['excluded_total']).toBe(2)
  })

  it('all=true lifts the gate — no gate clause in SQL, excluded_total reported as 0', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '7' }] })   // countResult
    mockQuery.mockResolvedValueOnce({ rows: [] })                  // result
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })    // firingsCountResult
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })    // doshaGatedCountResult (unused when all=true)

    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID, all: true }, undefined)
    const countSql = mockQuery.mock.calls[0][0] as string
    expect(countSql).not.toMatch(/requires_pass/)

    const content = result.content as Record<string, unknown>
    const gate = content['dosha_label_gate'] as Record<string, unknown>
    expect(gate['applied']).toBe(false)
    expect(gate['all']).toBe(true)
    expect(gate['excluded_total']).toBe(0)
  })

  it('requires chart_id-shaped input to run without throwing (defensive smoke)', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
  })
})

describe('getYogaDoshaCapability — kala_sarpa_reconciliation (D-1.6 Lane S-2 item c)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('agrees=true when dosha_label kala_sarpa fires=true and per-varga D1 fires=true', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })   // countResult
    mockQuery.mockResolvedValueOnce({
      rows: [{
        fact_category: 'dosha_label', fact_subject: 'kala_sarpa',
        fact_value_jsonb: { fires: true, catalog_only: false },
      }],
    }) // result (paged rows)
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })    // firingsCountResult
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })    // doshaGatedCountResult
    mockQuery.mockResolvedValueOnce({
      rows: [{ fact_value_jsonb: { varga: 'D1', fires: true } }],
    }) // kala_sarpa_per_varga SELECT (only fired when facet=dosha_fires)

    const result = await getYogaDoshaCapability.handler(
      { chart_id: CHART_ID, facet: 'dosha_fires' }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const recon = content['kala_sarpa_reconciliation'] as Record<string, unknown>
    expect(recon['dosha_label_row_served']).toBe(true)
    expect(recon['dosha_label_fires']).toBe(true)
    expect(recon['per_varga_d1_fires']).toBe(true)
    expect(recon['agrees']).toBe(true)
  })

  it('agrees=true when kala_sarpa dosha_label row is honestly absent (does not form) and D1 fires=false', async () => {
    // Reproduces the live 482012f1 specimen: kala_sarpa_per_varga D1 fires=false
    // (Rahu H2/Ketu H8, not axis-hemmed) — the bespoke detector correctly never
    // writes a dosha_label row at all (honest absence per CR-74), which must
    // read as AGREEMENT with the per-varga false verdict, not a gap.
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] }) // no dosha_label kala_sarpa row served
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({
      rows: [{ fact_value_jsonb: { varga: 'D1', fires: false } }],
    })

    const result = await getYogaDoshaCapability.handler(
      { chart_id: CHART_ID, facet: 'dosha_fires' }, undefined,
    )
    const content = result.content as Record<string, unknown>
    const recon = content['kala_sarpa_reconciliation'] as Record<string, unknown>
    expect(recon['dosha_label_row_served']).toBe(false)
    expect(recon['dosha_label_fires']).toBe(false)
    expect(recon['per_varga_d1_fires']).toBe(false)
    expect(recon['agrees']).toBe(true)
  })

  it('agrees=false and flags CONTRADICTION when the label row fires but D1 per-varga does not', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })
    mockQuery.mockResolvedValueOnce({
      rows: [{
        fact_category: 'dosha_label', fact_subject: 'kala_sarpa',
        fact_value_jsonb: { fires: true, catalog_only: false },
      }],
    })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({
      rows: [{ fact_value_jsonb: { varga: 'D1', fires: false } }],
    })

    const result = await getYogaDoshaCapability.handler(
      { chart_id: CHART_ID, facet: 'dosha_fires' }, undefined,
    )
    const content = result.content as Record<string, unknown>
    const recon = content['kala_sarpa_reconciliation'] as Record<string, unknown>
    expect(recon['agrees']).toBe(false)
    expect(String(recon['note'])).toMatch(/CONTRADICTION/)
  })

  it('is omitted from the response when facet is not dosha_fires (no per-varga fetch happened)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })

    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['kala_sarpa_reconciliation']).toBeUndefined()
  })
})
