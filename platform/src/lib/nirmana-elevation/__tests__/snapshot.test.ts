import { describe, expect, it } from 'vitest'
import {
  NIRMANA_LAYER_NAMES,
  NIRMANA_STAGE_IDS,
  NirmanaElevationSnapshotSchema,
  NirmanaElevationSnapshotV2Schema,
  projectNirmanaElevationSnapshot,
  type NirmanaElevationRawSources,
} from '../snapshot'
import { canonicalManifestDigest, canonicalNirmanaOptimizationVerdictDigest, canonicalNirmanaRebuildEvidenceDigest, canonicalRegistryContractDigest } from '../definitions'

const observedAt = '2026-08-25T09:00:00.000Z'
const milestoneAt = '2026-08-25T09:01:00.000Z'
const canonicalChartId = '482012f1-710e-4a25-994a-93821f5871aa'
const runOne = '10101010-1010-4010-8010-101010101010'
const runTwo = '20202020-2020-4020-8020-202020202020'
const layerRunIds = {
  L0: 'a0000000-0000-4000-8000-000000000000',
  L1: 'a1111111-1111-4111-8111-111111111111',
  L2: 'a2222222-2222-4222-8222-222222222222',
  L3: 'a3333333-3333-4333-8333-333333333333',
  L4: 'a4444444-4444-4444-8444-444444444444',
  L5: 'a5555555-5555-4555-8555-555555555555',
} as const

type RegistryAsset = NirmanaElevationRawSources['asset_registry'][number]
type AssetLabelRow = {
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
}
type ManifestSpec = {
  asset_id: string
  layer?: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'
  wave_index?: number
  execution_obligation: 'build' | 'probe' | 'producer_covered' | 'static_acceptance' | 'source_acceptance' | 'empty_acceptance' | 'retired_with_disposition' | 'unresolved'
  producer_id?: string
  covered_asset_ids?: string[]
}

function registryAsset(overrides: Partial<RegistryAsset> = {}): RegistryAsset {
  return {
    asset_id: 'bg_prashna_rules', english_name: 'Prashna Rules', layer: 'brahmagyan', scope: 'per_chart',
    sort_order: 1, has_writer: true, asset_type: 'data', asset_kind: 'data', catalog_status: 'CURRENT',
    is_active: true, depends_on: [], target_table: 'bg_prashna_rules',
    count_sql: 'SELECT count(*) FROM bg_prashna_rules', integrity_check_sql: null, health_probe: null,
    natural_key_partition: null, superseded_by: null, data_disposition: null, dead_flag: null,
    ...overrides,
  }
}

function manifestFor(registry: RegistryAsset[], specs: ManifestSpec[]) {
  const registryById = new Map(registry.map((asset) => [asset.asset_id, asset]))
  return {
    chart_id: canonicalChartId,
    assets: specs.map((spec) => {
      const row = registryById.get(spec.asset_id)
      if (!row) throw new Error(`missing test registry row ${spec.asset_id}`)
      const layer = spec.layer ?? ({ brahmagyan: 'L0', ganita: 'L1', bodha: 'L2', kala: 'L3', phala: 'L4', mimamsa: 'L5' } as const)[row.layer]
      const registry_contract = {
        sort_order: row.sort_order, scope: row.scope, asset_kind: row.asset_kind, catalog_status: row.catalog_status,
        is_active: row.is_active, has_writer: row.has_writer, target_table: row.target_table, count_sql: row.count_sql,
        integrity_check_sql: row.integrity_check_sql, health_probe: row.health_probe,
        natural_key_partition: row.natural_key_partition, superseded_by: row.superseded_by,
        data_disposition: row.data_disposition, dead_flag: row.dead_flag,
      }
      const asset = {
        ...spec,
        layer,
        wave_index: spec.wave_index ?? 0,
        depends_on: row.depends_on ?? [],
        registry_contract,
      }
      return {
        ...asset,
        registry_fingerprint_sha256: canonicalRegistryContractDigest({
          asset_id: asset.asset_id, layer: asset.layer, depends_on: asset.depends_on, registry_contract,
        }),
      }
    }),
  }
}

const defaultRegistry = [registryAsset()]
const defaultManifest = () => manifestFor(defaultRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])

function sources(overrides: Partial<NirmanaElevationRawSources> = {}): NirmanaElevationRawSources {
  return {
    asset_registry: defaultRegistry,
    asset_throughput: [{ asset_id: 'bg_prashna_rules', chart_id: canonicalChartId, state: 'lit', last_built_at: observedAt }],
    build_runs: [],
    build_run_assets: [],
    build_substep_progress: [],
    campaign_definitions: [],
    campaign_events: [],
    asset_labels: [],
    monitor_observations: [],
    ...overrides,
  } as NirmanaElevationRawSources
}

type MonitorObservationRow = NonNullable<NirmanaElevationRawSources['monitor_observations']>[number]

function monitorObservation(overrides: Partial<MonitorObservationRow> = {}): MonitorObservationRow {
  return {
    id: '30303030-3030-4030-8030-303030303030',
    observed_at: observedAt,
    status: 'in_sync',
    affected_asset_ids: [],
    current_definition_sha256: 'a'.repeat(64),
    candidate_definition_sha256: 'a'.repeat(64),
    candidate_catalogue_sha256: 'b'.repeat(64),
    source_state: 'available',
    source_observed_at: observedAt,
    freshness_state: 'fresh',
    freshness_deadline_at: '2026-08-25T09:15:00.000Z',
    runtime_liveness: 'quiet',
    source_error_code: null,
    ...overrides,
  }
}

function sourcesWithLabels(
  overrides: Partial<NirmanaElevationRawSources>,
  asset_labels: AssetLabelRow[],
): NirmanaElevationRawSources {
  return { ...sources(overrides), asset_labels } as unknown as NirmanaElevationRawSources
}

function labelReceipt(catalogueRevision: string, catalogueSha256: string, assetCount = 1) {
  return {
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_label_catalogue_accepted',
    entity_type: 'label_catalogue', entity_id: catalogueRevision, layer: null,
    evidence_payload: { catalogue_sha256: catalogueSha256, asset_count: assetCount }, source_kind: 'governed_catalogue',
    source_ref: `label_catalogue:${catalogueRevision}`, observed_at: observedAt, recorded_at: observedAt,
  }
}

function foundationLaneEvents() {
  return ['A', 'B', 'C', 'D', 'E'].map((laneId) => ({
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'foundation_lane_accepted',
    entity_type: 'foundation_lane', entity_id: laneId, layer: null,
    evidence_payload: foundationPayload(laneId), source_kind: 'server_reconstructed',
    source_ref: `nirmana-elevation:foundation-lane:${laneId}`, observed_at: observedAt, recorded_at: observedAt,
  }))
}

function foundationPayload(laneId: string) {
  const base = { schema_version: 'nirmana-foundation-lane-receipt/v1' as const, lane_id: laneId, manifest_sha256: 'a'.repeat(64) }
  if (laneId === 'A') return { ...base, asset_count: 1 }
  if (laneId === 'B') return { ...base, build_run_count: 0, terminal_build_run_count: 0 }
  if (laneId === 'C') return { ...base, registry_fingerprint_set_sha256: 'b'.repeat(64), manifest_asset_count: 1, live_registry_asset_count: 1, invalidated_analysis_count: 0 }
  if (laneId === 'D') return { ...base, main_sha: 'b'.repeat(40), serving_sha: 'b'.repeat(40), serving_revision: 'amjis-web-01799-abc', ci_run_id: '123' }
  return { ...base, migration_filename: '592_nirmana_elevation_campaign_evidence.sql', migration_sha256: 'c'.repeat(64) }
}

function stageEventsThrough(stageId: (typeof NIRMANA_STAGE_IDS)[number]) {
  const targetIndex = NIRMANA_STAGE_IDS.indexOf(stageId)
  return NIRMANA_STAGE_IDS.slice(0, targetIndex + 1).map((to_stage, index) => {
    const eventAt = new Date(Date.parse(observedAt) + index * 1_000).toISOString()
    return {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'stage_transition_accepted',
      entity_type: 'campaign_stage', entity_id: to_stage, layer: null,
      evidence_payload: {
        schema_version: 'nirmana-stage-transition-receipt/v1',
        from_stage: index === 0 ? null : NIRMANA_STAGE_IDS[index - 1],
        to_stage, manifest_sha256: String(index.toString(16)).repeat(64),
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine', observed_at: eventAt, recorded_at: eventAt,
    }
  })
}

function assetMilestoneEvents(
  assetId: string,
  layer: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5',
  runId: string,
  { includeImplementation = true, registryFingerprint = 'a'.repeat(64) }: { includeImplementation?: boolean; registryFingerprint?: string } = {},
) {
  const eventAt = Date.parse(milestoneAt) + Number(layer.slice(1)) * 60_000
  const binding = { registry_fingerprint_sha256: registryFingerprint, analysis_digest: 'b'.repeat(64) }
  const decision = {
    ...binding,
    verdict: 'optimize' as const,
    basis: {
      measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'optimize' as const, summary: 'A governed change is required.', output_contract: 'digest_identical' as const },
  }
  const eventTypes = [
    'asset_analysis_accepted', 'optimization_verdict_accepted',
    ...(includeImplementation ? ['implementation_accepted'] : []),
    'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
  ]
  return eventTypes.map((event_type, index) => ({
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type,
    entity_type: 'asset', entity_id: assetId, layer,
    evidence_payload: event_type === 'asset_analysis_accepted' ? binding
      : event_type === 'optimization_verdict_accepted' ? decision
        : event_type === 'implementation_accepted' ? { ...binding, decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision), implementation_digest: 'c'.repeat(64) }
          : event_type === 'accepted_rebuild_observed' ? {
            ...binding,
            build_run_id: runId,
            wave_index: 0,
            authorization_sha256: '9'.repeat(64),
            decision_digest: canonicalNirmanaOptimizationVerdictDigest(decision),
            implementation_digest: includeImplementation ? 'c'.repeat(64) : null,
            output_digest: 'd'.repeat(64), output_digest_spec_sha256: 'e'.repeat(64),
          }
            : event_type === 'integrity_verified' ? { ...binding, integrity_contract_sha256: 'f'.repeat(64), result_digest: '0'.repeat(64) }
              : { ...binding, lifecycle_digest: '1'.repeat(64) },
    source_kind: ['asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted'].includes(event_type)
      ? 'git_commit' : ['integrity_verified', 'asset_frozen'].includes(event_type) ? 'server_reconstructed' : 'build_run',
    source_ref: event_type === 'accepted_rebuild_observed' ? `build_run:${runId}`
      : event_type === 'integrity_verified' ? `nirmana-elevation:integrity:${assetId}`
        : event_type === 'asset_frozen' ? `nirmana-elevation:freeze:${assetId}`
          : `git:${'a'.repeat(40)}`,
    observed_at: new Date(eventAt + index * 1_000).toISOString(), recorded_at: new Date(eventAt + index * 1_000).toISOString(),
  }))
}

