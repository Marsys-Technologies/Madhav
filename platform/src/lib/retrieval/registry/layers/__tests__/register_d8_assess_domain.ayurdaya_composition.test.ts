/**
 * register_d8_assess_domain.ayurdaya_composition.test.ts — SS N-62 Q10 coverage test for a COMPOSED tool.
 *
 * THE QUESTION: query_signals tags its own `ayurdaya:*` MSR signals (per-row figure_kind + page-level
 * disclosure), but assess_* does not forward that result — it re-projects each signal through
 * `pickSignals` ({signal_id, signal_type_class, summary, ...}), which DROPS `signal_type_id`,
 * `configuration_jsonb`, `figure_kind` and the page-level disclosure object. Does the ayurdaya
 * disclosure survive that composition?
 *
 * THE ANSWER THIS TEST PINS: yes, via the registry post-processor that wraps assess_*'s OWN handler at
 * registerCapability. It walks the assembled bundle and recognises the projected rows by their
 * `summary` text (`category=ayurdaya | key=... | harana_status=...`), re-derives each row's own
 * figure_kind, and attaches the page-level disclosure + closed-vocabulary flag. The disclosure
 * therefore depends on the projected `summary` text surviving; if a future projection drops the
 * summary (or truncates it before the `category=ayurdaya` prefix) the rows silently lose disclosure —
 * see the "What this does not cover" list on the post-processor.
 *
 * Harness copied from register_d8_assess_domain.f166_domain_resolution.test.ts (same mocks).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))
vi.mock('../../generation/served_generation', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../generation/served_generation')>()
  return {
    ...original,
    resolveChartServedGeneration: async (chartId: string) => original.chartServedGenerationFromRows(chartId, null, [{
      asset_id: 'ga_structural', partition_key: '__whole_asset__', receipt_version: 'v1',
      receipt_build_id: '11111111-1111-4111-8111-111111111111', rows_build_id: '11111111-1111-4111-8111-111111111111',
      receipt_state: 'proven', freshness_state: 'fresh', output_digest_spec_sha256: 'a'.repeat(64), spec_active: true,
      receipt_run_state: 'completed', receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    }]),
  }
})

const domainReadingHandler = vi.fn()
const temporalHandler = vi.fn()
const contradictionsHandler = vi.fn()
const signalsHandler = vi.fn()

vi.mock('../L2_bodha/query_domain_reading', () => ({
  queryDomainReadingCapability: { handler: (...a: unknown[]) => domainReadingHandler(...a) },
}))
vi.mock('../L3_kala/query_temporal_activation', () => ({
  queryTemporalActivationCapability: { handler: (...a: unknown[]) => temporalHandler(...a) },
}))
vi.mock('../L2_bodha/query_contradictions', () => ({
  queryContradictionsCapability: { handler: (...a: unknown[]) => contradictionsHandler(...a) },
}))
vi.mock('../L2_bodha/query_signals', () => ({
  querySignalsCapability: { handler: (...a: unknown[]) => signalsHandler(...a) },
}))

import { clearRegistry, getCapability } from '../../index'
import { registerD8AssessDomainCapabilities } from '../register_d8_assess_domain'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const BASE = 'base_only_haranas_deferred_to_w3'

/** An `ayurdaya:*` MSR signal as the (real) query_signals would hand it to assess_*. */
function ayuSignal(id: string, key: string, summary: string): Record<string, unknown> {
  return {
    signal_id: id, signal_type_id: `ayurdaya:${key}`, signal_type_class: 'composite_state',
    source_subsystem: 'structural', signal_summary_text: summary, computed_salience: 0.46,
    constituent_facts_array: ['F-1'], configuration_jsonb: { fact_key: key, method: 'pindayu' },
  }
}

