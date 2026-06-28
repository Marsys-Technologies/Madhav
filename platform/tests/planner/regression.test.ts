/**
 * regression.test.ts — BF.GAP.001 regression guard + routing coverage
 *
 * Pure data assertions on MODELS, STACK_ROUTING, and FAMILY_WORKER from registry.ts.
 * No LLM calls, no API keys required — CI-safe.
 *
 * Guards (updated 2026-06-28 — deepseek-chat → deepseek-v4-flash migration):
 *   1. deepseek-chat does NOT appear as primary in any routing slot (replaced by v4-flash)
 *   2. deepseek stack planner_fast.primary === 'deepseek-v4-flash'
 *   3. All 5 stacks have planner_fast defined
 *   4. FAMILY_WORKER entries all resolve to model IDs in MODELS
 *   5. deepseek-v4-flash is the canonical FAMILY_WORKER for deepseek
 * NOTE: deepseek-chat / deepseek-reasoner entries kept in MODELS for backward compat
 *       (localStorage persistence). They retire 2026-07-24 and will be removed after.
 */
import { describe, it, expect } from 'vitest'

import {
  MODELS,
  STACK_ROUTING,
  FAMILY_WORKER,
  type ModelStack,
  type CallType,
} from '@/lib/models/registry'

const ALL_STACKS: ModelStack[] = ['anthropic', 'gemini', 'gpt', 'deepseek', 'nim']
const ALL_CALL_TYPES: CallType[] = ['synthesis', 'planner_deep', 'planner_fast', 'context_assembly', 'worker']

const modelIds = new Set(MODELS.map(m => m.id))

describe('BF.GAP.001 regression guard', () => {
  // Post-migration (2026-06-28): deepseek-v4-flash IS the canonical primary.
  // Guard now prevents regression back to deepseek-chat.
  it('deepseek planner_fast.primary is deepseek-v4-flash (not deepseek-chat)', () => {
    expect(STACK_ROUTING.deepseek.planner_fast.primary).toBe('deepseek-v4-flash')
  })

  it('deepseek-chat does not appear as primary in any deepseek stack routing slot', () => {
    const violations: string[] = []
    for (const callType of ALL_CALL_TYPES) {
      const { primary } = STACK_ROUTING.deepseek[callType]
      if (primary === 'deepseek-chat') {
        violations.push(`deepseek.${callType}.primary`)
      }
    }
    expect(violations).toEqual([])
  })
})

describe('Stack coverage assertions', () => {
  it('all 5 stacks have planner_fast defined', () => {
    for (const stack of ALL_STACKS) {
      expect(STACK_ROUTING[stack].planner_fast, `${stack} missing planner_fast`).toBeDefined()
      expect(STACK_ROUTING[stack].planner_fast.primary, `${stack}.planner_fast.primary missing`).toBeTruthy()
    }
  })

  it('all 5 stacks have all 5 call types defined', () => {
    for (const stack of ALL_STACKS) {
      for (const callType of ALL_CALL_TYPES) {
        expect(STACK_ROUTING[stack][callType], `${stack}.${callType} missing`).toBeDefined()
      }
    }
  })
})

describe('FAMILY_WORKER integrity', () => {
  it('all FAMILY_WORKER values correspond to model IDs in MODELS', () => {
    const missing: string[] = []
    for (const [provider, modelId] of Object.entries(FAMILY_WORKER)) {
      if (!modelIds.has(modelId)) {
        missing.push(`${provider} → ${modelId}`)
      }
    }
    expect(missing).toEqual([])
  })
})

// deepseek-chat / deepseek-v4-flash entry integrity
// deepseek-chat is kept as a backward-compat entry for persisted localStorage model IDs.
// deepseek-v4-flash is now the canonical routing ID.
describe('deepseek model entry health', () => {
  it('deepseek-chat entry exists in MODELS (backward compat)', () => {
    expect(modelIds.has('deepseek-chat')).toBe(true)
  })

  it('deepseek-chat entry does not have "deprecated" in label or hint (label is user-facing)', () => {
    const entry = MODELS.find(m => m.id === 'deepseek-chat')
    expect(entry).toBeDefined()
    expect(entry!.label.toLowerCase()).not.toContain('deprecated')
    expect(entry!.hint.toLowerCase()).not.toContain('deprecated')
  })

  it('deepseek-chat speedTier is fast', () => {
    const entry = MODELS.find(m => m.id === 'deepseek-chat')
    expect(entry!.speedTier).toBe('fast')
  })

  it('deepseek-v4-flash entry exists in MODELS (canonical routing ID)', () => {
    expect(modelIds.has('deepseek-v4-flash')).toBe(true)
  })

  it('FAMILY_WORKER.deepseek is deepseek-v4-flash', () => {
    expect(FAMILY_WORKER.deepseek).toBe('deepseek-v4-flash')
  })
})
