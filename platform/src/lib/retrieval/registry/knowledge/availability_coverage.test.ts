import { describe, expect, it } from 'vitest'
import generatedCapabilityKnowledge from '../../../../generated/capability_knowledge.snapshot.json'
import { loadChartCapabilityOverlay, type OverlayQueryRow } from './overlay_loader'
import type { CapabilityKnowledgeSnapshot, ProducerOutputAvailabilityRequirement } from './types'

const snapshot = generatedCapabilityKnowledge as CapabilityKnowledgeSnapshot
const CHART_ID = 'chart-first-slice'
const BUILD_ID = 'build-first-slice'

/**
 * This is an executable accounting of the original first planner slice.  A
 * route is called concrete only when its own executable binding has a complete
 * exact availability contract; the rest remain named fail-closed decisions,
 * not inferred availability from neighbouring producer assets.
 */
const FIRST_SLICE = {
  concrete: [
    'scu.bodha.mechanism.network',
    'scu.catalog.get_dashas',
    'scu.catalog.get_divisionals',
    'scu.catalog.query_chart_gestalt',
    'scu.catalog.query_planet_transit',
    'scu.finance.prosperity_assessment',
    'scu.yoga.firing_and_cancellation',
  ],
  deliberately_dark: [
    'scu.catalog.assess_career',
    'scu.catalog.assess_marriage',
    'scu.catalog.judgment_query',
    'scu.catalog.query_classical_texts',
    'scu.catalog.query_contradictions',
    'scu.kala.temporal_activation',
  ],
} as const

function findScu(scuId: string) {
  const scu = snapshot.scus.find((candidate) => candidate.scu_id === scuId)
  if (!scu) throw new Error(`Missing first-slice SCU: ${scuId}`)
  return scu
}

function producerRequirements(scuId: string): ProducerOutputAvailabilityRequirement[] {
  return findScu(scuId).availability_contracts?.flatMap((contract) => contract.requirements
    .filter((requirement): requirement is ProducerOutputAvailabilityRequirement => requirement.kind === 'producer_output')) ?? []
}

function receipt(requirement: ProducerOutputAvailabilityRequirement): OverlayQueryRow {
  return {
    active_build_id: BUILD_ID,
    active_build_status: 'completed',
    asset_id: requirement.asset_id,
    chart_id: CHART_ID,
    build_id: BUILD_ID,
    receipt_version: 'first-slice-fixture',
    receipt_state: 'proven',
    output_digest_spec_sha256: requirement.spec_sha256,
    observed_at: '2026-09-17T00:00:00.000Z',
    freshness_state: 'fresh',
    unknown_reasons: [],
    freshness_reasons: [],
  }
}

function adjacentProducerReceipt(assetId: string, specSha256: string): OverlayQueryRow {
  return {
    active_build_id: BUILD_ID,
    active_build_status: 'completed',
    asset_id: assetId,
    chart_id: CHART_ID,
    build_id: BUILD_ID,
    receipt_version: 'first-slice-adjacent-producer-fixture',
    receipt_state: 'proven',
    output_digest_spec_sha256: specSha256,
    observed_at: '2026-09-17T00:00:00.000Z',
    freshness_state: 'fresh',
    unknown_reasons: [],
    freshness_reasons: [],
  }
}

function globalProducerReceipt(
  assetId: string,
  specSha256: string,
  overrides: Partial<OverlayQueryRow> = {},
): OverlayQueryRow {
  return {
    active_build_id: BUILD_ID,
    active_build_status: 'completed',
    asset_id: assetId,
    chart_id: null,
    build_id: null,
    receipt_version: 'first-slice-global-producer-fixture',
    receipt_state: 'proven',
    output_digest_spec_sha256: specSha256,
    observed_at: '2026-09-17T00:00:00.000Z',
    freshness_state: 'fresh',
    unknown_reasons: [],
    freshness_reasons: [],
    ...overrides,
  }
}

