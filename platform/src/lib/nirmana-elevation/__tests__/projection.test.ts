import { describe, expect, it } from 'vitest'
import { canonicalNirmanaOptimizationVerdictDigest, canonicalNirmanaRebuildEvidenceDigest, type NirmanaElevationManifest } from '../definitions'
import {
  deriveEligibleNextAssetIds,
  deriveLayerActivityState,
  projectAssetFrontier,
  projectAssetMilestones,
  projectCampaignStages,
  projectCompletion,
  projectLayerWaveProgress,
  projectProgrammePosition,
  projectProgrammePositionV21,
  summarizeStageGroupState,
  type CampaignEvent,
  type NirmanaLayerId,
  type NirmanaStageId,
} from '../projection'

type ManifestAsset = NirmanaElevationManifest['assets'][number]

const observedAt = '2026-08-26T09:00:00.000Z'
const activeDefinition = { campaignId: 'nirmana-elevation', definitionRevision: 'v2' } as const

function projectStages(input: Omit<Parameters<typeof projectCampaignStages>[0], 'campaignId' | 'definitionRevision'>) {
  return projectCampaignStages({ ...activeDefinition, ...input })
}

function projectMilestones(input: Omit<Parameters<typeof projectAssetMilestones>[0], 'campaignId' | 'definitionRevision'>) {
  return projectAssetMilestones({ ...activeDefinition, ...input })
}

function event(overrides: Partial<CampaignEvent> = {}): CampaignEvent {
  const merged = {
    campaign_id: 'nirmana-elevation',
    definition_revision: 'v2',
    event_type: 'asset_analysis_accepted',
    entity_type: 'asset',
    entity_id: 'bg_alpha',
    layer: 'L0',
    evidence_payload: {},
    source_kind: 'test',
    source_ref: 'event:test',
    observed_at: observedAt,
    recorded_at: observedAt,
    ...overrides,
  }
  return {
    ...merged,
    writer_identity: overrides.writer_identity ?? (merged.source_kind === 'server_reconstructed'
      ? 'nirmana_evidence_ingress_writer'
      : 'nirmana_campaign_control_writer'),
  }
}

function transition(from_stage: string | null, to_stage: string, recorded_at: string): CampaignEvent {
  return event({
    event_type: 'stage_transition_accepted',
    entity_type: 'campaign_stage',
    entity_id: to_stage,
    layer: null,
    evidence_payload: {
      schema_version: 'nirmana-stage-transition-receipt/v1', from_stage, to_stage, manifest_sha256: 'a'.repeat(64),
    },
    source_ref: 'nirmana-elevation:stage-spine',
    source_kind: 'server_reconstructed',
    observed_at: recorded_at,
    recorded_at,
  })
}

function foundationLane(laneId: string, minute = Number(laneId.charCodeAt(0) - 64)): CampaignEvent {
  const timestamp = `2026-08-26T09:${String(minute).padStart(2, '0')}:00.000Z`
  return event({
    event_type: 'foundation_lane_accepted',
    entity_type: 'foundation_lane',
    entity_id: laneId,
    layer: null,
    evidence_payload: foundationPayload(laneId),
    source_ref: `nirmana-elevation:foundation-lane:${laneId}`,
    source_kind: 'server_reconstructed',
    observed_at: timestamp,
    recorded_at: timestamp,
  })
}

function foundationPayload(laneId: string) {
  const base = { schema_version: 'nirmana-foundation-lane-receipt/v1' as const, lane_id: laneId }
  if (laneId === 'A') return { ...base, manifest_sha256: 'a'.repeat(64), asset_count: 1 }
  if (laneId === 'B') return { ...base, manifest_sha256: 'a'.repeat(64), build_run_count: 0, terminal_build_run_count: 0 }
  if (laneId === 'C') return { ...base, manifest_sha256: 'a'.repeat(64), registry_fingerprint_set_sha256: 'b'.repeat(64), manifest_asset_count: 1, live_registry_asset_count: 1, invalidated_analysis_count: 0 }
  if (laneId === 'D') return { ...base, manifest_sha256: 'a'.repeat(64), main_sha: 'b'.repeat(40), serving_sha: 'b'.repeat(40), serving_revision: 'amjis-web-01799-abc', ci_run_id: '123' }
  return { ...base, manifest_sha256: 'a'.repeat(64), migration_filename: '592_nirmana_elevation_campaign_evidence.sql', migration_sha256: 'c'.repeat(64) }
}

const emptyLayers = [
  { layer_id: 'L0' as const, state: 'locked', assets_total: 2, frozen: 0 },
  { layer_id: 'L1' as const, state: 'locked', assets_total: 1, frozen: 0 },
  { layer_id: 'L2' as const, state: 'locked', assets_total: 0, frozen: 0 },
  { layer_id: 'L3' as const, state: 'locked', assets_total: 0, frozen: 0 },
  { layer_id: 'L4' as const, state: 'locked', assets_total: 0, frozen: 0 },
  { layer_id: 'L5' as const, state: 'locked', assets_total: 0, frozen: 0 },
]

function manifestAsset(overrides: Partial<ManifestAsset> = {}): ManifestAsset {
  return {
    asset_id: 'bg_alpha',
    layer: 'L0',
    wave_index: 0,
    execution_obligation: 'build',
    depends_on: [],
    ...overrides,
  }
}

