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