beforeEach(() => {
  queryMock.mockReset()
  domainReadingHandler.mockReset()
  temporalHandler.mockReset()
  contradictionsHandler.mockReset()
  signalsHandler.mockReset()
  domainReadingHandler.mockResolvedValue({ is_error: false, content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [], lens_count: 0 } })
  temporalHandler.mockResolvedValue({ is_error: false, content: { activations: [], predicates: [], activation_count: 0, signal_id_refs: [] } })
  contradictionsHandler.mockResolvedValue({ is_error: false, content: { contradiction_count: 0, discoveries: [] } })
  signalsHandler.mockResolvedValue({
    is_error: false,
    content: {
      signals: [
        ayuSignal('ayu-total', 'total_years', `category=ayurdaya | key=total_years | value_num=98.75 | harana_status=${BASE} | method=pindayu`),
        ayuSignal('ayu-contrib', 'pindayu_contribution_years', 'category=ayurdaya | key=pindayu_contribution_years | value_num=19.86 | graha=Saturn | method=pindayu'),
        { signal_id: 'plain', signal_type_class: 'composite_state', source_subsystem: 'structural', signal_summary_text: 'category=yoga | key=x', computed_salience: 0.4 },
      ],
      ranking_basis: { mode: 'composite', priors_version: '1.0', domain: 'health' },
    },
  })
  queryMock.mockImplementation(async (sql: string) => {
    if (String(sql).includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: { health: { vargas: ['D1', 'D6', 'D9'], provisional: true, houses: [6], karaka: 'Saturn' } } }] }
    }
    return { rows: [] }
  })
})

/** Collect every object in `v` whose summary/signal_summary_text starts with 'category=ayurdaya'. */
function ayurdayaSummaryObjects(v: unknown, out: Array<Record<string, unknown>> = []): Array<Record<string, unknown>> {
  if (!v || typeof v !== 'object') return out
  if (Array.isArray(v)) { v.forEach(x => ayurdayaSummaryObjects(x, out)); return out }
  const o = v as Record<string, unknown>
  const text = o['summary'] ?? o['signal_summary_text']
  if (typeof text === 'string' && text.startsWith('category=ayurdaya')) out.push(o)
  Object.values(o).forEach(x => ayurdayaSummaryObjects(x, out))
  return out
}

describe('assess_health (composed tool) — ayurdaya disclosure survives composition', () => {
  it('re-projected ayurdaya signals still carry per-row figure_kind, and the bundle carries the page-level disclosure + flag', async () => {
    clearRegistry()
    registerD8AssessDomainCapabilities()
    const cap = getCapability('marsys://tool/L-DOMAIN/assess_health')
    expect(cap).toBeDefined()
    const res = await cap!.handler({ chart_id: CHART_ID }, undefined) as unknown as {
      is_error: boolean; content: Record<string, unknown>; judgment_flags?: Array<Record<string, unknown>>
    }
    expect(res.is_error, JSON.stringify(res.content)).toBe(false)

    // The inner query_signals disclosure object is NOT forwarded by assess_* (it only reads `signals`):
    // what the bundle carries is the post-processor's own, re-derived from the projected rows.
    expect(Object.keys(res.content)[0]).toBe('ayurdaya_figure_disclosure')
    expect(res.content['ayurdaya_figure_disclosure']).toMatchObject({
      figure_kind: 'unreduced_base', reductions_applied: false, figure_counts: { unreduced_base: 2, reduction_status_unverified: 0 },
    })
    expect((res.content['judgment_flags'] as Array<Record<string, unknown>>).map(f => f['code'])).toContain('ayurdaya_unreduced_base_figures')
    expect((res.judgment_flags ?? []).map(f => f['code'])).toContain('ayurdaya_unreduced_base_figures')

    // Every projected ayurdaya signal (the composite top-10 projection) is tagged with its own kind; the
    // non-ayurdaya signal is not.
    const projected = ayurdayaSummaryObjects(res.content)
    expect(projected.length).toBeGreaterThanOrEqual(2)
    for (const p of projected) expect(p).toMatchObject({ figure_kind: 'unreduced_base', reductions_applied: false })
    expect(JSON.stringify(res.content)).not.toMatch(/"signal_id":"plain"[^}]*figure_kind/)
  })
})
