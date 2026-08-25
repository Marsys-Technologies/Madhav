import { describe, expect, it } from 'vitest'
import type { NirmanaElevationManifest } from '../definitions'
import {
  deriveEligibleNextAssetIds,
  projectAssetMilestones,
  projectCampaignStages,
  type CampaignEvent,
} from '../projection'

type ManifestAsset = NirmanaElevationManifest['assets'][number]

const observedAt = '2026-08-26T09:00:00.000Z'

function event(overrides: Partial<CampaignEvent> = {}): CampaignEvent {
  return {
    campaign_id: 'nirmana-elevation',
    definition_revision: 'v2',
    event_type: 'asset_analysis_accepted',
    entity_type: 'asset',
    entity_id: 'bg_alpha',
    layer: 'L0',
    evidence_payload: {},
    observed_at: observedAt,
    recorded_at: observedAt,
    ...overrides,
  }
}

function transition(from_stage: string, to_stage: string, recorded_at: string): CampaignEvent {
  return event({
    event_type: 'stage_transition_accepted',
    entity_type: 'campaign_stage',
    entity_id: to_stage,
    layer: null,
    evidence_payload: { from_stage, to_stage, prerequisites_sha256: 'a'.repeat(64) },
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
    evidence_payload: { acceptance_sha256: 'b'.repeat(64) },
    observed_at: timestamp,
    recorded_at: timestamp,
  })
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
  return eventTypes.map((event_type, index) => event({
    event_type,
    entity_id: asset.asset_id,
    layer: asset.layer,
    observed_at: `2026-08-26T10:${String(index).padStart(2, '0')}:00.000Z`,
    recorded_at: `2026-08-26T10:${String(index).padStart(2, '0')}:00.000Z`,
    ...overrides,
  }))
}

