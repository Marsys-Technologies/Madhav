import { readTimingWindowsFamily, readContradictionsFamily } from '../registry_bridge'

const MOCK_ACTIVATION = {
  id: '8106742',
  signal_id: 'abc',
  ayanamsha_id: 'lahiri_chitrapaksha',
  signature_class: 'SUBSYSTEM',
  activation_start: '2027-08-18',
  activation_end: '2028-01-15',
  activation_peak_date: '2027-10-01',
}

const MOCK_CONTRADICTION = {
  contradiction_id: '3fa9292b',
  signal_a_id: 'aaa',
  signal_b_id: 'bbb',
  // NOTE: no tension_label / label / description — matches live data shape
}

describe('F-130 — no raw JSON in reading[] sentences', () => {
  it('readTimingWindowsFamily: sentence is prose, not JSON', () => {
    const result = readTimingWindowsFamily({ activations: [MOCK_ACTIVATION] })
    expect(result.status).toBe('served')
    const sentence = result.sentences[0]!
    expect(sentence).not.toMatch(/{/)   // FAILS on current code (JSON.stringify)
    expect(sentence).toContain('SUBSYSTEM')
    expect(sentence).toContain('2027-08-18')
  })

  it('readContradictionsFamily: fallback sentence is prose, not JSON', () => {
    const result = readContradictionsFamily({
      total_count: 1,
      items: [MOCK_CONTRADICTION],
    })
    expect(result.status).toBe('served')
    const sentence = result.sentences[0]!
    expect(sentence).not.toMatch(/{/)   // FAILS on current code (JSON.stringify fallback)
    expect(sentence).toContain('3fa9292b')
  })
})
