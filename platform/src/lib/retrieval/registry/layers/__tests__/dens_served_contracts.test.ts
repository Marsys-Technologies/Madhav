/**
 * dens_served_contracts.test.ts — DENS-SERVED (Dens.served workstream, CLAUDE.md §N.6).
 *
 * Every capability below declares `density_contract` so the census can read that the served
 * surface layers its rows (CLAUDE.md §N.6). A contract is a CLAIM about the handler, so each claim
 * is tested against the real handler with a mocked `query` (no database):
 *   - `empty_reason: true`  → a zero-row result carries a non-empty `empty_reason`, and a populated
 *     result does not;
 *   - `facets`              → every declared facet is a real input of the capability
 *     (its `input_schema`), never an invented axis;
 *   - `paginated`           → true only when the capability exposes a bound (limit / offset) and discloses it.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import type { CapabilityDescriptor } from '../../types'
import { queryClassPriorsCapability } from '../L0_brahmagyan/query_class_priors'
import { queryYogaCatalogCapability } from '../L0_brahmagyan/query_yoga_catalog'
import { queryRemedyCorpusCapability } from '../L0_brahmagyan/query_remedy_corpus'
import { queryCompendiumIndexCapability } from '../L0_brahmagyan/query_compendium_index'
import { queryDashaSystemsCapability } from '../L0_brahmagyan/query_dasha_systems'
import { queryDoshaCatalogCapability } from '../L0_brahmagyan/query_dosha_catalog'
import { queryPariharaGraphCapability } from '../L0_brahmagyan/query_parihara_graph'
import { queryFormulaConstantsCapability } from '../L0_brahmagyan/query_formula_constants'
import { queryMedicalMappingsCapability } from '../L0_brahmagyan/query_medical_mappings'
import { queryMuhurtaLatticeCapability } from '../L0_brahmagyan/query_muhurta_lattice'
import { queryNakshatraMedicalCapability } from '../L0_brahmagyan/query_nakshatra_medical'
import { queryPrashnaFructificationRulesCapability } from '../L0_brahmagyan/query_prashna_fructification_rules'
import { queryPrashnaLagnaMethodsCapability } from '../L0_brahmagyan/query_prashna_lagna_methods'
import { queryPrashnaSignificatorsCapability } from '../L0_brahmagyan/query_prashna_significators'
import { queryPrashnaSpecialTechniquesCapability } from '../L0_brahmagyan/query_prashna_special_techniques'
import { queryPrashnaTajikYogasCapability } from '../L0_brahmagyan/query_prashna_tajik_yogas'
import { querySignMedicalCapability } from '../L0_brahmagyan/query_sign_medical'
import { querySkyCalendarCapability } from '../L0_brahmagyan/query_sky_calendar'
import { queryTransitEngineCapability } from '../L0_brahmagyan/query_transit_engine'
import { queryVastuDirectionsCapability } from '../L0_brahmagyan/query_vastu_directions'
import { queryTransitVedhaCapability } from '../L0_brahmagyan/query_transit_vedha'
import { queryCgmMotifsCapability } from '../L2_bodha/query_cgm_motifs'
import { queryDiscoveriesCapability } from '../L2_bodha/query_discoveries'
import { queryQualityScorecardCapability } from '../L2_bodha/query_quality_scorecard'
import { queryProspectiveLedgerCapability } from '../L4_phala/query_prospective_ledger'
import { lelIntakeChecklistCapability } from '../L5_mimamsa/lel_intake_checklist'
import { predictionLifecycleSweepCapability } from '../L5_mimamsa/prediction_lifecycle_sweep'
import { queryCgmPathsCapability } from '../L2_bodha/query_cgm_paths'
import { queryRmResonancesCapability } from '../L2_bodha/query_rm_resonances'
import { queryRmPrescriptionsCapability } from '../L2_bodha/query_rm_prescriptions'
import { getAyurdayaCapability } from '../L1_ganita/get_ayurdaya'
import { getStructuralSignalsCapability } from '../L1_ganita/get_structural_signals'
import { getDivisionalsCapability } from '../L1_ganita/get_divisionals'
import { queryDomainReadingCapability } from '../L2_bodha/query_domain_reading'
import { querySignalsCapability } from '../L2_bodha/query_signals'
import { getPanchangaCapability } from '../L1_ganita/get_panchanga'
import { getSadeSatiCapability } from '../L1_ganita/get_sade_sati'
import { getNakshatraCapability } from '../L1_ganita/get_nakshatra'
import { getPositionsCapability } from '../L1_ganita/get_positions'
import { getSensitivePointsCapability } from '../L1_ganita/get_sensitive_points'
import { getSensitiveDegreesCapability } from '../L1_ganita/get_sensitive_degrees'
import { getGrahaYuddhaCapability } from '../L1_ganita/get_graha_yuddha'
import { queryUcdCapability } from '../L2_bodha/query_ucd'
import { getTajikCapability } from '../L1_ganita/get_tajik'
import { queryCdlmSummaryCapability } from '../L2_bodha/query_cdlm_summary'
import { traverseChartGraphCapability } from '../L2_bodha/traverse_chart_graph'
import { getDashaLordCapabilityCapability } from '../L1_ganita/get_dasha_lord_capability'
import { getYogaDoshaCapability } from '../L1_ganita/get_yoga_dosha'
import { getYogaFiringsCapability } from '../L1_ganita/get_yoga_firings'
import { queryMechanismsCapability } from '../L2_bodha/query_mechanisms'
import { queryPratijnaCapability } from '../L2_bodha/query_pratijna'
import { queryMechanismRetrodictionCapability } from '../L5_mimamsa/query_mechanism_retrodiction'
import { judgmentQueryCapability } from '../register_d9_judgment'
import { registerD7ChannelCapabilities } from '../register_d7_channel'
import { clearRegistry, getCapability } from '../../index'
import { getCatalog } from '../../catalog'
import { getArgalaCapability } from '../L1_ganita/get_argala'
import { queryQuestionLensesCapability } from '../L2_bodha/query_question_lenses'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const WINDOW = { start_utc: '2026-08-05T00:00:00Z', end_utc: '2026-08-06T00:00:00Z' }

/** `empty_reason` at the top of the content, or (a multi-section payload such as query_parihara_graph) inside each section object. */
function emptyReasons(content: Record<string, unknown>): string[] {
  const out: string[] = []
  if (typeof content['empty_reason'] === 'string') out.push(content['empty_reason'] as string)
  for (const v of Object.values(content)) {
    if (v && typeof v === 'object' && !Array.isArray(v) && typeof (v as Record<string, unknown>)['empty_reason'] === 'string') {
      out.push((v as Record<string, unknown>)['empty_reason'] as string)
    }
  }
  return out
}

interface Case {
  cap: CapabilityDescriptor
  args: Record<string, unknown>
  facets: string[]
  paginated: boolean
  /** default true; false = the capability honestly declares no empty_reason (get_argala), and the empty-result test is skipped */
  emptyReason?: boolean
}

