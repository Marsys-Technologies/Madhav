/**
 * register_spine_bundle.test.ts — capability-level tests for query_spine_bundle.
 * Mocks the materialize.ts read path (getOrMaterializeSpineBundle) directly rather
 * than the DB — the join logic itself is covered by compute_spine_bundle.test.ts
 * and materialize.test.ts; this file covers the capability contract (registration,
 * required_inputs, error handling, response shape).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const getOrMaterializeMock = vi.fn()
vi.mock('../../../spine/materialize', () => ({
  getOrMaterializeSpineBundle: (...args: unknown[]) => getOrMaterializeMock(...args),
}))

import { querySpineBundleCapability } from '../register_spine_bundle'
import { getCapability } from '../../index'
import '../../catalog' // triggers full registration side-effects

const CHART_C = '33333333-3333-3333-3333-333333333333'

describe('querySpineBundleCapability', () => {
  beforeEach(() => getOrMaterializeMock.mockReset())

  it('is registered in the catalog under the L-SPINE URI', () => {
    const cap = getCapability('marsys://tool/L-SPINE/query_spine_bundle')
    expect(cap).toBeDefined()
    expect(cap?.name).toBe('query_spine_bundle')
    expect(cap?.scope).toBe('per_chart')
    expect(cap?.required_inputs).toContain('chart_id')
  })

  it('errors without chart_id (chart-agnostic gate contract)', async () => {
    const result = await querySpineBundleCapability.handler({})
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>).error).toMatch(/chart_id/)
  })

  it('defaults domain to career and forwards args to getOrMaterializeSpineBundle', async () => {
    getOrMaterializeMock.mockResolvedValue({
      bundle: { chart_id: CHART_C, domain: 'career', signal_count: 0, signals: [] },
      source: 'fresh_materialized',
      computed_at: '2026-07-21T00:00:00.000Z',
    })

    const result = await querySpineBundleCapability.handler({ chart_id: CHART_C })

    expect(getOrMaterializeMock).toHaveBeenCalledWith(
      { chart_id: CHART_C, domain: 'career', ayanamsha_id: 'lahiri_chitrapaksha', top_k: undefined },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content.source).toBe('fresh_materialized')
    expect(content.computed_at).toBe('2026-07-21T00:00:00.000Z')
  })

  it('discloses which path served the request via `source` — never silently presented as cached', async () => {
    getOrMaterializeMock.mockResolvedValue({
      bundle: { chart_id: CHART_C, domain: 'wealth', signal_count: 3, signals: [] },
      source: 'materialized',
      computed_at: '2026-07-20T00:00:00.000Z',
    })
    const result = await querySpineBundleCapability.handler({ chart_id: CHART_C, domain: 'wealth' })
    expect((result.content as Record<string, unknown>).source).toBe('materialized')
  })
})

// The "materialize layer throws" case lives in its own file
// (register_spine_bundle_error.test.ts) — co-locating an async-rejecting mock call with
// other handler-invoking tests in the SAME file triggers a Vitest/Node unhandledRejection
// false-positive in this project's test environment (reproduced independently of this
// capability's code: isolated single-test files pass every time; the failure is purely a
// function of test-file co-location, not of the handler's actual try/catch behavior, which
// was verified correct via the isolated repro). Splitting the file sidesteps the flake
// without weakening coverage.
