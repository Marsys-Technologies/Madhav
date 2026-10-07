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
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import type { CapabilityDescriptor } from '../../types'
import { queryClassPriorsCapability } from '../L0_brahmagyan/query_class_priors'
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
import { queryTransitVedhaCapability } from '../L0_brahmagyan/query_transit_vedha'
import { queryCgmMotifsCapability } from '../L2_bodha/query_cgm_motifs'
import { queryCgmPathsCapability } from '../L2_bodha/query_cgm_paths'
import { queryRmResonancesCapability } from '../L2_bodha/query_rm_resonances'
import { queryRmPrescriptionsCapability } from '../L2_bodha/query_rm_prescriptions'
import { getAyurdayaCapability } from '../L1_ganita/get_ayurdaya'
import { getStructuralSignalsCapability } from '../L1_ganita/get_structural_signals'
import { getDivisionalsCapability } from '../L1_ganita/get_divisionals'

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
}

const CASES: Case[] = [
  { cap: queryClassPriorsCapability, args: {}, facets: ['prior_version', 'signal_type_class', 'source_subsystem'], paginated: false },
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
  { cap: queryTransitVedhaCapability, args: {}, facets: ['primary_graha', 'primary_transit_house'], paginated: false },
  { cap: queryCgmMotifsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'motif_class'], paginated: true },
  { cap: queryCgmPathsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'path_type', 'final_only'], paginated: true },
  { cap: queryRmResonancesCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'graha'], paginated: true },
  { cap: getAyurdayaCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'method'], paginated: true },
  { cap: getStructuralSignalsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'domain', 'categories'], paginated: true },
  { cap: getDivisionalsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'varga', 'graha'], paginated: true },
  { cap: queryRmPrescriptionsCapability, args: { chart_id: CHART_ID }, facets: ['ayanamsha_id', 'tradition', 'remedy_category', 'target_graha'], paginated: true },
]

describe('DENS-SERVED: declared density_contract claims hold against the handler', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  for (const c of CASES) {
    describe(c.cap.name, () => {
      it('declares exactly the expected contract', () => {
        expect(c.cap.density_contract).toEqual({ paginated: c.paginated, facets: c.facets, empty_reason: true })
      })

      it('every declared facet is a real input of the capability', () => {
        const inputs = Object.keys(c.cap.input_schema ?? {})
        for (const f of c.facets) expect(inputs).toContain(f)
      })

      it('a zero-row result carries a non-empty empty_reason; a populated one carries none', async () => {
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
