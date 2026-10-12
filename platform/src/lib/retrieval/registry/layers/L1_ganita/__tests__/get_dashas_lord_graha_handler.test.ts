/** lord_graha is resolved to the stored form before it reaches SQL; an unknown value is a structured error, never an empty page. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getDashasCapability } from '../get_dashas'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const originalSigningEnvironment = {
  currentKid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID,
  current: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT,
  previousKid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID,
  previous: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS,
}

describe('get_dashas lord_graha filter at the handler (SU/Sun/sun, sign names, unknown value)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 7).toString('base64url')
    delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID
    delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS
  })
  afterEach(() => {
    if (originalSigningEnvironment.currentKid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
    else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = originalSigningEnvironment.currentKid
    if (originalSigningEnvironment.current === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
    else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = originalSigningEnvironment.current
    if (originalSigningEnvironment.previousKid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID
    else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID = originalSigningEnvironment.previousKid
    if (originalSigningEnvironment.previous === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS
    else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS = originalSigningEnvironment.previous
  })

  const page = () => mockQuery
    .mockResolvedValueOnce({ rows: [{ replacement_in_progress: false, eligible_build_id: 'build-a', rows: [] }] })
    .mockResolvedValue({ rows: [{ max_level: 3 }] })
  const boundValues = () => mockQuery.mock.calls.flatMap(c => (Array.isArray(c[1]) ? c[1] : []))

  it.each(['SU', 'Sun', 'sun', 'SUN'])("lord_graha %s binds the stored value 'Sun' (same rows for every spelling)", async spelling => {
    mockQuery.mockReset(); page()
    const result = await getDashasCapability.handler({ chart_id: CHART_ID, lord_graha: spelling }, undefined)
    expect(result.is_error).toBe(false)
    const values = boundValues()
    expect(values).toContain('Sun')
    const applied = (result.content as { facets_applied: { lord_graha?: unknown } }).facets_applied.lord_graha
    expect(applied).toEqual({ requested: spelling, stored: 'Sun' })      // the resolution is echoed, not silent
    const flags = (result as typeof result & { judgment_flags?: Array<{ code: string }> }).judgment_flags ?? []
    expect(flags.some(f => f.code === 'lord_graha_resolved')).toBe(spelling !== 'Sun')   // a different spelling is disclosed; an exact stored form is not
    expect(values).not.toContain(spelling === 'Sun' ? '__never__' : spelling)
  })

  it("a sign name for a rashi dasha system is resolved to the stored sign name", async () => {
    mockQuery.mockReset(); page()
    const result = await getDashasCapability.handler({ chart_id: CHART_ID, system: 'narayana', lord_graha: 'taurus' }, undefined)
    expect(result.is_error).toBe(false)
    expect(boundValues()).toContain('Taurus')
  })

  it('an unknown lord_graha is a structured invalid_lord_graha error and never reaches the database', async () => {
    mockQuery.mockReset(); page()
    const result = await getDashasCapability.handler({ chart_id: CHART_ID, lord_graha: 'Pluto' }, undefined)
    expect(result.is_error).toBe(true)
    const c = result.content as Record<string, unknown>
    expect(c['code']).toBe('invalid_lord_graha')
    expect(c['recognized_lord_graha']).toEqual(expect.arrayContaining(['Sun', 'Taurus', 'Mangala']))
    expect(boundValues()).not.toContain('Pluto')
  })
})
