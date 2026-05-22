/**
 * E-S0: tool-loop-capability-check.test.ts
 *
 * R11.E entry-point. Verifies all 5 provider manifests correctly declare
 * their adaptiveToolLoop strategy per CAPABILITY_MATRIX.
 *
 * Expected manifest values:
 *   - Anthropic: 'stop_reason'              — loop while stop_reason === 'tool_use'
 *   - Google:    'finish_reason_function_calls' — loop while finish_reason === 'function_calls'
 *   - OpenAI:    'finish_reason_tool_calls'  — loop while finish_reason === 'tool_calls'
 *   - DeepSeek:  'finish_reason_tool_calls'  — OpenAI-compat
 *   - NVIDIA:    'finish_reason_tool_calls'  — OpenAI-compat (hosted model dependent)
 */

import { describe, it, expect } from 'vitest'
import { ANTHROPIC_MANIFEST } from '../../src/lib/providers/anthropic/manifest'
import { GOOGLE_MANIFEST } from '../../src/lib/providers/google/manifest'
import { OPENAI_MANIFEST } from '../../src/lib/providers/openai/manifest'
import { DEEPSEEK_MANIFEST } from '../../src/lib/providers/deepseek/manifest'
import { NVIDIA_MANIFEST } from '../../src/lib/providers/nvidia/manifest'
import { getAllManifests } from '../../src/lib/providers/dispatcher'

// ---------------------------------------------------------------------------
// Per-provider adaptiveToolLoop declarations
// ---------------------------------------------------------------------------

describe('E-S0: adaptiveToolLoop — per-provider manifest values', () => {
  it('Anthropic uses stop_reason (tool_use sentinel)', () => {
    expect(ANTHROPIC_MANIFEST.adaptiveToolLoop).toBe('stop_reason')
  })

  it('Google uses finish_reason_function_calls', () => {
    expect(GOOGLE_MANIFEST.adaptiveToolLoop).toBe('finish_reason_function_calls')
  })

  it('OpenAI uses finish_reason_tool_calls', () => {
    expect(OPENAI_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls')
  })

  it('DeepSeek uses finish_reason_tool_calls (OpenAI-compat)', () => {
    expect(DEEPSEEK_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls')
  })

  it('NVIDIA uses finish_reason_tool_calls (OpenAI-compat)', () => {
    expect(NVIDIA_MANIFEST.adaptiveToolLoop).toBe('finish_reason_tool_calls')
  })
})

// ---------------------------------------------------------------------------
// Coverage via getAllManifests()
// ---------------------------------------------------------------------------

describe('E-S0: getAllManifests() tool-loop coverage', () => {
  const all = getAllManifests()

  it('all 5 manifests declare adaptiveToolLoop (non-null, non-undefined)', () => {
    for (const [provider, manifest] of Object.entries(all)) {
      expect(manifest.adaptiveToolLoop, `${provider}.adaptiveToolLoop`).toBeDefined()
      expect(manifest.adaptiveToolLoop, `${provider}.adaptiveToolLoop not null`).not.toBeNull()
    }
  })

  it('exactly 1 provider uses stop_reason (Anthropic only)', () => {
    const stopReason = Object.entries(all)
      .filter(([, m]) => m.adaptiveToolLoop === 'stop_reason')
      .map(([id]) => id)
    expect(stopReason).toEqual(['anthropic'])
  })

  it('exactly 1 provider uses finish_reason_function_calls (Google only)', () => {
    const fnCalls = Object.entries(all)
      .filter(([, m]) => m.adaptiveToolLoop === 'finish_reason_function_calls')
      .map(([id]) => id)
    expect(fnCalls).toEqual(['google'])
  })

  it('exactly 3 providers use finish_reason_tool_calls (OpenAI, DeepSeek, NVIDIA)', () => {
    const toolCalls = Object.entries(all)
      .filter(([, m]) => m.adaptiveToolLoop === 'finish_reason_tool_calls')
      .map(([id]) => id)
      .sort()
    expect(toolCalls).toEqual(['deepseek', 'nvidia', 'openai'])
  })
})

// ---------------------------------------------------------------------------
// Invariant: providers with native thinking also support tool loops
// ---------------------------------------------------------------------------

describe('E-S0: thinking + tool-loop co-occurrence invariant', () => {
  const all = getAllManifests()

  it('all 5 providers have both adaptiveToolLoop and smoothStreaming declared', () => {
    for (const [provider, manifest] of Object.entries(all)) {
      expect(manifest.adaptiveToolLoop, `${provider}.adaptiveToolLoop`).toBeDefined()
      expect(manifest.smoothStreaming, `${provider}.smoothStreaming`).toBe(true)
    }
  })
})
