import { describe, it, expect } from 'vitest'
import {
  CLASS_TOKEN_CAP,
  STYLE_OUTPUT_CAP,
  computeEffectiveMaxTokens,
} from '../token_caps'

describe('CLASS_TOKEN_CAP / computeEffectiveMaxTokens', () => {
  it('factual class + acharya style + roomy model → model max (64000) wins (passthrough)', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.factual, 64000),
    ).toBe(64000)
  })

  it('holistic class + acharya style + roomy model → model max (64000) wins (passthrough)', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.holistic, 64000),
    ).toBe(64000)
  })

  it('temporal class + client style + roomy model → model max (64000) wins (passthrough)', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.client, CLASS_TOKEN_CAP.temporal, 64000),
    ).toBe(64000)
  })

  it('holistic class + acharya style + small-model max (4096) → model cap wins', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.holistic, 4096),
    ).toBe(4096)
  })

  it('predictive class + acharya style + roomy model → model max (64000) wins (passthrough)', () => {
    expect(
      computeEffectiveMaxTokens(STYLE_OUTPUT_CAP.acharya, CLASS_TOKEN_CAP.predictive, 64000),
    ).toBe(64000)
  })

  it('falls back to styleCap when modelMax is undefined', () => {
    expect(computeEffectiveMaxTokens(3500, 8000, undefined)).toBe(3500)
  })

  it('CLASS_TOKEN_CAP all entries are passthrough (65536)', () => {
    expect(CLASS_TOKEN_CAP.factual).toBe(65536)
    expect(CLASS_TOKEN_CAP.holistic).toBe(65536)
    expect(CLASS_TOKEN_CAP.discovery).toBe(65536)
  })
})
