/**
 * ppl_writer.test.ts — Unit tests for the PPL writer module.
 *
 * Tests logPrediction() and recordOutcome() with a mocked DB client.
 * The DB write path is isolated — no real Postgres connections are made.
 *
 * Coverage:
 *   1. logPrediction returns a PPL.MCP.* prediction_id
 *   2. logPrediction calls DB INSERT with correct fields
 *   3. logPrediction truncates prediction_text to 2000 chars
 *   4. recordOutcome with a valid (mocked) prediction_id returns {ok: true}
 *   5. recordOutcome with an unknown prediction_id returns {ok: false}
 *   6. Provenance fields (key_id, trace_id) are present in the logged entry
 *   7. logPrediction handles DB errors gracefully (non-fatal; returns id anyway)
 */

import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'

// ── Mock the DB client before importing the module under test ─────────────────

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'
import { logPrediction, recordOutcome } from '@/lib/mcp/ppl_writer'

const mockQuery = query as unknown as MockInstance

// ── Helpers ───────────────────────────────────────────────────────────────────

function makePredictionEntry(overrides: Partial<Parameters<typeof logPrediction>[0]> = {}) {
  return {
    horizon: '2026-Q3',
    domain: 'career',
    prediction_text: 'Native transitions to a leadership role during Saturn Antardasha',
    confidence: 'medium' as const,
    falsifier: 'No promotion or role change by 2026-09-30',
    source: {
      key_id: 'mcp_prod_ABCD1234',
      trace_id: 'qry-test-trace-001',
      caller_context: 'test session',
    },
    ...overrides,
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('logPrediction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: DB write succeeds
    mockQuery.mockResolvedValue({ rows: [], rowCount: 1 })
  })

  it('returns a prediction_id with PPL.MCP. prefix', async () => {
    const id = await logPrediction(makePredictionEntry())
    expect(id).toMatch(/^PPL\.MCP\.[A-Z0-9]{8}$/)
  })

  it('uses the provided prediction_id if supplied', async () => {
    const provided_id = 'PPL.MCP.TESTXXXX'
    const id = await logPrediction(makePredictionEntry({ prediction_id: provided_id }))
    expect(id).toBe(provided_id)
  })

  it('calls DB INSERT with correct fields including key_id and trace_id', async () => {
    const entry = makePredictionEntry()
    const id = await logPrediction(entry)

    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]

    expect(sql).toContain('INSERT INTO mcp_predictions')
    // Params: [prediction_id, logged_at, horizon, domain, prediction_text,
    //          confidence, falsifier, key_id, trace_id, caller_context]
    expect(params[0]).toBe(id)                              // prediction_id
    expect(params[2]).toBe('2026-Q3')                       // horizon
    expect(params[3]).toBe('career')                        // domain
    expect(params[5]).toBe('medium')                        // confidence
    expect(params[6]).toBe('No promotion or role change by 2026-09-30') // falsifier
    expect(params[7]).toBe('mcp_prod_ABCD1234')             // key_id
    expect(params[8]).toBe('qry-test-trace-001')            // trace_id
  })

  it('truncates prediction_text longer than 2000 chars', async () => {
    const longText = 'x'.repeat(3000)
    await logPrediction(makePredictionEntry({ prediction_text: longText }))

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    const storedText = params[4] as string
    expect(storedText.length).toBe(2000)
  })

  it('handles DB errors gracefully — returns id without throwing', async () => {
    mockQuery.mockRejectedValueOnce(new Error('DB connection refused'))

    const entry = makePredictionEntry()
    // Should not throw despite DB error
    const id = await logPrediction(entry)
    expect(id).toMatch(/^PPL\.MCP\.[A-Z0-9]{8}$/)
  })
})

describe('recordOutcome', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns {ok: true} when the prediction_id is found (UPDATE returns 1 row)', async () => {
    mockQuery.mockResolvedValue({ rows: [{ prediction_id: 'PPL.MCP.TESTXXXX' }], rowCount: 1 })

    const result = await recordOutcome({
      prediction_id: 'PPL.MCP.TESTXXXX',
      outcome_text: 'Native received team lead title in August 2026',
      verified: true,
      notes: null,
      source: { key_id: 'mcp_prod_ABCD1234', trace_id: null },
    })

    expect(result.ok).toBe(true)
  })

  it('returns {ok: false} when the prediction_id is not found (UPDATE returns 0 rows)', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const result = await recordOutcome({
      prediction_id: 'PPL.MCP.NOTFOUND',
      outcome_text: 'Some outcome',
      verified: false,
      notes: null,
      source: { key_id: 'mcp_prod_ABCD1234', trace_id: null },
    })

    expect(result.ok).toBe(false)
  })

  it('calls DB UPDATE with correct fields including provenance', async () => {
    mockQuery.mockResolvedValue({ rows: [{ prediction_id: 'PPL.MCP.TESTXXXX' }], rowCount: 1 })

    await recordOutcome({
      prediction_id: 'PPL.MCP.TESTXXXX',
      outcome_text: 'Outcome text here',
      verified: true,
      notes: 'Some notes',
      source: { key_id: 'mcp_prod_KEY00001', trace_id: 'qry-outcome-trace' },
    })

    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]

    expect(sql).toContain('UPDATE mcp_predictions')
    expect(params[0]).toBe('PPL.MCP.TESTXXXX')      // WHERE prediction_id
    expect(params[1]).toBe('Outcome text here')      // outcome_text
    expect(params[2]).toBe(true)                     // verified
    expect(params[3]).toBe('Some notes')             // notes
    expect(params[5]).toBe('mcp_prod_KEY00001')      // outcome_key_id
    expect(params[6]).toBe('qry-outcome-trace')      // outcome_trace_id
  })

  it('returns {ok: false} on DB error', async () => {
    mockQuery.mockRejectedValueOnce(new Error('DB timeout'))

    const result = await recordOutcome({
      prediction_id: 'PPL.MCP.TESTXXXX',
      outcome_text: 'Outcome',
      verified: true,
      notes: null,
      source: { key_id: 'mcp_prod_ABCD1234', trace_id: null },
    })

    expect(result.ok).toBe(false)
  })
})
