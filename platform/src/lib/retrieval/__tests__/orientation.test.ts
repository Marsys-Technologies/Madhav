/**
 * orientation.test.ts — S-1 orientation front-door: shape + ≤2000-token budget enforcement
 * (W4 core step 5).
 *
 * The DB-backed deps (query_ucd handler + chart_header resolver) are mocked so the test exercises
 * the composition + budget logic deterministically, without a live Postgres.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'

// ── Mocks: the two DB-backed deps buildChartOrientation composes ────────────────
const handlerMock = vi.fn()
vi.mock('../registry/layers/L2_bodha/query_ucd', () => ({
  queryUcdCapability: { handler: (...args: unknown[]) => handlerMock(...args) },
}))

const headerMock = vi.fn()
vi.mock('../chart_header', () => ({
  fetchChartHeaderResolution: (...args: unknown[]) => headerMock(...args),
}))

import { buildChartOrientation, ORIENTATION_TOKEN_BUDGET } from '../orientation'
import { estimateTokens } from '@/lib/pipeline/manifest_compressor'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function header(overrides: Record<string, unknown> = {}) {
  return {
    header: {
      chart_id_short: '482012f1',
      name: 'Test Native',
      lagna_sign: 'Aries',
      lagna_deg: 12.3,
      moon_sign: 'Aquarius',
      sun_sign: 'Capricorn',
      ayanamsha: 'lahiri_chitrapaksha',
      current_maha_antar: 'Mercury / Saturn',
      ...overrides,
    },
    flags: [],
  }
}

function ucdContent(entityCount: number) {
  return {
    is_error: false,
    content: {
      chart_id: CHART,
      ayanamsha_id: 'lahiri_chitrapaksha',
      digest: {
        msr_signal_count: 573,
        yoga_count: 41,
        dosha_count: 12,
        contradiction_count: 7,
        weakest_graha: 'Saturn',
        weakest_graha_source: 'shadbala_total_min',
        top_priority_class: 'chart_defining',
      },
      entity_profiles: Array.from({ length: entityCount }, (_, i) => ({
        entity: `Graha_${i}`,
        entity_type: 'graha',
        signal_count: 20 + i,
        dominant_domains: ['career', 'wealth', 'spiritual'],
        dominant_valence: 'benefic',
        top_signal_ids: [`SIG.MSR.${i}00`, `SIG.MSR.${i}01`, `SIG.MSR.${i}02`],
      })),
      convergence_domains: Array.from({ length: 7 }, (_, i) => ({ domain: `DOMAIN_${i}`, convergence_score: 0.9 - i * 0.1 })),
    },
  }
}

describe('buildChartOrientation — shape', () => {
  beforeEach(() => {
    handlerMock.mockReset()
    headerMock.mockReset()
  })

  it('composes header + structural facts + notable findings + dasha + category inventory', async () => {
    headerMock.mockResolvedValue(header())
    handlerMock.mockResolvedValue(ucdContent(3))

    const o = await buildChartOrientation(CHART)
    expect(o.chart_id).toBe(CHART)
    expect(o.chart_header?.lagna_sign).toBe('Aries')
    expect(o.structural_facts?.msr_signal_count).toBe(573)
    expect(o.structural_facts?.weakest_graha).toBe('Saturn')
    expect(o.notable_findings.length).toBeGreaterThan(0)
    expect(o.dasha_context.current_maha_antar).toBe('Mercury / Saturn')
    expect(o.category_inventory.length).toBeGreaterThan(0)
    expect(o.category_inventory.every(c => c.drill_tool && c.hint)).toBe(true)
    expect(o.degraded).toBe(false)
  })

  it('degrades to header + inventory when query_ucd errors (non-throwing)', async () => {
    headerMock.mockResolvedValue(header())
    handlerMock.mockResolvedValue({ is_error: true, content: { error: 'db down' } })

    const o = await buildChartOrientation(CHART)
    expect(o.degraded).toBe(true)
    expect(o.structural_facts).toBeNull()
    expect(o.notable_findings).toHaveLength(0)
    // Frame + inventory still present — a useful degraded orientation.
    expect(o.chart_header?.name).toBe('Test Native')
    expect(o.category_inventory.length).toBeGreaterThan(0)
  })

  it('survives a header resolution failure (flags surfaced, never throws)', async () => {
    headerMock.mockRejectedValue(new Error('header boom'))
    handlerMock.mockResolvedValue(ucdContent(2))

    const o = await buildChartOrientation(CHART)
    expect(o.header_flags).toContain('chart_header_unresolved')
    expect(o.dasha_context.current_maha_antar).toBeNull()
    // Digest still composed.
    expect(o.structural_facts?.msr_signal_count).toBe(573)
  })
})

describe('buildChartOrientation — ≤2000-token budget enforcement', () => {
  beforeEach(() => {
    handlerMock.mockReset()
    headerMock.mockReset()
  })

  it('a small orientation fits under budget with no trims', async () => {
    headerMock.mockResolvedValue(header())
    handlerMock.mockResolvedValue(ucdContent(2))

    const o = await buildChartOrientation(CHART)
    expect(o.budget.limit_tokens).toBe(ORIENTATION_TOKEN_BUDGET)
    expect(o.budget.estimated_tokens).toBeLessThanOrEqual(ORIENTATION_TOKEN_BUDGET)
    expect(o.budget.enforced).toBe(false)
    expect(o.budget.trims).toHaveLength(0)
  })

  it('an oversized orientation is trimmed to fit and records the trims', async () => {
    headerMock.mockResolvedValue(header())
    // 40 fat entity profiles → well over 2000 tokens before trimming.
    handlerMock.mockResolvedValue(ucdContent(40))

    const o = await buildChartOrientation(CHART, undefined, { topKEntities: 40 })
    expect(o.budget.enforced).toBe(true)
    expect(o.budget.trims.length).toBeGreaterThan(0)
    // Final block must actually be within budget (the whole point of the enforcement).
    expect(o.budget.estimated_tokens).toBeLessThanOrEqual(ORIENTATION_TOKEN_BUDGET)
    // Independent re-measure of the delivered payload confirms it fits.
    const remeasure = estimateTokens(
      JSON.stringify({
        chart_header: o.chart_header,
        structural_facts: o.structural_facts,
        notable_findings: o.notable_findings,
        convergence_domains: o.convergence_domains,
        dasha_context: o.dasha_context,
        category_inventory: o.category_inventory,
      }),
    )
    expect(remeasure).toBeLessThanOrEqual(ORIENTATION_TOKEN_BUDGET)
  })

  it('trims the least-load-bearing sections first (convergence, then drill ids, then findings)', async () => {
    headerMock.mockResolvedValue(header())
    handlerMock.mockResolvedValue(ucdContent(40))

    const o = await buildChartOrientation(CHART, undefined, { topKEntities: 40 })
    // Convergence trimmed to at most 3.
    expect(o.convergence_domains.length).toBeLessThanOrEqual(3)
    // At least one finding survives (core is never fully emptied).
    expect(o.notable_findings.length).toBeGreaterThanOrEqual(1)
    // The category inventory (core) is never dropped.
    expect(o.category_inventory.length).toBeGreaterThan(0)
  })
})
