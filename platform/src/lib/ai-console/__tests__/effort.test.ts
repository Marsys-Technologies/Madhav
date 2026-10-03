import { describe, expect, it } from 'vitest'
import { cliEffortLevels, providerEffortLevels } from '../effort'

describe('AI Console effort capability', () => {
  it('only exposes direct provider effort for known reasoning-capable model families', () => {
    expect(providerEffortLevels('openai', 'gpt-5.5')).toEqual(['low', 'medium', 'high'])
    expect(providerEffortLevels('anthropic', 'claude-sonnet-4-6')).toEqual(['low', 'medium', 'high'])
    expect(providerEffortLevels('google', 'gemini-3.1-pro-preview')).toEqual(['low', 'medium', 'high'])
    expect(providerEffortLevels('google', 'gemini-3-pro-preview')).toEqual([])
    expect(providerEffortLevels('openai', 'gpt-4o')).toEqual([])
  })

  it('does not present a guessed effort for a CLI built-in default or Kimi ACP', () => {
    expect(cliEffortLevels('codex', null)).toEqual([])
    expect(cliEffortLevels('claude_code', 'claude-sonnet-4-6')).toEqual(['low', 'medium', 'high'])
    expect(cliEffortLevels('gemini_antigravity', 'gemini-3.8-flash-low')).toEqual([])
    expect(cliEffortLevels('kimi_code', 'kimi-code/k3-256k')).toEqual([])
  })

  it('only forwards OpenRouter effort for known upstream families', () => {
    expect(providerEffortLevels('openrouter', 'openai/gpt-5.5')).toEqual(['low', 'medium', 'high'])
    expect(providerEffortLevels('openrouter', 'unknown/new-model')).toEqual([])
  })
})