function assetEvents(asset: ManifestAsset, eventTypes: string[], overrides: Partial<CampaignEvent> = {}): CampaignEvent[] {
  const binding = { registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64) }
  const decision = {
    ...binding,
    verdict: 'optimize' as const,
    basis: {
      measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'optimize' as const, summary: 'A governed change is required.', output_contract: 'digest_identical' as const },
  }
  const payloadFor = (eventType: string) => {
    if (eventType === 'asset_analysis_accepted') return binding
    if (eventType === 'optimization_verdict_accepted') return decision
    if (eventType === 'implementation_accepted') return { ...binding, decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision), implementation_digest: 'c'.repeat(64) }
    if (eventType === 'accepted_rebuild_observed') return {
      ...binding,
      build_run_id: '11111111-1111-4111-8111-111111111111',
      wave_index: asset.wave_index ?? 0,
      authorization_sha256: 'f'.repeat(64),
      decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision),
      implementation_digest: eventTypes.includes('implementation_accepted') ? 'c'.repeat(64) : null,
      output_digest: 'd'.repeat(64), output_digest_spec_sha256: 'e'.repeat(64),
    }
    if (eventType === 'probe_accepted') return { ...binding, probe_contract_sha256: 'f'.repeat(64), response_digest: '0'.repeat(64) }
    if (eventType === 'integrity_verified') return { ...binding, integrity_contract_sha256: '1'.repeat(64), result_digest: '2'.repeat(64) }
    if (eventType === 'asset_frozen') return { ...binding, lifecycle_digest: '3'.repeat(64) }
    if (['static_accepted', 'source_accepted', 'empty_accepted', 'retired_with_disposition'].includes(eventType)) {
      const disposition = ({ static_accepted: 'static_acceptance', source_accepted: 'source_acceptance', empty_accepted: 'empty_acceptance', retired_with_disposition: 'retired_with_disposition' } as const)[eventType as 'static_accepted' | 'source_accepted' | 'empty_accepted' | 'retired_with_disposition']
      return { ...binding, disposition, disposition_digest: '4'.repeat(64) }
    }
    return {}
  }
  const sourceFor = (eventType: string) => {
    if (['asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted', 'static_accepted', 'source_accepted', 'empty_accepted', 'retired_with_disposition'].includes(eventType)) return `git:${'a'.repeat(40)}`
    if (eventType === 'accepted_rebuild_observed' || eventType === 'producer_covered') return 'build_run:11111111-1111-4111-8111-111111111111'
    if (eventType === 'probe_accepted') return `nirmana-elevation:health-probe:${asset.asset_id}`
    if (eventType === 'integrity_verified') return `nirmana-elevation:integrity:${asset.asset_id}`
    if (eventType === 'asset_frozen') return `nirmana-elevation:freeze:${asset.asset_id}`
    return 'event:test'
  }
  const sourceKindFor = (eventType: string) => ['probe_accepted', 'integrity_verified', 'asset_frozen'].includes(eventType)
    ? 'server_reconstructed' : ['asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted', 'static_accepted', 'source_accepted', 'empty_accepted', 'retired_with_disposition'].includes(eventType)
      ? 'git_commit' : eventType === 'accepted_rebuild_observed' ? 'build_run' : 'test'
  return eventTypes.map((event_type, index) => event({
    event_type,
    entity_id: asset.asset_id,
    layer: asset.layer,
    evidence_payload: payloadFor(event_type),
    source_ref: sourceFor(event_type),
    source_kind: sourceKindFor(event_type),
    observed_at: `2026-08-26T10:${String(index).padStart(2, '0')}:00.000Z`,
    recorded_at: `2026-08-26T10:${String(index).padStart(2, '0')}:00.000Z`,
    ...overrides,
  }))
}

