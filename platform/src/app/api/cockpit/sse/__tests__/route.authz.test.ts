/**
 * Regression test for V3-E-011 (Paripraśna Assurance systemic authorization
 * sweep, Session S5): cross-chart live-stream disclosure on GET
 * /api/cockpit/sse.
 *
 * Same root-cause family as B-001/B-007/B-008 and the runs/active sibling:
 * the handler checked only `getServerUser() !== null` and then trusted the
 * caller-supplied `chart_id` with no ownership/grant check — any
 * authenticated user could open a live SSE stream on an arbitrary chart_id
 * and receive real-time `run.state_change` / `asset.progress` events
 * (including `rows_written`) indefinitely.
 *
 * Fix: gate the route through `requireChartPermission` at 'read' access,
 * placed after chart_id is read and BEFORE the pubsub/polling branch, so
 * neither stream implementation can open without it.
 *
 * This file is deliberately independent of the pre-existing
 * `route.test.ts` (which covers pubsub-vs-polling fallback behaviour for an
 * always-super_admin caller) — it adds the authz DENY/ALLOW matrix without
 * touching that file's fixtures.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

function makeReq(chartId: string): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/sse?chart_id=${chartId}`)
}

/** SQL-shape-dispatching mock, mirroring the runs/route.authz.test.ts precedent. */
function setupMocks(opts: { uid: string; role?: string; ownerId?: string | null; grantPermission?: string | null }) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue({ uid })

  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({
        rows: ownerId !== null ? [{ owner_id: ownerId }] : [],
        rowCount: ownerId !== null ? 1 : 0,
      })
    }
    // Any other query (build_runs poll, asset_throughput poll) — empty, harmless.
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

async function readFirstFrame(response: Response): Promise<string | null> {
  if (!response.body) return null
  const reader = response.body.getReader()
  const { value } = await reader.read()
  reader.cancel()
  return value ? new TextDecoder().decode(value) : null
}

beforeEach(() => {
  vi.clearAllMocks()
  // Force the pollingStream branch — this fix must gate BOTH branches, but
  // exercising one deterministically (no external Pub/Sub client to mock)
  // is enough to prove the gate runs before either stream opens.
  process.env.PUBSUB_DISABLED = '1'
})

describe('GET /api/cockpit/sse — V3-E-011 cross-chart live-stream disclosure', () => {
  it('DENIES a non-owner guest opening a stream on another chart — no stream body reaches them', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const { GET } = await import('../route')
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(res.headers.get('Content-Type')).not.toBe('text/event-stream')
    // The real proof: no SSE frame of any kind (hello/heartbeat/event) was
    // ever emitted — the body is the plain 403 JSON error, not a stream.
    const body = await res.clone().json().catch(() => null)
    expect(body?.code).toBe('FORBIDDEN_CHART')
    const frame = await readFirstFrame(res)
    expect(frame).not.toMatch(/^event: hello\n/)
  })

  it('DENIES a caller when the chart does not exist at all', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const { GET } = await import('../route')
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const { GET } = await import('../route')
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
  })

  it('ALLOWS the legitimate owner to open a stream on their own chart', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const { GET } = await import('../route')
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    expect(res.headers.get('Content-Type')).toBe('text/event-stream')
    const frame = await readFirstFrame(res)
    expect(frame).toMatch(/^event: hello\n/)
  })

  it('ALLOWS a chart_grants view-grantee to open a stream — a read grant covers a live read', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const { GET } = await import('../route')
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })

  it('ALLOWS super_admin to open a stream on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const { GET } = await import('../route')
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })
})
