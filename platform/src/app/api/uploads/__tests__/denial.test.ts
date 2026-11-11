import { beforeEach, describe, expect, it, vi } from 'vitest'

const { user, store, retrieve } = vi.hoisted(() => ({
  user: vi.fn(),
  store: vi.fn(),
  retrieve: vi.fn(),
}))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: user }))
vi.mock('@/lib/multimodal/fake_gcs_store', () => ({ fakeGcsStore: store, fakeGcsRetrieve: retrieve }))

import { POST } from '../sign/route'
import { GET, PUT } from '../store/[token]/route'

const TOKEN = '00000000-0000-4000-8000-000000000001'
const metadata = { filename: 'fixture.png', contentType: 'image/png', size: 12 }

function sign(body: string) {
  return POST(new Request('https://fixture.invalid/api/uploads/sign', { method: 'POST', body }))
}

function access(method: typeof GET, token = TOKEN) {
  const request = new Request('https://fixture.invalid/api/uploads/store/' + token, {
    method: method === PUT ? 'PUT' : 'GET',
    ...(method === PUT ? { body: 'synthetic', headers: { 'x-filename': '%' } } : {}),
  })
  vi.spyOn(request, 'arrayBuffer').mockRejectedValue(new Error('body must remain unread'))
  return method(request, { params: Promise.resolve({ token }) }).then(response => ({ request, response }))
}

beforeEach(() => {
  vi.clearAllMocks()
  user.mockResolvedValue({ uid: 'synthetic-owner' })
})

describe('upload containment', () => {
  it('requires authentication before sign validation or store path handling', async () => {
    user.mockResolvedValue(null)
    const responses = await Promise.all([sign('{'), ...[GET, PUT].map(method => access(method, 'bad').then(value => value.response))])
    for (const response of responses) {
      expect(response.status).toBe(401)
      expect(response.headers.get('Cache-Control')).toBe('private, no-store')
    }
    expect(store).not.toHaveBeenCalled()
    expect(retrieve).not.toHaveBeenCalled()
  })

  it.each(['{', 'null', '[]', '1', '{}'])('rejects malformed sign metadata (%s)', async input => {
    const response = await sign(input)
    expect(response.status).toBe(400)
    expect(response.headers.get('Cache-Control')).toBe('private, no-store')
  })

  it('preserves invalid MIME rejection and refuses valid metadata without issuing a token', async () => {
    expect((await sign(JSON.stringify({ ...metadata, contentType: 'text/html' }))).status).toBe(422)
    const response = await sign(JSON.stringify(metadata))
    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('private, no-store')
    expect(await response.json()).toEqual({ error: 'Attachment uploads are currently unavailable.' })
    expect(store).not.toHaveBeenCalled()
  })

  it.each([GET, PUT])('keeps malformed token rejection in %s', async method => {
    const { request, response } = await access(method, 'malformed')
    expect(response.status).toBe(400)
    expect(response.headers.get('Cache-Control')).toBe('private, no-store')
    expect(request.arrayBuffer).not.toHaveBeenCalled()
  })

  it.each(['synthetic-owner', 'synthetic-other'])('denies reads and writes uniformly for %s', async uid => {
    user.mockResolvedValue({ uid })
    for (const method of [GET, PUT]) {
      for (const token of [TOKEN, '00000000-0000-4000-8000-000000000002']) {
        const { request, response } = await access(method, token)
        expect(response.status).toBe(503)
        expect(response.headers.get('Cache-Control')).toBe('private, no-store')
        expect(response.headers.has('Content-Disposition')).toBe(false)
        expect(await response.json()).toEqual({ error: 'Attachment storage is currently unavailable.' })
        expect(request.arrayBuffer).not.toHaveBeenCalled()
      }
    }
    expect(store).not.toHaveBeenCalled()
    expect(retrieve).not.toHaveBeenCalled()
  })
})