describe('projectCampaignStages', () => {
  it('treats a delayed same-digest bootstrap receipt replay as idempotent stage evidence', () => {
    const bootstrap = transition(null, 'BOOTSTRAP', '2026-08-26T09:00:00.000Z')
    const advance = transition('BOOTSTRAP', 'T0_CENSUS', '2026-08-26T09:00:01.000Z')
    const replay = {
      ...bootstrap,
      observed_at: '2026-08-26T09:00:02.000Z',
      recorded_at: '2026-08-26T09:00:02.000Z',
    }

    const result = projectStages({
      definitionStatus: 'reconciling',
      events: [bootstrap, advance, replay],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBe('T0_CENSUS')
    expect(result.stages[0]).toMatchObject({ stage_id: 'BOOTSTRAP', state: 'completed' })
    expect(result.stages[1]).toMatchObject({ stage_id: 'T0_CENSUS', state: 'active' })
    expect(result.contradictions).toEqual([])
  })

  it('blocks delayed bootstrap receipt replays whose prerequisite digests conflict', () => {
    const bootstrap = transition(null, 'BOOTSTRAP', '2026-08-26T09:00:00.000Z')
    const advance = transition('BOOTSTRAP', 'T0_CENSUS', '2026-08-26T09:00:01.000Z')
    const conflict = {
      ...bootstrap,
      evidence_payload: {
        schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: null, to_stage: 'BOOTSTRAP', manifest_sha256: 'b'.repeat(64),
      },
      observed_at: '2026-08-26T09:00:02.000Z',
      recorded_at: '2026-08-26T09:00:02.000Z',
    }

    const result = projectStages({
      definitionStatus: 'reconciling',
      events: [bootstrap, advance, conflict],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBe('T0_CENSUS')
    expect(result.stages[1]).toMatchObject({ stage_id: 'T0_CENSUS', state: 'blocked' })
    expect(result.contradictions).toEqual([
      'Contradictory stage transition null -> BOOTSTRAP: prerequisite digests differ.',
    ])
  })

  it('uses the latest accepted stage transition instead of guessing from incomplete stages', () => {
    const result = projectStages({
      definitionStatus: 'reconciling',
      events: [
        transition('BOOTSTRAP', 'T0_CENSUS', '2026-08-26T09:01:00.000Z'),
        transition('T0_CENSUS', 'PLAN_FROZEN', '2026-08-26T09:02:00.000Z'),
      ],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBe('PLAN_FROZEN')
    expect(result.stages.find(({ stage_id }) => stage_id === 'T0_CENSUS')?.state).toBe('completed')
    expect(result.stages.find(({ stage_id }) => stage_id === 'PLAN_FROZEN')?.state).toBe('active')
  })

  it('leaves current_stage unknown when no valid stage-transition evidence exists', () => {
    const result = projectStages({
      definitionStatus: 'frozen',
      events: [event({ event_type: 'stage_transition_accepted', entity_type: 'campaign_stage', entity_id: 'L0', evidence_payload: {} })],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBeNull()
    expect(result.stages.some(({ state }) => state === 'active')).toBe(false)
  })

  it('ignores a stale-first definition cohort when selecting the active stage', () => {
    const stale = {
      ...transition('L0', 'L1', '2026-08-26T09:02:00.000Z'),
      definition_revision: 'v1',
    }
    const active = transition('BOOTSTRAP', 'T0_CENSUS', '2026-08-26T09:01:00.000Z')

    const result = projectStages({
      definitionStatus: 'reconciling',
      events: [stale, active],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBe('T0_CENSUS')
    expect(result.contradictions).toEqual([])
  })

  it('does not mark F0 complete from a frozen denominator alone', () => {
    const result = projectStages({ definitionStatus: 'frozen', events: [], layers: emptyLayers })
    const foundation = result.stages.find(({ stage_id }) => stage_id === 'F0_FOUNDATION')

    expect(foundation).toMatchObject({ state: 'unknown', earned: 0, required: 5 })
    expect(foundation?.foundation_lanes?.every(({ state }) => state === 'unknown')).toBe(true)
  })

  it('projects all five F0 lanes from foundation-lane receipts and leaves missing lanes unknown', () => {
    const complete = projectStages({
      definitionStatus: 'frozen',
      events: ['A', 'B', 'C', 'D', 'E'].map((laneId) => foundationLane(laneId)),
      layers: emptyLayers,
    })
    const incomplete = projectStages({
      definitionStatus: 'frozen',
      events: ['A', 'B', 'C', 'D'].map((laneId) => foundationLane(laneId)),
      layers: emptyLayers,
    })

    expect(complete.stages.find(({ stage_id }) => stage_id === 'F0_FOUNDATION')).toMatchObject({
      state: 'completed', earned: 5, required: 5,
    })
    expect(complete.stages.find(({ stage_id }) => stage_id === 'F0_FOUNDATION')?.foundation_lanes?.map(({ lane_id, state }) => [lane_id, state])).toEqual([
      ['A', 'completed'], ['B', 'completed'], ['C', 'completed'], ['D', 'completed'], ['E', 'completed'],
    ])
    expect(incomplete.stages.find(({ stage_id }) => stage_id === 'F0_FOUNDATION')?.foundation_lanes?.at(-1)).toMatchObject({ lane_id: 'E', state: 'unknown' })
  })

  it('does not project Lane C from receipts missing its registry fingerprint or reporting invalidated analysis', () => {
    const omittedFingerprint = foundationLane('C')
    omittedFingerprint.evidence_payload = {
      schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'C', manifest_sha256: 'a'.repeat(64),
      manifest_asset_count: 1, live_registry_asset_count: 1, invalidated_analysis_count: 0,
    }
    const invalidatedAnalysis = foundationLane('C')
    invalidatedAnalysis.evidence_payload = {
      schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'C', manifest_sha256: 'a'.repeat(64),
      registry_fingerprint_set_sha256: 'b'.repeat(64), manifest_asset_count: 1,
      live_registry_asset_count: 1, invalidated_analysis_count: 1,
    }

    for (const invalidLaneC of [omittedFingerprint, invalidatedAnalysis]) {
      const result = projectStages({
        definitionStatus: 'frozen',
        events: ['A', 'B', 'D', 'E'].map((laneId) => foundationLane(laneId)).concat(invalidLaneC),
        layers: emptyLayers,
      })
      const foundation = result.stages.find(({ stage_id }) => stage_id === 'F0_FOUNDATION')

      expect(foundation).toMatchObject({ state: 'unknown', earned: 4, required: 5 })
      expect(foundation?.foundation_lanes?.find(({ lane_id }) => lane_id === 'C')).toMatchObject({ state: 'unknown' })
    }
  })

  it('marks a layer complete only when every in-layer asset is frozen and prior layers are complete', () => {
    const events = [
      ...['A', 'B', 'C', 'D', 'E'].map((laneId) => foundationLane(laneId)),
      transition('F0_FOUNDATION', 'L0', '2026-08-26T09:10:00.000Z'),
      transition('L0', 'L1', '2026-08-26T09:11:00.000Z'),
    ]
    const completed = projectStages({
      definitionStatus: 'frozen',
      events,
      layers: emptyLayers.map((layer) => layer.layer_id === 'L0'
        ? { ...layer, frozen: 2 }
        : layer.layer_id === 'L1' ? { ...layer, frozen: 1 } : layer),
    })
    const priorIncomplete = projectStages({
      definitionStatus: 'frozen',
      events,
      layers: emptyLayers.map((layer) => layer.layer_id === 'L0'
        ? { ...layer, frozen: 1 }
        : layer.layer_id === 'L1' ? { ...layer, frozen: 1 } : layer),
    })

    expect(completed.stages.find(({ stage_id }) => stage_id === 'L0')?.state).toBe('completed')
    expect(completed.stages.find(({ stage_id }) => stage_id === 'L1')?.state).toBe('completed')
    expect(priorIncomplete.stages.find(({ stage_id }) => stage_id === 'L0')?.state).not.toBe('completed')
    expect(priorIncomplete.stages.find(({ stage_id }) => stage_id === 'L1')?.state).not.toBe('completed')
    expect(priorIncomplete.stages.find(({ stage_id }) => stage_id === 'L1')?.state).toBe('blocked')
    expect(priorIncomplete.contradictions.some((contradiction) => contradiction.includes('L0 -> L1'))).toBe(true)
  })

  it('turns contradictory transitions into a blocked stage and a contradiction', () => {
    const result = projectStages({
      definitionStatus: 'frozen',
      events: [
        transition('BOOTSTRAP', 'T0_CENSUS', '2026-08-26T09:01:00.000Z'),
        transition('T0_CENSUS', 'DENOMINATOR_FROZEN', '2026-08-26T09:02:00.000Z'),
      ],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBe('DENOMINATOR_FROZEN')
    expect(result.stages.find(({ stage_id }) => stage_id === 'DENOMINATOR_FROZEN')?.state).toBe('blocked')
    expect(result.contradictions).toHaveLength(1)
    expect(result.contradictions[0]).toContain('T0_CENSUS -> DENOMINATOR_FROZEN')
  })
})

describe('projectAssetMilestones', () => {
  it('requires and earns all six milestones for a build with an accepted change', () => {
    const asset = manifestAsset()
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
      'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ])
    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(Array(6).fill('earned'))
    expect(result).toMatchObject({ milestones_earned: 6, milestones_required: 6, current_action: null, next_action: null })
  })

  it('does not let a generic or cross-writer receipt earn a lifecycle milestone', () => {
    const asset = manifestAsset()
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
      'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ]).map((receipt) => ({ ...receipt, writer_identity: 'amjis_app' }))

    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(['current', ...Array(5).fill('pending')])
    expect(result.milestones_earned).toBe(0)
  })

  it('allows a trusted current analysis to progress after the frozen T0 registry fingerprint has drifted', () => {
    const asset = manifestAsset({ registry_fingerprint_sha256: 'f'.repeat(64) })
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
      'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ])

    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(Array(6).fill('earned'))
  })

  it('does not credit a completed run whose receipt is bound to a superseded registry analysis and decision', () => {
    const asset = manifestAsset()
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
      'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ])
    const binding = { registry_fingerprint_sha256: 'f'.repeat(64), analysis_digest: '0'.repeat(64) }
    const decision = {
      ...binding,
      verdict: 'correct' as const,
      basis: {
        measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
        evidence_refs: ['git:current-evidence'],
      },
      proposal: { action: 'correct' as const, summary: 'The current contract requires correction.', output_contract: 'correctness_change' as const },
    }
    events[0].evidence_payload = binding
    events[1].evidence_payload = decision
    events[2].evidence_payload = {
      ...binding,
      decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision),
      implementation_digest: '1'.repeat(64),
    }

    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(['earned', 'earned', 'earned', 'current', 'pending', 'pending'])
  })

  it('makes the build implementation milestone N/A when the accepted decision requires no change', () => {
    const asset = manifestAsset()
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ])
    events[1].evidence_payload = {
      registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64),
      verdict: 'examined_and_already_efficient',
      basis: {
        measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
        evidence_refs: ['git:test-evidence'],
      },
      proposal: { action: 'no_change', summary: 'No change is justified.', output_contract: 'digest_identical' },
    }
    const unchangedDecision = events[1].evidence_payload
    const rebuild = events.find(({ event_type }) => event_type === 'accepted_rebuild_observed')!
    rebuild.evidence_payload = {
      registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64),
      build_run_id: '11111111-1111-4111-8111-111111111111',
      wave_index: asset.wave_index ?? 0,
      authorization_sha256: 'f'.repeat(64),
      decision_digest: canonicalNirmanaOptimizationVerdictDigest(unchangedDecision),
      implementation_digest: null,
      output_digest: 'd'.repeat(64), output_digest_spec_sha256: 'e'.repeat(64),
    }

    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones[2]).toMatchObject({ milestone_id: 'built_or_dispositioned', state: 'not_applicable', event_type: null, accepted_at: null })
    expect(result).toMatchObject({ milestones_earned: 5, milestones_required: 5 })
  })

  it('withholds every downstream milestone from legacy-shaped or unbound receipts', () => {
    const asset = manifestAsset()
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
      'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ])
    events[1].evidence_payload = { change_required: true }
    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(['earned', 'current', 'pending', 'pending', 'pending', 'pending'])
    expect(result.milestones_earned).toBe(1)
  })

  it('makes probe implementation N/A unless a change receipt exists', () => {
    const asset = manifestAsset({ execution_obligation: 'probe' })
    const unchangedEvents = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'probe_accepted', 'integrity_verified', 'asset_frozen',
    ])
    unchangedEvents[1].evidence_payload = {
      registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64),
      verdict: 'examined_and_already_efficient',
      basis: {
        measurement: { status: 'insufficient_history', sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
        evidence_refs: ['git:test-evidence'],
      },
      proposal: { action: 'no_change', summary: 'No change is justified.', output_contract: 'digest_identical' },
    }
    const changedEvents = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted', 'probe_accepted', 'integrity_verified', 'asset_frozen',
    ])

    const unchanged = projectMilestones({ asset, events: unchangedEvents, activeRunState: null, producerAsset: null })
    const changed = projectMilestones({
      asset,
      events: changedEvents,
      activeRunState: null,
      producerAsset: null,
    })

    expect(unchanged.milestones[2].state).toBe('not_applicable')
    expect(unchanged.milestones_required).toBe(5)
    expect(changed.milestones[2].state).toBe('earned')
    expect(changed.milestones_required).toBe(6)
  })

  it.each([
    ['source_acceptance', 'source_accepted'],
    ['static_acceptance', 'static_accepted'],
    ['empty_acceptance', 'empty_accepted'],
    ['retired_with_disposition', 'retired_with_disposition'],
  ] as const)('earns disposition and skips deployment for %s', (execution_obligation, dispositionEvent) => {
    const asset = manifestAsset({ execution_obligation })
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', dispositionEvent, 'integrity_verified', 'asset_frozen',
    ])

    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones[2]).toMatchObject({ state: 'earned', event_type: dispositionEvent })
    expect(result.milestones[3].state).toBe('not_applicable')
    expect(result).toMatchObject({ milestones_earned: 5, milestones_required: 5 })
  })

  it('inherits producer execution without claiming an independent covered-asset build', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({ asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: producer.asset_id, depends_on: [producer.asset_id] })
    const producerEvents = assetEvents(producer, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted', 'accepted_rebuild_observed',
    ])
    const producerBuild = producerEvents.find(({ event_type }) => event_type === 'accepted_rebuild_observed')!
    const coveredEvents = assetEvents(covered, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered',
    ]).map((receipt) => receipt.event_type !== 'producer_covered' ? receipt : {
      ...receipt,
      evidence_payload: {
        registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64),
        producer_asset_id: producer.asset_id, producer_layer: producer.layer,
        producer_run_id: '11111111-1111-4111-8111-111111111111',
        producer_rebuild_digest: canonicalNirmanaRebuildEvidenceDigest(producerBuild.evidence_payload),
      },
      source_kind: 'build_run', source_ref: 'build_run:11111111-1111-4111-8111-111111111111',
      observed_at: '2026-08-26T10:04:00.000Z', recorded_at: '2026-08-26T10:04:00.000Z',
    })

    const withoutProducer = projectMilestones({
      asset: covered, events: coveredEvents, activeRunState: null, producerAsset: producer,
    })
    const inherited = projectMilestones({
      asset: covered, events: [...coveredEvents, ...producerEvents], activeRunState: null, producerAsset: producer,
    })

    expect(withoutProducer.milestones[3].state).toBe('current')
    expect(inherited.milestones[3]).toMatchObject({ state: 'earned', event_type: 'accepted_rebuild_observed', accepted_at: producerBuild.observed_at })
    expect(inherited.inherited_from_asset_id).toBe(producer.asset_id)
  })

  it('withholds producer coverage that lacks a typed reciprocal producer receipt', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({
      asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: producer.asset_id,
      depends_on: [producer.asset_id],
    })
    const events = [
      ...assetEvents(producer, [
        'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted', 'accepted_rebuild_observed',
      ]),
      ...assetEvents(covered, [
        'asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered',
      ]),
    ]

    const result = projectMilestones({ asset: covered, events, activeRunState: null, producerAsset: producer })

    expect(result.milestones[2]).toMatchObject({ state: 'current', event_type: null })
    expect(result.milestones[3]).toMatchObject({ state: 'pending', event_type: null })
  })

  it('withholds covered execution when the named producer run belongs to a stale producer analysis generation', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({
      asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: producer.asset_id,
      depends_on: [producer.asset_id],
    })
    const producerEvents = assetEvents(producer, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted', 'accepted_rebuild_observed',
    ]).map((event) => event.event_type !== 'accepted_rebuild_observed' ? event : {
      ...event,
      evidence_payload: { ...(event.evidence_payload as Record<string, unknown>), registry_fingerprint_sha256: 'c'.repeat(64) },
    })
    const staleRebuild = producerEvents.find((event) => event.event_type === 'accepted_rebuild_observed')!
    const coveredEvents = assetEvents(covered, ['asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered'])
      .map((event) => event.event_type !== 'producer_covered' ? event : {
        ...event,
        evidence_payload: {
          registry_fingerprint_sha256: 'a'.repeat(64), analysis_digest: 'b'.repeat(64),
          producer_asset_id: producer.asset_id, producer_layer: producer.layer,
          producer_run_id: '11111111-1111-4111-8111-111111111111',
          producer_rebuild_digest: canonicalNirmanaRebuildEvidenceDigest(staleRebuild.evidence_payload),
        },
        source_kind: 'build_run', source_ref: 'build_run:11111111-1111-4111-8111-111111111111',
        observed_at: '2026-08-26T10:04:00.000Z', recorded_at: '2026-08-26T10:04:00.000Z',
      })

    const result = projectMilestones({ asset: covered, events: [...producerEvents, ...coveredEvents], activeRunState: null, producerAsset: producer })

    expect(result.milestones[2]).toMatchObject({ state: 'earned', event_type: 'producer_covered' })
    expect(result.milestones[3]).toMatchObject({ state: 'current', event_type: null })
  })

  it('withholds determinate progress for an unresolved obligation', () => {
    const result = projectMilestones({
      asset: manifestAsset({ execution_obligation: 'unresolved' }),
      events: assetEvents(manifestAsset(), ['asset_analysis_accepted', 'asset_frozen']),
      activeRunState: 'building',
      producerAsset: null,
    })

    expect(result.milestones_earned).toBeNull()
    expect(result.milestones_required).toBeNull()
    expect(result.current_action).toBeNull()
    expect(result.next_action).toBeNull()
  })

  it('does not let stale-first events from another definition revision earn milestones', () => {
    const asset = manifestAsset()
    const events = [
      ...assetEvents(asset, ['optimization_verdict_accepted', 'implementation_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen'], { definition_revision: 'v1' }),
      ...assetEvents(asset, ['asset_analysis_accepted']),
    ]

    const result = projectMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(['earned', 'current', 'pending', 'pending', 'pending', 'pending'])
    expect(result.milestones_earned).toBe(1)
  })
})

