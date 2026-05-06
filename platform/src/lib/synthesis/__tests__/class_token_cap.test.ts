import { describe, it, expect } from 'vitest'
import {
  CLASS_TOKEN_CAP,
  STYLE_OUTPUT_CAP,
  computeEffectiveMaxTokens,
} from '../token_caps'

describe('CLASS_TOKEN_CAP / computeEffectiveMaxTokens', () => {
  it('factual class + acharya style + roomy model → class cap (1500) wins', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.factual, 64000),
    ).toBe(1500)
  })

  it('holistic class + acharya style + roomy model → both caps tie at 8000', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.holistic, 64000),
    ).toBe(8000)
  })

  it('temporal class + client style → class cap (2500) wins over style cap (3500)', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.client, CLASS_TOKEN_CAP.temporal, 64000),
    ).toBe(2500)
  })

  it('holistic class + acharya style + small-model max (4096) → model cap wins', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.holistic, 4096),
    ).toBe(4096)
  })

  it('predictive class is capped at 4000 even with acharya style', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.predictive, 64000),
    ).toBe(4000)
  })

  it('falls back to styleCap when modelMax is undefined', () => {
    expect(computeEffectiveMaxTokens(3500, 8000, undefined)).toBe(3500)
  })

  it('CLASS_TOKEN_CAP exposes expected entries', () => {
    expect(CLASS_TOKEN_CAP.factual).toBe(1500)
    expect(CLASS_TOKEN_CAP.holistic).toBe(8000)
    expect(CLASS_TOKEN_CAP.discovery).toBe(8000)
  })
})
