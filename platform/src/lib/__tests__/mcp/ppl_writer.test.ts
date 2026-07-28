/**
 * ppl_writer.test.ts — retired-no-op tests.
 *
 * ppl_writer.ts was RETIRED by PB-3 (SAMĪKṢĀ) lane L-1 (MEMO_PB-3_0): the `mcp_predictions`
 * table it wrote was dropped by migration 471, and its write path was neutered to inert
 * no-ops. These tests assert the retirement contract:
 *   - logPrediction returns a signature-compatible PPL.MCP.* id but does NO DB write.
 *   - recordOutcome always returns { ok: false } and does NO DB write.
 *   - NEITHER function imports/uses the DB client (the whole point of the retirement).
 *
 * The DB client is mocked to a throwing spy: if either function tried to write, the test
 * would see the spy invoked (and could fail). This is what makes the "no DB write" assertion
 * real rather than vacuous — it can distinguish a retired no-op from a live writer.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// The DB client is mocked to a spy. ppl_writer.ts no longer imports it at all (that IS the
// retirement) — so this spy must remain uncalled. Asserting `not.toHaveBeenCalled()` is what
// makes "no DB write" falsifiable: a regression that re-added a live write would trip it.
const queryMock = vi.fn().mockResolvedValue({ rows: [], rowCount: 0 })
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { logPrediction, recordOutcome } from '@/lib/mcp/ppl_writer'

const mockQuery = queryMock

function makePredictionEntry(overrides: Partial<Parameters<typeof logPrediction>[0]> = {}) {
  return {
    horizon: '2026-Q3',
    domain: 'career',
    prediction_text: 'Native transitions to a leadership role during Saturn Antardasha',
    confidence: 'medium' as const,
    falsifier: 'No promotion or role change by 2026-09-30',
    source: { key_id: 'mcp_prod_ABCD1234', trace_id: 'qry-test-trace-001', caller_context: 'test' },
    ...overrides,
  }
}

describe('logPrediction (RETIRED)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
  })

  it('returns a signature-compatible PPL.MCP. id', async () => {
    const id = await logPrediction(makePredictionEntry())
    expect(id).toMatch(/^PPL\.MCP\.[A-Z0-9]{8}$/)
  })

  it('uses the provided prediction_id if supplied', async () => {
    const id = await logPrediction(makePredictionEntry({ prediction_id: 'PPL.MCP.TESTXXXX' }))
    expect(id).toBe('PPL.MCP.TESTXXXX')
  })

  it('performs NO database write (mcp_predictions is dropped)', async () => {
    await logPrediction(makePredictionEntry())
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('recordOutcome (RETIRED)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
  })

  it('always returns { ok: false } (no table to update)', async () => {
    const result = await recordOutcome({
      prediction_id: 'PPL.MCP.TESTXXXX',
      outcome_text: 'Native received team lead title in August 2026',
      verified: true,
      notes: null,
      source: { key_id: 'mcp_prod_ABCD1234', trace_id: null },
    })
    expect(result.ok).toBe(false)
  })

  it('performs NO database write', async () => {
    await recordOutcome({
      prediction_id: 'PPL.MCP.TESTXXXX',
      outcome_text: 'Outcome',
      verified: true,
      notes: null,
      source: { key_id: 'mcp_prod_ABCD1234', trace_id: null },
    })
    expect(mockQuery).not.toHaveBeenCalled()
  })
})
