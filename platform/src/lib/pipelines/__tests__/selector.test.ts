/**
 * Selector tests — unit 3.gateway_pipeline_isolation.
 *
 * The pure selector mirrors route.ts:967 — per-provider R11.E flag gates
 * agentic-vs-single_pass. AC.4: route.ts is a thin selector. These tests
 * pin the selection rule so the route's delegation is deterministic.
 */

import { describe, it, expect } from 'vitest'
import {
  selectPipelineKind,
  getPipeline,
  ADAPTER_TO_LOOP_FLAG,
} from '../selector'
import { singlePassPipeline } from '../single_pass'
import { agenticPipeline } from '../agentic'

describe('selectPipelineKind', () => {
  it('returns single_pass when the agentic-loop flag is off', () => {
    expect(
      selectPipelineKind({ adapterId: 'anthropic', agenticLoopEnabled: false }),
    ).toBe('single_pass')
  })

  it('returns agentic when the loop flag is on AND provider is in the flag map', () => {
    for (const adapterId of Object.keys(ADAPTER_TO_LOOP_FLAG)) {
      expect(
        selectPipelineKind({ adapterId, agenticLoopEnabled: true }),
      ).toBe('agentic')
    }
  })

  it('returns single_pass when the provider is not in the flag map (even if flag on)', () => {
    expect(
      selectPipelineKind({ adapterId: 'unknown-provider', agenticLoopEnabled: true }),
    ).toBe('single_pass')
  })

  it('flag map matches the legacy route.ts L959–965 mapping verbatim', () => {
    expect(ADAPTER_TO_LOOP_FLAG).toEqual({
      anthropic: 'R11E_ANTHROPIC_LOOP',
      google: 'R11E_GEMINI_LOOP',
      openai: 'R11E_OPENAI_LOOP',
      deepseek: 'R11E_DEEPSEEK_LOOP',
      nvidia: 'R11E_NVIDIA_LOOP',
    })
  })
})

describe('getPipeline', () => {
  it('returns the singlePass instance for kind=single_pass', () => {
    expect(getPipeline('single_pass')).toBe(singlePassPipeline)
  })
  it('returns the agentic instance for kind=agentic', () => {
    expect(getPipeline('agentic')).toBe(agenticPipeline)
  })
})
