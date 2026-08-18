import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  computeGocharaActivation,
  computeGocharaElectionAvoidance,
  computeGocharaForecast,
} from './register_gochara_windows.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'test-user', key_id: 'test-key', role: 'guest' } as never

type AuthorityOptions = {
  mappingReachable?: boolean
  vocabularyReachable?: boolean
  marriageSwept?: boolean
  includeNonAliasEventClass?: boolean
}

function response(rows: Record<string, unknown>[]) {
  return new Response(JSON.stringify({ rows }), { status: 200 })
}

function unavailable() {
  return new Response('authority unavailable', { status: 503 })
}

function mockAuthorities(options: AuthorityOptions = {}) {
  const mappingReachable = options.mappingReachable ?? true
  const vocabularyReachable = options.vocabularyReachable ?? true
  const marriageSwept = options.marriageSwept ?? true
  const mainParams: unknown[][] = []

  vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
    const { sql, params } = JSON.parse(String(init?.body ?? '{}')) as {
      sql: string
      params: unknown[]
    }
    if (sql.includes('kala_gochara_authority') && !sql.includes('kala_gochara_windows')) {
      return response([])
    }
    if (sql.includes('gochara_resonance_map')) {
      return mappingReachable
        ? response([
          { event_class: 'marriage', domain: 'relationship' },
          ...(options.includeNonAliasEventClass
            ? [{ event_class: 'career_advancement', domain: 'career' }]
            : []),
        ])
        : unavailable()
    }
    if (sql.includes('brahma_event_ontology') && sql.includes('DISTINCT domain')) {
      return vocabularyReachable
        ? response([{ domain: 'career' }, { domain: 'relationship' }])
        : unavailable()
    }
    if (sql.includes('build_substep_progress')) {
      return response([{
        substeps_committed: marriageSwept ? 1 : 0,
        swept_event_classes: marriageSwept ? ['marriage'] : [],
      }])
    }
    if (sql.includes('MAX(window_end)')) return response([])
    if (sql.includes('FROM kala_gochara_windows')) {
      mainParams.push(params)
      return response([])
    }
    if (sql.includes('bg_gochara_citation_resolution')) return response([])
    throw new Error(`unexpected query: ${sql}`)
  }))

  return {
    mainParams,
    mainQueries: () => mainParams.length,
  }
}

const INVOCATIONS = [
  ['activation', () => computeGocharaActivation(CHART_ID, '2026-08-15', PRINCIPAL, undefined, 'marriage')],
  ['forecast', () => computeGocharaForecast(
    CHART_ID,
    { start: '2026-08-15', end: '2026-11-15' },
    undefined,
    undefined,
    50,
    PRINCIPAL,
    'marriage',
  )],
  ['election avoidance', () => computeGocharaElectionAvoidance(
    CHART_ID,
    { start: '2026-08-15', end: '2026-11-15' },
    undefined,
    50,
    PRINCIPAL,
    'marriage',
  )],
] as const

afterEach(() => vi.unstubAllGlobals())

describe('F-53 successor — Gochara domain aliases preserve authority honesty', () => {
  it.each(INVOCATIONS)(
    '%s resolves the live marriage event-class alias to canonical relationship before scanning',
    async (_name, invoke) => {
      const { mainParams, mainQueries } = mockAuthorities()

      const result = await invoke()

      expect(result['invalid_domain']).toBeUndefined()
      expect(result['not_covered']).toBeUndefined()
      expect(mainQueries()).toBe(1)
      expect(mainParams[0]).toContain('relationship')
      expect(mainParams[0]).not.toContain('marriage')
      expect((result['provenance_envelope'] as Record<string, unknown>)['domain_filter']).toBe('marriage')
    },
  )

  it.each([
    ['event-class mapping', { mappingReachable: false }],
    ['canonical vocabulary', { vocabularyReachable: false }],
  ] as const)(
    'passes marriage through without an invalid-domain verdict when %s authority is unavailable',
    async (_axis, options) => {
      const { mainParams, mainQueries } = mockAuthorities(options)

      const result = await computeGocharaForecast(
        CHART_ID,
        { start: '2026-08-15', end: '2026-11-15' },
        undefined,
        undefined,
        50,
        PRINCIPAL,
        'marriage',
      )

      expect(result['invalid_domain']).toBeUndefined()
      expect(result['not_covered']).toBeUndefined()
      expect(mainQueries()).toBe(1)
      expect(mainParams[0]).toContain('marriage')
      expect(mainParams[0]).not.toContain('relationship')
      expect((result['provenance_envelope'] as Record<string, unknown>)['backing_data_reachable']).toBe(false)
    },
  )

  it('resolves marriage before reporting a targeted-but-unswept relationship refusal', async () => {
    const { mainQueries } = mockAuthorities({ marriageSwept: false })

    const result = await computeGocharaForecast(
      CHART_ID,
      { start: '2026-08-15', end: '2026-11-15' },
      undefined,
      undefined,
      50,
      PRINCIPAL,
      'marriage',
    )

    expect(result['invalid_domain']).toBeUndefined()
    expect(result['not_covered']).toEqual({
      domain: 'relationship',
      cross_pointer: {
        instrument: 'kala_windows_get',
        hint: expect.stringContaining('marriage'),
      },
    })
    expect((result['coverage'] as Record<string, unknown>)['event_classes_targeted_not_swept']).toEqual(['marriage'])
    expect(mainQueries()).toBe(0)
  })

  it('does not widen arbitrary event-class labels into domain aliases', async () => {
    const { mainQueries } = mockAuthorities({ includeNonAliasEventClass: true })

    const result = await computeGocharaForecast(
      CHART_ID,
      { start: '2026-08-15', end: '2026-11-15' },
      undefined,
      undefined,
      50,
      PRINCIPAL,
      'career_advancement',
    )

    expect(result['invalid_domain']).toEqual({
      provided_domain: 'career_advancement',
      valid_domains: ['career', 'relationship'],
      reason: 'domain_not_in_gochara_ontology',
    })
    expect(mainQueries()).toBe(0)
  })
})
