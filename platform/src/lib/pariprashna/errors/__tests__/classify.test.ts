/**
 * P2-G — pins `classifyPariprashnaError`'s output to the design plan's §7.5
 * table VERBATIM (exact string equality, never a loose `.toContain()`).
 * Source: PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §7.5.
 */
import { describe, it, expect } from 'vitest'
import { classifyPariprashnaError } from '../classify'

describe('classifyPariprashnaError — §7.5 verbatim copy', () => {
  it('rate_limit', () => {
    const e = classifyPariprashnaError('RATE_LIMIT_429')
    expect(e.kind).toBe('rate_limit')
    expect(e.bandLabel).toBe('A moment — the provider asks us to slow')
    expect(e.sentence).toBe('Nothing was lost. Try again shortly, or switch models.')
    expect(e.actions).toEqual(['retry', 'switch_model'])
  })

  it('model_overload — generic provider (honest gap, no fabricated provider name)', () => {
    const e = classifyPariprashnaError('MODEL_OVERLOADED_503')
    expect(e.kind).toBe('model_overload')
    expect(e.bandLabel).toBe('The model is overloaded')
    expect(e.sentence).toBe('The provider is under load. Your question is kept; another model can take it.')
    expect(e.actions).toEqual(['retry', 'switch_model'])
  })

  it('model_overload — with a real provider label interpolated', () => {
    const e = classifyPariprashnaError('OVERLOAD', { providerLabel: 'Anthropic' })
    expect(e.sentence).toBe('Anthropic is under load. Your question is kept; another model can take it.')
  })

  it('timeout', () => {
    const e = classifyPariprashnaError('DEADLINE_EXCEEDED')
    expect(e.kind).toBe('timeout')
    expect(e.bandLabel).toBe('The reading ran long and was cut short')
    expect(e.sentence).toBe('What arrived is above. The reading can be continued.')
    expect(e.actions).toEqual(['continue', 'retry'])
  })

  it('network — terminal (default; retries exhausted or moot)', () => {
    const e = classifyPariprashnaError('NETWORK_RESUME_EXHAUSTED')
    expect(e.kind).toBe('network')
    expect(e.bandLabel).toBe('The connection was lost')
    expect(e.sentence).toBe('What arrived is above; nothing was altered.')
    expect(e.actions).toEqual(['continue'])
  })

  it('network — mid-attempt reuses the §7.8 RECONNECTING… edge-state label', () => {
    const e = classifyPariprashnaError('NETWORK_DROPPED', { networkExhausted: false })
    expect(e.kind).toBe('network')
    expect(e.bandLabel).toBe('Reconnecting…')
    expect(e.actions).toEqual(['continue'])
  })

  it('auth — native (default): renew in settings', () => {
    const e = classifyPariprashnaError('AUTH_401')
    expect(e.kind).toBe('auth')
    expect(e.bandLabel).toBe('This model needs its key renewed')
    expect(e.sentence).toBe('Renew in settings.')
    expect(e.actions).toEqual(['settings'])
  })

  it('auth — guest: another model can take the question', () => {
    const e = classifyPariprashnaError('FORBIDDEN_403', { audience: 'guest' })
    expect(e.kind).toBe('auth')
    expect(e.bandLabel).toBe('This model is unavailable')
    expect(e.sentence).toBe('Another model can take the question.')
    expect(e.actions).toEqual(['switch_model'])
  })

  it('unknown — never blames the user, states what was preserved', () => {
    const e = classifyPariprashnaError('SOME_UNMAPPED_CODE')
    expect(e.kind).toBe('unknown')
    expect(e.bandLabel).toBe('Something failed on our side')
    expect(e.sentence).toBe('Not the chart, not your question — the plumbing. It is logged.')
    expect(e.actions).toEqual(['retry'])
  })

  it('never leaks the raw code/message into the sentence (§7.5: never raw provider error strings)', () => {
    const e = classifyPariprashnaError('anthropic_api_internal_trace_id_9f8e7d')
    expect(e.sentence).not.toContain('anthropic_api_internal_trace_id_9f8e7d')
  })
})
