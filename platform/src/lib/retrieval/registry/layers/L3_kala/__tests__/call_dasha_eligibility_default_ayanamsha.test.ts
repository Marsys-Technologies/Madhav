/**
 * call_dasha_eligibility_default_ayanamsha.test.ts — N1-A DEFECT-2 regression.
 *
 * call_dasha_eligibility (ka_dasha_kala) used to default `ayanamsha_id` to the literal
 * `'lahiri'` while every other ayanamsha-bearing handler in this file (call_ephemeris_at_t,
 * call_priority_ranking) defaults to the project canonical `DEFAULT_AYANAMSHA` constant
 * (`'lahiri_chitrapaksha'`, `platform/src/lib/retrieval/registry/constants.ts`). Since
 * `chart_dashas` rows are stored under `lahiri_chitrapaksha`, a caller omitting
 * `ayanamsha_id` silently got zero rows instead of an error. Proves the fixed default
 * resolves to the canonical value and is what actually reaches the SQL query params.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, params: unknown[]) => queryMock(sql, params) }))

import { callDashaEligibilityCapability } from '../call_service_wrappers'
import { DEFAULT_AYANAMSHA } from '../../../constants'

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
const handler = callDashaEligibilityCapability.handler as Handler

describe('call_dasha_eligibility — default ayanamsha_id', () => {
  beforeEach(() => {
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
  })

  it('defaults to the canonical DEFAULT_AYANAMSHA, not the literal "lahiri"', async () => {
    expect(DEFAULT_AYANAMSHA).toBe('lahiri_chitrapaksha')

    const result = await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' }, undefined)

    expect(result.is_error).toBeFalsy()
    expect(result.content['ayanamsha_id']).toBe(DEFAULT_AYANAMSHA)

    expect(queryMock).toHaveBeenCalled()
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(params[1]).toBe(DEFAULT_AYANAMSHA)
  })

  it('still honors an explicit ayanamsha_id override', async () => {
    const result = await handler(
      { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', ayanamsha_id: 'raman' },
      undefined,
    )
    expect(result.content['ayanamsha_id']).toBe('raman')
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(params[1]).toBe('raman')
  })
})
