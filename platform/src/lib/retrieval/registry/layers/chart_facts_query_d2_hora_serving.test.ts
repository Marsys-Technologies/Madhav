/**
 * chart_facts_query_d2_hora_serving.test.ts — D-1.5b Gate B (CR-58) regression pin.
 *
 * Defect: the D2 hora-class data IS built correctly in `chart_divisionals`
 * (fact_category='varga_hora_class', fact_key in {hora_class, hora_d2_house}, fact_value_text
 * in {surya_hora, chandra_hora}), but NO exposed MCP tool surfaced it. `ganita_chart_facts_get`
 * / `query_chart_facts` (registry cap `marsys://tool/L1/chart_facts_query`) queries the
 * chart_facts table, which carries DERIVED per-varga facts but NOT the divisional-native EAV
 * rows — so "both wealth lords in Chandra-hora, D2 house 12" was unanswerable in one call.
 *
 * Fix: when `divisional_chart` is set, the handler ALSO queries chart_divisionals for that varga
 * and serves the rows in a separate, source-tagged, budget-capped `divisional_facts` section
 * (§N.6: layered, capped, disclosed — never flattened into the chart_facts rows).
 *
 * Mocks `@/lib/db/client`'s `query()` and asserts on the real registered capability handler.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'

beforeEach(() => {
  mockQuery.mockReset()
})

async function getCapabilityHandler() {
  await import('../catalog')
  const { getCapability } = await import('../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: unknown; is_error?: boolean }>
}

type DivisionalFacts = {
  source_table: string
  varga: string
  rows: Array<Record<string, unknown>>
  returned_count: number
  total: number
  more_available: boolean
  note: string
}

describe('chart_facts_query — Gate B (CR-58): D2 hora_class servable via divisional_chart', () => {
  it('divisional_chart=D2 + category=varga_hora_class surfaces hora_class + hora_d2_house from chart_divisionals in `divisional_facts`', async () => {
    const handler = await getCapabilityHandler()

    const horaRows = [
      { id: 'cd1', graha: 'Moon', varga: 'D2', fact_category: 'varga_hora_class', fact_key: 'hora_class', fact_value_num: null, fact_value_text: 'chandra_hora', sign: 'Cancer', house: 12, degree_in_sign: '29.7721' },
      { id: 'cd2', graha: 'Moon', varga: 'D2', fact_category: 'varga_hora_class', fact_key: 'hora_d2_house', fact_value_num: '12', fact_value_text: null, sign: 'Cancer', house: 12, degree_in_sign: '29.7721' },
      { id: 'cd3', graha: 'Venus', varga: 'D2', fact_category: 'varga_hora_class', fact_key: 'hora_class', fact_value_num: null, fact_value_text: 'chandra_hora', sign: 'Cancer', house: 12, degree_in_sign: '19.4542' },
    ]

    mockQuery.mockImplementation(async (sql: string) => {
      if (sql.includes('FROM chart_divisionals')) {
        if (sql.includes('COUNT(*)')) return { rows: [{ total: horaRows.length }] }
        return { rows: horaRows }
      }
      // chart_facts main fetch + count + any dignity join
      if (sql.includes('COUNT')) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const result = await handler({
      chart_id: CHART_ID, ayanamsha_id: AYANAMSHA,
      divisional_chart: 'D2', category: 'varga_hora_class', shape: 'rows',
    })

    const content = result.content as { divisional_facts?: DivisionalFacts }
    const dv = content.divisional_facts
    expect(dv).toBeDefined()
    expect(dv!.source_table).toBe('chart_divisionals')
    expect(dv!.varga).toBe('D2')
    expect(dv!.returned_count).toBe(3)

    // Both wealth-lord-carrying grahas (Moon, Venus) show chandra_hora + D2 house 12.
    const horaClass = dv!.rows.filter((r) => r.fact_key === 'hora_class')
    expect(horaClass.every((r) => r.fact_value_text === 'chandra_hora')).toBe(true)
    const horaHouse = dv!.rows.find((r) => r.fact_key === 'hora_d2_house')
    expect(String(horaHouse!.fact_value_num)).toBe('12')

    // fact_id resolves to chart_divisionals.id (provenance intact).
    expect(dv!.rows.map((r) => r.fact_id)).toContain('cd1')

    // The chart_divisionals query was scoped by the caller's category filter.
    const dvFetch = mockQuery.mock.calls.find(
      ([sql]) => (sql as string).includes('FROM chart_divisionals') && !(sql as string).includes('COUNT'),
    )
    expect(dvFetch).toBeDefined()
    expect(dvFetch![1]).toContainEqual(['varga_hora_class'])
  })

  it('no divisional_chart => no chart_divisionals query and no `divisional_facts` section (chart_facts contract untouched)', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (sql.includes('COUNT')) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const result = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows' })

    expect((result.content as Record<string, unknown>).divisional_facts).toBeUndefined()
    expect(mockQuery.mock.calls.some(([sql]) => (sql as string).includes('FROM chart_divisionals'))).toBe(false)
  })

  it('discloses more_available + a paging note when the varga row set exceeds the cap', async () => {
    const handler = await getCapabilityHandler()
    // 300 served rows, but 500 total => capped, more_available=true.
    const served = Array.from({ length: 300 }, (_, i) => ({
      id: `r${i}`, graha: 'Sun', varga: 'D2', fact_category: 'varga_position', fact_key: 'sign',
      fact_value_num: null, fact_value_text: 'Leo', sign: 'Leo', house: 1, degree_in_sign: '1.0',
    }))
    mockQuery.mockImplementation(async (sql: string) => {
      if (sql.includes('FROM chart_divisionals')) {
        if (sql.includes('COUNT(*)')) return { rows: [{ total: 500 }] }
        return { rows: served }
      }
      if (sql.includes('COUNT')) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const result = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, divisional_chart: 'D2', shape: 'rows' })
    const dv = (result.content as { divisional_facts: DivisionalFacts }).divisional_facts
    expect(dv.returned_count).toBe(300)
    expect(dv.total).toBe(500)
    expect(dv.more_available).toBe(true)
    expect(dv.note).toMatch(/Capped at 300 of 500/)
  })
})
