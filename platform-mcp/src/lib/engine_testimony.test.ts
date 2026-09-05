import { describe, expect, it } from 'vitest'
import {
  kpVoiceToTestimony,
  agnivasaVoiceToTestimony,
  a5AgreementToTestimony,
} from './engine_testimony'
import type { KpSchoolVoice } from './kp_school_voice'
import { computeAgnivasaConventionBVoice } from './agnivasa_convention_b_voice'

function makeKpVoice(overrides: Partial<KpSchoolVoice> = {}): KpSchoolVoice {
  return {
    school: 'kp',
    school_label: 'KP sub-lord clock (Krishnamurti Paddhati significator ladder)',
    state: 'computed',
    empty_reason: null,
    bhava: 7,
    kp_stance: 'signified',
    parasari_stance: 'promised',
    agreement: 'concurs',
    ladder: null,
    running_lords: [],
    matches: [],
    strongest_limb: null,
    kp_ayanamsha_id: 'krishnamurti',
    chain_ayanamsha_id: 'lahiri',
    ayanamsha_divergence: true,
    claim: 'KP concurs: the running lord signifies bhava 7.',
    ...overrides,
  }
}

describe('kpVoiceToTestimony', () => {
  it('maps a computed, concurring voice field-for-field', () => {
    const voice = makeKpVoice()
    const testimony = kpVoiceToTestimony(voice)
    expect(testimony).toEqual({
      engine: 'kp',
      engine_label: voice.school_label,
      state: 'computed',
      empty_reason: null,
      agreement: 'concurs',
      claim: voice.claim,
    })
  })

  it('preserves honest_empty state and empty_reason unchanged', () => {
    const voice = makeKpVoice({
      state: 'honest_empty',
      empty_reason: 'no kp_house_significators for this chart',
      agreement: 'not_comparable',
    })
    const testimony = kpVoiceToTestimony(voice)
    expect(testimony.state).toBe('honest_empty')
    expect(testimony.empty_reason).toBe('no kp_house_significators for this chart')
    expect(testimony.agreement).toBe('not_comparable')
  })

  it('passes dissents through unchanged (already canonical)', () => {
    const voice = makeKpVoice({ agreement: 'dissents' })
    expect(kpVoiceToTestimony(voice).agreement).toBe('dissents')
  })
})

describe('agnivasaVoiceToTestimony', () => {
  it('maps agrees -> concurs', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 1, element: 'prithvi' }, true)
    expect(voice.agreement).toBe('agrees') // sanity on the source fixture
    const testimony = agnivasaVoiceToTestimony(voice)
    expect(testimony.agreement).toBe('concurs')
    expect(testimony.engine).toBe('muhurta_chintamani')
    expect(testimony.state).toBe('computed')
    expect(testimony.claim).toBe(voice.claim)
  })

  it('maps diverges -> dissents (the proof case)', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 3, element: 'prithvi' }, true)
    expect(voice.agreement).toBe('diverges') // sanity on the source fixture
    const testimony = agnivasaVoiceToTestimony(voice)
    expect(testimony.agreement).toBe('dissents')
  })

  it('maps not_comparable -> not_comparable and preserves honest_empty', () => {
    const voice = computeAgnivasaConventionBVoice({ tithi_id: 1, vara_id: 1, element: 'prithvi' }, false)
    expect(voice.state).toBe('honest_empty') // sanity on the source fixture
    const testimony = agnivasaVoiceToTestimony(voice)
    expect(testimony.agreement).toBe('not_comparable')
    expect(testimony.state).toBe('honest_empty')
    expect(testimony.empty_reason).toBe(voice.empty_reason)
  })
})

describe('a5AgreementToTestimony', () => {
  it('maps concurs to computed/concurs with no empty_reason', () => {
    const testimony = a5AgreementToTestimony({
      agreement: 'concurs',
      note: 'Gochara gain windows align with PACT chain_complete.',
    })
    expect(testimony).toEqual({
      engine: 'gochara_v3',
      engine_label: 'Gochara v3 (transit) agreement (SM-γ C4.2, flag-guarded)',
      state: 'computed',
      empty_reason: null,
      agreement: 'concurs',
      claim: 'Gochara gain windows align with PACT chain_complete.',
    })
  })

  it('maps dissents to computed/dissents', () => {
    const testimony = a5AgreementToTestimony({
      agreement: 'dissents',
      note: 'Gochara loss windows diverge from PACT chain_complete.',
    })
    expect(testimony.agreement).toBe('dissents')
    expect(testimony.state).toBe('computed')
    expect(testimony.empty_reason).toBeNull()
  })

  it('maps insufficient_data to honest_empty/not_comparable with the note as empty_reason', () => {
    const testimony = a5AgreementToTestimony({
      agreement: 'insufficient_data',
      note: 'No active gochara windows found for this domain/period.',
    })
    expect(testimony.agreement).toBe('not_comparable')
    expect(testimony.state).toBe('honest_empty')
    expect(testimony.empty_reason).toBe('No active gochara windows found for this domain/period.')
    expect(testimony.claim).toBe('No active gochara windows found for this domain/period.')
  })
})
