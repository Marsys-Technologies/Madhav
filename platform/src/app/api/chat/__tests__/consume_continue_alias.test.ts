// @vitest-environment node
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GET, POST } from '../consume/continue/route'

afterEach(() => vi.restoreAllMocks())

describe('consume/continue compatibility alias', () => {
  it.each(['', '?conversation_id=fixture&last_message_id=message'])('GET%s is explicitly unavailable without redirecting or executing continuation', async suffix => {
    const fetch = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('unexpected network request'))
    const response = await GET(new Request(`https://x.test/api/chat/consume/continue${suffix}`))
    expect(response.status).toBe(410)
    expect(response.headers.get('Location')).toBeNull()
    expect(response.redirected).toBe(false)
    expect(await response.json()).toEqual({
      error: 'GET continuation is unavailable. Use POST /api/chat/consult/continue.',
      code: 'ENDPOINT_GONE',
    })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('POST retains the permanent redirect and empty response', async () => {
    const response = await POST(new Request('https://x.test/api/chat/consume/continue', { method: 'POST' }))
    expect(response.status).toBe(308)
    expect(response.headers.get('Location')).toBe('https://x.test/api/chat/consult/continue')
    expect(await response.text()).toBe('')
  })

  it('POST forwards the complete query unchanged, including repeats and encoding', async () => {
    const query = '?query_id=abc%2Fdef&since_chars=10&query_id=two&empty=&plus=a+b'
    const response = await POST(new Request(`https://x.test/api/chat/consume/continue${query}`, {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: '{"conversation_id":"fixture"}',
    }))
    expect(response.status).toBe(308)
    expect(response.headers.get('Location')).toBe(`https://x.test/api/chat/consult/continue${query}`)
    expect(await response.text()).toBe('')
  })
})