describe('projectCampaignStages', () => {
  it('uses the latest accepted stage transition instead of guessing from incomplete stages', () => {
    const result = projectCampaignStages({
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
    const result = projectCampaignStages({
      definitionStatus: 'frozen',
      events: [event({ event_type: 'stage_transition_accepted', entity_type: 'campaign_stage', entity_id: 'L0', evidence_payload: {} })],
      layers: emptyLayers,
    })

    expect(result.current_stage).toBeNull()
    expect(result.stages.some(({ state }) => state === 'active')).toBe(false)
  })

  it('does not mark F0 complete from a frozen denominator alone', () => {
    const result = projectCampaignStages({ definitionStatus: 'frozen', events: [], layers: emptyLayers })
    const foundation = result.stages.find(({ stage_id }) => stage_id === 'F0_FOUNDATION')

    expect(foundation).toMatchObject({ state: 'unknown', earned: 0, required: 5 })
    expect(foundation?.foundation_lanes?.every(({ state }) => state === 'unknown')).toBe(true)
  })

  it('projects all five F0 lanes from foundation-lane receipts and leaves missing lanes unknown', () => {
    const complete = projectCampaignStages({
      definitionStatus: 'frozen',
      events: ['A', 'B', 'C', 'D', 'E'].map((laneId) => foundationLane(laneId)),
      layers: emptyLayers,
    })
    const incomplete = projectCampaignStages({
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

  it('marks a layer complete only when every in-layer asset is frozen and prior layers are complete', () => {
    const events = [
      ...['A', 'B', 'C', 'D', 'E'].map((laneId) => foundationLane(laneId)),
      transition('F0_FOUNDATION', 'L0', '2026-08-26T09:10:00.000Z'),
      transition('L0', 'L1', '2026-08-26T09:11:00.000Z'),
    ]
    const completed = projectCampaignStages({
      definitionStatus: 'frozen',
      events,
      layers: emptyLayers.map((layer) => layer.layer_id === 'L0'
        ? { ...layer, frozen: 2 }
        : layer.layer_id === 'L1' ? { ...layer, frozen: 1 } : layer),
    })
    const priorIncomplete = projectCampaignStages({
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
    const result = projectCampaignStages({
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
    events[1].evidence_payload = { change_required: true }

    const result = projectAssetMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones.map(({ state }) => state)).toEqual(Array(6).fill('earned'))
    expect(result).toMatchObject({ milestones_earned: 6, milestones_required: 6, current_action: null, next_action: null })
  })

  it('makes the build implementation milestone N/A when the accepted decision requires no change', () => {
    const asset = manifestAsset()
    const events = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ])
    events[1].evidence_payload = { change_required: false }

    const result = projectAssetMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones[2]).toMatchObject({ milestone_id: 'built_or_dispositioned', state: 'not_applicable', event_type: null, accepted_at: null })
    expect(result).toMatchObject({ milestones_earned: 5, milestones_required: 5 })
  })

  it('makes probe implementation N/A unless a change receipt exists', () => {
    const asset = manifestAsset({ execution_obligation: 'probe' })
    const baseEvents = assetEvents(asset, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'probe_accepted', 'integrity_verified', 'asset_frozen',
    ])

    const unchanged = projectAssetMilestones({ asset, events: baseEvents, activeRunState: null, producerAsset: null })
    const changed = projectAssetMilestones({
      asset,
      events: [...baseEvents, ...assetEvents(asset, ['implementation_accepted'], { recorded_at: '2026-08-26T11:00:00.000Z', observed_at: '2026-08-26T11:00:00.000Z' })],
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

    const result = projectAssetMilestones({ asset, events, activeRunState: null, producerAsset: null })

    expect(result.milestones[2]).toMatchObject({ state: 'earned', event_type: dispositionEvent })
    expect(result.milestones[3].state).toBe('not_applicable')
    expect(result).toMatchObject({ milestones_earned: 5, milestones_required: 5 })
  })

  it('inherits producer execution without claiming an independent covered-asset build', () => {
    const producer = manifestAsset({ asset_id: 'bg_producer', covered_asset_ids: ['bg_covered'] })
    const covered = manifestAsset({ asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: producer.asset_id, depends_on: [producer.asset_id] })
    const coveredEvents = assetEvents(covered, [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered', 'integrity_verified', 'asset_frozen',
    ])
    const independentCoveredBuild = event({
      event_type: 'accepted_rebuild_observed', entity_id: covered.asset_id, layer: covered.layer,
      observed_at: '2026-08-26T11:00:00.000Z', recorded_at: '2026-08-26T11:00:00.000Z',
    })
    const producerBuild = event({
      event_type: 'accepted_rebuild_observed', entity_id: producer.asset_id, layer: producer.layer,
      observed_at: '2026-08-26T11:01:00.000Z', recorded_at: '2026-08-26T11:01:00.000Z',
    })

    const withoutProducer = projectAssetMilestones({
      asset: covered, events: [...coveredEvents, independentCoveredBuild], activeRunState: null, producerAsset: producer,
    })
    const inherited = projectAssetMilestones({
      asset: covered, events: [...coveredEvents, independentCoveredBuild, producerBuild], activeRunState: null, producerAsset: producer,
    })

    expect(withoutProducer.milestones[3].state).toBe('current')
    expect(inherited.milestones[3]).toMatchObject({ state: 'earned', event_type: 'accepted_rebuild_observed', accepted_at: producerBuild.observed_at })
    expect(inherited.inherited_from_asset_id).toBe(producer.asset_id)
  })

  it('withholds determinate progress for an unresolved obligation', () => {
    const result = projectAssetMilestones({
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

  it('does not combine a present event from another definition revision', () => {
    const asset = manifestAsset()
    const events = [
      ...assetEvents(asset, ['asset_analysis_accepted']),
      ...assetEvents(asset, ['optimization_verdict_accepted', 'implementation_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen'], { definition_revision: 'v1' }),
    ]

    const result = projectAssetMilestones({ asset, events, activeRunState: null, producerAsset: null })

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
})
