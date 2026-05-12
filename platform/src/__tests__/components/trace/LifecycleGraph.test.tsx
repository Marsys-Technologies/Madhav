/**
 * LifecycleGraph.test.tsx — Gate II W8 (2026-05-12).
 *
 * Per AC.4: lifecycle renders Planner → Retrieval (grouped) → Synthesis →
 * Audit, followed by a Checkpoints group with N-of-3 summary. The graph's
 * top-level node set must be stable across all-checkpoints-on vs
 * checkpoints-off fixtures (D1).
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { LifecycleGraph } from '@/components/trace/LifecycleGraph'
import type { AssembledTrace, TraceStep } from '@/lib/trace/types'

const ASSEMBLED_EMPTY: AssembledTrace = {
  query_id: 'q1',
  query_text: null,
  total_latency_ms: null,
  query_plan: null,
  steps: [],
  partial: false,
  grouped: {
    planner: null,
    retrieval: [],
    synthesis: null,
    audit: null,
    checkpoints: [],
  },
}

function step(
  seq: number,
  name: string,
  type: TraceStep['step_type'] = 'llm',
  opts: Partial<{ status: TraceStep['status']; parallel_group: string }> = {},
): TraceStep {
  return {
    query_id: 'q1',
    step_seq: seq,
    step_name: name,
    step_type: type,
    status: opts.status ?? 'done',
    started_at: '2026-05-12T00:00:00Z',
    completed_at: '2026-05-12T00:00:01Z',
    latency_ms: 100,
    parallel_group: opts.parallel_group,
    data_summary: {},
    payload: {},
  }
}

const STEPS_NO_CHECKPOINTS: TraceStep[] = [
  step(1, 'classify', 'llm'),
  step(2, 'vector_search', 'vector', { parallel_group: 'tool_fetch' }),
  step(3, 'cgm_graph_walk', 'sql', { parallel_group: 'tool_fetch' }),
  step(4, 'synthesis', 'llm'),
]

const STEPS_WITH_CHECKPOINTS: TraceStep[] = [
  ...STEPS_NO_CHECKPOINTS,
  step(5, 'checkpoint_4_5', 'llm'),
  step(6, 'checkpoint_5_5', 'llm'),
  step(7, 'checkpoint_8_5', 'llm'),
]

describe('LifecycleGraph', () => {
  it('renders Planner → Retrieval → Synthesis → Audit + Checkpoints group (no checkpoints)', () => {
    render(
      <LifecycleGraph
        steps={STEPS_NO_CHECKPOINTS}
        assembled={ASSEMBLED_EMPTY}
        selectedStepId="synthesis"
        onSelectStep={vi.fn()}
      />,
    )
    expect(screen.getByTestId('lifecycle-node-planner')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-retrieval')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-synthesis')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-audit')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-checkpoints')).toBeInTheDocument()
    expect(screen.getByTestId('checkpoints-summary')).toHaveTextContent(/0 of 3 ran/i)
  })

  it('renders the same top-level node set with all checkpoints firing (D1)', () => {
    render(
      <LifecycleGraph
        steps={STEPS_WITH_CHECKPOINTS}
        assembled={ASSEMBLED_EMPTY}
        selectedStepId="synthesis"
        onSelectStep={vi.fn()}
      />,
    )
    expect(screen.getByTestId('lifecycle-node-planner')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-retrieval')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-synthesis')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-audit')).toBeInTheDocument()
    expect(screen.getByTestId('lifecycle-node-checkpoints')).toBeInTheDocument()
    expect(screen.getByTestId('checkpoints-summary')).toHaveTextContent(/3 of 3 ran/i)
  })

  it('renders one retrieval sub-row per fired tool', () => {
    render(
      <LifecycleGraph
        steps={STEPS_NO_CHECKPOINTS}
        assembled={ASSEMBLED_EMPTY}
        selectedStepId="synthesis"
        onSelectStep={vi.fn()}
      />,
    )
    expect(screen.getByTestId('retrieval-subrow-vector_search')).toBeInTheDocument()
    expect(screen.getByTestId('retrieval-subrow-cgm_graph_walk')).toBeInTheDocument()
  })

  it('Audit node renders even without an audit step row', () => {
    render(
      <LifecycleGraph
        steps={STEPS_NO_CHECKPOINTS}
        assembled={ASSEMBLED_EMPTY}
        selectedStepId="synthesis"
        onSelectStep={vi.fn()}
      />,
    )
    const audit = screen.getByTestId('lifecycle-node-audit')
    expect(audit).toHaveAttribute('data-stage-has-data', 'false')
  })
})