describe('deriveEligibleNextAssetIds', () => {
  it('returns only unblocked, resolved assets in the next unfinished wave', () => {
    const assets = [
      manifestAsset({ asset_id: 'bg_beta' }),
      manifestAsset({ asset_id: 'bg_alpha' }),
      manifestAsset({ asset_id: 'bg_blocked' }),
      manifestAsset({ asset_id: 'bg_unresolved', execution_obligation: 'unresolved' }),
      manifestAsset({ asset_id: 'bg_later', wave_index: 1, depends_on: ['bg_alpha'] }),
    ]

    expect(deriveEligibleNextAssetIds({
      manifestAssets: assets,
      frozenAssetIds: new Set(),
      blockedAssetIds: new Set(['bg_blocked']),
      currentLayer: 'L0',
      currentWave: 0,
    })).toEqual(['bg_alpha', 'bg_beta'])
  })

  it('refuses to skip an unfinished earlier wave', () => {
    const assets = [
      manifestAsset({ asset_id: 'bg_first', wave_index: 0 }),
      manifestAsset({ asset_id: 'bg_second', wave_index: 1, depends_on: ['bg_first'] }),
    ]

    expect(deriveEligibleNextAssetIds({
      manifestAssets: assets,
      frozenAssetIds: new Set(),
      blockedAssetIds: new Set(),
      currentLayer: 'L0',
      currentWave: 1,
    })).toEqual([])
  })

  it('requires every same-layer dependency to be frozen or validly inherited', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', wave_index: 0, covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({
      asset_id: 'bg_covered', wave_index: 0, execution_obligation: 'producer_covered', producer_id: producer.asset_id, depends_on: [producer.asset_id],
    })
    const consumer = manifestAsset({ asset_id: 'bg_consumer', wave_index: 1, depends_on: [covered.asset_id] })

    expect(deriveEligibleNextAssetIds({
      manifestAssets: [producer, covered, consumer],
      frozenAssetIds: new Set([producer.asset_id]),
      blockedAssetIds: new Set(),
      currentLayer: 'L0',
      currentWave: 1,
    })).toEqual([consumer.asset_id])
    expect(deriveEligibleNextAssetIds({
      manifestAssets: [producer, covered, consumer],
      frozenAssetIds: new Set([producer.asset_id]),
      blockedAssetIds: new Set([covered.asset_id]),
      currentLayer: 'L0',
      currentWave: 1,
    })).toEqual([])
  })

  it('keeps L1 locked until every L0 asset is frozen', () => {
    const l0a = manifestAsset({ asset_id: 'bg_alpha' })
    const l0b = manifestAsset({ asset_id: 'bg_beta' })
    const l1 = manifestAsset({ asset_id: 'ga_alpha', layer: 'L1', depends_on: [l0a.asset_id] })
    const input = {
      manifestAssets: [l0a, l0b, l1],
      blockedAssetIds: new Set<string>(),
      currentLayer: 'L1' as const,
      currentWave: 0,
    }

    expect(deriveEligibleNextAssetIds({ ...input, frozenAssetIds: new Set([l0a.asset_id]) })).toEqual([])
    expect(deriveEligibleNextAssetIds({ ...input, frozenAssetIds: new Set([l0a.asset_id, l0b.asset_id]) })).toEqual([l1.asset_id])
  })

  it('does not treat producer inheritance as the covered asset freeze required to unlock L1', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({
      asset_id: 'bg_covered',
      execution_obligation: 'producer_covered',
      producer_id: producer.asset_id,
      depends_on: [producer.asset_id],
    })
    const l1 = manifestAsset({ asset_id: 'ga_alpha', layer: 'L1', depends_on: [producer.asset_id] })

    expect(deriveEligibleNextAssetIds({
      manifestAssets: [producer, covered, l1],
      frozenAssetIds: new Set([producer.asset_id]),
      blockedAssetIds: new Set(),
      currentLayer: 'L1',
      currentWave: 0,
    })).toEqual([])
  })
})

