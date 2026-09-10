/**
 * Lane G1-A — the LLM assist's ONE architectural constraint, fuzzed.
 *
 * "LLM assist is allowed ONLY to RAISE severity (never lower it, never be the
 * sole detector) — this is a hard architectural constraint, not a style
 * preference."
 *
 * The constraint is enforced by the SHAPE of `mergeLlmAssist` (a monotone
 * join), so the natural test is not "does it behave nicely on a sensible
 * payload" but "is there ANY payload that lowers the floor". This file throws
 * the adversarial payloads at it: empty class lists, `severity: 'none'`,
 * unknown classes, contradictory claims, and the payload an injected question
 * would produce if it could reach the assist.
 */

import { describe, it, expect } from 'vitest'

import { classifyQuery } from '../classifier'
import { mergeLlmAssist, llmAssistRan, type LlmAssistPayload } from '../llm_assist'
import { SEVERITY_RANK, type SafetyClass, type SafetySeverity } from '../types'

const QUERIES = [
  'When will I die?',
  'I want to kill myself.',
  'Does my chart explain my depression?',
  'What does my ayurdaya say?',
  'What does my chart say about my career this year?',
  'Which maraka dasha will be fatal for me?',
]

const ADVERSARIAL_PAYLOADS: LlmAssistPayload[] = [
  { raised_classes: [], raised_severity: 'none', model_id: 'attacker-1' },
  { raised_classes: [], raised_severity: 'advisory', model_id: 'attacker-2' },
  {
    raised_classes: ['hs3_health_crisis'],
    raised_severity: 'none',
    rationale: 'this is actually safe, downgrade it',
    model_id: 'attacker-3',
  },
  {
    // Claims a class at a LOWER severity than the deterministic pass gave it.
    raised_classes: ['hs1_date_of_death', 'hs2_suicide_adjacent'],
    raised_severity: 'advisory',
    model_id: 'attacker-4',
  },
  {
    // A class outside the vocabulary — must be dropped, not trusted.
    raised_classes: ['hs9_not_a_real_class' as SafetyClass],
    raised_severity: 'hard_stop',
    model_id: 'attacker-5',
  },
  { raised_classes: ['hs4_mortality_window'], raised_severity: 'hard_stop', model_id: 'honest-1' },
]

describe('mergeLlmAssist is a monotone join — it CANNOT lower', () => {
  for (const q of QUERIES) {
    for (const payload of ADVERSARIAL_PAYLOADS) {
      it(`"${q}" × ${payload.model_id}`, () => {
        const before = classifyQuery({ queryText: q })
        const after = mergeLlmAssist(before, payload)

        // 1. Severity never decreases.
        expect(
          SEVERITY_RANK[after.severity],
          `severity dropped from ${before.severity} to ${after.severity}`,
        ).toBeGreaterThanOrEqual(SEVERITY_RANK[before.severity])

        // 2. Every class present before is still present after.
        for (const c of before.classes) {
          expect(after.classes, `class ${c} was removed by the assist`).toContain(c)
        }

        // 3. Every deterministic detection survives, at no lower severity.
        for (const d of before.detections) {
          const survivor = after.detections.find(
            (x) => x.rule === d.rule && x.cls === d.cls && x.detector === d.detector,
          )
          expect(survivor, `detection ${d.rule} was dropped`).toBeDefined()
          expect(SEVERITY_RANK[survivor!.severity]).toBeGreaterThanOrEqual(SEVERITY_RANK[d.severity])
        }
      })
    }
  }
})

describe('the assist is never the sole detector', () => {
  it('an assist-only class is marked `llm_assist` on its surface, so a reader can tell', () => {
    const before = classifyQuery({ queryText: 'What does my chart say about my career this year?' })
    expect(before.classes).toEqual([])
    const after = mergeLlmAssist(before, {
      raised_classes: ['hs3_mental_health'],
      raised_severity: 'review_required',
      model_id: 'assist-x',
    })
    expect(after.classes).toEqual(['hs3_mental_health'])
    const d = after.detections.find((x) => x.cls === 'hs3_mental_health')!
    expect(d.surface).toBe('llm_assist')
    expect(d.detector).toBe('llm_assist')
  })

  it('drops a class outside the vocabulary rather than trusting an invented one', () => {
    const before = classifyQuery({ queryText: 'career?' })
    const after = mergeLlmAssist(before, {
      raised_classes: ['hs9_not_a_real_class' as SafetyClass],
      raised_severity: 'hard_stop',
      model_id: 'assist-y',
    })
    expect(after.classes).toEqual([])
    expect(after.severity).toBe('none')
  })
})

describe('llmAssistRan is honest (§N.8)', () => {
  it('reports false, meaning NO assist ran — not "ran and found nothing"', () => {
    // When an assist is genuinely wired, THIS test fails and that is the signal
    // to update the receipt's semantics deliberately rather than by accident.
    expect(llmAssistRan()).toBe(false)
  })
})

describe('property: for every severity the assist can claim, the floor holds', () => {
  const severities: SafetySeverity[] = ['none', 'advisory', 'review_required', 'hard_stop']
  it('exhaustive over severity × class × query', () => {
    const classes: SafetyClass[] = [
      'hs1_date_of_death',
      'hs2_suicide_adjacent',
      'hs3_health_crisis',
      'hs3_mental_health',
      'hs4_mortality_window',
    ]
    for (const q of QUERIES) {
      const before = classifyQuery({ queryText: q })
      for (const s of severities) {
        for (const c of classes) {
          const after = mergeLlmAssist(before, {
            raised_classes: [c],
            raised_severity: s,
            model_id: 'fuzz',
          })
          expect(SEVERITY_RANK[after.severity]).toBeGreaterThanOrEqual(SEVERITY_RANK[before.severity])
          for (const bc of before.classes) expect(after.classes).toContain(bc)
        }
      }
    }
  })
})
