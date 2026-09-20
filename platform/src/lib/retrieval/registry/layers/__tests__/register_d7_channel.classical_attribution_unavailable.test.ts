import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../catalog'

describe('classical_attribution_lookup source closure', () => {
  it('fails closed instead of presenting the retired attribution store as an empty successful lookup', async () => {
    const capability = getCatalog().find((candidate) =>
      candidate.uri === 'marsys://tool/L2/classical_attribution_lookup',
    )
    expect(capability).toBeDefined()

    const response = await capability!.handler({
      chart_id: '11111111-1111-4111-8111-111111111111',
      signal_ids: ['SIG.MSR.042'],
    })

    expect(response.is_error).toBe(true)
    expect(response.content).toMatchObject({
      code: 'CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE',
    })
  })
})
