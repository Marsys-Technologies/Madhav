import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => mockQuery(...a) }))

const mockRecordError = vi.fn()
vi.mock('@/lib/telemetry/index', () => ({
  telemetry: { recordError: (...a: unknown[]) => mockRecordError(...a) },
}))

import { writeAuditEvent, writeQueryPlan, type AuditEventParams } from '../audit_writer'
import type { QueryPlan } from '@/lib/router/types'

function makeAuditParams(overrides: Partial<AuditEventParams> = {}): AuditEventParams {
  return {
    queryId: 'aaaaaaaa-0000-0000-0000-000000000001',
    queryPlanId: 'bbbbbbbb-0000-0000-0000-000000000002',
    queryText: 'What does my chart say about career?',
    queryClass: 'interpretive',
    userId: 'user-uid-001',
    chartId: 'cccccccc-0000-0000-0000-000000000003',
    conversationId: 'dddddddd-0000-0000-0000-000000000004',
    toolBundles: [
      { tool_name: 'msr_sql', item_count: 12, latency_ms: 45, cached: false },
      { tool_name: 'vector_search', item_count: 8, latency_ms: 120, cached: true },
    ],
    latencyMs: 1250,
    ...overrides,
  }
}

function makeQueryPlan(overrides: Partial<QueryPlan> = {}): QueryPlan {
  return {
    query_plan_id: 'aaaaaaaa-0000-0000-0000-000000000001',
    query_text: 'What sign is my Mercury placed in?',
    query_class: 'factual',
    domains: ['planets'],
    forward_looking: false,
    tools_authorized: ['msr_sql', 'vector_search'],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'fp-test-abc',
    schema_version: '1.0',
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockResolvedValue({ rows: [], rowCount: 1 })
})

// ── writeAuditEvent — happy path ──────────────────────────────────────────────

describe('writeAuditEvent — happy path', () => {
  it('inserts into audit_events with correct columns', async () => {
    await writeAuditEvent(makeAuditParams())

    expect(mockQuery).toHaveBeenCalledOnce()
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(sql).toContain('INSERT INTO audit_events')
    expect(params[0]).toBe('aaaaaaaa-0000-0000-0000-000000000001') // queryId
    expect(params[1]).toBe('bbbbbbbb-0000-0000-0000-000000000002') // queryPlanId
    expect(params[2]).toBe('What does my chart say about career?')  // queryText
    expect(params[3]).toBe('interpretive')                           // queryClass
    expect(params[4]).toBe('user-uid-001')                           // userId
  })

  it('serialises tool_bundles as JSON string', async () => {
    await writeAuditEvent(makeAuditParams())

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    const bundles = JSON.parse(params[7] as string) as { tool_name: string }[]
    expect(bundles).toHaveLength(2)
    expect(bundles[0].tool_name).toBe('msr_sql')
    expect(bundles[1].tool_name).toBe('vector_search')
  })

  it('defaults audit_status to ok when omitted', async () => {
    await writeAuditEvent(makeAuditParams())

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[9]).toBe('ok')
  })

  it('uses provided audit_status when supplied', async () => {
    await writeAuditEvent(makeAuditParams({ auditStatus: 'warn' }))

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[9]).toBe('warn')
  })

  it('sets optional UUIDs to null when omitted', async () => {
    await writeAuditEvent(makeAuditParams({ queryPlanId: undefined, chartId: undefined, conversationId: undefined }))

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    expect(params[1]).toBeNull()
    expect(params[5]).toBeNull()
    expect(params[6]).toBeNull()
  })
})

// ── writeAuditEvent — failure-does-not-throw ─────────────────────────────────

describe('writeAuditEvent — failure isolation', () => {
  it('does not throw when DB query rejects', async () => {
    mockQuery.mockRejectedValueOnce(new Error('connection refused'))
    await expect(writeAuditEvent(makeAuditParams())).resolves.toBeUndefined()
  })

  it('records telemetry error on DB failure', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    await writeAuditEvent(makeAuditParams())

    expect(mockRecordError).toHaveBeenCalledOnce()
    const [component, type] = mockRecordError.mock.calls[0] as [string, string]
    expect(component).toBe('audit_writer')
    expect(type).toBe('write_audit_event_failed')
  })

  it('wraps non-Error throws before recording telemetry', async () => {
    mockQuery.mockRejectedValueOnce('string error')
    await writeAuditEvent(makeAuditParams())

    const [, , err] = mockRecordError.mock.calls[0] as [string, string, Error]
    expect(err).toBeInstanceOf(Error)
  })
})

// ── writeQueryPlan — no-op (query_plans dropped WS-0) ────────────────────────

describe('writeQueryPlan — no-op stub', () => {
  it('resolves without making any DB calls', async () => {
    await expect(writeQueryPlan(makeQueryPlan())).resolves.toBeUndefined()
    expect(mockQuery).not.toHaveBeenCalled()
  })
})