describe('projectLayerWaveProgress', () => {
  const asset = (layer: NirmanaLayerId, states: Record<string, 'earned' | 'current' | 'pending' | 'not_applicable'>) => ({
    layer,
    milestones: Object.entries(states).map(([milestone_id, state]) => ({ milestone_id, state })),
  })

  it('returns exactly 6 entries in W1..W6 order for a layer with no assets', () => {
    const result = projectLayerWaveProgress([], 'L0')
    expect(result.map((w) => w.wave_id)).toEqual(['W1', 'W2', 'W3', 'W4', 'W5', 'W6'])
    expect(result.every((w) => w.earned === 0 && w.required === 0)).toBe(true)
  })

  it('counts earned/required per milestone, excluding not_applicable from the denominator', () => {
    const assets = [
      asset('L0', { analysed: 'earned', decision_accepted: 'earned', built_or_dispositioned: 'earned', deployed_and_executed: 'not_applicable', verified: 'current', frozen: 'pending' }),
      asset('L0', { analysed: 'earned', decision_accepted: 'pending', built_or_dispositioned: 'pending', deployed_and_executed: 'earned', verified: 'pending', frozen: 'pending' }),
    ]
    const result = projectLayerWaveProgress(assets, 'L0')
    const byWave = Object.fromEntries(result.map((w) => [w.wave_id, w]))
    expect(byWave.W1).toMatchObject({ earned: 2, required: 2 })
    expect(byWave.W2).toMatchObject({ earned: 1, required: 2 })
    expect(byWave.W4).toMatchObject({ earned: 1, required: 1 }) // one asset's deployed_and_executed is not_applicable, excluded
  })

  it('ignores assets from other layers', () => {
    const assets = [asset('L1', { analysed: 'earned', decision_accepted: 'pending', built_or_dispositioned: 'pending', deployed_and_executed: 'pending', verified: 'pending', frozen: 'pending' })]
    const result = projectLayerWaveProgress(assets, 'L0')
    expect(result.every((w) => w.required === 0)).toBe(true)
  })
})

