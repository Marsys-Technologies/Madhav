/**
 * M0 entitlement gate: resolveMcpPrincipalRole unit tests.
 *
 * Tests that the role resolver correctly reads from profiles table
 * and defaults to 'guest' on missing rows or errors.
 *
 * No native chart_id or name appears in this file.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock db/client ─────────────────────────────────────────────────────────────

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
import { resolveMcpPrincipalRole } from '../auth'

const mockQuery = query as ReturnType<typeof vi.fn>

beforeEach(() => {
  mockQuery.mockReset()
})

describe('resolveMcpPrincipalRole', () => {
  it('returns super_admin when profiles row has role=super_admin', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
    const role = await resolveMcpPrincipalRole('uid-admin')
    expect(role).toBe('super_admin')
  })

  it('returns guest when profiles row has role=guest', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    const role = await resolveMcpPrincipalRole('uid-guest')
    expect(role).toBe('guest')
  })

  it('defaults to guest when no profiles row exists', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const role = await resolveMcpPrincipalRole('uid-new-user')
    expect(role).toBe('guest')
  })

  it('defaults to guest on DB error (fail-safe)', async () => {
    mockQuery.mockRejectedValueOnce(new Error('connection refused'))
    const role = await resolveMcpPrincipalRole('uid-error-case')
    expect(role).toBe('guest')
  })

  it('queries profiles table with correct uid', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    await resolveMcpPrincipalRole('uid-test-123')
    expect(mockQuery).toHaveBeenCalledWith(
      expect.stringContaining('profiles'),
      ['uid-test-123']
    )
  })
})
