/**
 * chart_facts_helpers.test.ts — SS N-339 / N-342 ayanamsha normaliser (platform side).
 *
 * Table-driven: every alias, case variants, whitespace, null/undefined/empty, "all", INVARIANT,
 * unknown, non-string. Pure unit test (no DB).
 */
import { describe, it, expect } from 'vitest'
import {
  AYANAMSHA_ALIAS_KEYS,
  AYANAMSHA_ALL,
  AYANAMSHA_SERVE_ORDER,
  InvalidAyanamshaError,
  PRIMARY_AYANAMSHA,
  STORED_AYANAMSHA_IDS,
  applyAyanamshaContract,
  applyAyanamshaContractForCapability,
  normalizeAyanamshaId,
  resolveAyanamshaArg,
  shouldInjectPrimaryAyanamsha,
} from './chart_facts_helpers'
import {
  DEFAULT_AYANAMSHA,
  INVARIANT_BEARING_CAPABILITY_URIS,
  KP_FRAME_CAPABILITY_URIS,
} from './registry/constants'

const LAHIRI = 'lahiri_chitrapaksha'

/** [input, expected normalised id (null = the "all" opt-out)] */
const ACCEPTED: Array<[unknown, string | null]> = [
  // omitted forms -> primary
  [undefined, LAHIRI],
  [null, LAHIRI],
  ['', LAHIRI],
  ['   ', LAHIRI],
  ['\t\n', LAHIRI],
  // Lahiri
  ['lahiri', LAHIRI],
  ['LAHIRI', LAHIRI],
  ['Lahiri', LAHIRI],
  ['  lahiri  ', LAHIRI],
  ['lahiri_chitra', LAHIRI],
  ['lahiri_chitrapaksha', LAHIRI],
  ['LAHIRI_CHITRAPAKSHA', LAHIRI],
  ['Lahiri Chitrapaksha', LAHIRI],
  // N-348: `chitrapaksha` is the standard name of Lahiri's ayanamsha
  ['chitrapaksha', LAHIRI],
  ['Chitrapaksha', LAHIRI],
  ['CHITRAPAKSHA', LAHIRI],
  [' chitrapaksha ', LAHIRI],
  ['lahiri-chitrapaksha', LAHIRI],
  // True Chitrapaksha
  ['true_chitra', 'true_chitra'],
  ['TRUE_CHITRA', 'true_chitra'],
  ['true_citra', 'true_chitra'],
  ['True_Citra', 'true_chitra'],
  ['true_chitra_paksha', 'true_chitra'],
  ['true_chitrapaksha', 'true_chitra'],
  ['true-chitra', 'true_chitra'],
  ['chitra', 'true_chitra'],
  ['true chitra', 'true_chitra'],
  ['True Chitra', 'true_chitra'],
  ['TRUE_CHITRAPAKSHA', 'true_chitra'],
  ['true chitrapaksha', 'true_chitra'],
  // Krishnamurti
  ['kp', 'krishnamurti'],
  ['KP', 'krishnamurti'],
  ['krishnamurti', 'krishnamurti'],
  ['Krishnamurti', 'krishnamurti'],
  ['krishnamurti_paddhati', 'krishnamurti'],
  [' KP ', 'krishnamurti'],
  // Raman
  ['raman', 'raman'],
  ['RAMAN', 'raman'],
  // Surya Siddhanta
  ['surya_siddhanta', 'surya_siddhanta_classical'],
  ['surya_siddhanta_classical', 'surya_siddhanta_classical'],
  ['Surya Siddhanta', 'surya_siddhanta_classical'],
  ['suryasiddhanta', 'surya_siddhanta_classical'],
  ['ss', 'surya_siddhanta_classical'],
  ['SS', 'surya_siddhanta_classical'],
  // sentinel
  ['INVARIANT', 'INVARIANT'],
  ['invariant', 'INVARIANT'],
  ['Invariant', 'INVARIANT'],
  // explicit opt-out
  ['all', null],
  ['ALL', null],
  [' All ', null],
]