describe('summarizeStageGroupState', () => {
  const stage = (stage_id: string, state: string) => ({
    stage_id: stage_id as NirmanaStageId,
    state: state as 'completed' | 'active' | 'locked' | 'blocked' | 'paused' | 'unknown',
  })

  it('is completed only when every member is completed', () => {
    const stages = [stage('BOOTSTRAP', 'completed'), stage('T0_CENSUS', 'completed')]
    expect(summarizeStageGroupState(stages, ['BOOTSTRAP', 'T0_CENSUS'])).toBe('completed')
  })

  it('surfaces blocked over any other non-completed state', () => {
    const stages = [stage('BOOTSTRAP', 'completed'), stage('T0_CENSUS', 'blocked'), stage('PLAN_FROZEN', 'locked')]
    expect(summarizeStageGroupState(stages, ['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN'])).toBe('blocked')
  })

  it('surfaces active when nothing is blocked or paused', () => {
    const stages = [stage('BOOTSTRAP', 'completed'), stage('T0_CENSUS', 'active'), stage('PLAN_FROZEN', 'locked')]
    expect(summarizeStageGroupState(stages, ['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN'])).toBe('active')
  })

  it('is unknown for an empty or unmatched group', () => {
    expect(summarizeStageGroupState([], ['BOOTSTRAP'])).toBe('unknown')
  })
})

