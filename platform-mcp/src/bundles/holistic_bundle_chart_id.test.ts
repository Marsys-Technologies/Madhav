/**
 * holistic_bundle_chart_id.test.ts — CR-39/CR-14 regression, SECOND live copy.
 * ============================================================================================
 * This is the sibling regression test to `platform/src/lib/mcp/__tests__/bundle_adapters.test.ts`
 * (PR #848), written against the OTHER implementation of the exact same bundle logic:
 * `platform-mcp/src/bundles/holistic_bundle.ts`. This file's `executeHolisticBundle` — not the
 * `platform/` copy — is what `platform-mcp/src/bundles/index.ts` actually exports and wires to the
 * live, deployed `bodha_bundle_get` MCP tool. PR #848 fixed the `platform/` copy only; this copy's
 * `buildParams()` still dropped `chart_id` for MSR/CGM/LEL/PANCHANG/DASHA, reproducing the identical
 * 5/8 sub_tools_errored failure live in production even after #848 merged.
 *
 * DB-free: exercises the pure `buildParams()` function directly, no fetch/DB involved.
 */
import { describe, it, expect } from 'vitest'
import { buildParams, type HolisticBundleParams } from './holistic_bundle.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const baseParams: HolisticBundleParams = {
  query_text: 'career outlook',
  tier: 'client',
  chart_id: CHART_ID,
}

const PER_CHART_TOOLS = ['MSR', 'CGM', 'LEL', 'PANCHANG', 'DASHA'] as const
const GLOBAL_TOOLS = ['UCN', 'RM', 'CDLM'] as const

describe('buildParams — CR-39/CR-14 chart_id threading (platform-mcp copy)', () => {
  it.each(PER_CHART_TOOLS)('includes chart_id for per-chart sub-tool %s when bundleParams.chart_id is set', (name) => {
    const params = buildParams(name, baseParams)
    expect(params['chart_id']).toBe(CHART_ID)
  })

  it.each(GLOBAL_TOOLS)('does not include chart_id for global sub-tool %s regardless of bundleParams.chart_id', (name) => {
    const params = buildParams(name, baseParams)
    expect(params['chart_id']).toBeUndefined()
  })

  it.each(PER_CHART_TOOLS)('omits chart_id for per-chart sub-tool %s when bundleParams.chart_id is absent (no fabrication)', (name) => {
    const { chart_id: _chart_id, ...withoutChartId } = baseParams
    const params = buildParams(name, withoutChartId)
    expect(params['chart_id']).toBeUndefined()
  })

  it('preserves existing per-sub-tool param shape alongside chart_id', () => {
    expect(buildParams('MSR', { ...baseParams, focus_domains: ['career'], subset_size: 42 })).toEqual({
      chart_id: CHART_ID,
      domain: 'career',
      limit: 42,
    })
    expect(buildParams('CGM', baseParams)).toEqual({
      chart_id: CHART_ID,
      query: 'career outlook',
      hops: 3,
    })
    expect(buildParams('LEL', { ...baseParams, time_window: { start: '2020-01-01', end: '2020-12-31' } })).toEqual({
      chart_id: CHART_ID,
      start: '2020-01-01',
      end: '2020-12-31',
    })
    expect(buildParams('PANCHANG', baseParams)).toEqual({
      chart_id: CHART_ID,
      date: new Date().toISOString().slice(0, 10),
    })
    expect(buildParams('DASHA', baseParams)).toEqual({
      chart_id: CHART_ID,
      active_only: true,
    })
  })
})
