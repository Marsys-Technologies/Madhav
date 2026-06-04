/**
 * Selector tests — unit 3.gateway_pipeline_isolation.
 * R11E flags permanently true (WS-0 2026-06-04): all 5 providers use agentic path.
 */

import { describe, it, expect } from 'vitest'
import { selectPipelineKind, getPipeline } from '../selector'
import { singlePassPipeline } from '../single_pass'
import { agenticPipeline } from '../agentic'

describe('selectPipelineKind', () => {
  it('returns single_pass when agenticLoopEnabled is false', () => {
    expect(selectPipelineKind({ adapterId: 'anthropic', agenticLoopEnabled: false })).toBe('single_pass')
  })

  it('returns agentic for all known providers when loop enabled', () => {
    for (const id of ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']) {
      expect(selectPipelineKind({ adapterId: id, agenticLoopEnabled: true })).toBe('agentic')
    }
  })

  it('returns single_pass for unknown provider even if loop flag on', () => {
    expect(selectPipelineKind({ adapterId: 'unknown', agenticLoopEnabled: true })).toBe('single_pass')
  })
})

describe('getPipeline', () => {
  it('returns singlePass instance for kind=single_pass', () => {
    expect(getPipeline('single_pass')).toBe(singlePassPipeline)
  })
  it('returns agentic instance for kind=agentic', () => {
    expect(getPipeline('agentic')).toBe(agenticPipeline)
  })
})
