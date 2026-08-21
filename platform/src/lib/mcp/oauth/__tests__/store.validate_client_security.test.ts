/**
 * SF-002: validateClient must never validate a client with no secret provided.
 *
 * Prior behaviour: `if (clientSecret !== undefined)` skipped hash verification
 * entirely when no secret was sent, returning the client record as valid. Reached
 * externally via POST /mcp/oauth/token {grant_type:'client_credentials', client_id}
 * with no client_secret at all -- JSON.stringify() drops an undefined key, so the
 * platform side saw client_secret===undefined and skipped verification, issuing
 * real tokens for that client's owner_uid to anyone who knew a (non-secret)
 * client_id.
 *
 * validateClient has exactly one caller chain in this codebase (the
 * client_credentials grant, via /api/mcp/oauth/clients/validate) -- the
 * authorization_code+PKCE flow never calls it (see token.ts's authorization_code
 * branch, which uses consumeAuthCode + its own PKCE check instead). So there is no
 * legitimate no-secret caller to preserve.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createHash } from 'crypto'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
import { validateClient } from '../store'

const mockQuery = query as ReturnType<typeof vi.fn>

const REAL_SECRET = 'correct-horse-battery-staple'
const REAL_HASH = createHash('sha256').update(REAL_SECRET).digest('hex')

const CLIENT_ROW = {
  client_id: 'victim_client',
  client_secret_hash: REAL_HASH,
  owner_uid: 'victim-firebase-uid',
  redirect_uris: ['https://example.com/callback'],
  scopes: ['read'],
  created_at: new Date('2026-01-01'),
}

beforeEach(() => {
  mockQuery.mockReset()
})

describe('validateClient — SF-002 no-secret bypass closed', () => {
  it('rejects a known client_id when no secret is provided at all (the exploit path)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [CLIENT_ROW] })
    const result = await validateClient('victim_client', undefined)
    expect(result).toBeNull()
  })

  it('rejects a known client_id when secret is an empty string', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [CLIENT_ROW] })
    const result = await validateClient('victim_client', '')
    expect(result).toBeNull()
  })

  it('rejects a known client_id with a wrong secret', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [CLIENT_ROW] })
    const result = await validateClient('victim_client', 'wrong-secret')
    expect(result).toBeNull()
  })

  it('accepts a known client_id with the correct secret', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [CLIENT_ROW] })
    const result = await validateClient('victim_client', REAL_SECRET)
    expect(result).not.toBeNull()
    expect(result?.owner_uid).toBe('victim-firebase-uid')
  })

  it('rejects an unknown client_id regardless of secret', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await validateClient('nonexistent_client', undefined)
    expect(result).toBeNull()
  })
})
