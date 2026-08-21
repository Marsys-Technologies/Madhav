/**
 * F-107 (PARIŚEṢA-V4, CL-20) — cross-varga scope disclosure regression tests.
 * ==========================================================================
 * The defect: `bodha_mechanisms_get`, asked "what convergent mechanisms across my D1, D2,
 * D11 and Indu Lagna support or contradict wealth accumulation?", returned its rāśi-D1-only
 * mechanism list with NO field, filter, facet or note anywhere in the envelope saying the
 * cross-varga half of the question was never computed — a silent substitution of a narrower
 * answer for the one asked.
 *
 * These tests lock the disclosure, not the mechanism rows. They deliberately assert the
 * NEGATIVE claim is stated (`cross_varga_mechanisms_computed: false`) rather than asserting
 * any cross-varga finding exists — per CLAUDE.md §N.8, a signal with no detector behind it
 * must read null, not green, and this fix adds honesty, not a guessed detector.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { queryMechanismsCapability } from '../query_mechanisms'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

/**
 * Route each stubbed result by inspecting the SQL, not by call order — the handler issues a
 * rows SELECT, a COUNT and a facet rollup, and an order-coupled stub silently breaks the
 * moment their order changes.
 */
function stubDb(rows: Record<string, unknown>[], facets: Record<string, unknown>[]) {
  queryMock.mockReset()
  queryMock.mockImplementation((sql: string) => {
    if (/count\(\*\)/i.test(sql) && !/group by/i.test(sql)) {
      return Promise.resolve({ rows: [{ n: String(rows.length) }] })
    }
    if (/group by/i.test(sql)) return Promise.resolve({ rows: facets })
    return Promise.resolve({ rows })
  })
}

const D1_ROW = {
  mechanism_id: '5088c9e6-9b21-4703-a426-2135abc92f0e',
  ayanamsha_id: 'lahiri_chitrapaksha',
  snapshot_type: 'static_natal',
  mechanism_name: 'Convergent dispositor chain onto Jupiter',
  mechanism_class: 'convergent_dispositor_chain',
  valence: 'mixed',
  is_chain_circuit: true,
}

describe('F-107 — bodha_mechanisms_get varga-scope disclosure', () => {
  beforeEach(() => queryMock.mockReset())

  it('states the D1-only scope on a POPULATED response (the actual F-107 reproducer shape)', async () => {
    stubDb([D1_ROW], [{ mechanism_class: 'convergent_dispositor_chain', valence: 'mixed', is_chain_circuit: true, n: 1 }])

    const res = await queryMechanismsCapability.handler({ chart_id: CHART }, undefined)
    expect(res.is_error).toBe(false)
    const c = res.content as Record<string, unknown>

    // The row set is unchanged — no data is dropped or invented (B.10).
    expect((c['rows'] as unknown[]).length).toBe(1)

    const scope = c['varga_scope'] as Record<string, unknown>
    expect(scope).toBeDefined()
    expect(scope['computed_over']).toEqual(['D1'])
    expect(scope['frame']).toBe('rasi_d1_natal_graph_only')
    // The load-bearing negative claim: never silently true.
    expect(scope['cross_varga_mechanisms_computed']).toBe(false)
    expect(c['scope_flags']).toEqual(['d1_rasi_only', 'cross_varga_mechanisms_not_computed'])
  })

  it('names D2, D11 and Indu Lagna specifically — the three legs DC-W-16 asked for', async () => {
    stubDb([D1_ROW], [{ mechanism_class: 'convergent_dispositor_chain', valence: 'mixed', is_chain_circuit: true, n: 1 }])
    const c = (await queryMechanismsCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, unknown>
    const blob = JSON.stringify(c['varga_scope'])

    for (const leg of ['D2', 'D11', 'Indu Lagna']) {
      expect(blob).toContain(leg)
    }
  })

  it('points at ganita_vichara_get — the one real cross-varga convergence primitive that exists', async () => {
    stubDb([D1_ROW], [{ mechanism_class: 'convergent_dispositor_chain', valence: 'mixed', is_chain_circuit: true, n: 1 }])
    const c = (await queryMechanismsCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, unknown>
    const scope = c['varga_scope'] as Record<string, unknown>
    const pointers = scope['drill_pointers'] as Record<string, unknown>[]

    const vichara = pointers.find(p => p['instrument'] === 'ganita_vichara_get')
    expect(vichara, 'the varga_ratification pointer must be present and FIRST — it is closer to a cross-varga question than any D1 row here').toBeDefined()
    expect(pointers[0]?.['instrument']).toBe('ganita_vichara_get')
    expect(String(vichara?.['serves'])).toContain('varga_ratification')
    // The ratified wealth operative-varga set, verified live against chart_vichara.
    expect(String(vichara?.['note'])).toContain("['D1','D2','D9','D11']")
    // The honest limit of that primitive: it covers vargas, not special lagnas.
    expect(String(vichara?.['note'])).toContain('Indu Lagna is a special lagna, not a varga')

    for (const instrument of ['assess_wealth', 'ganita_chart_facts_get', 'ganita_special_lagnas_get']) {
      expect(pointers.some(p => p['instrument'] === instrument)).toBe(true)
    }
  })

  it('keeps the disclosure on an EMPTY result too (empty_reason must not displace it)', async () => {
    stubDb([], [])
    const c = (await queryMechanismsCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, unknown>

    expect(c['empty_reason']).toBeTruthy()
    expect((c['varga_scope'] as Record<string, unknown>)['cross_varga_mechanisms_computed']).toBe(false)
  })

  it('declares the D1-only scope in the tool DESCRIPTION, so a caller sees it before calling', () => {
    const d = queryMechanismsCapability.description
    expect(d).toContain('RĀŚI (D1) natal graph ONLY')
    expect(d).toContain('varga_scope')
  })

  it('provenance.source states the scope, not just the tables', async () => {
    stubDb([D1_ROW], [{ mechanism_class: 'convergent_dispositor_chain', valence: 'mixed', is_chain_circuit: true, n: 1 }])
    const c = (await queryMechanismsCapability.handler({ chart_id: CHART }, undefined)).content as Record<string, unknown>
    expect(String((c['provenance'] as Record<string, unknown>)['source'])).toContain('rāśi (D1) natal graph ONLY')
  })
})
