import { buildDashaNarration } from '../get_dashas'

const BIRTH_DATE = '1984-06-10'

const allFourLevels: Record<number, Record<string, unknown>> = {
  1: { level_n: 1, lord_graha: 'Mercury', end_date: '2027-08-18', sandhi_flag: false,
       lord_natal_dignity_d1: null, lord_natal_house_d1: null, lord_natal_nakshatra: null },
  2: { level_n: 2, lord_graha: 'Saturn',  end_date: '2027-08-18', sandhi_flag: false,
       lord_natal_dignity_d1: 'exalted', lord_natal_house_d1: '7', lord_natal_nakshatra: 'Vishakha' },
  3: { level_n: 3, lord_graha: 'Moon',    end_date: '2026-09-17', sandhi_flag: false,
       lord_natal_dignity_d1: 'neutral', lord_natal_house_d1: '11', lord_natal_nakshatra: 'Purva Bhadrapada' },
  4: { level_n: 4, lord_graha: 'Mercury', end_date: '2026-08-25', sandhi_flag: true,
       lord_natal_dignity_d1: null, lord_natal_house_d1: null, lord_natal_nakshatra: null },
}

describe('F-120: buildDashaNarration', () => {
  it('includes level-4 Sukshmadasha in the narration chain', () => {
    const result = buildDashaNarration(allFourLevels, BIRTH_DATE)
    expect(result).toContain('Mercury Sukshmadasha')
  })

  it('labels only the finest level (level-4) as current', () => {
    const result = buildDashaNarration(allFourLevels, BIRTH_DATE)
    expect(result).toMatch(/Mercury Sukshma.*current/)
    expect(result).not.toMatch(/Moon Pratyantardasha.*current/)
  })

  it('surfaces sandhi_flag at level-4', () => {
    const result = buildDashaNarration(allFourLevels, BIRTH_DATE)
    expect(result).toMatch(/sandhi|junction/i)
  })

  it('does not emit sandhi sentence when all flags are false', () => {
    const noSandhi: Record<number, Record<string, unknown>> = Object.fromEntries(
      Object.entries(allFourLevels).map(([k, v]) => [k, { ...v, sandhi_flag: false }])
    )
    const result = buildDashaNarration(noSandhi, BIRTH_DATE)
    expect(result).not.toMatch(/sandhi|junction/i)
  })

  it('preserves correct 3-level behaviour when only levels 1-3 are present', () => {
    const threeLevels = { 1: allFourLevels[1], 2: allFourLevels[2], 3: allFourLevels[3] }
    const result = buildDashaNarration(threeLevels, BIRTH_DATE)
    expect(result).toContain('Moon Pratyantardasha')
    expect(result).toMatch(/Moon Pratyantardasha.*current/)
    expect(result).not.toContain('Sukshmadasha')
  })
})
