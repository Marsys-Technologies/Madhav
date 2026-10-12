/**
 * Lahiri-primary PR-5 (SS N-339 / N-348): the policy text shown at /cockpit/command-center and the
 * contract default ayanamsha ids say Lahiri (lahiri_chitrapaksha) is canonical and PRIMARY and the
 * other four stored ayanamshas are cross-checks. The old wording (canonical = True Chitrapaksha,
 * Lahiri = "reference", the non-stored `kp_newcomb`) must be gone.
 */
import { describe, it, expect } from 'vitest'
import { AYANAMSHA_REGISTRY, GATE_REGISTRY, getGateSpec } from '../gate_registry'
import { DEFAULT_AYANAMSHA_BY_ROLE } from '@/lib/contract/types'
import { AYANAMSHA_SERVE_ORDER } from '@/lib/retrieval/registry/constants'
import { normalizeAyanamshaId } from '@/lib/retrieval/chart_facts_helpers'

const ayanamshaText = [
  ...AYANAMSHA_REGISTRY.map((r) => r.source),
  ...GATE_REGISTRY.filter((g) => g.group === 'ayanamsha').map((g) => g.description),
].join('\n')

describe('gate_registry ayanamsha policy text', () => {
  it('keeps the three role keys and gate names (stored in the DB, display only changes)', () => {
    expect(AYANAMSHA_REGISTRY.map((r) => r.role)).toEqual(['canonical', 'kp', 'reference'])
    expect(AYANAMSHA_REGISTRY.map((r) => r.gate)).toEqual([
      'AYANAMSHA_CANONICAL_ENABLED', 'AYANAMSHA_KP_ENABLED', 'AYANAMSHA_REFERENCE_ENABLED',
    ])
  })

  it('canonical row: Lahiri (lahiri_chitrapaksha), canonical and PRIMARY', () => {
    const row = AYANAMSHA_REGISTRY.find((r) => r.role === 'canonical')!
    expect(row.source).toContain('Lahiri')
    expect(row.source).toContain('lahiri_chitrapaksha')
    expect(row.source).toMatch(/PRIMARY/)
    const spec = getGateSpec('AYANAMSHA_CANONICAL_ENABLED')
    expect(spec.description).toContain('lahiri_chitrapaksha')
    expect(spec.description).toMatch(/canonical and PRIMARY/)
    expect(spec.description).toMatch(/CANNOT be disabled/)
  })

  it('reference row is the cross-check set naming the four other stored ayanamshas', () => {
    const row = AYANAMSHA_REGISTRY.find((r) => r.role === 'reference')!
    expect(row.source).toMatch(/cross-check/i)
    for (const id of AYANAMSHA_SERVE_ORDER.slice(1)) expect(row.source).toContain(id)
    expect(row.source).not.toContain('Lahiri')
    expect(getGateSpec('AYANAMSHA_REFERENCE_ENABLED').description).toMatch(/cross-check/i)
  })

  it('kp row is the KP frame on Krishnamurti, not a "KP-Newcomb" ayanamsha', () => {
    const row = AYANAMSHA_REGISTRY.find((r) => r.role === 'kp')!
    expect(row.source).toContain('KP frame')
    expect(row.source).toContain('krishnamurti')
  })

  it('the old wording is gone', () => {
    expect(ayanamshaText).not.toMatch(/True Chitrapaksha/)
    expect(ayanamshaText).not.toMatch(/Newcomb/i)
    expect(ayanamshaText).not.toMatch(/Reference \(Lahiri\)/)
    expect(ayanamshaText).not.toMatch(/kp_newcomb/)
  })
})

describe('contract DEFAULT_AYANAMSHA_BY_ROLE', () => {
  it('canonical and reference default to the stored Lahiri id; kp to the stored Krishnamurti id', () => {
    expect(DEFAULT_AYANAMSHA_BY_ROLE.canonical).toBe('lahiri_chitrapaksha')
    expect(DEFAULT_AYANAMSHA_BY_ROLE.reference).toBe('lahiri_chitrapaksha')
    expect(DEFAULT_AYANAMSHA_BY_ROLE.kp).toBe('krishnamurti')
  })

  it('kp_newcomb is removed and every default is a STORED id (round-trips through the PR-1 normaliser)', () => {
    const values = Object.values(DEFAULT_AYANAMSHA_BY_ROLE)
    expect(values).not.toContain('kp_newcomb')
    for (const v of values) {
      expect(AYANAMSHA_SERVE_ORDER).toContain(v)
      expect(normalizeAyanamshaId(v)).toBe(v)
    }
  })
})