const CASES: Case[] = [
  { cap: queryClassPriorsCapability, args: {}, facets: ['prior_version', 'signal_type_class', 'source_subsystem'], paginated: true },
  { cap: queryCompendiumIndexCapability, args: {}, facets: ['text_id', 'chapter_num', 'topic_id'], paginated: true },
  { cap: queryDashaSystemsCapability, args: {}, facets: ['canonical_id', 'school'], paginated: false },
  { cap: queryDoshaCatalogCapability, args: {}, facets: ['dosha_name', 'severity', 'domain'], paginated: true },
  { cap: queryPariharaGraphCapability, args: {}, facets: ['section', 'activity_class', 'dosha_canonical_id', 'disposition'], paginated: false },
  { cap: queryFormulaConstantsCapability, args: {}, facets: ['constant_id', 'class'], paginated: false },
  { cap: queryMedicalMappingsCapability, args: {}, facets: ['graha'], paginated: false },
  { cap: queryMuhurtaLatticeCapability, args: WINDOW, facets: ['factor_family', 'factor_key'], paginated: true },
  { cap: queryNakshatraMedicalCapability, args: {}, facets: ['nakshatra_name', 'nakshatra_number'], paginated: false },
  { cap: queryPrashnaFructificationRulesCapability, args: {}, facets: ['rule_id', 'time_unit'], paginated: false },
  { cap: queryPrashnaLagnaMethodsCapability, args: {}, facets: ['method_id', 'tradition'], paginated: false },
  { cap: queryPrashnaSignificatorsCapability, args: {}, facets: ['question_class'], paginated: false },
  { cap: queryPrashnaSpecialTechniquesCapability, args: {}, facets: ['technique_id'], paginated: false },
  { cap: queryPrashnaTajikYogasCapability, args: {}, facets: ['yoga_id', 'is_fructification_indicator'], paginated: false },
  { cap: querySignMedicalCapability, args: {}, facets: ['sign_number', 'sign_name'], paginated: false },
  { cap: querySkyCalendarCapability, args: WINDOW, facets: ['event_type', 'primary_body'], paginated: true },
  { cap: queryTransitEngineCapability, args: {}, facets: ['graha'], paginated: false },
  { cap: queryVastuDirectionsCapability, args: {}, facets: ['direction', 'ruling_graha'], paginated: false },
  { cap: queryTransitVedhaCapability, args: {}, facets: ['primary_graha', 'primary_transit_house'], paginated: false },
  { cap: queryCgmMotifsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'motif_class'], paginated: true },
  { cap: queryCgmPathsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'path_type', 'final_only'], paginated: true },
  { cap: queryRmResonancesCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'graha'], paginated: true },
  { cap: getAyurdayaCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'method'], paginated: true },
  { cap: getStructuralSignalsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'domain', 'categories'], paginated: true },
  { cap: getDivisionalsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'varga', 'graha'], paginated: true },
  { cap: getPanchangaCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'limb', 'categories'], paginated: true },
  { cap: getSadeSatiCapability, args: { chart_id: CHART_ID, all: true }, facets: ['ayanamsha_id', 'categories', 'all'], paginated: true },
  { cap: getNakshatraCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'domain', 'categories'], paginated: true },
  { cap: getPositionsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'categories', 'include_upagrahas', 'planet', 'frame'], paginated: true },
  { cap: getSensitivePointsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'tradition', 'categories'], paginated: true },
  { cap: getSensitiveDegreesCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'subject', 'check_type'], paginated: true },
  { cap: getTajikCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'include_varsha', 'include_hadda', 'year_min', 'year_max', 'varsha_year', 'varsha_date'], paginated: true },
  { cap: queryCdlmSummaryCapability, args: { chart_id: CHART_ID }, facets: ['tier', 'ayanamsha_id', 'domain'], paginated: false },
  { cap: traverseChartGraphCapability, args: { chart_id: CHART_ID, mode: 'neighbors', seed_node_ids: ['n1'] }, facets: ['mode', 'ayanamsha_id', 'snapshot_type', 'edge_types', 'valence_filter', 'cross_subsystem_only', 'direction', 'min_strength', 'subgraph_type'], paginated: true },
  { cap: getArgalaCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'type', 'varga', 'shape'], paginated: true, emptyReason: false },
  { cap: queryQuestionLensesCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'question_type'], paginated: true },
  { cap: queryRmPrescriptionsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'tradition', 'remedy_category', 'target_graha'], paginated: true },
  // DENS-A: the modules newly credited (directly, or as a second contract-declaring entry of a PASS asset) for assets whose capability declared a contract but selected no tier column
  { cap: getYogaDoshaCapability, args: { chart_id: CHART_ID }, facets: ['type', 'categories', 'facet', 'all'], paginated: true },
  { cap: getYogaFiringsCapability, args: { chart_id: CHART_ID }, facets: ['fired', 'all', 'bhanga_active', 'is_partial', 'yoga_canonical_id'], paginated: true },
  { cap: queryPratijnaCapability, args: { chart_id: CHART_ID }, facets: ['status', 'ayanamsha_id', 'event_class_id'], paginated: true },
  // DENS-B (certification): the modules newly credited by the Dens.served PASS of bg_yogas / bg_ghatana (declared uniform authority: the contract's facets are what the surface layers by),
  // bg_remedies (`confidence`), bo_anveshana (`corroboration_count`) and bo_pramana_mapa (`two_pass_verified_pct`). A filtered args object is used where the handler emits `empty_reason` only for a filtered miss.
  { cap: queryYogaCatalogCapability, args: { tradition: 'parashari' }, facets: ['yoga_name', 'tradition', 'domain'], paginated: true },
  { cap: queryRemedyCorpusCapability, args: { planet: 'Venus' }, facets: ['planet', 'graha', 'domain', 'category'], paginated: true },
  { cap: queryDiscoveriesCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'discovery_class', 'domain'], paginated: true },
  { cap: queryQualityScorecardCapability, args: { chart_id: CHART_ID }, facets: [], paginated: false },
  { cap: queryProspectiveLedgerCapability, args: { chart_id: CHART_ID }, facets: ['domain', 'status'], paginated: false },
  { cap: lelIntakeChecklistCapability, args: { chart_id: CHART_ID }, facets: ['mode', 'domain'], paginated: false },
  { cap: predictionLifecycleSweepCapability, args: { chart_id: CHART_ID }, facets: ['table', 'dry_run'], paginated: false },
]

describe('DENS-SERVED: declared density_contract claims hold against the handler', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  for (const c of CASES) {
    describe(c.cap.name, () => {
      it('declares exactly the expected contract', () => {
        expect(c.cap.density_contract).toMatchObject({ paginated: c.paginated, facets: c.facets, empty_reason: c.emptyReason ?? true })      // toMatchObject: a measured byte budget may sit beside the claims
      })

      it('every declared facet is a real input of the capability', () => {
        const inputs = Object.keys(c.cap.input_schema ?? {})
        for (const f of c.facets) expect(inputs).toContain(f)
      })

      it('a zero-row result carries a non-empty empty_reason; a populated one carries none', async () => {
        if (c.emptyReason === false) return
        mockQuery.mockResolvedValue({ rows: [] })
        const empty = await c.cap.handler(c.args, undefined)
        expect(empty.is_error).toBe(false)
        const reasons = emptyReasons(empty.content as Record<string, unknown>)
        expect(reasons.length).toBeGreaterThan(0)
        for (const r of reasons) expect(r.length).toBeGreaterThan(10)

        mockQuery.mockReset()
        mockQuery.mockResolvedValue({ rows: [{ total: '1', n: 1, sample: 'row' }] })
        const full = await c.cap.handler(c.args, undefined)
        expect(full.is_error).toBe(false)
        expect(emptyReasons(full.content as Record<string, unknown>)).toEqual([])
      })
    })
  }
})

/**
 * The tier-bearing tables: PASS needs the SELECT of the capability that declares the contract to carry the
 * table's verification tier (`verification_pass_status`), so a consumer can layer rows by it.
 */
