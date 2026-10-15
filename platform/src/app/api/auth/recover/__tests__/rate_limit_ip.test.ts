// @vitest-environment node
/**
 * SS N-373 item 4 (recover swap): the recovery rate limit keys on the TRUSTED
 * X-Forwarded-For hop, so rotating the client-controlled leftmost entry does not
 * mint a fresh bucket per request.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn().mockResolvedValue({ rows: [] }) }))

import { POST } from '@/app/api/auth/recover/route'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'

const post = (xff: string) =>
  new Request('http://localhost/api/auth/recover', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-forwarded-for': xff },
    body: JSON.stringify({ identifier: 'someone' }),
  })

beforeEach(() => {
  __resetRpmCountersForTest()
  vi.stubEnv('NEXT_PUBLIC_FIREBASE_API_KEY', 'test-public-key')
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}')))
})

describe('POST /api/auth/recover rate limit', () => {
  it('rotating the spoofed leftmost X-Forwarded-For entry does not evade the 10/min limit', async () => {
    const statuses: number[] = []
    for (let i = 0; i < 14; i++) statuses.push((await POST(post(`10.9.${i}.1, 203.0.113.9`))).status)
    expect(statuses.filter((s) => s === 429).length).toBe(4)
  })

  it('a different trusted IP is a different bucket', async () => {
    for (let i = 0; i < 10; i++) await POST(post(`10.9.${i}.1, 203.0.113.9`))
    expect((await POST(post('1.1.1.1, 203.0.113.9'))).status).toBe(429)
    expect((await POST(post('1.1.1.1, 198.51.100.7'))).status).not.toBe(429)
  })
})