const REJECTED: unknown[] = [
  'nonsense',
  'lahiri2',
  'kp_newcomb',
  'yukteshwar',
  'lahiri_chitrapaksha_x',
  '*',
  'all,lahiri',
  42,
  true,
  ['lahiri'],
  { id: 'lahiri' },
]

describe('serve-order constants', () => {
  it('PRIMARY_AYANAMSHA is the stored Lahiri id and aliases DEFAULT_AYANAMSHA', () => {
    expect(PRIMARY_AYANAMSHA).toBe(LAHIRI)
    expect(PRIMARY_AYANAMSHA).toBe(DEFAULT_AYANAMSHA)
  })

  it('AYANAMSHA_SERVE_ORDER is Lahiri first, then the project canonical order of the other four', () => {
    expect([...AYANAMSHA_SERVE_ORDER]).toEqual([
      'lahiri_chitrapaksha',
      'true_chitra',
      'krishnamurti',
      'raman',
      'surya_siddhanta_classical',
    ])
    expect(AYANAMSHA_SERVE_ORDER[0]).toBe(PRIMARY_AYANAMSHA)
    expect([...STORED_AYANAMSHA_IDS]).toEqual([...AYANAMSHA_SERVE_ORDER])
  })

  it('every stored id resolves to itself', () => {
    for (const id of AYANAMSHA_SERVE_ORDER) expect(normalizeAyanamshaId(id)).toBe(id)
  })

  it('every alias key resolves to a stored id or the INVARIANT sentinel (no alias maps to nothing)', () => {
    for (const key of AYANAMSHA_ALIAS_KEYS) {
      const r = resolveAyanamshaArg(key)
      expect(r.ok, key).toBe(true)
      if (r.ok) {
        expect([...AYANAMSHA_SERVE_ORDER, 'INVARIANT'], key).toContain(r.ayanamsha_id)
      }
    }
  })

  it('the KP-frame set names get_kp_cusps', () => {
    expect(KP_FRAME_CAPABILITY_URIS.has('marsys://tool/L1/get_kp_cusps')).toBe(true)
  })
})

describe('resolveAyanamshaArg / normalizeAyanamshaId (table)', () => {
  it.each(ACCEPTED)('%j -> %j', (input, expected) => {
    expect(normalizeAyanamshaId(input)).toBe(expected)
    const r = resolveAyanamshaArg(input)
    expect(r.ok).toBe(true)
    if (r.ok) {
      expect(r.ayanamsha_id).toBe(expected)
      const blank = input == null || (typeof input === 'string' && input.trim() === '')
      expect(r.source).toBe(blank ? 'omitted' : expected === null ? 'all' : 'explicit')
    }
  })

  it.each(REJECTED.map((v) => [v]))('%j is an error that lists every stored id', (input) => {
    const r = resolveAyanamshaArg(input)
    expect(r.ok).toBe(false)
    if (!r.ok) {
      expect(r.stored_ids).toEqual([...AYANAMSHA_SERVE_ORDER])
      for (const id of AYANAMSHA_SERVE_ORDER) expect(r.message).toContain(id)
      expect(r.message).toContain('INVARIANT')
      expect(r.message).toContain('"all"')
    }
    expect(() => normalizeAyanamshaId(input)).toThrow(InvalidAyanamshaError)
  })

  it('InvalidAyanamshaError carries a stable code, the received value and the stored ids', () => {
    try {
      normalizeAyanamshaId('bogus')
      throw new Error('expected throw')
    } catch (e) {
      expect(e).toBeInstanceOf(InvalidAyanamshaError)
      const err = e as InvalidAyanamshaError
      expect(err.code).toBe('invalid_ayanamsha_id')
      expect(err.received).toBe('bogus')
      expect(err.stored_ids).toEqual([...AYANAMSHA_SERVE_ORDER])
      expect(err.message).toContain('"bogus"')
    }
  })

  it('"all" is the exported sentinel constant', () => {
    expect(AYANAMSHA_ALL).toBe('all')
  })
})