describe('projectProgrammePosition', () => {
  it('reports execution not yet evidenced when there is no current stage', () => {
    const position = projectProgrammePosition({ currentStage: null, layerWaveProgress: {}, layerNames: {}, openWp: null })
    expect(position.phase_id).toBe('PHASE_A')
  })

  it('reports PHASE_A for any pre-L0 stage', () => {
    const position = projectProgrammePosition({ currentStage: 'F0_FOUNDATION', layerWaveProgress: {}, layerNames: {}, openWp: null })
    expect(position.phase_id).toBe('PHASE_A')
  })

  it('reports the layer id for a layer stage, independent of openWp', () => {
    const layerWaveProgress = { L0: [{ wave_id: 'W1' as const, label: 'ANALYZE', milestone_id: 'analysed', earned: 17, required: 40 }] }
    const position = projectProgrammePosition({ currentStage: 'L0', layerWaveProgress, layerNames: { L0: 'Brahmagyan' }, openWp: { wp_id: 'WP-1' } })
    expect(position.phase_id).toBe('L0')
    expect(position.label).toContain('L0')
    expect(position.label).toContain('W1')
    expect(position.label).toContain('17/40')
  })

  it('reports PHASE_Z for CLOSING/COMPLETE', () => {
    expect(projectProgrammePosition({ currentStage: 'CLOSING', layerWaveProgress: {}, layerNames: {}, openWp: null }).phase_id).toBe('PHASE_Z')
    expect(projectProgrammePosition({ currentStage: 'COMPLETE', layerWaveProgress: {}, layerNames: {}, openWp: null }).phase_id).toBe('PHASE_Z')
  })

  it('reports O_WAVE when there is an open WP and no current stage yet (previously untested branch)', () => {
    const position = projectProgrammePosition({ currentStage: null, layerWaveProgress: {}, layerNames: {}, openWp: { wp_id: 'WP-3' } })
    expect(position.phase_id).toBe('O_WAVE')
    expect(position.label).toContain('WP-3')
  })
})

describe('projectCompletion', () => {
  it('sums earned/required only across assets with non-null milestones_required', () => {
    const result = projectCompletion([
      { milestones_earned: 3, milestones_required: 6 },
      { milestones_earned: null, milestones_required: null },
      { milestones_earned: 2, milestones_required: 4 },
    ])
    expect(result).toEqual({ earned: 5, required: 10, percent: 50 })
  })

  it('floors instead of rounding (199/200 must read 99, not 100)', () => {
    const result = projectCompletion([{ milestones_earned: 199, milestones_required: 200 }])
    expect(result.percent).toBe(99)
  })

  it('reports percent null when required is zero', () => {
    const result = projectCompletion([{ milestones_earned: null, milestones_required: null }])
    expect(result).toEqual({ earned: 0, required: 0, percent: null })
  })
})

