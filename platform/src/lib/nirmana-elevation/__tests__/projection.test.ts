import { describe, expect, it } from 'vitest'
import { canonicalNirmanaOptimizationVerdictDigest, type NirmanaElevationManifest } from '../definitions'
import {
  deriveEligibleNextAssetIds,
  projectAssetMilestones,
  projectCampaignStages,
  type CampaignEvent,
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
  return {
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
    if (eventType === 'accepted_rebuild_observed') return { output_digest: 'd'.repeat(64), output_digest_spec_sha256: 'e'.repeat(64) }
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
      ? 'git_commit' : 'test'
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
    const coveredEvents = assetEvents(covered, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered', 'integrity_verified', 'asset_frozen',
    ]).map((receipt) => receipt.event_type === 'producer_covered'
      ? { ...receipt, source_ref: 'build_run:11111111-1111-4111-8111-111111111111' }
      : receipt)
    const independentCoveredBuild = event({
      event_type: 'accepted_rebuild_observed', entity_id: covered.asset_id, layer: covered.layer,
      observed_at: '2026-08-26T11:00:00.000Z', recorded_at: '2026-08-26T11:00:00.000Z',
    })
    const producerBuild = event({
      event_type: 'accepted_rebuild_observed', entity_id: producer.asset_id, layer: producer.layer,
      observed_at: '2026-08-26T11:01:00.000Z', recorded_at: '2026-08-26T11:01:00.000Z',
    }) as CampaignEvent & { source_ref: string }
    producerBuild.source_ref = 'build_run:11111111-1111-4111-8111-111111111111'

    const withoutProducer = projectMilestones({
      asset: covered, events: [...coveredEvents, independentCoveredBuild], activeRunState: null, producerAsset: producer,
    })
    const inherited = projectMilestones({
      asset: covered, events: [...coveredEvents, independentCoveredBuild, producerBuild], activeRunState: null, producerAsset: producer,
    })

    expect(withoutProducer.milestones[3].state).toBe('current')
    expect(inherited.milestones[3]).toMatchObject({ state: 'earned', event_type: 'accepted_rebuild_observed', accepted_at: producerBuild.observed_at })
    expect(inherited.inherited_from_asset_id).toBe(producer.asset_id)
  })

  it('inherits producer execution only when coverage names the exact accepted producer run', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({
      asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: producer.asset_id,
      depends_on: [producer.asset_id],
    })
    const coverage = {
      ...assetEvents(covered, ['producer_covered'])[0],
      source_ref: 'build_run:11111111-1111-4111-8111-111111111111',
    }
    const producerBuild = {
      ...assetEvents(producer, ['accepted_rebuild_observed'])[0],
      source_ref: 'build_run:22222222-2222-4222-8222-222222222222',
    }

    const result = projectMilestones({
      asset: covered,
      events: [coverage, producerBuild],
      activeRunState: null,
      producerAsset: producer,
    })

    expect(result.milestones[2]).toMatchObject({ milestone_id: 'built_or_dispositioned', state: 'earned' })
    expect(result.milestones[3]).toMatchObject({ milestone_id: 'deployed_and_executed', state: 'pending', event_type: null })
    expect(result.inherited_from_asset_id).toBeNull()
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
