import { createHash } from 'node:crypto'
import { query } from '@/lib/db/client'
import { canonicalManifestDigest, parseNirmanaElevationManifest, type NirmanaElevationManifest } from './definitions'
import { NirmanaElevationSnapshotSchema, type NirmanaElevationSnapshot } from './types'

const LAYERS = [
  ['L0', 'brahmagyan'], ['L1', 'ganita'], ['L2', 'bodha'],
  ['L3', 'kala'], ['L4', 'phala'], ['L5', 'mimamsa'],
] as const

type SourceId = keyof NirmanaElevationRawSources

export interface NirmanaElevationRawSources {
  asset_registry: Array<{ asset_id: string; english_name: string | null; layer: string; sort_order: number; has_writer: boolean | null; asset_type: string | null; asset_kind: string | null; is_active: boolean; depends_on: string[] | null }>
  asset_throughput: Array<{ asset_id: string; state: string; last_built_at: string | null }>
  build_runs: Array<{ id: string; state: string; current_asset_id: string | null; created_at: string; started_at: string | null }>
  build_run_assets: Array<{ run_id: string; asset_id: string; position: number; state: string; started_at: string | null; ended_at: string | null; error: string | null }>
  build_substep_progress: Array<{ asset_id: string; committed: string | number; last_progress_at: string | null }>
  campaign_definitions: Array<{ campaign_id: string; definition_revision: string; definition_status: 'reconciling' | 'frozen' | 'superseded'; manifest: unknown; manifest_sha256: string; created_at: string }>
  campaign_events: Array<{ campaign_id: string; definition_revision: string; event_type: string; entity_type: string; entity_id: string; layer: string | null; evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>
}

type ManifestAsset = NirmanaElevationManifest['assets'][number]

export class NirmanaElevationSourceError extends Error {
  constructor(readonly sourceId: SourceId, cause: unknown) {
    super(cause instanceof Error ? cause.message : 'source query failed')
  }
}

async function loadSource<K extends SourceId>(sourceId: K, sql: string): Promise<Pick<NirmanaElevationRawSources, K>> {
  try {
    const { rows } = await query(sql)
    return { [sourceId]: rows } as Pick<NirmanaElevationRawSources, K>
  } catch (error) {
    throw new NirmanaElevationSourceError(sourceId, error)
  }
}

/** Only primary build tables plus tracker-owned evidence tables feed this projection. */
export async function loadNirmanaElevationRawSources(): Promise<NirmanaElevationRawSources> {
  const registry = await loadSource('asset_registry', `SELECT asset_id, english_name, layer, sort_order, has_writer, asset_type, asset_kind, is_active, COALESCE(depends_on, '{}') AS depends_on FROM asset_registry WHERE is_active = true ORDER BY layer, sort_order, asset_id`)
  const throughput = await loadSource('asset_throughput', `SELECT DISTINCT ON (asset_id) asset_id, state, last_built_at FROM asset_throughput ORDER BY asset_id, last_built_at DESC NULLS LAST`)
  const runs = await loadSource('build_runs', `SELECT id, state, current_asset_id, created_at, started_at FROM build_runs ORDER BY created_at DESC`)
  const runAssets = await loadSource('build_run_assets', `SELECT run_id, asset_id, position, state, started_at, ended_at, error FROM build_run_assets ORDER BY run_id, position`)
  const substeps = await loadSource('build_substep_progress', `SELECT bsp.asset_id, COUNT(*)::text AS committed, MAX(bsp.completed_at) AS last_progress_at FROM build_substep_progress bsp WHERE EXISTS (SELECT 1 FROM build_runs br WHERE br.chart_id = bsp.chart_id AND br.state IN ('planned', 'running', 'paused')) GROUP BY bsp.asset_id`)
  const definitions = await loadSource('campaign_definitions', `SELECT campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_at FROM nirmana_elevation_campaign_definitions WHERE campaign_id = 'nirmana-elevation' AND superseded_at IS NULL ORDER BY created_at DESC LIMIT 1`)
  const events = await loadSource('campaign_events', `SELECT campaign_id, definition_revision, event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref, observed_at, recorded_at FROM nirmana_elevation_campaign_events WHERE campaign_id = 'nirmana-elevation' ORDER BY recorded_at ASC`)
  return { ...registry, ...throughput, ...runs, ...runAssets, ...substeps, ...definitions, ...events }
}

function digest(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex')
}

function asIso(value: string | null | undefined): string | null {
  return value && !Number.isNaN(Date.parse(value)) ? new Date(value).toISOString() : null
}

function validManifest(definition: NirmanaElevationRawSources['campaign_definitions'][number] | undefined, registryIds: Set<string>): ManifestAsset[] | null {
  if (!definition || definition.definition_status !== 'frozen') return null
  const parsed = parseNirmanaElevationManifest(definition.manifest)
  if (!parsed) return null
  if (canonicalManifestDigest(parsed) !== definition.manifest_sha256) return null
  const ids = parsed.assets.map((asset) => asset.asset_id)
  if (new Set(ids).size !== ids.length || ids.some((id) => !registryIds.has(id))) return null
  return parsed.assets
}

export function projectNirmanaElevationSnapshot(raw: NirmanaElevationRawSources, { generatedAt = new Date().toISOString() }: { generatedAt?: string } = {}): NirmanaElevationSnapshot {
  const generated_at = new Date(generatedAt).toISOString()
  const definition = raw.campaign_definitions[0]
  const registryById = new Map(raw.asset_registry.map((asset) => [asset.asset_id, asset]))
  const manifestAssets = validManifest(definition, new Set(registryById.keys()))
  const manifestById = new Map((manifestAssets ?? []).map((asset) => [asset.asset_id, asset]))
  const throughputById = new Map(raw.asset_throughput.map((entry) => [entry.asset_id, entry]))
  const runAssetById = new Map(raw.build_run_assets.map((entry) => [entry.asset_id, entry]))
  const substepsById = new Map(raw.build_substep_progress.map((entry) => [entry.asset_id, entry]))
  const campaignEvents = definition ? raw.campaign_events.filter((event) => event.definition_revision === definition.definition_revision) : []
  const eventTypesByAsset = new Map<string, Set<string>>()
  for (const event of campaignEvents) {
    const types = eventTypesByAsset.get(event.entity_id) ?? new Set<string>()
    types.add(event.event_type)
    eventTypesByAsset.set(event.entity_id, types)
  }
  const completedRunAssets = new Set(
    raw.build_run_assets
      .filter((asset) => asset.state === 'complete')
      .map((asset) => `${asset.run_id}:${asset.asset_id}`),
  )
  const acceptedRebuildAssetIds = new Set(
    campaignEvents
      .filter((event) => event.event_type === 'accepted_rebuild_observed')
      .filter((event) => {
        const runId = event.source_ref.startsWith('build_run:') ? event.source_ref.slice('build_run:'.length) : null
        return runId !== null && completedRunAssets.has(`${runId}:${event.entity_id}`)
      })
      .map((event) => event.entity_id),
  )
  const frozenAssetIds = new Set(
    manifestAssets?.filter((asset) => {
      const types = eventTypesByAsset.get(asset.asset_id) ?? new Set<string>()
      return acceptedRebuildAssetIds.has(asset.asset_id)
        && throughputById.get(asset.asset_id)?.state === 'lit'
        && ['asset_analysis_accepted', 'optimization_verdict_accepted', 'integrity_verified', 'asset_frozen'].every((type) => types.has(type))
    }).map((asset) => asset.asset_id) ?? [],
  )

  const assets = raw.asset_registry.map((asset) => {
    const manifest = manifestById.get(asset.asset_id)
    const runAsset = runAssetById.get(asset.asset_id)
    const throughput = throughputById.get(asset.asset_id)
    const eventRefs = campaignEvents.filter((event) => event.entity_id === asset.asset_id).map((event) => event.source_ref)
    const substeps = substepsById.get(asset.asset_id)
    return {
      asset_id: asset.asset_id,
      display_name: asset.english_name || asset.asset_id,
      layer: LAYERS.find(([, sourceLayer]) => sourceLayer === asset.layer)?.[0] ?? asset.layer,
      wave_index: manifest?.wave_index ?? null,
      producer_id: manifest?.producer_id ?? null,
      covered_asset_ids: manifest?.covered_asset_ids ?? [],
      execution_obligation: manifest?.execution_obligation ?? 'unresolved',
      lifecycle_state: !manifest ? 'unverified'
        : frozenAssetIds.has(asset.asset_id) ? 'frozen'
          : eventTypesByAsset.get(asset.asset_id)?.has('integrity_verified') ? 'verifying'
            : acceptedRebuildAssetIds.has(asset.asset_id) ? 'rebuilt'
              : 'catalogued',
      readiness_state: throughput?.state ?? 'unknown',
      current_run_state: runAsset?.state ?? null,
      progress_mode: runAsset?.state === 'building' ? 'indeterminate' : 'not_applicable',
      work_committed: null,
      work_total: null,
      current_unit_label: runAsset?.state === 'building' ? (substeps ? `${substeps.committed} committed substeps` : 'execution in progress') : null,
      baseline_duration_seconds: null,
      final_duration_seconds: null,
      improvement_percent: null,
      blocker: runAsset?.error ?? null,
      evidence_refs: eventRefs,
    } as const
  })

  const layers = LAYERS.map(([layer_id], order) => {
    const layerManifest = manifestAssets?.filter((asset) => asset.layer === layer_id) ?? []
    const waves = [...new Set(layerManifest.map((asset) => asset.wave_index).filter((value): value is number => value != null))].sort((a, b) => a - b).map((wave_index) => {
      const asset_ids = layerManifest.filter((asset) => asset.wave_index === wave_index).map((asset) => asset.asset_id)
      const active_asset_ids = asset_ids.filter((assetId) => runAssetById.get(assetId)?.state === 'building')
      const blocked_asset_ids = asset_ids.filter((assetId) => runAssetById.get(assetId)?.state === 'error')
      return { wave_index, state: active_asset_ids.length ? 'running' : blocked_asset_ids.length ? 'blocked' : 'pending', asset_ids, active_asset_ids, blocked_asset_ids }
    })
    const layerAssetIds = new Set(layerManifest.map((asset) => asset.asset_id))
    const frozen = [...layerAssetIds].filter((assetId) => frozenAssetIds.has(assetId)).length
    const rebuilt_or_dispositioned = [...layerAssetIds].filter((assetId) => acceptedRebuildAssetIds.has(assetId)).length
    const verified = [...layerAssetIds].filter((assetId) => eventTypesByAsset.get(assetId)?.has('integrity_verified')).length
    const optimization_reviewed = [...layerAssetIds].filter((assetId) => eventTypesByAsset.get(assetId)?.has('optimization_verdict_accepted')).length
    return { layer_id, order, state: layerManifest.length > 0 && frozen === layerManifest.length ? 'frozen' as const : 'locked' as const, assets_total: manifestAssets ? layerManifest.length : null, optimization_reviewed, rebuilt_or_dispositioned, verified, frozen, waves }
  })

  const active_runs = raw.build_runs.filter((run) => ['planned', 'running', 'paused'].includes(run.state)).map((run) => {
    const runAssets = raw.build_run_assets.filter((asset) => asset.run_id === run.id)
    const active_asset_ids = runAssets.filter((asset) => asset.state === 'building').map((asset) => asset.asset_id)
    const timestamp = runAssets.map((asset) => asset.ended_at ?? asset.started_at).filter((value): value is string => Boolean(value)).sort().at(-1) ?? run.started_at
    const currentAsset = run.current_asset_id ? registryById.get(run.current_asset_id) : undefined
    return { run_id: run.id, layer: currentAsset ? (LAYERS.find(([, sourceLayer]) => sourceLayer === currentAsset.layer)?.[0] ?? currentAsset.layer) : null, wave_index: run.current_asset_id ? manifestById.get(run.current_asset_id)?.wave_index ?? null : null, state: run.state, active_asset_ids, completed_assets: runAssets.filter((asset) => asset.state === 'complete' || asset.state === 'skipped').length, planned_assets: runAssets.length, started_at: asIso(run.started_at), last_progress_at: asIso(timestamp) }
  })

  const definitionIsFrozen = Boolean(manifestAssets)
  const gaps = [
    ...(definitionIsFrozen ? [] : ['Campaign denominator is reconciling; totals and percentages are withheld.']),
    'Release reconciliation is not yet connected to an authoritative deployment source.',
  ]
  const semantic = { campaign: definition ? { campaign_id: definition.campaign_id, definition_revision: definition.definition_revision, definition_status: definition.definition_status } : { campaign_id: 'nirmana-elevation', definition_revision: null, definition_status: 'reconciling' }, raw, assets, layers, active_runs }
  const generation = digest(semantic)
  return NirmanaElevationSnapshotSchema.parse({
    schema_version: '1.0', generation, generated_at,
    campaign: { campaign_id: definition?.campaign_id ?? 'nirmana-elevation', definition_revision: definition?.definition_revision ?? null, definition_status: definition?.definition_status ?? 'reconciling', campaign_status: definitionIsFrozen ? 'foundation' : 'takeover', current_layer: null, current_wave: null },
    progress: { denominator_status: definitionIsFrozen ? 'frozen' : 'reconciling', assets_total: manifestAssets?.length ?? null, assets_frozen: frozenAssetIds.size, layers_total: 6, layers_frozen: layers.filter((layer) => layer.state === 'frozen').length, buildable_assets_total: manifestAssets?.filter((asset) => asset.execution_obligation === 'build').length ?? null, accepted_rebuilds: acceptedRebuildAssetIds.size },
    layers, assets, active_runs,
    release: { main_sha: null, deployed_sha: null, deployed_revision: null, production_in_sync: null, observed_at: null },
    sources: [
      ['asset_registry', 'Cloud SQL asset_registry'], ['asset_throughput', 'Cloud SQL asset_throughput'], ['build_runs', 'Cloud SQL build_runs'], ['build_run_assets', 'Cloud SQL build_run_assets'], ['build_substep_progress', 'Cloud SQL build_substep_progress'], ['campaign_definitions', 'Cloud SQL nirmana_elevation_campaign_definitions'], ['campaign_events', 'Cloud SQL nirmana_elevation_campaign_events'],
    ].map(([source_id, provenance]) => ({ source_id, provenance, state: 'fresh' as const, observed_at: generated_at, age_seconds: 0, error: null })),
    data_quality: { verdict: gaps.length ? 'degraded' : 'reliable', gaps, contradictions: [] },
  })
}

export function unavailableNirmanaElevationSnapshot(error: NirmanaElevationSourceError, { generatedAt = new Date().toISOString() }: { generatedAt?: string } = {}): NirmanaElevationSnapshot {
  const generated_at = new Date(generatedAt).toISOString()
  const sourceIds: SourceId[] = ['asset_registry', 'asset_throughput', 'build_runs', 'build_run_assets', 'build_substep_progress', 'campaign_definitions', 'campaign_events']
  const generation = digest({ unavailable: error.sourceId, message: error.message })
  return NirmanaElevationSnapshotSchema.parse({
    schema_version: '1.0', generation, generated_at,
    campaign: { campaign_id: 'nirmana-elevation', definition_revision: null, definition_status: 'reconciling', campaign_status: 'unknown', current_layer: null, current_wave: null },
    progress: { denominator_status: 'reconciling', assets_total: null, assets_frozen: 0, layers_total: 6, layers_frozen: 0, buildable_assets_total: null, accepted_rebuilds: 0 },
    layers: LAYERS.map(([layer_id], order) => ({ layer_id, order, state: 'unknown', assets_total: null, optimization_reviewed: 0, rebuilt_or_dispositioned: 0, verified: 0, frozen: 0, waves: [] })),
    assets: [], active_runs: [],
    release: { main_sha: null, deployed_sha: null, deployed_revision: null, production_in_sync: null, observed_at: null },
    sources: sourceIds.map((source_id) => ({ source_id, provenance: source_id.startsWith('campaign_') ? 'Cloud SQL campaign evidence' : `Cloud SQL ${source_id}`, state: source_id === error.sourceId ? 'unavailable' as const : 'unknown' as const, observed_at: null, age_seconds: null, error: source_id === error.sourceId ? error.message : null })),
    data_quality: { verdict: 'degraded', gaps: [`Authoritative source ${error.sourceId} is unavailable; no empty-state conclusion is valid.`], contradictions: [] },
  })
}

export { NirmanaElevationSnapshotSchema, type NirmanaElevationSnapshot } from './types'