describe('projectAssetFrontier', () => {
  const manifestAsset = (asset_id: string, layer: NirmanaLayerId, depends_on?: string[]) => ({ asset_id, layer, depends_on })

  it('honors a linear dependency chain: only the asset whose sole ancestor is frozen is eligible', () => {
    const manifestAssets = [
      manifestAsset('a', 'L0'),
      manifestAsset('b', 'L0', ['a']),
      manifestAsset('c', 'L0', ['b']),
    ]
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(['a']),
      decidedAssetIds: new Set(['a', 'b', 'c']),
    })
    expect(frontier.L0).toEqual(['b'])
  })

  it('requires every branch of a diamond dependency to be frozen', () => {
    const manifestAssets = [
      manifestAsset('a', 'L0'),
      manifestAsset('b', 'L0', ['a']),
      manifestAsset('c', 'L0', ['a']),
      manifestAsset('d', 'L0', ['b', 'c']),
    ]
    const decidedAssetIds = new Set(['a', 'b', 'c', 'd'])
    const partial = projectAssetFrontier({ manifestAssets, frozenAssetIds: new Set(['a', 'b']), decidedAssetIds })
    expect(partial.L0).toEqual(['c'])
    const complete = projectAssetFrontier({ manifestAssets, frozenAssetIds: new Set(['a', 'b', 'c']), decidedAssetIds })
    expect(complete.L0).toEqual(['d'])
  })

  it('excludes an asset that has not been decided even when its ancestors are frozen', () => {
    const manifestAssets = [manifestAsset('a', 'L0'), manifestAsset('b', 'L0', ['a'])]
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(['a']),
      decidedAssetIds: new Set(['a']),
    })
    expect(frontier.L0 ?? []).not.toContain('b')
  })

  it('excludes an asset that is already frozen', () => {
    const manifestAssets = [manifestAsset('a', 'L0'), manifestAsset('b', 'L0', ['a'])]
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(['a', 'b']),
      decidedAssetIds: new Set(['a', 'b']),
    })
    expect(frontier.L0 ?? []).not.toContain('b')
  })

  it('excludes an asset whose ancestor is decided but not yet frozen', () => {
    const manifestAssets = [manifestAsset('a', 'L0'), manifestAsset('b', 'L0', ['a'])]
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(),
      decidedAssetIds: new Set(['a', 'b']),
    })
    expect(frontier.L0 ?? []).not.toContain('b')
  })

  it('honors a cross-layer ancestor: an L3 asset whose only ancestor is a frozen L0 asset is eligible', () => {
    const manifestAssets = [
      manifestAsset('root', 'L0'),
      manifestAsset('mid_l1', 'L1'),
      manifestAsset('mid_l2', 'L2'),
      manifestAsset('leaf', 'L3', ['root']),
    ]
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(['root']),
      decidedAssetIds: new Set(['root', 'mid_l1', 'mid_l2', 'leaf']),
    })
    expect(frontier.L3).toEqual(['leaf'])
  })

  it('returns deterministic sorted ids per layer', () => {
    const manifestAssets = [
      manifestAsset('zeta', 'L0'),
      manifestAsset('alpha', 'L0'),
    ]
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(),
      decidedAssetIds: new Set(['zeta', 'alpha']),
    })
    expect(frontier.L0).toEqual(['alpha', 'zeta'])
  })

  it('excludes an asset with a dangling depends_on reference (id not in manifestAssets) instead of crashing', () => {
    const manifestAssets = [manifestAsset('orphan', 'L0', ['ghost'])]
    expect(() => projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(),
      decidedAssetIds: new Set(['orphan']),
    })).not.toThrow()
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(),
      decidedAssetIds: new Set(['orphan']),
    })
    expect(frontier.L0 ?? []).not.toContain('orphan')
  })

  it('excludes a self-referential depends_on asset instead of looping forever', () => {
    const manifestAssets = [manifestAsset('loop', 'L0', ['loop'])]
    expect(() => projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(),
      decidedAssetIds: new Set(['loop']),
    })).not.toThrow()
    const frontier = projectAssetFrontier({
      manifestAssets,
      frozenAssetIds: new Set(),
      decidedAssetIds: new Set(['loop']),
    })
    expect(frontier.L0 ?? []).not.toContain('loop')
  })
})

describe('deriveLayerActivityState', () => {
  it('is unknown when assetsTotal is null', () => {
    expect(deriveLayerActivityState({ assetsTotal: null, frozen: 0, milestonesEarned: 0 })).toBe('unknown')
  })

  it('is completed when frozen equals assetsTotal', () => {
    expect(deriveLayerActivityState({ assetsTotal: 5, frozen: 5, milestonesEarned: 30 })).toBe('completed')
  })

  it('is active when milestones have been earned but the layer is not fully frozen', () => {
    expect(deriveLayerActivityState({ assetsTotal: 5, frozen: 2, milestonesEarned: 4 })).toBe('active')
  })

  it('is pending when nothing has been earned yet', () => {
    expect(deriveLayerActivityState({ assetsTotal: 5, frozen: 0, milestonesEarned: 0 })).toBe('pending')
  })

  it('is pending, never a vacuously-true completed, when assetsTotal is a real zero', () => {
    // frozen === assetsTotal (0 === 0) would otherwise read 'completed' with zero evidence
    // that anything was ever actually elevated — the exact §N.8 vacuous-truth defect class.
    expect(deriveLayerActivityState({ assetsTotal: 0, frozen: 0, milestonesEarned: 0 })).toBe('pending')
  })
})

describe('projectProgrammePositionV21', () => {
  it('reports overall percent and frozen/total counts', () => {
    const position = projectProgrammePositionV21({
      overall: { earned: 100, required: 294, percent: 34 },
      frozenTotal: 29,
      assetsTotal: 128,
    })
    expect(position).toBe('34% · 29/128 frozen')
  })

  it('renders an honest unknown marker, not a fabricated 0, when assetsTotal is null but percent is not', () => {
    const position = projectProgrammePositionV21({
      overall: { earned: 100, required: 294, percent: 34 },
      frozenTotal: 29,
      assetsTotal: null,
    })
    expect(position).not.toContain('/0 frozen')
    expect(position).toBe('34% · 29/— frozen')
  })

  it('reports execution not yet evidenced when percent is null', () => {
    const position = projectProgrammePositionV21({
      overall: { earned: 0, required: 0, percent: null },
      frozenTotal: 0,
      assetsTotal: 128,
    })
    expect(position).toBe('Execution not yet evidenced')
  })
})
