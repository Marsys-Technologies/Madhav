/**
 * disagreement_writer.test.ts — Unit tests for the disagreement writer module.
 *
 * Tests flagDisagreement() with a mocked DB client.
 *
 * Coverage:
 *   1. flagDisagreement returns a DIS.MCP.* disagreement_id
 *   2. Appended entry uses the correct DB schema (class, description, key_id, etc.)
 *   3. disagreement_id follows DIS.MCP.NNNNNNNN format
 *   4. Uses provided disagreement_id if supplied
 *   5. Re-throws on DB error (caller returns error envelope)
 */

import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'

// ── Mock the DB client before importing the module under test ─────────────────

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
import { flagDisagreement } from '@/lib/mcp/disagreement_writer'

const mockQuery = query as unknown as MockInstance

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeDisagreementEntry(
  overrides: Partial<Parameters<typeof flagDisagreement>[0]> = {}
) {
  return {
    class: 'factual' as const,
    description:
      'SIG.MSR.377 asserts Muntha in Gemini 3H but FORENSIC §22 records Muntha = Libra 7H. ' +
      'Cannot be silently resolved — MSR.377 is load-bearing in predictive synthesis.',
    source_session: 'Cowork_test_2026-05-21',
    proposed_resolution: 'Correct SIG.MSR.377 to Libra 7H per FORENSIC §22.',
    source: {
      key_id: 'mcp_prod_ABCD1234',
      trace_id: 'qry-test-trace-002',
    },
    ...overrides,
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('flagDisagreement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: DB write succeeds
    mockQuery.mockResolvedValue({ rows: [], rowCount: 1 })
  })

  it('returns a disagreement_id with DIS.MCP. prefix', async () => {
    const id = await flagDisagreement(makeDisagreementEntry())
    expect(id).toMatch(/^DIS\.MCP\.[A-Z0-9]{8}$/)
  })

  it('uses the provided disagreement_id if supplied', async () => {
    const provided_id = 'DIS.MCP.TESTXXXX'
    const id = await flagDisagreement(
      makeDisagreementEntry({ disagreement_id: provided_id })
    )
    expect(id).toBe(provided_id)
  })

  it('calls DB INSERT with correct schema fields', async () => {
    const entry = makeDisagreementEntry()
    const id = await flagDisagreement(entry)

    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]

    expect(sql).toContain('INSERT INTO mcp_disagreements')
    // Params: [disagreement_id, logged_at, class, description,
    //          source_session, proposed_resolution, key_id, trace_id]
    expect(params[0]).toBe(id)                          // disagreement_id
    expect(params[2]).toBe('factual')                   // class
    expect(params[4]).toBe('Cowork_test_2026-05-21')    // source_session
    expect(params[6]).toBe('mcp_prod_ABCD1234')         // key_id
    expect(params[7]).toBe('qry-test-trace-002')        // trace_id
  })

  it('includes proposed_resolution in the DB insert', async () => {
    await flagDisagreement(
      makeDisagreementEntry({ proposed_resolution: 'Fix the signal.' })
    )

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[5]).toBe('Fix the signal.')   // proposed_resolution
  })

  it('stores null proposed_resolution when not provided', async () => {
    await flagDisagreement(
      makeDisagreementEntry({ proposed_resolution: undefined })
    )

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[5]).toBeNull()   // proposed_resolution
  })

  it('re-throws DB errors so the dispatcher can return an error envelope', async () => {
    mockQuery.mockRejectedValueOnce(new Error('DB constraint violation'))

    await expect(flagDisagreement(makeDisagreementEntry())).rejects.toThrow(
      'DB constraint violation'
    )
  })
})
