import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => mockQuery(...args),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

import {
  classical_attribution_lookup,
  ClassicalAttributionSourceUnavailableError,
  CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE,
} from '@/lib/tools/classical_attribution_lookup'

// The classical_attributions / classical_chunks / classical_texts relations were
// dropped in WS-0 and have no queryable replacement. The lookup previously
// returned every requested signal as `signal_ids_silent` — an unmeasured
// "classically silent" claim. It now fails closed.
describe('classical_attribution_lookup (retired source — fails closed)', () => {
  it.each([
    [{ signal_ids: [] as string[] }],
    [{ signal_ids: ['SIG.MSR.042'] }],
    [{ signal_ids: ['SIG.MSR.042', 'SIG.MSR.999'], attribution_type: 'confirms' as const, confidence_tier: 'HIGH' as const }],
  ])('rejects with CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE for %j', async (input) => {
    const pending = classical_attribution_lookup(input)
    await expect(pending).rejects.toBeInstanceOf(ClassicalAttributionSourceUnavailableError)
    await expect(pending).rejects.toMatchObject({
      code: CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE,
      name: 'ClassicalAttributionSourceUnavailableError',
    })
  })

  it('never queries the database (there is no source relation to query)', async () => {
    await expect(classical_attribution_lookup({ signal_ids: ['SIG.MSR.042'] })).rejects.toThrow()
    expect(mockQuery).not.toHaveBeenCalled()
  })
})
