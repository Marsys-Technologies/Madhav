import type { NirmanaElevationManifest } from './definitions'
import type { NirmanaCampaignStage, NirmanaElevationSnapshotV2 } from './types'
import { NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from './vocab'

export interface CampaignEvent {
  campaign_id: string
  definition_revision: string
  event_type: string
  entity_type: string
  entity_id: string
  layer: string | null
  evidence_payload: unknown
  observed_at: string
  recorded_at: string
}

export type NirmanaLayerId = NirmanaElevationSnapshotV2['layers'][number]['layer_id']
export type NirmanaStageId = (typeof NIRMANA_STAGE_IDS)[number]
type ManifestAsset = NirmanaElevationManifest['assets'][number]
type Milestone = NirmanaElevationSnapshotV2['assets'][number]['milestones'][number]

export interface AssetMilestoneProjection {
  milestones: NirmanaElevationSnapshotV2['assets'][number]['milestones']
  milestones_earned: number | null
  milestones_required: number | null
  current_action: string | null
  next_action: string | null
  inherited_from_asset_id: string | null
}

const STAGE_KINDS: NirmanaCampaignStage['kind'][] = [
  'bootstrap', 'census', 'plan', 'denominator', 'foundation',
  'layer', 'layer', 'layer', 'layer', 'layer', 'layer', 'closing', 'complete',
]

const STAGE_GATES = [
  'Campaign charter accepted',
  'Registry census reconciled',
  'Campaign plan frozen',
  'Campaign denominator frozen',
  'Foundation lanes accepted',
  'L0 assets frozen',
  'L1 assets frozen',
  'L2 assets frozen',
  'L3 assets frozen',
  'L4 assets frozen',
  'L5 assets frozen',
  'Campaign close evidence accepted',
  'All campaign stages closed',
] as const

const FOUNDATION_LANES = [
  ['A', 'Asset and DAG census'],
  ['B', 'Run and progress truth'],
  ['C', 'Hash and invalidation'],
  ['D', 'Tracker and release'],
  ['E', 'Evidence control'],
] as const

const LAYER_IDS = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5'] as const
const SHA256 = /^[a-f0-9]{64}$/

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function validIso(value: string): boolean {
  return !Number.isNaN(Date.parse(value))
}

function eventTime(event: CampaignEvent): number {
  return Date.parse(event.recorded_at)
}

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

function eventTieBreaker(event: CampaignEvent): string {
  return [event.campaign_id, event.definition_revision, event.event_type, event.entity_type,
    event.entity_id, event.layer ?? '', stableJson(event.evidence_payload)].join('\0')
}

function compareEvents(left: CampaignEvent, right: CampaignEvent): number {
  return eventTime(left) - eventTime(right)
    || Date.parse(left.observed_at) - Date.parse(right.observed_at)
    || eventTieBreaker(left).localeCompare(eventTieBreaker(right))
}

function acceptedAt(event: CampaignEvent | undefined): string | null {
  return event && validIso(event.observed_at) ? new Date(event.observed_at).toISOString() : null
}

/** Projection inputs are one accepted definition cohort; mixed rows never combine across revisions. */
function oneDefinitionCohort(events: CampaignEvent[]): CampaignEvent[] {
  const first = events.find((event) => event.campaign_id.length > 0 && event.definition_revision.length > 0)
  if (!first) return []
  return events.filter((event) => event.campaign_id === first.campaign_id
    && event.definition_revision === first.definition_revision
    && validIso(event.observed_at)
    && validIso(event.recorded_at))
}

function latest(events: CampaignEvent[]): CampaignEvent | undefined {
  return [...events].sort((left, right) => compareEvents(right, left))[0]
}

function isStageId(value: unknown): value is NonNullable<NirmanaStageId> {
  return typeof value === 'string' && (NIRMANA_STAGE_IDS as readonly string[]).includes(value)
}

interface StageTransition {
  event: CampaignEvent
  from: NonNullable<NirmanaStageId>
  to: NonNullable<NirmanaStageId>
  prerequisitesSha256: string
}

function stageTransition(event: CampaignEvent): StageTransition | null {
  if (event.event_type !== 'stage_transition_accepted'
    || event.entity_type !== 'campaign_stage'
    || event.layer !== null
    || !isRecord(event.evidence_payload)) return null
  const from = event.evidence_payload.from_stage
  const to = event.evidence_payload.to_stage
  const prerequisitesSha256 = event.evidence_payload.prerequisites_sha256
  if (!isStageId(from) || !isStageId(to)
    || event.entity_id !== to
    || typeof prerequisitesSha256 !== 'string'
    || !SHA256.test(prerequisitesSha256)) return null
  return { event, from, to, prerequisitesSha256 }
}

function laneReceipt(event: CampaignEvent): boolean {
  return event.event_type === 'foundation_lane_accepted'
    && event.entity_type === 'foundation_lane'
    && event.layer === null
    && FOUNDATION_LANES.some(([laneId]) => laneId === event.entity_id)
    && isRecord(event.evidence_payload)
    && typeof event.evidence_payload.acceptance_sha256 === 'string'
    && SHA256.test(event.evidence_payload.acceptance_sha256)
}

export function projectCampaignStages(input: {
  definitionStatus: 'reconciling' | 'frozen' | 'superseded'
  events: CampaignEvent[]
  layers: Array<{ layer_id: NirmanaLayerId; state: string; assets_total: number | null; frozen: number }>
}): { current_stage: NirmanaStageId | null; stages: NirmanaCampaignStage[]; contradictions: string[] } {
  const events = oneDefinitionCohort(input.events)
  const transitions = events.map(stageTransition).filter((value): value is StageTransition => value !== null)
    .sort((left, right) => compareEvents(left.event, right.event))
  const currentTransition = transitions.at(-1)
  const current_stage = currentTransition?.to ?? null
  const currentIndex = current_stage === null ? -1 : NIRMANA_STAGE_IDS.indexOf(current_stage)
  const contradictions: string[] = []
  let previous: StageTransition | null = null

  for (const transition of transitions) {
    const fromIndex = NIRMANA_STAGE_IDS.indexOf(transition.from)
    const toIndex = NIRMANA_STAGE_IDS.indexOf(transition.to)
    const isDuplicate = previous?.from === transition.from && previous.to === transition.to
    if (toIndex !== fromIndex + 1) {
      contradictions.push(`Contradictory stage transition ${transition.from} -> ${transition.to}: stages must advance exactly once in canonical order.`)
    } else if (previous && !isDuplicate && transition.from !== previous.to) {
      contradictions.push(`Contradictory stage transition ${transition.from} -> ${transition.to}: prior accepted stage was ${previous.to}.`)
    } else if (isDuplicate && previous?.prerequisitesSha256 !== transition.prerequisitesSha256) {
      contradictions.push(`Contradictory stage transition ${transition.from} -> ${transition.to}: prerequisite digests differ.`)
    }
    previous = transition
  }

  const completedAt = new Map<NonNullable<NirmanaStageId>, string | null>()
  for (const transition of transitions) {
    const fromIndex = NIRMANA_STAGE_IDS.indexOf(transition.from)
    const toIndex = NIRMANA_STAGE_IDS.indexOf(transition.to)
    const completionRequiresProjectedEvidence = transition.from === 'F0_FOUNDATION'
      || LAYER_IDS.includes(transition.from as NirmanaLayerId)
    if (toIndex === fromIndex + 1 && !completionRequiresProjectedEvidence) {
      completedAt.set(transition.from, acceptedAt(transition.event))
    }
  }
  if (input.definitionStatus === 'frozen') completedAt.set('DENOMINATOR_FROZEN', null)

  const acceptedLaneById = new Map<string, CampaignEvent>()
  for (const laneId of FOUNDATION_LANES.map(([id]) => id)) {
    const receipt = latest(events.filter((event) => event.entity_id === laneId && laneReceipt(event)))
    if (receipt) acceptedLaneById.set(laneId, receipt)
  }
  const foundation_lanes: NonNullable<NirmanaCampaignStage['foundation_lanes']> = FOUNDATION_LANES.map(([lane_id, name]) => {
    const receipt = acceptedLaneById.get(lane_id)
    return {
      lane_id,
      name,
      state: receipt ? 'completed' : 'unknown',
      completed_at: acceptedAt(receipt),
      blocked_reason: null,
    }
  })
  if (input.definitionStatus === 'frozen' && acceptedLaneById.size === FOUNDATION_LANES.length) {
    completedAt.set('F0_FOUNDATION', acceptedAt(latest([...acceptedLaneById.values()])))
  }

  let priorStageComplete = completedAt.has('F0_FOUNDATION')
  for (const layerId of LAYER_IDS) {
    const layer = input.layers.find(({ layer_id }) => layer_id === layerId)
    const layerComplete = priorStageComplete
      && layer?.assets_total !== null
      && layer?.assets_total !== undefined
      && layer.frozen === layer.assets_total
    if (layerComplete) {
      const latestFreeze = latest(events.filter((event) => event.event_type === 'asset_frozen' && event.entity_type === 'asset' && event.layer === layerId))
      completedAt.set(layerId, acceptedAt(latestFreeze))
    }
    priorStageComplete = layerComplete
  }

  for (const transition of transitions) {
    const fromIndex = NIRMANA_STAGE_IDS.indexOf(transition.from)
    const toIndex = NIRMANA_STAGE_IDS.indexOf(transition.to)
    const requiresProjectedEvidence = transition.from === 'F0_FOUNDATION'
      || LAYER_IDS.includes(transition.from as NirmanaLayerId)
    if (toIndex === fromIndex + 1 && requiresProjectedEvidence && !completedAt.has(transition.from)) {
      contradictions.push(`Contradictory stage transition ${transition.from} -> ${transition.to}: ${transition.from} completion evidence is incomplete.`)
    }
  }

  const stages = NIRMANA_STAGE_IDS.map((stage_id, order): NirmanaCampaignStage => {
    const layer = LAYER_IDS.includes(stage_id as NirmanaLayerId)
      ? input.layers.find(({ layer_id }) => layer_id === stage_id) : undefined
    const isCompleted = completedAt.has(stage_id)
    let state: NirmanaCampaignStage['state'] = isCompleted
      ? 'completed'
      : currentIndex === order ? 'active'
        : currentIndex >= 0 && order > currentIndex ? 'locked' : 'unknown'
    if (input.definitionStatus === 'superseded' && state === 'active') state = 'paused'
    const blocked = contradictions.length > 0 && stage_id === current_stage
    if (blocked) state = 'blocked'
    return {
      stage_id,
      order,
      kind: STAGE_KINDS[order],
      state,
      required_gate: STAGE_GATES[order],
      completed_at: isCompleted ? completedAt.get(stage_id) ?? null : null,
      blocked_reason: blocked ? contradictions.join(' ') : null,
      earned: stage_id === 'F0_FOUNDATION' ? acceptedLaneById.size
        : layer ? layer.frozen : null,
      required: stage_id === 'F0_FOUNDATION' ? FOUNDATION_LANES.length
        : layer ? layer.assets_total : null,
      foundation_lanes: stage_id === 'F0_FOUNDATION' ? foundation_lanes : null,
    }
  })

  return { current_stage, stages, contradictions }
}

const BUILD_EVENT_BY_MILESTONE = {
  analysed: 'asset_analysis_accepted',
  decision_accepted: 'optimization_verdict_accepted',
  built_or_dispositioned: 'implementation_accepted',
  deployed_and_executed: 'accepted_rebuild_observed',
  verified: 'integrity_verified',
  frozen: 'asset_frozen',
} as const

const DISPOSITION_EVENTS = {
  static_acceptance: 'static_accepted',
  source_acceptance: 'source_accepted',
  empty_acceptance: 'empty_accepted',
  retired_with_disposition: 'retired_with_disposition',
} as const

const ACTIONS: Record<(typeof NIRMANA_MILESTONE_IDS)[number], string> = {
  analysed: 'Accept asset analysis',
  decision_accepted: 'Accept optimization decision',
  built_or_dispositioned: 'Accept implementation or disposition',
  deployed_and_executed: 'Accept deployed execution',
  verified: 'Verify asset integrity',
  frozen: 'Freeze asset evidence',
}

function latestAssetEvent(events: CampaignEvent[], asset: ManifestAsset, eventType: string): CampaignEvent | undefined {
  return latest(events.filter((event) => event.event_type === eventType
    && event.entity_type === 'asset'
    && event.entity_id === asset.asset_id
    && event.layer === asset.layer))
}

export function projectAssetMilestones(input: {
  asset: ManifestAsset
  events: CampaignEvent[]
  activeRunState: string | null
  producerAsset: ManifestAsset | null
}): AssetMilestoneProjection {
  const events = oneDefinitionCohort(input.events)
  const obligation = input.asset.execution_obligation ?? 'unresolved'
  let validProducer: ManifestAsset | null = null
  if (obligation === 'producer_covered'
    && input.asset.producer_id
    && input.producerAsset?.asset_id === input.asset.producer_id
    && input.producerAsset.execution_obligation === 'build'
    && input.producerAsset.covered_asset_ids?.includes(input.asset.asset_id) === true) {
    validProducer = input.producerAsset
  }

  if (obligation === 'unresolved') {
    return {
      milestones: NIRMANA_MILESTONE_IDS.map((milestone_id) => ({ milestone_id, state: 'pending', event_type: null, accepted_at: null })),
      milestones_earned: null,
      milestones_required: null,
      current_action: null,
      next_action: null,
      inherited_from_asset_id: null,
    }
  }

  const acceptedEvents = new Map<(typeof NIRMANA_MILESTONE_IDS)[number], CampaignEvent>()
  const notApplicable = new Set<(typeof NIRMANA_MILESTONE_IDS)[number]>()
  const analysis = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.analysed)
  const decision = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.decision_accepted)
  const integrity = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.verified)
  const frozen = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.frozen)
  if (analysis) acceptedEvents.set('analysed', analysis)
  if (decision) acceptedEvents.set('decision_accepted', decision)
  if (integrity) acceptedEvents.set('verified', integrity)
  if (frozen) acceptedEvents.set('frozen', frozen)

  if (obligation === 'build') {
    const changeRequired = isRecord(decision?.evidence_payload) ? decision.evidence_payload.change_required : undefined
    if (changeRequired === false) notApplicable.add('built_or_dispositioned')
    else {
      const implementation = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.built_or_dispositioned)
      if (implementation) acceptedEvents.set('built_or_dispositioned', implementation)
    }
    const execution = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.deployed_and_executed)
    if (execution) acceptedEvents.set('deployed_and_executed', execution)
  } else if (obligation === 'probe') {
    const implementation = latestAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.built_or_dispositioned)
    if (implementation) acceptedEvents.set('built_or_dispositioned', implementation)
    else notApplicable.add('built_or_dispositioned')
    const execution = latestAssetEvent(events, input.asset, 'probe_accepted')
    if (execution) acceptedEvents.set('deployed_and_executed', execution)
  } else if (obligation === 'producer_covered') {
    const coverage = latestAssetEvent(events, input.asset, 'producer_covered')
    if (coverage) acceptedEvents.set('built_or_dispositioned', coverage)
    if (coverage && validProducer) {
      const producerExecution = latestAssetEvent(events, validProducer, BUILD_EVENT_BY_MILESTONE.deployed_and_executed)
      if (producerExecution) acceptedEvents.set('deployed_and_executed', producerExecution)
    }
  } else {
    const dispositionEventType = DISPOSITION_EVENTS[obligation as keyof typeof DISPOSITION_EVENTS]
    const disposition = dispositionEventType ? latestAssetEvent(events, input.asset, dispositionEventType) : undefined
    if (disposition) acceptedEvents.set('built_or_dispositioned', disposition)
    notApplicable.add('deployed_and_executed')
  }

  let milestones: Milestone[] = NIRMANA_MILESTONE_IDS.map((milestone_id) => {
    const receipt = acceptedEvents.get(milestone_id)
    return {
      milestone_id,
      state: notApplicable.has(milestone_id) ? 'not_applicable' : receipt ? 'earned' : 'pending',
      event_type: receipt?.event_type ?? null,
      accepted_at: acceptedAt(receipt),
    }
  })
  const currentIndex = milestones.findIndex(({ state }) => state === 'pending')
  if (currentIndex >= 0) {
    milestones = milestones.map((milestone, index) => index === currentIndex ? { ...milestone, state: 'current' } : milestone)
  }
  const nextIndex = currentIndex < 0
    ? -1
    : milestones.findIndex((milestone, index) => index > currentIndex && milestone.state === 'pending')
  const milestones_earned = milestones.filter(({ state }) => state === 'earned').length
  const milestones_required = milestones.filter(({ state }) => state !== 'not_applicable').length

  return {
    milestones,
    milestones_earned,
    milestones_required,
    current_action: currentIndex < 0 ? null
      : input.activeRunState ? `Active run: ${input.activeRunState}` : ACTIONS[milestones[currentIndex].milestone_id],
    next_action: nextIndex < 0 ? null : ACTIONS[milestones[nextIndex].milestone_id],
    inherited_from_asset_id: validProducer?.asset_id ?? null,
  }
}

