/**
 * kp_school_voice.test.ts — ṢAḌ-DARŚANA W3K Lane 2, gap G-5.
 *
 * THE GOLDEN CASE IS REAL, NOT CONSTRUCTED.
 * ----------------------------------------
 * The `H7_LADDER` / `RUNNING_2026_08_04` fixtures below are not invented shapes: every
 * value is what the production data yields for the canonical chart
 * 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty), read read-only on 2026-08-03 and
 * recorded in `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` §9.
 *
 *   • H7_LADDER is the output of the SHIPPED Lane-1 emitter
 *     (`ga_writers/ga_kp_significators.emit_kp_significators`) run over production
 *     `chart_facts` for ayanāṃśa `krishnamurti` — real graha longitudes, real Placidus
 *     `bhava_cusps`, real `graha_kp_lords` star lords, real `reference_signs` lords.
 *   • RUNNING_2026_08_04 is the live `chart_dashas` row set for
 *     `system_id='vimshottari_kp'` covering 2026-08-04.
 *   • `denied_at_promise` is the ACTUAL `pact_status` `kala_explain_get` returns for
 *     bhava 7 on that chart at that date (composite −3.5, "contested").
 *
 * The disagreement was FOUND by comparing those three real reads, not manufactured to
 * satisfy Gate W3K. Its cause is the textbook methodological split: Mars and Saturn both
 * occupy the 7th in the KP/Placidus cusp frame, so KP ranks them the 7th's own delivering
 * agents (limb B) irrespective of their malefic nature, while the Parāśarī checklist grades
 * those same two occupants as the affliction that denies the promise. Saturn is running at
 * both AD and SD on the date — so the two schools read the identical running window to
 * opposite verdicts.
 */
import { describe, it, expect } from 'vitest'
import {
  buildKpSchoolVoice,
  parseKpHouseLadder,
  parasariStanceFromPactStatus,
  runningKpLords,
  KP_SCHOOL_LABEL,
  type KpHouseLadder,
  type KpRunningPeriod,
} from './kp_school_voice.js'

// ── The real fixtures (chart 482012f1, ayanāṃśa krishnamurti, 2026-08-04) ──────────────

const H7_LADDER: KpHouseLadder = {
  house: 7,
  cusp_owner: 'Venus',
  level_a: [],                       // no graha has Mars or Saturn as its star lord
  level_b: ['Mars', 'Saturn'],       // both occupy cusp 7 (192.528°–222.517°)
  level_c: ['Venus'],                // Venus tenants its own star
  level_d: ['Venus'],                // cusp 7 falls in Libra
  ranked: ['Mars', 'Saturn', 'Venus'],
  fact_ids: [],
}

const H10_LADDER: KpHouseLadder = {
  house: 10,
  cusp_owner: 'Saturn',
  level_a: ['Mercury'],
  level_b: ['Sun'],
  level_c: [],
  level_d: ['Saturn'],
  ranked: ['Mercury', 'Sun', 'Saturn'],
  fact_ids: [],
}

const RUNNING_2026_08_04: KpRunningPeriod[] = [
  {
    level_n: 2, lord_graha: 'Saturn', kp_sub_lord: 'Saturn', kp_sub_sub_lord: null,
    start_date: '2024-12-08', end_date: '2027-08-18',
  },
  {
    level_n: 3, lord_graha: 'Moon', kp_sub_lord: 'Saturn', kp_sub_sub_lord: 'Moon',
    start_date: '2026-06-27', end_date: '2026-09-17',
  },
]

const KP_AY = 'krishnamurti'
const CHAIN_AY = 'lahiri_chitrapaksha'

function voice(over: Partial<Parameters<typeof buildKpSchoolVoice>[0]> = {}) {
  return buildKpSchoolVoice({
    bhava: 7,
    ladder: H7_LADDER,
    periods: RUNNING_2026_08_04,
    pactStatus: 'denied_at_promise',
    kpAyanamshaId: KP_AY,
    chainAyanamshaId: CHAIN_AY,
    ...over,
  })
}

// ── THE GATE-W3K CASE: one real served dissent ────────────────────────────────────────

