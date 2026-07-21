import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => mockQuery(...a) }))

const mockRecordError = vi.fn()
vi.mock('@/lib/telemetry/index', () => ({
  telemetry: { recordError: (...a: unknown[]) => mockRecordError(...a) },
}))

import {
  writeConsumePerformanceRow,
  writeEvalRun,
  writeEvalPerformanceRow,
  finalizeEvalRun,
  type ConsumePerformanceInput,
  type EvalPerformanceRow,
} from '../ingestion'
import type { QueryPlan } from '@/lib/router/types'

function makePlan(overrides: Partial<QueryPlan> = {}): QueryPlan {
  return {
    query_plan_id: 'pp-1',
    query_text: 'Will my career take off?',
    query_class: 'interpretive',
    domains: ['career'],
    forward_looking: false,
    tools_authorized: ['msr_sql', 'vector_search'],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'sha:abc',
    schema_version: '1.0',
    router_confidence: 0.82,
    ...overrides,
  }
}

function makeInput(overrides: Partial<ConsumePerformanceInput> = {}): ConsumePerformanceInput {
  return {
    query_id: 'q-1',
    query_plan: makePlan(),
    tool_results: [
      {
        tool_bundle_id: 'tb-1',
        tool_name: 'msr_sql',
        tool_version: '1.0',
        invocation_params: {},
        results: [{ content: 'x', significance: 0.9 }],
        served_from_cache: false,
        latency_ms: 120,
        result_hash: 'sha256:a',
        schema_version: '1.0',
      },
      {
        tool_bundle_id: 'tb-2',
        tool_name: 'vector_search',
        tool_version: '1.0',
        invocation_params: {},
        results: [{ content: 'y', significance: 0.7 }],
        served_from_cache: false,
        latency_ms: 80,
        result_hash: 'sha256:b',
        schema_version: '1.0',
      },
    ],
    validator_results: [
      { validator_id: 'v1', validator_version: '1.0', vote: 'pass', reason: 'ok' },
    ],
    disclosure_tier: 'super_admin',
    synthesis_event: {
      event_type: 'synthesis_complete',
      query_plan_id: 'pp-1',
      bundle_id: 'b-1',
      synthesis_prompt_version: 'v1',
      synthesizer_model_id: 'gemini-2.5-pro',
      finish_reason: 'stop',
      validator_votes: {},
      started_at: '2026-05-12T10:00:00.000Z',
      finished_at: '2026-05-12T10:00:03.000Z',
      input_tokens: 1000,
      output_tokens: 200,
      final_output:
        'Jupiter activates the 10th house (→ FORENSIC: Jupiter natal). Confidence is moderate.',
    },
    ...overrides,
  }
}

beforeEach(() => {
  mockQuery.mockReset()
  mockRecordError.mockReset()
})

describe('writeConsumePerformanceRow', () => {
  it('happy path: looks up audit_event_id then inserts a row', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ id: 'ae-1' }] }) // SELECT id FROM audit_log
      .mockResolvedValueOnce({ rows: [] }) // INSERT
    await writeConsumePerformanceRow(makeInput())
    expect(mockQuery).toHaveBeenCalledTimes(2)
    const insertCall = mockQuery.mock.calls[1]
    expect(insertCall[0]).toMatch(/INSERT INTO performance_queries/)
    expect(insertCall[1]?.[0]).toBe('ae-1')
  })

  it('swallows DB errors without throwing (consume path is non-blocking)', async () => {
    // First call (SELECT id FROM audit_log) succeeds; second call (INSERT) throws.
    mockQuery
      .mockResolvedValueOnce({ rows: [{ id: 'ae-1' }] })
      .mockRejectedValueOnce(new Error('db down'))
    await expect(writeConsumePerformanceRow(makeInput())).resolves.toBeUndefined()
    expect(mockRecordError).toHaveBeenCalled()
  })

  it('sets is_prediction=true and prediction_outcome_state=pending for predictive class', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [] })
    await writeConsumePerformanceRow(
      makeInput({ query_plan: makePlan({ query_class: 'predictive' }) })
    )
    const params = mockQuery.mock.calls[1][1] as unknown[]
    // is_prediction is param $20; prediction_outcome_state is param $21
    expect(params[19]).toBe(true)
    expect(params[20]).toBe('pending')
  })

  it('derives synthesis_status="success" when finish_reason=stop', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [] })
    await writeConsumePerformanceRow(makeInput())
    const params = mockQuery.mock.calls[1][1] as unknown[]
    // synthesis_status is param $13
    expect(params[12]).toBe('success')
  })

  // PERF-S1 fix (b): per-tool score map
  it('populates retrieval_scores as JSON object for tools with scores (PERF-S1 fix b)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [] })
    await writeConsumePerformanceRow(makeInput())
    const params = mockQuery.mock.calls[1][1] as unknown[]
    // retrieval_scores is param $22 (index 21)
    const scores = JSON.parse(params[21] as string) as Record<string, number>
    // msr_sql has significance 0.9; vector_search has significance 0.7
    expect(scores['msr_sql']).toBe(0.9)
    expect(scores['vector_search']).toBe(0.7)
  })

  // PERF-S1 fix (d): latency_complete flag
  it('sets latency_complete=true when timestamps are valid (PERF-S1 fix d)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [] })
    await writeConsumePerformanceRow(makeInput())
    const params = mockQuery.mock.calls[1][1] as unknown[]
    // latency_complete is param $24 (index 23)
    expect(params[23]).toBe(true)
  })

  it('sets latency_complete=false and latency_total_ms=null for invalid timestamps (PERF-S1 fix d)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }).mockResolvedValueOnce({ rows: [] })
    await writeConsumePerformanceRow(
      makeInput({
        synthesis_event: {
          event_type: 'synthesis_complete',
          query_plan_id: 'pp-1',
          bundle_id: 'b-1',
          synthesis_prompt_version: 'v1',
          synthesizer_model_id: 'gemini-2.5-pro',
          finish_reason: 'stop',
          validator_votes: {},
          started_at: 'not-a-date',
          finished_at: 'also-not-a-date',
          input_tokens: 1000,
          output_tokens: 200,
          final_output: 'Jupiter activates the 10th house.',
        },
      })
    )
    const params = mockQuery.mock.calls[1][1] as unknown[]
    // latency_total_ms is param $10 (index 9); latency_complete is param $24 (index 23)
    expect(params[9]).toBeNull()
    expect(params[23]).toBe(false)
  })
})

