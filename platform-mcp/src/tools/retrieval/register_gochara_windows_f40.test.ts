import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  computeGocharaActivation,
  computeGocharaElectionAvoidance,
  computeGocharaForecast,
} from './register_gochara_windows.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'test-user', key_id: 'test-key', role: 'guest' } as never
const UNKNOWN_DOMAIN = 'nonexistent_domain_xyz'

function response(rows: Record<string, unknown>[]) {
  return new Response(JSON.stringify({ rows }), { status: 200 })
}

function mockCoverage(): { mainQueries: () => number } {
  let mainQueries = 0
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
    const { sql } = JSON.parse(String(init?.body ?? '{}')) as { sql: string }
    if (sql.includes('kala_gochara_authority') && !sql.includes('kala_gochara_windows')) return response([])
    if (sql.includes('gochara_resonance_map')) return response([{ event_class: 'career_advancement', domain: 'career' }])
    if (sql.includes('brahma_event_ontology') && sql.includes('DISTINCT domain')) return response([{ domain: 'career' }, { domain: 'health' }])
    if (sql.includes('build_substep_progress')) return response([{ substeps_committed: 1, swept_event_classes: ['career_advancement'] }])
    if (sql.includes('MAX(window_end)')) return response([])
    if (sql.includes('FROM kala_gochara_windows')) {
      mainQueries += 1
      return response([])
    }
    throw new Error(`unexpected query: ${sql}`)
  }))
  return { mainQueries: () => mainQueries }
}

afterEach(() => vi.unstubAllGlobals())

describe('F-40 — unknown Gochara domain is not an honest zero', () => {
  it.each([
    ['forecast', () => computeGocharaForecast(CHART_ID, { start: '2026-08-15', end: '2026-11-15' }, undefined, undefined, 50, PRINCIPAL, UNKNOWN_DOMAIN)],
    ['activation', () => computeGocharaActivation(CHART_ID, '2026-08-15', PRINCIPAL, undefined, UNKNOWN_DOMAIN)],
    ['election avoidance', () => computeGocharaElectionAvoidance(CHART_ID, { start: '2026-08-15', end: '2026-11-15' }, undefined, 50, PRINCIPAL, UNKNOWN_DOMAIN)],
  ])('%s returns an explicit invalid-domain receipt before the main scan', async (_name, invoke) => {
    const { mainQueries } = mockCoverage()

    const result = await invoke()

    expect(result['windows']).toEqual([])
    expect(result['invalid_domain']).toEqual({
      provided_domain: UNKNOWN_DOMAIN,
      valid_domains: ['career', 'health'],
      reason: 'domain_not_in_gochara_ontology',
    })
    expect(result['not_covered']).toBeUndefined()
    expect(mainQueries()).toBe(0)
  })
})
