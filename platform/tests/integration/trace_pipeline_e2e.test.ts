/**
 * trace_pipeline_e2e.test.ts — Gate II W8 / AC.11 (2026-05-12).
 *
 * Synthetic end-to-end fixture test. Replaces the v1.0 manual smoke test:
 * stub pipeline emitters write canned `query_trace_steps` rows; the test
 * invokes the assembler; asserts the returned AssembledTrace matches the
 * schema; writes the result to `platform/tests/fixtures/gate_ii_smoke_trace.json`
 * for the §12 native review.
 */

import { describe, it, expect, vi } from 'vitest'
import { writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'

vi.mock('server-only', () => ({}))

import { assembleTraceFull } from '@/lib/admin/trace_assembler'
import type { StorageClient } from '@/lib/storage/types'

const QID = '11111111-2222-3333-4444-555555555555'

type Row = Record<string, unknown>

function makeStubDb(tables: Record<string, Row[]>): StorageClient {
  return {
    query: vi.fn(function (this: unknown, sql: string) {
      const lower = sql.toLowerCase()
      if (lower.includes('from query_trace_steps')) return Promise.resolve({ rows: tables.query_trace_steps ?? [] })
      if (lower.includes('from audit_events')) return Promise.resolve({ rows: tables.audit_events ?? [] })
      if (lower.includes('from synthesis_quality_scorecard')) return Promise.resolve({ rows: tables.synthesis_quality_scorecard ?? [] })
      if (lower.includes('from query_plan_log')) return Promise.resolve({ rows: tables.query_plan_log ?? [] })
      return Promise.resolve({ rows: [] })
    }) as never,
  } as unknown as StorageClient
}

describe('Gate II — synthetic end-to-end trace assembly', () => {
  it('canned pipeline emit → AssembledTrace matches the schema; fixture JSON saved', async () => {
    const stepRows: Row[] = [
      {
        query_id: QID, conversation_id: null, step_seq: 1,
        step_name: 'classify', step_type: 'llm', status: 'done',
        started_at: '2026-05-12T00:00:00.000Z',
        completed_at: '2026-05-12T00:00:00.250Z',
        latency_ms: 250, parallel_group: null,
        data_summary: { query_class: 'CHART_ANALYSIS', confidence: 0.92, planning_confidence: 0.92 },
        payload: {
          query_plan: {
            query_class: 'CHART_ANALYSIS',
            router_confidence: 0.92,
            expected_output_shape: 'analytical',
            planning_rationale: 'Selected analytical tools for forensic chart query',
            tools_authorized: ['vector_search', 'cgm_graph_walk', 'chart_facts_query'],
          },
          tool_calls: [
            { tool_name: 'vector_search', params: { q: 'forensic' }, priority: 1, reason: 'semantic' },
            { tool_name: 'cgm_graph_walk', params: {}, priority: 2, reason: 'graph' },
            { tool_name: 'chart_facts_query', params: {}, priority: 3, reason: 'facts' },
          ],
        },
      },
      {
        query_id: QID, conversation_id: null, step_seq: 2,
        step_name: 'compose_bundle', step_type: 'deterministic', status: 'done',
        started_at: '2026-05-12T00:00:00.250Z',
        completed_at: '2026-05-12T00:00:00.300Z',
        latency_ms: 50, parallel_group: null,
        data_summary: { result: '3 assets · 3 tools' },
        payload: {},
      },
      {
        query_id: QID, conversation_id: null, step_seq: 3,
        step_name: 'vector_search', step_type: 'vector', status: 'done',
        started_at: '2026-05-12T00:00:00.300Z',
        completed_at: '2026-05-12T00:00:00.700Z',
        latency_ms: 400, parallel_group: 'tool_fetch',
        data_summary: { rows_returned: 20, token_estimate: 1800, top_score: 0.87, tool_name: 'vector_search' },
        payload: {},
      },
      {
        query_id: QID, conversation_id: null, step_seq: 4,
        step_name: 'cgm_graph_walk', step_type: 'sql', status: 'done',
        started_at: '2026-05-12T00:00:00.300Z',
        completed_at: '2026-05-12T00:00:00.500Z',
        latency_ms: 200, parallel_group: 'tool_fetch',
        data_summary: { rows_returned: 5, token_estimate: 600 },
        payload: {},
      },
      {
        query_id: QID, conversation_id: null, step_seq: 5,
        step_name: 'chart_facts_query', step_type: 'sql', status: 'done',
        started_at: '2026-05-12T00:00:00.300Z',
        completed_at: '2026-05-12T00:00:00.450Z',
        latency_ms: 150, parallel_group: 'tool_fetch',
        data_summary: { rows_returned: 18, token_estimate: 1200 },
        payload: {},
      },
      {
        query_id: QID, conversation_id: null, step_seq: 6,
        step_name: 'synthesis', step_type: 'llm', status: 'done',
        started_at: '2026-05-12T00:00:00.700Z',
        completed_at: '2026-05-12T00:00:04.900Z',
        latency_ms: 4200, parallel_group: null,
        data_summary: {
          model: 'gemini-2.5-pro',
          input_tokens: 14000,
          output_tokens: 1800,
          citation_count: 11,
          temperature: 0.3,
          provider: 'google',
          output_shape_compliant: true,
          reasoning_path: false,
        },
        payload: { prompt_preview: 'You are an acharya …' },
      },
    ]

    const auditRow: Row = {
      audit_event_id: 'ae-gate2-smoke',
      audit_event_version: 1,
      disclosure_tier: 'super_admin',
      audit_status: 'ok',
      b10_compliant: true,
      b11_compliant: true,
    }

    const db = makeStubDb({
      query_trace_steps: stepRows,
      audit_events: [auditRow],
      query_plan_log: [{ query_text: 'Forensic chart analysis test' }],
    })

    const out = await assembleTraceFull(QID, db)

    // Schema-shape assertions
    expect(out.assembled.query_id).toBe(QID)
    expect(out.assembled.query_text).toBe('Forensic chart analysis test')
    expect(out.assembled.grouped.planner).not.toBeNull()
    expect(out.assembled.grouped.planner?.tool_calls).toHaveLength(3)
    expect(out.assembled.grouped.retrieval.map(r => r.tool_name)).toEqual([
      'vector_search', 'cgm_graph_walk', 'chart_facts_query',
    ])
    expect(out.assembled.grouped.synthesis?.mode).toBe('single_model')
    if (out.assembled.grouped.synthesis?.mode === 'single_model') {
      expect(out.assembled.grouped.synthesis.model).toBe('gemini-2.5-pro')
      expect(out.assembled.grouped.synthesis.citation_count).toBe(11)
    }
    expect(out.assembled.grouped.audit?.audit_event_id).toBe('ae-gate2-smoke')
    expect(out.assembled.grouped.audit?.validator_verdict).toBe('PASS')
    expect(out.assembled.grouped.checkpoints).toHaveLength(3)
    expect(out.assembled.grouped.checkpoints.every(c => !c.ran)).toBe(true)
    expect(out.assembled.partial).toBe(false)

    // Persist the assembled trace JSON for native §12 review.
    const fixturePath = join(__dirname, '..', 'fixtures', 'gate_ii_smoke_trace.json')
    mkdirSync(dirname(fixturePath), { recursive: true })
    writeFileSync(fixturePath, JSON.stringify(out.assembled, null, 2))
  })
})
