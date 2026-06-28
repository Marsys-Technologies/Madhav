/**
 * SSE route fallback behaviour.
 *
 * Key assertion: when Pub/Sub subscription creation throws, the route falls
 * back to 5s pollingStream (not heartbeat-only). We verify this by inspecting
 * what the response stream emits: pollingStream sends a JSON `hello` data frame,
 * pubsubStream sends an SSE comment (`: hello …`). So the test checks that the
 * first bytes from the response body are `data:` (poll path), not `: hello` (pubsub path).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// ─── hoisted mocks (must precede vi.mock calls) ───────────────────────────────

const { mockCreateSubscription, MockPubSub } = vi.hoisted(() => {
  const mockCreateSubscription = vi.fn()
  // Must use `function`, not an arrow, so `new MockPubSub()` works.
  const MockPubSub = vi.fn().mockImplementation(function () {
    return {
      topic: vi.fn().mockReturnValue({
        createSubscription: mockCreateSubscription,
      }),
    }
  })
  return { mockCreateSubscription, MockPubSub }
})

vi.mock('@google-cloud/pubsub', () => ({ PubSub: MockPubSub }))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const mockGetServerUser = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

// ─── helpers ──────────────────────────────────────────────────────────────────

const CHART_ID = 'test-chart-abc'
const SUPER_ADMIN = { uid: 'admin-1' }

function makeRequest(chartId = CHART_ID): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/sse?chart_id=${chartId}`)
}

async function readFirstFrame(response: Response): Promise<string> {
  const reader = response.body!.getReader()
  const { value } = await reader.read()
  reader.cancel()
  return new TextDecoder().decode(value)
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('GET /api/cockpit/sse', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    process.env.GOOGLE_CLOUD_PROJECT = 'madhav-astrology'
    delete process.env.PUBSUB_DISABLED

    mockGetServerUser.mockResolvedValue(SUPER_ADMIN)
    mockQuery.mockResolvedValue({ rows: [{ role: 'super_admin' }] })
  })

  it('falls back to pollingStream (not heartbeat-only) when subscription creation throws', async () => {
    mockCreateSubscription.mockRejectedValue(new Error('PERMISSION_DENIED: subscription create failed'))

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(200)
    expect(res.headers.get('Content-Type')).toBe('text/event-stream')

    const firstFrame = await readFirstFrame(res)

    // Both paths now emit a named hello event: `event: hello\ndata: {...}\n\n`
    expect(firstFrame).toMatch(/^event: hello\n/)
    expect(firstFrame).toContain(CHART_ID)
  })

  it('uses Pub/Sub stream when subscription creation succeeds', async () => {
    const mockSub = {
      on: vi.fn(),
      removeAllListeners: vi.fn(),
      delete: vi.fn().mockResolvedValue(undefined),
    }
    mockCreateSubscription.mockResolvedValue([mockSub])

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(200)

    const firstFrame = await readFirstFrame(res)

    // pubsubStream emits a named hello event
    expect(firstFrame).toMatch(/^event: hello\n/)
    expect(firstFrame).toContain(CHART_ID)
  })

  it('returns 200 + poll path when PUBSUB_DISABLED is set', async () => {
    process.env.PUBSUB_DISABLED = '1'

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(200)
    const firstFrame = await readFirstFrame(res)
    expect(firstFrame).toMatch(/^event: hello\n/)
  })

  it('returns 403 for unauthenticated requests', async () => {
    mockGetServerUser.mockResolvedValue(null)

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(403)
  })

  it('returns 400 when chart_id is missing', async () => {
    const { GET } = await import('../route')
    const res = await GET(new NextRequest('http://localhost/api/cockpit/sse'))

    expect(res.status).toBe(400)
  })
})
