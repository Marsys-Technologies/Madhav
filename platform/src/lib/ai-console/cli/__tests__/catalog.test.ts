import { describe, expect, it } from 'vitest'
import { parseCliModelCatalog } from '../catalog'

describe('CLI model catalog parser', () => {
  it('parses the Antigravity tab-separated catalog and rejects malformed rows', () => {
    expect(parseCliModelCatalog('antigravity_models', [
      'gemini-3.8-flash-low\tGemini 3.8 Flash (Low)',
      'claude-sonnet-4-6\tClaude Sonnet 4.6 (Thinking)',
    ].join('\n'))).toEqual([
      { modelId: 'gemini-3.8-flash-low', displayName: 'Gemini 3.8 Flash (Low)' },
      { modelId: 'claude-sonnet-4-6', displayName: 'Claude Sonnet 4.6 (Thinking)' },
    ])
    expect(() => parseCliModelCatalog('antigravity_models', 'unsafe-only-one-column')).toThrow()
    expect(() => parseCliModelCatalog('antigravity_models', '--danger\tUnsafe')).toThrow()
  })

  it('returns only Kimi managed-subscription models and never provider credentials', () => {
    const raw = JSON.stringify({
      providers: {
        'managed:kimi-code': { type: 'kimi', apiKey: 'private-oauth-value', oauth: { token: 'secret' } },
        'Deep Infra': { type: 'openai', apiKey: 'private-api-key' },
      },
      models: {
        'kimi-code/k3': { provider: 'managed:kimi-code', model: 'k3', displayName: 'K3' },
        'kimi-code/k3-256k': { provider: 'managed:kimi-code', model: 'k3-256k', displayName: 'K3-256k' },
        'Deep Infra/moonshotai/Kimi-K3': { provider: 'Deep Infra', model: 'moonshotai/Kimi-K3',
          displayName: 'Kimi K3' },
      },
    })
    const parsed = parseCliModelCatalog('kimi_provider_json', raw)
    expect(parsed).toEqual([
      { modelId: 'kimi-code/k3', displayName: 'K3' },
      { modelId: 'kimi-code/k3-256k', displayName: 'K3-256k' },
    ])
    expect(JSON.stringify(parsed)).not.toMatch(/private|secret|Deep Infra/)
  })

  it('fails closed on duplicate, empty, oversized, or structurally invalid catalogs', () => {
    expect(() => parseCliModelCatalog('antigravity_models', 'm\tOne\nm\tTwo')).toThrow()
    expect(() => parseCliModelCatalog('antigravity_models', '')).toThrow()
    expect(() => parseCliModelCatalog('kimi_provider_json', '{broken')).toThrow()
    expect(() => parseCliModelCatalog('kimi_provider_json', JSON.stringify({ providers: {}, models: {} })))
      .toThrow()
  })
})
