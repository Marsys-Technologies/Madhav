/**
 * chart_facts_offset_clamp_disclosure.test.ts — F-36 exit test
 *
 * Verifies that ganita_chart_facts_get discloses when the caller's offset is
 * clamped (>100,000 → 100,000) by adding offset_requested and offset_clamped
 * fields alongside the existing offset field in both response branches.
 *
 * Today's code: offset_requested and offset_clamped do not exist → tests are RED.
 * After fix: both fields are present → GREEN.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'

beforeEach(() => {
  mockQuery.mockReset()
})

async function getHandler() {
  await import('../catalog')
  const { getCapability } = await import('../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

describe('ganita_chart_facts_get — F-36: discloses offset clamping', () => {
  it('returns offset_requested and offset_clamped=true when offset is clamped (>100000)', async () => {
    const handler = await getHandler()
    // main rows query returns empty; count query returns total=0
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const res = await handler({ chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA, offset: 999999 })

    expect(res.is_error).toBeFalsy()
    expect(res.content['offset']).toBe(100000)
    expect(res.content['offset_requested']).toBe(999999)   // fails today: field doesn't exist
    expect(res.content['offset_clamped']).toBe(true)        // fails today: field doesn't exist
  })

  it('returns offset_clamped=false when offset is within bounds', async () => {
    const handler = await getHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const res = await handler({ chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA, offset: 50 })

    expect(res.is_error).toBeFalsy()
    expect(res.content['offset_clamped']).toBe(false)
  })
})
