/**
 * Ayanamsha edit policy (SS N-319): env parsing (default block_all, validated,
 * unknown -> block_all and logged) and the pure edit decision.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  AYANAMSHA_EDIT_BLOCKED,
  AYANAMSHA_EDIT_NEEDS_CONFIRMATION,
  DEFAULT_AYANAMSHA_EDIT_POLICY,
  decideAyanamshaEdit,
  type AyanamshaEditPolicy,
} from '../ayanamshaEditGuard'
import { AYANAMSHA_EDIT_POLICY_ENV, getAyanamshaEditPolicy, parseAyanamshaEditPolicy } from '../ayanamshaEditPolicy'

const env = (values: Record<string, string>) => values as unknown as NodeJS.ProcessEnv

afterEach(() => vi.restoreAllMocks())

describe('parseAyanamshaEditPolicy', () => {
  it('defaults to block_all', () => {
    expect(DEFAULT_AYANAMSHA_EDIT_POLICY).toBe('block_all')
    expect(parseAyanamshaEditPolicy(undefined)).toBe('block_all')
    expect(parseAyanamshaEditPolicy(null)).toBe('block_all')
    expect(parseAyanamshaEditPolicy('')).toBe('block_all')
    expect(parseAyanamshaEditPolicy('   ')).toBe('block_all')
  })

  it.each(['block_all', 'warn', 'off'])('accepts %s', (value) => {
    expect(parseAyanamshaEditPolicy(value)).toBe(value)
  })

  it('ignores case and surrounding whitespace', () => {
    expect(parseAyanamshaEditPolicy(' WARN ')).toBe('warn')
    expect(parseAyanamshaEditPolicy('Off')).toBe('off')
  })

  it.each(['allow', 'false', '0', 'block', 'warn,off', 'on'])('maps the unknown value %j to block_all and reports it', (value) => {
    const seen: string[] = []
    expect(parseAyanamshaEditPolicy(value, (raw) => seen.push(raw))).toBe('block_all')
    expect(seen).toEqual([value])
  })

  it('does not report valid or empty values', () => {
    const seen: string[] = []
    for (const v of ['warn', '', undefined, 'off']) parseAyanamshaEditPolicy(v, (raw) => seen.push(raw))
    expect(seen).toEqual([])
  })
})

describe('getAyanamshaEditPolicy', () => {
  it('reads exactly CHART_AYANAMSHA_EDIT_POLICY', () => {
    expect(AYANAMSHA_EDIT_POLICY_ENV).toBe('CHART_AYANAMSHA_EDIT_POLICY')
    expect(getAyanamshaEditPolicy(env({ CHART_AYANAMSHA_EDIT_POLICY: 'warn' }))).toBe('warn')
    expect(getAyanamshaEditPolicy(env({ SOMETHING_ELSE: 'off' }))).toBe('block_all')
  })

  it('logs an unknown value once per read and falls back to block_all', () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    expect(getAyanamshaEditPolicy(env({ CHART_AYANAMSHA_EDIT_POLICY: 'sure' }))).toBe('block_all')
    expect(log).toHaveBeenCalledTimes(1)
    expect(String(log.mock.calls[0][0])).toContain('CHART_AYANAMSHA_EDIT_POLICY')
  })

  it('does not log for a valid or unset value', () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    getAyanamshaEditPolicy(env({}))
    getAyanamshaEditPolicy(env({ CHART_AYANAMSHA_EDIT_POLICY: 'off' }))
    expect(log).not.toHaveBeenCalled()
  })
})

describe('decideAyanamshaEdit', () => {
  const policies: AyanamshaEditPolicy[] = ['block_all', 'warn', 'off']

  it.each(policies)('%s: no ayanamsha change always proceeds, whatever else changed', (policy) => {
    for (const otherFieldsChanged of [false, true]) {
      for (const confirmDestructive of [false, true]) {
        expect(decideAyanamshaEdit({ policy, ayanamshasChanged: false, otherFieldsChanged, confirmDestructive })).toEqual({ action: 'proceed' })
      }
    }
  })

  it('off proceeds on an ayanamsha change', () => {
    expect(decideAyanamshaEdit({ policy: 'off', ayanamshasChanged: true, otherFieldsChanged: true, confirmDestructive: false })).toEqual({ action: 'proceed' })
  })

  it('block_all refuses with AYANAMSHA_EDIT_BLOCKED whether or not confirmed', () => {
    for (const confirmDestructive of [false, true]) {
      const verdict = decideAyanamshaEdit({ policy: 'block_all', ayanamshasChanged: true, otherFieldsChanged: false, confirmDestructive })
      expect(verdict).toMatchObject({ action: 'refuse', code: AYANAMSHA_EDIT_BLOCKED })
    }
  })

  it('block_all names the ayanamsha, and says nothing was saved when other fields came with it', () => {
    const alone = decideAyanamshaEdit({ policy: 'block_all', ayanamshasChanged: true, otherFieldsChanged: false, confirmDestructive: false })
    const mixed = decideAyanamshaEdit({ policy: 'block_all', ayanamshasChanged: true, otherFieldsChanged: true, confirmDestructive: false })
    expect(alone.action === 'refuse' && alone.message).toMatch(/^The ayanamsha of an existing chart can't be changed here\. Contact support/)
    expect(mixed.action === 'refuse' && mixed.message).toMatch(/ayanamsha[\s\S]*nothing was saved/i)
  })

  it('warn refuses without the flag and proceeds with it', () => {
    expect(decideAyanamshaEdit({ policy: 'warn', ayanamshasChanged: true, otherFieldsChanged: false, confirmDestructive: false })).toMatchObject({
      action: 'refuse',
      code: AYANAMSHA_EDIT_NEEDS_CONFIRMATION,
    })
    expect(decideAyanamshaEdit({ policy: 'warn', ayanamshasChanged: true, otherFieldsChanged: true, confirmDestructive: true })).toEqual({ action: 'proceed' })
  })
})