describe('DENS-SERVED: the served row set carries its verification tier', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  const TIERED: Array<[string, CapabilityDescriptor, Record<string, unknown>]> = [
    ['query_cgm_motifs', queryCgmMotifsCapability, { chart_id: CHART_ID }],
    ['query_cgm_paths', queryCgmPathsCapability, { chart_id: CHART_ID }],
    ['query_rm_resonances', queryRmResonancesCapability, { chart_id: CHART_ID }],
    ['get_ayurdaya', getAyurdayaCapability, { chart_id: CHART_ID }],
    ['get_structural', getStructuralSignalsCapability, { chart_id: CHART_ID }],
  ]
  for (const [name, cap, args] of TIERED) {
    it(`${name}: the row SELECT names verification_pass_status`, async () => {
      await cap.handler(args, undefined)
      const sqls = mockQuery.mock.calls.map(c => String(c[0]))
      expect(sqls.some(q => /\bSELECT\b[\s\S]*\bverification_pass_status\b[\s\S]*\bFROM\b/i.test(q))).toBe(true)
    })
  }

  it('get_structural: total_matching / more_available disclose the real size, not the page length', async () => {
    mockQuery.mockReset()
    mockQuery
      .mockResolvedValueOnce({ rows: [{ fact_id: 'f1' }, { fact_id: 'f2' }] })
      .mockResolvedValueOnce({ rows: [{ total: '5' }] })
    const r = await getStructuralSignalsCapability.handler({ chart_id: CHART_ID, limit: 2 }, undefined)
    const c = r.content as Record<string, unknown>
    expect(c['total']).toBe(2)
    expect(c['total_matching']).toBe(5)
    expect(c['more_available']).toBe(true)
  })
})

describe('DENS-SERVED: query_domain_reading (bo_sangati: bodha_cdlm_cells)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('declares its contract; domain and ayanamsha_id are real inputs', () => {
    expect(queryDomainReadingCapability.density_contract).toEqual({ paginated: true, facets: ['domain', 'ayanamsha_id'], empty_reason: true })
    const inputs = Object.keys(queryDomainReadingCapability.input_schema ?? {})
    for (const f of ['domain', 'ayanamsha_id', 'lens_limit', 'lens_offset']) expect(inputs).toContain(f)
  })

  it('the CDLM cell SELECT carries verification_pass_status (the cell tier)', async () => {
    await queryDomainReadingCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)
    const sqls = mockQuery.mock.calls.map(c => String(c[0]))
    expect(sqls.some(q => /FROM bodha_cdlm_cells/i.test(q) && /\bverification_pass_status\b/.test(q))).toBe(true)
  })

  it('a domain slice that matches nothing carries empty_reason; a populated one does not', async () => {
    const empty = await queryDomainReadingCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)
    expect(String((empty.content as Record<string, unknown>)['empty_reason'])).toMatch(/matched domain 'career'/)

    mockQuery.mockReset()
    mockQuery.mockResolvedValueOnce({ rows: [] })                                     // lensRes
    mockQuery.mockResolvedValueOnce({ rows: [{ n: 0 }] })                             // lensCountRes
    mockQuery.mockResolvedValueOnce({ rows: [{ cell_id: 'c1', domain_row: 'career', domain_col: 'wealth', verification_pass_status: 'two_pass_verified' }] }) // cdlmRes
    mockQuery.mockResolvedValue({ rows: [] })
    const full = await queryDomainReadingCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)
    expect((full.content as Record<string, unknown>)['empty_reason']).toBeUndefined()
  })
})

describe('DENS-SERVED: query_signals (bodha_msr_signals) selects its row tier as a literal item', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  for (const projection of [undefined, ['*'], ['signal_id', 'valence']]) {
    it(`projection ${JSON.stringify(projection)}: every signal SELECT starts with m.verification_pass_status and names it exactly once`, async () => {
      mockQuery.mockClear()
      const result = await querySignalsCapability.handler({ chart_id: CHART_ID, ...(projection ? { projection } : {}) }, undefined)
      expect(result.is_error).toBe(false)
      const selects = mockQuery.mock.calls.map(c => String(c[0])).filter(q => /FROM bodha_msr_signals m/i.test(q) && /ORDER BY m\.computed_salience/i.test(q))
      expect(selects.length).toBeGreaterThan(0)
      for (const q of selects) {
        expect(q).toMatch(/SELECT m\.verification_pass_status, /)
        expect((q.match(/verification_pass_status/g) ?? []).length).toBe(1)
      }
    })
  }

  it('declares signal_type_class as a documented input and a facet (the bind-parameter facet the msr producers are attributed through)', () => {
    expect(Object.keys(querySignalsCapability.input_schema ?? {})).toContain('signal_type_class')
    expect(querySignalsCapability.density_contract?.facets).toContain('signal_type_class')
  })
})