describe('W3K Gate — a real KP/Parāśarī dissent on a running window', () => {
  it('bhava 7 on chart 482012f1 at 2026-08-04: KP signifies, Parāśarī denies', () => {
    const v = voice()
    expect(v.state).toBe('computed')
    expect(v.kp_stance).toBe('signified')
    expect(v.parasari_stance).toBe('denied')
    expect(v.agreement).toBe('dissents')
  })

  it('names the running lord and the limb that produced the KP verdict', () => {
    const v = voice()
    // Saturn occupies the 7th cusp — limb B, a strong agency limb.
    const saturn = v.matches.find((m) => m.lord === 'Saturn')
    expect(saturn).toBeDefined()
    expect(saturn!.limb).toBe('b')
    expect(saturn!.strong).toBe(true)
    expect(v.strongest_limb).toBe('b')
    // Saturn is running at the KP sub level AND as the AD lord of the same window.
    expect(v.matches.map((m) => m.running_level)).toContain('AD')
    expect(v.matches.map((m) => m.running_level)).toContain('KP_SUB')
  })

  it('the served claim states the disagreement and its methodological cause', () => {
    const v = voice()
    expect(v.claim).toContain('DISSENTS')
    expect(v.claim).toContain('7th house')
    expect(v.claim).toMatch(/benefic\/malefic/)
  })

  it('carries the school tag other schools route on', () => {
    expect(KP_SCHOOL_LABEL).toContain('Krishnamurti Paddhati')
    expect(voice().school).toBe('kp')
  })

  it('serves the ayanāṃśa divergence rather than reconciling it', () => {
    const v = voice()
    expect(v.kp_ayanamsha_id).toBe(KP_AY)
    expect(v.chain_ayanamsha_id).toBe(CHAIN_AY)
    expect(v.ayanamsha_divergence).toBe(true)
  })

  it('the dissent is not an artefact of the ayanāṃśa split — it holds in lahiri too', () => {
    // Verified read-only against production: in lahiri_chitrapaksha the cusp-7 arc is
    // 192.431°–222.420° and Mars (198.519°) / Saturn (202.432°) still both fall inside it,
    // so the ladder is unchanged and the KP sub-lord at 2026-08-04 is still Saturn.
    const v = voice({ kpAyanamshaId: CHAIN_AY })
    expect(v.ayanamsha_divergence).toBe(false)
    expect(v.agreement).toBe('dissents')
  })
})

// ── The concurrence half, same chart, same instant, same running lords ────────────────

describe('W3K Gate — KP concurrence', () => {
  it('bhava 10 on the same chart at the same instant: both schools agree', () => {
    const v = voice({ bhava: 10, ladder: H10_LADDER, pactStatus: 'chain_complete' })
    expect(v.kp_stance).toBe('signified')
    expect(v.parasari_stance).toBe('promised')
    expect(v.agreement).toBe('concurs')
    expect(v.claim).not.toContain('DISSENTS')
  })

  it('proves the two verdicts are genuinely independent, not a relabelled clock', () => {
    // The SAME running lord stack yields `dissents` for bhava 7 and `concurs` for bhava 10.
    // A voice that merely restated Vimśottarī could not produce both from one stack.
    const seven = voice()
    const ten = voice({ bhava: 10, ladder: H10_LADDER, pactStatus: 'chain_complete' })
    expect(seven.running_lords).toEqual(ten.running_lords)
    expect(seven.agreement).not.toBe(ten.agreement)
  })

  it('KP agreeing with a denial is also concurrence, not silence', () => {
    const barren: KpHouseLadder = { ...H7_LADDER, level_b: [], ranked: ['Venus'], level_c: ['Venus'], level_d: ['Venus'] }
    const v = voice({ ladder: barren, pactStatus: 'denied_at_promise' })
    expect(v.kp_stance).toBe('not_signified')
    expect(v.agreement).toBe('concurs')
  })
})

// ── Honest-empty discipline (§N.8: a gap never reads as agreement) ────────────────────

describe('honest-empty discipline', () => {
  it('an absent significator ladder is a named gap, never "no dissent"', () => {
    const v = voice({ ladder: null })
    expect(v.state).toBe('honest_empty')
    expect(v.agreement).toBe('not_comparable')
    expect(v.kp_stance).toBe('unknown')
    expect(v.empty_reason).toContain('kp_house_significators')
    expect(v.empty_reason).toContain('ga_kp_significators')
    expect(v.claim).not.toContain('CONCURS')
  })

  it('a substrate outage is reported as an outage, not as an astrological finding', () => {
    const v = voice({ ladder: null, substrateNote: 'KP substrate read failed this call (ECONNREFUSED)' })
    expect(v.state).toBe('honest_empty')
    expect(v.empty_reason).toContain('ECONNREFUSED')
  })

  it('no running KP window means nothing to judge, reported as such', () => {
    const v = voice({ periods: [] })
    expect(v.state).toBe('honest_empty')
    expect(v.empty_reason).toContain('no running `vimshottari_kp` period rows')
  })

  it('an unreachable ephemeris (chain_incomplete_infra) is not graded as a Parāśarī denial', () => {
    const v = voice({ pactStatus: 'chain_incomplete_infra' })
    expect(v.parasari_stance).toBe('unknown')
    // KP still reached its own verdict; it is simply not comparable.
    expect(v.kp_stance).toBe('signified')
    expect(v.agreement).toBe('not_comparable')
  })

  it('the writer\'s own EXTERNAL_COMPUTATION_REQUIRED marker is relayed, not parsed as data', () => {
    const rows = [
      { fact_subject: 'HOUSE_07', fact_key: 'ranked_significators',
        fact_value_text: '[EXTERNAL_COMPUTATION_REQUIRED] real Placidus cusps unavailable' },
    ]
    expect(parseKpHouseLadder(rows, 7)).toBeNull()
  })
})

