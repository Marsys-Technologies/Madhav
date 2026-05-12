/**
 * trace_assembler.test.ts — Gate II W8 (2026-05-12).
 *
 * Golden-fixture tests: synthetic `query_trace_steps` + `audit_events` rows
 * in → AssembledTrace out. Covers the seven shapes the brief calls out:
 *   1. planner-only
 *   2. planner + retrieval (all 4 named sub-tools from D5, plus extras)
 *   3. planner + retrieval (subset)
 *   4. full pipeline with single-model synthesis
 *   5. full pipeline with panel synthesis (placeholder — emitter does not
 *      yet write panel rows, so the assembler infers single_model)
 *   6. full pipeline with all checkpoints (synthetic)
 *   7. full pipeline with no checkpoints (the production default)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

import { assembleTraceFull } from '@/lib/admin/trace_assembler'
import type { StorageClient } from '@/lib/storage/types'

const QID = '00000000-1234-5678-90ab-cdef00000001'

type Row = Record<string, unknown>

function makeDb(tables: Record<string, Row[]>): StorageClient {
  return {
    query: vi.fn(function (this: unknown, sql: string) {
      const lower = sql.toLowerCase()
      if (lower.includes('from query_trace_steps')) return Promise.resolve({ rows: tables.query_trace_steps ?? [] })
      if (lower.includes('from audit_events')) return Promise.resolve({ rows: tables.audit_events ?? [] })
      if (lower.includes('from synthesis_quality_scorecard')) return Promise.resolve({ rows: tables.synthesis_quality_scorecard ?? [] })
      if (lower.includes('from query_plan_log')) return Promise.resolve({ rows: tables.query_plan_log ?? [] })
      if (lower.includes('from baselines')) return Promise.resolve({ rows: tables.baselines ?? [] })
      return Promise.resolve({ rows: [] })
    }) as never,
  } as unknown as StorageClient
}

function step(
  step_seq: number,
  step_name: string,
  step_type: 'llm' | 'sql' | 'vector' | 'gcs' | 'deterministic',
  opts: Partial<{ status: 'done' | 'error' | 'running' | 'pending'; latency_ms: number; parallel_group: string; data_summary: Row; payload: Row }> = {},
): Row {
  return {
    query_id: QID,
    conversation_id: null,
    step_seq,
    step_name,
    step_type,
    status: opts.status ?? 'done',
    started_at: '2026-05-12T00:00:00.000Z',
    completed_at: '2026-05-12T00:00:00.500Z',
    latency_ms: opts.latency_ms ?? 100,
    parallel_group: opts.parallel_group ?? null,
    data_summary: opts.data_summary ?? {},
    payload: opts.payload ?? {},
  }
}

function plannerStep(): Row {
  return step(1, 'classify', 'llm', {
    latency_ms: 250,
    data_summary: { query_class: 'CHART_ANALYSIS', confidence: 0.92, planning_confidence: 0.92 },
    payload: {
      query_plan: {
        query_class: 'CHART_ANALYSIS',
        router_confidence: 0.92,
        expected_output_shape: 'analytical',
        planning_rationale: 'Selected analytical tools',
        tools_authorized: ['vector_search', 'cgm_graph_walk'],
      },
      tool_calls: [
        { tool_name: 'vector_search', params: {}, priority: 1, reason: 'semantic' },
        { tool_name: 'cgm_graph_walk', params: {}, priority: 2, reason: 'graph' },
      ],
    },
  })
}

function retrievalStep(seq: number, name: string, type: 'sql' | 'vector' | 'gcs' | 'llm' = 'sql'): Row {
  return step(seq, name, type, {
    parallel_group: 'tool_fetch',
    data_summary: { rows_returned: 12, token_estimate: 800 },
    payload: {},
  })
}

function synthStep(seq: number): Row {
  return step(seq, 'synthesis', 'llm', {
    latency_ms: 4200,
    data_summary: {
      model: 'gemini-2.5-pro',
      input_tokens: 12000,
      output_tokens: 1500,
      citation_count: 8,
      temperature: 0.3,
      provider: 'google',
    },
    payload: { prompt_preview: 'You are an acharya…' },
  })
}

function checkpointStep(seq: number, stage: 'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'): Row {
  return step(seq, stage, 'llm', { data_summary: { verdict: 'PASS' } })
}

describe('assembleTraceFull', () => {
  beforeEach(() => vi.clearAllMocks())

  it('1. planner-only: produces planner stage, empty retrieval/synthesis, audit placeholder', async () => {
    const db = makeDb({ query_trace_steps: [plannerStep()] })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.planner).not.toBeNull()
    expect(out.assembled.grouped.planner?.tool_calls).toHaveLength(2)
    expect(out.assembled.grouped.retrieval).toEqual([])
    expect(out.assembled.grouped.synthesis).toBeNull()
    expect(out.assembled.grouped.audit?.placeholder_note).toMatch(/audit_events/i)
    expect(out.assembled.grouped.checkpoints).toHaveLength(3)
    expect(out.assembled.grouped.checkpoints.every(c => !c.ran)).toBe(true)
  })

  it('2. planner + retrieval (all 4 named sub-tools): grouped.retrieval contains 4 rows', async () => {
    const tools = ['vector_search', 'cgm_graph_walk', 'structured_sql', 'hybrid_rank']
    const db = makeDb({
      query_trace_steps: [
        plannerStep(),
        ...tools.map((t, i) => retrievalStep(2 + i, t)),
      ],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.retrieval.map(r => r.tool_name)).toEqual(tools)
    expect(out.assembled.grouped.retrieval.every(r => r.status === 'done')).toBe(true)
  })

  it('3. planner + retrieval (subset): grouped.retrieval reflects what actually fired', async () => {
    const db = makeDb({
      query_trace_steps: [plannerStep(), retrievalStep(2, 'vector_search', 'vector')],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.retrieval).toHaveLength(1)
    expect(out.assembled.grouped.retrieval[0].tool_name).toBe('vector_search')
  })

  it('4. full pipeline with single-model synthesis: synthesis.mode === single_model', async () => {
    const db = makeDb({
      query_trace_steps: [
        plannerStep(),
        retrievalStep(2, 'vector_search', 'vector'),
        synthStep(3),
      ],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.synthesis?.mode).toBe('single_model')
    if (out.assembled.grouped.synthesis?.mode === 'single_model') {
      expect(out.assembled.grouped.synthesis.model).toBe('gemini-2.5-pro')
      expect(out.assembled.grouped.synthesis.citation_count).toBe(8)
    }
  })

  it('5. full pipeline (no panel rows yet): default to single_model per R1', async () => {
    const db = makeDb({
      query_trace_steps: [plannerStep(), retrievalStep(2, 'vector_search', 'vector'), synthStep(3)],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.synthesis?.mode).toBe('single_model')
  })

  it('6. full pipeline with all checkpoints: ran=true on all three', async () => {
    const db = makeDb({
      query_trace_steps: [
        plannerStep(),
        retrievalStep(2, 'vector_search', 'vector'),
        synthStep(3),
        checkpointStep(4, 'checkpoint_4_5'),
        checkpointStep(5, 'checkpoint_5_5'),
        checkpointStep(6, 'checkpoint_8_5'),
      ],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.checkpoints.every(c => c.ran)).toBe(true)
  })

  it('7. full pipeline with no checkpoints: all three render as skipped (production default)', async () => {
    const db = makeDb({
      query_trace_steps: [plannerStep(), retrievalStep(2, 'vector_search', 'vector'), synthStep(3)],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.checkpoints.map(c => c.ran)).toEqual([false, false, false])
    expect(out.assembled.grouped.checkpoints.map(c => c.verdict)).toEqual(['SKIPPED', 'SKIPPED', 'SKIPPED'])
  })

  it('audit_events JOIN populates AuditStepMetadata when present', async () => {
    const db = makeDb({
      query_trace_steps: [plannerStep(), synthStep(2)],
      audit_events: [
        {
          audit_event_id: 'ae-1',
          audit_event_version: 1,
          disclosure_tier: 'super_admin',
          validator_verdict: 'PASS',
          b10_compliant: true,
          b11_compliant: true,
        },
      ],
    })
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.grouped.audit?.audit_event_id).toBe('ae-1')
    expect(out.assembled.grouped.audit?.validator_verdict).toBe('PASS')
    expect(out.assembled.grouped.audit?.b10_compliant).toBe(true)
    expect(out.assembled.grouped.audit?.placeholder_note).toBeNull()
  })

  it('legacy projection: classify is always null, context_assembly is always null', async () => {
    const db = makeDb({ query_trace_steps: [plannerStep(), synthStep(2)] })
    const out = await assembleTraceFull(QID, db)
    expect(out.legacy.classify).toBeNull()
    expect(out.legacy.context_assembly).toBeNull()
    expect(out.legacy.plan).not.toBeNull()
    expect(out.legacy.synthesis?.model).toBe('gemini-2.5-pro')
  })

  it('empty DB → partial=true, all stages null/empty', async () => {
    const db = makeDb({})
    const out = await assembleTraceFull(QID, db)
    expect(out.assembled.partial).toBe(true)
    expect(out.assembled.steps).toEqual([])
    expect(out.assembled.grouped.planner).toBeNull()
    expect(out.assembled.grouped.synthesis).toBeNull()
  })
})
