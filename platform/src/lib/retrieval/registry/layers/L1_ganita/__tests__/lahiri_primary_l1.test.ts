/**
 * Lahiri primary PR-2 — L1 handler specifics beyond the table-driven registry test:
 *   - get_yoga_dosha: the kala-sarpa verdict reads the PRIMARY ayanamsha's row even when rows of
 *     all five ayanamshas are present (it used to read krishnamurti's),
 *   - get_eclipse_flags: the new ayanamsha_id parameter,
 *   - citation_human (SS N-345): served beside citation_ref on the typed readers; present and
 *     non-empty where the row has it, honest null where it does not.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getYogaDoshaCapability } from '../get_yoga_dosha'
import { getEclipseFlagsCapability } from '../get_eclipse_flags'
import { getNakshatraCapability } from '../get_nakshatra'
import { getAyurdayaCapability } from '../get_ayurdaya'
import { getPanchangaCapability } from '../get_panchanga'
import { getPositionsCapability } from '../get_positions'
import { getSadeSatiCapability } from '../get_sade_sati'
import { getSensitiveDegreesCapability } from '../get_sensitive_degrees'
import { getSensitivePointsCapability } from '../get_sensitive_points'
import { getStrengthCapability } from '../get_strength'
import { getStructuralSignalsCapability } from '../get_structural_signals'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const LAHIRI = 'lahiri_chitrapaksha'
beforeEach(() => mockQuery.mockReset())

describe('get_yoga_dosha kala-sarpa verdict with all five ayanamshas present', () => {
  // Per-ayanamsha D1 verdicts: krishnamurti and raman say "does not fire", Lahiri says "fires".
  const ks = [
    ['krishnamurti', false], ['lahiri_chitrapaksha', true], ['raman', false],
    ['surya_siddhanta_classical', false], ['true_chitra', false],
  ].map(([a, fires]) => ({ ayanamsha_id: a, fact_value_jsonb: { varga: 'D1', fires } }))
  const labels = ks.map((r) => ({
    ayanamsha_id: r.ayanamsha_id, fact_category: 'dosha_label', fact_subject: 'kala_sarpa',
    fact_value_jsonb: { fires: (r.fact_value_jsonb as { fires: boolean }).fires, catalog_only: false },
  }))

  function mockAll() {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })       // count
    mockQuery.mockResolvedValueOnce({ rows: labels })                  // page (krishnamurti first)
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })       // firings count
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })       // gated count
    mockQuery.mockResolvedValueOnce({ rows: ks })                      // kala_sarpa_per_varga (krishnamurti first)
  }

  it('pooled ("all"): reconciliation compares the LAHIRI label with the LAHIRI D1 fact, not natal[0]', async () => {
    mockAll()
    const res = await getYogaDoshaCapability.handler({ chart_id: CHART_ID, facet: 'dosha_fires', ayanamsha_id: 'all' }, undefined)
    const recon = (res.content as Record<string, unknown>)['kala_sarpa_reconciliation'] as Record<string, unknown>
    expect(recon['verdict_ayanamsha_id']).toBe(LAHIRI)
    expect(recon['per_varga_d1_fires']).toBe(true)
    expect(recon['dosha_label_fires']).toBe(true)
    expect(recon['agrees']).toBe(true)
    expect((res.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
  })

  it('default: every one of its statements is filtered to Lahiri', async () => {
    mockQuery.mockResolvedValue({ rows: [{ total: '0' }] })
    await getYogaDoshaCapability.handler({ chart_id: CHART_ID, facet: 'dosha_fires' }, undefined)
    expect(mockQuery.mock.calls.length).toBeGreaterThan(0)
    for (const [sql, params] of mockQuery.mock.calls as Array<[string, unknown[]]>) {
      expect(params, sql).toContain(LAHIRI)
    }
  })
})

describe('get_eclipse_flags ayanamsha_id parameter', () => {
  it('declares ayanamsha_id', () => {
    expect(getEclipseFlagsCapability.input_schema).toHaveProperty('ayanamsha_id')
  })
  it('omitted -> Lahiri bound; "all" -> unfiltered, serve-ordered, scope marker; unknown -> error', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    await getEclipseFlagsCapability.handler({ chart_id: CHART_ID }, undefined)
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params).toEqual([CHART_ID, 20, 0, LAHIRI])
    expect(sql).toMatch(/ayanamsha_id = \$4/)
    mockQuery.mockClear()
    const all = await getEclipseFlagsCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'all' }, undefined)
    const [sqlAll, paramsAll] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(paramsAll).toEqual([CHART_ID, 20, 0])
    expect(sqlAll).toMatch(/array_position\(ARRAY\['lahiri_chitrapaksha'/)
    expect((all.content as Record<string, unknown>)['ayanamsha_scope']).toBe('all')
    mockQuery.mockClear()
    const bad = await getEclipseFlagsCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'bogus' }, undefined)
    expect(bad.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('citation_human (SS N-345): served beside citation_ref on the typed readers', () => {
  const READERS = [
    ['get_nakshatra', getNakshatraCapability],
    ['get_ayurdaya', getAyurdayaCapability],
    ['get_panchanga', getPanchangaCapability],
    ['get_positions', getPositionsCapability],
    ['get_sade_sati', getSadeSatiCapability],
    ['get_sensitive_degrees', getSensitiveDegreesCapability],
    ['get_sensitive_points', getSensitivePointsCapability],
    ['get_strength', getStrengthCapability],
    ['get_structural_signals', getStructuralSignalsCapability],
  ] as const

  const rowWith = { fact_id: 'f1', fact_category: 'graha_position', fact_subject: 'SUN', ayanamsha_id: LAHIRI, fact_key: 'sign', citation_ref: 'ref-1', citation_human: 'Sun in Capricorn (Lahiri), whole-sign.' }
  const rowWithout = { fact_id: 'f2', fact_category: 'graha_position', fact_subject: 'MOON', ayanamsha_id: LAHIRI, fact_key: 'sign', citation_ref: 'ref-2', citation_human: null }
  const rowBlank = { fact_id: 'f3', fact_category: 'graha_position', fact_subject: 'MAR', ayanamsha_id: LAHIRI, fact_key: 'sign', citation_ref: 'ref-3', citation_human: '   ' }
  const rowMissing = { fact_id: 'f4', fact_category: 'graha_position', fact_subject: 'JUP', ayanamsha_id: LAHIRI, fact_key: 'sign', citation_ref: 'ref-4' }

  it.each(READERS)('%s selects citation_human next to citation_ref', async (_n, cap) => {
    mockQuery.mockResolvedValue({ rows: [] })
    await cap.handler({ chart_id: CHART_ID }, undefined)
    const selectSql = (mockQuery.mock.calls as Array<[string]>).map((c) => String(c[0])).find((s) => /citation_ref/.test(s))!
    expect(selectSql.replace(/\s+/g, ' ')).toMatch(/citation_ref,[^;]*NULLIF\(BTRIM\(citation_human\), ''\) AS citation_human|citation_human[^;]*citation_ref/)
  })

  it.each(READERS)('%s: present+non-empty where the row has it; null where it does not (never a default)', async (_n, cap) => {
    mockQuery.mockImplementation((sql: unknown) =>
      /COUNT\(\*\)/.test(String(sql)) && !/citation_ref/.test(String(sql))
        ? Promise.resolve({ rows: [{ total: '4', n: 4, total_count: 4 }] })
        : Promise.resolve({ rows: [{ ...rowWith }, { ...rowWithout }, { ...rowBlank }, { ...rowMissing }] }))
    const res = await cap.handler({ chart_id: CHART_ID, all: true, limit: 10 }, undefined)
    expect(res.is_error).toBe(false)
    const rows = (res.content as { rows: Array<Record<string, unknown>> }).rows
    const byId = new Map(rows.map((r) => [r['fact_id'], r]))
    expect(byId.get('f1')?.['citation_human']).toBe('Sun in Capricorn (Lahiri), whole-sign.')
    expect(byId.get('f1')?.['citation_ref']).toBe('ref-1')
    for (const id of ['f2', 'f3', 'f4']) {
      const r = byId.get(id)
      expect(r, `${id} served`).toBeDefined()
      expect(r!['citation_human'], `${id}: honest null`).toBeNull()
      expect('citation_human' in r!, `${id}: the key is present as null`).toBe(true)
    }
  })
})
