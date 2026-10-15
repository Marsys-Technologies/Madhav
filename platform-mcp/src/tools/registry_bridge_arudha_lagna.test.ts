import { describe, expect, it } from 'vitest'
import { pickArudhaLagnaSignRow } from './registry_bridge'

const row = (fact_subject: string, fact_key: string, fact_value_text: string | null, fact_id: string) => ({ fact_subject, fact_key, fact_value_text, fact_id })

// Production stores the arudha subjects as BHAVA_ARUDHA_A1..A12, BHAVA_ARUDHA_AL and BHAVA_ARUDHA_UPA, each with house_d1 / longitude_sidereal / sign.
// The old pick (`includes('HOUSE_1') || === 'AL1' || === 'ARUDHA_LAGNA'`, first row) matched NOTHING real, so the Arudha Lagna never appeared in the sentence.
describe('pickArudhaLagnaSignRow', () => {
  it('picks the AL sign row even when A10, A11, A12, A1 and the null-text AL keys come first', () => {
    const rows = [
      row('BHAVA_ARUDHA_A10', 'sign', 'Aries', '10'), row('BHAVA_ARUDHA_A11', 'sign', 'Gemini', '11'), row('BHAVA_ARUDHA_A12', 'sign', 'Gemini', '12'),
      row('BHAVA_ARUDHA_A1', 'sign', 'Scorpio', '01'),
      row('BHAVA_ARUDHA_AL', 'house_d1', null, '20'), row('BHAVA_ARUDHA_AL', 'longitude_sidereal', null, '21'),
      row('BHAVA_ARUDHA_AL', 'sign', 'Capricorn', '22'), row('BHAVA_ARUDHA_UPA', 'sign', 'Leo', '30'),
    ]
    expect(pickArudhaLagnaSignRow(rows)).toMatchObject({ fact_subject: 'BHAVA_ARUDHA_AL', fact_value_text: 'Capricorn', fact_id: '22' })
  })

  it('does not substring-match: HOUSE_10 / HOUSE_11 / HOUSE_12 / A10 are never the Arudha Lagna', () => {
    const rows = [row('D1_HOUSE_10', 'sign', 'Aries', '1'), row('HOUSE_11', 'sign', 'Taurus', '2'), row('HOUSE_12', 'sign', 'Gemini', '3'), row('BHAVA_ARUDHA_A10', 'sign', 'Aries', '4')]
    expect(pickArudhaLagnaSignRow(rows)).toBeUndefined()
  })

  it('the legacy guesses (AL1, ARUDHA_LAGNA) are not accepted: only the stored canonical subject counts', () => {
    expect(pickArudhaLagnaSignRow([row('AL1', 'sign', 'Aries', '1'), row('ARUDHA_LAGNA', 'sign', 'Aries', '2')])).toBeUndefined()
  })

  it('is independent of row order: several AL sign rows give the same pick whichever comes first', () => {
    const a = row('BHAVA_ARUDHA_AL', 'sign', 'Capricorn', 'b'), b = row('BHAVA_ARUDHA_AL', 'sign', 'Capricorn', 'a')
    expect(pickArudhaLagnaSignRow([a, b])?.fact_id).toBe('a')
    expect(pickArudhaLagnaSignRow([b, a])?.fact_id).toBe('a')
  })

  it('no AL row, an AL row without text, or an empty list gives undefined (an honest absence, not a wrong sign)', () => {
    expect(pickArudhaLagnaSignRow([])).toBeUndefined()
    expect(pickArudhaLagnaSignRow([row('BHAVA_ARUDHA_AL', 'sign', null, '1'), row('BHAVA_ARUDHA_AL', 'sign', '', '2')])).toBeUndefined()
  })
})
