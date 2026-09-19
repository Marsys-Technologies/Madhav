import { beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { querySignalsCapability } from '../query_signals'

const CHART_ID = '3279af05-8812-4fe6-8e84-9203f5e8a760'
const BUILD_A = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const BUILD_B = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'

const SIGNALS = [
  {
    signal_id: 'sun-signal', signal_type_id: 'graha_position:sun', signal_type_class: 'position',
    signal_tradition: 'parashari', signal_summary_text: 'Sun signal', signal_headline_text: 'Sun',
    computed_salience: 1, top_k_salience_rank: 1, domains_affected_array: ['career'],
    constituent_facts_array: ['sun-fact'], source_subsystem: 'ganita', valence: 'positive',
    verification_pass_status: 'pass', citation_human: 'test', lel_origin: false,
    signature_tier: 'background', configuration_jsonb: { graha: 'SU' },
  },
  {
    signal_id: 'moon-signal', signal_type_id: 'graha_position:moon', signal_type_class: 'position',
    signal_tradition: 'parashari', signal_summary_text: 'Moon signal', signal_headline_text: 'Moon',
    computed_salience: 1, top_k_salience_rank: 2, domains_affected_array: ['career'],
    constituent_facts_array: ['moon-fact'], source_subsystem: 'ganita', valence: 'positive',
    verification_pass_status: 'pass', citation_human: 'test', lel_origin: false,
    signature_tier: 'background', configuration_jsonb: { graha: 'MO' },
  },
]

function l1FactsFor(buildId: string) {
  const sunStrong = buildId === BUILD_A
  return [
    { fact_category: 'graha_shadbala_total', fact_subject: 'SUN', fact_key: 'rupa', fact_value_num: sunStrong ? 5 : 0.1, fact_value_text: null, fact_value_jsonb: null },
    { fact_category: 'graha_shadbala_total', fact_subject: 'SUN', fact_key: 'ratio', fact_value_num: sunStrong ? 0.01 : 99, fact_value_text: null, fact_value_jsonb: null },
    { fact_category: 'graha_dignity_per_varga', fact_subject: 'D1_SUN', fact_key: 'dignity_state', fact_value_num: null, fact_value_text: sunStrong ? 'exalted' : 'debilitated', fact_value_jsonb: { house: 10 } },
    { fact_category: 'graha_dignity_per_varga', fact_subject: 'D1_SUN', fact_key: 'dignity_weight', fact_value_num: null, fact_value_text: sunStrong ? 'debilitated' : 'exalted', fact_value_jsonb: { house: 1 } },
    { fact_category: 'graha_shadbala_total', fact_subject: 'MOON', fact_key: 'rupa', fact_value_num: sunStrong ? 0.1 : 5, fact_value_text: null, fact_value_jsonb: null },
    { fact_category: 'graha_shadbala_total', fact_subject: 'MOON', fact_key: 'ratio', fact_value_num: sunStrong ? 99 : 0.01, fact_value_text: null, fact_value_jsonb: null },
    { fact_category: 'graha_dignity_per_varga', fact_subject: 'D1_MOON', fact_key: 'dignity_state', fact_value_num: null, fact_value_text: sunStrong ? 'debilitated' : 'exalted', fact_value_jsonb: { house: 10 } },
    { fact_category: 'graha_dignity_per_varga', fact_subject: 'D1_MOON', fact_key: 'dignity_weight', fact_value_num: null, fact_value_text: sunStrong ? 'exalted' : 'debilitated', fact_value_jsonb: { house: 1 } },
  ]
}

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sqlValue: unknown, params: unknown[] = []) => {
    const sql = String(sqlValue)
    if (sql.includes('information_schema.columns')) return { rows: [] }
    if (sql.includes('FROM chart_facts') && sql.includes("fact_category = 'graha_shadbala_total'")) {
      return { rows: l1FactsFor(String(params[2])) }
    }
    if (sql.includes('FROM chart_facts') && sql.includes("fact_subject = $4 AND fact_key = 'sign'")) {
      return { rows: [{ fact_id: 'sun-sign', fact_value_text: 'Aries' }] }
    }
    if (sql.includes('SELECT fact_subject, fact_value_text FROM chart_facts')) {
      return { rows: [{ fact_subject: 'SUN', fact_value_text: 'Aries' }] }
    }
    if (sql.includes('FROM chart_facts')) return { rows: [] }
    if (sql.includes('FROM chart_dashas')) {
      const lord = params[3] === BUILD_A ? 'SUN' : 'MOON'
      return { rows: [{ level: 1, dasha_lord: lord }, { level: 2, dasha_lord: lord }] }
    }
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '2' }] }
    if (sql.includes('FROM bodha_msr_signals m')) return { rows: SIGNALS }
    return { rows: [] }
  })
})

