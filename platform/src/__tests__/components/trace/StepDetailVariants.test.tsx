/**
 * StepDetailVariants.test.tsx — Gate II W8 (2026-05-12).
 *
 * Per AC.5: each step-detail variant renders correct metadata for its stage.
 * Tests cover PlannerDetail, RetrievalDetail, SynthesisDetail (single_model
 * + panel), AuditDetail, CheckpointDetail.
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PlannerDetail } from '@/components/trace/step_detail/PlannerDetail'
import { RetrievalDetail } from '@/components/trace/step_detail/RetrievalDetail'
import { SynthesisDetail } from '@/components/trace/step_detail/SynthesisDetail'
import { AuditDetail } from '@/components/trace/step_detail/AuditDetail'
import { CheckpointDetail } from '@/components/trace/step_detail/CheckpointDetail'
import type {
  AuditStepMetadata,
  CheckpointStepMetadata,
  PlannerStepMetadata,
  RetrievalSubToolRun,
  SynthesisStepMetadata,
} from '@/lib/trace/types'

describe('PlannerDetail', () => {
  it('renders query_class, plan_type, confidence, and tool chips', () => {
    const planner: PlannerStepMetadata = {
      step_seq: 1,
      status: 'done',
      latency_ms: 250,
      query_plan: {
        query_class: 'CHART_ANALYSIS',
        expected_output_shape: 'analytical',
        router_confidence: 0.92,
        planning_rationale: 'analytical tools selected',
      },
      tool_calls: [
        { tool_name: 'vector_search', params: {}, priority: 1 },
        { tool_name: 'cgm_graph_walk', params: {}, priority: 2 },
      ],
      bundle_summary: '3 assets · 2 tools',
    }
    render(<PlannerDetail planner={planner} />)
    expect(screen.getByTestId('planner-query-class')).toHaveTextContent('CHART_ANALYSIS')
    expect(screen.getByTestId('planner-plan-type')).toHaveTextContent('analytical')
    expect(screen.getByTestId('planner-confidence')).toHaveTextContent('0.92')
    const chips = screen.getByTestId('planner-tool-chips')
    expect(chips.textContent).toContain('vector_search')
    expect(chips.textContent).toContain('cgm_graph_walk')
  })

  it('renders graceful empty state when planner is null', () => {
    render(<PlannerDetail planner={null} />)
    expect(screen.getByTestId('planner-detail')).toHaveTextContent(/did not run/i)
  })
})

describe('RetrievalDetail', () => {
  it('renders one block per sub-tool', () => {
    const retrieval: RetrievalSubToolRun[] = [
      {
        tool_name: 'vector_search',
        step_seq: 2,
        step_type: 'vector',
        status: 'done',
        latency_ms: 150,
        data_summary: { rows_returned: 20, token_estimate: 1500, top_score: 0.87 },
        payload: {},
      },
      {
        tool_name: 'cgm_graph_walk',
        step_seq: 3,
        step_type: 'sql',
        status: 'done',
        latency_ms: 80,
        data_summary: { rows_returned: 5 },
        payload: {},
      },
    ]
    render(<RetrievalDetail retrieval={retrieval} />)
    expect(screen.getByTestId('retrieval-detail-vector_search')).toBeInTheDocument()
    expect(screen.getByTestId('retrieval-detail-cgm_graph_walk')).toBeInTheDocument()
  })

  it('focusedTool narrows to a single sub-tool', () => {
    const retrieval: RetrievalSubToolRun[] = [
      {
        tool_name: 'vector_search', step_seq: 2, step_type: 'vector', status: 'done',
        latency_ms: 150, data_summary: {}, payload: {},
      },
      {
        tool_name: 'cgm_graph_walk', step_seq: 3, step_type: 'sql', status: 'done',
        latency_ms: 80, data_summary: {}, payload: {},
      },
    ]
    render(<RetrievalDetail retrieval={retrieval} focusedTool="vector_search" />)
    expect(screen.getByTestId('retrieval-detail-vector_search')).toBeInTheDocument()
    expect(screen.queryByTestId('retrieval-detail-cgm_graph_walk')).toBeNull()
  })
})

describe('SynthesisDetail', () => {
  it('single_model: renders one LLM-call row', () => {
    const sm: SynthesisStepMetadata = {
      mode: 'single_model',
      step_seq: 1, status: 'done', latency_ms: 4000,
      model: 'gemini-2.5-pro',
      input_tokens: 12000, output_tokens: 1500,
      citation_count: 8, provider: 'google', reasoning_path: false,
      output_shape_compliant: true, temperature: 0.3,
      prompt_preview: null, reasoning_trace: null, context_assembly_short_circuit: null,
    }
    render(<SynthesisDetail synthesis={sm} />)
    expect(screen.getByTestId('synthesis-detail')).toHaveAttribute('data-mode', 'single_model')
    expect(screen.getByTestId('synthesis-llm-call')).toBeInTheDocument()
  })

  it('panel: renders panelist rows + aggregator row + pending note', () => {
    const pm: SynthesisStepMetadata = {
      mode: 'panel',
      step_seq: 1, status: 'done', latency_ms: 5000,
      panelists: [
        { panelist_id: 'pa', model: 'gemini-2.5-pro', latency_ms: 1500, input_tokens: 1, output_tokens: 1 },
        { panelist_id: 'pb', model: 'deepseek-chat', latency_ms: 1700, input_tokens: 1, output_tokens: 1 },
      ],
      aggregator: { model: 'gemini-2.5-pro', latency_ms: 1800, input_tokens: 1, output_tokens: 1 },
      panel_trace_pending: false,
    }
    render(<SynthesisDetail synthesis={pm} />)
    expect(screen.getByTestId('synthesis-detail')).toHaveAttribute('data-mode', 'panel')
    expect(screen.getByTestId('panel-panelist-pa')).toBeInTheDocument()
    expect(screen.getByTestId('panel-panelist-pb')).toBeInTheDocument()
    expect(screen.getByTestId('panel-aggregator')).toBeInTheDocument()
  })

  it('panel with panel_trace_pending=true renders the pending note', () => {
    const pm: SynthesisStepMetadata = {
      mode: 'panel',
      step_seq: 1, status: 'done', latency_ms: 5000,
      panelists: [], aggregator: null, panel_trace_pending: true,
    }
    render(<SynthesisDetail synthesis={pm} />)
    expect(screen.getByTestId('panel-pending-note')).toBeInTheDocument()
  })
})

describe('AuditDetail', () => {
  it('renders verdict, compliance flags, and audit_event_id', () => {
    const audit: AuditStepMetadata = {
      audit_event_id: 'ae-42',
      audit_event_version: 1,
      disclosure_tier: 'super_admin',
      validator_verdict: 'PASS',
      b10_compliant: true,
      b11_compliant: true,
      citation_gate: null,
      placeholder_note: null,
    }
    render(<AuditDetail audit={audit} />)
    expect(screen.getByTestId('audit-event-id')).toHaveTextContent('ae-42')
    expect(screen.getByTestId('audit-detail').textContent).toMatch(/PASS/)
    expect(screen.getByTestId('audit-detail').textContent).toMatch(/super_admin/)
  })

  it('surfaces placeholder_note when audit_events row is missing', () => {
    const audit: AuditStepMetadata = {
      audit_event_id: null, audit_event_version: null, disclosure_tier: null,
      validator_verdict: 'UNKNOWN', b10_compliant: null, b11_compliant: null,
      citation_gate: null,
      placeholder_note: 'No audit_events row found for this query_id.',
    }
    render(<AuditDetail audit={audit} />)
    expect(screen.getByTestId('audit-placeholder-note')).toBeInTheDocument()
  })
})

describe('CheckpointDetail', () => {
  it('renders SKIPPED checkpoint dimmed and with disabled note', () => {
    const cp: CheckpointStepMetadata = {
      stage: 'checkpoint_4_5',
      enabled: null, ran: false, status: null,
      latency_ms: null, verdict: 'SKIPPED', notes: 'Checkpoint disabled or did not run',
    }
    render(<CheckpointDetail checkpoint={cp} />)
    const el = screen.getByTestId('checkpoint-detail-checkpoint_4_5')
    expect(el).toBeInTheDocument()
    expect(el.className).toMatch(/opacity-70/)
  })
})