describe('applyAyanamshaContract', () => {
  it('omitted -> Lahiri injected, other args untouched, input not mutated', () => {
    const input = { chart_id: 'c1', limit: 5 }
    const out = applyAyanamshaContract(input)
    expect(out).toEqual({ chart_id: 'c1', limit: 5, ayanamsha_id: LAHIRI })
    expect(input).toEqual({ chart_id: 'c1', limit: 5 })
  })

  it.each([[null], [''], ['  ']])('blank %j is treated as omitted', (v) => {
    expect(applyAyanamshaContract({ ayanamsha_id: v })['ayanamsha_id']).toBe(LAHIRI)
  })

  it.each([['LAHIRI'], ['lahiri'], [' Lahiri ']])('%j -> lahiri_chitrapaksha', (v) => {
    expect(applyAyanamshaContract({ ayanamsha_id: v })['ayanamsha_id']).toBe(LAHIRI)
  })

  it('kp -> krishnamurti; INVARIANT passes verbatim', () => {
    expect(applyAyanamshaContract({ ayanamsha_id: 'kp' })['ayanamsha_id']).toBe('krishnamurti')
    expect(applyAyanamshaContract({ ayanamsha_id: 'invariant' })['ayanamsha_id']).toBe('INVARIANT')
  })

  it('"all" removes the filter and marks ayanamsha_scope:"all" (explicit opt-out)', () => {
    const out = applyAyanamshaContract({ chart_id: 'c1', ayanamsha_id: 'ALL' })
    expect('ayanamsha_id' in out).toBe(false)
    expect(out['ayanamsha_scope']).toBe('all')
    expect(out['chart_id']).toBe('c1')
  })

  it('unknown id throws InvalidAyanamshaError (never a silent zero-row id)', () => {
    expect(() => applyAyanamshaContract({ ayanamsha_id: 'nope' })).toThrow(InvalidAyanamshaError)
  })

  it('inject:false (KP frame): omitted stays omitted, explicit is still normalised, unknown still throws', () => {
    expect('ayanamsha_id' in applyAyanamshaContract({}, { inject: false })).toBe(false)
    expect('ayanamsha_id' in applyAyanamshaContract({ ayanamsha_id: '' }, { inject: false })).toBe(false)
    expect(applyAyanamshaContract({ ayanamsha_id: 'KP' }, { inject: false })['ayanamsha_id']).toBe('krishnamurti')
    expect(applyAyanamshaContract({ ayanamsha_id: 'lahiri' }, { inject: false })['ayanamsha_id']).toBe(LAHIRI)
    expect(() => applyAyanamshaContract({ ayanamsha_id: 'zzz' }, { inject: false })).toThrow(InvalidAyanamshaError)
  })
})

describe('applyAyanamshaContractForCapability', () => {
  const withAya = { uri: 'marsys://tool/L1/get_positions', input_schema: { chart_id: {}, ayanamsha_id: {} } }
  const noAya = { uri: 'marsys://tool/L5/lel_query', input_schema: { chart_id: {} } }

  it('capability whose schema defines ayanamsha_id -> injected', () => {
    expect(applyAyanamshaContractForCapability(withAya, { chart_id: 'c' })['ayanamsha_id']).toBe(LAHIRI)
  })

  it('capability without ayanamsha_id in its schema -> args returned untouched (same object), even for a bad value', () => {
    const args = { chart_id: 'c', ayanamsha_id: 'garbage' }
    expect(applyAyanamshaContractForCapability(noAya, args)).toBe(args)
    const none = { uri: 'marsys://tool/L0/x' }
    expect(applyAyanamshaContractForCapability(none, args)).toBe(args)
  })

  it('KP-frame capability -> no injection on omission', () => {
    const kp = { uri: 'marsys://tool/L1/get_kp_cusps', input_schema: { chart_id: {}, ayanamsha_id: {} } }
    expect('ayanamsha_id' in applyAyanamshaContractForCapability(kp, { chart_id: 'c' })).toBe(false)
    expect(applyAyanamshaContractForCapability(kp, { chart_id: 'c', ayanamsha_id: 'kp' })['ayanamsha_id']).toBe('krishnamurti')
  })
})

