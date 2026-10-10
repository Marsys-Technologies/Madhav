/**
 * ayanamsha_cross_check.test.ts — golden tests for the labelled cross-check envelope (Lahiri-primary PR-3).
 */
import { describe, it, expect } from 'vitest'
import {
  buildAyanamshaCrossCheck, identityFactSpecs, isCrossCheckUnavailable, CROSS_CHECK_KEY, CROSS_CHECK_HEADING,
  CROSS_CHECK_AGREE_ALL_LINE, type CrossCheckInputRow, type AyanamshaCrossCheckAvailable,
} from '../ayanamsha_cross_check'
import { AYANAMSHA_SERVE_ORDER, PRIMARY_AYANAMSHA } from '../registry/constants'
import * as budget from '../../../../../platform-mcp/src/lib/response_budget'

const FACTS = identityFactSpecs(['lagna_sign', 'moon_sign', 'moon_nakshatra', 'maha_lord'])
const BASE: Record<string, string> = {
  lagna_sign: 'Aries', moon_sign: 'Aquarius', moon_nakshatra: 'Purva Bhadrapada', maha_lord: 'Venus',
}

/** Rows for the given ayanamshas; `override` patches one ayanamsha's values; rows are emitted krishnamurti-first on purpose. */
function rows(ayas: readonly string[], override: Record<string, Record<string, string | null>> = {}, degrees = false): CrossCheckInputRow[] {
  const alpha = [...ayas].sort()
  const out: CrossCheckInputRow[] = []
  for (const a of alpha) {
    for (const [k, v] of Object.entries(BASE)) {
      const value = override[a] && k in override[a]! ? override[a]![k]! : v
      out.push({ ayanamsha_id: a, fact_key: k, value, ...(degrees ? { degrees: 10 + alpha.indexOf(a) } : {}) })
    }
  }
  return out
}
const ok = (c: ReturnType<typeof buildAyanamshaCrossCheck>): AyanamshaCrossCheckAvailable => {
  if (isCrossCheckUnavailable(c)) throw new Error('unexpected not_available: ' + c.reason)
  return c
}

