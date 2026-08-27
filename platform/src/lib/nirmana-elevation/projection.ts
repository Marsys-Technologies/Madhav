import {
  NirmanaAssetAnalysisEvidenceSchema,
  NirmanaFoundationLaneEvidenceSchema,
  NirmanaFreezeEvidenceSchema,
  NirmanaImplementationEvidenceSchema,
  NirmanaIntegrityEvidenceSchema,
  NirmanaNonBuildDispositionEvidenceSchema,
  NirmanaOptimizationVerdictEvidenceSchema,
  NirmanaProbeEvidenceSchema,
  canonicalNirmanaOptimizationVerdictDigest,
  type NirmanaElevationManifest,
} from './definitions'
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
  source_kind: string
  source_ref: string
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
const BUILD_RUN_SOURCE_REF = /^build_run:([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i

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

/** Selects only the caller-pinned active definition; array order can never choose authority. */
function definitionCohort(events: CampaignEvent[], campaignId: string, definitionRevision: string): CampaignEvent[] {
  return events.filter((event) => event.campaign_id === campaignId
    && event.definition_revision === definitionRevision
    && validIso(event.observed_at)
    && validIso(event.recorded_at))
}

function latest(events: CampaignEvent[]): CampaignEvent | undefined {
  return [...events].sort((left, right) => compareEvents(right, left))[0]
}

function isStageId(value: unknown): value is NonNullable<NirmanaStageId> {
  return typeof value === 'string' && (NIRMANA_STAGE_IDS as readonly string[]).includes(value)
}

export interface AcceptedCampaignStageTransition<TEvent extends CampaignEvent = CampaignEvent> {
  event: TEvent
  from: NirmanaStageId | null
  to: NonNullable<NirmanaStageId>
  prerequisitesSha256: string
}

export function parseCampaignStageTransition<TEvent extends CampaignEvent>(
  event: TEvent,
): AcceptedCampaignStageTransition<TEvent> | null {
  if (event.event_type !== 'stage_transition_accepted'
    || event.entity_type !== 'campaign_stage'
    || event.layer !== null
    || event.source_kind !== 'server_reconstructed'
    || event.source_ref !== 'nirmana-elevation:stage-spine'
    || !isRecord(event.evidence_payload)
    || !validIso(event.observed_at)
    || !validIso(event.recorded_at)) return null
  const from = event.evidence_payload.from_stage
  const to = event.evidence_payload.to_stage
  const manifestSha256 = event.evidence_payload.manifest_sha256
  if (!isStageId(to)
    || event.entity_id !== to
    || event.evidence_payload.schema_version !== 'nirmana-stage-transition-receipt/v1'
    || typeof manifestSha256 !== 'string'
    || !SHA256.test(manifestSha256)) return null
  if (from === null) {
    return to === 'BOOTSTRAP' ? { event, from, to, prerequisitesSha256: manifestSha256 } : null
  }
  if (!isStageId(from)) return null
  return { event, from, to, prerequisitesSha256: manifestSha256 }
}

function stageIndex(stage: NirmanaStageId | null): number {
  return stage === null ? -1 : NIRMANA_STAGE_IDS.indexOf(stage)
}

export function canonicalizeCampaignStageTransitions<TEvent extends CampaignEvent>(events: TEvent[]): {
  transitions: Array<AcceptedCampaignStageTransition<TEvent>>
  contradictions: string[]
  invalidEventCount: number
} {
  const parsed = events.flatMap((event) => {
    const transition = parseCampaignStageTransition(event)
    return transition === null ? [] : [transition]
  }).sort((left, right) => compareEvents(left.event, right.event))
  const byEdge = new Map<string, {
    transition: AcceptedCampaignStageTransition<TEvent>
    prerequisiteDigests: Set<string>
  }>()

  for (const transition of parsed) {
    const edgeKey = `${transition.from ?? 'null'}\0${transition.to}`
    const edge = byEdge.get(edgeKey)
    if (edge) {
      edge.prerequisiteDigests.add(transition.prerequisitesSha256)
    } else {
      byEdge.set(edgeKey, {
        transition,
        prerequisiteDigests: new Set([transition.prerequisitesSha256]),
      })
    }
  }

  const contradictions = [...byEdge.values()]
    .filter(({ prerequisiteDigests }) => prerequisiteDigests.size > 1)
    .map(({ transition }) => `Contradictory stage transition ${transition.from ?? 'null'} -> ${transition.to}: prerequisite digests differ.`)
  return {
    transitions: [...byEdge.values()].map(({ transition }) => transition),
    contradictions,
    invalidEventCount: events.length - parsed.length,
  }
}

function laneReceipt(event: CampaignEvent): boolean {
  if (event.event_type !== 'foundation_lane_accepted'
    || event.entity_type !== 'foundation_lane'
    || event.layer !== null
    || !FOUNDATION_LANES.some(([laneId]) => laneId === event.entity_id)
    || !isRecord(event.evidence_payload)
    || event.evidence_payload.schema_version !== 'nirmana-foundation-lane-receipt/v1'
    || event.evidence_payload.lane_id !== event.entity_id
    || event.source_kind !== 'server_reconstructed'
    || event.source_ref !== `nirmana-elevation:foundation-lane:${event.entity_id}`) return false
  const receipt = NirmanaFoundationLaneEvidenceSchema.safeParse(event.evidence_payload)
  return receipt.success && receipt.data.lane_id === event.entity_id
}

export function projectCampaignStages(input: {
  campaignId: string
  definitionRevision: string
  definitionStatus: 'reconciling' | 'frozen' | 'superseded'
  events: CampaignEvent[]
  layers: Array<{ layer_id: NirmanaLayerId; state: string; assets_total: number | null; frozen: number }>
}): { current_stage: NirmanaStageId | null; stages: NirmanaCampaignStage[]; contradictions: string[] } {
  const events = definitionCohort(input.events, input.campaignId, input.definitionRevision)
  const canonical = canonicalizeCampaignStageTransitions(
    events.filter((event) => event.event_type === 'stage_transition_accepted'),
  )
  const transitions = canonical.transitions
  const currentTransition = transitions.at(-1)
  const current_stage = currentTransition?.to ?? null
  const currentIndex = current_stage === null ? -1 : NIRMANA_STAGE_IDS.indexOf(current_stage)
  const contradictions = [...canonical.contradictions]
  let previous: AcceptedCampaignStageTransition | null = null

  for (const transition of transitions) {
    const fromIndex = stageIndex(transition.from)
    const toIndex = stageIndex(transition.to)
    if (toIndex !== fromIndex + 1) {
      contradictions.push(`Contradictory stage transition ${transition.from ?? 'null'} -> ${transition.to}: stages must advance exactly once in canonical order.`)
    } else if (previous && transition.from !== previous.to) {
      contradictions.push(`Contradictory stage transition ${transition.from ?? 'null'} -> ${transition.to}: prior accepted stage was ${previous.to}.`)
    }
    previous = transition
  }

  const completedAt = new Map<NonNullable<NirmanaStageId>, string | null>()
  for (const transition of transitions) {
    const fromIndex = stageIndex(transition.from)
    const toIndex = stageIndex(transition.to)
    const completionRequiresProjectedEvidence = transition.from === 'F0_FOUNDATION'
      || LAYER_IDS.includes(transition.from as NirmanaLayerId)
    if (transition.from !== null && toIndex === fromIndex + 1 && !completionRequiresProjectedEvidence) {
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
    const fromIndex = stageIndex(transition.from)
    const toIndex = stageIndex(transition.to)
    const requiresProjectedEvidence = transition.from === 'F0_FOUNDATION'
      || LAYER_IDS.includes(transition.from as NirmanaLayerId)
    if (transition.from !== null && toIndex === fromIndex + 1 && requiresProjectedEvidence && !completedAt.has(transition.from)) {
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

function after(event: CampaignEvent | undefined, predecessor: CampaignEvent | undefined): boolean {
  return event !== undefined && predecessor !== undefined && compareEvents(event, predecessor) > 0
}

function hasCurrentBinding(payload: unknown, analysis: CampaignEvent | undefined): boolean {
  const analysisPayload = NirmanaAssetAnalysisEvidenceSchema.safeParse(analysis?.evidence_payload)
  if (!analysisPayload.success || !isRecord(payload)) return false
  return payload.registry_fingerprint_sha256 === analysisPayload.data.registry_fingerprint_sha256
    && payload.analysis_digest === analysisPayload.data.analysis_digest
}

function latestTrustedAssetEvent(
  events: CampaignEvent[],
  asset: ManifestAsset,
  eventType: string,
  predicate: (event: CampaignEvent) => boolean,
): CampaignEvent | undefined {
  return latest(events.filter((event) => event.event_type === eventType
    && event.entity_type === 'asset'
    && event.entity_id === asset.asset_id
    && event.layer === asset.layer
    && predicate(event)))
}

export function projectAssetMilestones(input: {
  campaignId: string
  definitionRevision: string
  asset: ManifestAsset
  events: CampaignEvent[]
  activeRunState: string | null
  producerAsset: ManifestAsset | null
}): AssetMilestoneProjection {
  const events = definitionCohort(input.events, input.campaignId, input.definitionRevision)
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
  const analysis = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.analysed, (event) =>
    NirmanaAssetAnalysisEvidenceSchema.safeParse(event.evidence_payload).success
      && event.source_kind === 'git_commit' && /^git:[a-f0-9]{40}$/.test(event.source_ref)
      && (!input.asset.registry_fingerprint_sha256
        || (event.evidence_payload as { registry_fingerprint_sha256?: unknown }).registry_fingerprint_sha256 === input.asset.registry_fingerprint_sha256))
  const decision = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.decision_accepted, (event) => {
    const payload = NirmanaOptimizationVerdictEvidenceSchema.safeParse(event.evidence_payload)
    return payload.success && event.source_kind === 'git_commit' && /^git:[a-f0-9]{40}$/.test(event.source_ref)
      && hasCurrentBinding(payload.data, analysis) && after(event, analysis)
  })
  const integrity = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.verified, (event) =>
    NirmanaIntegrityEvidenceSchema.safeParse(event.evidence_payload).success && hasCurrentBinding(event.evidence_payload, analysis))
  const frozen = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.frozen, (event) =>
    NirmanaFreezeEvidenceSchema.safeParse(event.evidence_payload).success && hasCurrentBinding(event.evidence_payload, analysis))
  if (analysis) acceptedEvents.set('analysed', analysis)
  if (decision) acceptedEvents.set('decision_accepted', decision)

  if (obligation === 'build') {
    const decisionPayload = NirmanaOptimizationVerdictEvidenceSchema.safeParse(decision?.evidence_payload)
    const requiresChange = decisionPayload.success && ['optimize', 'correct', 'optimize_and_correct'].includes(decisionPayload.data.proposal.action)
    if (decisionPayload.success && !requiresChange) notApplicable.add('built_or_dispositioned')
    else {
      const implementation = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.built_or_dispositioned, (event) => {
        const payload = NirmanaImplementationEvidenceSchema.safeParse(event.evidence_payload)
        return payload.success && event.source_kind === 'git_commit' && /^git:[a-f0-9]{40}$/.test(event.source_ref)
          && hasCurrentBinding(payload.data, analysis)
          && payload.data.decision_digest === (decisionPayload.success ? canonicalNirmanaOptimizationVerdictDigest(decisionPayload.data) : '')
          && after(event, decision)
      })
      if (implementation) acceptedEvents.set('built_or_dispositioned', implementation)
    }
    const execution = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.deployed_and_executed, (event) =>
      isRecord(event.evidence_payload)
        && typeof event.evidence_payload.output_digest === 'string'
        && typeof event.evidence_payload.output_digest_spec_sha256 === 'string'
        && /^build_run:[0-9a-f-]{36}$/i.test(event.source_ref)
        && after(event, requiresChange ? acceptedEvents.get('built_or_dispositioned') : decision))
    if (execution) acceptedEvents.set('deployed_and_executed', execution)
  } else if (obligation === 'probe') {
    const decisionPayload = NirmanaOptimizationVerdictEvidenceSchema.safeParse(decision?.evidence_payload)
    const requiresChange = decisionPayload.success && ['optimize', 'correct', 'optimize_and_correct'].includes(decisionPayload.data.proposal.action)
    const implementation = latestTrustedAssetEvent(events, input.asset, BUILD_EVENT_BY_MILESTONE.built_or_dispositioned, (event) => {
      const payload = NirmanaImplementationEvidenceSchema.safeParse(event.evidence_payload)
      return payload.success && event.source_kind === 'git_commit' && /^git:[a-f0-9]{40}$/.test(event.source_ref)
        && hasCurrentBinding(payload.data, analysis)
        && payload.data.decision_digest === (decisionPayload.success ? canonicalNirmanaOptimizationVerdictDigest(decisionPayload.data) : '')
        && after(event, decision)
    })
    if (requiresChange && implementation) acceptedEvents.set('built_or_dispositioned', implementation)
    else if (!requiresChange && decisionPayload.success) notApplicable.add('built_or_dispositioned')
    const execution = latestTrustedAssetEvent(events, input.asset, 'probe_accepted', (event) =>
      NirmanaProbeEvidenceSchema.safeParse(event.evidence_payload).success
        && hasCurrentBinding(event.evidence_payload, analysis)
        && event.source_kind === 'server_reconstructed'
        && event.source_ref === `nirmana-elevation:health-probe:${input.asset.asset_id}`
        && after(event, requiresChange ? implementation : decision))
    if (execution) acceptedEvents.set('deployed_and_executed', execution)
  } else if (obligation === 'producer_covered') {
    const coverage = latestAssetEvent(events, input.asset, 'producer_covered')
    const coverageRunId = coverage ? BUILD_RUN_SOURCE_REF.exec(coverage.source_ref)?.[1]?.toLowerCase() : undefined
    if (coverage && coverageRunId) acceptedEvents.set('built_or_dispositioned', coverage)
    if (coverageRunId && validProducer) {
      const producerExecution = latest(events.filter((event) => {
        if (event.event_type !== BUILD_EVENT_BY_MILESTONE.deployed_and_executed
          || event.entity_type !== 'asset'
          || event.entity_id !== validProducer.asset_id
          || event.layer !== validProducer.layer) return false
        return BUILD_RUN_SOURCE_REF.exec(event.source_ref)?.[1]?.toLowerCase() === coverageRunId
      }))
      if (producerExecution) acceptedEvents.set('deployed_and_executed', producerExecution)
    }
  } else {
    const dispositionEventType = DISPOSITION_EVENTS[obligation as keyof typeof DISPOSITION_EVENTS]
    const disposition = dispositionEventType ? latestTrustedAssetEvent(events, input.asset, dispositionEventType, (event) => {
      const payload = NirmanaNonBuildDispositionEvidenceSchema.safeParse(event.evidence_payload)
      return payload.success && payload.data.disposition === obligation
        && hasCurrentBinding(payload.data, analysis)
        && event.source_kind === 'git_commit' && /^git:[a-f0-9]{40}$/.test(event.source_ref)
        && after(event, decision)
    }) : undefined
    if (disposition) acceptedEvents.set('built_or_dispositioned', disposition)
    notApplicable.add('deployed_and_executed')
  }

  const operational = ['build', 'probe', 'producer_covered'].includes(obligation)
    ? acceptedEvents.get('deployed_and_executed')
    : acceptedEvents.get('built_or_dispositioned')
  if (integrity && after(integrity, operational)
    && integrity.source_kind === 'server_reconstructed'
    && integrity.source_ref === `nirmana-elevation:integrity:${input.asset.asset_id}`) acceptedEvents.set('verified', integrity)
  if (frozen && after(frozen, acceptedEvents.get('verified'))
    && frozen.source_kind === 'server_reconstructed'
    && frozen.source_ref === `nirmana-elevation:freeze:${input.asset.asset_id}`) acceptedEvents.set('frozen', frozen)

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
    inherited_from_asset_id: acceptedEvents.has('deployed_and_executed') ? validProducer?.asset_id ?? null : null,
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

  const lowerLayersActuallyFrozen = input.manifestAssets
    .filter((asset) => LAYER_IDS.indexOf(asset.layer) < currentLayerRank)
    .every((asset) => asset.execution_obligation !== undefined
      && asset.execution_obligation !== 'unresolved'
      && !input.blockedAssetIds.has(asset.asset_id)
      && input.frozenAssetIds.has(asset.asset_id))
  if (!lowerLayersActuallyFrozen) return []

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