describe('shouldInjectPrimaryAyanamsha (KP frame, INVARIANT-bearing, INVARIANT categories)', () => {
  const plain = { uri: 'marsys://tool/L1/get_dignity' }

  it('an ordinary capability is injected', () => {
    expect(shouldInjectPrimaryAyanamsha(plain, {})).toBe(true)
    expect(shouldInjectPrimaryAyanamsha(plain, { categories: ['graha_position'] })).toBe(true)
  })

  it('KP-frame capabilities are never injected', () => {
    for (const uri of KP_FRAME_CAPABILITY_URIS) expect(shouldInjectPrimaryAyanamsha({ uri }, {})).toBe(false)
  })

  it('INVARIANT-bearing capabilities (their default pages hold ayanamsha-independent rows) are not injected', () => {
    for (const uri of INVARIANT_BEARING_CAPABILITY_URIS) expect(shouldInjectPrimaryAyanamsha({ uri }, {})).toBe(false)
    expect(INVARIANT_BEARING_CAPABILITY_URIS.has('marsys://tool/L1/get_panchanga')).toBe(true)
  })

  it.each([
    [{ categories: ['nakshatra_cross_ayanamsha'] }],
    [{ categories: ['graha_position', 'nakshatra_cross_ayanamsha'] }],
    [{ categories: ['panchanga_tithi'] }],
    [{ category: 'panchanga_vara' }],
    [{ categories: ['graha_shadbala_naisargika'] }],
  ])('a call naming an INVARIANT-stored category (%j) is not narrowed to one ayanamsha', (args) => {
    expect(shouldInjectPrimaryAyanamsha(plain, args)).toBe(false)
  })

  it('applyAyanamshaContractForCapability honours it: omitted stays omitted, explicit is still normalised', () => {
    const cap = { uri: 'marsys://tool/L1/get_positions', input_schema: { ayanamsha_id: {} } }
    const inv = { chart_id: 'c', categories: ['nakshatra_cross_ayanamsha'] }
    expect('ayanamsha_id' in applyAyanamshaContractForCapability(cap, inv)).toBe(false)
    expect(applyAyanamshaContractForCapability(cap, { ...inv, ayanamsha_id: 'LAHIRI' })['ayanamsha_id']).toBe(LAHIRI)
    expect(applyAyanamshaContractForCapability(cap, { chart_id: 'c' })['ayanamsha_id']).toBe(LAHIRI)
  })

  it('opts.inject:false (MCP capability route): omitted stays omitted; aliases, "all" and unknown ids are still handled', () => {
    const cap = { uri: 'marsys://tool/L1/get_dignity', input_schema: { ayanamsha_id: {} } }
    expect('ayanamsha_id' in applyAyanamshaContractForCapability(cap, { chart_id: 'c' }, { inject: false })).toBe(false)
    expect(applyAyanamshaContractForCapability(cap, { ayanamsha_id: 'kp' }, { inject: false })['ayanamsha_id']).toBe('krishnamurti')
    expect(applyAyanamshaContractForCapability(cap, { ayanamsha_id: 'all' }, { inject: false })['ayanamsha_scope']).toBe('all')
    expect(() => applyAyanamshaContractForCapability(cap, { ayanamsha_id: 'zz' }, { inject: false })).toThrow(InvalidAyanamshaError)
  })
})
