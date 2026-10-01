import { describe, expect, it } from 'vitest'
import { normalizeSdkUsage } from '../usage'
import { priceUsage, type RateCard } from '../pricing'

const card: RateCard = { id: 'rate-1', provider: 'openai', model: 'model', effectiveFrom: '2026-01-01T00:00:00Z',
  observedAt: '2026-01-01T00:00:00Z', sourceUrl: 'https://openai.com/api/pricing/',
  inputPerMillion: '2', outputPerMillion: '8', cacheReadPerMillion: '0.2', cacheWritePerMillion: null,
  reasoningPerMillion: null, outputIncludesReasoning: true, maxInputTokens: null }

describe('usage evidence', () => {
  it('retains unknown counts instead of making zero', () => {
    expect(normalizeSdkUsage(undefined).input).toBeNull()
    expect(normalizeSdkUsage(undefined).source).toBe('unavailable')
    expect(normalizeSdkUsage({ inputTokens: { total: 0 }, outputTokens: { total: 0 } }).input).toBe(0)
  })
  it('normalizes SDK v3 cache and reasoning subsets', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total: 100, noCache: 70, cacheRead: 30, cacheWrite: 0 },
      outputTokens: { total: 20, text: 15, reasoning: 5 } })
    expect(usage).toMatchObject({ input: 100, uncachedInput: 70, cacheRead: 30, cacheWrite: 0,
      output: 20, textOutput: 15, reasoning: 5, source: 'provider_reported', issues: [] })
  })
  it('rejects negative, fractional, unsafe and inconsistent subsets', () => {
    expect(normalizeSdkUsage({ inputTokens: { total: -1 } }).issues).toContain('invalid_input')
    expect(normalizeSdkUsage({ inputTokens: { total: 10, cacheRead: 20 } }).issues).toContain('input_subsets_exceed_total')
    expect(normalizeSdkUsage({ outputTokens: { total: 10, reasoning: 20 } }).issues).toContain('output_subsets_exceed_total')
  })
  it('keeps only allowlisted numeric raw usage evidence', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total: 1 }, raw: { prompt_tokens: 1, secret: 'key', text: 'private',
      completion_tokens_details: { reasoning_tokens: 2, text: 'private' } } })
    expect(JSON.stringify(usage)).not.toMatch(/private|secret|key/)
    expect(usage.raw).toEqual({ prompt_tokens: 1, completion_tokens_details: { reasoning_tokens: 2 } })
  })
})

describe('snapshot pricing', () => {
  it('does not charge cached input or reasoning twice', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total: 100, cacheRead: 30, cacheWrite: 0 },
      outputTokens: { total: 20, reasoning: 5 } })
    expect(priceUsage(usage, card).costUsd).toBe('0.000306000000')
    expect(priceUsage(usage, card).lines.map(x => x.quantity)).toEqual([70, 30, 20])
  })
  it('requires cache prices when cache use is present', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total: 100, cacheRead: 30 }, outputTokens: { total: 20 } })
    expect(priceUsage(usage, { ...card, cacheReadPerMillion: null }).costUsd).toBeNull()
  })
  it('keeps missing rates, missing usage and malformed evidence unpriced', () => {
    expect(priceUsage(normalizeSdkUsage(undefined), card).status).toBe('usage_unavailable')
    expect(priceUsage(normalizeSdkUsage({ inputTokens: { total: 1 }, outputTokens: { total: 1 } }), null).status).toBe('rate_unavailable')
    expect(priceUsage(normalizeSdkUsage({ inputTokens: { total: 1, cacheRead: 2 }, outputTokens: { total: 1 } }), card).status).toBe('usage_inconsistent')
  })
  it('keeps missing cache breakdown and non-token tariffs unpriced', () => {
    const usage=normalizeSdkUsage({inputTokens:{total:100},outputTokens:{total:10}})
    expect(priceUsage(usage,card).status).toBe('partial_rate')
    expect(priceUsage(usage,{...card,tokenPricingOnly:false}).status).toBe('rate_inapplicable')
  })
  it('refuses incomplete explicit input partitions', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total:100,noCache:50,cacheRead:20,cacheWrite:0 },outputTokens:{total:10} })
    expect(usage.issues).toContain('input_subsets_incomplete')
    expect(priceUsage(usage,card).costUsd).toBeNull()
    expect(priceUsage({...usage,issues:[]},card).costUsd).toBeNull()
  })
  it('supports a separately priced reasoning subset without duplicate output', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total: 0 }, outputTokens: { total: 20, reasoning: 5 } })
    expect(priceUsage(usage, { ...card, outputIncludesReasoning: false, reasoningPerMillion: '10' }).costUsd).toBe('0.000170000000')
  })
  it('does decimal costing without floating point drift and respects thresholds', () => {
    const usage = normalizeSdkUsage({ inputTokens: { total: 3, cacheRead: 0 }, outputTokens: { total: 0 } })
    expect(priceUsage(usage, { ...card, inputPerMillion: '0.1' }).costUsd).toBe('0.000000300000')
    expect(priceUsage(usage, { ...card, maxInputTokens: 2 }).status).toBe('rate_inapplicable')
  })
})
