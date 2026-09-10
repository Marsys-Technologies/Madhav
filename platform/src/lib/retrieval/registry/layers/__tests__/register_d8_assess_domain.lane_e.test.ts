/**
 * register_d8_assess_domain.lane_e.test.ts — γ Stream, Lane E (Elevation Campaign v2.1)
 * ============================================================================
 * Covers the 5 Lane E deliverables against assess_wealth / assess_career:
 *   1. EL-44 — deterministic verdict layer (3-5 grounded clauses).
 *   2. R6-composite-score — by_stage signals carry real composite_score (not null);
 *      the graha_shadbala_ranking (EL-59/20 rank vocabulary) is populated; identical
 *      question_lenses are deduped.
 *   3. EL-45 — assess_wealth consumes D2+D11+Indu-Lagna directly (never a stub); the
 *      CI-assertable rule loop asserts every DOMAIN_DIRECT_VARGAS entry is non-stub.
 *   4. EL-55 covered separately in ranking/__tests__/priors_config_varga_citation.test.ts.
 *   5. EL-57 — contradictions are domain-filtered with an honest domain-scoped empty.
 *
 * DB-mocked (no live DB): `query` routes on SQL text; sub-capabilities mocked at their
 * dynamic-import specifiers (mirrors register_d8_verdict_skeleton.test.ts's pattern).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

const domainReadingHandler = vi.fn()
const temporalHandler = vi.fn()
const contradictionsHandler = vi.fn()
const signalsHandler = vi.fn()
const yogaFiringsHandler = vi.fn()

vi.mock('../L2_bodha/query_domain_reading', () => ({
  queryDomainReadingCapability: { handler: (...a: unknown[]) => domainReadingHandler(...a) },
}))
vi.mock('../L3_kala/query_temporal_activation', () => ({
  queryTemporalActivationCapability: { handler: (...a: unknown[]) => temporalHandler(...a) },
}))
vi.mock('../L2_bodha/query_contradictions', () => ({
  queryContradictionsCapability: { handler: (...a: unknown[]) => contradictionsHandler(...a) },
}))
vi.mock('../L2_bodha/query_signals', () => ({
  querySignalsCapability: { handler: (...a: unknown[]) => signalsHandler(...a) },
}))
vi.mock('../L1_ganita/get_yoga_firings', () => ({
  getYogaFiringsCapability: { handler: (...a: unknown[]) => yogaFiringsHandler(...a) },
}))
vi.mock('../../address_resolver', () => ({
  resolveAddress: vi.fn().mockRejectedValue(new Error('no live DB in test')),
}))

import { clearRegistry, getCapability } from '../../index'
import { registerD8AssessDomainCapabilities, DOMAIN_DIRECT_VARGAS } from '../register_d8_assess_domain'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'

function sig(id: string, cls: string, sss = 'structural') {
  return {
    signal_id: id,
    signal_type_class: cls,
    source_subsystem: sss,
    signal_summary_text: `summary-${id}`,
    computed_salience: 0.5,
    domains_affected_array: ['wealth', 'career'],
    constituent_facts_array: [`fact-${id}-a`, `fact-${id}-b`],
  }
}

// ── query() router — dispatches on SQL text so every DB touchpoint this file's new
// code exercises (stagePool, fetchL1Context ×2, buildVargaAnalysisDirect ×3) gets a
// realistic, distinguishable answer instead of one undifferentiated mock. ──────────
// F-164: mirrors migration 435_ga_vichara.sql's brahma_vichara_constants seed exactly —
// DOMAIN_DIRECT_VARGAS is now a live read of this row (minus D1), not a hardcoded literal.
const OPERATIVE_VARGAS_FIXTURE = {
  wealth:   { vargas: ['D1', 'D2', 'D9', 'D11'], provisional: false, houses: [2, 11], karaka: 'Jupiter' },
  career:   { vargas: ['D1', 'D10', 'D9'], provisional: true, houses: [10], karaka: 'Saturn' },
  marriage: { vargas: ['D1', 'D9', 'D7'], provisional: true, houses: [7], karaka: 'Venus' },
  health:   { vargas: ['D1', 'D6', 'D9'], provisional: true, houses: [6], karaka: 'Saturn' },
  general:  { vargas: ['D1', 'D9'], provisional: true, houses: [1], karaka: 'Sun' },
}

function installQueryRouter() {
  queryMock.mockImplementation(async (sql: string, params: unknown[]) => {
    const s = String(sql)
    if (s.includes('brahma_vichara_constants')) {
      return { rows: [{ value_jsonb: OPERATIVE_VARGAS_FIXTURE }] }
    }
    if (s.includes('FROM bodha_msr_signals') && s.includes('domains_affected_array')) {
      return {
        rows: [
          sig('par-1', 'parivartana'),
          sig('yog-1', 'yoga', 'yoga'),
          sig('cfg-1', 'configuration'),
          sig('kar-1', 'karaka_alignment'),
          sig('var-1', 'varga_pattern', 'varga'),
        ],
      }
    }
    if (s.includes("fact_category IN ('graha_shadbala_total', 'graha_dignity_per_varga')")) {
      // fetchL1Context query 1 — shadbala + D1 dignity
      return {
        rows: [
          { fact_category: 'graha_shadbala_total', fact_subject: 'SUN', fact_value_num: 3.1 },
          { fact_category: 'graha_shadbala_total', fact_subject: 'MOON', fact_value_num: 4.2 },
          { fact_category: 'graha_shadbala_total', fact_subject: 'MAR', fact_value_num: 2.5 },
          { fact_category: 'graha_shadbala_total', fact_subject: 'MER', fact_value_num: 3.6 },
          { fact_category: 'graha_shadbala_total', fact_subject: 'JUP', fact_value_num: 4.8 },
          { fact_category: 'graha_shadbala_total', fact_subject: 'VEN', fact_value_num: 1.7 },
          { fact_category: 'graha_shadbala_total', fact_subject: 'SAT', fact_value_num: 2.9 },
        ],
      }
    }
    if (s.includes('FROM chart_dashas')) {
      return { rows: [{ level: 1, dasha_lord: 'SATURN' }] }
    }
    if (s.includes("fact_category = 'graha_dignity_per_varga'") && s.includes("fact_value_jsonb->>'varga'")) {
      // EL-45 direct varga-dignity query — params: [chart_id, ayanamsha_id, vargas[]]
      const vargas = params[2] as string[]
      const rows: Record<string, unknown>[] = []
      for (const v of vargas) {
        rows.push({
          fact_id: `fid-${v}-SUN`, fact_subject: `${v}_SUN`, fact_value_text: 'own',
          fact_value_jsonb: { varga: v, sign: 'Leo', house: 1 },
        })
        rows.push({
          fact_id: `fid-${v}-JUP`, fact_subject: `${v}_JUP`, fact_value_text: 'exalted',
          fact_value_jsonb: { varga: v, sign: 'Cancer', house: 12 },
        })
      }
      return { rows }
    }
    if (s.includes("fact_category = 'ashtakavarga_pinda_sarva_per_varga'")) {
      // Simulate the real, documented data-plane gap: D2 has AV rows, D11 does not.
      const vargas = params[2] as string[]
      const rows: Record<string, unknown>[] = []
      if (vargas.includes('D2')) {
        rows.push({ fact_id: 'av-d2-sun', fact_subject: 'SUN', fact_key: 'D2', fact_value_num: 48 })
        rows.push({ fact_id: 'av-d2-sarva', fact_subject: 'SARVA', fact_key: 'D2', fact_value_num: 336 })
      }
      if (vargas.includes('D10')) {
        rows.push({ fact_id: 'av-d10-sun', fact_subject: 'SUN', fact_key: 'D10', fact_value_num: 48 })
      }
      // D11 intentionally yields zero rows (the honest gap under test).
      return { rows }
    }
    if (s.includes("fact_category = 'special_lagna'") && s.includes('INDU_LAGNA')) {
      return {
        rows: [
          { fact_id: 'indu-sign', fact_key: 'sign', fact_value_text: 'Scorpio' },
          { fact_id: 'indu-lord', fact_key: 'sign_lord', fact_value_text: 'Mars' },
          { fact_id: 'indu-house', fact_key: 'house_d1', fact_value_num: 8 },
        ],
      }
    }
    return { rows: [] }
  })
}

beforeEach(() => {
  queryMock.mockReset()
  installQueryRouter()
  domainReadingHandler.mockReset()
  temporalHandler.mockReset()
  contradictionsHandler.mockReset()
  signalsHandler.mockReset()
  yogaFiringsHandler.mockReset()

  domainReadingHandler.mockResolvedValue({
    is_error: false,
    content: { question_lenses: [], signal_id_refs: [], cdlm_cells: [], lens_count: 0 },
  })
  temporalHandler.mockResolvedValue({
    is_error: false,
    content: { activations: [], predicates: [], activation_count: 0, signal_id_refs: [] },
  })
  contradictionsHandler.mockResolvedValue({
    is_error: false,
    content: { contradiction_count: 0, discoveries: [] },
  })
  signalsHandler.mockResolvedValue({
    is_error: false,
    content: {
      signals: Array.from({ length: 5 }, (_, i) => ({ ...sig(`comp-${i}`, 'composite_state'), composite_score: 0.8 - i * 0.1 })),
      ranking_basis: { mode: 'composite_4d', priors_version: '1.2', domain: 'wealth' },
    },
  })
  yogaFiringsHandler.mockResolvedValue({ is_error: false, content: { rows: [] } })
})

async function run(uri: string, args: Record<string, unknown> = {}) {
  clearRegistry()
  registerD8AssessDomainCapabilities()
  const cap = getCapability(uri)
  expect(cap).toBeDefined()
  const res = await cap!.handler({ chart_id: CHART_ID, ayanamsha_id: AYA, ...args }, undefined)
  expect(res.is_error).toBe(false)
  return res.content as Record<string, unknown>
}

describe('EL-44 — deterministic verdict layer', () => {
  it('assess_wealth serves a `verdict` with 3-5 grounded clauses, deterministic template', async () => {
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const verdict = content['verdict'] as Record<string, unknown>
    expect(verdict).toBeDefined()
    expect(verdict['template']).toBe('deterministic_v1')
    const clauses = verdict['clauses'] as Array<Record<string, unknown>>
    expect(clauses.length).toBeGreaterThanOrEqual(3)
    expect(clauses.length).toBeLessThanOrEqual(5)
    for (const c of clauses) {
      expect(typeof c['text']).toBe('string')
      expect(Array.isArray(c['fact_ids'])).toBe(true)
      expect(typeof c['grounded']).toBe('boolean')
    }
  })
})

describe('R6-composite-score — by_stage signals carry real composite_score', () => {
  it('stagePool-derived by_stage.lord/karaka/yoga/varga signals are NOT null composite_score', async () => {
    const content = await run('marsys://tool/L-DOMAIN/assess_career')
    const vs = content['verdict_skeleton'] as Record<string, unknown>
    const byStage = vs['by_stage'] as Record<string, Array<Record<string, unknown>>>
    const populated = [...byStage['lord']!, ...byStage['yoga']!, ...byStage['karaka']!, ...byStage['varga']!]
    expect(populated.length).toBeGreaterThan(0)
    for (const s of populated) {
      expect(s['composite_score'], `${String(s['signal_id'])} composite_score should be a real number, not null`).not.toBeNull()
      expect(typeof s['composite_score']).toBe('number')
    }
  })
})

describe('EL-59/20 — graha shadbala rank vocabulary', () => {
  it('stage_status.strength.graha_shadbala_ranking carries rank + population_size + rank_basis on every entry', async () => {
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const vs = content['verdict_skeleton'] as Record<string, unknown>
    const status = vs['stage_status'] as Record<string, Record<string, unknown>>
    const ranking = status['strength']!['graha_shadbala_ranking'] as Array<Record<string, unknown>>
    expect(ranking.length).toBeGreaterThan(0)
    for (const r of ranking) {
      expect(r).toHaveProperty('rank')
      expect(r).toHaveProperty('population_size')
      expect(r).toHaveProperty('rank_basis')
      expect(r).toHaveProperty('rank_statement')
    }
    // by_stage.strength itself stays honestly empty (MSR has no strength signal class) —
    // the ranking above is an ADDITIVE real-data field, not a replacement of that invariant.
    const byStage = vs['by_stage'] as Record<string, unknown[]>
    expect(byStage['strength']).toEqual([])
  })
})

describe('EL-45 — direct varga/AV consumption, never a stub', () => {
  it('assess_wealth consumes D2 + D11 + Indu Lagna directly, with an honest D11-AV gap disclosure', async () => {
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const va = content['varga_analysis'] as Record<string, unknown>
    expect(va['direct_consumption']).toBe(true)
    // F-164: the live-read set now includes D9 (the old ['D2','D11'] literal had drifted).
    expect(va['consumed_vargas']).toEqual(['D2', 'D9', 'D11'])
    expect(va['indu_lagna']).toBeDefined()
    const perVarga = va['per_varga'] as Record<string, Record<string, unknown>>
    expect(perVarga['D2']!['ashtakavarga_available']).toBe(true)
    expect(perVarga['D11']!['ashtakavarga_available']).toBe(false)
    expect(String(perVarga['D11']!['empty_reason'])).toMatch(/data-plane gap|not.*computed/i)
    // D11's sign/house/dignity ARE real and directly consumed even though AV isn't built yet.
    expect((perVarga['D11']!['graha_dignity'] as unknown[]).length).toBeGreaterThan(0)
  })

  it('CI-assertable rule: every DOMAIN_DIRECT_VARGAS entry produces direct_consumption:true (no classical-layer stub)', async () => {
    // Runs assess_wealth and assess_career (the two flagship domains this lane wires) and
    // asserts their varga_analysis is never the old "see chart_facts_query" stub shape.
    const wealthContent = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const careerContent = await run('marsys://tool/L-DOMAIN/assess_career')
    for (const [domain, content] of [['wealth', wealthContent], ['career', careerContent]] as const) {
      const va = content['varga_analysis'] as Record<string, unknown>
      expect(va['direct_consumption'], `${domain} varga_analysis must not be a stub`).toBe(true)
      expect(va['consumed_vargas']).toEqual(DOMAIN_DIRECT_VARGAS[domain])
      // The old stub shape was exactly {note, drill_uri} with no consumed_vargas/per_varga —
      // assert the new shape actually carries per-graha data, not just a pointer.
      expect(va['per_varga']).toBeDefined()
    }
  })
})

describe('EL-57 — domain-filtered contradiction surface with honest empty', () => {
  it('filters contradictions to this domain and states the chart-wide count alongside', async () => {
    contradictionsHandler.mockResolvedValue({
      is_error: false,
      content: {
        contradictions: [
          { contradiction_id: 'c1', domains_affected_array: ['wealth'] },
          { contradiction_id: 'c2', domains_affected_array: ['career'] },
        ],
        discoveries: [],
      },
    })
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const contra = content['contradictions'] as Record<string, unknown>
    expect(contra['status']).toBe('ok')
    expect(contra['chart_wide_contradiction_count']).toBe(2)
    expect(contra['domain_filtered']).toBe(true)
    const items = contra['items'] as Array<Record<string, unknown>>
    expect(items).toHaveLength(1)
    expect(items[0]!['contradiction_id']).toBe('c1')
  })

  it('reports an explicit honest empty when contradictions exist chart-wide but none tag this domain', async () => {
    contradictionsHandler.mockResolvedValue({
      is_error: false,
      content: {
        contradictions: [
          { contradiction_id: 'c1', domains_affected_array: ['wealth'] },
          { contradiction_id: 'c2', domains_affected_array: ['wealth'] },
        ],
        discoveries: [],
      },
    })
    const content = await run('marsys://tool/L-DOMAIN/assess_career')
    const contra = content['contradictions'] as Record<string, unknown>
    expect(contra['status']).toBe('no_contradictions_in_domain')
    expect(contra['chart_wide_contradiction_count']).toBe(2)
    expect(String(contra['note'])).toMatch(/no contradictions found for this domain|none are tagged/i)
  })

  it('distinguishes chart-wide no_data (0 rows total) from domain-empty (0 of N rows)', async () => {
    contradictionsHandler.mockResolvedValue({
      is_error: false,
      content: { contradictions: [], discoveries: [] },
    })
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const contra = content['contradictions'] as Record<string, unknown>
    expect(contra['status']).toBe('no_data')
  })
})

describe('R6-lens-dedup — identical question_lenses collapsed', () => {
  it('two question_types with byte-identical signal_ids collapse into one served lens block', async () => {
    const identicalIds = ['s1', 's2', 's3']
    domainReadingHandler.mockResolvedValue({
      is_error: false,
      content: {
        question_lenses: [
          {
            lens_id: 'lens-property', question_type: 'property',
            template_element_ids_jsonb: { signal_ids: identicalIds },
            all_relevant_ranked_jsonb: { ranked_signals: [] },
          },
          {
            lens_id: 'lens-wealth', question_type: 'wealth',
            template_element_ids_jsonb: { signal_ids: identicalIds },
            all_relevant_ranked_jsonb: { ranked_signals: [] },
          },
        ],
        signal_id_refs: [], cdlm_cells: [], lens_count: 2,
      },
    })
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const ha = content['house_analysis'] as Record<string, unknown>
    const lenses = ha['question_lenses'] as Array<Record<string, unknown>>
    expect(lenses).toHaveLength(1)
    expect(lenses[0]!['is_deduped']).toBe(true)
    expect(lenses[0]!['collapsed_question_types']).toEqual(['property', 'wealth'])
    expect(ha['lenses_deduped_count']).toBe(1)
  })

  it('distinct-signal-set lenses are NOT collapsed', async () => {
    domainReadingHandler.mockResolvedValue({
      is_error: false,
      content: {
        question_lenses: [
          {
            lens_id: 'lens-a', question_type: 'property',
            template_element_ids_jsonb: { signal_ids: ['s1', 's2'] },
            all_relevant_ranked_jsonb: { ranked_signals: [] },
          },
          {
            lens_id: 'lens-b', question_type: 'wealth',
            template_element_ids_jsonb: { signal_ids: ['s9', 's10'] },
            all_relevant_ranked_jsonb: { ranked_signals: [] },
          },
        ],
        signal_id_refs: [], cdlm_cells: [], lens_count: 2,
      },
    })
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')
    const ha = content['house_analysis'] as Record<string, unknown>
    expect((ha['question_lenses'] as unknown[])).toHaveLength(2)
    expect(ha['lenses_deduped_count']).toBe(0)
  })
})

// ── ŚODHANA T5 (PŪRTI): the joined classical legs + reading_checklist ──────────────
describe('T5 (PŪRTI) — computed-but-never-joined legs + reading_checklist on assess_wealth', () => {
  it('assess_wealth carries kp_cusp_chain, sensitive_degree_firings, gochara_sweep, and a reading_checklist (AC2/AC3 structural presence)', async () => {
    const content = await run('marsys://tool/L-DOMAIN/assess_wealth')

    // AC2: the KP cuspal chain is present in assess_wealth's OWN response (not tail-only).
    const kp = content['kp_cusp_chain'] as Record<string, unknown>
    expect(kp).toBeDefined()
    expect(Array.isArray(kp['cusps'])).toBe(true)

    // The other two joined legs are present as their own slots.
    expect(Array.isArray(content['sensitive_degree_firings'])).toBe(true)
    const gochara = content['gochara_sweep'] as Record<string, unknown>
    expect(gochara).toBeDefined()
    expect('domain_covered' in gochara).toBe(true)

    // AC3: the reading_checklist receipt is present and names every classical unit.
    const rc = content['reading_checklist'] as Record<string, unknown>
    expect(rc).toBeDefined()
    const units = rc['units'] as Array<Record<string, unknown>>
    const names = new Set(units.map(u => u['unit']))
    expect(names.has('kp_cusp_chain')).toBe(true)
    expect(names.has('sensitive_degree_firings')).toBe(true)
    expect(names.has('gochara_sweep')).toBe(true)
    expect(names.has('yogi_avayogi')).toBe(true)
    expect('non_exhaustive' in rc).toBe(true)

    // AC3 truthfulness cross-count: the checklist's claimed state for each leg must match
    // what is actually served (under this mock the legs resolve empty → NOT 'served').
    const byName = new Map(units.map(u => [u['unit'] as string, u]))
    const kpServed = (kp['cusps'] as unknown[]).length
    if (byName.get('kp_cusp_chain')!['state'] === 'served') expect(kpServed).toBeGreaterThan(0)
    else expect(kpServed).toBe(0)
    const sensServed = (content['sensitive_degree_firings'] as unknown[]).length
    if (byName.get('sensitive_degree_firings')!['state'] === 'served') expect(sensServed).toBeGreaterThan(0)
    else expect(sensServed).toBe(0)
  })
})
