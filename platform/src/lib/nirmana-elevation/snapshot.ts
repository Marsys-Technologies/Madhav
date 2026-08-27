import { createHash } from 'node:crypto'
import { query } from '@/lib/db/client'
import {
  assertManifestMatchesRegistryIdentity,
  canonicalManifestDigest,
  canonicalNirmanaRebuildEvidenceDigest,
  canonicalRegistryContractDigest,
  NirmanaProducerCoverageEvidenceSchema,
  NirmanaRebuildEvidenceSchema,
  parseFreezableNirmanaElevationManifest,
  registryContractFingerprintInput,
  type NirmanaElevationManifest,
  type NirmanaRegistryContractRow,
} from './definitions'
import {
  canonicalizeCampaignStageTransitions,
  deriveEligibleNextAssetIds,
  projectAssetMilestones,
  projectCampaignStages,
} from './projection'
import type { NirmanaReleaseStatus } from './release'
import {
  NIRMANA_LAYER_NAMES,
  NIRMANA_MILESTONE_IDS,
  NIRMANA_STAGE_IDS,
  NirmanaElevationSnapshotV2Schema,
  type NirmanaElevationSnapshotV2,
} from './types'

const LAYERS = [
  ['L0', 'brahmagyan'], ['L1', 'ganita'], ['L2', 'bodha'],
  ['L3', 'kala'], ['L4', 'phala'], ['L5', 'mimamsa'],
] as const
const EXECUTION_PERMITTING_OBLIGATIONS = new Set(['build', 'probe'])

type RawSourceId = keyof NirmanaElevationRawSources
type SourceId = Exclude<RawSourceId, 'asset_labels' | 'monitor_observations'> | 'asset_label_catalogue' | 'program_monitor'

const SOURCE_PROVENANCE: Record<SourceId, string> = {
  asset_registry: 'Cloud SQL asset_registry',
  asset_throughput: 'Cloud SQL asset_throughput',
  build_runs: 'Cloud SQL build_runs',
  build_run_assets: 'Cloud SQL build_run_assets',
  build_substep_progress: 'Cloud SQL build_substep_progress',
  campaign_definitions: 'Cloud SQL nirmana_elevation_campaign_definitions',
  campaign_events: 'Cloud SQL nirmana_elevation_campaign_events',
  asset_label_catalogue: 'Cloud SQL nirmana_elevation_asset_labels',
  program_monitor: 'Cloud SQL nirmana_elevation_monitor_observations',
}

type NirmanaProgramSyncStatus = NirmanaElevationSnapshotV2['program_sync']['status']

interface NirmanaMonitorObservationRow {
  id: string
  observed_at: string
  status: Exclude<NirmanaProgramSyncStatus, 'unknown'>
  affected_asset_ids: string[]
  current_definition_sha256: string | null
  candidate_definition_sha256: string | null
  candidate_catalogue_sha256: string | null
  source_state: 'available' | 'unavailable'
  source_observed_at: string | null
  freshness_state: 'fresh' | 'stale' | 'unavailable'
  freshness_deadline_at: string | null
  source_error_code: string | null
  runtime_liveness: 'active' | 'quiet' | 'unavailable'
}

export interface NirmanaElevationRawSources {
  asset_registry: Array<NirmanaRegistryContractRow & { english_name: string | null; asset_type: string | null }>
  asset_throughput: Array<{ asset_id: string; chart_id: string | null; state: string; last_built_at: string | null }>
  build_runs: Array<{ id: string; chart_id: string | null; action?: string | null; state: string; current_asset_id: string | null; created_at: string; started_at: string | null; triggered_by?: string | null }>
  build_run_assets: Array<{ run_id: string; asset_id: string; position: number; state: string; started_at: string | null; ended_at: string | null; error: string | null }>
  build_substep_progress: Array<{ chart_id: string; asset_id: string; committed: string | number; last_progress_at: string | null }>
  campaign_definitions: Array<{ campaign_id: string; definition_revision: string; definition_status: 'reconciling' | 'frozen' | 'superseded'; manifest: unknown; manifest_sha256: string; created_at: string }>
  campaign_events: Array<{ event_id?: string; idempotency_key?: string; campaign_id: string; definition_revision: string; event_type: string; entity_type: string; entity_id: string; layer: string | null; evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>
  asset_labels: Array<{
    campaign_id: string
    definition_revision: string
    catalogue_revision: string
    asset_id: string
    sanskrit_name: string | null
    english_name: string | null
    description: string | null
    legacy_aliases: Array<{ asset_id: string; sanskrit_name: string | null; english_name: string | null }>
    source_ref: string
    label_digest: string
    recorded_at: string
  }>
  monitor_observations?: NirmanaMonitorObservationRow[]
}

export class NirmanaElevationSourceError extends Error {
  readonly publicCode = 'NIRMANA_SOURCE_UNAVAILABLE' as const
  readonly publicMessage = 'Authoritative source is unavailable.'

