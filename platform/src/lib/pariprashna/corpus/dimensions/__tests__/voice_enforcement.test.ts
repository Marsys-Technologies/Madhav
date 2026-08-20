import { describe, expect, it } from 'vitest'

import { CORPUS_FIXTURES } from '../../fixtures'
import { baseObservation } from '../../__tests__/test_helpers'
import { scoreVoiceEnforcement } from '../voice_enforcement'

describe('scoreVoiceEnforcement', () => {
  const remedialFixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'remedial')!
  const factualFixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'factual')!

  it('scores 1.0 for a remedial fixture whose prose uses "the tradition prescribes" phrasing', () => {
    const result = scoreVoiceEnforcement(
      baseObservation({
        fixture: remedialFixture,
        proseText: 'Classically, the tradition prescribes strengthening Saturn through disciplined routine.',
      }),
    )
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('flags and lowers score for "you should wear" second-person-imperative phrasing', () => {
    const result = scoreVoiceEnforcement(
      baseObservation({ fixture: remedialFixture, proseText: 'You should wear a red coral to strengthen Mars.' }),
    )
    expect(result.status).toBe('scored')
    expect(result.score).toBeLessThan(1)
    expect(result.findings.length).toBeGreaterThan(0)
  })

  it('returns not_yet_measurable for a non-remedial fixture (scoped dimension)', () => {
    const result = scoreVoiceEnforcement(baseObservation({ fixture: factualFixture }))
    expect(result.status).toBe('not_yet_measurable')
    expect(result.reason).toContain('remedial')
  })

  it('returns not_yet_measurable when no prose text was supplied', () => {
    const result = scoreVoiceEnforcement(baseObservation({ fixture: remedialFixture, proseText: null }))
    expect(result.status).toBe('not_yet_measurable')
  })
})
