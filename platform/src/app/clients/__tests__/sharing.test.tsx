/**
 * Sharing UI + API tests — Unit 3.consult_nav Commit 3.
 *
 * AC.3: Sharing UI grant/revoke writes/removes chart_grants rows;
 *       revoke blocks access on next request (via authorizeChartAccess
 *       returning 'deny' once the row is gone).
 * AC.4: No tier/depth UI in the sharing panel.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, fireEvent, waitFor } from '@testing-library/react'

vi.mock('server-only', () => ({}))

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

beforeEach(() => {
  mockQuery.mockReset()
  mockGetServerUser.mockReset()
})

function makeRequest(method: string, urlSuffix = '', body?: unknown): Request {
  const url = new URL(`http://localhost/api/clients/chart-1/grants${urlSuffix}`)
  if (body !== undefined) {
    return new Request(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  }
  return new Request(url, { method })
}

const params = Promise.resolve({ id: 'chart-1' })

// ── API — GET ────────────────────────────────────────────────────────────────

describe('/api/clients/[id]/grants GET', () => {
  it('401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const { GET } = await import('@/app/api/clients/[id]/grants/route')
    const r = await GET(makeRequest('GET'), { params })
    expect(r.status).toBe(401)
  })

  it('403 when not super_admin', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'guest', email: 'g@test' })
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    const { GET } = await import('@/app/api/clients/[id]/grants/route')
    const r = await GET(makeRequest('GET'), { params })
    expect(r.status).toBe(403)
  })

  it('200 with grants list when super_admin', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery
      .mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({
        rows: [
          { id: 'g1', chart_id: 'chart-1', principal_id: 'guest-1', permission: 'view', granted_by: 'admin', granted_at: '2026-05-28T00:00:00Z' },
        ],
      })
    const { GET } = await import('@/app/api/clients/[id]/grants/route')
    const r = await GET(makeRequest('GET'), { params })
    expect(r.status).toBe(200)
    const body = await r.json()
    expect(body.grants).toHaveLength(1)
    expect(body.grants[0].principal_id).toBe('guest-1')
  })
})

// ── API — POST (grant) ──────────────────────────────────────────────────────

describe('/api/clients/[id]/grants POST', () => {
  it('401 when unauthenticated', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const { POST } = await import('@/app/api/clients/[id]/grants/route')
    const r = await POST(makeRequest('POST', '', { principal_id: 'p1' }), { params })
    expect(r.status).toBe(401)
  })

  it('403 when guest', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'guest', email: 'g@test' })
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    const { POST } = await import('@/app/api/clients/[id]/grants/route')
    const r = await POST(makeRequest('POST', '', { principal_id: 'p1' }), { params })
    expect(r.status).toBe(403)
  })

  it('400 when principal_id missing', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
    const { POST } = await import('@/app/api/clients/[id]/grants/route')
    const r = await POST(makeRequest('POST', '', {}), { params })
    expect(r.status).toBe(400)
  })

  it('404 when chart does not exist', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery
      .mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({ rows: [] }) // chart check
    const { POST } = await import('@/app/api/clients/[id]/grants/route')
    const r = await POST(makeRequest('POST', '', { principal_id: 'p1' }), { params })
    expect(r.status).toBe(404)
  })

  it('AC.3 — 201 grants writes a chart_grants row (INSERT with ON CONFLICT)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery
      .mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({ rows: [{ id: 'chart-1' }] })
      .mockResolvedValueOnce({
        rows: [{ id: 'g1', chart_id: 'chart-1', principal_id: 'guest-1', permission: 'view', granted_by: 'admin', granted_at: '2026-05-28T00:00:00Z' }],
      })
    const { POST } = await import('@/app/api/clients/[id]/grants/route')
    const r = await POST(makeRequest('POST', '', { principal_id: 'guest-1' }), { params })
    expect(r.status).toBe(201)
    const body = await r.json()
    expect(body.grant.principal_id).toBe('guest-1')
    expect(body.grant.permission).toBe('view')

    // Inspect the INSERT call:
    const insertCall = mockQuery.mock.calls[2]
    expect(insertCall[0]).toMatch(/INSERT INTO chart_grants/)
    expect(insertCall[0]).toMatch(/ON CONFLICT/)
    expect(insertCall[1]).toEqual(['chart-1', 'guest-1', 'admin'])
  })
})

// ── API — DELETE (revoke) ───────────────────────────────────────────────────

describe('/api/clients/[id]/grants DELETE', () => {
  it('AC.3 — revoke removes the chart_grants row', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery
      .mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({ rows: [{ id: 'g1' }] }) // DELETE … RETURNING
    const { DELETE } = await import('@/app/api/clients/[id]/grants/route')
    const r = await DELETE(makeRequest('DELETE', '?principal_id=guest-1'), { params })
    expect(r.status).toBe(200)
    const body = await r.json()
    expect(body.revoked).toBe('g1')

    const deleteCall = mockQuery.mock.calls[1]
    expect(deleteCall[0]).toMatch(/DELETE FROM chart_grants/)
    expect(deleteCall[1]).toEqual(['chart-1', 'guest-1'])
  })

  it('404 when grant does not exist', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery
      .mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({ rows: [] })
    const { DELETE } = await import('@/app/api/clients/[id]/grants/route')
    const r = await DELETE(makeRequest('DELETE', '?principal_id=guest-x'), { params })
    expect(r.status).toBe(404)
  })

  it('403 when not super_admin', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'guest', email: 'g@test' })
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    const { DELETE } = await import('@/app/api/clients/[id]/grants/route')
    const r = await DELETE(makeRequest('DELETE', '?principal_id=guest-1'), { params })
    expect(r.status).toBe(403)
  })

  it('400 when principal_id query param missing', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'admin', email: 'a@test' })
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
    const { DELETE } = await import('@/app/api/clients/[id]/grants/route')
    const r = await DELETE(makeRequest('DELETE', ''), { params })
    expect(r.status).toBe(400)
  })
})

// ── SharingPanel UI ─────────────────────────────────────────────────────────

describe('SharingPanel — UI grant/revoke flow (AC.3)', () => {
  it('renders empty state when no grants', async () => {
    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { getByTestId } = render(<SharingPanel chartId="chart-1" initialGrants={[]} />)
    expect(getByTestId('sharing-empty')).toBeTruthy()
  })

  it('renders grant rows for each grant', async () => {
    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { getAllByTestId } = render(
      <SharingPanel
        chartId="chart-1"
        initialGrants={[
          { id: 'g1', principal_id: 'guest-1', permission: 'view', granted_by: 'admin', granted_at: '2026-05-28' },
          { id: 'g2', principal_id: 'guest-2', permission: 'view', granted_by: 'admin', granted_at: '2026-05-27' },
        ]}
      />
    )
    expect(getAllByTestId('grant-row')).toHaveLength(2)
  })

  it('AC.3 — clicking Grant POSTs principal_id to /api/clients/[id]/grants', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (init?.method === 'POST') {
        return new Response(JSON.stringify({ grant: { id: 'g1', principal_id: 'guest-9', permission: 'view', granted_by: 'admin', granted_at: '2026-05-28' } }), { status: 201 })
      }
      if (url.endsWith('/grants') && (!init || init.method === undefined || init.method === 'GET')) {
        return new Response(JSON.stringify({ grants: [{ id: 'g1', principal_id: 'guest-9', permission: 'view', granted_by: 'admin', granted_at: '2026-05-28' }] }), { status: 200 })
      }
      return new Response('{}', { status: 200 })
    }) as unknown as typeof fetch

    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { getByTestId } = render(
      <SharingPanel chartId="chart-1" initialGrants={[]} fetcher={fetcher} />
    )

    fireEvent.change(getByTestId('grant-principal-input'), { target: { value: 'guest-9' } })
    fireEvent.click(getByTestId('grant-submit-button'))

    await waitFor(() => {
      const postCall = (fetcher as unknown as { mock: { calls: unknown[][] } }).mock.calls.find(
        (c) => (c[1] as RequestInit)?.method === 'POST'
      )
      expect(postCall).toBeDefined()
      const body = JSON.parse((postCall![1] as RequestInit).body as string) as { principal_id: string }
      expect(body.principal_id).toBe('guest-9')
    })
  })

  it('AC.3 — clicking Revoke DELETEs against /api/clients/[id]/grants?principal_id=…', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (init?.method === 'DELETE') {
        return new Response(JSON.stringify({ revoked: 'g1' }), { status: 200 })
      }
      return new Response(JSON.stringify({ grants: [] }), { status: 200 })
    }) as unknown as typeof fetch

    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { getByTestId } = render(
      <SharingPanel
        chartId="chart-1"
        initialGrants={[{ id: 'g1', principal_id: 'guest-9', permission: 'view', granted_by: 'admin', granted_at: '2026-05-28' }]}
        fetcher={fetcher}
      />
    )

    fireEvent.click(getByTestId('grant-revoke-button'))

    await waitFor(() => {
      const deleteCall = (fetcher as unknown as { mock: { calls: unknown[][] } }).mock.calls.find(
        (c) => (c[1] as RequestInit)?.method === 'DELETE'
      )
      expect(deleteCall).toBeDefined()
      const url = deleteCall![0] as string
      expect(url).toContain('/api/clients/chart-1/grants')
      expect(url).toContain('principal_id=guest-9')
    })
  })

  it('AC.4 — sharing panel contains no tier/depth UI', async () => {
    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { container } = render(<SharingPanel chartId="chart-1" initialGrants={[]} />)
    expect(container.textContent?.toLowerCase()).not.toMatch(/tier/)
    expect(container.textContent?.toLowerCase()).not.toMatch(/depth/)
  })

  it('disables Grant button when input empty', async () => {
    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { getByTestId } = render(<SharingPanel chartId="chart-1" initialGrants={[]} />)
    expect(getByTestId('grant-submit-button')).toBeDisabled()
  })

  it('surfaces server error when POST fails', async () => {
    const fetcher = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === 'POST') {
        return new Response(JSON.stringify({ error: 'principal_id_required' }), { status: 400 })
      }
      return new Response(JSON.stringify({ grants: [] }), { status: 200 })
    }) as unknown as typeof fetch

    const { SharingPanel } = await import('@/components/sharing/SharingPanel')
    const { getByTestId } = render(
      <SharingPanel chartId="chart-1" initialGrants={[]} fetcher={fetcher} />
    )
    fireEvent.change(getByTestId('grant-principal-input'), { target: { value: 'bad' } })
    fireEvent.click(getByTestId('grant-submit-button'))
    await waitFor(() => {
      expect(getByTestId('sharing-error').textContent).toMatch(/principal_id_required/)
    })
  })
})

// ── Revoke → next-request denial (integration via authorizeChartAccess) ─────

describe('AC.3 integration — revoke blocks access on next request', () => {
  it('authorizeChartAccess returns "deny" after the chart_grants row is gone', async () => {
    const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')

    // Simulate the DB after revoke: no owner_id match, no chart_grants row.
    const db = {
      query: vi.fn(async (sql: string) => {
        if (sql.includes('FROM charts')) return { rows: [{ owner_id: 'other-owner' }] }
        if (sql.includes('FROM chart_grants')) return { rows: [] }
        return { rows: [] }
      }),
    }

    const perm = await authorizeChartAccess({
      principal: { uid: 'revoked-guest', role: 'guest' },
      chartId: 'chart-1',
      db,
    })
    expect(perm).toBe('deny')
  })

  it('authorizeChartAccess returns "view" while the chart_grants row exists', async () => {
    const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
    const db = {
      query: vi.fn(async (sql: string) => {
        if (sql.includes('FROM charts')) return { rows: [{ owner_id: 'other-owner' }] }
        if (sql.includes('FROM chart_grants')) return { rows: [{ permission: 'view' }] }
        return { rows: [] }
      }),
    }
    const perm = await authorizeChartAccess({
      principal: { uid: 'granted-guest', role: 'guest' },
      chartId: 'chart-1',
      db,
    })
    expect(perm).toBe('view')
  })
})
