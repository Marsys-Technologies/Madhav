/** KA-4b oracles. Classical sources: Muhūrta Cintāmaṇi vivāha-chapter parihāra verses as admitted in
 * ALGO 3.17 step 3 (KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md §3.17): v.88 (PG115:C2 + PG116:C1) Venus
 * debilitated → no doṣa even in the 6th; v.90 (PG116:C1) Moon in lagna → all doṣas perish; PG26 v.34
 * ṭīkā (general) Jupiter in a kendra → kṣaya/vṛddhi-tithi doṣa absent; PG109 v.65 ṭīkā: the chapter's
 * reckoning is not doṣa-producing in other undertakings. Envelopes follow the producer's output keys
 * (parihara_eval.py `evaluate_candidate`); the sky facts are the producer's, not recomputed here. */
import { readFileSync } from 'node:fs'
import { describe, expect, it, vi } from 'vitest'
import {
  RULE_METADATA_KEYS, evaluateScopedCancellation, parseCancellationRequest, projectCancellation, type CancellationRequest,
} from './parihara_cancellation'

const rule = (over: Record<string, unknown> = {}) => ({
  rule_id: 101, dosha_canonical_id: 'venus_sixth', scope: 'marriage',
  source_citation: 'Muhūrta Cintāmaṇi, Vivāha v.88 (PG116:C1)', source_chunk_id: 'muhurta_chintamani_pg0116_c01',
  source_verse: 88, extraction_context: 'tika_commentary', conjunction_reading: 'tika', tika_extension: false,
  priority_rank: null, net_standing: 'cancellable_by_condition', result: 'applies', reason: null, terms: [], ...over,
})
const envelope = (rules: Record<string, unknown>[], dosas: Record<string, unknown>[]) => ({
  evaluator_version: '1', ayanamsha: 'lahiri', rules, dosas, sky_coverage: { basis: 'start_mid_end_samples', complete: true, samples: [] },
})
const cancelledVenus = envelope([rule()],
  [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, by_rules: [101] }])
const request = (over: Partial<CancellationRequest> = {}): CancellationRequest => ({
  undertaking: 'marriage', candidate: { start_utc: '2026-11-20T04:00:00Z', end_utc: '2026-11-20T06:00:00Z' },
  location: { lat: 20.27, lon: 85.84, tz_offset_minutes: 330 }, location_basis: 'caller', dosas_present: ['venus_sixth'], ...over,
})

describe('in-scope planted doṣa with a parihāra row (v.88 Venus)', () => {
  it('reads cancelled and carries the citing rule\'s locator', () => {
    const out = projectCancellation('marriage', ['venus_sixth'], cancelledVenus)
    expect(out.in_scope).toBe(true)
    expect(out.dosas).toEqual([{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, citations: [{
      rule_id: 101, scope: 'marriage', source_citation: 'Muhūrta Cintāmaṇi, Vivāha v.88 (PG116:C1)',
      source_chunk_id: 'muhurta_chintamani_pg0116_c01', source_verse: 88, extraction_context: 'tika_commentary', result: 'applies' }] }])
  })
  it('reads cancelled for upanayana and general with their own admissible scopes', () => {
    for (const [undertaking, scope] of [['upanayana', 'upanayana'], ['general', 'general']] as const) {
      const env = envelope([rule({ scope })], [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, by_rules: [101] }])
      expect(projectCancellation(undertaking, ['venus_sixth'], env).dosas[0]).toMatchObject({ state: 'cancelled', citations: [{ scope }] })
    }
  })
  it('a general-scope clause (PG26 v.34 ṭīkā) cancels in marriage too', () => {
    const env = envelope([rule({ rule_id: 7, scope: 'general', dosha_canonical_id: 'kshaya_tithi', source_chunk_id: 'muhurta_chintamani_pg0026_c01', source_verse: 34 })],
      [{ dosha_canonical_id: 'kshaya_tithi', state: 'cancelled', reason: null, by_rules: [7] }])
    expect(projectCancellation('marriage', ['kshaya_tithi'], env).dosas[0]).toMatchObject({ state: 'cancelled', citations: [{ source_verse: 34 }] })
  })
})

describe('out-of-scope undertaking', () => {
  it('reads cancellation_unassessed, never clear, and never reaches the producer', async () => {
    const evaluate = vi.fn().mockResolvedValue(cancelledVenus)
    const out = await evaluateScopedCancellation(request({ undertaking: 'business' }), evaluate)
    expect(evaluate).not.toHaveBeenCalled()
    expect(out.in_scope).toBe(false)
    expect(out.dosas).toEqual([{ dosha_canonical_id: 'venus_sixth', state: 'cancellation_unassessed', reason: 'undertaking_out_of_scope', citations: [] }])
    expect(JSON.stringify(out)).not.toMatch(/clear/)
  })
  it('projection of a producer "cancelled" envelope is still refused for an out-of-scope undertaking', () => {
    expect(projectCancellation('griha_pravesh', ['venus_sixth'], cancelledVenus).dosas[0]).toMatchObject({ state: 'cancellation_unassessed', reason: 'undertaking_out_of_scope' })
  })
})