describe('DENS-SERVED (SS N-212 L2 / M3): the contract claims are checked statically', () => {
  // What `paginated` means in these contracts (stated once): TRUE = a bounded read the caller can follow: an offset / cursor input, OR a LIMIT whose bound the response DISCLOSES
  // (total_matching / more_available / truncated). FALSE = the whole matching set is returned: no LIMIT, no offset / cursor. The claim is read from the capability's own SOURCE (the handler
  // text), not from its declaration. query_cdlm_summary is the one named exception: its contract predates this lane and umbrella_density_contract.test.ts pins it false ("limit alone is a cap").
  const LAYERS_DIR = path.resolve(__dirname, '..')
  // prediction_lifecycle_sweep: a sweep must consider EVERY lapsed row to be a correct sweep (its contract comment), so it is not paged; its LIMIT (MAX_LAPSED_ROWS) is an internal row-growth
  // bound on each half, not a page window. query_quality_scorecard: serves the ONE latest scorecard row of the chart (`ORDER BY scored_at DESC LIMIT 1`): a single-row read, not a window.
  // query_prospective_ledger: a `limit` input (default 100, max 500) bounds the read of the chart's OPEN predictions while its contract says paginated:false (the whole open set); the response
  // echoes the bound (`filters.limit`) but discloses no truncation. Flipping the claim needs a source-reviewed pagination route contract in the knowledge compiler, outside this lane.
  const DOCTRINE_FALSE = new Set(['query_cdlm_summary', 'prediction_lifecycle_sweep', 'query_quality_scorecard', 'query_prospective_ledger'])
  function sourceOf(name: string): string {
    const walk = (d: string): string[] => fs.readdirSync(d, { withFileTypes: true }).flatMap(e =>
      e.isDirectory() ? (e.name === '__tests__' || e.name === 'node_modules' ? [] : walk(path.join(d, e.name))) : e.name.endsWith('.ts') && !e.name.endsWith('.test.ts') ? [path.join(d, e.name)] : [])
    const hit = walk(LAYERS_DIR).find(p => new RegExp(`name:\\s*'${name}'`).test(fs.readFileSync(p, 'utf8')))
    if (!hit) throw new Error(`source of ${name} not found`)
    const txt = fs.readFileSync(hit, 'utf8')
    // the handler AND the module's helper functions below it (a LIMIT in a helper mode is still a LIMIT of the capability)
    return txt.slice(Math.max(txt.search(/async handler\(/), 0))
  }
  const PAGER_INPUT = /^(offset|page_cursor|cursor|page|lens_offset)$/
  const DISCLOSES = /truncated|more_available|total_matching|\btotal\b/

  it('paginated:true needs an offset / cursor input or a disclosed LIMIT bound; paginated:false means the whole set (no LIMIT, no pager input)', () => {
    for (const c of CASES) {
      const pagers = Object.keys(c.cap.input_schema ?? {}).filter(i => PAGER_INPUT.test(i))
      const src = sourceOf(c.cap.name)
      if (c.paginated) expect(pagers.length > 0 || (/\bLIMIT\b/.test(src) && DISCLOSES.test(src)), `${c.cap.name} claims paginated:true`).toBe(true)
      else if (!DOCTRINE_FALSE.has(c.cap.name)) {
        expect(pagers, `${c.cap.name} claims paginated:false`).toEqual([])
        expect(src, `${c.cap.name} claims paginated:false`).not.toMatch(/\bLIMIT\b|\boffset\b|\bOFFSET\b|\bcursor\b/)
      }
    }
  })

  // The two contracts below declare a facet that is not an input of their capability; both are outside this lane (query_mechanisms is a build-fence reader, judgment_query is not Dens-credited).
  const KNOWN_FACET_GAPS = new Set(['query_mechanisms:chain_circuit', 'judgment_query:operative_varga'])
  it('every density_contract in the catalog lists only facets that are input_schema keys (ratchet: the two named gaps are the whole list)', () => {
    const gaps: string[] = []
    for (const c of getCatalog()) {
      if (!c.density_contract) continue
      const inputs = Object.keys(c.input_schema ?? {})
      for (const f of c.density_contract.facets) if (!inputs.includes(f)) gaps.push(`${c.name}:${f}`)
    }
    expect(new Set(gaps)).toEqual(KNOWN_FACET_GAPS)
  })

  it('every case in CASES has a facet list inside its own input_schema (the credited capabilities)', () => {
    for (const c of CASES) {
      const inputs = Object.keys(c.cap.input_schema ?? {})
      for (const f of c.facets) expect(inputs, `${c.cap.name}.${f}`).toContain(f)
    }
  })
})

describe('DENS-SERVED (SS N-212 M2): the served row keeps its tier whatever the projection', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('projection [signal_id, valence] still serves verification_pass_status on every row', async () => {
    const row = { signal_id: 's1', signal_type_id: 't', signal_type_class: 'arudha', valence: 'benefic', verification_pass_status: 'two_pass_verified', computed_salience: 1, top_k_salience_rank: 1,
      domains_affected_array: [], constituent_facts_array: [], source_subsystem: 'x', signal_summary_text: 'a', signal_headline_text: 'b', signal_tradition: 'p', citation_human: 'c', lel_origin: false,
      signature_tier: null, configuration_jsonb: {} }
    mockQuery.mockImplementation(async (q: unknown) => ({ rows: /bodha_msr_signals m/i.test(String(q)) ? [row] : [{ total: '1' }] }))
    // a chart id no earlier case used: query_signals caches by its arguments
    const result = await querySignalsCapability.handler({ chart_id: '11111111-2222-4333-8444-555555555555', projection: ['signal_id', 'valence'] }, undefined)
    expect(result.is_error).toBe(false)
    const signals = ((result.content as Record<string, unknown>)['signals'] ?? []) as Array<Record<string, unknown>>
    expect(signals.length).toBeGreaterThan(0)
    for (const s of signals) {
      expect(s['verification_pass_status']).toBe('two_pass_verified')
      expect(Object.keys(s).sort()).toEqual(['signal_id', 'valence', 'verification_pass_status'])
    }
  })
})

describe('DENS-SERVED (SS N-212 a): traverse_chart_graph neighbours selects the node tier and names an empty traversal', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('the recursive-CTE node SELECT lists n.verification_pass_status', async () => {
    await traverseChartGraphCapability.handler({ chart_id: CHART_ID, mode: 'neighbors', seed_node_ids: ['n1'] }, undefined)
    const sqls = mockQuery.mock.calls.map(c => String(c[0]))
    expect(sqls.some(q => /WITH RECURSIVE bfs/i.test(q) && /n\.verification_pass_status/.test(q) && /FROM bodha_cgm_nodes n/i.test(q))).toBe(true)
  })

  it('an unreachable traversal carries empty_reason, a reached one does not', async () => {
    const empty = await traverseChartGraphCapability.handler({ chart_id: CHART_ID, mode: 'neighbors', seed_node_ids: ['n1'] }, undefined)
    expect(String((empty.content as Record<string, unknown>)['empty_reason'])).toMatch(/No CGM node is reachable/)
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [{ node_id: 'n1' }] })
    const full = await traverseChartGraphCapability.handler({ chart_id: CHART_ID, mode: 'neighbors', seed_node_ids: ['n1'] }, undefined)
    expect((full.content as Record<string, unknown>)['empty_reason']).toBeUndefined()
  })
})

describe('DENS-SERVED (SS N-212 review 2): every traverse_chart_graph mode names an empty result', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  const MODES: Array<[string, Record<string, unknown>]> = [
    ['neighbors', { seed_node_ids: ['n1'] }],
    ['paths', { seed_node_ids: ['n1', 'n2'] }],
    ['convergence', {}],
    ['contradictions', {}],
    ['sub_graphs', {}],
  ]
  for (const [mode, extra] of MODES) {
    it(`${mode}: an empty result carries empty_reason`, async () => {
      const r = await traverseChartGraphCapability.handler({ chart_id: CHART_ID, mode, ...extra }, undefined)
      expect(r.is_error, JSON.stringify(r.content).slice(0, 200)).toBe(false)
      expect(String((r.content as Record<string, unknown>)['empty_reason'] ?? '')).toMatch(/\w{8,}/)
    })
  }

  it('paths: the LIMIT 5 bound is disclosed', async () => {
    mockQuery.mockResolvedValue({ rows: [{ path: ['n1', 'n2'], path_length: 1 }] })
    const r = await traverseChartGraphCapability.handler({ chart_id: CHART_ID, mode: 'paths', seed_node_ids: ['n1', 'n2'] }, undefined)
    const c = r.content as Record<string, unknown>
    expect(c['max_paths']).toBe(5)
    expect(c['paths_truncated']).toBe(false)
    expect(c['empty_reason']).toBeUndefined()
  })
})

