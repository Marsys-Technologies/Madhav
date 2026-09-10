import { vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))

vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { getDashasCapability } from '../get_dashas'
import { REAL_AYANAMSHAS } from '@/lib/vidhi/ayanamsha_variation'

describe('F-42: get_dashas ayanamsha validation', () => {
  beforeEach(() => queryMock.mockReset())

  it.each(['not_a_real_ayanamsha', 'INVARIANT'])('rejects %s before any database query', async (ayanamsha_id) => {
    const result = await getDashasCapability.handler({
      chart_id: '482012f1-0000-4000-8000-000000000000',
      ayanamsha_id,
    }, {})

    expect(result).toEqual({
      content: {
        chart_id: '482012f1-0000-4000-8000-000000000000',
        code: 'invalid_ayanamsha_id',
        error: 'get_dashas: ayanamsha_id is not one of the stored chart ayanamshas.',
        recognized_ayanamsha_ids: [...REAL_AYANAMSHAS],
      },
      is_error: true,
    })
    expect(queryMock).not.toHaveBeenCalled()
  })
})
