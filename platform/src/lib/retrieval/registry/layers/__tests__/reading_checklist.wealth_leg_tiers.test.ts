/**
 * reading_checklist.wealth_leg_tiers.test.ts — TI-served-tier-legs.
 *
 * The three fixed-shape wealth evidence legs (special lagnas / yogi system / Tājika) used to
 * REQUIRE `verification_pass_status = 'two_pass_verified'` and fail closed (`source_incomplete`,
 * count 0) otherwise. The S-L1 tier-honesty rebuild stops stamping `two_pass_verified` on rows
 * nothing double-checked (special_lagna -> `single`; sensitive_point_yogi and the Vārṣaphala
 * year-lord rows -> `classical_match`), which would have gone dark serving over fully present
 * evidence. The legs now serve any tier that describes a computed value, CARRY the row's tier,
 * and report `verified_count` separately from presence; floored / unknown tiers stay refused.
 *
 * Real code path (the three fetchers + their predicate), SQL mocked at the `query` seam, same
 * style as reading_checklist.build_fence.test.ts.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { VERIFICATION_PASS_STATUS_VOCAB, isVerifiedPassStatus } from '../../../envelope'
import {
  fetchWealthSpecialLagnas,
  fetchWealthTajaka,
  fetchWealthYogiAvayogi,
  isWealthLegServableTier,
  WEALTH_LEG_REFUSED_TIERS,
  WEALTH_LEG_SERVABLE_TIERS,
  WEALTH_SPECIAL_LAGNAS,
  WEALTH_SPECIAL_LAGNA_KEYS,
  WEALTH_YOGI_SUBJECT_KEYS,
} from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const BUILD_ID = '11111111-1111-4111-8111-111111111111'

beforeEach(() => queryMock.mockReset())

const NUMERIC_LAGNA_KEYS = new Set(['longitude_sidereal', 'pada', 'house_d1'])

function lagnaRows(tier: string | null, overrides: Record<string, string | null> = {}) {
  return WEALTH_SPECIAL_LAGNAS.flatMap(subject => WEALTH_SPECIAL_LAGNA_KEYS.map(fact_key => ({
    fact_id: `${subject}-${fact_key}`,
    fact_subject: subject,
    fact_key,
    fact_value_num: NUMERIC_LAGNA_KEYS.has(fact_key) ? 12 : null,
    fact_value_text: NUMERIC_LAGNA_KEYS.has(fact_key) ? null : 'Aries',
    verification_pass_status: `${subject}|${fact_key}` in overrides ? overrides[`${subject}|${fact_key}`]! : tier,
  })))
}

function yogiRows(tier: string | null, overrides: Record<string, string | null> = {}) {
  return Object.entries(WEALTH_YOGI_SUBJECT_KEYS).flatMap(([fact_subject, keys]) => keys.map(fact_key => ({
    fact_id: `${fact_subject}-${fact_key}`,
    fact_subject,
    fact_key,
    fact_value_num: fact_key === 'point_longitude' ? 123.45 : null,
    fact_value_text: fact_key === 'point_longitude' ? null : 'Mercury',
    verification_pass_status: `${fact_subject}|${fact_key}` in overrides ? overrides[`${fact_subject}|${fact_key}`]! : tier,
  })))
}

function tajakaRow(tier: string | null) {
  return {
    varsha_id: 'annual-1', varsha_year: 42,
    varsha_start_iso: '2026-01-01T00:00:00.000Z', varsha_end_iso: '2027-01-01T00:00:00.000Z',
    year_lord_method: 'tajik_classical', year_lord: 'Jupiter',
    candidate_lord_jsonb: { Jupiter: 5 }, muntha_position_jsonb: { sign: 'Aries' },
    applicable_tajik_yogas_array: [], verification_pass_status: tier,
    citation_ref: 'tajaka-ref', citation_human: 'Tajaka citation.',
  }
}

/** Tiers a leg must REFUSE: every refused vocabulary member plus values outside the vocabulary. */
const REFUSED_FOR_LEGS: Array<string | null> = [
  ...WEALTH_LEG_REFUSED_TIERS, // includes 'floored'
  null,
  'unknown_tier',
  'PASS', // prohibited spelling — never case-folded into a served tier
  'Two_Pass_Verified',
]

describe('wealth-leg tier vocabulary law', () => {
  it('classifies every settled vocabulary member exactly once (a new member forces a serve/refuse decision)', () => {
    const vocab = VERIFICATION_PASS_STATUS_VOCAB.map(e => e.status)
    for (const status of vocab) {
      const inServable = WEALTH_LEG_SERVABLE_TIERS.has(status)
      const inRefused = WEALTH_LEG_REFUSED_TIERS.has(status)
      expect({ status, inServable, inRefused, exactlyOne: inServable !== inRefused })
        .toEqual({ status, inServable, inRefused, exactlyOne: true })
    }
    expect(WEALTH_LEG_SERVABLE_TIERS.size + WEALTH_LEG_REFUSED_TIERS.size).toBe(vocab.length)
  })

  it('serves every verified tier and never serves floored or no-value tiers', () => {
    for (const e of VERIFICATION_PASS_STATUS_VOCAB.filter(v => v.verified)) {
      expect(isWealthLegServableTier(e.status)).toBe(true)
    }
    for (const t of ['floored', 'not_defined_for_nodes', 'scope_cap_sentinel', 'skipped_malformed_source', 'external_computation_required']) {
      expect(isWealthLegServableTier(t)).toBe(false)
    }
    expect(isWealthLegServableTier(null)).toBe(false)
    expect(isWealthLegServableTier(undefined)).toBe(false)
  })
})