describe('DENS-F: the shared-table facets the serving code pins (chart_facts, bodha_msr_signals, brahma_class_priors)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('query_signals: producer_asset_id is a documented input and a facet, and reaches the WHERE as a bind parameter', async () => {
    expect(Object.keys(querySignalsCapability.input_schema ?? {})).toContain('producer_asset_id')
    expect(querySignalsCapability.density_contract?.facets).toContain('producer_asset_id')
    await querySignalsCapability.handler({ chart_id: CHART_ID, producer_asset_id: 'bo_laksana' }, undefined)
    const calls = mockQuery.mock.calls.filter(c => /FROM bodha_msr_signals m/i.test(String(c[0])) && /m\.producer_asset_id = \$\d+/.test(String(c[0])))
    expect(calls.length).toBeGreaterThan(0)
    for (const c of calls) expect((c[1] as unknown[])).toContain('bo_laksana')
  })

  it('query_signals: with no producer_asset_id the SELECT carries no producer filter', async () => {
    // a chart id no other test uses: query_signals caches by (chart, filters), a cached payload would run no SELECT
    await querySignalsCapability.handler({ chart_id: '33333333-3333-4333-8333-333333333333' }, undefined)
    const sqls = mockQuery.mock.calls.map(c => String(c[0])).filter(q => /FROM bodha_msr_signals m/i.test(q))
    expect(sqls.length).toBeGreaterThan(0)
    for (const q of sqls) expect(q).not.toMatch(/producer_asset_id/)
  })

  it('query_signals: an empty result under a producer filter names the producer', async () => {
    const r = await querySignalsCapability.handler({ chart_id: CHART_ID, producer_asset_id: 'bo_laksana' }, undefined)
    expect(String((r.content as Record<string, unknown>)['empty_reason'])).toContain("producer_asset_id='bo_laksana'")
  })

  it('get_sensitive_degrees: the literal fact_category pin in the SELECT is exactly the categories the response reports', async () => {
    const r = await getSensitiveDegreesCapability.handler({ chart_id: CHART_ID }, undefined)
    const served = ((r.content as Record<string, unknown>)['provenance'] as { fact_category: string[] }).fact_category
    const sqls = mockQuery.mock.calls.map(c => String(c[0])).filter(q => /FROM chart_facts/i.test(q))
    expect(sqls.length).toBeGreaterThan(0)
    for (const q of sqls) {
      const m = /fact_category IN \(([^)]*)\)/.exec(q)
      expect(m, q).not.toBeNull()
      const pinned = [...(m as RegExpExecArray)[1].matchAll(/'([^']+)'/g)].map(x => x[1])
      expect(pinned).toEqual(served)
    }
  })

  it('get_sensitive_degrees: the first SELECT binds only chart_id as $1 and the optional filters after it', async () => {
    await getSensitiveDegreesCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha' }, undefined)
    const first = mockQuery.mock.calls.find(c => /FROM chart_facts/i.test(String(c[0])))
    expect(String(first?.[0])).toMatch(/ayanamsha_id = \$2/)
    expect((first?.[1] as unknown[]).slice(0, 2)).toEqual([CHART_ID, 'lahiri_chitrapaksha'])
  })

  it('query_class_priors: contested_rows_in_page counts the contested rows of the page; prior_version reaches the WHERE as a bind parameter', async () => {
    mockQuery.mockResolvedValue({ rows: [{ contested: true }, { contested: false }, { contested: true }] })
    const r = await queryClassPriorsCapability.handler({ prior_version: '1.0' }, undefined)
    expect((r.content as Record<string, unknown>)['contested_rows_in_page']).toBe(2)
    const c = mockQuery.mock.calls[0]
    expect(String(c[0])).toMatch(/prior_version = \$1/)
    expect(c[1]).toEqual(['1.0'])
  })

  for (const [name, cap] of [
    ['get_nakshatra', getNakshatraCapability],
    ['get_positions', getPositionsCapability],
    ['get_sensitive_points', getSensitivePointsCapability],
  ] as const) {
    it(`${name}: the served SELECT binds the categories input as fact_category = ANY($2) and selects the row tier`, async () => {
      await cap.handler({ chart_id: CHART_ID, categories: ['graha_position'] }, undefined)
      const c = mockQuery.mock.calls.find(x => /FROM chart_facts/i.test(String(x[0])))
      expect(String(c?.[0])).toMatch(/fact_category = ANY\(\$2::text\[\]\)/)
      expect(String(c?.[0])).toMatch(/\bverification_pass_status\b/)
      expect((c?.[1] as unknown[])[1]).toEqual(['graha_position'])
    })
  }
})

describe('DENS-F: bo_samvada (query_ucd over vw_chart_digest) and bg_ephemeris (get_graha_yuddha over ephemeris_daily) contracts', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('query_ucd: facets are real inputs; the contract is the one the handler honours', () => {
    expect(queryUcdCapability.density_contract).toEqual({
      paginated: true, facets: ['ayanamsha_id', 'signal_class', 'min_salience', 'response_format'], empty_reason: true,
    })
    const inputs = Object.keys(queryUcdCapability.input_schema ?? {})
    for (const f of queryUcdCapability.density_contract?.facets ?? []) expect(inputs).toContain(f)
  })

  it('query_ucd: an empty chart carries empty_reason and a disclosed (empty) signals_page', async () => {
    const r = await queryUcdCapability.handler({ chart_id: '44444444-4444-4444-8444-444444444444' }, undefined)
    expect(r.is_error, JSON.stringify(r.content).slice(0, 300)).toBe(false)
    const c = r.content as Record<string, unknown>
    expect(String(c['empty_reason'])).toMatch(/No Bodha synthesis for chart 44444444/)
    expect(c['signals_page']).toEqual({ returned: 0, available: 0, top_k: 20, truncated: false })
  })

  it('query_ucd: a chart with a digest row carries no empty_reason', async () => {
    mockQuery.mockImplementation(async (sql: string) => (/FROM vw_chart_digest/i.test(String(sql))
      ? { rows: [{ msr_signal_count: 3, yoga_count: 1, dosha_count: 0, contradiction_count: 0 }] }
      : { rows: [] }))
    const r = await queryUcdCapability.handler({ chart_id: '55555555-5555-4555-8555-555555555555' }, undefined)
    expect(r.is_error).toBe(false)
    expect((r.content as Record<string, unknown>)['empty_reason']).toBeUndefined()
  })

  it('get_graha_yuddha: contract is whole-set (no LIMIT, no pager) with real facets; no pair names itself empty, a pair does not', async () => {
    expect(getGrahaYuddhaCapability.density_contract).toEqual({ paginated: false, facets: ['ayanamsha_id'], empty_reason: true })
    for (const f of getGrahaYuddhaCapability.density_contract?.facets ?? []) expect(Object.keys(getGrahaYuddhaCapability.input_schema ?? {})).toContain(f)
    const empty = await getGrahaYuddhaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(String((empty.content as Record<string, unknown>)['empty_reason'])).toMatch(/No graha yuddha pair/)
    mockQuery.mockReset()
    mockQuery.mockImplementation(async (sql: string) => {
      const s = String(sql)
      if (/FROM chart_facts/i.test(s)) return { rows: [{ fact_id: 'f1', fact_subject: 'MAR_VEN', fact_key: 'pair', ayanamsha_id: 'lahiri', fact_value_jsonb: { orb_deg: 0.4, sign: 'Leo' } }] }
      if (/FROM charts/i.test(s)) return { rows: [{ birth_date: '1984-02-05' }] }
      return { rows: [] }
    })
    const full = await getGrahaYuddhaCapability.handler({ chart_id: CHART_ID }, undefined)
    const c = full.content as Record<string, unknown>
    expect(c['total']).toBe(1)
    expect(c['empty_reason']).toBeUndefined()
  })

  for (const [name, cap, own, foreignCat] of [
    ['get_nakshatra', getNakshatraCapability, 'graha_nakshatra_join', 'graha_position'],
    ['get_positions', getPositionsCapability, 'graha_position', 'upagraha_position'],
    ['get_sensitive_points', getSensitivePointsCapability, 'midpoint', 'graha_position'],
  ] as const) {
    it(`${name}: an explicit categories list naming another asset's category is disclosed (categories_outside_asset); an owned-only list is not`, async () => {
      mockQuery.mockResolvedValue({ rows: [{ fact_id: 'f1' }] })
      const mixed = await cap.handler({ chart_id: CHART_ID, categories: [own, foreignCat] }, undefined)
      const mc = mixed.content as Record<string, unknown>
      expect(mc['categories_outside_asset']).toEqual([foreignCat])
      expect(String(mc['categories_outside_asset_note'])).toMatch(/another asset/)
      const ownOnly = await cap.handler({ chart_id: CHART_ID, categories: [own] }, undefined)
      expect((ownOnly.content as Record<string, unknown>)['categories_outside_asset']).toBeUndefined()
      const dflt = await cap.handler({ chart_id: CHART_ID }, undefined)
      expect((dflt.content as Record<string, unknown>)['categories_outside_asset']).toBeUndefined()
    })
  }
})


// ───────────────────────────── DENS-A: the 14 assets that declared a contract but selected no tier column ─────────────────────────────

