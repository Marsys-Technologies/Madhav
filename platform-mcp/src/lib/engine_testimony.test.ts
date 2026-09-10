import { describe, expect, it } from 'vitest'
import {
  kpVoiceToTestimony,
  agnivasaVoiceToTestimony,
  a5AgreementToTestimony,
  composeConcordanceVerdict,
} from './engine_testimony'
import type { EngineTestimony, AuthorityProfileRow } from './engine_testimony'
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

describe('composeConcordanceVerdict', () => {
  const PROFILE: AuthorityProfileRow[] = [
    { convention_id: 'pact', arbitration_role: 'primary', precedence: 1 },
    { convention_id: 'kp', arbitration_role: 'corroborating', precedence: null },
    { convention_id: 'gochara_v3', arbitration_role: 'corroborating', precedence: null },
  ]

  function makeTestimony(overrides: Partial<EngineTestimony> = {}): EngineTestimony {
    return {
      engine: 'pact',
      engine_label: 'PACT',
      state: 'computed',
      empty_reason: null,
      agreement: 'concurs',
      claim: 'stub claim',
      ...overrides,
    }
  }

  it('returns null when there is no computed testimony at all', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', state: 'honest_empty', empty_reason: 'no chain', agreement: 'not_comparable' }),
      makeTestimony({ engine: 'kp', state: 'honest_empty', empty_reason: 'no significators', agreement: 'not_comparable' }),
    ]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toBeNull()
  })

  it('returns null when no testimony engine maps to a primary role in the profile', () => {
    const testimony = [makeTestimony({ engine: 'kp', agreement: 'concurs' })]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toBeNull()
  })

  it('returns aligned/null when the primary stands alone with no corroborating testimony', () => {
    const testimony = [makeTestimony({ engine: 'pact' })]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'aligned', adjudicated_by: null })
  })

  it('returns aligned/null when every corroborating engine concurs', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'kp', agreement: 'concurs' }),
      makeTestimony({ engine: 'gochara_v3', agreement: 'concurs' }),
    ]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'aligned', adjudicated_by: null })
  })

  it('returns aligned/null when every corroborating engine is not_comparable (nothing contradicts the primary)', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'kp', agreement: 'not_comparable' }),
      makeTestimony({ engine: 'gochara_v3', agreement: 'not_comparable' }),
    ]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'aligned', adjudicated_by: null })
  })

  it('returns disputed/primary-engine when every corroborating engine that took a stance dissents', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'kp', agreement: 'dissents' }),
      makeTestimony({ engine: 'gochara_v3', agreement: 'dissents' }),
    ]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'disputed', adjudicated_by: 'pact' })
  })

  it('returns partially_aligned/primary-engine on a split between concurring and dissenting corroborators', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'kp', agreement: 'concurs' }),
      makeTestimony({ engine: 'gochara_v3', agreement: 'dissents' }),
    ]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'partially_aligned', adjudicated_by: 'pact' })
  })

  it('ignores testimony from an engine absent from the profile entirely', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'some_untracked_engine', agreement: 'dissents' }),
    ]
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'aligned', adjudicated_by: null })
  })

  it('ignores informational/declared_silent/gate-tagged testimony as neither primary nor corroborating', () => {
    const profile: AuthorityProfileRow[] = [
      ...PROFILE,
      { convention_id: 'muhurta_chintamani', arbitration_role: 'informational', precedence: null },
      { convention_id: 'some_gate', arbitration_role: 'gate', precedence: null },
      { convention_id: 'some_silent', arbitration_role: 'declared_silent', precedence: null },
    ]
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'muhurta_chintamani', agreement: 'dissents' }),
      makeTestimony({ engine: 'some_gate', agreement: 'dissents' }),
      makeTestimony({ engine: 'some_silent', agreement: 'dissents' }),
    ]
    expect(composeConcordanceVerdict(testimony, profile)).toEqual({ status: 'aligned', adjudicated_by: null })
  })

  it('excludes honest_empty testimony from corroborating votes (only computed states count)', () => {
    const testimony = [
      makeTestimony({ engine: 'pact', agreement: 'concurs' }),
      makeTestimony({ engine: 'kp', state: 'honest_empty', empty_reason: 'no significators', agreement: 'not_comparable' }),
      makeTestimony({ engine: 'gochara_v3', agreement: 'dissents' }),
    ]
    // kp is honest_empty (excluded), gochara_v3 dissents alone -> disputed
    expect(composeConcordanceVerdict(testimony, PROFILE)).toEqual({ status: 'disputed', adjudicated_by: 'pact' })
  })
})
