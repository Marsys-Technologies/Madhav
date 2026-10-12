/**
 * M0 entitlement gate: resolveMcpPrincipalRole unit tests.
 *
 * Tests that the role resolver correctly reads from profiles table
 * and refuses ('inactive') any principal whose profile is not active: disabled,
 * pending, missing row or lookup error (fail closed).
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
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'super_admin', status: 'active' }] })
    const role = await resolveMcpPrincipalRole('uid-admin')
    expect(role).toBe('super_admin')
  })

  it('returns guest when profiles row has role=guest', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest', status: 'active' }] })
    const role = await resolveMcpPrincipalRole('uid-guest')
    expect(role).toBe('guest')
  })

  it('is inactive when no profiles row exists (fail closed)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const role = await resolveMcpPrincipalRole('uid-new-user')
    expect(role).toBe('inactive')
  })

  it('is inactive on DB error (fail closed)', async () => {
    mockQuery.mockRejectedValueOnce(new Error('connection refused'))
    const role = await resolveMcpPrincipalRole('uid-error-case')
    expect(role).toBe('inactive')
  })

  it.each(['disabled', 'pending'])('is inactive when the profile status is %s, whatever the role', async (status) => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'super_admin', status }] })
    expect(await resolveMcpPrincipalRole('uid-not-active')).toBe('inactive')
  })

  it('queries profiles table with correct uid', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest', status: 'active' }] })
    await resolveMcpPrincipalRole('uid-test-123')
    expect(mockQuery).toHaveBeenCalledWith(
      expect.stringContaining('profiles'),
      ['uid-test-123']
    )
  })
})