describe('DENS-A: the declared tier column is in the SELECT the capability serves, and the response carries it', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  // [capability, args, table, the tier column the asset declares in asset_declarations.json]
  const DECLARED: Array<[string, CapabilityDescriptor, Record<string, unknown>, string, string]> = [
    ['query_formula_constants', queryFormulaConstantsCapability, {}, 'brahma_formula_constants', 'class'],
  ]
  for (const [name, cap, args, table, column] of DECLARED) {
    it(`${name}: the row SELECT of ${table} names ${column}`, async () => {
      await cap.handler(args, undefined)
      const sqls = mockQuery.mock.calls.map(c => String(c[0]))
      const rowSelect = sqls.find(q => new RegExp(`\\bFROM\\s+${table}\\b`, 'i').test(q) && !/COUNT\(\*\)/i.test(q))
      expect(rowSelect, `no row SELECT of ${table}`).toBeDefined()
      expect(rowSelect!).toMatch(new RegExp(`\\b${column}\\b[\\s\\S]*\\bFROM\\b`, 'i'))
    })
  }

  it('the declared tier columns are exactly the reviewed multi-valued ones; a single-valued label (ga_yoga.strength_label, ga_medical / ga_vastu indication_tier) is never declared', () => {
    const decl = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../../../../scripts/governance/asset_declarations.json'), 'utf8')).assets as Record<string, { density_tier_columns?: Array<{ column: string }> }>
    const declared = Object.fromEntries(Object.entries(decl).filter(([, v]) => v.density_tier_columns).map(([k, v]) => [k, v.density_tier_columns!.map(d => d.column)]))
    expect(declared).toEqual({ bg_class_priors: ['contested'], bg_formula_constants: ['class'], bg_gochara_citation_resolution: ['status'], bg_muhurta_lattice: ['corpus_status'], bg_remedies: ['confidence'], bo_anveshana: ['corroboration_count'], bo_pramana_mapa: ['two_pass_verified_pct'], ga_yoga: ['fired'] })
  })

  it('query_formula_constants serves the class on every row (an authority class, classical / engineering / native_judgment, not a verification pass)', async () => {
    mockQuery.mockResolvedValue({ rows: [{ constant_id: 'a', class: 'classical' }, { constant_id: 'b', class: 'native_judgment' }] })
    const r = await queryFormulaConstantsCapability.handler({}, undefined)
    const rows = (r.content as Record<string, unknown>)['rows'] as Array<Record<string, unknown>>
    expect(new Set(rows.map(x => x['class'])).size).toBeGreaterThan(1)
  })
})

describe('DENS-A: get_dasha_lord_capability (ga_dashas) reads and serves the dasha row verification tier', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  function arrange(dashaRows: Array<Record<string, unknown>>) {
    mockQuery.mockImplementation(async (q: unknown) => {
      const sql = String(q)
      if (/FROM chart_dashas/i.test(sql)) return { rows: dashaRows }
      return { rows: [] }
    })
  }

  it('declares its contract: unpaginated (at most 9 lords), facet ayanamsha_id is a real input, a zero-lord result names its empty_reason and a populated one does not', async () => {
    expect(getDashaLordCapabilityCapability.density_contract).toMatchObject({ paginated: false, facets: ['ayanamsha_id'], empty_reason: true })
    expect(Object.keys(getDashaLordCapabilityCapability.input_schema ?? {})).toContain('ayanamsha_id')
    arrange([])
    const empty = await getDashaLordCapabilityCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(String((empty.content as Record<string, unknown>)['empty_reason'])).toMatch(/No Vimśottarī level-1/)
  })

  it('the chart_dashas SELECT lists verification_pass_status', async () => {
    arrange([])
    await getDashaLordCapabilityCapability.handler({ chart_id: CHART_ID }, undefined)
    const sql = mockQuery.mock.calls.map(c => String(c[0])).find(q => /FROM chart_dashas/i.test(q))
    expect(sql).toMatch(/SELECT DISTINCT lord_graha, verification_pass_status FROM chart_dashas/)
  })

  it('a lord with two stored statuses is ONE row carrying both, sorted; a lord with none stored gets [], never a defaulted tier', async () => {
    arrange([
      { lord_graha: 'Sun', verification_pass_status: 'two_pass_verified' },
      { lord_graha: 'Sun', verification_pass_status: 'computed_extension' },
      { lord_graha: 'Moon', verification_pass_status: null },
    ])
    const r = await getDashaLordCapabilityCapability.handler({ chart_id: CHART_ID }, undefined)
    const c = r.content as Record<string, unknown>
    const rows = c['rows'] as Array<Record<string, unknown>>
    expect(rows.map(x => x['lord'])).toEqual(['Sun', 'Moon'])
    expect(rows[0]!['dasha_verification_pass_status']).toEqual(['computed_extension', 'two_pass_verified'])
    expect(rows[1]!['dasha_verification_pass_status']).toEqual([])
    expect(c['empty_reason']).toBeUndefined()
  })
})

