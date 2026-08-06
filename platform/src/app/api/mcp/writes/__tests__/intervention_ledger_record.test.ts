/**
 * intervention_ledger_record.test.ts — POST /api/mcp/writes/intervention_ledger_record.
 *
 * ṢAḌ-DARŚANA W4 gate-discharge prep: the serve-time write path into
 * `mimamsa_intervention_ledger` (KALA_W4_UPAYA_DESIGN §4.1 ruling S-1 / migration 532's
 * "FILED live, at serve time, through the sanctioned HTTP action" — the gap PR #1055's
 * harness lane disclosed).
 *
 * Coverage:
 *   1. Requires write (all) authz — denied for a view-only principal with the DISTINCT
 *      entitlement_denied envelope.
 *   2. Validation: chart_id required; the caller-suppliable NOT NULL entry fields required.
 *   3. Happy path: calls recordInterventionLedgerEntry with filed_by STAMPED from the
 *      resolved principal (x-mcp-user) — never trusted from the caller body.
 *   4. Idempotent re-record (created:false) passes through.
 *   5. A writer/DB error (CHECK/FK violation) surfaces the verbatim message with 400 —
 *      never a fabricated success.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/mcp/rate_limiter', () => ({
  checkRateLimit: vi.fn().mockResolvedValue({ allowed: true }),
  buildRateLimitErrorEnvelope: vi.fn(() => ({ error: 'rate_limit' })),
}))

const mockRecordEntry = vi.fn()
vi.mock('@/lib/mcp/intervention_ledger_writer', () => ({
  recordInterventionLedgerEntry: mockRecordEntry,
}))

const mockAuthorize = vi.fn()
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/mcp/auth', () => ({ resolveMcpPrincipalRole: vi.fn().mockResolvedValue('guest') }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function makeReq(body: object): Request {
  return new Request('http://localhost/api/mcp/writes/intervention_ledger_record', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'owner-uid',
      'x-mcp-audience-tier': 'super_admin',
      'x-mcp-key-id': 'mcp_test_KEY001',
    },
    body: JSON.stringify(body),
  })
}

const PARAMS = { params: Promise.resolve({ action: 'intervention_ledger_record' }) }

const VALID_ENTRY = {
  intent: 'Adopt the Shani propitiation targeting the confirmation block.',
  intervention_class: 'upaya',
  rite_or_activity_class: 'phala_mitigation:pm-1',
  event_class: 'career_promotion',
  window_start: '2026-09-01T00:00:00Z',
  window_end: '2027-01-01T00:00:00Z',
  precision_regime: 'day_grade',
  precision_basis: 'caller-stated adoption window',
  adjudication_record: { kind: 'upaya_adoption' },
  score_vector: { factors_present: [] },
  efficacy_tier: 'classically_attested',
  source_citation: 'BPHS 27.4',
  paddhati_version: 'none_applied_upaya_adoption',
  predicted_differential: 'adopted upāya window vs no-intervention baseline',
  prediction_id: 'e0a1a1a1-0000-4000-8000-000000000001',
  adoption_basis: 'native_directed',
  authority_basis: 'pact_query:denied_at_confirmation',
  engine_version: 'upaya_setu_v1',
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  mockAuthorize.mockResolvedValue('all')
  mockRecordEntry.mockResolvedValue({ intervention_id: 'iv-uuid-1', created: true })
})

async function post(body: object) {
  const { POST } = await import('../[action]/route')
  return POST(makeReq(body), PARAMS)
}

describe('POST /api/mcp/writes/intervention_ledger_record — authz', () => {
  it('denies a view-only principal (perm !== all) with 401 and the DISTINCT entitlement_denied envelope', async () => {
    mockAuthorize.mockResolvedValue('view')
    const res = await post({ chart_id: CHART, entry: VALID_ENTRY })
    expect(res.status).toBe(401)
    const json = await res.json()
    expect(json.ok).toBe(false)
    expect(JSON.stringify(json)).toContain('entitlement')
    expect(mockRecordEntry).not.toHaveBeenCalled()
  })

  it('denies a deny principal with 401', async () => {
    mockAuthorize.mockResolvedValue('deny')
    const res = await post({ chart_id: CHART, entry: VALID_ENTRY })
    expect(res.status).toBe(401)
    expect(mockRecordEntry).not.toHaveBeenCalled()
  })
})

describe('POST /api/mcp/writes/intervention_ledger_record — validation', () => {
  it('requires chart_id (400 when absent)', async () => {
    const res = await post({ entry: VALID_ENTRY })
    expect(res.status).toBe(400)
    expect(mockRecordEntry).not.toHaveBeenCalled()
  })

  it('requires body.entry (400 when absent)', async () => {
    const res = await post({ chart_id: CHART })
    expect(res.status).toBe(400)
    expect(mockRecordEntry).not.toHaveBeenCalled()
  })

  it('rejects an entry missing a caller-suppliable NOT NULL field (e.g. predicted_differential) with 400 naming the requirement', async () => {
    const rest: Record<string, unknown> = { ...VALID_ENTRY }
    delete rest.predicted_differential
    const res = await post({ chart_id: CHART, entry: rest })
    expect(res.status).toBe(400)
    const json = await res.json()
    expect(JSON.stringify(json)).toContain('predicted_differential')
    expect(mockRecordEntry).not.toHaveBeenCalled()
  })
})

describe('POST /api/mcp/writes/intervention_ledger_record — happy path', () => {
  it('records and returns { intervention_id, created } with filed_by STAMPED from x-mcp-user, never the body', async () => {
    const res = await post({
      chart_id: CHART,
      entry: { ...VALID_ENTRY, filed_by: 'spoofed-caller-value' },
    })
    expect(res.status).toBe(200)
    const json = await res.json()
    expect(json.ok).toBe(true)
    expect(json.result.intervention_id).toBe('iv-uuid-1')
    expect(json.result.created).toBe(true)
    expect(mockRecordEntry).toHaveBeenCalledTimes(1)
    const input = mockRecordEntry.mock.calls[0][0]
    expect(input.chart_id).toBe(CHART)
    expect(input.filed_by).toBe('owner-uid') // stamped from the resolved principal
    expect(input.filed_by).not.toBe('spoofed-caller-value')
    expect(input.window_start).toBe(VALID_ENTRY.window_start)
    expect(input.prediction_id).toBe(VALID_ENTRY.prediction_id)
  })

  it('idempotent re-record passes created:false through unchanged', async () => {
    mockRecordEntry.mockResolvedValue({ intervention_id: 'iv-existing', created: false })
    const res = await post({ chart_id: CHART, entry: VALID_ENTRY })
    expect(res.status).toBe(200)
    const json = await res.json()
    expect(json.result.intervention_id).toBe('iv-existing')
    expect(json.result.created).toBe(false)
  })

  it('a writer/DB error (CHECK or FK violation) surfaces the VERBATIM message with 400 — never fabricated success', async () => {
    mockRecordEntry.mockRejectedValue(
      new Error('insert or update on table "mimamsa_intervention_ledger" violates foreign key constraint "mimamsa_intervention_ledger_prediction_id_fkey"')
    )
    const res = await post({ chart_id: CHART, entry: VALID_ENTRY })
    expect(res.status).toBe(400)
    const json = await res.json()
    expect(json.ok).toBe(false)
    expect(JSON.stringify(json)).toContain('mimamsa_intervention_ledger_prediction_id_fkey')
  })
})
