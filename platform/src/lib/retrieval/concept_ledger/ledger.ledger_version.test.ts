/**
 * ledger.ledger_version.test.ts — W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4, W-26).
 *
 * Verifies getLedgerVersion() against a mocked DB client:
 *   - empty ledger → honest null (never a fabricated version — B.10).
 *   - a real "bump" (row count or updated_at moves forward) produces a DIFFERENT
 *     ledger_version string, mirroring the same fixture-bump discipline the brief
 *     asks for on build_id (session_pin.test.ts's detectBuildDrift tests).
 *   - the SAME underlying DB row state produces the IDENTICAL ledger_version on a
 *     second call — the cache-safety property this field exists to carry.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getLedgerVersion } from './ledger'

function mockLedgerState(count: number, maxUpdatedAtEpochSeconds: number | null) {
  mockQuery.mockResolvedValueOnce({
    rows: [
      {
        ledger_version:
          count === 0 ? null : `${count}:${maxUpdatedAtEpochSeconds}`,
      },
    ],
  })
}

describe('getLedgerVersion (W3-L8, W-26)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('returns null when concept_ledger is empty (honest null, never fabricated — B.10)', async () => {
    mockLedgerState(0, null)
    const version = await getLedgerVersion()
    expect(version).toBeNull()
  })

  it('returns a real version string when the ledger has rows', async () => {
    mockLedgerState(3, 1_800_000_000)
    const version = await getLedgerVersion()
    expect(version).toBe('3:1800000000')
  })

  it('the SAME underlying ledger state produces the IDENTICAL version on repeated calls (cache-safety)', async () => {
    mockLedgerState(3, 1_800_000_000)
    const first = await getLedgerVersion()
    mockLedgerState(3, 1_800_000_000)
    const second = await getLedgerVersion()
    expect(first).toBe(second)
    expect(first).not.toBeNull()
  })

  it('a real bump (a row updated -> max(updated_at) advances) produces a DIFFERENT version', async () => {
    mockLedgerState(3, 1_800_000_000)
    const before = await getLedgerVersion()

    // Simulate the harvest pipeline / an adjudication updating one row's lifecycle_state —
    // count unchanged, updated_at advances.
    mockLedgerState(3, 1_800_000_500)
    const after = await getLedgerVersion()

    expect(before).not.toBe(after)
  })

  it('a new concept being added (count bump) also produces a DIFFERENT version', async () => {
    mockLedgerState(3, 1_800_000_000)
    const before = await getLedgerVersion()

    mockLedgerState(4, 1_800_000_600)
    const after = await getLedgerVersion()

    expect(before).not.toBe(after)
  })
})