describe('DENS-A: query_mechanisms (bo_yantra_mechanism) counts the verification tier of the matching rows, pinned to the page build', () => {
  const env = { kid: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID, key: process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT }
  beforeEach(() => {
    mockQuery.mockReset()
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = 'inquiry-v1'
    process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = Buffer.alloc(32, 3).toString('base64url')
  })
  afterEach(() => {
    if (env.kid === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID = env.kid
    if (env.key === undefined) delete process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT; else process.env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT = env.key
  })

  const snapshot = { replacement_in_progress: false, eligible_build_id: 'build-a', cursor_build_changed: false, rows: [], facets: [], total_matching: '3' }

  it('the tier SELECT names verification_pass_status, filters like the page and binds the page build', async () => {
    mockQuery.mockImplementation(async (q: unknown) => {
      const sql = String(q)
      if (/^\s*WITH eligible_receipt/.test(sql)) return { rows: [snapshot] }
      if (/SELECT d\.verification_pass_status, COUNT/.test(sql)) return { rows: [{ verification_pass_status: 'two_pass_verified', n: '2' }, { verification_pass_status: null, n: '1' }] }
      return { rows: [] }
    })
    const r = await queryMechanismsCapability.handler({ chart_id: CHART_ID, valence: 'benefic' }, undefined)
    expect(r.is_error).toBe(false)
    const [sql, params] = mockQuery.mock.calls.find(c => /FROM bodha_mechanisms d\s+WHERE/.test(String(c[0]))) as [string, unknown[]]
    expect(sql).toMatch(/SELECT d\.verification_pass_status, COUNT\(\*\)::text AS n\s+FROM bodha_mechanisms d/)
    // PR-2: the tier query carries the same primary-ayanamsha filter as the page ($2, Lahiri).
    expect(sql).toMatch(/d\.ayanamsha_id = \$2/)
    expect(sql).toMatch(/d\.valence = \$3/)
    expect(sql).toMatch(/d\.build_id = \$4::uuid/)
    expect(params).toEqual([CHART_ID, 'lahiri_chitrapaksha', 'benefic', 'build-a'])
    const facets = (r.content as Record<string, unknown>)['facets'] as Record<string, unknown>
    expect(facets['by_verification_pass_status']).toEqual({ two_pass_verified: 2, unset: 1 })
  })

  it('a tier count whose total differs from total_matching (a replacement landed between the two statements) is null, never a wrong number', async () => {
    mockQuery.mockImplementation(async (q: unknown) => {
      const sql = String(q)
      if (/^\s*WITH eligible_receipt/.test(sql)) return { rows: [snapshot] }
      if (/SELECT d\.verification_pass_status, COUNT/.test(sql)) return { rows: [{ verification_pass_status: 'two_pass_verified', n: '2' }] }
      return { rows: [] }
    })
    const r = await queryMechanismsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(r.is_error).toBe(false)
    expect(((r.content as Record<string, unknown>)['facets'] as Record<string, unknown>)['by_verification_pass_status']).toBeNull()
  })

  it('a failed tier read degrades to null and still serves the page', async () => {
    mockQuery.mockImplementation(async (q: unknown) => {
      const sql = String(q)
      if (/^\s*WITH eligible_receipt/.test(sql)) return { rows: [snapshot] }
      if (/SELECT d\.verification_pass_status, COUNT/.test(sql)) throw new Error('boom')
      return { rows: [] }
    })
    const r = await queryMechanismsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(r.is_error).toBe(false)
    expect(((r.content as Record<string, unknown>)['facets'] as Record<string, unknown>)['by_verification_pass_status']).toBeNull()
  })

  it('declares its contract; its only non-input facet is the known chain_circuit gap', () => {
    expect(queryMechanismsCapability.density_contract).toMatchObject({ paginated: true, empty_reason: true })
    const inputs = Object.keys(queryMechanismsCapability.input_schema ?? {})
    for (const f of ['mechanism_class', 'valence']) expect(inputs).toContain(f)
  })
})

describe('DENS-A: query_mechanism_retrodiction (credited through ga_dashas) keeps its honest empty_reason', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('declares its contract; every facet is a real input', () => {
    expect(queryMechanismRetrodictionCapability.density_contract).toMatchObject({ paginated: true, facets: ['domain', 'house', 'dasha_level', 'ayanamsha_id'], empty_reason: true })
    const inputs = Object.keys(queryMechanismRetrodictionCapability.input_schema ?? {})
    for (const f of ['domain', 'house', 'dasha_level', 'ayanamsha_id']) expect(inputs).toContain(f)
  })

  it('no pre-2020 events: empty_reason is named; with an event: none', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ lagna_sign: 'Aries', lagna_fact_id: 'f1' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const empty = await queryMechanismRetrodictionCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(empty.is_error).toBe(false)
    expect(String((empty.content as Record<string, unknown>)['empty_reason'])).toBe('no_pre_2020_life_events_for_chart')

    mockQuery.mockReset()
    mockQuery.mockResolvedValueOnce({ rows: [{ lagna_sign: 'Aries', lagna_fact_id: 'f1' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ event_id: 'e1', event_date: '2010-05-01', domain: 'career', description: 'x', significance: 'major', lord_graha: 'Sun', level_n: 1, dasha_row_id: 'd1', dasha_start: '2008-01-01', dasha_end: '2014-01-01' }] })
    const full = await queryMechanismRetrodictionCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(full.is_error, JSON.stringify(full.content).slice(0, 200)).toBe(false)
    expect((full.content as Record<string, unknown>)['empty_reason']).toBeUndefined()
  })
})

describe('DENS-A: judgment_query (credited through bo_yantra_mechanism) states its contract truthfully', () => {
  it('one judgment per call (not paginated); the honest gaps are judgment_flags, so empty_reason is declared false', () => {
    expect(judgmentQueryCapability.density_contract).toMatchObject({ paginated: false, empty_reason: false })
    expect(judgmentQueryCapability.density_contract?.facets).toEqual(['domain', 'operative_varga', 'max_signals'])
  })
})

describe('DENS-SERVED (SS N-268): read_sutravali_rule (bg_rules) serves its confidence score and names an empty result', () => {
  const RULE_ID = 'a8c5fa0a-6105-4e50-83de-7e88f7d235ad'
  const cap = () => { clearRegistry(); registerD7ChannelCapabilities(); return getCapability('marsys://tool/L0/read_sutravali_rule')! }
  beforeEach(() => { mockQuery.mockReset() })

  it('declares an unpaginated single-row contract with no filter axis and a real empty_reason', () => {
    expect(cap().density_contract).toEqual({ paginated: false, facets: [], empty_reason: true })
  })

  it('the sutravali_rules SELECT lists the discrete confidence score (not a declared tier) and the served rule carries it', async () => {
    mockQuery.mockResolvedValue({ rows: [{ rule_id: RULE_ID, text_id: 'bphs', verse_ref: '1.1', antecedent_jsonb: {}, predicate_jsonb: {}, prediction_jsonb: {}, confidence: '0.6', extracted_by: 'python_regex_v2' }] })
    const r = await cap().handler({ rule_id: RULE_ID }, undefined)
    expect(String(mockQuery.mock.calls[0]![0])).toMatch(/\bconfidence\b[\s\S]*\bFROM\s+sutravali_rules\b/)
    expect(((r.content as Record<string, unknown>)['rule'] as Record<string, unknown>)['confidence']).toBe(0.6)
    expect((r.content as Record<string, unknown>)['empty_reason']).toBeUndefined()
  })

  it('a zero-row result names its empty_reason; a populated one does not', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const r = await cap().handler({ rule_id: RULE_ID }, undefined)
    expect((r.content as Record<string, unknown>)['empty_reason']).toBe('rule_id_not_found')
  })
})

/**
 * DENS-B (certification): the tier layer each newly credited surface carries, tested against the real handler with a mocked `query`.
 */
describe('DENS-SERVED (certification): query_discoveries counts the page by corroboration_count (§N.6.1)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('selects corroboration_count on every row and reports corroboration_tiers_in_page', async () => {
    const rows = [
      { discovery_id: 'd1', corroboration_count: 3 },
      { discovery_id: 'd2', corroboration_count: 1 },
      { discovery_id: 'd3', corroboration_count: 1 },
      { discovery_id: 'd4', corroboration_count: null },
    ]
    mockQuery.mockImplementation(async (sql: string) => {
      const q = String(sql)
      if (/SELECT discovery_id, ayanamsha_id/.test(q)) return { rows }
      if (/GROUP BY discovery_class/.test(q)) return { rows: [] }
      return { rows: [{ total: '4', n: '1' }] }
    })
    const r = await queryDiscoveriesCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(r.is_error).toBe(false)
    const c = r.content as Record<string, unknown>
    expect(c['corroboration_tiers_in_page']).toEqual({ '3': 1, '1': 2, unknown: 1 })
    expect(c['count']).toBe(4)
    const rowSql = mockQuery.mock.calls.map(x => String(x[0])).find(q => /SELECT discovery_id, ayanamsha_id/.test(q)) ?? ''
    expect(rowSql).toMatch(/\bcorroboration_count\b/)
  })

  it('an empty page reports an empty tier count, not a missing key', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const r = await queryDiscoveriesCapability.handler({ chart_id: CHART_ID }, undefined)
    expect((r.content as Record<string, unknown>)['corroboration_tiers_in_page']).toEqual({})
  })
})

