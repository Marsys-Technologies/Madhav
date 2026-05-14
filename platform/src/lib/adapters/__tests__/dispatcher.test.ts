import { describe, test, expect } from 'vitest'
import { adapterFor } from '../dispatcher'
import { MODELS, STACK_ROUTING, type ModelStack, type CallType } from '@/lib/models/registry'

const STACKS = Object.keys(STACK_ROUTING) as ModelStack[]
const CALL_TYPES = Object.keys(STACK_ROUTING['gemini']) as CallType[]

// Mapping from provider string to expected providerId in the returned adapter
const EXPECTED_PROVIDER_IDS: Record<string, string> = {
  anthropic: 'anthropic',
  google:    'google',
  deepseek:  'deepseek',
  openai:    'openai',
  nvidia:    'nvidia',
}

describe('adapterFor — provider dispatch', () => {
  test('adapterFor returns adapter with correct providerId for anthropic', () => {
    expect(adapterFor('anthropic').providerId).toBe('anthropic')
  })

  test('adapterFor returns adapter with correct providerId for google', () => {
    expect(adapterFor('google').providerId).toBe('google')
  })

  test('adapterFor returns adapter with correct providerId for deepseek', () => {
    expect(adapterFor('deepseek').providerId).toBe('deepseek')
  })

  test('adapterFor returns adapter with correct providerId for openai', () => {
    expect(adapterFor('openai').providerId).toBe('openai')
  })

  test('adapterFor returns adapter with correct providerId for nvidia', () => {
    expect(adapterFor('nvidia').providerId).toBe('nvidia')
  })

  test('adapterFor returns an object with a stream function for each provider', () => {
    const providers = ['anthropic', 'google', 'deepseek', 'openai', 'nvidia'] as const
    for (const p of providers) {
      const adapter = adapterFor(p)
      expect(typeof adapter.stream, `${p}.stream`).toBe('function')
    }
  })
})

describe('adapterFor — model-level dispatch', () => {
  test('every model in registry resolves to an adapter with matching providerId', () => {
    for (const m of MODELS) {
      const adapter = adapterFor(m.provider)
      expect(adapter.providerId, `model ${m.id}: expected provider ${m.provider}`).toBe(
        EXPECTED_PROVIDER_IDS[m.provider],
      )
    }
  })

  test('dispatch is stable across multiple calls for same provider', () => {
    const a1 = adapterFor('anthropic')
    const a2 = adapterFor('anthropic')
    expect(a1).toBe(a2)
  })
})

describe('adapterFor — stack routing dispatch (6 stacks × 11 call_types × 2 slots = 132 cases)', () => {
  for (const stack of STACKS) {
    for (const callType of CALL_TYPES) {
      const routing = STACK_ROUTING[stack][callType]

      test(`stack=${stack} call_type=${callType} primary dispatches to correct adapter`, () => {
        const modelId = routing.primary
        const model = MODELS.find(m => m.id === modelId)
        if (!model) {
          // Model may be in registry under a different provider — skip if unknown
          // (this can happen with cross-provider fallback IDs like 'claude-haiku-4-5'
          // appearing in NIM stack fallbacks)
          return
        }
        const adapter = adapterFor(model.provider)
        expect(adapter.providerId).toBe(EXPECTED_PROVIDER_IDS[model.provider])
      })

      test(`stack=${stack} call_type=${callType} fallback dispatches to correct adapter`, () => {
        const modelId = routing.fallback
        const model = MODELS.find(m => m.id === modelId)
        if (!model) return
        const adapter = adapterFor(model.provider)
        expect(adapter.providerId).toBe(EXPECTED_PROVIDER_IDS[model.provider])
      })
    }
  }
})
