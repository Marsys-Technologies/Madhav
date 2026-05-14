import { describe, it, expect } from 'vitest'
import { MODELS, supports } from '@/lib/models/registry'

describe('Model registry — OpenAI entry', () => {
  const gpt = MODELS.find(m => m.provider === 'openai')

  it('OpenAI supports tool-use', () => {
    expect(supports(gpt!.id, 'tool-use')).toBe(true)
  })
})