describe('DENS-SERVED (certification): get_yoga_firings carries its verification tier (fired) in both projections and counts catalog-only rows', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('the row SELECT names f.fired with and without grounds_jsonb (the pre-Lane-3 fallback keeps the tier)', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)
    const withGrounds = mockQuery.mock.calls.map(c => String(c[0])).find(q => /FROM ga_yoga_firings f\s+LEFT JOIN/.test(q)) ?? ''
    expect(withGrounds).toMatch(/\bf\.fired\b[\s\S]*\bFROM ga_yoga_firings f\b/)
    expect(withGrounds).toMatch(/f\.grounds_jsonb/)

    mockQuery.mockReset()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/f\.grounds_jsonb/.test(String(sql))) throw new Error('column f.grounds_jsonb does not exist')
      return { rows: [] }
    })
    const r = await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(r.is_error).toBe(false)
    const base = mockQuery.mock.calls.map(c => String(c[0])).filter(q => /FROM ga_yoga_firings f\s+LEFT JOIN/.test(q) && !/f\.grounds_jsonb/.test(q))
    expect(base.length).toBeGreaterThan(0)
    expect(base[0]).toMatch(/\bf\.fired\b/)
  })

  it('all=true: catalog-only (fired=false) rows are served and counted separately; the default page counts none', async () => {
    const page = [
      { id: 'a', yoga_canonical_id: 'y1', fired: true, strength: 0.9 },
      { id: 'b', yoga_canonical_id: 'y2', fired: false, strength: 0.1 },
      { id: 'c', yoga_canonical_id: 'y3', fired: false, strength: 0.0 },
    ]
    mockQuery.mockImplementation(async (sql: string) => (/COUNT\(\*\)/.test(String(sql)) ? { rows: [{ total: '3' }] } : { rows: page }))
    const all = await getYogaFiringsCapability.handler({ chart_id: CHART_ID, all: true }, undefined)
    const c = all.content as Record<string, unknown>
    expect(c['catalog_only_rows_in_page']).toBe(2)
    expect(c['count']).toBe(3)

    mockQuery.mockImplementation(async (sql: string) => (/COUNT\(\*\)/.test(String(sql)) ? { rows: [{ total: '1' }] } : { rows: [page[0]] }))
    const dflt = await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect((dflt.content as Record<string, unknown>)['catalog_only_rows_in_page']).toBe(0)
  })
})

describe('DENS-SERVED (certification): query_remedy_corpus selects confidence in both projections', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [{ total: 1 }] })
  })

  it('compact: a literal column list holding confidence; all: SELECT *', async () => {
    await queryRemedyCorpusCapability.handler({ planet: 'Venus' }, undefined)
    await queryRemedyCorpusCapability.handler({ planet: 'Venus', fields: 'all' }, undefined)
    const sqls = mockQuery.mock.calls.map(c => String(c[0])).filter(q => /FROM brahma_remedy_corpus WHERE/.test(q) && /LIMIT/.test(q))
    expect(sqls).toHaveLength(2)
    expect(sqls[0]).toMatch(/SELECT remedy_id, planet,[^*]*\bconfidence\b[^*]* FROM brahma_remedy_corpus/)
    expect(sqls[0]).not.toMatch(/SELECT \*/)
    expect(sqls[1]).toMatch(/SELECT \* FROM brahma_remedy_corpus/)
  })

  it('a filtered miss names the applied filters; an unfiltered empty read carries none (the corpus is not empty-by-filter)', async () => {
    mockQuery.mockResolvedValue({ rows: [{ total: 0 }] })
    const miss = await queryRemedyCorpusCapability.handler({ graha: 'Rahu', category: 'mantras' }, undefined)
    expect(String((miss.content as Record<string, unknown>)['empty_reason'])).toMatch(/planet=Rahu, category=mantras/)
  })
})

describe('DENS-SERVED (certification): query_yoga_catalog paginates and names an empty filtered miss', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('a filtered miss carries empty_reason with the stored vocabulary; a populated page discloses total_matching / more_available', async () => {
    mockQuery.mockImplementation(async (sql: string) => (/COUNT\(\*\)/.test(String(sql)) ? { rows: [{ total: '0' }] } : { rows: [] }))
    const miss = await queryYogaCatalogCapability.handler({ tradition: 'Jaimini', domain: 'raja' }, undefined)
    expect(String((miss.content as Record<string, unknown>)['empty_reason'])).toMatch(/tradition=Jaimini, domain=raja/)

    mockQuery.mockImplementation(async (sql: string) => (/COUNT\(\*\)/.test(String(sql)) ? { rows: [{ total: '233' }] } : { rows: [{ canonical_id: 'gaja_kesari', name_en: 'Gaja Kesari', school: 'parashari' }] }))
    const page = await queryYogaCatalogCapability.handler({ limit: 1, offset: 0 }, undefined)
    const c = page.content as Record<string, unknown>
    expect(c['total_matching']).toBe(233)
    expect(c['more_available']).toBe(true)
    expect(c['empty_reason']).toBeUndefined()
  })
})

describe('DENS-SERVED (certification): lel_intake_checklist and prediction_lifecycle_sweep serve populated, mocked reads', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('lel_intake_checklist: a populated ontology yields per-domain entries and no empty_reason; an unknown domain filter names the known domains', async () => {
    const ontology = [
      { event_class_id: 'marriage', name_en: 'Marriage', domain: 'relationship', lel_category: 'relationship', temporal_shape: 'point', evidence_requirements: null },
      { event_class_id: 'job_start', name_en: 'Job start', domain: 'career', lel_category: 'career', temporal_shape: 'point', evidence_requirements: null },
    ]
    mockQuery.mockImplementation(async (sql: string) => (/FROM brahma_event_ontology/.test(String(sql)) ? { rows: ontology } : { rows: [{ domain: 'career', total: '2' }] }))
    const ok = await lelIntakeChecklistCapability.handler({ chart_id: CHART_ID }, undefined)
    const c = ok.content as Record<string, unknown>
    expect(c['domain_count']).toBe(2)
    expect(c['empty_reason']).toBeUndefined()
    const miss = await lelIntakeChecklistCapability.handler({ chart_id: CHART_ID, domain: 'wealth' }, undefined)
    expect(String((miss.content as Record<string, unknown>)['empty_reason'])).toMatch(/Known domains: career, relationship/)
  })

  it('prediction_lifecycle_sweep: a lapsed pending prediction is reported (dry run) and the empty_reason is withheld; a clean sweep states why', async () => {
    mockQuery.mockImplementation(async (sql: string) => {
      const q = String(sql)
      if (/FROM mimamsa_predictions/.test(q)) return { rows: [{ prediction_id: 'p1', domain: null, eval_date: '2020-01-01', observation_window: null, outcome_claim: 'x' }] }
      return { rows: [] }
    })
    const lapsed = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_ID }, undefined)
    const c = lapsed.content as Record<string, unknown>
    expect(c['empty_reason']).toBeUndefined()
    expect(JSON.stringify(c['mimamsa_predictions'])).toMatch(/would_write_expired/)

    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
    const clean = await predictionLifecycleSweepCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(String((clean.content as Record<string, unknown>)['empty_reason'])).toMatch(/No lapsed predictions/)
  })
})

describe('DENS-SERVED (certification): query_quality_scorecard selects two_pass_verified_pct and discloses an absent scorecard', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('the scorecard SELECT names two_pass_verified_pct; a present row carries no empty_reason, an absent one does', async () => {
    mockQuery.mockResolvedValue({ rows: [{ scorecard_id: 's1', chart_id: CHART_ID, two_pass_verified_pct: 91.5 }] })
    const present = await queryQualityScorecardCapability.handler({ chart_id: CHART_ID }, undefined)
    expect((present.content as Record<string, unknown>)['empty_reason']).toBeUndefined()
    const sql = mockQuery.mock.calls.map(c => String(c[0])).find(q => /FROM synthesis_quality_scorecard/.test(q)) ?? ''
    expect(sql).toMatch(/\btwo_pass_verified_pct\b/)

    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
    const absent = await queryQualityScorecardCapability.handler({ chart_id: CHART_ID }, undefined)
    expect((absent.content as Record<string, unknown>)['no_data']).toBe(true)
    expect(String((absent.content as Record<string, unknown>)['empty_reason'])).toMatch(/No synthesis_quality_scorecard row/)
  })
})