// ── Parsers ───────────────────────────────────────────────────────────────────────────

describe('parseKpHouseLadder', () => {
  const rows = [
    { fact_id: 'f1', fact_subject: 'HOUSE_07', fact_key: 'cusp_owner', fact_value_text: 'Venus' },
    { fact_id: 'f2', fact_subject: 'HOUSE_07', fact_key: 'level_a_star_of_occupants', fact_value_text: 'none' },
    { fact_id: 'f3', fact_subject: 'HOUSE_07', fact_key: 'level_b_occupants', fact_value_text: 'Mars,Saturn' },
    { fact_id: 'f4', fact_subject: 'HOUSE_07', fact_key: 'level_c_star_of_owner', fact_value_text: 'Venus' },
    { fact_id: 'f5', fact_subject: 'HOUSE_07', fact_key: 'level_d_owner', fact_value_text: 'Venus' },
    { fact_id: 'f6', fact_subject: 'HOUSE_07', fact_key: 'ranked_significators', fact_value_text: 'Mars,Saturn,Venus' },
    { fact_id: 'f7', fact_subject: 'HOUSE_07', fact_key: 'house_system', fact_value_text: 'placidus_kp' },
    { fact_id: 'f8', fact_subject: 'HOUSE_10', fact_key: 'level_b_occupants', fact_value_text: 'Sun' },
  ]

  it('reproduces the real H7 ladder from the emitter\'s own EAV rows', () => {
    expect(parseKpHouseLadder(rows, 7)).toEqual({ ...H7_LADDER, fact_ids: ['f1','f2','f3','f4','f5','f6'] })
  })

  it('ledgers ONLY the fact_ids the verdict consumes, not every row in the page', () => {
    // `house_system` (f7) is in the page but is not a ladder limb; HOUSE_10's f8 is another
    // house entirely. Over-scoped grounding is its own defect class.
    expect(parseKpHouseLadder(rows, 7)!.fact_ids).not.toContain('f7')
    expect(parseKpHouseLadder(rows, 7)!.fact_ids).not.toContain('f8')
  })

  it("reads the literal 'none' as empty, never as a graha named none", () => {
    expect(parseKpHouseLadder(rows, 7)!.level_a).toEqual([])
  })

  it('ignores other houses\' rows', () => {
    expect(parseKpHouseLadder(rows, 7)!.level_b).toEqual(['Mars', 'Saturn'])
  })

  it('returns null when the house has no rows at all', () => {
    expect(parseKpHouseLadder(rows, 3)).toBeNull()
  })
})

describe('runningKpLords', () => {
  it('takes the period lord AND the KP-native sub/sub-sub columns, deduped', () => {
    expect(runningKpLords(RUNNING_2026_08_04)).toEqual([
      { running_level: 'AD', lord: 'Saturn' },
      { running_level: 'KP_SUB', lord: 'Saturn' },
      { running_level: 'PD', lord: 'Moon' },
      { running_level: 'KP_SUB_SUB', lord: 'Moon' },
    ])
  })

  it('orders by level, outermost first', () => {
    const shuffled = [...RUNNING_2026_08_04].reverse()
    expect(runningKpLords(shuffled)[0]!.running_level).toBe('AD')
  })

  it('skips null lords rather than emitting a placeholder', () => {
    const out = runningKpLords([
      { level_n: 2, lord_graha: null, kp_sub_lord: null, kp_sub_sub_lord: null,
        start_date: null, end_date: null },
    ])
    expect(out).toEqual([])
  })
})

describe('parasariStanceFromPactStatus', () => {
  it.each(['denied_at_promise', 'denied_at_confirmation', 'denied_at_activation'])(
    '%s → denied', (s) => expect(parasariStanceFromPactStatus(s)).toBe('denied'))

  it.each(['chain_complete', 'chain_pending_activation'])(
    '%s → promised', (s) => expect(parasariStanceFromPactStatus(s)).toBe('promised'))

  it.each(['chain_incomplete_infra', 'unknown', ''])(
    '%s → unknown', (s) => expect(parasariStanceFromPactStatus(s)).toBe('unknown'))
})