function transitProbeAnchor(): OverlayQueryRow {
  return {
    active_build_id: BUILD_ID,
    active_build_status: 'completed',
    asset_id: '',
    chart_id: null,
    build_id: null,
    receipt_version: 'first-slice-probe-fixture',
    receipt_state: 'unknown',
    output_digest_spec_sha256: null,
    observed_at: '2026-09-17T00:00:00.000Z',
    freshness_state: null,
    unknown_reasons: [],
    freshness_reasons: [],
    service_probe_evidence: [{
      asset_id: 'bg_ephemeris_engine',
      source_kind: 'server_reconstructed',
      source_ref: 'nirmana-elevation:health-probe:bg_ephemeris_engine',
      observed_at: '2026-09-17T00:00:00.000Z',
      evidence_payload: {
        registry_fingerprint_sha256: 'a'.repeat(64),
        analysis_digest: 'b'.repeat(64),
        response_digest: 'c'.repeat(64),
        probe_contract_sha256: 'e94a594d245b97251bc731757b56dac406433e12c8daa4b1df1d478e8e9ae1c4',
        detector_observation: {
          probe_type: 'ephemeris_engine',
          runner_revision: 'first-slice-test',
          request_started_at: '2026-09-16T23:59:59.000Z',
          request_ended_at: '2026-09-17T00:00:01.000Z',
          result: { status: 'GREEN', checks: [{ check: 'forensic-anchor', passed: true }] },
        },
      },
    }],
  }
}

async function overlayFor(rows: readonly OverlayQueryRow[]) {
  return loadChartCapabilityOverlay(snapshot, CHART_ID, async () => ({ rows: [...rows] }), new Date('2026-09-17T00:05:00.000Z'))
}