  constructor(readonly sourceId: SourceId) {
    super('Authoritative Nirmana source query failed.')
    this.name = 'NirmanaElevationSourceError'
  }
}

async function loadSource<K extends RawSourceId>(sourceId: K, sql: string): Promise<Pick<NirmanaElevationRawSources, K>> {
  try {
    const { rows } = await query(sql)
    return { [sourceId]: rows } as Pick<NirmanaElevationRawSources, K>
  } catch {
    const publicSourceId: SourceId = sourceId === 'asset_labels' ? 'asset_label_catalogue'
      : sourceId === 'monitor_observations' ? 'program_monitor'
        : sourceId as SourceId
    console.error('[nirmana-elevation] authoritative source query failed', {
      source_id: publicSourceId,
      error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
    })
    throw new NirmanaElevationSourceError(publicSourceId)
  }
}

/** Only primary build tables plus tracker-owned evidence tables feed this projection. */
export async function loadNirmanaElevationRawSources(): Promise<NirmanaElevationRawSources> {
  const registry = await loadSource('asset_registry', `SELECT asset_id, english_name, layer, scope, sort_order, has_writer,
    asset_type, asset_kind, catalog_status, is_active, COALESCE(depends_on, '{}') AS depends_on,
    target_table, count_sql, integrity_check_sql, health_probe, natural_key_partition,
    superseded_by, data_disposition, dead_flag
    FROM asset_registry ORDER BY layer, sort_order, asset_id`)
  const throughput = await loadSource('asset_throughput', `SELECT DISTINCT ON (asset_id, chart_id) asset_id, chart_id, state, last_built_at FROM asset_throughput ORDER BY asset_id, chart_id, last_built_at DESC NULLS LAST`)
  const runs = await loadSource('build_runs', `SELECT id, chart_id, action, state, current_asset_id, created_at, started_at, triggered_by FROM build_runs ORDER BY created_at DESC`)
  const runAssets = await loadSource('build_run_assets', `SELECT bra.run_id, bra.asset_id, bra.position, bra.state, bra.started_at, bra.ended_at, bra.error FROM build_run_assets bra JOIN build_runs br ON br.id = bra.run_id ORDER BY br.created_at DESC, br.id DESC, bra.position ASC, bra.asset_id ASC`)
  const substeps = await loadSource('build_substep_progress', `SELECT bsp.chart_id, bsp.asset_id, COUNT(*)::text AS committed, MAX(bsp.completed_at) AS last_progress_at FROM build_substep_progress bsp WHERE EXISTS (SELECT 1 FROM build_runs br WHERE br.chart_id = bsp.chart_id AND br.state IN ('planned', 'running', 'paused')) GROUP BY bsp.chart_id, bsp.asset_id`)
  const definitions = await loadSource('campaign_definitions', `SELECT campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_at FROM nirmana_elevation_campaign_definitions WHERE campaign_id = 'nirmana-elevation' AND superseded_at IS NULL ORDER BY created_at DESC LIMIT 1`)
  const events = await loadSource('campaign_events', `SELECT event_id, idempotency_key, campaign_id, definition_revision, event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref, observed_at, recorded_at FROM nirmana_elevation_campaign_events WHERE campaign_id = 'nirmana-elevation' ORDER BY recorded_at ASC, event_id ASC`)
  const labels = await loadSource('asset_labels', `SELECT campaign_id, definition_revision, catalogue_revision, asset_id,
       sanskrit_name, english_name, description, legacy_aliases,
       source_ref, label_digest, recorded_at
  FROM nirmana_elevation_asset_labels
 WHERE campaign_id = 'nirmana-elevation'
 ORDER BY catalogue_revision, asset_id`)
  const monitor = await loadSource('monitor_observations', `SELECT id, observed_at, status, affected_asset_ids,
       current_definition_sha256, candidate_definition_sha256, candidate_catalogue_sha256,
       source_state, source_observed_at, freshness_state, freshness_deadline_at,
       source_error_code, runtime_liveness
  FROM nirmana_elevation_monitor_observations
 ORDER BY observed_at DESC, id DESC
 LIMIT 1`)
  return { ...registry, ...throughput, ...runs, ...runAssets, ...substeps, ...definitions, ...events, ...labels, ...monitor }
}

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

function digest(value: unknown): string {
  return createHash('sha256').update(stableJson(value)).digest('hex')
}

function asIso(value: string | null | undefined): string | null {
  return value && !Number.isNaN(Date.parse(value)) ? new Date(value).toISOString() : null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function timestamp(value: string): number {
  const parsed = Date.parse(value)
  return Number.isNaN(parsed) ? 0 : parsed
}

const PROGRAM_SYNC_GAPS: Partial<Record<NirmanaProgramSyncStatus, string>> = {
  unknown: 'No program synchronization observation is available.',
  baseline_missing: 'No accepted frozen program denominator is available.',
  plan_adaptation_required: 'Plan adaptation is required before the program denominator can change.',
  evidence_refresh_required: 'Accepted program evidence must be refreshed before synchronization can be restored.',
  label_refresh_required: 'The governed program label catalogue must be refreshed before synchronization can be restored.',
  release_attention: 'Program release reconciliation requires attention.',
  source_unavailable: 'The authoritative program monitor source is unavailable.',
}

function projectProgramSync(
  rows: NonNullable<NirmanaElevationRawSources['monitor_observations']>,
  generatedAt: string,
): {
  programSync: NirmanaElevationSnapshotV2['program_sync']
  source: NirmanaElevationSnapshotV2['sources'][number]
  gaps: string[]
} {
  const latest = [...rows].sort((left, right) => timestamp(right.observed_at) - timestamp(left.observed_at)
    || right.id.localeCompare(left.id))[0]
  if (!latest) {
    return {
      programSync: {
        status: 'unknown', source_observation_id: null, observed_at: null, age_seconds: null, affected_asset_ids: [],
        current_definition_sha256: null, candidate_definition_sha256: null, candidate_catalogue_sha256: null,
      },
      source: {
        source_id: 'program_monitor', provenance: SOURCE_PROVENANCE.program_monitor,
        state: 'unknown', observed_at: null, age_seconds: null, error_code: null, error_message: null,
      },
      gaps: [PROGRAM_SYNC_GAPS.unknown!],
    }
  }

  const sourceObservedAt = asIso(latest.source_observed_at)
  const freshnessDeadlineAt = asIso(latest.freshness_deadline_at)
  const ageSeconds = sourceObservedAt === null ? null : Math.max(
    0,
    Math.floor((Date.parse(generatedAt) - Date.parse(sourceObservedAt)) / 1000),
  )
  const unavailable = latest.status === 'source_unavailable' || latest.source_state === 'unavailable'
  const status: NirmanaProgramSyncStatus = unavailable ? 'source_unavailable' : latest.status
  const state = unavailable ? 'unavailable' as const
    : latest.freshness_state === 'fresh'
      && freshnessDeadlineAt !== null
      && Date.parse(generatedAt) <= Date.parse(freshnessDeadlineAt)
      ? 'fresh' as const : 'stale' as const
  const gaps = [
    ...(PROGRAM_SYNC_GAPS[status] ? [PROGRAM_SYNC_GAPS[status]!] : []),
    ...(state === 'stale' ? ['The program monitor observation is stale; synchronization status may be outdated.'] : []),
  ]
  return {
    programSync: {
      status,
      source_observation_id: unavailable ? null : latest.id,
      observed_at: sourceObservedAt,
      age_seconds: ageSeconds,
      affected_asset_ids: [...new Set(latest.affected_asset_ids)].sort(),
      current_definition_sha256: latest.current_definition_sha256,
      candidate_definition_sha256: latest.candidate_definition_sha256,
      candidate_catalogue_sha256: unavailable ? null : latest.candidate_catalogue_sha256,
    },
    source: {
      source_id: 'program_monitor', provenance: SOURCE_PROVENANCE.program_monitor,
      state, observed_at: sourceObservedAt, age_seconds: ageSeconds,
      error_code: unavailable ? 'NIRMANA_SOURCE_UNAVAILABLE' : null,
      error_message: unavailable ? 'Authoritative source is unavailable.' : null,
    },
    gaps,
  }
}

function layerIdForRegistry(layer: string): (typeof LAYERS)[number][0] | null {
  return LAYERS.find(([, sourceLayer]) => sourceLayer === layer)?.[0]
    ?? (LAYERS.some(([layerId]) => layerId === layer) ? layer as (typeof LAYERS)[number][0] : null)
}

function canonicalRawLabelDigest(labels: NirmanaElevationRawSources['asset_labels']): string {
  return digest(labels
    .map(({ asset_id, sanskrit_name, english_name, description, legacy_aliases, source_ref }) => ({
      asset_id, sanskrit_name, english_name, description, legacy_aliases, source_ref,
    }))
    .sort((left, right) => left.asset_id.localeCompare(right.asset_id)))
}

function selectAcceptedLabels(
  raw: NirmanaElevationRawSources,
  definition: NirmanaElevationRawSources['campaign_definitions'][number] | undefined,
): {
  labelsById: Map<string, NirmanaElevationRawSources['asset_labels'][number]>
  acceptedCatalogueRevision: string | null
  contradictions: string[]
} {
  if (!definition) return { labelsById: new Map(), acceptedCatalogueRevision: null, contradictions: [] }
  const receipts = raw.campaign_events
    .filter((event) => event.campaign_id === definition.campaign_id
      && event.definition_revision === definition.definition_revision
      && event.event_type === 'asset_label_catalogue_accepted'
      && event.entity_type === 'label_catalogue'
      && event.layer === null
      && event.entity_id.length > 0
      && isRecord(event.evidence_payload)
      && typeof event.evidence_payload.catalogue_sha256 === 'string'
      && /^[a-f0-9]{64}$/.test(event.evidence_payload.catalogue_sha256)
      && Number.isInteger(event.evidence_payload.asset_count)
      && Number(event.evidence_payload.asset_count) > 0
      && timestamp(event.observed_at) > 0
      && timestamp(event.recorded_at) > 0)
    .sort((left, right) => timestamp(right.recorded_at) - timestamp(left.recorded_at)
      || timestamp(right.observed_at) - timestamp(left.observed_at)
      || right.entity_id.localeCompare(left.entity_id))
  const receipt = receipts[0]
  if (!receipt || !isRecord(receipt.evidence_payload)) {
    return { labelsById: new Map(), acceptedCatalogueRevision: null, contradictions: [] }
  }

  const catalogueRevision = receipt.entity_id
  const acceptedDigest = String(receipt.evidence_payload.catalogue_sha256)
  const acceptedCount = Number(receipt.evidence_payload.asset_count)
  const labels = raw.asset_labels.filter((label) => label.campaign_id === definition.campaign_id
    && label.definition_revision === definition.definition_revision
    && label.catalogue_revision === catalogueRevision)
  const uniqueAssetIds = new Set(labels.map((label) => label.asset_id))
  const digestMatches = labels.length > 0
    && labels.every((label) => label.label_digest === acceptedDigest)
    && canonicalRawLabelDigest(labels) === acceptedDigest
  const countMatches = labels.length === acceptedCount && uniqueAssetIds.size === acceptedCount
  if (!digestMatches || !countMatches) {
    return {
      labelsById: new Map(),
      acceptedCatalogueRevision: catalogueRevision,
      contradictions: [
        `Accepted label catalogue ${catalogueRevision} digest/count does not match its authoritative label rows; versioned identity is withheld.`,
      ],
    }
  }
  return {
    labelsById: new Map(labels.map((label) => [label.asset_id, label])),
    acceptedCatalogueRevision: catalogueRevision,
    contradictions: [],
  }
}

type NirmanaStageId = (typeof NIRMANA_STAGE_IDS)[number]

function contiguousStageSpine(events: NirmanaElevationRawSources['campaign_events']): {
  currentStage: NirmanaStageId | null
  enteredAt: Map<NirmanaStageId, string | null>
  enteredReceiptTime: Map<NirmanaStageId, number>
  exitedAt: Map<NirmanaStageId, string | null>
  contradictions: string[]
} {
  const candidates = events.filter((event) => event.event_type === 'stage_transition_accepted')
  const canonical = canonicalizeCampaignStageTransitions(candidates)
  const transitions = canonical.transitions
  const contradictions: string[] = [
    ...(canonical.invalidEventCount === 0 ? []
      : ['One or more campaign-stage receipts have invalid entity, layer, ordering, or payload semantics.']),
    ...canonical.contradictions,
  ]
  const enteredAt = new Map<NirmanaStageId, string | null>()
  const enteredReceiptTime = new Map<NirmanaStageId, number>()
  const exitedAt = new Map<NirmanaStageId, string | null>()
  let currentStage: NirmanaStageId | null = null
  let nextIndex = 0
  for (const transition of transitions) {
    const expectedTo = NIRMANA_STAGE_IDS[nextIndex]
    const expectedFrom = nextIndex === 0 ? null : NIRMANA_STAGE_IDS[nextIndex - 1]
    if (transition.from === expectedFrom && transition.to === expectedTo) {
      currentStage = transition.to
      enteredAt.set(transition.to, asIso(transition.event.observed_at))
      enteredReceiptTime.set(transition.to, timestamp(transition.event.recorded_at))
      if (transition.from !== null) exitedAt.set(transition.from, asIso(transition.event.observed_at))
      nextIndex += 1
      continue
    }
    contradictions.push(`Campaign-stage receipts do not form a contiguous canonical chain at ${transition.from ?? 'null'} -> ${transition.to}.`)
  }
  return { currentStage, enteredAt, enteredReceiptTime, exitedAt, contradictions }
}

function validManifest(definition: NirmanaElevationRawSources['campaign_definitions'][number] | undefined, registryById: Map<string, NirmanaElevationRawSources['asset_registry'][number]>): NirmanaElevationManifest | null {
  if (!definition || definition.definition_status !== 'frozen') return null
  const parsed = parseFreezableNirmanaElevationManifest(definition.manifest)
  if (!parsed) return null
  if (canonicalManifestDigest(parsed) !== definition.manifest_sha256) return null
  try {
    assertManifestMatchesRegistryIdentity(parsed, [...registryById.values()])
  } catch {
    return null
  }
  return parsed
}

function runTimestamp(run: NirmanaElevationRawSources['build_runs'][number]): number {
  const timestamp = Date.parse(run.created_at) || Date.parse(run.started_at ?? '')
  return Number.isNaN(timestamp) ? 0 : timestamp
}

function activeRunPriority(run: NirmanaElevationRawSources['build_runs'][number]): number {
  return run.state === 'running' ? 2 : run.state === 'paused' ? 1 : 0
}

function activeRunsForChart(raw: NirmanaElevationRawSources, chartId: string | null | undefined, acceptedRunIds: Set<string>): NirmanaElevationRawSources['build_runs'] {
  return raw.build_runs
    .filter((run) => chartId !== undefined
      && run.chart_id === chartId
      && acceptedRunIds.has(run.id.toLowerCase())
      && run.triggered_by !== 'nirmana-f0-machinery-canary'
      && ['planned', 'running', 'paused'].includes(run.state))
    .sort((left, right) => activeRunPriority(right) - activeRunPriority(left) || runTimestamp(right) - runTimestamp(left) || right.id.localeCompare(left.id))
}

/** Current-run state is selected from active runs only, newest run first. */
function currentRunAssetsById(raw: NirmanaElevationRawSources, activeRuns: NirmanaElevationRawSources['build_runs']): Map<string, NirmanaElevationRawSources['build_run_assets'][number]> {
  const activeRunsById = new Map(activeRuns.map((run) => [run.id, run]))
  const ordered = raw.build_run_assets
    .filter((asset) => activeRunsById.has(asset.run_id))
    .sort((left, right) => {
      const leftRun = activeRunsById.get(left.run_id)!
      const rightRun = activeRunsById.get(right.run_id)!
      const stateDifference = activeRunPriority(rightRun) - activeRunPriority(leftRun)
      if (stateDifference !== 0) return stateDifference
      const timestampDifference = runTimestamp(rightRun) - runTimestamp(leftRun)
      if (timestampDifference !== 0) return timestampDifference
      const runDifference = right.run_id.localeCompare(left.run_id)
      if (runDifference !== 0) return runDifference
      return left.position - right.position
    })
  const byAsset = new Map<string, NirmanaElevationRawSources['build_run_assets'][number]>()
  for (const asset of ordered) {
    if (!byAsset.has(asset.asset_id)) byAsset.set(asset.asset_id, asset)
  }
  return byAsset
}

function latestTerminalFailuresByAsset(raw: NirmanaElevationRawSources, chartId: string | null | undefined, acceptedRunIds: Set<string>): Map<string, { run_id: string; timestamp: number }> {
  const terminalRunsById = new Map(raw.build_runs
    .filter((run) => chartId !== undefined
      && run.chart_id === chartId
      && acceptedRunIds.has(run.id.toLowerCase())
      && run.triggered_by !== 'nirmana-f0-machinery-canary'
      && ['failed', 'error', 'cancelled', 'stopped', 'aborted'].includes(run.state))
    .map((run) => [run.id, run]))
  const candidates = raw.build_run_assets
    .filter((asset) => terminalRunsById.has(asset.run_id))
    .map((asset) => ({
      asset_id: asset.asset_id,
      run_id: asset.run_id,
      timestamp: Date.parse(asset.ended_at ?? asset.started_at ?? '') || runTimestamp(terminalRunsById.get(asset.run_id)!),
    }))
    .sort((left, right) => right.timestamp - left.timestamp || right.run_id.localeCompare(left.run_id))
  const byAsset = new Map<string, { run_id: string; timestamp: number }>()
  for (const candidate of candidates) {
    if (!byAsset.has(candidate.asset_id)) byAsset.set(candidate.asset_id, candidate)
  }
  return byAsset
}

function runtimeThroughputById(raw: NirmanaElevationRawSources, registryById: Map<string, NirmanaElevationRawSources['asset_registry'][number]>, chartId: string | null | undefined): Map<string, NirmanaElevationRawSources['asset_throughput'][number]> {
  const rows = raw.asset_throughput
    .filter((entry) => {
      const scope = registryById.get(entry.asset_id)?.scope
      return scope === 'global' ? entry.chart_id === null : chartId !== undefined && entry.chart_id === chartId
    })
    .sort((left, right) => (Date.parse(right.last_built_at ?? '') || 0) - (Date.parse(left.last_built_at ?? '') || 0))
  const byAsset = new Map<string, NirmanaElevationRawSources['asset_throughput'][number]>()
  for (const entry of rows) {
    if (!byAsset.has(entry.asset_id)) byAsset.set(entry.asset_id, entry)
  }
  return byAsset
}

const BUILD_RUN_SOURCE_REF = /^build_run:([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i
const SHA256 = /^[a-f0-9]{64}$/
const PUBLIC_AUDIT_EVENT_ENTITIES = {
  asset_analysis_accepted: 'asset', optimization_verdict_accepted: 'asset', implementation_accepted: 'asset',
  accepted_rebuild_observed: 'asset', integrity_verified: 'asset', asset_frozen: 'asset', probe_accepted: 'asset',
  static_accepted: 'asset', source_accepted: 'asset', empty_accepted: 'asset', retired_with_disposition: 'asset',
  producer_covered: 'asset', stage_transition_accepted: 'campaign_stage', foundation_lane_accepted: 'foundation_lane',
  asset_label_catalogue_accepted: 'label_catalogue', build_run_authorized: 'build_run',
} as const

type PublicAuditEventType = keyof typeof PUBLIC_AUDIT_EVENT_ENTITIES

function buildRunId(sourceRef: string): string | null {
  return BUILD_RUN_SOURCE_REF.exec(sourceRef)?.[1]?.toLowerCase() ?? null
}

function sanitizedSourceKind(value: string): string {
  return /^[A-Za-z0-9._:-]{1,128}$/.test(value) ? value : 'other'
}

function sanitizedReference(value: string): string {
  const bounded = value.slice(0, 512)
  return /(?:password|passwd|token|secret|api[_-]?key|authorization)\s*[=:]|bearer\s|postgres(?:ql)?:\/\/|[a-z][a-z0-9+.-]*:\/\/[^/\s:@]+:[^/\s@]+@|BEGIN [A-Z ]*PRIVATE KEY/i.test(bounded)
    ? 'redacted:unsafe-reference'
    : bounded || 'unknown:reference'
}

type RunAuthorization = {
  layer: (typeof LAYERS)[number][0]
  waveIndex: number
  assetIds: string[]
  authorizationSha256: string
}

function orderedFrozenAssets(
  manifestAssets: NirmanaElevationManifest['assets'],
  lifecycleFrozenAssetIds: Set<string>,
  freezeReceiptTimesByAsset: Map<string, number[]>,
  stageEntryReceiptTimes: Map<NirmanaStageId, number>,
): { accepted: Set<string>; outOfOrder: Set<string> } {
  const accepted = new Set<string>()
  const outOfOrder = new Set<string>()
  let priorLayerComplete: boolean = true
  let priorLayerCompletedAt = 0

  for (const [layerId] of LAYERS) {
    const layerAssets = manifestAssets.filter((asset) => asset.layer === layerId)
    const layerEnteredAt = stageEntryReceiptTimes.get(layerId)
    let priorWaveComplete: boolean = priorLayerComplete && layerEnteredAt !== undefined
    let priorWaveCompletedAt = Math.max(priorLayerCompletedAt, layerEnteredAt ?? 0)
    const waveIndexes = [...new Set(layerAssets
      .map((asset) => asset.wave_index)
      .filter((waveIndex): waveIndex is number => waveIndex !== undefined))]
      .sort((left, right) => left - right)

    for (const waveIndex of waveIndexes) {
      const waveAssets = layerAssets.filter((asset) => asset.wave_index === waveIndex)
      const acceptedReceiptTimes: number[] = []
      for (const asset of waveAssets) {
        const receiptTimes = freezeReceiptTimesByAsset.get(asset.asset_id) ?? []
        const hasPrematureReceipt = receiptTimes.some((receiptTime) => !priorWaveComplete
          || receiptTime <= priorWaveCompletedAt)
        if (hasPrematureReceipt) {
          outOfOrder.add(asset.asset_id)
        }
        const validReceiptTime = receiptTimes.find((receiptTime) => receiptTime > priorWaveCompletedAt)
        if (!hasPrematureReceipt
          && priorWaveComplete
          && lifecycleFrozenAssetIds.has(asset.asset_id)
          && validReceiptTime !== undefined) {
          accepted.add(asset.asset_id)
          acceptedReceiptTimes.push(validReceiptTime)
        }
      }
      priorWaveComplete = priorWaveComplete
        && waveAssets.every((asset) => accepted.has(asset.asset_id))
      if (priorWaveComplete && acceptedReceiptTimes.length > 0) {
        priorWaveCompletedAt = Math.max(priorWaveCompletedAt, ...acceptedReceiptTimes)
      }
    }

    for (const asset of layerAssets.filter((candidate) => candidate.wave_index === undefined)) {
      if ((freezeReceiptTimesByAsset.get(asset.asset_id)?.length ?? 0) > 0) outOfOrder.add(asset.asset_id)
    }
    priorLayerComplete = priorWaveComplete
      && layerAssets.every((asset) => accepted.has(asset.asset_id))
    if (priorLayerComplete) priorLayerCompletedAt = priorWaveCompletedAt
  }

  return { accepted, outOfOrder }
}

function acceptedRunAuthorizations(
  raw: NirmanaElevationRawSources,
  events: NirmanaElevationRawSources['campaign_events'],
  manifest: NirmanaElevationManifest | null,
): { byRunId: Map<string, RunAuthorization>; contradictions: string[] } {
  const byRunId = new Map<string, RunAuthorization & { signature: string }>()
  const conflictedRunIds = new Set<string>()
  const contradictions: string[] = []
  if (!manifest) return { byRunId, contradictions }
  const manifestById = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  const runsById = new Map(raw.build_runs.map((run) => [run.id.toLowerCase(), run]))

  for (const event of events) {
    if (event.event_type !== 'build_run_authorized'
      || event.entity_type !== 'build_run'
      || !isRecord(event.evidence_payload)) continue
    const runId = buildRunId(event.source_ref)
    const waveIndex = event.evidence_payload.wave_index
    const assetIds = event.evidence_payload.asset_ids
    const authorizationSha256 = event.evidence_payload.authorization_sha256
    const layer = event.layer
    if (!runId
      || event.entity_id.toLowerCase() !== runId
      || !LAYERS.some(([layerId]) => layerId === layer)
      || !Number.isInteger(waveIndex)
      || Number(waveIndex) < 0
      || !Array.isArray(assetIds)
      || assetIds.length === 0
      || assetIds.some((assetId) => typeof assetId !== 'string')
      || new Set(assetIds).size !== assetIds.length
      || typeof authorizationSha256 !== 'string'
      || !SHA256.test(authorizationSha256)) continue
    const typedLayer = layer as RunAuthorization['layer']
    const sortedAssetIds = [...assetIds as string[]].sort((left, right) => left.localeCompare(right))
    if (sortedAssetIds.some((assetId) => {
      const asset = manifestById.get(assetId)
      return !asset
        || asset.layer !== typedLayer
        || asset.wave_index !== waveIndex
        || !asset.execution_obligation
        || !EXECUTION_PERMITTING_OBLIGATIONS.has(asset.execution_obligation)
    })) continue
    const run = runsById.get(runId)
    if (!run
      || run.chart_id !== manifest.chart_id
      || (run.action != null && run.action !== 'rebuild')
      || run.triggered_by === 'nirmana-f0-machinery-canary') continue
    const runAssetIds = [...new Set(raw.build_run_assets
      .filter((asset) => asset.run_id.toLowerCase() === runId)
      .map((asset) => asset.asset_id))].sort((left, right) => left.localeCompare(right))
    if (runAssetIds.length === 0 || stableJson(runAssetIds) !== stableJson(sortedAssetIds)) continue
    const signature = stableJson({ layer: typedLayer, wave_index: waveIndex, asset_ids: sortedAssetIds, authorization_sha256: authorizationSha256 })
    if (conflictedRunIds.has(runId)) continue
    const existing = byRunId.get(runId)
    if (existing && existing.signature !== signature) {
      byRunId.delete(runId)
      conflictedRunIds.add(runId)
      contradictions.push(`Build run ${runId} has conflicting campaign authorization receipts.`)
      continue
    }
    if (!existing) byRunId.set(runId, {
      layer: typedLayer,
      waveIndex: Number(waveIndex),
      assetIds: sortedAssetIds,
      authorizationSha256,
      signature,
    })
  }

  return {
    byRunId: new Map([...byRunId].map(([runId, { layer, waveIndex, assetIds, authorizationSha256 }]) => [runId, {
      layer, waveIndex, assetIds, authorizationSha256,
    }])),
    contradictions,
  }
}

function projectAudit(
  events: NirmanaElevationRawSources['campaign_events'],
  manifest: NirmanaElevationManifest | null,
) {
  const manifestIds = new Set(manifest?.assets.map((asset) => asset.asset_id) ?? [])
  const receipts = events
    .filter((event): event is typeof event & { event_type: PublicAuditEventType } => event.event_type in PUBLIC_AUDIT_EVENT_ENTITIES
      && PUBLIC_AUDIT_EVENT_ENTITIES[event.event_type as PublicAuditEventType] === event.entity_type
      && timestamp(event.observed_at) > 0
      && timestamp(event.recorded_at) > 0)
    .map((event) => {
      const payloadAssetIds = event.entity_type === 'build_run' && isRecord(event.evidence_payload) && Array.isArray(event.evidence_payload.asset_ids)
        ? event.evidence_payload.asset_ids.filter((assetId): assetId is string => typeof assetId === 'string' && manifestIds.has(assetId))
        : []
      const related_asset_ids = event.entity_type === 'asset' && manifestIds.has(event.entity_id)
        ? [event.entity_id]
        : [...new Set(payloadAssetIds)].sort((left, right) => left.localeCompare(right))
      const fallbackRef = digest({
        campaign_id: event.campaign_id,
        definition_revision: event.definition_revision,
        event_type: event.event_type,
        entity_type: event.entity_type,
        entity_id: event.entity_id,
        recorded_at: event.recorded_at,
      })
      return {
        ledger_ref: `campaign_event:${event.event_id && /^[0-9a-f-]{36}$/i.test(event.event_id) ? event.event_id : fallbackRef}`,
        event_type: event.event_type,
        entity_type: event.entity_type,
        entity_id: event.entity_id.slice(0, 256),
        related_asset_ids,
        layer: LAYERS.some(([layerId]) => layerId === event.layer) ? event.layer : null,
        source_kind: sanitizedSourceKind(event.source_kind),
        source_ref: sanitizedReference(event.source_ref),
        observed_at: new Date(event.observed_at).toISOString(),
        recorded_at: new Date(event.recorded_at).toISOString(),
        payload_sha256: digest(event.evidence_payload),
      }
    })
  const raw_ledger_refs = [...new Map(receipts.flatMap((receipt) => {
    const refs: Array<{ ledger_kind: 'campaign_event' | 'build_run'; ledger_ref: string }> = [
      { ledger_kind: 'campaign_event', ledger_ref: receipt.ledger_ref },
    ]
    const runId = buildRunId(receipt.source_ref)
    if (runId) refs.push({ ledger_kind: 'build_run' as const, ledger_ref: `build_run:${runId}` })
    return refs.map((reference) => [`${reference.ledger_kind}:${reference.ledger_ref}`, reference] as const)
  })).values()]
  return { receipts, raw_ledger_refs }
}

export function projectNirmanaElevationSnapshot(raw: NirmanaElevationRawSources, { generatedAt = new Date().toISOString(), releaseStatus = null }: { generatedAt?: string; releaseStatus?: NirmanaReleaseStatus | null } = {}): NirmanaElevationSnapshotV2 {
  const generated_at = new Date(generatedAt).toISOString()
  const programProjection = projectProgramSync(raw.monitor_observations ?? [], generated_at)
  const definition = raw.campaign_definitions[0]
  const rawWithLabels = raw.asset_labels ? raw : { ...raw, asset_labels: [] }
  const registryById = new Map(raw.asset_registry.map((asset) => [asset.asset_id, asset]))
  const manifest = validManifest(definition, registryById)
  const manifestAssets = manifest?.assets ?? null
  const manifestById = new Map((manifestAssets ?? []).map((asset) => [asset.asset_id, asset]))
  const campaignEvents = definition ? raw.campaign_events
    .filter((event) => event.campaign_id === definition.campaign_id
      && event.definition_revision === definition.definition_revision)
    .sort((left, right) => timestamp(left.recorded_at) - timestamp(right.recorded_at)
      || (left.event_id ?? '').localeCompare(right.event_id ?? '')) : []
  const labelSelection = selectAcceptedLabels(rawWithLabels, definition)
  const audit = projectAudit(campaignEvents, manifest)
  const eventTypesByAsset = new Map<string, Set<string>>()
  const acceptedAnalysisFingerprintByAsset = new Map<string, string>()
  const acceptedAnalysisDigestByAsset = new Map<string, string>()
  for (const event of campaignEvents) {
    const types = eventTypesByAsset.get(event.entity_id) ?? new Set<string>()
    types.add(event.event_type)
    eventTypesByAsset.set(event.entity_id, types)
    if (event.event_type === 'asset_analysis_accepted'
      && event.evidence_payload !== null
      && typeof event.evidence_payload === 'object'
      && !Array.isArray(event.evidence_payload)) {
      const fingerprint = (event.evidence_payload as Record<string, unknown>).registry_fingerprint_sha256
      const analysisDigest = (event.evidence_payload as Record<string, unknown>).analysis_digest
      if (typeof fingerprint === 'string' && /^[a-f0-9]{64}$/.test(fingerprint)
        && typeof analysisDigest === 'string' && /^[a-f0-9]{64}$/.test(analysisDigest)
        && event.source_kind === 'git_commit' && /^git:[a-f0-9]{40}$/.test(event.source_ref)) {
        acceptedAnalysisFingerprintByAsset.set(event.entity_id, fingerprint)
        acceptedAnalysisDigestByAsset.set(event.entity_id, analysisDigest)
      }
    }
  }
  const liveRegistryFingerprintByAsset = new Map((manifestAssets ? raw.asset_registry : []).map((asset) => [
    asset.asset_id,
    canonicalRegistryContractDigest(registryContractFingerprintInput(asset)),
  ]))
  const unacceptedContractDriftIds = new Set(
    manifestAssets?.filter((asset) => {
      const liveFingerprint = liveRegistryFingerprintByAsset.get(asset.asset_id)
      return liveFingerprint !== undefined
        && liveFingerprint !== asset.registry_fingerprint_sha256
        && acceptedAnalysisFingerprintByAsset.get(asset.asset_id) !== liveFingerprint
    }).map((asset) => asset.asset_id) ?? [],
  )
  const staleAcceptedAnalysisIds = new Set(
    manifestAssets?.filter((asset) => {
      const acceptedFingerprint = acceptedAnalysisFingerprintByAsset.get(asset.asset_id)
      return acceptedFingerprint !== undefined
        && acceptedFingerprint !== liveRegistryFingerprintByAsset.get(asset.asset_id)
    }).map((asset) => asset.asset_id) ?? [],
  )
  const completedRunIds = new Set(raw.build_runs
    .filter((run) => run.state === 'completed'
      && run.chart_id === manifest?.chart_id
      && (run.action == null || run.action === 'rebuild')
      && run.triggered_by !== 'nirmana-f0-machinery-canary')
    .map((run) => run.id.toLowerCase()))
  const completedRunAssets = new Set(raw.build_run_assets
    .filter((asset) => asset.state === 'complete' && completedRunIds.has(asset.run_id.toLowerCase()))
    .map((asset) => `${asset.run_id.toLowerCase()}:${asset.asset_id}`))
  const acceptedBuildRunIdsByAsset = new Map<string, Set<string>>()
  for (const event of campaignEvents.filter((candidate) => candidate.event_type === 'accepted_rebuild_observed')) {
    const runId = buildRunId(event.source_ref)
    const manifestAsset = manifestById.get(event.entity_id)
    if (event.entity_type === 'asset' && manifestAsset?.layer === event.layer && runId
      && completedRunAssets.has(`${runId}:${event.entity_id}`)) {
      const runIds = acceptedBuildRunIdsByAsset.get(event.entity_id) ?? new Set<string>()
      runIds.add(runId)
      acceptedBuildRunIdsByAsset.set(event.entity_id, runIds)
    }
  }
  const acceptedBuildAssetIds = new Set((manifestAssets ?? [])
    .filter((asset) => asset.execution_obligation === 'build' && acceptedBuildRunIdsByAsset.has(asset.asset_id))
    .map((asset) => asset.asset_id))
  const acceptedProducerCoverageEvents = new Set(campaignEvents.filter((event) => {
    if (event.event_type !== 'producer_covered' || event.entity_type !== 'asset') return false
    const coveredAsset = manifestById.get(event.entity_id)
    const runId = buildRunId(event.source_ref)
    const coverage = NirmanaProducerCoverageEvidenceSchema.safeParse(event.evidence_payload)
    if (!coverage.success || !runId || runId !== coverage.data.producer_run_id.toLowerCase()) return false
    const producer = coveredAsset?.producer_id ? manifestById.get(coveredAsset.producer_id) : undefined
    const producerRebuild = producer ? campaignEvents.find((candidate) => {
      const rebuild = NirmanaRebuildEvidenceSchema.safeParse(candidate.evidence_payload)
      return candidate.event_type === 'accepted_rebuild_observed' && candidate.entity_type === 'asset'
        && candidate.entity_id === producer.asset_id && candidate.layer === producer.layer
        && candidate.source_kind === 'build_run' && candidate.source_ref.toLowerCase() === `build_run:${coverage.data.producer_run_id.toLowerCase()}`
        && rebuild.success
        && rebuild.data.build_run_id.toLowerCase() === coverage.data.producer_run_id.toLowerCase()
        && canonicalNirmanaRebuildEvidenceDigest(rebuild.data) === coverage.data.producer_rebuild_digest
        && timestamp(candidate.observed_at) < timestamp(event.observed_at)
    }) : undefined
    const coveredAnalysis = campaignEvents.find((candidate) => candidate.event_type === 'asset_analysis_accepted'
      && candidate.entity_type === 'asset' && candidate.entity_id === event.entity_id
      && NirmanaProducerCoverageEvidenceSchema.safeParse({
        registry_fingerprint_sha256: (candidate.evidence_payload as Record<string, unknown>)?.registry_fingerprint_sha256,
        analysis_digest: (candidate.evidence_payload as Record<string, unknown>)?.analysis_digest,
        producer_asset_id: coverage.data.producer_asset_id,
        producer_layer: coverage.data.producer_layer,
        producer_run_id: coverage.data.producer_run_id,
        producer_rebuild_digest: coverage.data.producer_rebuild_digest,
      }).success
      && timestamp(candidate.observed_at) < timestamp(event.observed_at))
    return Boolean(coveredAsset?.execution_obligation === 'producer_covered'
      && coveredAsset.layer === event.layer
      && producer?.execution_obligation === 'build'
      && producer.layer === coverage.data.producer_layer
      && producer.asset_id === coverage.data.producer_asset_id
      && producer.covered_asset_ids?.includes(event.entity_id)
      && coverage.data.registry_fingerprint_sha256 === acceptedAnalysisFingerprintByAsset.get(event.entity_id)
      && coverage.data.analysis_digest === acceptedAnalysisDigestByAsset.get(event.entity_id)
      && producerRebuild && coveredAnalysis
      && acceptedBuildRunIdsByAsset.get(producer.asset_id)?.has(runId))
  }))
  const acceptedProducerCoverageAssetIds = new Set(
    [...acceptedProducerCoverageEvents].map((event) => event.entity_id),
  )
  const acceptedMilestoneEvents = campaignEvents.filter((event) => {
    if (event.event_type === 'accepted_rebuild_observed') {
      const runId = buildRunId(event.source_ref)
      return Boolean(runId && acceptedBuildRunIdsByAsset.get(event.entity_id)?.has(runId))
    }
    if (event.event_type === 'producer_covered') {
      return acceptedProducerCoverageEvents.has(event)
    }
    const manifestAsset = manifestById.get(event.entity_id)
    if (manifestAsset?.execution_obligation === 'producer_covered'
      && (event.event_type === 'integrity_verified' || event.event_type === 'asset_frozen')) {
      return acceptedProducerCoverageAssetIds.has(event.entity_id)
    }
    return true
  })
  const milestoneProjectionById = new Map((manifestAssets ?? []).map((asset) => [asset.asset_id, projectAssetMilestones({
    campaignId: definition?.campaign_id ?? 'nirmana-elevation',
    definitionRevision: definition?.definition_revision ?? 'unavailable',
    asset,
    events: acceptedMilestoneEvents,
    activeRunState: null,
    producerAsset: asset.producer_id ? manifestById.get(asset.producer_id) ?? null : null,
  })]))
  const dispositionedAssetIds = new Set((manifestAssets ?? [])
    .filter((asset) => asset.execution_obligation !== 'build' && asset.execution_obligation !== 'producer_covered')
    .filter((asset) => {
      const milestones = milestoneProjectionById.get(asset.asset_id)?.milestones ?? []
      const disposition = milestones.find((milestone) => milestone.milestone_id === 'built_or_dispositioned')
      const execution = milestones.find((milestone) => milestone.milestone_id === 'deployed_and_executed')
      return disposition?.state === 'earned' && (execution?.state === 'earned' || execution?.state === 'not_applicable')
    }).map((asset) => asset.asset_id))
  const producerCoveredAssetIds = new Set((manifestAssets ?? [])
    .filter((asset) => asset.execution_obligation === 'producer_covered' && Boolean(asset.producer_id))
    .filter((asset) => {
      const milestones = milestoneProjectionById.get(asset.asset_id)?.milestones ?? []
      return milestones.find((milestone) => milestone.milestone_id === 'built_or_dispositioned')?.state === 'earned'
        && milestones.find((milestone) => milestone.milestone_id === 'deployed_and_executed')?.state === 'earned'
        && acceptedProducerCoverageAssetIds.has(asset.asset_id)
    }).map((asset) => asset.asset_id))
  const terminalExecutionAssetIds = new Set([...acceptedBuildAssetIds, ...dispositionedAssetIds, ...producerCoveredAssetIds])
  const lifecycleFrozenAssetIds = new Set((manifestAssets ?? []).filter((asset) => {
    const acceptedFingerprint = acceptedAnalysisFingerprintByAsset.get(asset.asset_id)
    const liveFingerprint = liveRegistryFingerprintByAsset.get(asset.asset_id)
    const analysisMatchesCurrentContract = eventTypesByAsset.get(asset.asset_id)?.has('asset_analysis_accepted') === true
      && (acceptedFingerprint === liveFingerprint
        || (acceptedFingerprint === undefined && liveFingerprint === asset.registry_fingerprint_sha256))
    return terminalExecutionAssetIds.has(asset.asset_id)
      && !unacceptedContractDriftIds.has(asset.asset_id)
      && analysisMatchesCurrentContract
      && milestoneProjectionById.get(asset.asset_id)?.milestones.every((milestone) =>
        milestone.state === 'earned' || milestone.state === 'not_applicable') === true
  }).map((asset) => asset.asset_id))
  const definitionIsFrozen = Boolean(manifestAssets)
  const stageSpine = contiguousStageSpine(campaignEvents)
  const currentStage = stageSpine.currentStage
  const currentStageIndex = currentStage === null ? -1 : NIRMANA_STAGE_IDS.indexOf(currentStage)
  const freezeReceiptTimesByAsset = new Map<string, number[]>()
  for (const event of acceptedMilestoneEvents) {
    const asset = manifestById.get(event.entity_id)
    if (event.event_type !== 'asset_frozen'
      || event.entity_type !== 'asset'
      || asset?.layer !== event.layer
      || timestamp(event.observed_at) <= 0
      || timestamp(event.recorded_at) <= 0) continue
    const receiptTimes = freezeReceiptTimesByAsset.get(event.entity_id) ?? []
    receiptTimes.push(timestamp(event.recorded_at))
    receiptTimes.sort((left, right) => left - right)
    freezeReceiptTimesByAsset.set(event.entity_id, receiptTimes)
  }
  const orderedFreeze = orderedFrozenAssets(
    manifestAssets ?? [], lifecycleFrozenAssetIds, freezeReceiptTimesByAsset, stageSpine.enteredReceiptTime,
  )
  const frozenAssetIds = orderedFreeze.accepted
  const outOfOrderFreezeAssetIds = orderedFreeze.outOfOrder
  const freezeOrderContradictions = [...outOfOrderFreezeAssetIds]
    .sort((left, right) => left.localeCompare(right))
    .map((assetId) => `Asset ${assetId} has accepted freeze evidence before its governed stage/wave order is eligible; completion is withheld.`)

  for (const assetId of outOfOrderFreezeAssetIds) {
    const projection = milestoneProjectionById.get(assetId)
    if (!projection) continue
    let milestones = projection.milestones.map((milestone) => milestone.milestone_id === 'frozen'
      ? { ...milestone, state: 'pending' as const, event_type: null, accepted_at: null }
      : milestone)
    if (!milestones.some((milestone) => milestone.state === 'current')) {
      milestones = milestones.map((milestone) => milestone.milestone_id === 'frozen'
        ? { ...milestone, state: 'current' as const }
        : milestone)
    }
    milestoneProjectionById.set(assetId, {
      ...projection,
      milestones,
      milestones_earned: milestones.filter((milestone) => milestone.state === 'earned').length,
      current_action: 'Resolve freeze evidence ordering contradiction',
      next_action: null,
    })
  }

  const layerEvidence = LAYERS.map(([layer_id], order) => {
    const layerManifest = manifestAssets?.filter((asset) => asset.layer === layer_id) ?? []
    const layerAssetIds = layerManifest.map((asset) => asset.asset_id)
    return {
      layer_id,
      order,
      state: 'locked' as const,
      assets_total: manifestAssets ? layerManifest.length : null,
      optimization_reviewed: layerAssetIds.filter((assetId) => milestoneProjectionById.get(assetId)?.milestones.find((milestone) => milestone.milestone_id === 'decision_accepted')?.state === 'earned').length,
      rebuilt_or_dispositioned: layerAssetIds.filter((assetId) => terminalExecutionAssetIds.has(assetId)).length,
      verified: layerAssetIds.filter((assetId) => milestoneProjectionById.get(assetId)?.milestones.find((milestone) => milestone.milestone_id === 'verified')?.state === 'earned').length,
      frozen: layerAssetIds.filter((assetId) => frozenAssetIds.has(assetId)).length,
      waves: [],
    }
  })
  const stageProjection = projectCampaignStages({
    campaignId: definition?.campaign_id ?? 'nirmana-elevation',
    definitionRevision: definition?.definition_revision ?? 'unavailable',
    definitionStatus: definition?.definition_status ?? 'reconciling',
    events: campaignEvents,
    layers: layerEvidence,
  })
  const runAuthorizations = acceptedRunAuthorizations(raw, campaignEvents, manifest)
  const stageContradictions = [
    ...stageProjection.contradictions,
    ...stageSpine.contradictions,
    ...runAuthorizations.contradictions,
    ...freezeOrderContradictions,
  ]
  const completedStages = new Set<NirmanaStageId>()
  let priorStageComplete = true
  for (const stageId of NIRMANA_STAGE_IDS) {
    const stage = stageProjection.stages.find((candidate) => candidate.stage_id === stageId)!
    const layer = layerEvidence.find((candidate) => candidate.layer_id === stageId)
    const gateSatisfied = stageId === 'DENOMINATOR_FROZEN' ? definitionIsFrozen
      : stageId === 'F0_FOUNDATION' ? stage.earned === stage.required && stage.required === 5
        : layer ? layer.assets_total !== null && layer.frozen === layer.assets_total : true
    const reached = currentStageIndex >= NIRMANA_STAGE_IDS.indexOf(stageId)
    const transitionedOut = stageSpine.exitedAt.has(stageId)
    const complete: boolean = stageId === 'COMPLETE' ? reached && priorStageComplete : priorStageComplete && gateSatisfied && transitionedOut
    if (transitionedOut && (!priorStageComplete || !gateSatisfied)) {
      stageContradictions.push(`Accepted transition left ${stageId} before its governed completion evidence was satisfied.`)
    }
    if (complete) completedStages.add(stageId)
    priorStageComplete = complete
  }
  const stages = stageProjection.stages.map((stage) => {
    const completed = completedStages.has(stage.stage_id)
    const active = currentStage === stage.stage_id && !completed
    const blocked = active && stageContradictions.length > 0
    return {
      ...stage,
      state: completed ? 'completed' as const : blocked ? 'blocked' as const : active ? 'active' as const
        : currentStageIndex >= 0 && stage.order > currentStageIndex ? 'locked' as const : 'unknown' as const,
      completed_at: completed
        ? stage.stage_id === 'COMPLETE' ? stageSpine.enteredAt.get(stage.stage_id) ?? null : stageSpine.exitedAt.get(stage.stage_id) ?? null
        : null,
      blocked_reason: blocked ? stageContradictions.join(' ') : null,
    }
  })
  const current_layer = currentStage && LAYERS.some(([layerId]) => layerId === currentStage)
    ? currentStage as (typeof LAYERS)[number][0] : null
  const currentLayerManifest = current_layer ? manifestAssets?.filter((asset) => asset.layer === current_layer) ?? [] : []
  const unfinishedWaveIndexes = currentLayerManifest.filter((asset) => !frozenAssetIds.has(asset.asset_id))
    .map((asset) => asset.wave_index).filter((waveIndex): waveIndex is number => waveIndex !== undefined)
  const current_wave = unfinishedWaveIndexes.length > 0 ? Math.min(...unfinishedWaveIndexes) : null

  const scopedRunIds = new Set([...runAuthorizations.byRunId]
    .filter(([, authorization]) => authorization.layer === current_layer && authorization.waveIndex === current_wave)
    .map(([runId]) => runId))
  const activeRuns = activeRunsForChart(raw, manifest?.chart_id, scopedRunIds)
  const activeRunById = new Map(activeRuns.map((run) => [run.id, run]))
  const runAssetById = currentRunAssetsById(raw, activeRuns)
  const terminalFailureByAsset = latestTerminalFailuresByAsset(raw, manifest?.chart_id, scopedRunIds)
  const blockedAssetIds = new Set((manifestAssets ?? []).filter((asset) => asset.execution_obligation === 'unresolved'
    || unacceptedContractDriftIds.has(asset.asset_id)
    || staleAcceptedAnalysisIds.has(asset.asset_id)
    || runAssetById.get(asset.asset_id)?.state === 'error'
    || terminalFailureByAsset.has(asset.asset_id)
    || outOfOrderFreezeAssetIds.has(asset.asset_id)).map((asset) => asset.asset_id))
  const eligibleNextAssetIds = current_layer && stages.find((stage) => stage.stage_id === current_layer)?.state === 'active'
    ? deriveEligibleNextAssetIds({ manifestAssets: manifestAssets ?? [], frozenAssetIds, blockedAssetIds, currentLayer: current_layer, currentWave: current_wave })
    : []
  const eligibleSet = new Set(eligibleNextAssetIds)
  const activeAssetIds = new Set([...runAssetById]
    .filter(([, runAsset]) => ['planned', 'building', 'running', 'paused'].includes(runAsset.state))
    .map(([assetId]) => assetId))
  const campaignStateById = new Map((manifestAssets ?? []).map((asset) => {
    if (frozenAssetIds.has(asset.asset_id)) return [asset.asset_id, 'completed' as const]
    if (blockedAssetIds.has(asset.asset_id)) return [asset.asset_id, 'blocked' as const]
    if (asset.layer === current_layer && asset.wave_index === current_wave) {
      return [asset.asset_id, activeAssetIds.has(asset.asset_id) ? 'active' as const : 'unknown' as const]
    }
    const layerStage = stages.find((stage) => stage.stage_id === asset.layer)
    if (layerStage?.state === 'locked' || (asset.layer === current_layer && current_wave !== null && (asset.wave_index ?? -1) > current_wave)) {
      return [asset.asset_id, 'locked' as const]
    }
    return [asset.asset_id, 'unknown' as const]
  }))

  const unlocksById = new Map<string, string[]>()
  for (const manifestAsset of manifestAssets ?? []) {
    for (const dependencyId of manifestAsset.depends_on ?? []) {
      const unlocks = unlocksById.get(dependencyId) ?? []
      unlocks.push(manifestAsset.asset_id)
      unlocksById.set(dependencyId, unlocks)
    }
  }
  for (const unlocks of unlocksById.values()) unlocks.sort((left, right) => left.localeCompare(right))
  const throughputById = runtimeThroughputById(raw, registryById, manifest?.chart_id)
  const substepsById = new Map(raw.build_substep_progress
    .filter((entry) => manifest?.chart_id !== undefined && entry.chart_id === manifest.chart_id)
    .map((entry) => [entry.asset_id, entry]))
  const assets = raw.asset_registry.map((asset) => {
    const layer = layerIdForRegistry(asset.layer)
    if (!layer) throw new Error(`Unsupported Nirmana registry layer ${asset.layer} for ${asset.asset_id}.`)
    const manifestAsset = manifestById.get(asset.asset_id)
    const milestoneProjection = manifestAsset ? milestoneProjectionById.get(asset.asset_id)! : {
      milestones: NIRMANA_MILESTONE_IDS.map((milestone_id) => ({ milestone_id, state: 'pending' as const, event_type: null, accepted_at: null })),
      milestones_earned: null, milestones_required: null, current_action: null, next_action: null, inherited_from_asset_id: null,
    }
    const runAsset = runAssetById.get(asset.asset_id)
    const run = runAsset ? activeRunById.get(runAsset.run_id) : undefined
    const contractBlocker = unacceptedContractDriftIds.has(asset.asset_id)
      ? 'Live registry contract changed after the frozen T0 definition and has no matching asset_analysis_accepted fingerprint.'
      : staleAcceptedAnalysisIds.has(asset.asset_id)
        ? 'The accepted asset analysis fingerprint is stale relative to the current live registry contract.'
        : null
    const terminalFailure = terminalFailureByAsset.get(asset.asset_id)
    const blocker = contractBlocker ?? (manifestAsset?.execution_obligation === 'unresolved' ? 'Execution obligation is unresolved.'
      : runAsset?.error ? `Accepted campaign run ${runAsset.run_id} recorded an asset failure.`
        : terminalFailure && run ? `Accepted campaign run ${terminalFailure.run_id} ended with an asset failure; retry run ${run.id} is ${run.state}.`
          : terminalFailure ? `Accepted campaign run ${terminalFailure.run_id} ended with an asset failure.`
            : outOfOrderFreezeAssetIds.has(asset.asset_id) ? 'Accepted freeze evidence conflicts with governed stage or wave order.' : null)
    const acceptedLabel = labelSelection.labelsById.get(asset.asset_id)
    const english_name = acceptedLabel?.english_name ?? asset.english_name ?? asset.asset_id
    const identity_quality = !acceptedLabel || acceptedLabel.english_name === null ? 'unversioned_fallback' as const
      : acceptedLabel.sanskrit_name && acceptedLabel.description ? 'complete' as const : 'incomplete' as const
    const substeps = substepsById.get(asset.asset_id)
    const liveRegistryFingerprint = liveRegistryFingerprintByAsset.get(asset.asset_id)
    const acceptedAnalysisFingerprint = acceptedAnalysisFingerprintByAsset.get(asset.asset_id)
    const acceptedAnalysisDigest = acceptedAnalysisDigestByAsset.get(asset.asset_id)
    const evidence_refs = [
      ...campaignEvents.filter((event) => event.entity_type === 'asset' && event.entity_id === asset.asset_id && event.layer === layer).map((event) => sanitizedReference(event.source_ref)),
      ...(acceptedLabel?.source_ref ? [sanitizedReference(acceptedLabel.source_ref)] : []),
      ...(manifestAsset ? [`registry:t0:${manifestAsset.registry_fingerprint_sha256}`] : []),
      ...(liveRegistryFingerprint ? [`registry:live:${liveRegistryFingerprint}`] : []),
      ...(acceptedAnalysisFingerprint ? [`registry:accepted:${acceptedAnalysisFingerprint}`] : []),
      ...(acceptedAnalysisDigest ? [`analysis:sha256:${acceptedAnalysisDigest}`] : []),
    ]
    return {
      asset_id: asset.asset_id,
      display_name: english_name,
      sanskrit_name: acceptedLabel?.sanskrit_name ?? null,
      english_name,
      description: acceptedLabel?.description ?? null,
      legacy_aliases: acceptedLabel?.legacy_aliases ?? [],
      identity_quality,
      layer,
      campaign_state: campaignStateById.get(asset.asset_id) ?? 'unknown',
      wave_index: manifestAsset?.wave_index ?? null,
      producer_id: manifestAsset?.producer_id ?? null,
      covered_asset_ids: manifestAsset?.covered_asset_ids ?? [],
      execution_obligation: manifestAsset?.execution_obligation ?? 'unresolved',
      lifecycle_state: !manifestAsset ? 'unverified' : contractBlocker ? 'blocked' : frozenAssetIds.has(asset.asset_id) ? 'frozen'
        : milestoneProjection.milestones.find((milestone) => milestone.milestone_id === 'verified')?.state === 'earned' ? 'verifying'
          : acceptedBuildAssetIds.has(asset.asset_id) ? 'rebuilt' : terminalExecutionAssetIds.has(asset.asset_id) ? 'dispositioned' : 'catalogued',
      readiness_state: throughputById.get(asset.asset_id)?.state ?? 'unknown',
      current_run_state: runAsset?.state ?? null,
      progress_mode: runAsset?.state === 'building' ? 'indeterminate' as const : 'not_applicable' as const,
      work_committed: null,
      work_total: null,
      current_unit_label: runAsset?.state === 'building'
        ? substeps ? `Historical resumable work: ${substeps.committed} committed substeps` : 'execution in progress' : null,
      baseline_duration_seconds: null,
      final_duration_seconds: null,
      improvement_percent: null,
      blocker,
      evidence_refs,
      milestones: milestoneProjection.milestones,
      milestones_earned: milestoneProjection.milestones_earned,
      milestones_required: milestoneProjection.milestones_required,
      current_action: runAsset ? `Accepted campaign run: ${runAsset.state}` : milestoneProjection.current_action,
      next_action: milestoneProjection.next_action,
      depends_on: manifestAsset?.depends_on ?? asset.depends_on ?? [],
      unlocks: unlocksById.get(asset.asset_id) ?? [],
    }
  })
  const campaignAssetById = new Map(assets.map((asset) => [asset.asset_id, asset]))
  const baseLayers = layerEvidence.map((layer) => {
    const layerManifest = manifestAssets?.filter((asset) => asset.layer === layer.layer_id) ?? []
    const waves = [...new Set(layerManifest.map((asset) => asset.wave_index).filter((value): value is number => value != null))]
      .sort((left, right) => left - right)
      .map((wave_index) => {
        const asset_ids = layerManifest.filter((asset) => asset.wave_index === wave_index).map((asset) => asset.asset_id)
        const partition = (state: 'completed' | 'active' | 'blocked' | 'locked' | 'unknown') => asset_ids.filter((assetId) => campaignAssetById.get(assetId)?.campaign_state === state)
        const completed_asset_ids = partition('completed')
        const active_asset_ids = partition('active')
        const blocked_asset_ids = partition('blocked')
        const locked_asset_ids = partition('locked')
        const unknown_asset_ids = partition('unknown')
        const state = completed_asset_ids.length === asset_ids.length ? 'completed' as const
          : blocked_asset_ids.length > 0 ? 'blocked' as const
            : active_asset_ids.length > 0 ? 'active' as const
              : locked_asset_ids.length === asset_ids.length ? 'locked' as const : 'unknown' as const
        return {
          wave_index, state, asset_ids, completed_asset_ids, active_asset_ids, blocked_asset_ids,
          locked_asset_ids, unknown_asset_ids,
          eligible_next_asset_ids: asset_ids.filter((assetId) => eligibleSet.has(assetId)),
        }
      })
    return { ...layer, waves }
  })
  const layers = baseLayers.map((layer) => {
    const layerStage = stages.find((stage) => stage.stage_id === layer.layer_id)!
    const isCurrent = layer.layer_id === current_layer
    return {
      ...layer,
      state: layerStage.state === 'completed' ? 'frozen' as const
        : isCurrent && layerStage.state === 'blocked' ? 'blocked' as const
          : isCurrent ? 'open' as const : currentStage === null ? 'unknown' as const : 'locked' as const,
      layer_name: NIRMANA_LAYER_NAMES[layer.layer_id],
      required_gate: layerStage.required_gate,
      eligible_next_asset_ids: isCurrent ? eligibleNextAssetIds : [],
    }
  })
  const active_runs = activeRuns.map((run) => {
    const authorization = runAuthorizations.byRunId.get(run.id.toLowerCase())!
    const runAssets = raw.build_run_assets.filter((asset) => asset.run_id === run.id)
    const active_asset_ids = runAssets.filter((asset) => ['planned', 'building', 'running', 'paused'].includes(asset.state)).map((asset) => asset.asset_id)
    const latestProgress = runAssets.map((asset) => asset.ended_at ?? asset.started_at).filter((value): value is string => Boolean(value)).sort().at(-1) ?? run.started_at
    return {
      run_id: run.id,
      layer: authorization.layer,
      wave_index: authorization.waveIndex,
      state: run.state,
      active_asset_ids,
      completed_assets: runAssets.filter((asset) => asset.state === 'complete' || asset.state === 'skipped').length,
      planned_assets: runAssets.length,
      started_at: asIso(run.started_at),
      last_progress_at: asIso(latestProgress),
    }
  })

  const unversionedIdentityCount = assets.filter((asset) => asset.identity_quality === 'unversioned_fallback').length
  const gaps = [
    ...(definitionIsFrozen ? [] : ['Campaign denominator is reconciling; totals and percentages are withheld.']),
    ...(unacceptedContractDriftIds.size === 0 ? [] : [`${unacceptedContractDriftIds.size} asset registry contract${unacceptedContractDriftIds.size === 1 ? ' has' : 's have'} changed without a matching accepted analysis fingerprint.`]),
    ...(staleAcceptedAnalysisIds.size === 0 ? [] : [`${staleAcceptedAnalysisIds.size} accepted asset analysis fingerprint${staleAcceptedAnalysisIds.size === 1 ? ' is' : 's are'} stale relative to the live registry contract.`]),
    ...(currentStage === null ? ['No contiguous accepted campaign-stage spine is available; current position is withheld.'] : []),
    ...(unversionedIdentityCount > 0 ? [`${unversionedIdentityCount} asset identities use unversioned asset_registry fallback because no matching accepted catalogue label is available.`] : []),
    ...(releaseStatus?.gaps ?? ['Release reconciliation is not yet connected to an authoritative deployment source.']),
    ...programProjection.gaps,
  ]
  const sources = [
    ...(Object.entries(SOURCE_PROVENANCE) as Array<[SourceId, string]>)
      .filter(([source_id]) => source_id !== 'program_monitor')
      .map(([source_id, provenance]) => ({
      source_id, provenance, state: 'fresh' as const, observed_at: generated_at, age_seconds: 0,
      error_code: null, error_message: null,
      })),
    programProjection.source,
    ...(releaseStatus?.sources ?? []),
  ]
  const contradictions = [
    ...labelSelection.contradictions,
    ...stageContradictions,
    ...[...new Set([...unacceptedContractDriftIds, ...staleAcceptedAnalysisIds])].sort(),
  ]
  const release = releaseStatus?.release
    ?? { main_sha: null, deployed_sha: null, deployed_revision: null, production_in_sync: null, observed_at: null }
  const progress = {
    denominator_status: definitionIsFrozen ? 'frozen' as const : 'reconciling' as const,
    assets_total: manifestAssets?.length ?? null,
    assets_frozen: frozenAssetIds.size,
    layers_total: 6 as const,
    layers_frozen: layers.filter((layer) => layer.state === 'frozen').length,
    buildable_assets_total: manifestAssets?.filter((asset) => asset.execution_obligation === 'build').length ?? null,
    accepted_rebuilds: acceptedBuildAssetIds.size,
  }
  const campaign_status = definition?.definition_status === 'superseded' ? 'paused' as const
    : stageContradictions.length > 0 ? 'blocked' as const : currentStage === null ? 'unknown' as const
      : currentStage === 'COMPLETE' ? 'completed' as const : currentStage === 'F0_FOUNDATION' ? 'foundation' as const
        : ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'CLOSING'].includes(currentStage) ? 'running' as const : 'takeover' as const
  const campaign = {
    campaign_id: definition?.campaign_id ?? 'nirmana-elevation',
    definition_revision: definition?.definition_revision ?? null,
    definition_status: definition?.definition_status ?? 'reconciling' as const,
    campaign_status,
    current_stage: currentStage,
    current_layer,
    current_wave,
  }
  const data_quality = { verdict: contradictions.length || gaps.length ? 'degraded' as const : 'reliable' as const, gaps, contradictions }
  const generation = digest({
    campaign, progress, stages, layers, assets, active_runs, program_sync: programProjection.programSync,
    audit: { accepted_label_catalogue_revision: labelSelection.acceptedCatalogueRevision, release, sources, data_quality, receipts: audit.receipts, raw_ledger_refs: audit.raw_ledger_refs },
  })
  return NirmanaElevationSnapshotV2Schema.parse({
    schema_version: '2.0', generation, generated_at,
    campaign, progress, stages, layers, assets, active_runs, release, sources,
    program_sync: programProjection.programSync, data_quality, audit,
  })
}

export function unavailableNirmanaElevationSnapshot(error: NirmanaElevationSourceError, { generatedAt = new Date().toISOString() }: { generatedAt?: string } = {}): NirmanaElevationSnapshotV2 {
  const generated_at = new Date(generatedAt).toISOString()
  const sourceIds = Object.keys(SOURCE_PROVENANCE) as SourceId[]
  const baseLayers = LAYERS.map(([layer_id], order) => ({
    layer_id, order, state: 'unknown', assets_total: null, optimization_reviewed: 0,
    rebuilt_or_dispositioned: 0, verified: 0, frozen: 0, waves: [],
  }))
  const stageProjection = projectCampaignStages({
    campaignId: 'nirmana-elevation', definitionRevision: 'unavailable', definitionStatus: 'reconciling',
    events: [], layers: baseLayers,
  })
  const stages = stageProjection.stages
  const layers = baseLayers.map((layer) => ({
    ...layer,
    layer_name: NIRMANA_LAYER_NAMES[layer.layer_id],
    required_gate: stages.find((stage) => stage.stage_id === layer.layer_id)?.required_gate
      ?? `${layer.layer_id} assets frozen`,
    eligible_next_asset_ids: [],
  }))
  const sources = sourceIds.map((source_id) => ({
    source_id,
    provenance: SOURCE_PROVENANCE[source_id],
    state: source_id === error.sourceId ? 'unavailable' as const : 'unknown' as const,
    observed_at: null,
    age_seconds: null,
    error_code: source_id === error.sourceId ? error.publicCode : null,
    error_message: source_id === error.sourceId ? error.publicMessage : null,
  }))
  const data_quality = {
    verdict: 'degraded' as const,
    gaps: [`Authoritative source ${error.sourceId} is unavailable; no empty-state conclusion is valid.`],
    contradictions: [],
  }
  const audit = { receipts: [], raw_ledger_refs: [] }
  const program_sync: NirmanaElevationSnapshotV2['program_sync'] = {
    status: error.sourceId === 'program_monitor' ? 'source_unavailable' : 'unknown',
    source_observation_id: null,
    observed_at: null,
    age_seconds: null,
    affected_asset_ids: [],
    current_definition_sha256: null,
    candidate_definition_sha256: null,
    candidate_catalogue_sha256: null,
  }
  const generation = digest({ unavailable: error.sourceId, code: error.publicCode, stages, layers, sources, program_sync, data_quality, audit })
  return NirmanaElevationSnapshotV2Schema.parse({
    schema_version: '2.0', generation, generated_at,
    campaign: { campaign_id: 'nirmana-elevation', definition_revision: null, definition_status: 'reconciling', campaign_status: 'unknown', current_stage: null, current_layer: null, current_wave: null },
    progress: { denominator_status: 'reconciling', assets_total: null, assets_frozen: 0, layers_total: 6, layers_frozen: 0, buildable_assets_total: null, accepted_rebuilds: 0 },
    stages, layers, assets: [], active_runs: [],
    release: { main_sha: null, deployed_sha: null, deployed_revision: null, production_in_sync: null, observed_at: null },
    sources, program_sync, data_quality, audit,
  })
}

export {
  NIRMANA_LAYER_NAMES,
  NIRMANA_STAGE_IDS,
  NirmanaElevationSnapshotSchema,
  NirmanaElevationSnapshotV2Schema,
  type NirmanaElevationSnapshot,
  type NirmanaElevationSnapshotV2,
} from './types'
