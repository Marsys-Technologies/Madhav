import { describe, expect, it } from 'vitest'
import { configurationKindMatchesRoles } from '../configuration-kind'

const api = (connectionId: string) => ({ kind: 'provider_model' as const, connectionId, modelId: 'tested-model' })
const cli = (cliId: 'claude_code' | 'gemini_antigravity') => ({ kind: 'local_cli' as const, cliId, modelId: null })
const roles = (synthesizer: ReturnType<typeof api> | ReturnType<typeof cli>, planner = synthesizer,
  deep_planner = synthesizer, worker = synthesizer) => ({ synthesizer, planner, deep_planner, worker })

describe('configuration kind boundary', () => {
  it('allows a provider preset only when all four roles use its connection', () => {
    expect(configurationKindMatchesRoles('provider_preset', roles(api('one')), 'one', null)).toBe(true)
    expect(configurationKindMatchesRoles('provider_preset', roles(api('one'), api('two')), 'one', null)).toBe(false)
    expect(configurationKindMatchesRoles('provider_preset', roles(api('one'), cli('claude_code')), 'one', null)).toBe(false)
  })

  it('allows a CLI preset only when all four roles use its CLI', () => {
    expect(configurationKindMatchesRoles('cli_preset', roles(cli('claude_code')), null, 'claude_code')).toBe(true)
    expect(configurationKindMatchesRoles('cli_preset', roles(cli('claude_code'), cli('gemini_antigravity')), null, 'claude_code')).toBe(false)
  })

  it('keeps custom API and CLI configurations separate', () => {
    expect(configurationKindMatchesRoles('custom_api', roles(api('one'), api('two')), null, null)).toBe(true)
    expect(configurationKindMatchesRoles('custom_api', roles(api('one'), cli('claude_code')), null, null)).toBe(false)
    expect(configurationKindMatchesRoles('custom_cli', roles(cli('claude_code'), cli('gemini_antigravity')), null, null)).toBe(true)
    expect(configurationKindMatchesRoles('custom_cli', roles(cli('claude_code'), api('one')), null, null)).toBe(false)
  })
})
