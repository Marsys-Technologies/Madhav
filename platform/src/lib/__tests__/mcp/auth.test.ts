/**
 * auth.test.ts — Unit tests for MCP API key validation.
 *
 * Tests: validateMcpKey(), generateMcpKey(), splitKey (via validateMcpKey),
 *        hashKeyTail(), verifyKeyTail().
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { hashKeyTail, verifyKeyTail, generateMcpKey } from '@/lib/mcp/auth'

// Mock the DB client — auth.ts calls query() for DB lookup + last_used_at update.
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

// We import query AFTER the mock so we get the mock reference.
import { query } from '@/lib/db/client'
const mockQuery = vi.mocked(query)

// Import validateMcpKey after mocks are set up.
import { validateMcpKey } from '@/lib/mcp/auth'

// ── hashKeyTail / verifyKeyTail ───────────────────────────────────────────────

describe('hashKeyTail / verifyKeyTail', () => {
  it('round-trip: hash then verify succeeds', () => {
    const tail = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ012345' // 32 chars
    const hash = hashKeyTail(tail)
    expect(verifyKeyTail(tail, hash)).toBe(true)
  })

  it('wrong tail fails verification', () => {
    const tail = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ012345'
    const hash = hashKeyTail(tail)
    expect(verifyKeyTail('WRONG_TAIL_NOT_THE_ORIGINAL____X', hash)).toBe(false)
  })

  it('empty hash fails gracefully', () => {
    expect(verifyKeyTail('some-tail', '')).toBe(false)
  })

  it('malformed hash (no colon) fails gracefully', () => {
    expect(verifyKeyTail('some-tail', 'noColonHere')).toBe(false)
  })
})

// ── generateMcpKey ─────────────────────────────────────────────────────────────

describe('generateMcpKey', () => {
  it('returns key_id, full_key, key_hash', async () => {
    const { key_id, full_key, key_hash } = await generateMcpKey('dev')
    expect(key_id).toMatch(/^mcp_dev_[A-Za-z0-9]{8}$/)
    expect(full_key).toMatch(/^mcp_dev_[A-Za-z0-9]{40}$/)
    expect(key_hash).toContain(':')
  })

  it('full_key starts with key_id prefix', async () => {
    const { key_id, full_key } = await generateMcpKey('prod')
    expect(full_key.startsWith(key_id)).toBe(true)
  })

  it('key_hash verifies against the tail', async () => {
    const { full_key, key_id, key_hash } = await generateMcpKey('test')
    const tail = full_key.slice(key_id.length)
    expect(verifyKeyTail(tail, key_hash)).toBe(true)
  })

  it('generates unique keys on each call', async () => {
    const a = await generateMcpKey()
    const b = await generateMcpKey()
    expect(a.full_key).not.toBe(b.full_key)
    expect(a.key_id).not.toBe(b.key_id)
  })
})

// ── validateMcpKey ─────────────────────────────────────────────────────────────

describe('validateMcpKey', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  async function makeValidKey(): Promise<{ key_id: string; full_key: string; key_hash: string }> {
    return generateMcpKey('test')
  }

  it('returns null for missing header', async () => {
    const result = await validateMcpKey(null)
    expect(result).toBeNull()
  })

  it('returns null for undefined header', async () => {
    const result = await validateMcpKey(undefined)
    expect(result).toBeNull()
  })

  it('returns null for malformed header (no Bearer prefix)', async () => {
    const result = await validateMcpKey('Basic abc123')
    expect(result).toBeNull()
  })

  it('returns null for too-short key', async () => {
    const result = await validateMcpKey('Bearer mcp_short')
    expect(result).toBeNull()
  })

  it('returns null when key_id not found in DB', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [], rowCount: 0, command: '', oid: 0, fields: [] })
    const { full_key } = await makeValidKey()
    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).toBeNull()
  })

  it('returns null when tail does not match stored hash (wrong key)', async () => {
    const { key_id, full_key, key_hash } = await makeValidKey()
    mockQuery.mockResolvedValueOnce({
      rows: [{ key_id, key_hash, user_uid: 'uid_123', audience_tier: 'client' }],
      rowCount: 1, command: '', oid: 0, fields: [],
    })
    // Corrupt the tail by replacing the last char
    const corruptKey = full_key.slice(0, -1) + (full_key.endsWith('A') ? 'B' : 'A')
    const result = await validateMcpKey(`Bearer ${corruptKey}`)
    expect(result).toBeNull()
  })

  it('returns principal on valid key', async () => {
    const { key_id, full_key, key_hash } = await makeValidKey()
    mockQuery
      .mockResolvedValueOnce({
        rows: [{ key_id, key_hash, user_uid: 'uid_abc', audience_tier: 'super_admin' }],
        rowCount: 1, command: '', oid: 0, fields: [],
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 1, command: '', oid: 0, fields: [] }) // last_used_at update

    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).not.toBeNull()
    expect(result?.user_uid).toBe('uid_abc')
    expect(result?.audience_tier).toBe('super_admin')
    expect(result?.key_id).toBe(key_id)
  })

  it('returns null when DB throws (never throws to caller)', async () => {
    mockQuery.mockRejectedValueOnce(new Error('DB connection failed'))
    const { full_key } = await makeValidKey()
    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).toBeNull()
  })
})
