/**
 * explain_kp_voice.test.ts — ṢAḌ-DARŚANA W3K Lane 2, gap G-5: the WIRING half.
 *
 * `kp_school_voice.test.ts` proves the verdict; this file proves it reaches the envelope —
 * that a dissent lands in `reading.dissent` with the school tag, that a concurrence lands in
 * `reading.evidence`, and that an honest-empty voice contributes to NEITHER list while
 * flipping the `dissent_multi_system_concurrence` coverage entry to a named gap.
 *
 * The fixtures are the same real chart-482012f1 reads documented in
 * `kp_school_voice.test.ts`'s header and `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` §9.
 */
import { describe, it, expect } from 'vitest'
import { applyKpVoiceToReading, kpCoverageEntry, toKpPeriods } from './explain.js'
import { buildKpSchoolVoice, KP_SCHOOL_LABEL, type KpHouseLadder } from '../../lib/kp_school_voice.js'
import { composeArgument } from '../../lib/argument_composer.js'
import type { ArgumentReading } from '../../lib/kala_envelope.js'

const H7_LADDER: KpHouseLadder = {
  house: 7, cusp_owner: 'Venus',
  level_a: [], level_b: ['Mars', 'Saturn'], level_c: ['Venus'], level_d: ['Venus'],
  ranked: ['Mars', 'Saturn', 'Venus'], fact_ids: ['kp-h7-a', 'kp-h7-b'],
}
const H10_LADDER: KpHouseLadder = {
  house: 10, cusp_owner: 'Saturn',
  level_a: ['Mercury'], level_b: ['Sun'], level_c: [], level_d: ['Saturn'],
  ranked: ['Mercury', 'Sun', 'Saturn'], fact_ids: ['kp-h10-a'],
}
const PERIODS = toKpPeriods([
  { level_n: 2, lord_graha: 'Saturn', kp_sub_lord: 'Saturn', kp_sub_sub_lord: null,
    start_date: '2024-12-08', end_date: '2027-08-18' },
  { level_n: 3, lord_graha: 'Moon', kp_sub_lord: 'Saturn', kp_sub_sub_lord: 'Moon',
    start_date: '2026-06-27', end_date: '2026-09-17' },
])

function baseReading(): ArgumentReading {
  return {
    thesis: 'Why for Bhava 7 — Marriage / Partnership as of 2026-08-04: not promised.',
    evidence: [{ claim: 'PROMISE (denied): contested composite.', fact_ids: [] }],
    dissent: [],
    verdict: { statement: 'The chain halts at PROMISE.', tier: 'structural_prior' },
    falsifier: null,
  }
}

function makeVoice(over: Partial<Parameters<typeof buildKpSchoolVoice>[0]> = {}) {
  return buildKpSchoolVoice({
    bhava: 7, ladder: H7_LADDER, periods: PERIODS, pactStatus: 'denied_at_promise',
    kpAyanamshaId: 'krishnamurti', chainAyanamshaId: 'lahiri_chitrapaksha',
    ...over,
  })
}

describe('toKpPeriods', () => {
  it('reads the KP-native lord columns off get_dashas rows', () => {
    expect(PERIODS).toHaveLength(2)
    expect(PERIODS[0]!.kp_sub_lord).toBe('Saturn')
    expect(PERIODS[1]!.kp_sub_sub_lord).toBe('Moon')
  })

  it('drops rows with no usable level rather than coercing them to 0', () => {
    expect(toKpPeriods([{ lord_graha: 'Saturn' }])).toEqual([])
  })
})

describe('applyKpVoiceToReading — the served dissent', () => {
  it('a real dissent reaches reading.dissent, school-tagged', () => {
    const out = applyKpVoiceToReading(baseReading(), makeVoice())
    expect(out.dissent).toHaveLength(1)
    expect(out.dissent[0]!.source).toBe(KP_SCHOOL_LABEL)
    expect(out.dissent[0]!.claim).toContain('DISSENTS')
    // B.3: the dissent carries the ledger of the ladder rows it consumed.
    expect(out.dissent[0]!.fact_ids).toEqual(['kp-h7-a', 'kp-h7-b'])
  })

  it('the composed prose names the dissenting school in the canonical clause order', () => {
    const composed = composeArgument(applyKpVoiceToReading(baseReading(), makeVoice()))
    expect(composed.dissent_sentences).toHaveLength(1)
    expect(composed.dissent_sentences[0]).toContain(`${KP_SCHOOL_LABEL} dissents:`)
    // thesis → evidence → dissent → verdict (Elevation §5 E3's order)
    const t = composed.full_text
    expect(t.indexOf('dissents:')).toBeGreaterThan(t.indexOf('PROMISE (denied)'))
    expect(t.indexOf('dissents:')).toBeLessThan(t.indexOf('The chain halts at PROMISE.'))
  })

  it('does not disturb the PACT evidence the chain already produced', () => {
    const out = applyKpVoiceToReading(baseReading(), makeVoice())
    expect(out.evidence).toHaveLength(1)
    expect(out.verdict).toEqual(baseReading().verdict)
  })

  it('a concurrence lands in evidence, not in dissent', () => {
    const v = makeVoice({ bhava: 10, ladder: H10_LADDER, pactStatus: 'chain_complete' })
    const out = applyKpVoiceToReading(baseReading(), v)
    expect(out.dissent).toHaveLength(0)
    expect(out.evidence).toHaveLength(2)
    expect(out.evidence[1]!.claim).toContain('CONCURS')
    expect(out.evidence[1]!.fact_ids).toEqual(['kp-h10-a'])
  })

  it('an honest-empty voice adds to NEITHER list (a gap is never corroboration)', () => {
    const out = applyKpVoiceToReading(baseReading(), makeVoice({ ladder: null }))
    expect(out).toEqual(baseReading())
  })

  it('a not_comparable voice adds to neither list', () => {
    const out = applyKpVoiceToReading(baseReading(), makeVoice({ pactStatus: 'chain_incomplete_infra' }))
    expect(out).toEqual(baseReading())
  })

  it('a null voice (no bhava resolved) is a no-op', () => {
    expect(applyKpVoiceToReading(baseReading(), null)).toEqual(baseReading())
  })
})

describe('kpCoverageEntry', () => {
  it('reports `computed` only when a real verdict was reached', () => {
    const e = kpCoverageEntry(makeVoice())
    expect(e.concept).toBe('dissent_multi_system_concurrence')
    expect(e.state).toBe('computed')
  })

  it('reports honest_empty carrying the voice\'s own specific reason', () => {
    const e = kpCoverageEntry(makeVoice({ ladder: null }))
    expect(e.state).toBe('honest_empty')
    expect(e.reason).toContain('kp_house_significators')
  })

  it('reports honest_empty when no bhava could be resolved to judge', () => {
    const e = kpCoverageEntry(null)
    expect(e.state).toBe('honest_empty')
    expect(e.reason).toContain('needs a bhava to judge')
  })

  it('never reports `computed` for a voice that reached no verdict (§N.8)', () => {
    for (const over of [{ ladder: null }, { periods: [] }]) {
      expect(kpCoverageEntry(makeVoice(over)).state).toBe('honest_empty')
    }
  })
})