describe('query_signals selected-build L1 ranking context', () => {
  it('isolates L1 cache entries and rankings across two chart builds', async () => {
    const resultA = await querySignalsCapability.handler(
      { chart_id: CHART_ID, build_id: BUILD_A, domain: 'career', top_k: 2 },
      undefined,
    )
    const resultB = await querySignalsCapability.handler(
      { chart_id: CHART_ID, build_id: BUILD_B, domain: 'career', top_k: 2 },
      undefined,
    )

    expect(resultA.is_error).toBe(false)
    expect(resultB.is_error).toBe(false)
    const idsA = ((resultA.content as Record<string, unknown>)['signals'] as Array<Record<string, unknown>>)
      .map(row => row['signal_id'])
    const idsB = ((resultB.content as Record<string, unknown>)['signals'] as Array<Record<string, unknown>>)
      .map(row => row['signal_id'])
    expect(idsA).toEqual(['sun-signal', 'moon-signal'])
    expect(idsB).toEqual(['moon-signal', 'sun-signal'])

    const factCalls = queryMock.mock.calls.filter(([sql]) =>
      String(sql).includes('FROM chart_facts') && String(sql).includes("fact_category = 'graha_shadbala_total'"),
    )
    const dashaCalls = queryMock.mock.calls.filter(([sql]) => String(sql).includes('FROM chart_dashas'))
    expect(factCalls).toHaveLength(2)
    expect(dashaCalls).toHaveLength(2)
    expect(factCalls.map(([, params]) => (params as unknown[])[2])).toEqual([BUILD_A, BUILD_B])
    expect(dashaCalls.map(([, params]) => (params as unknown[])[3])).toEqual([BUILD_A, BUILD_B])
    for (const [sqlValue] of factCalls) {
      const sql = String(sqlValue).replace(/\s+/g, ' ')
      expect(sql).toContain('SELECT fact_category, fact_subject, fact_key, fact_value_num')
      expect(sql).toContain("fact_category = 'graha_shadbala_total' AND fact_key = 'rupa'")
      expect(sql).toContain("fact_category = 'graha_dignity_per_varga' AND fact_subject LIKE 'D1_%' AND fact_key = 'dignity_state'")
      expect(sql).toContain('build_id = $3::uuid')
      expect(sql).not.toContain('build_id = $3::text')
    }
    for (const [sql] of dashaCalls) expect(String(sql)).toContain('build_id = $4::uuid')
  })

  it('uses the UUID build fence for the frame-annotation chart_facts read', async () => {
    const result = await querySignalsCapability.handler(
      { chart_id: CHART_ID, build_id: BUILD_A, frame: 'surya', top_k: 1 },
      undefined,
    )

    expect(result.is_error).toBe(false)
    const frameFactCall = queryMock.mock.calls.find(([sql]) =>
      String(sql).includes('SELECT fact_subject, fact_value_text FROM chart_facts'),
    )
    expect(frameFactCall).toBeTruthy()
    expect(String(frameFactCall?.[0])).toContain('build_id = $4::uuid')
    expect(String(frameFactCall?.[0])).not.toContain('build_id = $4::text')
    expect(frameFactCall?.[1]).toEqual(expect.arrayContaining([BUILD_A]))
  })
})
