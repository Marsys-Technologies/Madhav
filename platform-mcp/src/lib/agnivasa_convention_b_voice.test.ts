import { describe, expect, it } from 'vitest'
import {
  computeAgnivasaConventionBVoice,
  computeConventionBElement,
} from './agnivasa_convention_b_voice'

describe('computeConventionBElement (MC 1.36 arithmetic)', () => {
  it('tithi_id=1, vara_id=1 (Sunday) -> prithvi (remainder 3)', () => {
    expect(computeConventionBElement(1, 1)).toBe('prithvi')
  })
  it('tithi_id=1, vara_id=3 (Tuesday) -> akasha (remainder 1) -- the divergence proof case', () => {
    expect(computeConventionBElement(1, 3)).toBe('akasha')
  })
  it('tithi_id=1, vara_id=4 (Wednesday) -> patala (remainder 2)', () => {
    expect(computeConventionBElement(1, 4)).toBe('patala')
  })
  it('tithi_id=30, vara_id=7 (Saturday) -> valid boundary input, no throw', () => {
    expect(() => computeConventionBElement(30, 7)).not.toThrow()
  })
})

describe('computeAgnivasaConventionBVoice', () => {
  it('reports honest_empty when Convention B is not operative', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 1, element: 'prithvi' }, false)
    expect(voice.state).toBe('honest_empty')
    expect(voice.empty_reason).toContain('convention_status=computed')
    expect(voice.agreement).toBe('not_comparable')
  })

  it('reports honest_empty when the lattice atom carries no tithi_id/vara_id', () => {
    const voice = computeAgnivasaConventionBVoice({ element: 'prithvi' }, true)
    expect(voice.state).toBe('honest_empty')
    expect(voice.empty_reason).toContain('tithi_id/vara_id')
  })

  it('agrees with Convention A when both favourable (tithi_id=1, vara_id=1)', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 1, element: 'prithvi' }, true)
    expect(voice.state).toBe('computed')
    expect(voice.element).toBe('prithvi')
    expect(voice.favourable).toBe(true)
    expect(voice.convention_a_favourable).toBe(true)
    expect(voice.agreement).toBe('agrees')
  })

  it('DIVERGES from Convention A on the proof case (tithi_id=1, vara_id=3)', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 3, element: 'prithvi' }, true)
    expect(voice.element).toBe('akasha')
    expect(voice.favourable).toBe(false)
    expect(voice.convention_a_favourable).toBe(true)
    expect(voice.agreement).toBe('diverges')
    expect(voice.claim).toContain('DIVERGING')
  })

  it('agrees when both unfavourable (tithi_id=16=vayu, vara_id chosen for B=akasha/patala)', () => {
    // tithi_id=16 -> Convention A = Vayu (unfavourable). Convention B: (16+1+2) mod 4 = 19 mod 4 = 3 -> prithvi.
    // Pick a vara_id that keeps B unfavourable too: (16+1+3) mod 4 = 20 mod 4 = 0 -> prithvi (still fav, not useful).
    // (16+1+1) mod 4 = 18 mod 4 = 2 -> patala (unfavourable) -- both unfavourable, agreement.
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 16, vara_id: 1, element: 'vayu' }, true)
    expect(voice.element).toBe('patala')
    expect(voice.favourable).toBe(false)
    expect(voice.convention_a_favourable).toBe(false)
    expect(voice.agreement).toBe('agrees')
  })

  it('never gates -- the voice is informational only, no mode/interval fields exist on it', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 3, element: 'prithvi' }, true)
    expect(voice).not.toHaveProperty('mode')
    expect(voice).not.toHaveProperty('intervals')
  })
})