describe('writeEvalRun / writeEvalPerformanceRow / finalizeEvalRun', () => {
  it('writeEvalRun returns runId from RETURNING clause', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ id: 'run-1' }] })
    const out = await writeEvalRun({ golden_set_version: '1.0', triggered_by: 'answer_eval.ts' })
    expect(out.runId).toBe('run-1')
    expect(mockQuery.mock.calls[0][0]).toMatch(/INSERT INTO eval_runs/)
  })

  it('writeEvalPerformanceRow inserts with eval_run_id wired and source=eval', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const row: EvalPerformanceRow = {
      query_id: 'gq-001',
      query_text: 'Q',
      query_class: 'factual',
      plan_type: 'single_answer',
      plan_tools_selected: ['vector_search'],
      planner_confidence: null,
      latency_planner_ms: 30,
      latency_retrieval_ms: 90,
      latency_synthesis_ms: 1500,
      latency_total_ms: 1620,
      citations_present: true,
      citation_count: 3,
      synthesis_status: 'success',
      validator_verdict: 'pass',
      disclosure_tier: 'super_admin',
      b10_violation: false,
      b11_violation: false,
      retrieval_hit: true,
      retrieval_score_top1: 0.81,
      plan_accuracy_label: 'correct',
      is_prediction: false,
    }
    await writeEvalPerformanceRow('run-1', row)
    const call = mockQuery.mock.calls[0]
    expect(call[0]).toMatch(/INSERT INTO performance_queries/)
    expect(call[0]).toMatch(/'eval'/)
    expect(call[0]).toMatch(/'golden'/)
    expect(call[1]?.[0]).toBe('run-1')
  })

  it('finalizeEvalRun updates aggregates and stamps finished_at', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await finalizeEvalRun('run-1', {
      queryCount: 15,
      recall: 0.93,
      precision: 0.95,
      citationRate: 0.81,
      avgLatencyMs: 2100,
      synthesisPassRate: 0.99,
      retrievalHitRate: 0.97,
      b10ComplianceRate: 1.0,
      b11ComplianceRate: 1.0,
    })
    const call = mockQuery.mock.calls[0]
    expect(call[0]).toMatch(/UPDATE eval_runs SET/)
    expect(call[1]?.[2]).toBe(15)
  })

  it('handles concurrent eval-row writes under one runId', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const baseRow: EvalPerformanceRow = {
      query_id: 'gq-x',
      query_text: 'Q',
      query_class: 'factual',
      plan_type: 'single_answer',
      plan_tools_selected: [],
      planner_confidence: null,
      latency_planner_ms: null,
      latency_retrieval_ms: null,
      latency_synthesis_ms: null,
      latency_total_ms: null,
      citations_present: false,
      citation_count: 0,
      synthesis_status: 'success',
      validator_verdict: 'pass',
      disclosure_tier: null,
      b10_violation: false,
      b11_violation: false,
      retrieval_hit: false,
      retrieval_score_top1: null,
      plan_accuracy_label: 'correct',
      is_prediction: false,
    }
    await Promise.all([
      writeEvalPerformanceRow('run-1', { ...baseRow, query_id: 'a' }),
      writeEvalPerformanceRow('run-1', { ...baseRow, query_id: 'b' }),
      writeEvalPerformanceRow('run-1', { ...baseRow, query_id: 'c' }),
    ])
    expect(mockQuery).toHaveBeenCalledTimes(3)
  })
})
