/**
 * The 3 §N.8 stub dimensions — proves each ALWAYS returns
 * `not_yet_measurable` regardless of input, never a fabricated number, even
 * when fed a "maximally favorable-looking" observation.
 */
import { describe, expect, it } from 'vitest'

import { baseObservation } from '../../__tests__/test_helpers'
import { scoreFalsifierQuality } from '../falsifier_quality'
import { scoreTypedConfidenceHonesty } from '../typed_confidence_honesty'
import { scoreReaderComprehension } from '../reader_comprehension'

const STUBS: Array<{ name: string; fn: (obs: ReturnType<typeof baseObservation>) => ReturnType<typeof scoreFalsifierQuality> }> = [
  { name: 'falsifier_quality', fn: scoreFalsifierQuality },
  { name: 'typed_confidence_honesty', fn: scoreTypedConfidenceHonesty },
  { name: 'reader_comprehension', fn: scoreReaderComprehension },
]

describe('unscored §N.8 stub dimensions', () => {
  for (const { name, fn } of STUBS) {
    describe(name, () => {
      it('returns not_yet_measurable with a null score and a non-empty reason on a full observation', () => {
        const result = fn(baseObservation())
        expect(result.status).toBe('not_yet_measurable')
        expect(result.score).toBeNull()
        expect(result.reason).toBeTruthy()
      })

      it('returns the SAME not_yet_measurable result even with no receipt/metrics/prose at all', () => {
        const result = fn(baseObservation({ receipt: null, turnMetrics: null, proseText: null }))
        expect(result.status).toBe('not_yet_measurable')
        expect(result.score).toBeNull()
      })
    })
  }
})
