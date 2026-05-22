/**
 * E-S5: nvidia-loop.test.ts
 *
 * Verifies the NVIDIA NIM agentic loop:
 * - NVIDIAAdapter.tools() returns mode='finish_reason_tool_calls'
 * - providerPayload documents supported/unsupported model lists
 * - NVIDIA planner routing preserved
 * - NVIDIA_LOOP_CONFIG is correctly shaped
 */

import { describe, it, expect } from 'vitest'
import { NVIDIAAdapter } from '../../../src/lib/providers/nvidia/adapter'
import {
  NVIDIA_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

describe('E-S5: NVIDIAAdapter.tools() — model-dependent tool loop', () => {
  const adapter = new NVIDIAAdapter()
  const response = adapter.tools({
    toolLoopMode: 'finish_reason_tool_calls',
    tools: [
      {
        name: 'query_chart_facts',
        description: 'Query chart facts',
        inputSchema: { type: 'object', properties: {} },
      },
    ],
    maxIterations: 8,
  })

  it('returns mode=finish_reason_tool_calls (OpenAI-compat)', () => {
    expect(response.mode).toBe('finish_reason_tool_calls')
  })

  it('returns maxIterations=8', () => {
    expect(response.maxIterations).toBe(8)
  })

  it('providerPayload declares supportedModels list', () => {
    const models = response.providerPayload?.supportedModels as string[]
    expect(Array.isArray(models)).toBe(true)
    expect(models.length).toBeGreaterThan(0)
  })

  it('providerPayload declares unsupportedModels list', () => {
    const models = response.providerPayload?.unsupportedModels as string[]
    expect(Array.isArray(models)).toBe(true)
  })

  it('providerPayload preservePlannerRouting=true (NVIDIA_PLANNER_ENABLED orthogonal)', () => {
    expect(response.providerPayload?.preservePlannerRouting).toBe(true)
  })

  it('llama-3.1-70b is in supportedModels', () => {
    const models = response.providerPayload?.supportedModels as string[]
    expect(models.some(m => m.includes('llama-3.1'))).toBe(true)
  })

  it('llama-3.3-70b is in supportedModels', () => {
    const models = response.providerPayload?.supportedModels as string[]
    expect(models.some(m => m.includes('llama-3.3'))).toBe(true)
  })
})

describe('E-S5: NVIDIA_LOOP_CONFIG invariants', () => {
  it('providerId=nvidia', () => {
    expect(NVIDIA_LOOP_CONFIG.providerId).toBe('nvidia')
  })

  it('terminationSignal=finish_reason_tool_calls', () => {
    expect(NVIDIA_LOOP_CONFIG.terminationSignal).toBe('finish_reason_tool_calls')
  })

  it('supportsInterleavedTextTool=false', () => {
    expect(NVIDIA_LOOP_CONFIG.supportsInterleavedTextTool).toBe(false)
  })

  it('hasReasoningMiddleware=false', () => {
    expect(NVIDIA_LOOP_CONFIG.hasReasoningMiddleware).toBe(false)
  })
})