describe('scope admissibility (ALGO 3.17 step 3; PG109 v.65 ṭīkā)', () => {
  it('a marriage-scope rule cannot cancel a general or upanayana election', () => {
    for (const undertaking of ['general', 'upanayana']) {
      expect(projectCancellation(undertaking, ['venus_sixth'], cancelledVenus).dosas[0])
        .toMatchObject({ state: 'cancellation_unassessed', reason: 'rule_scope_not_admissible' })
    }
  })
  it('natal and muhurta scope rows never cancel', () => {
    for (const scope of ['natal', 'muhurta']) {
      const env = envelope([rule({ scope })], [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, by_rules: [101] }])
      expect(projectCancellation('marriage', ['venus_sixth'], env).dosas[0].state).toBe('cancellation_unassessed')
    }
  })
})

describe('cancellation needs a full source locator (B.3/B.10, N.8)', () => {
  it.each([['source_verse', 0], ['source_chunk_id', ''], ['source_citation', ' ']])('an applying rule with bad %s is not cancelled', (key, value) => {
    const env = envelope([rule({ [key]: value })], [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, by_rules: [101] }])
    expect(projectCancellation('marriage', ['venus_sixth'], env).dosas[0]).toMatchObject({ state: 'cancellation_unassessed', reason: 'uncited_cancellation' })
  })
  it('a producer "cancelled" with no applying rule is not cancelled', () => {
    const env = envelope([rule({ result: 'does_not_apply' })], [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, by_rules: [101] }])
    expect(projectCancellation('marriage', ['venus_sixth'], env).dosas[0]).toMatchObject({ state: 'cancellation_unassessed', reason: 'cancellation_not_supported_by_rule' })
  })
})

describe('honest nulls', () => {
  it('a doṣa the producer did not return is unassessed', () => {
    expect(projectCancellation('marriage', ['venus_sixth', 'mars_eighth'], cancelledVenus).dosas[1])
      .toMatchObject({ dosha_canonical_id: 'mars_eighth', state: 'cancellation_unassessed', reason: 'dosha_missing_from_evaluation' })
  })
  it.each([[null], [{}], [{ ...cancelledVenus, rules: 'x' }], [{ ...cancelledVenus, dosas: [{ dosha_canonical_id: 'venus_sixth', state: 'clear', by_rules: [] }] }]])(
    'a malformed envelope %# is a contract violation, not an empty ledger', env => {
      expect(projectCancellation('marriage', ['venus_sixth'], env).dosas[0]).toMatchObject({ state: 'cancellation_unassessed', reason: 'producer_contract_violation' })
    })
  it('the producer\'s readings_disagree (Mars v.88, U11:36) passes through with both rows cited', () => {
    const env = envelope([
      rule({ rule_id: 201, dosha_canonical_id: 'mars_eighth', result: 'applies' }),
      rule({ rule_id: 206, dosha_canonical_id: 'mars_eighth', result: 'does_not_apply', extraction_context: 'mula_reconstructed', source_chunk_id: 'muhurta_chintamani_pg0115_c02' })],
      [{ dosha_canonical_id: 'mars_eighth', state: 'cancellation_unassessed', reason: 'readings_disagree', by_rules: [201, 206] }])
    const d = projectCancellation('marriage', ['mars_eighth'], env).dosas[0]
    expect(d).toMatchObject({ state: 'cancellation_unassessed', reason: 'readings_disagree' })
    expect(d.citations.map(c => c.rule_id)).toEqual([201, 206])
  })
  it('residual (evaluated, not cancelled) stays residual and is never rewritten to a clean state', () => {
    const env = envelope([rule({ result: 'does_not_apply' })], [{ dosha_canonical_id: 'venus_sixth', state: 'residual', reason: null, by_rules: [101] }])
    expect(projectCancellation('marriage', ['venus_sixth'], env).dosas[0].state).toBe('residual')
  })
  it('a producer failure names its reason and reads unassessed', async () => {
    for (const [error, reason] of [[new Error('parihara_source_unavailable'), 'parihara_source_unavailable'], [new TypeError('fetch failed: ECONNREFUSED'), 'producer_unavailable']] as const) {
      const out = await evaluateScopedCancellation(request(), vi.fn().mockRejectedValue(error))
      expect(out.dosas[0]).toMatchObject({ state: 'cancellation_unassessed', reason })
    }
  })
})

describe('request contract', () => {
  it('requires explicit undertaking, interval, place and non-wildcard targets', () => {
    expect(parseCancellationRequest(request())).toMatchObject({ undertaking: 'marriage', dosas_present: ['venus_sixth'] })
    for (const bad of [{ undertaking: '' }, { location: undefined }, { dosas_present: [] }, { dosas_present: ['*'] }, { candidate: { start_utc: 'x' } }, { location_basis: 'default' }]) {
      expect(typeof parseCancellationRequest({ ...request(), ...bad })).toBe('string')
    }
  })
})

describe('typed source contract tracks its producer (drift detector)', () => {
  it('RULE_METADATA_KEYS equals parihara_eval.py _METADATA, and the producer states the same contract', () => {
    const source = readFileSync(new URL('../../../../../../python-sidecar/services/ka_muhurta_seva/parihara_eval.py', import.meta.url), 'utf8')
    const block = /_METADATA = \(([^)]*)\)/s.exec(source)![1]
    expect([...block.matchAll(/"([a-z_]+)"/g)].map(m => m[1])).toEqual([...RULE_METADATA_KEYS])
    for (const key of ['state=', '"by_rules"', '"rule_id"', '"evaluator_version"', 'result=']) expect(source).toContain(key)
  })
})