export function deriveEligibleNextAssetIds(input: {
  manifestAssets: ManifestAsset[]
  frozenAssetIds: Set<string>
  blockedAssetIds: Set<string>
  currentLayer: NirmanaLayerId | null
  currentWave: number | null
}): string[] {
  if (input.currentLayer === null || input.currentWave === null) return []
  const currentLayerRank = LAYER_IDS.indexOf(input.currentLayer)
  if (currentLayerRank < 0) return []
  const byId = new Map(input.manifestAssets.map((asset) => [asset.asset_id, asset]))
  const validlyInherited = (asset: ManifestAsset): boolean => {
    if (asset.execution_obligation !== 'producer_covered' || !asset.producer_id) return false
    const producer = byId.get(asset.producer_id)
    return producer?.execution_obligation === 'build'
      && producer.covered_asset_ids?.includes(asset.asset_id) === true
      && !input.blockedAssetIds.has(producer.asset_id)
      && input.frozenAssetIds.has(producer.asset_id)
  }
  const satisfied = (asset: ManifestAsset): boolean => asset.execution_obligation !== undefined
    && asset.execution_obligation !== 'unresolved'
    && !input.blockedAssetIds.has(asset.asset_id)
    && (input.frozenAssetIds.has(asset.asset_id) || validlyInherited(asset))

  const lowerLayersComplete = input.manifestAssets
    .filter((asset) => LAYER_IDS.indexOf(asset.layer) < currentLayerRank)
    .every(satisfied)
  if (!lowerLayersComplete) return []

  const layerAssets = input.manifestAssets.filter((asset) => asset.layer === input.currentLayer)
  if (layerAssets.some((asset) => asset.wave_index === undefined)) return []
  const unfinishedWaves = layerAssets.filter((asset) => !satisfied(asset)).map((asset) => asset.wave_index!)
  if (unfinishedWaves.length === 0) return []
  const nextUnfinishedWave = Math.min(...unfinishedWaves)
  if (input.currentWave !== nextUnfinishedWave) return []

  return layerAssets.filter((asset) => asset.wave_index === nextUnfinishedWave
    && !satisfied(asset)
    && asset.execution_obligation !== undefined
    && asset.execution_obligation !== 'unresolved'
    && !input.blockedAssetIds.has(asset.asset_id)
    && (asset.depends_on ?? []).every((dependencyId) => {
      const dependency = byId.get(dependencyId)
      if (!dependency) return false
      const dependencyRank = LAYER_IDS.indexOf(dependency.layer)
      return dependencyRank >= 0 && dependencyRank <= currentLayerRank && satisfied(dependency)
    }))
    .map((asset) => asset.asset_id)
    .sort((left, right) => left.localeCompare(right))
}