describe('buildAyanamshaCrossCheck', () => {
  it('names exactly four others, in serve order, with the primary first and never among them', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.primary_id).toBe('lahiri_chitrapaksha')
    expect(c.primary.ayanamsha_id).toBe('lahiri_chitrapaksha')
    expect(c.others.map((o) => o.ayanamsha_id)).toEqual(['true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical'])
    expect(c.others.every((o) => o.label.length > 0)).toBe(true)
    expect(c.heading).toBe(CROSS_CHECK_HEADING)
    expect(CROSS_CHECK_KEY).toBe('ayanamsha_cross_check')
  })

  it('primary values equal the primary-only answer (the cross-check never alters the primary)', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, { raman: { moon_sign: 'Pisces' } }), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(Object.fromEntries(Object.entries(c.primary.values).map(([k, v]) => [k, v.value]))).toEqual(BASE)
  })

  it('all five categorically equal -> the single line "Agrees across all five ayanamshas"', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.agreement).toBe('all_agree')
    expect(c.summary).toBe(CROSS_CHECK_AGREE_ALL_LINE)
    expect(c.summary).toBe('Agrees across all five ayanamshas')
    expect(c.others.every((o) => o.status === 'agrees')).toBe(true)
    expect(c.density).toEqual({ stored_ayanamshas: 5, compared_facts: 4, dissenting_ayanamshas: 0 })
  })

  it('degrees are shown and NEVER compared: different degrees, same signs -> still "Agrees across all five"', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, {}, true), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.agreement).toBe('all_agree')
    expect(c.summary).toBe('Agrees across all five ayanamshas')
    // degrees are 10 + alphabetical index of the ayanamsha id: lahiri 11, true_chitra 14, surya 13
    expect(c.primary.values['moon_sign']!.degrees).toBe(11)
    expect(c.others[0]!.values!['moon_sign']!.degrees).toBe(14)
    expect(c.others[3]!.values!['moon_sign']!.degrees).toBe(13)
  })

  it('a dissenting ayanamsha is named with its value, under the heading; the others stay agreeing', () => {
    const c = ok(buildAyanamshaCrossCheck(
      rows(AYANAMSHA_SERVE_ORDER, { raman: { moon_sign: 'Pisces', moon_nakshatra: 'Uttara Bhadrapada' } }), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.heading).toBe('Cross-check, not the reading')
    expect(c.agreement).toBe('dissent')
    expect(c.summary).toBe('Dissent: Raman: Moon sign Pisces (primary Aquarius), Moon nakshatra Uttara Bhadrapada (primary Purva Bhadrapada)')
    const raman = c.others.find((o) => o.ayanamsha_id === 'raman')!
    expect(raman.status).toBe('dissents')
    expect(raman.dissenting!.map((d) => [d.fact_key, d.value, d.primary_value])).toEqual([
      ['moon_sign', 'Pisces', 'Aquarius'], ['moon_nakshatra', 'Uttara Bhadrapada', 'Purva Bhadrapada'],
    ])
    expect(c.others.filter((o) => o.status === 'agrees').map((o) => o.ayanamsha_id)).toEqual(['true_chitra', 'krishnamurti', 'surya_siddhanta_classical'])
    expect(c.summary).not.toContain('Agrees across all five')
  })

  it('a dissent is anchored on the PRIMARY: Lahiri is never listed as divergent when it is the odd one out', () => {
    const odd: Record<string, Record<string, string | null>> = { lahiri_chitrapaksha: { moon_sign: 'Capricorn' } }
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, odd), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.others.map((o) => o.ayanamsha_id)).not.toContain('lahiri_chitrapaksha')
    expect(c.others.every((o) => o.status === 'dissents')).toBe(true) // four others differ FROM Lahiri
    expect(c.primary.values['moon_sign']!.value).toBe('Capricorn')
  })

  it('serve order is independent of input row order', () => {
    const a = buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER), PRIMARY_AYANAMSHA, { facts: FACTS })
    const b = buildAyanamshaCrossCheck([...rows(AYANAMSHA_SERVE_ORDER)].reverse(), PRIMARY_AYANAMSHA, { facts: FACTS })
    expect(JSON.stringify(a)).toBe(JSON.stringify(b))
  })

  it('categorical comparison ignores case and spacing but never numeric closeness', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, { raman: { moon_sign: ' aquarius ' } }), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.agreement).toBe('all_agree')
  })

  it('single-ayanamsha chart -> not_available/single_ayanamsha_chart, never "1/1"', () => {
    const c = buildAyanamshaCrossCheck(rows(['lahiri_chitrapaksha']), PRIMARY_AYANAMSHA, { facts: FACTS })
    expect(c).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
    expect(JSON.stringify(c)).not.toMatch(/1\/1|agree/i)
    expect(buildAyanamshaCrossCheck([], PRIMARY_AYANAMSHA, { facts: FACTS })).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
  })

  it('INVARIANT and unknown ids are not ayanamshas: Lahiri + INVARIANT is still a single-ayanamsha chart', () => {
    const r = [...rows(['lahiri_chitrapaksha']), ...rows(['INVARIANT', 'kp_newcomb'])]
    expect(buildAyanamshaCrossCheck(r, PRIMARY_AYANAMSHA, { facts: FACTS })).toMatchObject({ not_available: true, reason: 'single_ayanamsha_chart' })
  })

  it('primary not stored -> not_available/primary_ayanamsha_not_stored', () => {
    const c = buildAyanamshaCrossCheck(rows(['true_chitra', 'raman']), PRIMARY_AYANAMSHA, { facts: FACTS })
    expect(c).toMatchObject({ not_available: true, reason: 'primary_ayanamsha_not_stored' })
  })

  it('a partial chart never claims "all five": it says which ayanamshas have no rows', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(['lahiri_chitrapaksha', 'true_chitra', 'raman']), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.agreement).toBe('agree_among_stored')
    expect(c.summary).toBe('Agrees across the three stored ayanamshas (no rows for: Krishnamurti, Surya Siddhanta)')
    expect(c.others.map((o) => [o.ayanamsha_id, o.status])).toEqual([
      ['true_chitra', 'agrees'], ['krishnamurti', 'no_rows'], ['raman', 'agrees'], ['surya_siddhanta_classical', 'no_rows'],
    ])
  })

  it('an unread value is never agreement: status incomplete, and the line says so', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, { krishnamurti: { moon_nakshatra: null } }), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.agreement).toBe('incomplete')
    expect(c.summary).not.toContain('Agrees across all five')
    expect(c.others.find((o) => o.ayanamsha_id === 'krishnamurti')!.status).toBe('incomplete')
  })

  it('an unread PRIMARY value cannot be confirmed either', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, { lahiri_chitrapaksha: { maha_lord: null } }), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.agreement).toBe('incomplete')
    expect(c.summary).toContain('primary reading')
  })

  it('two conflicting rows for one (ayanamsha, fact) are unread, never guessed', () => {
    const r = [...rows(AYANAMSHA_SERVE_ORDER), { ayanamsha_id: 'raman', fact_key: 'moon_sign', value: 'Pisces' }]
    const c = ok(buildAyanamshaCrossCheck(r, PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(c.others.find((o) => o.ayanamsha_id === 'raman')!.status).toBe('incomplete')
  })

  it('an explicit non-Lahiri primary (caller asked for KP) lists Lahiri among the others, still in serve order', () => {
    const c = ok(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER), 'krishnamurti', { facts: FACTS }))
    expect(c.others.map((o) => o.ayanamsha_id)).toEqual(['lahiri_chitrapaksha', 'true_chitra', 'raman', 'surya_siddhanta_classical'])
  })

  it('is deterministic and byte-stable', () => {
    const f = () => JSON.stringify(buildAyanamshaCrossCheck(rows(AYANAMSHA_SERVE_ORDER, { raman: { moon_sign: 'Pisces' } }), PRIMARY_AYANAMSHA, { facts: FACTS }))
    expect(f()).toBe(f())
  })

  it('the response-budget key in platform-mcp is the same key (parity)', () => {
    expect([...budget.CROSS_CHECK_FIELDS]).toEqual([CROSS_CHECK_KEY])
  })
})
