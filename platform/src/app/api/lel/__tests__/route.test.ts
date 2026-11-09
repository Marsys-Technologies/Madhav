import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'

const { admin, query, record } = vi.hoisted(() => ({
  admin: vi.fn(),
  query: vi.fn(),
  record: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: admin }))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('@/lib/mcp/lel_event_writer', async importOriginal => ({
  ...await importOriginal<typeof import('@/lib/mcp/lel_event_writer')>(),
  recordLelEvent: record,
}))
vi.mock('@/lib/lel/writer', () => ({
  appendPrediction: vi.fn(),
  markPredictionOutcome: vi.fn(),
  appendEvent: vi.fn(() => { throw new Error('Legacy Markdown must not be written') }),
}))

import { POST } from '../route'

const chartId = '11f4618f-a6ed-4cbb-8482-61e56ce3646e'
const event = { date: '2007-03-XX', eventClass: 'education_milestone', description: ' Fictional graduation ' }

function request(payload: unknown = event, contentType = 'application/json') {
  return new NextRequest('http://localhost/api/lel', {
    method: 'POST',
    headers: { 'Content-Type': contentType },
    body: JSON.stringify({ action: 'append_event', chartId, payload }),
  })
}

beforeEach(() => {
  vi.resetAllMocks()
  admin.mockResolvedValue({ user: { uid: 'admin-1' }, profile: { role: 'super_admin', status: 'active' } })
  query.mockResolvedValue({ rows: [{ id: chartId }] })
  record.mockResolvedValue({ id: 'event-row', event_id: 'event-key', created: true })
})

describe('portal Life Events write', () => {
  it('writes to the selected chart with date precision and server-stamped provenance', async () => {
    const response = await POST(request({ ...event, chartId: 'ignored', actor_uid: 'ignored' }))
    expect(response.status).toBe(200)
    expect(record).toHaveBeenCalledWith(expect.objectContaining({
      chartId,
      event: expect.objectContaining({
        event_date: '2007-03-01',
        date_confidence: 'month_known',
        description: 'Fictional graduation',
        event_class: 'education_milestone',
        category: 'education',
        domain: 'education',
        outcome_observed: true,
      }),
      provenance: expect.objectContaining({ actor_uid: 'admin-1' }),
    }))
  })

  it.each([401, 403])('does not write when authorization returns %i', async status => {
    admin.mockResolvedValue(NextResponse.json({}, { status }))
    expect((await POST(request())).status).toBe(status)
    expect(query).not.toHaveBeenCalled()
    expect(record).not.toHaveBeenCalled()
  })

  it.each([
    { ...event, date: '2007-02-30' },
    { ...event, date: '2007-13-XX' },
    { ...event, eventClass: 'unknown' },
    { ...event, description: '   ' },
  ])('rejects malformed input', async payload => {
    expect((await POST(request(payload))).status).toBe(400)
    expect(record).not.toHaveBeenCalled()
  })

  it('rejects a non-JSON cross-origin-compatible submission', async () => {
    expect((await POST(request(event, 'text/plain'))).status).toBe(400)
    expect(record).not.toHaveBeenCalled()
  })

  it('refuses a missing chart', async () => {
    query.mockResolvedValue({ rows: [] })
    expect((await POST(request())).status).toBe(404)
    expect(record).not.toHaveBeenCalled()
  })
})