describe('first-slice availability coverage', () => {
  it('accounts for every remaining first-slice route with either a concrete contract or an evidence-backed dark disposition', () => {
    const all = [...FIRST_SLICE.concrete, ...FIRST_SLICE.deliberately_dark]
    expect(all).toHaveLength(13)
    expect(new Set(all).size).toBe(all.length)

    for (const scuId of FIRST_SLICE.concrete) {
      const scu = findScu(scuId)
      expect(scu.availability_contracts?.length, scuId).toBeGreaterThan(0)
      expect(scu.availability_dispositions ?? [], scuId).toEqual([])
    }
    for (const scuId of FIRST_SLICE.deliberately_dark) {
      const scu = findScu(scuId)
      expect(scu.availability_contracts ?? [], scuId).toEqual([])
      expect(scu.availability_dispositions, scuId).toEqual([
        expect.objectContaining({
          binding_id: `registry:${scu.primary_binding_uri}`,
          status: 'deliberately_dark',
          reason: expect.any(String),
          source_refs: expect.any(Array),
        }),
      ])
      expect(scu.availability_dispositions![0]!.source_refs.length, scuId).toBeGreaterThan(0)
    }
  })

  it.each([
    'scu.catalog.assess_career',
    'scu.catalog.assess_marriage',
  ])('records the exact missing mandatory composite legs for %s', (scuId) => {
    expect(findScu(scuId).availability_dispositions).toEqual([expect.objectContaining({
      missing_binding_ids: [
        'registry:marsys://tool/L2/query_domain_reading',
        'registry:marsys://tool/L3/query_temporal_activation',
        'registry:marsys://tool/L2/query_contradictions',
      ],
    })])
  })

  it('keeps query_domain_reading machine-readably dark rather than inferring a composed route from adjacent producer receipts', async () => {
    const scu = findScu('scu.catalog.query_domain_reading')
    expect(scu.availability_contracts ?? []).toEqual([])
    expect(scu.availability_dispositions).toEqual([expect.objectContaining({
      binding_id: 'registry:marsys://tool/L2/query_domain_reading',
      status: 'deliberately_dark',
      reason: expect.stringContaining('bo_drishti question lenses, bo_sangati CDLM cells, bo_laksana signals'),
      source_refs: expect.arrayContaining([
        'platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts:193',
        'platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts:1010',
      ]),
    })])

    // These are exact reviewed output-spec hashes for the three producers the
    // handler reads. They are deliberately insufficient to prove the composed
    // route, which also reads runtime L1 context and derives DEFECT-001 live.
    const overlay = await overlayFor([
      adjacentProducerReceipt('bo_drishti', 'fd76f79e2f1b6a6659ef5d7bad4f5a422515fee85ab9245ac0e52fc58f9b81d2'),
      adjacentProducerReceipt('bo_sangati', 'f3918c9144df32fbc392120b9ad05a678dc4e06f7beb53cb8e62fe3ca70963dc'),
      adjacentProducerReceipt('bo_laksana', '39827b99bf58466909220fdc1e9d58e84031aae51cf2dc8e1ec0ad5d78258d47'),
    ])
    expect(overlay.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Binding is deliberately dark:')],
    })
  })

  it('keeps query_contradictions dark when adjacent graph and discovery receipts cannot attest its required contradiction relation', async () => {
    const scu = findScu('scu.catalog.query_contradictions')
    expect(scu.availability_contracts ?? []).toEqual([])
    expect(scu.availability_dispositions).toEqual([expect.objectContaining({
      binding_id: 'registry:marsys://tool/L2/query_contradictions',
      status: 'deliberately_dark',
      reason: expect.stringContaining('Every invocation reads bodha_contradictions'),
      source_refs: expect.arrayContaining([
        'platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:101',
        'platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:125',
        'platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:140',
      ]),
    })])

    // bo_karanajala attests its graph-edge output and bo_anveshana attests
    // discovery/anomaly output. Neither receipt represents the mandatory
    // bodha_contradictions relation read by this handler on every invocation.
    const overlay = await overlayFor([
      adjacentProducerReceipt('bo_karanajala', '2d474e10daf4319b71b664cde18c51dab74d8227a7092b488a28bf36aa25ddfb'),
      adjacentProducerReceipt('bo_anveshana', '4debaff16035da221a7c234b5fc7cd8d819d680d5f44cf615cfaac7f56215885'),
    ])
    expect(overlay.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Binding is deliberately dark:')],
    })
  })

  it('keeps judgment_query dark when direct-leg producer receipts cannot attest its assembled request response', async () => {
    const scu = findScu('scu.catalog.judgment_query')
    expect(scu.availability_contracts ?? []).toEqual([])
    expect(scu.availability_dispositions).toEqual([expect.objectContaining({
      binding_id: 'registry:marsys://tool/L-JUDGMENT/judgment_query',
      status: 'deliberately_dark',
      reason: expect.stringContaining('resolves chart facts for the requested bhava'),
      source_refs: expect.arrayContaining([
        'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:746',
        'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:824',
        'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:890',
        'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:1286',
        'platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:1308',
      ]),
    })])

    // These exact reviewed receipts cover direct divisional, fired-yoga,
    // dasha, and signal legs. They do not attest the handler's request-specific
    // chart-fact resolution, live mechanism reads, or assembled judgment result.
    const overlay = await overlayFor([
      adjacentProducerReceipt('ga_vargas', '5f332a4889cb465f317fe7f2315bd59a7aee9d53df58e283b436040403a9bb51'),
      adjacentProducerReceipt('ga_yoga', 'fdd546e448c5b4ea4a8d2562e93b2883324ceac8e9c0644c9ec9aeaa2b4a3246'),
      adjacentProducerReceipt('ga_dashas', '573e8aa1a0298d6626784b5ff540c004fd4d2298b6b47d2980a447acdc193d14'),
      adjacentProducerReceipt('bo_laksana', '39827b99bf58466909220fdc1e9d58e84031aae51cf2dc8e1ec0ad5d78258d47'),
    ])
    expect(overlay.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Binding is deliberately dark:')],
    })
  })

  it('keeps query_classical_texts dark when corpus and topic-index receipts cannot attest its served search result', async () => {
    const scu = findScu('scu.catalog.query_classical_texts')
    expect(scu.availability_contracts ?? []).toEqual([])
    expect(scu.availability_dispositions).toEqual([expect.objectContaining({
      binding_id: 'registry:marsys://tool/L0/query_classical_texts',
      status: 'deliberately_dark',
      reason: expect.stringContaining('serve content_summary and topics'),
      source_refs: expect.arrayContaining([
        'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_classical_texts.ts:186',
        'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_classical_texts.ts:250',
        'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_classical_texts.ts:286',
        'platform/supabase/migrations/609_nirmana_l0_digest_spec_revision.sql:27',
      ]),
    })])

    // bg_texts covers a fixed subset of corpus fields and text IDs; bg_text_index
    // covers only chunk_id/topic_tag. Neither attests the served summaries/topics
    // or the request-specific hybrid/list ranking that this handler returns.
    const overlay = await overlayFor([
      adjacentProducerReceipt('bg_texts', '10416cda800b6bd6d606f8daee76b06928071d66b09ff733a3b48ebc734c02f6'),
      adjacentProducerReceipt('bg_text_index', 'd64d63f85dc52de32537731121bfc696d3fcee7e9ab1d01415a019d2944c81e7'),
    ])
    expect(overlay.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Binding is deliberately dark:')],
    })
  })

  it('keeps query_dosha_catalog dark when its related digest omits a served catalog field', async () => {
    const scu = findScu('scu.catalog.query_dosha_catalog')
    expect(scu.availability_contracts ?? []).toEqual([])
    expect(scu.availability_dispositions).toEqual([expect.objectContaining({
      binding_id: 'registry:marsys://tool/L0/query_dosha_catalog',
      status: 'deliberately_dark',
      reason: expect.stringContaining('SELECT * rows from brahma_dosha_catalog, including created_at'),
      source_refs: expect.arrayContaining([
        'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dosha_catalog.ts:75',
        'platform/supabase/migrations/601_nirmana_l0_wave1_wave2_output_digest_specs.sql:40',
      ]),
    })])

    // bg_doshas is the reviewed producer linked to this catalog, but its
    // digest leaves out created_at even though the handler's SELECT * serves
    // it. A plausible fresh matching receipt cannot fill that route gap.
    const overlay = await overlayFor([
      globalProducerReceipt('bg_doshas', 'c4c570057c4d29495acb44cf3eff9ea907872a0e17eaf7e8878deea987a67346'),
    ])
    expect(overlay.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
      gaps: [expect.stringContaining('Binding is deliberately dark:')],
    })
  })

  it('activates query_formula_constants only from a fresh, matching global formula-constants receipt', async () => {
    const scu = findScu('scu.catalog.query_formula_constants')
    const bindingId = 'registry:marsys://tool/L0/query_formula_constants'
    const [requirement] = producerRequirements(scu.scu_id)

    expect(scu.availability_dispositions ?? []).toEqual([])
    expect(scu.producer_output_claims).toEqual([{
      asset_id: 'bg_formula_constants',
      component: 'formula_constants',
      output_digest_spec_sha256: '126465c083e5a3ca77c545a8ef6954a5d79b9df3104d79efe371960a2c55738b',
      disposition: 'reviewed_output',
      evidence: 'platform/supabase/migrations/598_nirmana_output_digest_specs.sql:41-43',
    }])
    expect(requirement).toEqual({
      kind: 'producer_output',
      asset_id: 'bg_formula_constants',
      spec_sha256: '126465c083e5a3ca77c545a8ef6954a5d79b9df3104d79efe371960a2c55738b',
      scope: 'global',
      source_ref: 'platform/supabase/migrations/598_nirmana_output_digest_specs.sql:41-43',
    })

    const available = await overlayFor([globalProducerReceipt(requirement!.asset_id, requirement!.spec_sha256)])
    expect(available.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      available_binding_ids: [bindingId],
    })

    for (const [rows, state] of [
      [[], 'dark'],
      [[globalProducerReceipt(requirement!.asset_id, 'b'.repeat(64))], 'incompatible'],
      [[globalProducerReceipt(requirement!.asset_id, requirement!.spec_sha256, { freshness_state: 'stale' })], 'dark'],
    ] as const) {
      const unavailable = await overlayFor(rows)
      expect(unavailable.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
        state,
        available_binding_ids: [],
      })
    }
  })

  it('activates query_dasha_systems only from a fresh, matching global dasha-system receipt', async () => {
    const scu = findScu('scu.catalog.query_dasha_systems')
    const bindingId = 'registry:marsys://tool/L0/query_dasha_systems'
    const [requirement] = producerRequirements(scu.scu_id)

    expect(scu.availability_dispositions ?? []).toEqual([])
    expect(scu.producer_output_claims).toEqual([{
      asset_id: 'bg_dasha_systems',
      component: 'dasha_system_catalog',
      output_digest_spec_sha256: 'b0e0e96b0c681dcc0929074eee3733875c0c4181270913cad98fbbcace0a8593',
      disposition: 'reviewed_output',
      evidence: 'platform/supabase/migrations/601_nirmana_l0_wave1_wave2_output_digest_specs.sql:39',
    }])
    expect(requirement).toEqual({
      kind: 'producer_output',
      asset_id: 'bg_dasha_systems',
      spec_sha256: 'b0e0e96b0c681dcc0929074eee3733875c0c4181270913cad98fbbcace0a8593',
      scope: 'global',
      source_ref: 'platform/supabase/migrations/601_nirmana_l0_wave1_wave2_output_digest_specs.sql:39',
    })

    const available = await overlayFor([globalProducerReceipt(requirement!.asset_id, requirement!.spec_sha256)])
    expect(available.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
      available_binding_ids: [bindingId],
    })

    for (const [rows, state] of [
      [[], 'dark'],
      [[globalProducerReceipt(requirement!.asset_id, 'a'.repeat(64))], 'incompatible'],
      [[globalProducerReceipt(requirement!.asset_id, requirement!.spec_sha256, { freshness_state: 'stale' })], 'dark'],
    ] as const) {
      const unavailable = await overlayFor(rows)
      expect(unavailable.availability.find((entry) => entry.scu_id === scu.scu_id)).toMatchObject({
        state,
        available_binding_ids: [],
      })
    }
  })

  it('activates each concrete primary binding only from its own exact evidence and keeps the remaining slice dark', async () => {
    const requirements = FIRST_SLICE.concrete.flatMap(producerRequirements)
    // The real SQL aggregates probe evidence onto every result row; put the
    // fixture anchor first to model the loader's `queryRows[0]` extraction.
    const complete = [transitProbeAnchor(), ...requirements.map(receipt)]
    const overlay = await overlayFor(complete)

    for (const scuId of FIRST_SLICE.concrete) {
      const scu = findScu(scuId)
      expect(overlay.availability.find((entry) => entry.scu_id === scuId), scuId).toMatchObject({
        available_binding_ids: [`registry:${scu.primary_binding_uri}`],
      })
    }
    for (const scuId of FIRST_SLICE.deliberately_dark) {
      expect(overlay.availability.find((entry) => entry.scu_id === scuId), scuId).toMatchObject({
        state: 'dark',
        available_binding_ids: [],
        gaps: [expect.stringContaining('Binding is deliberately dark:')],
      })
    }
  })

  it.each(FIRST_SLICE.concrete)('fails closed for %s when one of its own required receipts is absent', async (scuId) => {
    const requirements = producerRequirements(scuId)
    const omitted = requirements[0]
    const rows = requirements.slice(1).map(receipt)
    if (scuId === 'scu.catalog.query_planet_transit') {
      // The transit binding is service-backed, so a producer receipt cannot
      // substitute for its authenticated probe.
      const overlay = await overlayFor([])
      expect(overlay.availability.find((entry) => entry.scu_id === scuId)).toMatchObject({ state: 'dark', available_binding_ids: [] })
      return
    }
    expect(omitted, scuId).toBeDefined()
    const overlay = await overlayFor(rows)
    expect(overlay.availability.find((entry) => entry.scu_id === scuId), scuId).toMatchObject({
      state: 'dark',
      available_binding_ids: [],
    })
  })
})
