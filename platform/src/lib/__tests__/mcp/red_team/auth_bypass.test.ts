/**
 * auth_bypass.test.ts — Red-team: RT-01 + RT-02
 *
 * RT-01: Auth bypass — invalid key returns null / endpoint returns 401.
 * RT-02: Revoked key rejection — SQL WHERE clause includes revoked_at IS NULL.
 *
 * MCP-4-S2 red-team session.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { hashKeyTail, verifyKeyTail, generateMcpKey, validateMcpKey } from '@/lib/mcp/auth'

// Mock the DB client
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
const mockQuery = vi.mocked(query)

// ── RT-01: Auth bypass — invalid key ─────────────────────────────────────────

describe('RT-01 — Auth bypass: invalid key', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('RT-01a: null header returns null (not a principal)', async () => {
    const result = await validateMcpKey(null)
    expect(result).toBeNull()
  })

  it('RT-01b: empty string header returns null', async () => {
    const result = await validateMcpKey('')
    expect(result).toBeNull()
  })

  it('RT-01c: Bearer with garbage key returns null', async () => {
    // DB won't even be called for a malformed key (splitKey returns null)
    const result = await validateMcpKey('Bearer invalid_key_here')
    expect(result).toBeNull()
    // DB should NOT be called — short-circuits at splitKey
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('RT-01d: Bearer with valid format but non-existent key_id returns null', async () => {
    const { full_key } = await generateMcpKey('test')
    // Simulate DB returning no rows (key_id not found)
    mockQuery.mockResolvedValueOnce({ rows: [], rowCount: 0, command: '', oid: 0, fields: [] })
    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).toBeNull()
  })

  it('RT-01e: Bearer with correct key_id but wrong tail returns null', async () => {
    const { key_id, full_key, key_hash } = await generateMcpKey('test')
    // DB returns a valid row
    mockQuery.mockResolvedValueOnce({
      rows: [{ key_id, key_hash, user_uid: 'uid_attacker', audience_tier: 'super_admin' }],
      rowCount: 1, command: '', oid: 0, fields: [],
    })
    // Corrupt the key tail — different from what was hashed
    const corruptKey = full_key.slice(0, -1) + (full_key.endsWith('Z') ? 'A' : 'Z')
    const result = await validateMcpKey(`Bearer ${corruptKey}`)
    expect(result).toBeNull()
  })

  it('RT-01f: No "Bearer" prefix — rejected before DB lookup', async () => {
    const { full_key } = await generateMcpKey('test')
    // Pass key without "Bearer" prefix
    const result = await validateMcpKey(full_key)
    expect(result).toBeNull()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('RT-01g: valid key returns McpPrincipal with correct fields', async () => {
    const { key_id, full_key, key_hash } = await generateMcpKey('test')
    mockQuery
      .mockResolvedValueOnce({
        rows: [{ key_id, key_hash, user_uid: 'uid_native', audience_tier: 'super_admin' }],
        rowCount: 1, command: '', oid: 0, fields: [],
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 1, command: '', oid: 0, fields: [] }) // last_used_at
    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).not.toBeNull()
    expect(result?.user_uid).toBe('uid_native')
    expect(result?.audience_tier).toBe('super_admin')
    expect(result?.key_id).toBe(key_id)
  })
})

// ── RT-02: Revoked key rejection ──────────────────────────────────────────────

describe('RT-02 — Revoked key: SQL WHERE clause enforces revoked_at IS NULL', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * The SQL in auth.ts line 98-100:
   *
   *   WHERE key_id = $1 AND revoked_at IS NULL
   *
   * This test verifies the SQL string contains the revocation guard.
   * We capture the query call and inspect the SQL string.
   */
  it('RT-02a: DB query includes revoked_at IS NULL guard', async () => {
    const { full_key } = await generateMcpKey('test')
    // Return empty rows so auth fails gracefully (we only care about the SQL)
    mockQuery.mockResolvedValueOnce({ rows: [], rowCount: 0, command: '', oid: 0, fields: [] })

    await validateMcpKey(`Bearer ${full_key}`)

    // Inspect the SQL that was sent to the DB
    expect(mockQuery).toHaveBeenCalledWith(
      expect.stringContaining('revoked_at IS NULL'),
      expect.any(Array)
    )
  })

  it('RT-02b: revoked key (row missing from NOT NULL query) returns null', async () => {
    // When revoked_at IS NOT NULL, the WHERE clause excludes the row.
    // Simulate this by returning empty rows (same effect as if the row was filtered out).
    const { full_key } = await generateMcpKey('test')
    mockQuery.mockResolvedValueOnce({ rows: [], rowCount: 0, command: '', oid: 0, fields: [] })
    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).toBeNull()
  })

  it('RT-02c: non-revoked key (revoked_at IS NULL) returns principal', async () => {
    const { key_id, full_key, key_hash } = await generateMcpKey('test')
    // Simulate non-revoked row returned by query (revoked_at IS NULL matches)
    mockQuery
      .mockResolvedValueOnce({
        rows: [{ key_id, key_hash, user_uid: 'uid_active', audience_tier: 'client' }],
        rowCount: 1, command: '', oid: 0, fields: [],
      })
      .mockResolvedValueOnce({ rows: [], rowCount: 1, command: '', oid: 0, fields: [] })
    const result = await validateMcpKey(`Bearer ${full_key}`)
    expect(result).not.toBeNull()
    expect(result?.user_uid).toBe('uid_active')
  })
})

// ── PBKDF2 timing-safe comparison ────────────────────────────────────────────

describe('Timing-safe comparison (supporting evidence for RT-01)', () => {
  it('hashKeyTail produces salt:hash format', () => {
    const hash = hashKeyTail('ABCDEFGHIJKLMNOPQRSTUVWXYZ012345')
    expect(hash).toMatch(/^[0-9a-f]+:[0-9a-f]+$/)
  })

  it('verifyKeyTail is correct for matching tail', () => {
    const tail = 'ZYXWVUTSRQPONMLKJIHGFEDCBA543210'
    const hash = hashKeyTail(tail)
    expect(verifyKeyTail(tail, hash)).toBe(true)
  })

  it('verifyKeyTail returns false for wrong tail', () => {
    const tail = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0'
    const hash = hashKeyTail(tail)
    expect(verifyKeyTail('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1', hash)).toBe(false)
  })

  it('verifyKeyTail returns false for empty/malformed stored hash', () => {
    expect(verifyKeyTail('sometail', '')).toBe(false)
    expect(verifyKeyTail('sometail', 'nocolon')).toBe(false)
  })
})
