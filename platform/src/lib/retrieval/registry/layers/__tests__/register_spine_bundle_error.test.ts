/**
 * register_spine_bundle_error.test.ts — the "materialize layer throws" case, split
 * into its own file from register_spine_bundle.test.ts. See that file's trailing
 * comment for why: co-locating this async-rejecting-mock test with other
 * handler-invoking tests in the same file triggers a Vitest/Node unhandledRejection
 * false-positive in this project's test environment, independent of this
 * capability's actual (verified-correct) try/catch behavior.
 */
import { describe, it, expect, vi } from 'vitest'

const getOrMaterializeMock = vi.fn()
vi.mock('../../../spine/materialize', () => ({
  getOrMaterializeSpineBundle: (...args: unknown[]) => getOrMaterializeMock(...args),
}))

import { querySpineBundleCapability } from '../register_spine_bundle'

const CHART_C = '33333333-3333-3333-3333-333333333333'

describe('querySpineBundleCapability — materialize-layer failure path', () => {
  it('surfaces a thrown error from the materialize layer as a structured is_error response', async () => {
    getOrMaterializeMock.mockImplementation(async () => { throw new Error('db unreachable') })
    const result = await querySpineBundleCapability.handler({ chart_id: CHART_C })
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>).error).toBe('db unreachable')
  })
})