function nonBuildMilestoneEvents(
  assetId: string,
  layer: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5',
  eventType: 'static_accepted' | 'source_accepted' | 'empty_accepted' | 'retired_with_disposition',
  registryFingerprint = 'a'.repeat(64),
) {
  const binding = { registry_fingerprint_sha256: registryFingerprint, analysis_digest: 'b'.repeat(64) }
  const decision = {
    ...binding,
    verdict: 'non_build_disposition' as const,
    basis: {
      measurement: { status: 'not_applicable' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'formal_disposition' as const, summary: 'The formal non-build disposition is accepted.', output_contract: 'not_applicable' as const },
  }
  const disposition = ({ static_accepted: 'static_acceptance', source_accepted: 'source_acceptance', empty_accepted: 'empty_acceptance', retired_with_disposition: 'retired_with_disposition' } as const)[eventType]
  const sequence = ['asset_analysis_accepted', 'optimization_verdict_accepted', eventType, 'integrity_verified', 'asset_frozen']
  return sequence.map((currentEventType, index) => ({
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: currentEventType,
    entity_type: 'asset', entity_id: assetId, layer,
    evidence_payload: currentEventType === 'asset_analysis_accepted' ? binding
      : currentEventType === 'optimization_verdict_accepted' ? decision
        : currentEventType === eventType ? { ...binding, disposition, disposition_digest: 'c'.repeat(64) }
          : currentEventType === 'integrity_verified' ? { ...binding, integrity_contract_sha256: 'd'.repeat(64), result_digest: 'e'.repeat(64) }
            : { ...binding, lifecycle_digest: 'f'.repeat(64) },
    source_kind: ['asset_analysis_accepted', 'optimization_verdict_accepted', eventType].includes(currentEventType) ? 'git_commit' : 'server_reconstructed',
    source_ref: currentEventType === 'integrity_verified' ? `nirmana-elevation:integrity:${assetId}`
      : currentEventType === 'asset_frozen' ? `nirmana-elevation:freeze:${assetId}` : `git:${'a'.repeat(40)}`,
    observed_at: new Date(Date.parse(milestoneAt) + index * 1_000).toISOString(),
    recorded_at: new Date(Date.parse(milestoneAt) + index * 1_000).toISOString(),
  }))
}

function producerCoveredMilestoneEvents(assetId: string, producerRunId: string, registryFingerprint = 'a'.repeat(64)) {
  const binding = { registry_fingerprint_sha256: registryFingerprint, analysis_digest: 'b'.repeat(64) }
  const decision = {
    ...binding,
    verdict: 'optimize' as const,
    basis: {
      measurement: { status: 'insufficient_history' as const, sample_count: null, p50_ms: null, p90_ms: null, hotspot: null },
      evidence_refs: ['git:test-evidence'],
    },
    proposal: { action: 'optimize' as const, summary: 'Producer coverage is accepted.', output_contract: 'digest_identical' as const },
  }
  return ['asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered', 'integrity_verified', 'asset_frozen'].map((eventType, index) => ({
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: eventType,
    entity_type: 'asset', entity_id: assetId, layer: 'L0',
    evidence_payload: eventType === 'asset_analysis_accepted' ? binding
      : eventType === 'optimization_verdict_accepted' ? decision
        : eventType === 'integrity_verified' ? { ...binding, integrity_contract_sha256: 'c'.repeat(64), result_digest: 'd'.repeat(64) }
          : eventType === 'asset_frozen' ? { ...binding, lifecycle_digest: 'e'.repeat(64) } : {},
    source_kind: ['asset_analysis_accepted', 'optimization_verdict_accepted'].includes(eventType) ? 'git_commit'
      : ['integrity_verified', 'asset_frozen'].includes(eventType) ? 'server_reconstructed' : 'build_run',
    source_ref: eventType === 'producer_covered' ? `build_run:${producerRunId}`
      : eventType === 'integrity_verified' ? `nirmana-elevation:integrity:${assetId}`
        : eventType === 'asset_frozen' ? `nirmana-elevation:freeze:${assetId}` : `git:${'a'.repeat(40)}`,
    observed_at: new Date(Date.parse(milestoneAt) + index * 1_000).toISOString(),
    recorded_at: new Date(Date.parse(milestoneAt) + index * 1_000).toISOString(),
  }))
}

function runAuthorization(
  runId: string,
  assetIds: string[] = ['bg_prashna_rules'],
  { layer = 'L0', waveIndex = 0, at = '2026-08-25T08:59:00.000Z' }: {
    layer?: 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'
    waveIndex?: number
    at?: string
  } = {},
) {
  return {
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'build_run_authorized',
    entity_type: 'build_run', entity_id: runId, layer,
    evidence_payload: { wave_index: waveIndex, asset_ids: assetIds, authorization_sha256: 'd'.repeat(64) },
    source_kind: 'campaign_authorization', source_ref: `build_run:${runId}`, observed_at: at, recorded_at: at,
  }
}

function currentLayerRunEvidence(...authorizations: ReturnType<typeof runAuthorization>[]) {
  return [...foundationLaneEvents(), ...stageEventsThrough('L0'), ...authorizations]
}

describe('projectNirmanaElevationSnapshot', () => {
  it('projects only accepted, definition-scoped runtime activity and normalizes wave and asset states coherently', () => {
    const runIds = {
      completed: '11111111-1111-4111-8111-111111111111',
      active: '22222222-2222-4222-8222-222222222222',
      failed: '33333333-3333-4333-8333-333333333333',
      canary: '44444444-4444-4444-8444-444444444444',
      unaccepted: '55555555-5555-4555-8555-555555555555',
      unscoped: '66666666-6666-4666-8666-666666666666',
    }
    const assetRegistry = [
      registryAsset({ asset_id: 'bg_complete', sort_order: 0, target_table: 'bg_complete', count_sql: 'SELECT count(*) FROM bg_complete' }),
      registryAsset({ asset_id: 'bg_active', sort_order: 1, depends_on: ['bg_complete'], target_table: 'bg_active', count_sql: 'SELECT count(*) FROM bg_active' }),
      registryAsset({ asset_id: 'bg_blocked', sort_order: 2, depends_on: ['bg_complete'], target_table: 'bg_blocked', count_sql: 'SELECT count(*) FROM bg_blocked' }),
      registryAsset({ asset_id: 'bg_locked', sort_order: 3, depends_on: ['bg_active'], target_table: 'bg_locked', count_sql: 'SELECT count(*) FROM bg_locked' }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_complete', wave_index: 0, execution_obligation: 'build' },
      { asset_id: 'bg_active', wave_index: 1, execution_obligation: 'build' },
      { asset_id: 'bg_blocked', wave_index: 1, execution_obligation: 'build' },
      { asset_id: 'bg_locked', wave_index: 2, execution_obligation: 'build' },
    ])
    const authorize = (runId: string, assetId: string, triggeredAt: string) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'build_run_authorized',
      entity_type: 'build_run', entity_id: runId, layer: 'L0',
      evidence_payload: { wave_index: 1, asset_ids: [assetId], authorization_sha256: 'd'.repeat(64) },
      source_kind: 'campaign_authorization', source_ref: `build_run:${runId}`,
      observed_at: triggeredAt, recorded_at: triggeredAt,
    })
    const stageReceipts = [...stageEventsThrough('L0'), ...foundationLaneEvents()]
    const campaignEvents = [
      ...stageReceipts,
      ...assetMilestoneEvents('bg_complete', 'L0', runIds.completed, { registryFingerprint: manifest.assets.find((asset) => asset.asset_id === 'bg_complete')!.registry_fingerprint_sha256 }),
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_analysis_accepted',
        entity_type: 'asset', entity_id: 'bg_active', layer: 'L0', evidence_payload: { decision: 'accepted' },
        source_kind: 'campaign_evidence', source_ref: 'https://admin:super-secret@private-db.internal/evidence',
        observed_at: '2026-08-25T09:09:00.000Z', recorded_at: '2026-08-25T09:09:01.000Z',
      },
      authorize(runIds.active, 'bg_active', '2026-08-25T09:09:59.000Z'),
      authorize(runIds.failed, 'bg_blocked', '2026-08-25T09:10:59.000Z'),
      authorize(runIds.canary, 'bg_active', '2026-08-25T09:11:59.000Z'),
      authorize(runIds.unscoped, 'bg_active', '2026-08-25T09:13:59.000Z'),
    ]
    const rawSources = sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: campaignEvents,
      build_runs: [
        { id: runIds.completed, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt, triggered_by: 'nirmana-campaign' },
        { id: runIds.active, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_active', created_at: '2026-08-25T09:10:00.000Z', started_at: '2026-08-25T09:10:00.000Z', triggered_by: 'nirmana-campaign' },
        { id: runIds.failed, chart_id: canonicalChartId, action: 'rebuild', state: 'failed', current_asset_id: 'bg_blocked', created_at: '2026-08-25T09:11:00.000Z', started_at: '2026-08-25T09:11:00.000Z', triggered_by: 'nirmana-campaign' },
        { id: runIds.canary, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_active', created_at: '2026-08-25T09:12:00.000Z', started_at: '2026-08-25T09:12:00.000Z', triggered_by: 'nirmana-f0-machinery-canary' },
        { id: runIds.unaccepted, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_locked', created_at: '2026-08-25T09:13:00.000Z', started_at: '2026-08-25T09:13:00.000Z', triggered_by: 'manual' },
        { id: runIds.unscoped, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_locked', created_at: '2026-08-25T09:14:00.000Z', started_at: '2026-08-25T09:14:00.000Z', triggered_by: 'nirmana-campaign' },
      ],
      build_run_assets: [
        { run_id: runIds.completed, asset_id: 'bg_complete', position: 0, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null },
        { run_id: runIds.active, asset_id: 'bg_active', position: 0, state: 'building', started_at: '2026-08-25T09:10:00.000Z', ended_at: null, error: null },
        { run_id: runIds.failed, asset_id: 'bg_blocked', position: 0, state: 'error', started_at: '2026-08-25T09:11:00.000Z', ended_at: '2026-08-25T09:11:30.000Z', error: 'password=super-secret host=private-db.internal' },
        { run_id: runIds.canary, asset_id: 'bg_active', position: 0, state: 'building', started_at: '2026-08-25T09:12:00.000Z', ended_at: null, error: null },
        { run_id: runIds.unaccepted, asset_id: 'bg_locked', position: 0, state: 'building', started_at: '2026-08-25T09:13:00.000Z', ended_at: null, error: null },
        { run_id: runIds.unscoped, asset_id: 'bg_locked', position: 0, state: 'building', started_at: '2026-08-25T09:14:00.000Z', ended_at: null, error: null },
      ],
    } as Partial<NirmanaElevationRawSources>)
    const snapshot = projectNirmanaElevationSnapshot(rawSources, { generatedAt: '2026-08-25T09:20:00.000Z' })

    expect(snapshot.active_runs.map((run) => run.run_id)).toEqual([runIds.active])
    expect(snapshot.assets.map(({ asset_id, campaign_state }) => [asset_id, campaign_state])).toEqual([
      ['bg_complete', 'completed'], ['bg_active', 'active'], ['bg_blocked', 'blocked'], ['bg_locked', 'locked'],
    ])
    expect(snapshot.layers[0].waves.map((wave) => ({
      wave: wave.wave_index,
      state: wave.state,
      completed: wave.completed_asset_ids,
      active: wave.active_asset_ids,
      blocked: wave.blocked_asset_ids,
      locked: wave.locked_asset_ids,
      unknown: wave.unknown_asset_ids,
    }))).toEqual([
      { wave: 0, state: 'completed', completed: ['bg_complete'], active: [], blocked: [], locked: [], unknown: [] },
      { wave: 1, state: 'blocked', completed: [], active: ['bg_active'], blocked: ['bg_blocked'], locked: [], unknown: [] },
      { wave: 2, state: 'locked', completed: [], active: [], blocked: [], locked: ['bg_locked'], unknown: [] },
    ])
    expect(JSON.stringify(snapshot)).not.toContain('super-secret')
    expect(JSON.stringify(snapshot)).not.toContain('private-db.internal')
    expect(snapshot.audit.receipts).toEqual(expect.arrayContaining([
      expect.objectContaining({
        event_type: 'build_run_authorized', source_kind: 'campaign_authorization',
        source_ref: `build_run:${runIds.active}`, payload_sha256: expect.stringMatching(/^[a-f0-9]{64}$/),
        observed_at: '2026-08-25T09:09:59.000Z', recorded_at: '2026-08-25T09:09:59.000Z',
      }),
      expect.objectContaining({
        event_type: 'asset_analysis_accepted', entity_id: 'bg_active',
        source_ref: 'redacted:unsafe-reference', payload_sha256: expect.stringMatching(/^[a-f0-9]{64}$/),
      }),
    ]))
  })

  it('starts in takeover/catalogue reconciliation and refuses denominator claims before a frozen definition', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources(), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({
      campaign_id: 'nirmana-elevation',
      definition_revision: null,
      definition_status: 'reconciling',
      campaign_status: 'unknown',
      current_layer: null,
      current_wave: null,
    })
    expect(snapshot.progress).toMatchObject({
      denominator_status: 'reconciling',
      assets_total: null,
      buildable_assets_total: null,
      assets_frozen: 0,
      accepted_rebuilds: 0,
    })
    expect(snapshot.layers).toHaveLength(6)
    expect(snapshot.layers.every((layer) => layer.assets_total === null)).toBe(true)
    expect(snapshot.assets).toEqual(expect.arrayContaining([
      expect.objectContaining({
        asset_id: 'bg_prashna_rules',
        readiness_state: 'unknown',
        lifecycle_state: 'unverified',
        progress_mode: 'not_applicable',
      }),
    ]))
    expect(NirmanaElevationSnapshotSchema.safeParse(snapshot).success).toBe(true)
  })

  it('projects available release observations while withholding a commit-unproven sync verdict', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources(), {
      generatedAt: observedAt,
      releaseStatus: {
        release: {
          main_sha: 'a'.repeat(40), deployed_sha: null, deployed_revision: 'amjis-web-01704-mvb',
          production_in_sync: null, observed_at: observedAt,
        },
        sources: [
          { source_id: 'github_main', provenance: 'GitHub public commits API', state: 'fresh', observed_at: observedAt, age_seconds: 0, error_code: null, error_message: null },
          { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'fresh', observed_at: observedAt, age_seconds: 0, error_code: null, error_message: null },
          { source_id: 'artifact_registry_commit', provenance: 'Serving revision immutable commit provenance', state: 'unknown', observed_at: observedAt, age_seconds: null, error_code: 'NIRMANA_RELEASE_PROVENANCE_UNAVAILABLE', error_message: 'Immutable serving-revision commit provenance is unavailable.' },
        ],
        gaps: ['Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.'],
      },
    })

    expect(snapshot.release).toMatchObject({ main_sha: 'a'.repeat(40), deployed_sha: null, production_in_sync: null })
    expect(snapshot.sources).toEqual(expect.arrayContaining([
      expect.objectContaining({ source_id: 'github_main', state: 'fresh' }),
      expect.objectContaining({ source_id: 'artifact_registry_commit', state: 'unknown' }),
    ]))
    expect(snapshot.data_quality.gaps).toContain('Serving revision commit SHA is not published as immutable Cloud Run provenance; production sync is withheld.')
  })

  it('keeps current-run progress separate from persistent lit readiness', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(
      sources({
        campaign_definitions: [{
          campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
          manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
        }],
        campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
        build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
        build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      }),
      { generatedAt: observedAt },
    )

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      readiness_state: 'lit',
      current_run_state: 'building',
      progress_mode: 'indeterminate',
      work_committed: null,
      work_total: null,
    })
    expect(snapshot.active_runs).toEqual([
      expect.objectContaining({
        run_id: runOne,
        active_asset_ids: ['bg_prashna_rules'],
        completed_assets: 0,
        planned_assets: 1,
      }),
    ])
  })

  it('withholds runtime projection when an authorization was recorded after the run started', () => {
    const manifest = defaultManifest()
    const lateAuthorization = runAuthorization(runOne, ['bg_prashna_rules'], { at: '2026-08-25T09:01:00.000Z' })
    const snapshot = projectNirmanaElevationSnapshot(
      sources({
        campaign_definitions: [{
          campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
          manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
        }],
        campaign_events: currentLayerRunEvidence(lateAuthorization),
        build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
        build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      }),
      { generatedAt: '2026-08-25T09:02:00.000Z' },
    )

    expect(snapshot.active_runs).toEqual([])
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({ current_run_state: null })
  })

  it('does not infer campaign position or eligibility from an active run without valid stage evidence', () => {
    const manifest = manifestFor(defaultRegistry, [{ asset_id: 'bg_prashna_rules', wave_index: 0, execution_obligation: 'build' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{ id: 'run-current', chart_id: canonicalChartId, state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: 'run-current', asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({ current_stage: null, current_layer: null, current_wave: null })
    expect(snapshot.layers[0]?.state).not.toBe('open')
    expect(snapshot.layers[0]?.eligible_next_asset_ids).toEqual([])
  })

  it('projects plan adaptation without changing the accepted denominator', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      monitor_observations: [monitorObservation({
        status: 'plan_adaptation_required',
        affected_asset_ids: ['bg_new_asset', 'bg_prashna_rules'],
        current_definition_sha256: canonicalManifestDigest(manifest),
        candidate_definition_sha256: '9'.repeat(64),
      })],
    }), { generatedAt: '2026-08-25T09:05:00.000Z' })

    expect(snapshot.program_sync.status).toBe('plan_adaptation_required')
    expect(snapshot.program_sync).toMatchObject({
      observed_at: observedAt,
      age_seconds: 300,
      affected_asset_ids: ['bg_new_asset', 'bg_prashna_rules'],
      current_definition_sha256: canonicalManifestDigest(manifest),
      candidate_definition_sha256: '9'.repeat(64),
    })
    expect(snapshot.program_sync.candidate_catalogue_sha256).toMatch(/^[a-f0-9]{64}$/)
    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.data_quality.gaps).toContain('Plan adaptation is required before the program denominator can change.')
  })

  it('marks the monitor stale only after the five-minute window plus ten-minute grace', () => {
    const atBoundary = projectNirmanaElevationSnapshot(sources({
      monitor_observations: [monitorObservation()],
    }), { generatedAt: '2026-08-25T09:15:00.000Z' })
    const afterBoundary = projectNirmanaElevationSnapshot(sources({
      monitor_observations: [monitorObservation()],
    }), { generatedAt: '2026-08-25T09:15:01.000Z' })

    expect(atBoundary.sources.find((source) => source.source_id === 'program_monitor')?.state).toBe('fresh')
    expect(afterBoundary.sources.find((source) => source.source_id === 'program_monitor')).toMatchObject({
      state: 'stale', observed_at: observedAt, age_seconds: 901,
    })
  })

  it('uses the persisted source deadline when a newly inserted monitor row already represents stale source data', () => {
    const snapshot = projectNirmanaElevationSnapshot(sources({
      monitor_observations: [monitorObservation({
        observed_at: '2026-08-25T09:20:00.000Z',
        source_observed_at: observedAt,
        freshness_state: 'stale',
        freshness_deadline_at: '2026-08-25T09:15:00.000Z',
      })],
    }), { generatedAt: '2026-08-25T09:20:01.000Z' })

    expect(snapshot.program_sync).toMatchObject({
      observed_at: observedAt,
      age_seconds: 1_201,
    })
    expect(snapshot.sources.find((source) => source.source_id === 'program_monitor')).toMatchObject({
      state: 'stale', observed_at: observedAt, age_seconds: 1_201,
    })
  })

  it('keeps an in-sync frozen baseline at null stage and treats quiet runtime as fresh synchronization', () => {
    const manifest = defaultManifest()
    const manifestSha256 = canonicalManifestDigest(manifest)
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: manifestSha256, created_at: observedAt,
      }],
      monitor_observations: [monitorObservation({
        current_definition_sha256: manifestSha256,
        candidate_definition_sha256: manifestSha256,
        runtime_liveness: 'quiet',
      })],
    }), { generatedAt: '2026-08-25T09:05:00.000Z' })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.campaign).toMatchObject({ current_stage: null, current_layer: null, current_wave: null })
    expect(snapshot.program_sync).toMatchObject({ status: 'in_sync', age_seconds: 300 })
    expect(snapshot.sources.find((source) => source.source_id === 'program_monitor')?.state).toBe('fresh')
  })

  it('projects unknown and unavailable monitor source states without stale-green carryover', () => {
    const unknown = projectNirmanaElevationSnapshot(sources(), { generatedAt: observedAt })
    const unavailable = projectNirmanaElevationSnapshot(sources({
      monitor_observations: [monitorObservation({
        status: 'source_unavailable',
        affected_asset_ids: [],
        current_definition_sha256: null,
        candidate_definition_sha256: null,
        candidate_catalogue_sha256: 'c'.repeat(64),
        source_state: 'unavailable',
        runtime_liveness: 'unavailable',
        source_error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
      })],
    }), { generatedAt: '2026-08-25T09:01:00.000Z' })

    expect(unknown.program_sync).toMatchObject({
      status: 'unknown', observed_at: null, age_seconds: null, affected_asset_ids: [],
      current_definition_sha256: null, candidate_definition_sha256: null, candidate_catalogue_sha256: null,
    })
    expect(unknown.sources.find((source) => source.source_id === 'program_monitor')).toMatchObject({
      state: 'unknown', observed_at: null, age_seconds: null,
    })
    expect(unavailable.program_sync).toMatchObject({
      status: 'source_unavailable',
      candidate_catalogue_sha256: null,
    })
    expect(unavailable.sources.find((source) => source.source_id === 'program_monitor')).toMatchObject({
      state: 'unavailable', error_code: 'NIRMANA_SOURCE_UNAVAILABLE',
      error_message: 'Authoritative source is unavailable.',
    })
  })

  it('retains the latest terminal asset error when no active retry has replaced it', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'failed', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'running', started_at: observedAt, ended_at: observedAt, error: 'writer failed its integrity check' }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: null,
      blocker: `Accepted campaign run ${runOne} ended with an asset failure.`,
    })
  })

  it('blocks an accepted terminal run even when its aborted asset row has no error text', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'failed', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'aborted', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      campaign_state: 'blocked',
      current_run_state: null,
      blocker: `Accepted campaign run ${runOne} ended with an asset failure.`,
    })
  })

  it('retains terminal failure context while a later run retries the asset', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne), runAuthorization(runTwo)),
      build_runs: [
        { id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'failed', current_asset_id: 'bg_prashna_rules', created_at: '2026-08-25T09:00:00.000Z', started_at: '2026-08-25T09:00:00.000Z' },
        { id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'planned', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: null },
      ],
      build_run_assets: [
        { run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'error', started_at: '2026-08-25T09:00:00.000Z', ended_at: '2026-08-25T09:01:00.000Z', error: 'writer failed its integrity check' },
        { run_id: runTwo, asset_id: 'bg_prashna_rules', position: 1, state: 'planned', started_at: null, ended_at: null, error: null },
      ],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: 'planned',
      blocker: `Accepted campaign run ${runOne} ended with an asset failure; retry run ${runTwo} is planned.`,
    })
  })

  it('labels cross-attempt substep receipts as historical resumable work, not current progress', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      build_substep_progress: [{ chart_id: canonicalChartId, asset_id: 'bg_prashna_rules', committed: 7, last_progress_at: observedAt }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      progress_mode: 'indeterminate',
      work_committed: null,
      work_total: null,
      current_unit_label: 'Historical resumable work: 7 committed substeps',
    })
  })

  it('credits a global manifest asset through the mandatory canonical-chart cockpit build receipt', () => {
    const assetRegistry = [registryAsset({ scope: 'global' })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])
    const lifecycleEvents = assetMilestoneEvents('bg_prashna_rules', 'L0', runOne, { registryFingerprint: manifest.assets[0].registry_fingerprint_sha256 })
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      asset_throughput: [{ asset_id: 'bg_prashna_rules', chart_id: null, state: 'lit', last_built_at: observedAt }],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [...foundationLaneEvents(), ...stageEventsThrough('L0'), ...lifecycleEvents],
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('frozen')
  })

  it('never credits an F0 machinery canary as an accepted campaign rebuild', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'accepted_rebuild_observed',
        entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0', evidence_payload: {},
        source_kind: 'campaign_evidence', source_ref: `build_run:${runOne}`,
        observed_at: observedAt, recorded_at: observedAt,
      }],
      build_runs: [{
        id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null,
        created_at: observedAt, started_at: observedAt, triggered_by: 'nirmana-f0-machinery-canary',
      }],
      build_run_assets: [{
        run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete',
        started_at: observedAt, ended_at: observedAt, error: null,
      }],
    } as Partial<NirmanaElevationRawSources>), { generatedAt: observedAt })

    expect(snapshot.progress.accepted_rebuilds).toBe(0)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('catalogued')
  })

  it('does not let an uncorroborated frozen event turn primary evidence into elevation progress', () => {
    const snapshot = projectNirmanaElevationSnapshot(
      sources({
        campaign_events: [{
          campaign_id: 'nirmana-elevation',
          definition_revision: 'v1',
          event_type: 'asset_frozen',
          entity_type: 'asset',
          entity_id: 'bg_prashna_rules',
          layer: 'L0',
          evidence_payload: {},
          source_kind: 'campaign_evidence',
          source_ref: 'event:unverified',
          observed_at: observedAt,
          recorded_at: observedAt,
        }],
      }),
      { generatedAt: observedAt },
    )

    expect(snapshot.progress.assets_frozen).toBe(0)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('unverified')
  })

  it('counts an asset frozen only after a frozen manifest, all lifecycle receipts, and a completed build-run receipt agree', () => {
    const manifest = defaultManifest()
    const lifecycleEvents = assetMilestoneEvents('bg_prashna_rules', 'L0', runOne, { registryFingerprint: manifest.assets[0].registry_fingerprint_sha256 })
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation',
        definition_revision: 'v1',
        definition_status: 'frozen',
        manifest,
        manifest_sha256: canonicalManifestDigest(manifest),
        created_at: observedAt,
      }],
      campaign_events: [...foundationLaneEvents(), ...stageEventsThrough('L0'), ...lifecycleEvents],
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.assets_total).toBe(1)
    expect(snapshot.progress.assets_frozen).toBe(1)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('frozen')
  })

  it('requires a build asset accepted-rebuild receipt to name the completed build run exactly', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted',
      'optimization_verdict_accepted',
      'accepted_rebuild_observed',
      'integrity_verified',
      'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation',
      definition_revision: 'v1',
      event_type,
      entity_type: 'asset',
      entity_id: 'bg_prashna_rules',
      layer: 'L0',
      evidence_payload: {},
      source_kind: 'campaign_evidence',
      source_ref: event_type === 'accepted_rebuild_observed' ? `build_run:${runTwo}` : `event:${event_type}`,
      observed_at: observedAt,
      recorded_at: observedAt,
    }))
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.accepted_rebuilds).toBe(0)
    expect(snapshot.progress.assets_frozen).toBe(0)
  })

  it('rejects an accepted build receipt when its otherwise-complete run belongs to a different chart', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules',
      layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence',
      source_ref: event_type === 'accepted_rebuild_observed' ? `build_run:${runOne}` : `event:${event_type}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: runOne, chart_id: '11111111-1111-4111-8111-111111111111', action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ accepted_rebuilds: 0, assets_frozen: 0 })
  })

  it('withholds a build-obligated denominator for an active registry asset cockpit cannot dispatch', () => {
    const lifecycleEvents = [
      'asset_analysis_accepted', 'optimization_verdict_accepted', 'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
    ].map((event_type) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type, entity_type: 'asset', entity_id: 'bg_prashna_rules',
      layer: 'L0', evidence_payload: {}, source_kind: 'campaign_evidence',
      source_ref: event_type === 'accepted_rebuild_observed' ? `build_run:${runOne}` : `event:${event_type}`,
      observed_at: observedAt, recorded_at: observedAt,
    }))
    const assetRegistry = [registryAsset({ has_writer: false })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: lifecycleEvents,
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'reconciling', buildable_assets_total: null, accepted_rebuilds: 0, assets_frozen: 0 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.lifecycle_state).toBe('unverified')
  })

  it('allows an active non-writer asset to freeze only through its frozen formal non-build disposition', () => {
    const assetRegistry = [registryAsset({
      asset_id: 'lel_events', english_name: 'Life Events', layer: 'mimamsa', sort_order: 0,
      has_writer: false, catalog_status: 'DRAFT', target_table: null,
      count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1',
    })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'lel_events', execution_obligation: 'source_acceptance' }])
    const lifecycleEvents = nonBuildMilestoneEvents('lel_events', 'L5', 'source_accepted', manifest.assets[0].registry_fingerprint_sha256)
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [...foundationLaneEvents(), ...stageEventsThrough('L5'), ...lifecycleEvents],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', buildable_assets_total: 0, accepted_rebuilds: 0, assets_frozen: 1 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'lel_events')).toMatchObject({
      execution_obligation: 'source_acceptance',
      lifecycle_state: 'frozen',
    })
  })

  it('accepts formal non-build dispositions and producer-covered evidence without a rebuild of the logical asset', () => {
    const assetIds = ['lel_events', 'bg_transit_rules', 'bg_transit_engine']
    const assetRegistry = [
      registryAsset({
        asset_id: 'lel_events', english_name: 'Life Events', layer: 'mimamsa', sort_order: 0,
        has_writer: false, catalog_status: 'DRAFT', target_table: null,
        count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1',
      }),
      registryAsset({ asset_id: 'bg_transit_rules', english_name: 'Transit Rules', sort_order: 1, target_table: 'bg_transit_rules', count_sql: 'SELECT count(*) FROM bg_transit_rules' }),
      registryAsset({ asset_id: 'bg_transit_engine', english_name: 'Transit Engine', sort_order: 2, has_writer: false, target_table: 'bg_transit_engine', count_sql: 'SELECT count(*) FROM bg_transit_engine' }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'lel_events', execution_obligation: 'source_acceptance' },
      { asset_id: 'bg_transit_rules', execution_obligation: 'build', covered_asset_ids: ['bg_transit_engine'] },
      { asset_id: 'bg_transit_engine', execution_obligation: 'producer_covered', producer_id: 'bg_transit_rules' },
    ])
    const producerLifecycle = assetMilestoneEvents('bg_transit_rules', 'L0', runOne, { registryFingerprint: manifest.assets.find((asset) => asset.asset_id === 'bg_transit_rules')!.registry_fingerprint_sha256 })
    const producerRebuild = producerLifecycle.find((event) => event.event_type === 'accepted_rebuild_observed')!
    const coveredLifecycle = producerCoveredMilestoneEvents('bg_transit_engine', runOne, manifest.assets.find((asset) => asset.asset_id === 'bg_transit_engine')!.registry_fingerprint_sha256).map((event) => {
      if (event.event_type !== 'producer_covered') return event
      return {
        ...event,
        evidence_payload: {
          registry_fingerprint_sha256: manifest.assets.find((asset) => asset.asset_id === 'bg_transit_engine')!.registry_fingerprint_sha256,
          analysis_digest: 'b'.repeat(64),
          producer_asset_id: 'bg_transit_rules', producer_layer: 'L0', producer_run_id: runOne,
          producer_rebuild_digest: canonicalNirmanaRebuildEvidenceDigest(producerRebuild.evidence_payload),
        },
      }
    })
    const lifecycleEvents = [
      ...nonBuildMilestoneEvents('lel_events', 'L5', 'source_accepted', manifest.assets.find((asset) => asset.asset_id === 'lel_events')!.registry_fingerprint_sha256).map((event) => ({
        ...event,
        observed_at: new Date(Date.parse(event.observed_at) + 180_000).toISOString(),
        recorded_at: new Date(Date.parse(event.recorded_at) + 180_000).toISOString(),
      })),
      ...producerLifecycle,
      ...coveredLifecycle.map((event) => ({
        ...event,
        observed_at: new Date(Date.parse(event.observed_at) + 60_000).toISOString(),
        recorded_at: new Date(Date.parse(event.recorded_at) + 60_000).toISOString(),
      })),
    ]
    const rawSources = sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [...foundationLaneEvents(), ...stageEventsThrough('L5'), ...lifecycleEvents],
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_transit_rules', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    })
    const snapshot = projectNirmanaElevationSnapshot(rawSources, { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ assets_frozen: 3, accepted_rebuilds: 1 })
    expect(snapshot.layers[0]).toMatchObject({ rebuilt_or_dispositioned: 2, frozen: 2 })
    expect(snapshot.layers[5]).toMatchObject({ rebuilt_or_dispositioned: 1, frozen: 1 })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'lel_events')?.lifecycle_state).toBe('frozen')
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.lifecycle_state).toBe('frozen')

    const mismatch = projectNirmanaElevationSnapshot({
      ...rawSources,
      campaign_events: rawSources.campaign_events.map((event) => event.event_type === 'producer_covered'
        ? { ...event, source_ref: `build_run:${runTwo}` }
        : event),
    }, { generatedAt: observedAt })
    expect(mismatch.progress.assets_frozen).toBe(1)
    expect(mismatch.assets.find((asset) => asset.asset_id === 'bg_transit_engine')).toMatchObject({ lifecycle_state: 'catalogued' })
    expect(mismatch.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.milestones[2]).toMatchObject({
      milestone_id: 'built_or_dispositioned', state: 'current', event_type: null,
    })
    expect(mismatch.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.milestones[3]).toMatchObject({
      milestone_id: 'deployed_and_executed', state: 'pending', event_type: null,
    })
    const integrityBeforeCoverage = projectNirmanaElevationSnapshot({
      ...rawSources,
      campaign_events: rawSources.campaign_events.map((event) => event.event_type !== 'producer_covered' ? event : {
        ...event,
        observed_at: new Date(Date.parse(event.observed_at) + 600_000).toISOString(),
        recorded_at: new Date(Date.parse(event.recorded_at) + 600_000).toISOString(),
      }),
    }, { generatedAt: observedAt })
    expect(integrityBeforeCoverage.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.lifecycle_state).not.toBe('frozen')
    expect(mismatch.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.milestones[4]).toMatchObject({
      milestone_id: 'verified', state: 'pending', event_type: null,
    })
    expect(mismatch.assets.find((asset) => asset.asset_id === 'bg_transit_engine')?.milestones[5]).toMatchObject({
      milestone_id: 'frozen', state: 'pending', event_type: null,
    })
  })

  it('does not accept an active run authorization for a producer-covered logical asset', () => {
    const assetRegistry = [
      registryAsset({ asset_id: 'bg_transit_rules', english_name: 'Transit Rules', sort_order: 1, target_table: 'bg_transit_rules', count_sql: 'SELECT count(*) FROM bg_transit_rules' }),
      registryAsset({ asset_id: 'bg_transit_engine', english_name: 'Transit Engine', sort_order: 2, has_writer: false, target_table: 'bg_transit_engine', count_sql: 'SELECT count(*) FROM bg_transit_engine' }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_transit_rules', execution_obligation: 'build', covered_asset_ids: ['bg_transit_engine'] },
      { asset_id: 'bg_transit_engine', execution_obligation: 'producer_covered', producer_id: 'bg_transit_rules' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runTwo, ['bg_transit_engine'])),
      build_runs: [{ id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_transit_engine', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runTwo, asset_id: 'bg_transit_engine', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.active_runs).toEqual([])
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_transit_engine')).toMatchObject({
      current_run_state: null,
      progress_mode: 'not_applicable',
    })
  })

  it('does not accept an active run authorization for a non-executable disposition', () => {
    const assetRegistry = [registryAsset({
      asset_id: 'lel_events', english_name: 'Life Events', layer: 'mimamsa', sort_order: 0,
      has_writer: false, catalog_status: 'DRAFT', target_table: null,
      count_sql: 'SELECT count(*) FROM life_events WHERE chart_id = $1',
    })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'lel_events', execution_obligation: 'source_acceptance' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough('L5'),
        runAuthorization(runTwo, ['lel_events'], { layer: 'L5' }),
      ],
      build_runs: [{ id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'lel_events', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runTwo, asset_id: 'lel_events', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.active_runs).toEqual([])
    expect(snapshot.assets.find((asset) => asset.asset_id === 'lel_events')).toMatchObject({
      current_run_state: null,
      progress_mode: 'not_applicable',
    })
  })

  it('withholds a frozen denominator that gives a producer-covered asset a dangling or non-build producer', () => {
    const assetIds = ['bg_source', 'bg_covered']
    const assetRegistry = assetIds.map((asset_id, sort_order) => registryAsset({ asset_id, english_name: asset_id, sort_order, target_table: asset_id, count_sql: `SELECT count(*) FROM ${asset_id}` }))
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_source', execution_obligation: 'source_acceptance' },
      { asset_id: 'bg_covered', execution_obligation: 'producer_covered', producer_id: 'bg_source' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('withholds a frozen denominator that gives a producer-covered asset a missing producer', () => {
    const assetRegistry = [registryAsset({
      asset_id: 'bg_sign_medical', english_name: 'Sign Medical', has_writer: false,
      target_table: 'bg_sign_medical', count_sql: 'SELECT count(*) FROM bg_sign_medical',
    })]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_sign_medical', execution_obligation: 'producer_covered', producer_id: 'bg_medical_mappings' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('uses the latest active run for an asset rather than a historical run row that happens to arrive later', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
      build_runs: [
        { id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: '2026-08-25T10:00:00.000Z', started_at: '2026-08-25T10:00:00.000Z' },
        { id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt },
      ],
      build_run_assets: [
        { run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: '2026-08-25T10:00:00.000Z', ended_at: null, error: null },
        { run_id: runTwo, asset_id: 'bg_prashna_rules', position: 1, state: 'error', started_at: observedAt, ended_at: observedAt, error: 'obsolete failure' },
      ],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: 'building',
      blocker: null,
      progress_mode: 'indeterminate',
    })
  })

  it('keeps a running execution ahead of a newer planned retry for the same asset', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen',
        manifest, manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne), runAuthorization(runTwo)),
      build_runs: [
        { id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt },
        { id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'planned', current_asset_id: 'bg_prashna_rules', created_at: '2026-08-25T10:00:00.000Z', started_at: null },
      ],
      build_run_assets: [
        { run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null },
        { run_id: runTwo, asset_id: 'bg_prashna_rules', position: 1, state: 'planned', started_at: null, ended_at: null, error: null },
      ],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      current_run_state: 'building',
      progress_mode: 'indeterminate',
    })
  })

  it('does not project a different chart\'s throughput as canonical readiness', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_throughput: [{ asset_id: 'bg_prashna_rules', chart_id: '11111111-1111-4111-8111-111111111111', state: 'lit', last_built_at: observedAt }],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.readiness_state).toBe('unknown')
  })

  it('does not expose another chart\'s active run in the campaign projection', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
      build_runs: [{ id: runOne, chart_id: '11111111-1111-4111-8111-111111111111', action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
    }), { generatedAt: observedAt })

    expect(snapshot.active_runs).toEqual([])
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.current_run_state).toBeNull()
  })

  it('does not use another chart\'s substep receipts for canonical active progress', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: currentLayerRunEvidence(runAuthorization(runOne)),
      build_runs: [{ id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules', created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building', started_at: observedAt, ended_at: null, error: null }],
      build_substep_progress: [{ chart_id: '11111111-1111-4111-8111-111111111111', asset_id: 'bg_prashna_rules', committed: 99, last_progress_at: observedAt }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.current_unit_label).toBe('execution in progress')
  })

  it('retains only explicitly global throughput rows as safe shared evidence', () => {
    const assetRegistry = [registryAsset({ scope: 'global' })]
    const manifest = manifestFor(assetRegistry, [{ asset_id: 'bg_prashna_rules', execution_obligation: 'build' }])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      asset_throughput: [
        { asset_id: 'bg_prashna_rules', chart_id: null, state: 'lit', last_built_at: observedAt },
        { asset_id: 'bg_prashna_rules', chart_id: '11111111-1111-4111-8111-111111111111', state: 'error', last_built_at: observedAt },
      ],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.readiness_state).toBe('lit')
  })

  it('keeps an adjudicated retired asset inside the frozen denominator', () => {
    const assetRegistry = [
      registryAsset(),
      registryAsset({
        asset_id: 'ka_gochara_sweep', english_name: 'Retired Gochara Sweep', layer: 'kala', sort_order: 105,
        is_active: false, catalog_status: 'RETIRED', target_table: 'kala_gochara_windows',
        count_sql: "SELECT count(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'",
        superseded_by: 'bg_prashna_rules', data_disposition: 'RETAINED_AS_CAPITAL',
      }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_prashna_rules', execution_obligation: 'build' },
      { asset_id: 'ka_gochara_sweep', execution_obligation: 'retired_with_disposition' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 2 })
    expect(snapshot.assets.map((asset) => asset.asset_id)).toContain('ka_gochara_sweep')
  })

  it('keeps the frozen denominator while blocking unaccepted per-asset registry-contract drift', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: [registryAsset({ count_sql: 'SELECT count(*) FROM drifted_table' })],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.assets[0]).toMatchObject({
      lifecycle_state: 'blocked',
      blocker: expect.stringContaining('registry contract changed after the frozen T0 definition'),
    })
    expect(snapshot.assets[0].evidence_refs).toEqual(expect.arrayContaining([
      `registry:t0:${manifest.assets[0].registry_fingerprint_sha256}`,
      expect.stringMatching(/^registry:live:[a-f0-9]{64}$/),
    ]))
    expect(snapshot.assets[0].evidence_refs.find((reference) => reference.startsWith('registry:live:')))
      .not.toBe(`registry:live:${manifest.assets[0].registry_fingerprint_sha256}`)
    expect(snapshot.data_quality.gaps).toContain('1 asset registry contract has changed without a matching accepted analysis fingerprint.')
    expect(snapshot.data_quality.contradictions).toEqual(['bg_prashna_rules'])
  })

  it('accepts governed contract evolution only when asset analysis pins the current registry fingerprint', () => {
    const manifest = defaultManifest()
    const driftedRegistry = [registryAsset({ count_sql: 'SELECT count(*) FROM evolved_table' })]
    const currentFingerprint = canonicalRegistryContractDigest({
      asset_id: 'bg_prashna_rules',
      layer: 'L0',
      depends_on: [],
      registry_contract: {
        ...manifest.assets[0].registry_contract,
        count_sql: 'SELECT count(*) FROM evolved_table',
      },
    })
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: driftedRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_analysis_accepted',
        entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { registry_fingerprint_sha256: currentFingerprint, analysis_digest: 'a'.repeat(64) },
        source_kind: 'git_commit', source_ref: `git:${'b'.repeat(40)}`,
        observed_at: observedAt, recorded_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.assets[0]).toMatchObject({ lifecycle_state: 'catalogued', blocker: null })
    expect(snapshot.assets[0].evidence_refs).toEqual(expect.arrayContaining([
      `registry:live:${currentFingerprint}`,
      `registry:accepted:${currentFingerprint}`,
      `analysis:sha256:${'a'.repeat(64)}`,
    ]))
    expect(snapshot.data_quality.gaps).not.toContain(expect.stringContaining('registry contract has changed'))
    expect(snapshot.data_quality.contradictions).toEqual([])
  })

  it('does not let a stale analysis receipt accept a later registry-contract mutation', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: [registryAsset({ count_sql: 'SELECT count(*) FROM later_mutation' })],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_analysis_accepted',
        entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
        evidence_payload: { registry_fingerprint_sha256: 'c'.repeat(64), analysis_digest: 'a'.repeat(64) },
        source_kind: 'git_commit', source_ref: `git:${'b'.repeat(40)}`,
        observed_at: observedAt, recorded_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'frozen', assets_total: 1 })
    expect(snapshot.assets[0]).toMatchObject({ lifecycle_state: 'blocked' })
    expect(snapshot.data_quality.contradictions).toEqual(['bg_prashna_rules'])
  })

  it('still fails closed when the current registry changes the frozen asset/DAG identity', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: [registryAsset({ layer: 'ganita' })],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ denominator_status: 'reconciling', assets_total: null })
  })

  it('withholds a claimed frozen denominator whose canonical manifest digest does not verify', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sources({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation',
        definition_revision: 'v1',
        definition_status: 'frozen',
        manifest,
        manifest_sha256: '0'.repeat(64),
        created_at: observedAt,
      }],
    }), { generatedAt: observedAt })

    expect(snapshot.progress.denominator_status).toBe('reconciling')
    expect(snapshot.progress.assets_total).toBeNull()
  })

  it('uses only the accepted label catalogue revision and exposes explicit incomplete identity fields', () => {
    const manifest = defaultManifest()
    const acceptedDigest = 'f072566e2076e9938c1803e8ae6dd913842258bfe6a23152d146017b8c02bb4d'
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [labelReceipt('labels-v2', acceptedDigest)],
    }, [
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', catalogue_revision: 'labels-v1',
        asset_id: 'bg_prashna_rules', sanskrit_name: 'Stale Sanskrit', english_name: 'Stale label',
        description: 'Unaccepted catalogue.', legacy_aliases: [], source_ref: 'labels-v1',
        label_digest: 'a'.repeat(64), recorded_at: '2026-08-25T08:00:00.000Z',
      },
      {
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', catalogue_revision: 'labels-v2',
        asset_id: 'bg_prashna_rules', sanskrit_name: null, english_name: 'Accepted Prashna Rules',
        description: null, legacy_aliases: [{ asset_id: 'bg_prashna_legacy', sanskrit_name: null, english_name: 'Legacy Prashna' }],
        source_ref: 'labels-v2', label_digest: acceptedDigest, recorded_at: observedAt,
      },
    ]), { generatedAt: observedAt })

    expect(snapshot.schema_version).toBe('2.0')
    if (snapshot.schema_version !== '2.0') throw new Error('expected snapshot v2')
    expect(snapshot.assets[0]).toMatchObject({
      display_name: 'Accepted Prashna Rules', sanskrit_name: null, english_name: 'Accepted Prashna Rules',
      description: null, identity_quality: 'incomplete',
      legacy_aliases: [{ asset_id: 'bg_prashna_legacy', sanskrit_name: null, english_name: 'Legacy Prashna' }],
    })
    expect(NirmanaElevationSnapshotV2Schema.safeParse(snapshot).success).toBe(true)
  })

  it('rejects an accepted label catalogue digest mismatch and falls back without presenting it as versioned identity', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [labelReceipt('labels-v1', 'b'.repeat(64))],
    }, [{
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', catalogue_revision: 'labels-v1',
      asset_id: 'bg_prashna_rules', sanskrit_name: 'Untrusted', english_name: 'Untrusted label',
      description: 'Digest does not match.', legacy_aliases: [], source_ref: 'labels-v1',
      label_digest: 'a'.repeat(64), recorded_at: observedAt,
    }]), { generatedAt: observedAt })

    expect(snapshot.schema_version).toBe('2.0')
    if (snapshot.schema_version !== '2.0') throw new Error('expected snapshot v2')
    expect(snapshot.assets[0]).toMatchObject({
      sanskrit_name: null, english_name: 'Prashna Rules', description: null,
      legacy_aliases: [], identity_quality: 'unversioned_fallback',
    })
    expect(snapshot.data_quality.contradictions).toEqual(expect.arrayContaining([
      expect.stringContaining('labels-v1'), expect.stringContaining('digest'),
    ]))
  })

  it('emits the ordered v2 campaign spine, governed layer names, milestones, and eligible next assets', () => {
    const assetRegistry = [
      registryAsset(),
      registryAsset({
        asset_id: 'bg_gochara_citation_resolution', english_name: 'Gochara Citation Resolution', sort_order: 2,
        target_table: 'bg_gochara_citation_resolution', depends_on: ['bg_prashna_rules'], has_writer: false,
      }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_prashna_rules', wave_index: 0, execution_obligation: 'build' },
      { asset_id: 'bg_gochara_citation_resolution', wave_index: 1, execution_obligation: 'static_acceptance' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [
        ...foundationLaneEvents(),
        ...stageEventsThrough('L0'),
        runAuthorization(runOne),
        {
          campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_analysis_accepted',
          entity_type: 'asset', entity_id: 'bg_prashna_rules', layer: 'L0',
          evidence_payload: { registry_fingerprint_sha256: manifest.assets[0].registry_fingerprint_sha256, analysis_digest: 'b'.repeat(64) },
          source_kind: 'git_commit', source_ref: `git:${'a'.repeat(40)}`, observed_at: observedAt, recorded_at: observedAt,
        },
      ],
      build_runs: [{
        id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules',
        created_at: observedAt, started_at: observedAt,
      }],
      build_run_assets: [{
        run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'building',
        started_at: observedAt, ended_at: null, error: null,
      }],
    }, []), { generatedAt: observedAt })

    expect(snapshot.schema_version).toBe('2.0')
    if (snapshot.schema_version !== '2.0') throw new Error('expected snapshot v2')
    expect(snapshot.campaign.current_stage).toBe('L0')
    expect(snapshot.stages.map((stage) => stage.stage_id)).toEqual(NIRMANA_STAGE_IDS)
    expect(snapshot.layers.map((layer) => layer.layer_name)).toEqual(
      snapshot.layers.map((layer) => NIRMANA_LAYER_NAMES[layer.layer_id]),
    )
    expect(snapshot.layers[0].waves.map((wave) => wave.wave_index)).toEqual([0, 1])
    expect(snapshot.layers[0].eligible_next_asset_ids).toEqual(['bg_prashna_rules'])
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      milestones_earned: 1, milestones_required: 6, current_action: 'Accepted campaign run: building',
      next_action: 'Accept implementation or disposition',
      evidence_refs: expect.arrayContaining([
        `git:${'a'.repeat(40)}`,
        `registry:t0:${manifest.assets[0].registry_fingerprint_sha256}`,
        `registry:live:${manifest.assets[0].registry_fingerprint_sha256}`,
      ]),
    })
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_gochara_citation_resolution')).toMatchObject({
      milestones_earned: 0, milestones_required: 5, current_action: 'Accept asset analysis',
    })
  })

  it('changes the generation digest when governed stage semantics change', () => {
    const manifest = defaultManifest()
    const baseline = sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }, [])
    const transitioned = sourcesWithLabels({
      ...baseline,
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'stage_transition_accepted',
        entity_type: 'campaign_stage', entity_id: 'T0_CENSUS', layer: null,
        evidence_payload: { schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: 'BOOTSTRAP', to_stage: 'T0_CENSUS', manifest_sha256: 'c'.repeat(64) },
        source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine', observed_at: observedAt, recorded_at: observedAt,
      }],
    }, [])

    const first = projectNirmanaElevationSnapshot(baseline, { generatedAt: observedAt })
    const second = projectNirmanaElevationSnapshot(transitioned, { generatedAt: observedAt })
    expect(first.generation).not.toBe(second.generation)
  })

  it('does not complete F0 from lane receipts until an accepted transition leaves F0', () => {
    const manifest = defaultManifest()
    const campaign_events = ['A', 'B', 'C', 'D', 'E'].map((laneId) => ({
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'foundation_lane_accepted',
      entity_type: 'foundation_lane', entity_id: laneId, layer: null,
      evidence_payload: foundationPayload(laneId), source_kind: 'server_reconstructed',
      source_ref: `nirmana-elevation:foundation-lane:${laneId}`, observed_at: observedAt, recorded_at: observedAt,
    }))
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events,
    }, []), { generatedAt: observedAt })

    expect(snapshot.schema_version).toBe('2.0')
    if (snapshot.schema_version !== '2.0') throw new Error('expected snapshot v2')
    expect(snapshot.stages.find((stage) => stage.stage_id === 'F0_FOUNDATION')).toMatchObject({
      state: 'unknown', earned: 5, required: 5, completed_at: null,
    })
  })

  it('keeps Lane C unknown in snapshots when its fingerprint is omitted or its analysis is invalidated', () => {
    const manifest = defaultManifest()
    const invalidLaneCPayloads = [
      {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'C', manifest_sha256: 'a'.repeat(64),
        manifest_asset_count: 1, live_registry_asset_count: 1, invalidated_analysis_count: 0,
      },
      {
        schema_version: 'nirmana-foundation-lane-receipt/v1', lane_id: 'C', manifest_sha256: 'a'.repeat(64),
        registry_fingerprint_set_sha256: 'b'.repeat(64), manifest_asset_count: 1,
        live_registry_asset_count: 1, invalidated_analysis_count: 1,
      },
    ]

    for (const evidence_payload of invalidLaneCPayloads) {
      const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
        campaign_definitions: [{
          campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
          manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
        }],
        campaign_events: foundationLaneEvents().map((event) => event.entity_id === 'C'
          ? { ...event, evidence_payload }
          : event),
      }, []), { generatedAt: observedAt })

      const foundation = snapshot.stages.find((stage) => stage.stage_id === 'F0_FOUNDATION')
      expect(foundation).toMatchObject({ state: 'unknown', earned: 4, required: 5 })
      expect(foundation?.foundation_lanes?.find(({ lane_id }) => lane_id === 'C')).toMatchObject({ state: 'unknown' })
    }
  })

  it('projects the nullable-from initial transition as the active bootstrap stage', () => {
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_events: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'stage_transition_accepted',
        entity_type: 'campaign_stage', entity_id: 'BOOTSTRAP', layer: null,
        evidence_payload: { schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: null, to_stage: 'BOOTSTRAP', manifest_sha256: 'a'.repeat(64) },
        source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine', observed_at: observedAt, recorded_at: observedAt,
      }],
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'reconciling',
        manifest: defaultManifest(), manifest_sha256: canonicalManifestDigest(defaultManifest()), created_at: observedAt,
      }],
    }, []), { generatedAt: observedAt })

    expect(snapshot.campaign.current_stage).toBe('BOOTSTRAP')
    expect(snapshot.stages[0]).toMatchObject({ stage_id: 'BOOTSTRAP', state: 'active' })
  })

  it('does not freeze a changed build or unlock its next wave before implementation is accepted', () => {
    const assetRegistry = [
      registryAsset(),
      registryAsset({
        asset_id: 'bg_second', english_name: 'Second Asset', sort_order: 2,
        target_table: 'bg_second', depends_on: ['bg_prashna_rules'],
      }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_prashna_rules', wave_index: 0, execution_obligation: 'build' },
      { asset_id: 'bg_second', wave_index: 1, execution_obligation: 'build' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough('L0'),
        ...assetMilestoneEvents('bg_prashna_rules', 'L0', runOne, { includeImplementation: false, registryFingerprint: manifest.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')!.registry_fingerprint_sha256 }),
      ],
      build_runs: [{
        id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null,
        created_at: observedAt, started_at: observedAt,
      }],
      build_run_assets: [{
        run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete',
        started_at: observedAt, ended_at: observedAt, error: null,
      }],
    }, []), { generatedAt: observedAt })

    expect(snapshot.progress.assets_frozen).toBe(0)
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')).toMatchObject({
      lifecycle_state: 'rebuilt', milestones_earned: 2, current_action: 'Accept implementation or disposition',
    })
    expect(snapshot.campaign).toMatchObject({ current_layer: 'L0', current_wave: 0 })
    expect(snapshot.layers[0].eligible_next_asset_ids).toEqual(['bg_prashna_rules'])
    expect(snapshot.layers[0].eligible_next_asset_ids).not.toContain('bg_second')
  })

  it('does not count a completed build receipt whose entity layer contradicts the manifest', () => {
    const manifest = defaultManifest()
    const campaign_events = assetMilestoneEvents('bg_prashna_rules', 'L0', runOne, { registryFingerprint: manifest.assets[0].registry_fingerprint_sha256 }).map((event) =>
      event.event_type === 'accepted_rebuild_observed' ? { ...event, layer: 'L1' } : event)
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events,
      build_runs: [{
        id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null,
        created_at: observedAt, started_at: observedAt,
      }],
      build_run_assets: [{
        run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete',
        started_at: observedAt, ended_at: observedAt, error: null,
      }],
    }, []), { generatedAt: observedAt })

    expect(snapshot.progress).toMatchObject({ accepted_rebuilds: 0, assets_frozen: 0 })
  })

  it('does not complete a layer before the accepted transition from F0 enters L0', () => {
    const manifest = defaultManifest()
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough('F0_FOUNDATION'),
        ...assetMilestoneEvents('bg_prashna_rules', 'L0', runOne, { registryFingerprint: manifest.assets[0].registry_fingerprint_sha256 }),
      ],
      build_runs: [{
        id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null,
        created_at: observedAt, started_at: observedAt,
      }],
      build_run_assets: [{
        run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete',
        started_at: observedAt, ended_at: observedAt, error: null,
      }],
    }, []), { generatedAt: observedAt })

    expect(snapshot.progress.assets_frozen).toBe(0)
    expect(snapshot.campaign).toMatchObject({ current_stage: 'F0_FOUNDATION', current_layer: null, current_wave: null })
    expect(snapshot.stages.find((stage) => stage.stage_id === 'F0_FOUNDATION')?.state).toBe('blocked')
    expect(snapshot.stages.find((stage) => stage.stage_id === 'L0')?.state).not.toBe('completed')
    expect(snapshot.layers[0].state).toBe('locked')
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.campaign_state).not.toBe('completed')
    expect(snapshot.assets.find((asset) => asset.asset_id === 'bg_prashna_rules')?.milestones.at(-1)?.state).not.toBe('earned')
    expect(snapshot.data_quality.contradictions).toEqual(expect.arrayContaining([
      expect.stringMatching(/bg_prashna_rules.*freeze evidence.*governed stage\/wave order/i),
    ]))
  })

  it('withholds an early-wave freeze until every prior wave is frozen in governed order', () => {
    const assetRegistry = [
      registryAsset({ asset_id: 'bg_first', english_name: 'First Asset', sort_order: 1, target_table: 'bg_first', count_sql: 'SELECT count(*) FROM bg_first' }),
      registryAsset({ asset_id: 'bg_second', english_name: 'Second Asset', sort_order: 2, depends_on: ['bg_first'], target_table: 'bg_second', count_sql: 'SELECT count(*) FROM bg_second' }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_first', wave_index: 0, execution_obligation: 'build' },
      { asset_id: 'bg_second', wave_index: 1, execution_obligation: 'build' },
    ])
    const snapshot = projectNirmanaElevationSnapshot(sources({
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough('L0'),
        ...assetMilestoneEvents('bg_second', 'L0', runTwo, { registryFingerprint: manifest.assets.find((asset) => asset.asset_id === 'bg_second')!.registry_fingerprint_sha256 }),
      ],
      build_runs: [{ id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runTwo, asset_id: 'bg_second', position: 1, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null }],
    }), { generatedAt: observedAt })

    const earlyAsset = snapshot.assets.find((asset) => asset.asset_id === 'bg_second')
    const earlyWave = snapshot.layers[0].waves.find((wave) => wave.wave_index === 1)
    expect(snapshot.progress.assets_frozen).toBe(0)
    expect(snapshot.layers[0].frozen).toBe(0)
    expect(earlyAsset?.campaign_state).not.toBe('completed')
    expect(earlyAsset?.milestones.at(-1)?.state).not.toBe('earned')
    expect(earlyWave?.state).not.toBe('completed')
    expect(earlyWave?.completed_asset_ids).toEqual([])
    expect(snapshot.data_quality.contradictions).toEqual(expect.arrayContaining([
      expect.stringMatching(/bg_second.*freeze evidence.*governed stage\/wave order/i),
    ]))
  })

  it('never retroactively credits a time-skewed freeze recorded before its layer stage entry', () => {
    const manifest = defaultManifest()
    const prematureFreezeEvents = assetMilestoneEvents('bg_prashna_rules', 'L0', runOne, { registryFingerprint: manifest.assets[0].registry_fingerprint_sha256 }).map((event) =>
      event.event_type === 'asset_frozen'
        ? {
            ...event,
            observed_at: '2026-08-25T10:00:00.000Z',
            recorded_at: '2026-08-25T09:00:04.500Z',
          }
        : event)
    const commonSources = {
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen' as const, manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      build_runs: [{
        id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null,
        created_at: observedAt, started_at: observedAt,
      }],
      build_run_assets: [{
        run_id: runOne, asset_id: 'bg_prashna_rules', position: 1, state: 'complete',
        started_at: observedAt, ended_at: milestoneAt, error: null,
      }],
    }
    const projectAt = (stage: 'F0_FOUNDATION' | 'L0') => projectNirmanaElevationSnapshot(sourcesWithLabels({
      ...commonSources,
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough(stage), ...prematureFreezeEvents,
      ],
    }, []), { generatedAt: '2026-08-25T10:01:00.000Z' })

    const beforeStageEntry = projectAt('F0_FOUNDATION')
    const afterStageEntry = projectAt('L0')

    for (const snapshot of [beforeStageEntry, afterStageEntry]) {
      const asset = snapshot.assets.find((candidate) => candidate.asset_id === 'bg_prashna_rules')
      const wave = snapshot.layers[0].waves.find((candidate) => candidate.wave_index === 0)
      expect(snapshot.progress).toMatchObject({ assets_frozen: 0, layers_frozen: 0 })
      expect(snapshot.layers[0]).toMatchObject({ frozen: 0 })
      expect(snapshot.layers[0].state).not.toBe('frozen')
      expect(asset?.campaign_state).not.toBe('completed')
      expect(asset?.milestones.at(-1)?.state).not.toBe('earned')
      expect(wave?.state).not.toBe('completed')
      expect(wave?.completed_asset_ids).toEqual([])
      expect(snapshot.data_quality.contradictions).toEqual(expect.arrayContaining([
        expect.stringMatching(/bg_prashna_rules.*freeze evidence.*governed stage\/wave order/i),
      ]))
    }
  })

  it('does not let a later prior-wave freeze validate an already-premature next-wave receipt', () => {
    const assetRegistry = [
      registryAsset({ asset_id: 'bg_first', english_name: 'First Asset', sort_order: 1, target_table: 'bg_first', count_sql: 'SELECT count(*) FROM bg_first' }),
      registryAsset({ asset_id: 'bg_second', english_name: 'Second Asset', sort_order: 2, depends_on: ['bg_first'], target_table: 'bg_second', count_sql: 'SELECT count(*) FROM bg_second' }),
    ]
    const manifest = manifestFor(assetRegistry, [
      { asset_id: 'bg_first', wave_index: 0, execution_obligation: 'build' },
      { asset_id: 'bg_second', wave_index: 1, execution_obligation: 'build' },
    ])
    const secondWaveEvents = assetMilestoneEvents('bg_second', 'L0', runTwo, { registryFingerprint: manifest.assets.find((asset) => asset.asset_id === 'bg_second')!.registry_fingerprint_sha256 }).map((event) =>
      event.event_type === 'asset_frozen'
        ? { ...event, observed_at: '2026-08-25T10:00:00.000Z', recorded_at: '2026-08-25T09:00:10.000Z' }
        : event)
    const firstWaveEvents = assetMilestoneEvents('bg_first', 'L0', runOne, { registryFingerprint: manifest.assets.find((asset) => asset.asset_id === 'bg_first')!.registry_fingerprint_sha256 }).map((event) =>
      event.event_type === 'asset_frozen'
        ? { ...event, observed_at: '2026-08-25T09:02:00.000Z', recorded_at: '2026-08-25T09:02:00.000Z' }
        : event)
    const commonSources = {
      asset_registry: assetRegistry,
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen' as const, manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
    }
    const beforePriorWaveCompletes = projectNirmanaElevationSnapshot(sources({
      ...commonSources,
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough('L0'), ...secondWaveEvents,
      ],
      build_runs: [{ id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt }],
      build_run_assets: [{ run_id: runTwo, asset_id: 'bg_second', position: 1, state: 'complete', started_at: observedAt, ended_at: milestoneAt, error: null }],
    }), { generatedAt: '2026-08-25T09:01:30.000Z' })
    const afterPriorWaveCompletes = projectNirmanaElevationSnapshot(sources({
      ...commonSources,
      campaign_events: [
        ...foundationLaneEvents(), ...stageEventsThrough('L0'), ...secondWaveEvents, ...firstWaveEvents,
      ],
      build_runs: [
        { id: runTwo, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt },
        { id: runOne, chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null, created_at: observedAt, started_at: observedAt },
      ],
      build_run_assets: [
        { run_id: runTwo, asset_id: 'bg_second', position: 1, state: 'complete', started_at: observedAt, ended_at: milestoneAt, error: null },
        { run_id: runOne, asset_id: 'bg_first', position: 1, state: 'complete', started_at: observedAt, ended_at: '2026-08-25T09:02:00.000Z', error: null },
      ],
    }), { generatedAt: '2026-08-25T09:03:00.000Z' })

    expect(beforePriorWaveCompletes.progress).toMatchObject({ assets_frozen: 0, layers_frozen: 0 })
    const secondAsset = afterPriorWaveCompletes.assets.find((asset) => asset.asset_id === 'bg_second')
    const secondWave = afterPriorWaveCompletes.layers[0].waves.find((wave) => wave.wave_index === 1)
    expect(afterPriorWaveCompletes.progress).toMatchObject({ assets_frozen: 1, layers_frozen: 0 })
    expect(afterPriorWaveCompletes.layers[0]).toMatchObject({ frozen: 1 })
    expect(afterPriorWaveCompletes.layers[0].state).not.toBe('frozen')
    expect(secondAsset?.campaign_state).not.toBe('completed')
    expect(secondAsset?.milestones.at(-1)?.state).not.toBe('earned')
    expect(secondWave?.state).not.toBe('completed')
    expect(secondWave?.completed_asset_ids).toEqual([])
    expect(afterPriorWaveCompletes.data_quality.contradictions).toEqual(expect.arrayContaining([
      expect.stringMatching(/bg_second.*freeze evidence.*governed stage\/wave order/i),
    ]))
  })

  it('derives running and completed campaign status from the contiguous accepted stage spine', () => {
    const layerSpecs = [
      ['L0', 'bg_alpha', 'brahmagyan'], ['L1', 'ga_alpha', 'ganita'], ['L2', 'bo_alpha', 'bodha'],
      ['L3', 'ka_alpha', 'kala'], ['L4', 'ph_alpha', 'phala'], ['L5', 'mi_alpha', 'mimamsa'],
    ] as const
    const assetRegistry = layerSpecs.map(([layer, asset_id, registryLayer], index) => registryAsset({
      asset_id, english_name: `${layer} Asset`, layer: registryLayer, sort_order: index + 1,
      target_table: asset_id, count_sql: `SELECT count(*) FROM ${asset_id}`,
    }))
    const manifest = manifestFor(assetRegistry, layerSpecs.map(([layer, asset_id]) => ({
      asset_id, layer, wave_index: 0, execution_obligation: 'build' as const,
    })))
    const projectAt = (currentStage: 'L3' | 'COMPLETE') => {
      const frozenLayerCount = currentStage === 'COMPLETE' ? 6 : 3
      const frozenSpecs = layerSpecs.slice(0, frozenLayerCount)
      return projectNirmanaElevationSnapshot(sourcesWithLabels({
        asset_registry: assetRegistry,
        asset_throughput: [],
        campaign_definitions: [{
          campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
          manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
        }],
        campaign_events: [
          ...foundationLaneEvents(), ...stageEventsThrough(currentStage),
          ...frozenSpecs.flatMap(([layer, assetId]) => assetMilestoneEvents(assetId, layer, layerRunIds[layer], { registryFingerprint: manifest.assets.find((asset) => asset.asset_id === assetId)!.registry_fingerprint_sha256 })),
        ],
        build_runs: frozenSpecs.map(([layer]) => ({
          id: layerRunIds[layer], chart_id: canonicalChartId, action: 'rebuild', state: 'completed', current_asset_id: null,
          created_at: observedAt, started_at: observedAt,
        })),
        build_run_assets: frozenSpecs.map(([layer, asset_id], position) => ({
          run_id: layerRunIds[layer], asset_id, position, state: 'complete',
          started_at: observedAt, ended_at: observedAt, error: null,
        })),
      }, []), { generatedAt: observedAt })
    }

    expect(projectAt('L3').campaign).toMatchObject({ current_stage: 'L3', campaign_status: 'running' })
    expect(projectAt('COMPLETE').campaign).toMatchObject({ current_stage: 'COMPLETE', campaign_status: 'completed' })
  })

  it('tolerates a historical duplicate stage receipt while the writer itself prevents a second append', () => {
    const manifest = defaultManifest()
    const transitions = stageEventsThrough('L0')
    const original = transitions[1]
    transitions.splice(2, 0, {
      ...original,
      source_ref: 'nirmana-elevation:stage-spine',
      observed_at: '2026-08-25T09:00:01.500Z',
      recorded_at: '2026-08-25T09:00:01.500Z',
    })
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [...foundationLaneEvents(), ...transitions],
    }, []), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({ current_stage: 'L0', campaign_status: 'running' })
    expect(snapshot.data_quality.contradictions).toEqual([])
  })

  it('tolerates a historical duplicate bootstrap receipt while the writer itself prevents a second append', () => {
    const manifest = defaultManifest()
    const [bootstrap, advance] = stageEventsThrough('T0_CENSUS')
    const replay = {
      ...bootstrap,
      source_ref: 'nirmana-elevation:stage-spine',
      observed_at: '2026-08-25T09:00:02.000Z',
      recorded_at: '2026-08-25T09:00:02.000Z',
    }
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'reconciling', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [bootstrap, advance, replay],
    }, []), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({ current_stage: 'T0_CENSUS', campaign_status: 'takeover' })
    expect(snapshot.stages[1]).toMatchObject({ stage_id: 'T0_CENSUS', state: 'active' })
    expect(snapshot.data_quality.contradictions).toEqual([])
  })

  it('blocks the campaign when delayed bootstrap receipt replays have conflicting prerequisite digests', () => {
    const manifest = defaultManifest()
    const [bootstrap, advance] = stageEventsThrough('T0_CENSUS')
    const conflict = {
      ...bootstrap,
      evidence_payload: { schema_version: 'nirmana-stage-transition-receipt/v1', from_stage: null, to_stage: 'BOOTSTRAP', manifest_sha256: 'f'.repeat(64) },
      source_ref: 'nirmana-elevation:stage-spine',
      observed_at: '2026-08-25T09:00:02.000Z',
      recorded_at: '2026-08-25T09:00:02.000Z',
    }
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'reconciling', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [bootstrap, advance, conflict],
    }, []), { generatedAt: observedAt })

    expect(snapshot.campaign).toMatchObject({ current_stage: 'T0_CENSUS', campaign_status: 'blocked' })
    expect(snapshot.stages[1]).toMatchObject({ stage_id: 'T0_CENSUS', state: 'blocked' })
    expect(snapshot.data_quality.contradictions).toContain(
      'Contradictory stage transition null -> BOOTSTRAP: prerequisite digests differ.',
    )
    expect(snapshot.data_quality.contradictions.some((contradiction) => contradiction.includes('prior accepted stage'))).toBe(false)
  })

  it('marks registry-English substitution as unversioned fallback when the governed English name is null', () => {
    const manifest = defaultManifest()
    const acceptedDigest = '5976b5fd12288c37e4dfc319f9593e79eb86aa3a1e2224ba387efcd6e3d8a541'
    const snapshot = projectNirmanaElevationSnapshot(sourcesWithLabels({
      campaign_definitions: [{
        campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
        manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
      }],
      campaign_events: [labelReceipt('labels-v3', acceptedDigest)],
    }, [{
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', catalogue_revision: 'labels-v3',
      asset_id: 'bg_prashna_rules', sanskrit_name: 'Praśna Niyama', english_name: null,
      description: 'Governed description', legacy_aliases: [], source_ref: 'labels-v3',
      label_digest: acceptedDigest, recorded_at: observedAt,
    }]), { generatedAt: observedAt })

    expect(snapshot.assets[0]).toMatchObject({
      sanskrit_name: 'Praśna Niyama', english_name: 'Prashna Rules', description: 'Governed description',
      identity_quality: 'unversioned_fallback',
      evidence_refs: expect.arrayContaining([
        'labels-v3',
        `registry:t0:${manifest.assets[0].registry_fingerprint_sha256}`,
        `registry:live:${manifest.assets[0].registry_fingerprint_sha256}`,
      ]),
    })
  })
})
