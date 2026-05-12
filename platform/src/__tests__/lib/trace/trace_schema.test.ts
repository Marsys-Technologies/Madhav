/**
 * trace_schema.test.ts — Gate II W8 (2026-05-12).
 *
 * Type-level + runtime assertions that the canonical schema in
 * `lib/trace/types.ts` is what renderers + the assembler depend on.
 *
 * Discriminated-union tests ensure the SynthesisStepMetadata branches
 * exclude impossible states (panel.model, single_model.panelists, etc.)
 * at compile time.
 */

import { describe, it, expect, expectTypeOf } from 'vitest'
import type {
  AssembledTrace,
  AuditStepMetadata,
  CheckpointStepMetadata,
  PipelineStage,
  PlannerStepMetadata,
  RetrievalSubToolRun,
  SynthesisStepMetadata,
  TraceStep,
} from '@/lib/trace/types'
import { STAGE_FROM_STEP_NAME, mapStepToStage } from '@/lib/trace/types'

describe('PipelineStage canonical set', () => {
  it('STAGE_FROM_STEP_NAME projects legacy step_names onto canonical stages', () => {
    expect(STAGE_FROM_STEP_NAME.classify).toBe('planner')
    expect(STAGE_FROM_STEP_NAME.compose_bundle).toBe('planner')
    expect(STAGE_FROM_STEP_NAME.context_assembly).toBe('synthesis')
    expect(STAGE_FROM_STEP_NAME.synthesis).toBe('synthesis')
    expect(STAGE_FROM_STEP_NAME.synthesis_done).toBe('synthesis')
    expect(STAGE_FROM_STEP_NAME.citation_warn).toBe('audit')
    expect(STAGE_FROM_STEP_NAME.citation_error).toBe('audit')
  })

  it('mapStepToStage honors parallel_group=tool_fetch for retrieval grouping', () => {
    const toolFetchStep: Pick<TraceStep, 'step_name' | 'parallel_group'> = {
      step_name: 'chart_facts_query',
      parallel_group: 'tool_fetch',
    }
    expect(mapStepToStage(toolFetchStep)).toBe('retrieval')

    const plannerLlmStep: Pick<TraceStep, 'step_name' | 'parallel_group'> = {
      step_name: 'classify',
    }
    expect(mapStepToStage(plannerLlmStep)).toBe('planner')

    const unknownStep: Pick<TraceStep, 'step_name' | 'parallel_group'> = {
      step_name: 'totally_made_up_name',
    }
    expect(mapStepToStage(unknownStep)).toBeNull()
  })

  it('PipelineStage type covers exactly the brief-stated seven stages', () => {
    // compile-time assertion via expectTypeOf
    expectTypeOf<PipelineStage>().toEqualTypeOf<
      'planner' | 'retrieval' | 'synthesis' | 'audit'
      | 'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'
    >()
  })
})

describe('SynthesisStepMetadata discriminated union', () => {
  it('single_model has model but not panelists', () => {
    const sm: SynthesisStepMetadata = {
      mode: 'single_model',
      step_seq: 1,
      status: 'done',
      latency_ms: 100,
      model: 'gemini-2.5-pro',
      input_tokens: 10,
      output_tokens: 20,
      citation_count: 5,
      provider: 'google',
      reasoning_path: false,
      output_shape_compliant: true,
      temperature: 0.3,
      prompt_preview: null,
      reasoning_trace: null,
      context_assembly_short_circuit: null,
    }
    if (sm.mode === 'single_model') {
      // accessible
      expect(sm.model).toBe('gemini-2.5-pro')
      // @ts-expect-error — single_model variant does not have panelists
      void sm.panelists
    }
  })

  it('panel has panelists+aggregator but not single-model fields', () => {
    const pm: SynthesisStepMetadata = {
      mode: 'panel',
      step_seq: 2,
      status: 'done',
      latency_ms: 200,
      panelists: [],
      aggregator: null,
      panel_trace_pending: true,
    }
    if (pm.mode === 'panel') {
      expect(pm.panel_trace_pending).toBe(true)
      // @ts-expect-error — panel variant has no `model` at the top level
      void pm.model
    }
  })
})

describe('AssembledTrace contract', () => {
  it('grouped projection slots are all present (one of each canonical stage)', () => {
    const empty: AssembledTrace = {
      query_id: 'q1',
      query_text: null,
      total_latency_ms: null,
      query_plan: null,
      steps: [],
      grouped: {
        planner: null,
        retrieval: [],
        synthesis: null,
        audit: null,
        checkpoints: [],
      },
      partial: true,
    }
    expect(empty.grouped.planner).toBeNull()
    expect(empty.grouped.retrieval).toEqual([])
    expect(empty.grouped.checkpoints).toEqual([])
  })

  // Compile-time only: ensure each metadata interface is referenceable
  it('referencing each grouped slot type compiles', () => {
    expectTypeOf<AssembledTrace['grouped']['planner']>().toMatchTypeOf<PlannerStepMetadata | null>()
    expectTypeOf<AssembledTrace['grouped']['retrieval']>().toMatchTypeOf<RetrievalSubToolRun[]>()
    expectTypeOf<AssembledTrace['grouped']['synthesis']>().toMatchTypeOf<SynthesisStepMetadata | null>()
    expectTypeOf<AssembledTrace['grouped']['audit']>().toMatchTypeOf<AuditStepMetadata | null>()
    expectTypeOf<AssembledTrace['grouped']['checkpoints']>().toMatchTypeOf<CheckpointStepMetadata[]>()
  })
})
