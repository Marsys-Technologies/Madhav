/**
 * Disabled accounts stop working at once for MCP credentials too (SS N-413, S10).
 *
 * A valid, unrevoked MCP key (or OAuth token) is only usable while its OWNER's
 * profile is 'active'. The key/token rows are never altered, so re-enabling the user
 * restores them. Covers: validateMcpKey (bearer-key path), OAuth validateAccessToken
 * and refreshAccessToken, the OAuth token-issue and session-to-code routes, and the
 * 'inactive' role -> 'deny' mapping in authorizeChartAccess.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('@/lib/mcp/service_token', () => ({ validateServiceToken: vi.fn(() => true) }))
vi.mock('@/lib/firebase/server', () => ({ verifySessionCookie: vi.fn() }))

import { query } from '@/lib/db/client'
import { verifySessionCookie } from '@/lib/firebase/server'
import { generateMcpKey, isMcpOwnerActive, resolveMcpPrincipalRole, validateMcpKey } from '@/lib/mcp/auth'
import { refreshAccessToken, sha256, validateAccessToken } from '@/lib/mcp/oauth/store'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'

const mockQuery = vi.mocked(query)
const rows = (r: unknown[]) => ({ rows: r, rowCount: r.length, command: '', oid: 0, fields: [] }) as never

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockReset()
})

describe('validateMcpKey: owner status', () => {
  async function keyRow(ownerStatus: string | null, ownerRole: string | null = 'guest') {
    const { key_id, full_key, key_hash } = await generateMcpKey('test')
    mockQuery
      .mockResolvedValueOnce(rows([{ key_id, key_hash, user_uid: 'owner-1', model_family: null, owner_status: ownerStatus, owner_role: ownerRole }]))
      .mockResolvedValue(rows([])) // last_used_at touch
    return { key_id, header: `Bearer ${full_key}` }
  }

  it('accepts a valid unrevoked key whose owner is active', async () => {
    const { key_id, header } = await keyRow('active')
    const principal = await validateMcpKey(header)
    expect(principal).toMatchObject({ user_uid: 'owner-1', key_id, role: 'guest' })
  })

  it('maps the joined owner role (super_admin) without a second profiles query', async () => {
    const { header } = await keyRow('active', 'super_admin')
    const principal = await validateMcpKey(header)
    expect(principal?.role).toBe('super_admin')
    const profileReads = mockQuery.mock.calls.filter(([sql]) => /FROM profiles/.test(String(sql)) && !/mcp_api_keys/.test(String(sql)))
    expect(profileReads).toHaveLength(0)
  })

  it.each(['disabled', 'pending'])('rejects a valid unrevoked key whose owner is %s', async (status) => {
    const { header } = await keyRow(status)
    expect(await validateMcpKey(header)).toBeNull()
  })

  it('rejects a valid key whose owner has no profile row (fail closed)', async () => {
    const { header } = await keyRow(null, null)
    expect(await validateMcpKey(header)).toBeNull()
  })

  it('does not touch last_used_at for a refused key', async () => {
    const { header } = await keyRow('disabled')
    await validateMcpKey(header)
    expect(mockQuery.mock.calls.some(([sql]) => /UPDATE mcp_api_keys/.test(String(sql)))).toBe(false)
  })

  it('reads the owner in the SAME query (one round trip) and never rewrites the key row', async () => {
    const { header } = await keyRow('disabled')
    await validateMcpKey(header)
    const [sql] = mockQuery.mock.calls[0]
    expect(String(sql)).toMatch(/JOIN profiles p ON p\.id = k\.user_uid/)
    expect(String(sql)).toMatch(/revoked_at IS NULL/)
    expect(mockQuery.mock.calls.some(([s]) => /(UPDATE|DELETE)[\s\S]*mcp_api_keys/.test(String(s)))).toBe(false)
  })
})

describe('resolveMcpPrincipalRole / isMcpOwnerActive', () => {
  it('active guest and active super_admin keep their role', async () => {
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'active' }]))
    expect(await resolveMcpPrincipalRole('u')).toBe('guest')
    mockQuery.mockResolvedValueOnce(rows([{ role: 'super_admin', status: 'active' }]))
    expect(await resolveMcpPrincipalRole('u')).toBe('super_admin')
  })

  it('a disabled super_admin is inactive, not super_admin', async () => {
    mockQuery.mockResolvedValueOnce(rows([{ role: 'super_admin', status: 'disabled' }]))
    expect(await resolveMcpPrincipalRole('u')).toBe('inactive')
  })

  it('isMcpOwnerActive mirrors it', async () => {
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'active' }]))
    expect(await isMcpOwnerActive('u')).toBe(true)
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'disabled' }]))
    expect(await isMcpOwnerActive('u')).toBe(false)
    mockQuery.mockResolvedValueOnce(rows([]))
    expect(await isMcpOwnerActive('u')).toBe(false)
  })
})

describe('authorizeChartAccess: inactive principal', () => {
  it('denies without reading anything, even if the uid owns the chart', async () => {
    const db = { query: vi.fn().mockResolvedValue({ rows: [{ owner_id: 'u' }] }) }
    const perm = await authorizeChartAccess({ principal: { uid: 'u', role: 'inactive' }, chartId: 'c', db })
    expect(perm).toBe('deny')
    expect(db.query).not.toHaveBeenCalled()
  })
})

describe('OAuth access / refresh tokens: owner status', () => {
  const expiry = new Date(Date.now() + 3_600_000).toISOString()

  it('validateAccessToken: active owner accepted', async () => {
    mockQuery.mockResolvedValueOnce(rows([{ uid: 'owner-1', scopes: ['mcp:tools'], expires_at: expiry, refresh_expires_at: expiry, owner_status: 'active' }]))
    expect(await validateAccessToken('a-token')).toMatchObject({ uid: 'owner-1', scopes: ['mcp:tools'] })
  })

  it.each(['disabled', 'pending', null])('validateAccessToken: owner status %s -> null', async (status) => {
    mockQuery.mockResolvedValueOnce(rows([{ uid: 'owner-1', scopes: [], expires_at: expiry, refresh_expires_at: expiry, owner_status: status }]))
    expect(await validateAccessToken('a-token')).toBeNull()
  })

  it('validateAccessToken: owner joined in the same query, looked up by hash', async () => {
    mockQuery.mockResolvedValueOnce(rows([]))
    await validateAccessToken('a-token')
    const [sql, params] = mockQuery.mock.calls[0]
    expect(String(sql)).toMatch(/JOIN profiles p ON p\.id = t\.uid/)
    expect(params).toEqual([sha256('a-token')])
  })

  it('refreshAccessToken: active owner rotates the pair', async () => {
    mockQuery
      .mockResolvedValueOnce(rows([{ access_token_hash: 'h', uid: 'owner-1', scopes: ['mcp:tools'], refresh_expires_at: expiry, owner_status: 'active' }]))
      .mockResolvedValue(rows([]))
    const tokens = await refreshAccessToken('r-token')
    expect(tokens?.access_token).toMatch(/^mcp_at/)
  })

  it.each(['disabled', 'pending'])('refreshAccessToken: owner %s -> null, old pair NOT deleted, nothing issued', async (status) => {
    mockQuery.mockResolvedValueOnce(rows([{ access_token_hash: 'h', uid: 'owner-1', scopes: [], refresh_expires_at: expiry, owner_status: status }]))
    expect(await refreshAccessToken('r-token')).toBeNull()
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })
})

describe('OAuth routes', () => {
  it('POST /api/mcp/oauth/tokens refuses to mint for a disabled owner (403) and writes nothing', async () => {
    const { POST } = await import('@/app/api/mcp/oauth/tokens/route')
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'disabled' }]))
    const res = await POST(new Request('http://localhost/api/mcp/oauth/tokens', {
      method: 'POST',
      body: JSON.stringify({ uid: 'owner-1', scopes: ['mcp:tools'] }),
    }))
    expect(res.status).toBe(403)
    expect(await res.json()).toMatchObject({ error: 'invalid_grant' })
    expect(mockQuery.mock.calls.some(([sql]) => /INSERT INTO mcp_oauth_tokens/.test(String(sql)))).toBe(false)
  })

  it('POST /api/mcp/oauth/tokens still mints for an active owner (201)', async () => {
    const { POST } = await import('@/app/api/mcp/oauth/tokens/route')
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'active' }])).mockResolvedValue(rows([]))
    const res = await POST(new Request('http://localhost/api/mcp/oauth/tokens', {
      method: 'POST',
      body: JSON.stringify({ uid: 'owner-1', scopes: ['mcp:tools'] }),
    }))
    expect(res.status).toBe(201)
  })

  it('POST /api/auth/verify-session: a disabled owner\'s still-valid cookie yields 401, no uid', async () => {
    const { POST } = await import('@/app/api/auth/verify-session/route')
    vi.mocked(verifySessionCookie).mockResolvedValue({ uid: 'owner-1' } as never)
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'disabled' }]))
    const res = await POST(new Request('http://localhost/api/auth/verify-session', {
      method: 'POST',
      body: JSON.stringify({ session: 'cookie-value' }),
    }))
    expect(res.status).toBe(401)
    expect(await res.json()).not.toHaveProperty('uid')
  })

  it('POST /api/auth/verify-session: an active owner still gets the uid', async () => {
    const { POST } = await import('@/app/api/auth/verify-session/route')
    vi.mocked(verifySessionCookie).mockResolvedValue({ uid: 'owner-1' } as never)
    mockQuery.mockResolvedValueOnce(rows([{ role: 'guest', status: 'active' }]))
    const res = await POST(new Request('http://localhost/api/auth/verify-session', {
      method: 'POST',
      body: JSON.stringify({ session: 'cookie-value' }),
    }))
    expect(await res.json()).toEqual({ uid: 'owner-1' })
  })
})
