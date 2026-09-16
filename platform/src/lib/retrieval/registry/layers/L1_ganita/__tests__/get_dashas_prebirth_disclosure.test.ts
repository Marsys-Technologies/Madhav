/** F-33: pre-birth as-of dasha rows must carry a machine-readable boundary disclosure. */
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

describe('F-33 get_dashas pre-birth as_of disclosure', () => {
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

  it('keeps computed rows but flags an as_of_date before the chart birth date', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ replacement_in_progress: false, eligible_build_id: 'build-a', rows: [] }] }) // consistent receipt and page snapshot
      .mockResolvedValueOnce({ rows: [{ birth_date: '1984-02-05', as_of_date_precedes_birth: true }] })
      .mockResolvedValueOnce({ rows: [{ max_level: 3 }] })

    const result = await getDashasCapability.handler({
      chart_id: CHART_ID,
      system: 'yogini',
      as_of_date: '1980-01-01',
    }, undefined)

    expect(result.is_error).toBe(false)
    const flags = (result as typeof result & { judgment_flags?: unknown[] }).judgment_flags
    expect(flags).toContainEqual(expect.objectContaining({
      code: 'as_of_date_precedes_chart_birth', severity: 'warning',
    }))
    expect((result.content as Record<string, unknown>)['temporal_context']).toEqual({
      as_of_date: '1980-01-01',
      birth_date: '1984-02-05',
      as_of_date_status: 'pre_birth',
    })
  })

  it('does not add the pre-birth warning for a post-birth as_of_date', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ replacement_in_progress: false, eligible_build_id: 'build-a', rows: [] }] }) // consistent receipt and page snapshot
      .mockResolvedValueOnce({ rows: [{ birth_date: '1984-02-05', as_of_date_precedes_birth: false }] })
      .mockResolvedValueOnce({ rows: [{ max_level: 3 }] })

    const result = await getDashasCapability.handler({
      chart_id: CHART_ID,
      system: 'yogini',
      as_of_date: '1984-02-05',
    }, undefined)

    expect(result.is_error).toBe(false)
    const flags = (result as typeof result & { judgment_flags?: unknown[] }).judgment_flags
    expect(flags ?? []).not.toContainEqual(expect.objectContaining({
      code: 'as_of_date_precedes_chart_birth',
    }))
    expect((result.content as Record<string, unknown>)['temporal_context']).toBeUndefined()
  })
})