describe('fetchWealthSpecialLagnas — tier law', () => {
  it('today\'s data (two_pass_verified rows): still served, every row verified', async () => {
    queryMock.mockResolvedValueOnce({ rows: lagnaRows('two_pass_verified') })
    const r = await fetchWealthSpecialLagnas(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('served')
    expect(r.rows).toHaveLength(21)
    expect(r.tier_breakdown).toEqual({ two_pass_verified: 21 })
    expect(r.verified_count).toBe(21)
    expect(r.evidence_tier).toBe('verified')
    expect(r.incomplete_reason).toBeNull()
  })

  it('post-S-L1 data (single rows): served, rows carry their tier, verified_count is 0', async () => {
    queryMock.mockResolvedValueOnce({ rows: lagnaRows('single') })
    const r = await fetchWealthSpecialLagnas(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('served')
    expect(r.rows).toHaveLength(21)
    expect(r.rows.every(row => row.verification_pass_status === 'single')).toBe(true)
    expect(r.tier_breakdown).toEqual({ single: 21 })
    expect(r.verified_count).toBe(0)
    // present at an unverified tier is a SERVED state with its own marker — never source_incomplete
    expect(r.evidence_tier).toBe('present_at_unverified_tier')
    expect(r.incomplete_reason).toBeNull()
  })

  it('a mixed generation reports each tier and counts only the verified subset', async () => {
    queryMock.mockResolvedValueOnce({ rows: lagnaRows('single', { 'INDU_LAGNA|sign': 'two_pass_verified' }) })
    const r = await fetchWealthSpecialLagnas(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('served')
    expect(r.tier_breakdown).toEqual({ single: 20, two_pass_verified: 1 })
    expect(r.verified_count).toBe(1)
    expect(r.evidence_tier).toBe('mixed')
    expect(r.incomplete_reason).toBeNull()
  })

  it.each(REFUSED_FOR_LEGS.map(t => [String(t), t]))('refuses a leg with one %s atom (fail closed, no partial rows)', async (_name, tier) => {
    queryMock.mockResolvedValueOnce({ rows: lagnaRows('single', { 'HORA_LAGNA|house_d1': tier }) })
    const r = await fetchWealthSpecialLagnas(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('source_incomplete')
    expect(r.rows).toEqual([])
    expect(r.tier_breakdown).toEqual({})
    expect(r.verified_count).toBe(0)
    expect(r.evidence_tier).toBeNull()
    expect(r.incomplete_reason).toBe('unservable_tier')
  })
})

describe('fetchWealthYogiAvayogi — tier law', () => {
  it('today\'s data (two_pass_verified rows): still served, every row verified', async () => {
    queryMock.mockResolvedValueOnce({ rows: yogiRows('two_pass_verified') })
    const r = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('served')
    expect(r.rows).toHaveLength(12)
    expect(r.tier_breakdown).toEqual({ two_pass_verified: 12 })
    expect(r.verified_count).toBe(12)
    expect(r.evidence_tier).toBe('verified')
    expect(r.incomplete_reason).toBeNull()
  })

  it('post-S-L1 data (classical_match rows): served, rows carry their tier, verified_count is 0', async () => {
    queryMock.mockResolvedValueOnce({ rows: yogiRows('classical_match') })
    const r = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('served')
    expect(r.rows).toHaveLength(12)
    expect(r.rows.every(row => row.verification_pass_status === 'classical_match')).toBe(true)
    expect(r.tier_breakdown).toEqual({ classical_match: 12 })
    expect(r.verified_count).toBe(0)
    expect(r.evidence_tier).toBe('present_at_unverified_tier')
    expect(r.incomplete_reason).toBeNull()
  })

  it.each(REFUSED_FOR_LEGS.map(t => [String(t), t]))('refuses a leg with one %s atom (fail closed, no partial rows)', async (_name, tier) => {
    queryMock.mockResolvedValueOnce({ rows: yogiRows('classical_match', { 'SAHAYOGI|sign': tier }) })
    const r = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('source_incomplete')
    expect(r.rows).toEqual([])
    expect(r.tier_breakdown).toEqual({})
    expect(r.verified_count).toBe(0)
    expect(r.evidence_tier).toBeNull()
    expect(r.incomplete_reason).toBe('unservable_tier')
  })
})

describe('fetchWealthTajaka — tier law', () => {
  it('today\'s data (two_pass_verified row): still served, verified', async () => {
    queryMock.mockResolvedValueOnce({ rows: [tajakaRow('two_pass_verified')] })
    const r = await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')
    expect(r.state).toBe('served')
    expect(r.tier).toBe('two_pass_verified')
    expect(r.verified_count).toBe(1)
    expect(r.evidence_tier).toBe('verified')
    expect(r.incomplete_reason).toBeNull()
    expect(r.row?.verification_pass_status).toBe('two_pass_verified')
  })

  it('post-S-L1 data (classical_match row): served, carries its tier, verified_count is 0', async () => {
    queryMock.mockResolvedValueOnce({ rows: [tajakaRow('classical_match')] })
    const r = await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')
    expect(r.state).toBe('served')
    expect(r.row?.varsha_year).toBe(42)
    expect(r.tier).toBe('classical_match')
    expect(r.row?.verification_pass_status).toBe('classical_match')
    expect(r.verified_count).toBe(0)
    expect(r.evidence_tier).toBe('present_at_unverified_tier')
    expect(r.incomplete_reason).toBeNull()
  })

  it.each(REFUSED_FOR_LEGS.map(t => [String(t), t]))('refuses a %s year-lord row (fail closed, no row)', async (_name, tier) => {
    queryMock.mockResolvedValueOnce({ rows: [tajakaRow(tier)] })
    const r = await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')
    expect(r.state).toBe('source_incomplete')
    expect(r.row).toBeNull()
    expect(r.tier).toBeNull()
    expect(r.verified_count).toBe(0)
    expect(r.evidence_tier).toBeNull()
    expect(r.incomplete_reason).toBe('unservable_tier')
  })

  it('still demands exactly one as-of annual record and the tajik_classical method (tier relaxation loosens nothing else)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [tajakaRow('classical_match'), tajakaRow('classical_match')] })
    expect((await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')).state).toBe('source_incomplete')
    queryMock.mockResolvedValueOnce({ rows: [{ ...tajakaRow('classical_match'), year_lord_method: 'other' }] })
    expect((await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')).state).toBe('source_incomplete')
  })
})

describe('source_incomplete reasons stay distinct from present-at-unverified-tier', () => {
  it('a MISSING atom is evidence_missing_or_malformed, even when every present row is at a servable tier', async () => {
    queryMock.mockResolvedValueOnce({ rows: lagnaRows('single').slice(1) })
    const sl = await fetchWealthSpecialLagnas(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(sl.state).toBe('source_incomplete')
    expect(sl.incomplete_reason).toBe('evidence_missing_or_malformed')
    queryMock.mockResolvedValueOnce({ rows: yogiRows('classical_match').slice(1) })
    const y = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(y.state).toBe('source_incomplete')
    expect(y.incomplete_reason).toBe('evidence_missing_or_malformed')
  })

  it('a DUPLICATE atom is evidence_missing_or_malformed, not an unservable tier', async () => {
    const rows = yogiRows('classical_match')
    queryMock.mockResolvedValueOnce({ rows: [...rows, rows[0]!] })
    const y = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(y.state).toBe('source_incomplete')
    expect(y.incomplete_reason).toBe('evidence_missing_or_malformed')
  })

  it('no Tājika record (or two) is evidence_missing_or_malformed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    const none = await fetchWealthTajaka(CHART_ID, AYANAMSHA, BUILD_ID, '2026-09-19')
    expect(none.state).toBe('source_incomplete')
    expect(none.incomplete_reason).toBe('evidence_missing_or_malformed')
  })

  it('a failed read is source_unproven with NO incomplete_reason', async () => {
    queryMock.mockRejectedValueOnce(new Error('db down'))
    const r = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    expect(r.state).toBe('source_unproven')
    expect(r.incomplete_reason).toBeNull()
    expect(r.evidence_tier).toBeNull()
  })

  it('the three outcomes are three distinct (state, evidence_tier, incomplete_reason) triples', async () => {
    queryMock.mockResolvedValueOnce({ rows: yogiRows('classical_match') })
    const present = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    queryMock.mockResolvedValueOnce({ rows: yogiRows('classical_match').slice(1) })
    const missing = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    queryMock.mockResolvedValueOnce({ rows: yogiRows('floored') })
    const floored = await fetchWealthYogiAvayogi(CHART_ID, AYANAMSHA, BUILD_ID)
    const triples = [present, missing, floored].map(r => `${r.state}|${r.evidence_tier}|${r.incomplete_reason}`)
    expect(triples).toEqual([
      'served|present_at_unverified_tier|null',
      'source_incomplete|null|evidence_missing_or_malformed',
      'source_incomplete|null|unservable_tier',
    ])
  })
})

describe('verified_count uses the one settled definition of "verified"', () => {
  it('only two_pass_verified is verified today; classical_match / single are present, not verified', () => {
    expect(isVerifiedPassStatus('two_pass_verified')).toBe(true)
    expect(isVerifiedPassStatus('classical_match')).toBe(false)
    expect(isVerifiedPassStatus('single')).toBe(false)
  })
})
