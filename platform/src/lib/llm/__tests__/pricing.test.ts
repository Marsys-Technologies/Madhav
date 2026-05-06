import { describe, it, expect } from 'vitest'
import { getModelPricing, getModelPricingSync, computeCostUsd } from '../pricing'

describe('pricing helper', () => {
  it('returns null for unknown model_id', async () => {
    expect(await getModelPricing('does-not-exist-zz')).toBeNull()
    expect(getModelPricingSync('does-not-exist-zz')).toBeNull()
  })

  it('returns ModelPricing shape for a known model', async () => {
    const p = await getModelPricing('claude-opus-4-7')
    expect(p).not.toBeNull()
    expect(p!.model_id).toBe('claude-opus-4-7')
    expect(p!.input_per_1m_usd).toBeGreaterThan(0)
    expect(p!.output_per_1m_usd).toBeGreaterThan(0)
  })

  it('computeCostUsd returns null when pricing missing', () => {
    expect(computeCostUsd(null, { input_tokens: 100, output_tokens: 100 })).toBeNull()
  })

  it('computeCostUsd returns null when both input and output token counts are missing', () => {
    const p = getModelPricingSync('claude-opus-4-7')!
    expect(computeCostUsd(p, {})).toBeNull()
    expect(computeCostUsd(p, { input_tokens: null, output_tokens: null })).toBeNull()
  })

  it('computeCostUsd handles input-only', () => {
    const p: import('../pricing').ModelPricing = {
      model_id: 'x',
      input_per_1m_usd: 1.0,
      output_per_1m_usd: 5.0,
    }
    // 1M input * $1/M = $1.00
    expect(computeCostUsd(p, { input_tokens: 1_000_000 })).toBe(1.0)
  })

  it('computeCostUsd handles output-only', () => {
    const p: import('../pricing').ModelPricing = {
      model_id: 'x',
      input_per_1m_usd: 1.0,
      output_per_1m_usd: 5.0,
    }
    // 1M output * $5/M = $5.00
    expect(computeCostUsd(p, { output_tokens: 1_000_000 })).toBe(5.0)
  })

  it('computeCostUsd combines input + output', () => {
    const p: import('../pricing').ModelPricing = {
      model_id: 'x',
      input_per_1m_usd: 3.0,
      output_per_1m_usd: 15.0,
    }
    // 100k input * $3/M + 50k output * $15/M = 0.30 + 0.75 = 1.05
    expect(computeCostUsd(p, { input_tokens: 100_000, output_tokens: 50_000 })).toBe(1.05)
  })

  it('computeCostUsd includes cache fields when present', () => {
    const p: import('../pricing').ModelPricing = {
      model_id: 'x',
      input_per_1m_usd: 3.0,
      output_per_1m_usd: 15.0,
      cache_read_per_1m_usd: 0.30,
      cache_write_per_1m_usd: 3.75,
    }
    // 1M cache read * 0.30 = 0.30
    expect(
      computeCostUsd(p, { input_tokens: 0, cache_read_tokens: 1_000_000 })
    ).toBe(0.30)
  })

  it('computeCostUsd rounds to 6 decimal places', () => {
    const p: import('../pricing').ModelPricing = {
      model_id: 'x',
      input_per_1m_usd: 1.234567891,
      output_per_1m_usd: 0,
    }
    const v = computeCostUsd(p, { input_tokens: 1 })!
    // 1/1e6 * 1.234567891 ≈ 1.234567891e-6 → rounded to 6dp = 0.000001
    expect(v).toBeLessThanOrEqual(0.000002)
    expect(Number.isFinite(v)).toBe(true)
  })
})
