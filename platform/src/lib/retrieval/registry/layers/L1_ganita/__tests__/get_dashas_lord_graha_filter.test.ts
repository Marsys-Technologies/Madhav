import { describe, expect, it } from 'vitest'
import { LORD_GRAHA_STORED_FORMS, resolveLordGrahaFilter } from '@/lib/retrieval/registry/layers/L1_ganita/get_dashas'
import { getDashasCapability } from '@/lib/retrieval/registry/layers/L1_ganita/get_dashas'

// chart_dashas.lord_graha stores Title-case names: the 9 graha names (graha systems), the 12 sign names (rashi systems: chara_karaka,
// kalachakra, narayana) and the 8 yogini deity names. The filter used to apply the caller's string verbatim and its description said
// "abbreviation (SU, MO, MA)", so 'SU' returned zero rows silently. It must resolve the value to the stored form, and an unknown value
// must be a structured error, not an empty page.
describe('get_dashas lord_graha filter resolves to the stored form', () => {
  it("'SU', 'Sun', 'sun' and 'SUN' resolve to the same stored value", () => {
    const got = ['SU', 'Sun', 'sun', 'SUN', ' sun '].map(v => resolveLordGrahaFilter(v))
    expect(new Set(got.map(g => (g.ok ? g.stored : 'ERR')))).toEqual(new Set(['Sun']))
  })

  it.each([
    ['MO', 'Moon'], ['moon', 'Moon'], ['MA', 'Mars'], ['mars', 'Mars'], ['MER', 'Mercury'], ['JUP', 'Jupiter'], ['VEN', 'Venus'], ['SAT', 'Saturn'],
    ['shani', 'Saturn'], ['Rahu', 'Rahu'], ['RAH_MEAN', 'Rahu'], ['Ketu', 'Ketu'], ['KET_TRUE', 'Ketu'],
  ])('graha %s -> %s', (input, stored) => {
    expect(resolveLordGrahaFilter(input)).toEqual({ ok: true, stored })
  })

  it.each([['taurus', 'Taurus'], ['SAGITTARIUS', 'Sagittarius'], ['Aries', 'Aries']])('sign %s -> %s (rashi dasha systems)', (input, stored) => {
    expect(resolveLordGrahaFilter(input)).toEqual({ ok: true, stored })
  })

  it.each([['mangala', 'Mangala'], ['Sankata', 'Sankata']])('yogini deity %s -> %s', (input, stored) => {
    expect(resolveLordGrahaFilter(input)).toEqual({ ok: true, stored })
  })

  it.each(['', '   ', 'Pluto', 'XYZ', 'node', 'lagna', 'KP_LEVELS_BEYOND_SUB_SUB'])('unknown or ambiguous %j is refused, not guessed', input => {
    expect(resolveLordGrahaFilter(input)).toEqual({ ok: false })
  })

  it('every resolved value is one of the stored forms listed in the error', () => {
    for (const v of ['SU', 'moon', 'KET_MEAN', 'taurus', 'dhanya']) {
      const r = resolveLordGrahaFilter(v)
      expect(r.ok && LORD_GRAHA_STORED_FORMS.includes(r.stored)).toBe(true)
    }
    expect(LORD_GRAHA_STORED_FORMS).toHaveLength(9 + 12 + 8)
  })

  it('the tool description no longer calls the filter an abbreviation and names the error', () => {
    const desc = JSON.stringify(getDashasCapability)
    expect(desc).not.toContain('lord graha abbreviation')
    expect(desc).toContain('invalid_lord_graha')
  })
})
