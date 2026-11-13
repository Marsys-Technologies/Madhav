import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GET } from '../route'

const mocks = vi.hoisted(() => ({ query: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))
vi.mock('@/lib/auth/oidc', () => ({
  verifyOidcToken: () => { throw new Error('Unexpected OIDC call from chart-list route') },
}))

const token = 'synthetic-service-token'
const uid = "fixture-guest' OR '1'='1"
const guestSql = `SELECT DISTINCT c.id,
              COALESCE(c.preferred_name, c.subject_name, c.name) AS display_name
       FROM charts c
       WHERE c.owner_id = $1
       UNION
       SELECT DISTINCT c.id,
              COALESCE(c.preferred_name, c.subject_name, c.name) AS display_name
       FROM charts c
       JOIN chart_grants g ON g.chart_id = c.id
       WHERE g.principal_id = $1
       ORDER BY display_name`
const adminSql = `SELECT id, COALESCE(preferred_name, subject_name, name) AS display_name
       FROM charts
       ORDER BY COALESCE(preferred_name, subject_name, name)`

function request(serviceToken: string | null, user: string | null, role: string | null = null) {
  const headers = new Headers()
  if (serviceToken !== null) headers.set('X-MCP-Internal-Token', serviceToken)
  if (user !== null) headers.set('X-MCP-User', user)
  if (role !== null) headers.set('X-MCP-Role', role)
  const req = new Request('http://fixture.invalid/api/mcp/my/charts', { headers })
  return { req, readHeader: vi.spyOn(req.headers, 'get') }
}

beforeEach(() => {
  vi.stubEnv('MCP_INTERNAL_TOKEN', token)
  mocks.query.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllEnvs()
})

describe('MCP my charts GET', () => {
  it.each([null, '', 'wrong-synthetic-token'])('rejects invalid token %s before reading principal headers or querying', async (invalidToken) => {
    const { req, readHeader } = request(invalidToken, uid, 'super_admin')
    const result = await GET(req)
    expect(result.status).toBe(401)
    expect(await result.json()).toEqual({ error: 'Unauthorized' })
    expect(readHeader.mock.calls).toEqual([['x-mcp-internal-token']])
    expect(mocks.query).not.toHaveBeenCalled()
  })

  it('fails closed when the expected service token is absent', async () => {
    vi.stubEnv('MCP_INTERNAL_TOKEN', '')
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { req, readHeader } = request(token, uid)
    const result = await GET(req)
    expect(result.status).toBe(401)
    expect(readHeader.mock.calls).toEqual([['x-mcp-internal-token']])
    expect(mocks.query).not.toHaveBeenCalled()
  })

  it.each([null, ''])('requires a UID after valid service authentication (%s)', async (missingUid) => {
    const { req, readHeader } = request(token, missingUid, 'super_admin')
    const result = await GET(req)
    expect(result.status).toBe(400)
    expect(await result.json()).toEqual({ error: 'X-MCP-User header required' })
    expect(readHeader.mock.calls).toEqual([['x-mcp-internal-token'], ['x-mcp-user'], ['x-mcp-role']])
    expect(mocks.query).not.toHaveBeenCalled()
  })

  it.each([null, 'guest', 'SUPER_ADMIN', 'super_admin, guest'])('uses guest scope for role header %s', async (role) => {
    mocks.query.mockResolvedValueOnce({ rows: [
      { id: 'fixture-owned', display_name: 'A', ignored: 'omitted' },
      { id: 'fixture-granted', display_name: 'B' },
    ] })
    const { req } = request(token, uid, role)
    const result = await GET(req)
    expect(result.status).toBe(200)
    expect(mocks.query.mock.calls).toEqual([[guestSql, [uid]]])
    expect(await result.json()).toEqual({ charts: [
      { id: 'fixture-owned', display_name: 'A', index: 0 },
      { id: 'fixture-granted', display_name: 'B', index: 1 },
    ] })
  })

  it('uses the unbound all-chart query only for exact super_admin', async () => {
    mocks.query.mockResolvedValueOnce({ rows: [{ id: 'fixture-chart', display_name: 'A' }] })
    const { req } = request(token, uid, 'super_admin')
    const result = await GET(req)
    expect(result.status).toBe(200)
    expect(mocks.query.mock.calls).toEqual([[adminSql]])
    expect(await result.json()).toEqual({ charts: [{ id: 'fixture-chart', display_name: 'A', index: 0 }] })
  })

  it('preserves an empty success and lets a query failure propagate', async () => {
    const failure = new Error('synthetic query failure')
    mocks.query.mockResolvedValueOnce({ rows: [] }).mockRejectedValueOnce(failure)
    const result = await GET(request(token, uid).req)
    expect(result.status).toBe(200)
    expect(await result.json()).toEqual({ charts: [] })
    await expect(GET(request(token, uid).req)).rejects.toBe(failure)
    expect(mocks.query.mock.calls).toEqual([[guestSql, [uid]], [guestSql, [uid]]])
  })
})
