/**
 * route.test.ts — POST/GET /api/clients/[id]/learning.
 *
 * V3-E-011 finding 2 (MEDIUM): `guardChartAccess()` is an ownership check that
 * does NOT distinguish read from write — a `chart_grants` VIEW-ONLY grantee
 * passes it and could call every mutating action on this route, including
 * `cosign` (flips `mimamsa_calibration_snapshot.publication_status` to
 * 'live'/'revoked' — the route's own docstring calls this "native
 * approve/revoke"), `adjudicate` (inserts `mimamsa_adjudication_log`),
 * `schedule_followup` (inserts `prashna_followup_schedule`), `resonance`
 * (inserts `mimamsa_resonance_feedback`), and `lel_entry` (appends directly to
 * the LEL markdown source-of-truth file — the most sensitive write in the
 * route, not named in the original finding text but independently confirmed
 * mutating by inspection).
 *
 * Every one of this route's five POST actions performs a write; none is
 * genuinely read-only. Fix adds a `requireChartPermission({ access: 'write' })`
 * gate (owner/super_admin only) after the existing `guardChartAccess` ownership
 * check and before the action switch — additive, does not remove
 * `guardChartAccess` (still gates GET, the one genuinely read-only surface in
 * this route).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('fs', () => ({
  existsSync: vi.fn(() => true),
  appendFileSync: vi.fn(),
}))

import * as fs from 'fs'
import { POST, GET } from '../route'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const OWNER_UID = 'owner-uid'
const VIEW_GRANTEE_UID = 'view-grantee-uid'
const ADMIN_UID = 'admin-uid'

/**
 * Configures `mockQuery` to answer every distinct SQL shape this route (and
 * the shared authz helpers it now calls) issues, keyed by caller identity:
 *   - guardChartAccess's own combined charts+chart_grants+profiles query
 *   - requireChartPermission's `getPrincipalRole` (`FROM profiles`)
 *   - authorizeChartAccess's `SELECT owner_id FROM charts WHERE id=$1`
 *   - authorizeChartAccess's `SELECT permission FROM chart_grants ...`
 * Any other query (the action handlers' own INSERT/UPDATE/SELECT) is recorded
 * and answered with an empty row set.
 */
function setupMocks(opts: { role: 'guest' | 'super_admin'; isOwner: boolean; hasGrant: boolean }) {
  const { role, isOwner, hasGrant } = opts
  mockQuery.mockImplementation((sql: string) => {
    if (sql.includes('LEFT JOIN chart_grants g')) {
      // guardChartAccess: owner OR grantee OR super_admin all pass.
      const passes = isOwner || hasGrant || role === 'super_admin'
      return Promise.resolve({ rows: passes ? [{ id: CHART_ID }] : [] })
    }
    if (sql.includes('FROM profiles')) {
      return Promise.resolve({ rows: [{ role }] })
    }
    if (sql.includes('SELECT owner_id FROM charts WHERE id=$1')) {
      return Promise.resolve({ rows: [{ owner_id: isOwner ? OWNER_UID : (role === 'super_admin' ? OWNER_UID : 'someone-else') }] })
    }
    if (sql.includes('FROM chart_grants WHERE chart_id=$1')) {
      return Promise.resolve({ rows: hasGrant ? [{ permission: 'view' }] : [] })
    }
    return Promise.resolve({ rows: [] })
  })
}

function makeReq(body: object): NextRequest {
  return new NextRequest(`http://localhost/api/clients/${CHART_ID}/learning`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function paramsFor(): { params: Promise<{ id: string }> } {
  return { params: Promise.resolve({ id: CHART_ID }) }
}

beforeEach(() => {
  vi.clearAllMocks()
  global.fetch = vi.fn().mockResolvedValue({ ok: true }) as unknown as typeof fetch
})

describe('POST /api/clients/[id]/learning — write-gated mutating actions (V3-E-011 finding 2)', () => {
  const MUTATING_ACTIONS: Array<{ action: string; body: object }> = [
    { action: 'adjudicate', body: { action: 'adjudicate', prediction_id: 'p1', outcome: 'happened' } },
    { action: 'lel_entry', body: { action: 'lel_entry', event_id: 'e1', category: 'career', magnitude: 'major', date: '2026-01-01' } },
    { action: 'schedule_followup', body: { action: 'schedule_followup', prediction_id: 'p1', domain: 'career', fructification_date: '2026-06-01', follow_up_prompt: 'How did it go?' } },
    { action: 'cosign', body: { action: 'cosign', snapshot_id: 's1', cosign_action: 'approved' } },
    { action: 'resonance', body: { action: 'resonance', signal_ref: 'sig1', resonance: 'resonates' } },
  ]

  for (const { action, body } of MUTATING_ACTIONS) {
    it(`DENY: a chart_grants view-only grantee cannot call '${action}' (a read grant is not a write grant)`, async () => {
      mockGetServerUser.mockResolvedValue({ uid: VIEW_GRANTEE_UID })
      setupMocks({ role: 'guest', isOwner: false, hasGrant: true })

      const res = await POST(makeReq(body), paramsFor())

      expect(res.status).toBe(403)
      // Prove the write never actually happened: no INSERT/UPDATE reached the DB,
      // and the LEL markdown file was never appended to.
      const writeCalls = mockQuery.mock.calls.filter(
        (call: unknown[]) => /^\s*(INSERT|UPDATE)/i.test(String(call[0]).trim())
      )
      expect(writeCalls.length).toBe(0)
      expect(fs.appendFileSync).not.toHaveBeenCalled()
    })

    it(`ALLOW: the chart owner can call '${action}'`, async () => {
      mockGetServerUser.mockResolvedValue({ uid: OWNER_UID })
      setupMocks({ role: 'guest', isOwner: true, hasGrant: false })

      const res = await POST(makeReq(body), paramsFor())

      expect(res.status).toBe(200)
    })

    it(`ALLOW: a super_admin can call '${action}'`, async () => {
      mockGetServerUser.mockResolvedValue({ uid: ADMIN_UID })
      setupMocks({ role: 'super_admin', isOwner: false, hasGrant: false })

      const res = await POST(makeReq(body), paramsFor())

      expect(res.status).toBe(200)
    })
  }

  it('DENY: an unauthenticated caller gets 401 before any authz brain runs', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await POST(makeReq({ action: 'cosign', snapshot_id: 's1', cosign_action: 'approved' }), paramsFor())
    expect(res.status).toBe(401)
  })

  it('DENY: a caller with no relationship to the chart at all gets 403 from the existing guardChartAccess check (unchanged)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'total-stranger-uid' })
    setupMocks({ role: 'guest', isOwner: false, hasGrant: false })
    const res = await POST(makeReq({ action: 'adjudicate', prediction_id: 'p1', outcome: 'happened' }), paramsFor())
    expect(res.status).toBe(403)
  })
})

describe('GET /api/clients/[id]/learning — unaffected read path (regression)', () => {
  it('ALLOW: a chart_grants view-only grantee can still read open windows (guardChartAccess unchanged for GET)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: VIEW_GRANTEE_UID })
    setupMocks({ role: 'guest', isOwner: false, hasGrant: true })

    const res = await GET(new NextRequest(`http://localhost/api/clients/${CHART_ID}/learning`), paramsFor())

    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty('open_windows')
  })

  it('DENY: a stranger cannot read', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'total-stranger-uid' })
    setupMocks({ role: 'guest', isOwner: false, hasGrant: false })

    const res = await GET(new NextRequest(`http://localhost/api/clients/${CHART_ID}/learning`), paramsFor())

    expect(res.status).toBe(403)
  })
})
