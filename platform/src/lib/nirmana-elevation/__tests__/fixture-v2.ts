import { createHash } from 'node:crypto'
import { canonicalManifestDigest, canonicalRegistryContractDigest } from '../definitions'
import {
  projectNirmanaElevationSnapshot,
  type NirmanaElevationRawSources,
} from '../snapshot'
import type { NirmanaReleaseStatus } from '../release'
import { NIRMANA_STAGE_IDS } from '../vocab'

const observedAt = '2026-08-26T00:00:00.000Z'
const chartId = '482012f1-710e-4a25-994a-93821f5871aa'
const producerRunId = '11111111-1111-4111-8111-111111111111'
const activeRunId = '33333333-3333-4333-8333-333333333333'

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

function sha256(value: unknown): string {
  return createHash('sha256').update(stableJson(value)).digest('hex')
}

type RegistryAsset = NirmanaElevationRawSources['asset_registry'][number]

function registryAsset(overrides: Partial<RegistryAsset>): RegistryAsset {
  const assetId = overrides.asset_id ?? 'bg_prashna_rules'
  return {
    asset_id: assetId,
    english_name: assetId,
    layer: 'brahmagyan',
    scope: 'per_chart',
    sort_order: 0,
    has_writer: true,
    asset_type: 'data',
    asset_kind: 'data',
    catalog_status: 'CURRENT',
    is_active: true,
    depends_on: [],
    target_table: assetId,
    count_sql: `SELECT count(*) FROM ${assetId}`,
    integrity_check_sql: null,
    health_probe: null,
    natural_key_partition: null,
    superseded_by: null,
    data_disposition: null,
    dead_flag: null,
    ...overrides,
  }
}

const registry = [
  registryAsset({
    asset_id: 'bg_medical_mappings', english_name: 'Medical Mappings', sort_order: 0,
  }),
  registryAsset({
    asset_id: 'bg_sign_medical', english_name: 'Sign Medical', sort_order: 1,
    has_writer: false, depends_on: ['bg_medical_mappings'],
  }),
  registryAsset({
    asset_id: 'bg_nakshatra_medical', english_name: 'Nakshatra Medical', sort_order: 2,
    has_writer: false, depends_on: ['bg_medical_mappings'],
  }),
  registryAsset({
    asset_id: 'bg_prashna_rules', english_name: 'Prashna Rules', sort_order: 3,
    depends_on: ['bg_sign_medical'],
  }),
  registryAsset({
    asset_id: 'ka_smriti', english_name: 'Kala Smriti', layer: 'kala', sort_order: 4,
    has_writer: false, asset_kind: 'service', asset_type: 'service', health_probe: { endpoint: '/health/ka-smriti' },
    target_table: 'ka_smriti', count_sql: 'SELECT count(*) FROM ka_smriti',
  }),
]

const registryById = new Map(registry.map((asset) => [asset.asset_id, asset]))

function manifestAsset(
  assetId: string,
  layer: 'L0' | 'L3',
  waveIndex: number,
  executionObligation: 'build' | 'producer_covered' | 'probe',
  extras: { producer_id?: string; covered_asset_ids?: string[] } = {},
) {
  const row = registryById.get(assetId)
  if (!row) throw new Error(`Missing projected fixture registry row ${assetId}.`)
  const depends_on = row.depends_on ?? []
  const registry_contract = {
    sort_order: row.sort_order,
    scope: row.scope,
    asset_kind: row.asset_kind,
    catalog_status: row.catalog_status,
    is_active: row.is_active,
    has_writer: row.has_writer,
    target_table: row.target_table,
    count_sql: row.count_sql,
    integrity_check_sql: row.integrity_check_sql,
    health_probe: row.health_probe,
    natural_key_partition: row.natural_key_partition,
    superseded_by: row.superseded_by,
    data_disposition: row.data_disposition,
    dead_flag: row.dead_flag,
  }
  return {
    asset_id: assetId,
    layer,
    wave_index: waveIndex,
    execution_obligation: executionObligation,
    depends_on,
    registry_contract,
    registry_fingerprint_sha256: canonicalRegistryContractDigest({
      asset_id: assetId, layer, depends_on, registry_contract,
    }),
    ...extras,
  }
}

const manifest = {
  chart_id: chartId,
  assets: [
    manifestAsset('bg_medical_mappings', 'L0', 0, 'build', { covered_asset_ids: ['bg_nakshatra_medical', 'bg_sign_medical'] }),
    manifestAsset('bg_sign_medical', 'L0', 1, 'producer_covered', { producer_id: 'bg_medical_mappings' }),
    manifestAsset('bg_nakshatra_medical', 'L0', 1, 'producer_covered', { producer_id: 'bg_medical_mappings' }),
    manifestAsset('bg_prashna_rules', 'L0', 2, 'build'),
    manifestAsset('ka_smriti', 'L3', 0, 'probe'),
  ],
}

const labelInputs = [
  {
    asset_id: 'bg_medical_mappings', sanskrit_name: 'Cikitsā Mapping', english_name: 'Medical Mappings',
    description: 'Producer for governed medical mappings', legacy_aliases: [], source_ref: 'catalogue:fixture-v1:bg_medical_mappings',
  },
  {
    asset_id: 'bg_sign_medical', sanskrit_name: 'Rāśi Medical', english_name: 'Sign Medical',
    description: 'Producer-covered foundation asset', legacy_aliases: [], source_ref: 'catalogue:fixture-v1:bg_sign_medical',
  },
  {
    asset_id: 'bg_nakshatra_medical', sanskrit_name: 'Nakṣatra Medical', english_name: 'Nakshatra Medical',
    description: 'Producer-covered lunar mansion medical asset', legacy_aliases: [], source_ref: 'catalogue:fixture-v1:bg_nakshatra_medical',
  },
  {
    asset_id: 'bg_prashna_rules', sanskrit_name: 'Praśna Rules', english_name: 'Prashna Rules',
    description: 'Active foundation build asset', legacy_aliases: [], source_ref: 'catalogue:fixture-v1:bg_prashna_rules',
  },
  {
    asset_id: 'ka_smriti', sanskrit_name: 'Kāla Smṛti', english_name: 'Kala Smriti',
    description: 'Per-varsha digest',
    legacy_aliases: [{ asset_id: 'A22', sanskrit_name: 'Varsha-Darshan', english_name: 'Per-varsha digest' }],
    source_ref: 'catalogue:fixture-v1:ka_smriti',
  },
]
const labelDigest = sha256([...labelInputs].sort((left, right) => left.asset_id.localeCompare(right.asset_id)))
const labels = labelInputs.map((label) => ({
  campaign_id: 'nirmana-elevation',
  definition_revision: 'v1',
  catalogue_revision: 'fixture-v1',
  ...label,
  label_digest: labelDigest,
  recorded_at: observedAt,
}))

function stageEvents() {
  const lastStage = NIRMANA_STAGE_IDS.indexOf('L0')
  return NIRMANA_STAGE_IDS.slice(0, lastStage + 1).map((toStage, index) => {
    const at = new Date(Date.parse(observedAt) + index * 1_000).toISOString()
    return {
      campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'stage_transition_accepted',
      entity_type: 'campaign_stage', entity_id: toStage, layer: null,
      evidence_payload: {
        schema_version: 'nirmana-stage-transition-receipt/v1',
        from_stage: index === 0 ? null : NIRMANA_STAGE_IDS[index - 1],
        to_stage: toStage,
        manifest_sha256: 'a'.repeat(64),
      },
      source_kind: 'server_reconstructed', source_ref: 'nirmana-elevation:stage-spine', observed_at: at, recorded_at: at,
    }
  })
}

function foundationPayload(laneId: string) {
  const base = { schema_version: 'nirmana-foundation-lane-receipt/v1' as const, lane_id: laneId, manifest_sha256: 'a'.repeat(64) }
  if (laneId === 'A') return { ...base, asset_count: 1 }
  if (laneId === 'B') return { ...base, build_run_count: 0, terminal_build_run_count: 0 }
  if (laneId === 'C') return { ...base, registry_fingerprint_set_sha256: 'b'.repeat(64), manifest_asset_count: 1, live_registry_asset_count: 1, invalidated_analysis_count: 0 }
  if (laneId === 'D') return { ...base, main_sha: 'b'.repeat(40), serving_sha: 'b'.repeat(40), serving_revision: 'amjis-web-01799-abc', ci_run_id: '123' }
  return { ...base, migration_filename: '592_nirmana_elevation_campaign_evidence.sql', migration_sha256: 'c'.repeat(64) }
}

function assetEvents(assetId: string, eventTypes: string[], runId?: string, startOffsetSeconds = 10) {
  return eventTypes.map((eventType, index) => ({
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: eventType,
    entity_type: 'asset', entity_id: assetId, layer: assetId === 'ka_smriti' ? 'L3' : 'L0',
    evidence_payload: eventType === 'optimization_verdict_accepted' ? { change_required: true } : {},
    source_kind: 'campaign_evidence',
    source_ref: eventType === 'accepted_rebuild_observed' || eventType === 'producer_covered'
      ? `build_run:${runId}` : `event:${assetId}:${eventType}`,
    observed_at: new Date(Date.parse(observedAt) + startOffsetSeconds * 1_000 + index * 1_000).toISOString(),
    recorded_at: new Date(Date.parse(observedAt) + startOffsetSeconds * 1_000 + index * 1_000).toISOString(),
  }))
}

const campaignEvents = [
  ...stageEvents(),
  ...['A', 'B', 'C', 'D', 'E'].map((laneId, index) => ({
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'foundation_lane_accepted',
    entity_type: 'foundation_lane', entity_id: laneId, layer: null,
    evidence_payload: foundationPayload(laneId),
    source_kind: 'server_reconstructed', source_ref: `nirmana-elevation:foundation-lane:${laneId}`,
    observed_at: new Date(Date.parse(observedAt) + 20_000 + index * 1_000).toISOString(),
    recorded_at: new Date(Date.parse(observedAt) + 20_000 + index * 1_000).toISOString(),
  })),
  ...assetEvents('bg_medical_mappings', [
    'asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
    'accepted_rebuild_observed', 'integrity_verified', 'asset_frozen',
  ], producerRunId),
  ...assetEvents('bg_sign_medical', [
    'asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered',
    'integrity_verified', 'asset_frozen',
  ], producerRunId, 20),
  ...assetEvents('bg_nakshatra_medical', [
    'asset_analysis_accepted', 'optimization_verdict_accepted', 'producer_covered',
    'integrity_verified', 'asset_frozen',
  ], producerRunId, 20),
  ...assetEvents('bg_prashna_rules', ['asset_analysis_accepted', 'optimization_verdict_accepted'], undefined, 30),
  ...assetEvents('ka_smriti', ['asset_analysis_accepted'], undefined, 30),
  {
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'build_run_authorized',
    entity_type: 'build_run', entity_id: activeRunId, layer: 'L0',
    evidence_payload: { wave_index: 2, asset_ids: ['bg_prashna_rules'], authorization_sha256: 'd'.repeat(64) },
    source_kind: 'campaign_authorization', source_ref: `build_run:${activeRunId}`,
    observed_at: '2026-08-26T00:01:00.000Z', recorded_at: '2026-08-26T00:01:01.000Z',
  },
  {
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', event_type: 'asset_label_catalogue_accepted',
    entity_type: 'label_catalogue', entity_id: 'fixture-v1', layer: null,
    evidence_payload: { catalogue_sha256: labelDigest, asset_count: labels.length },
    source_kind: 'governed_catalogue', source_ref: 'label_catalogue:fixture-v1',
    observed_at: '2026-08-26T00:02:00.000Z', recorded_at: '2026-08-26T00:02:01.000Z',
  },
]

const raw: NirmanaElevationRawSources = {
  asset_registry: registry,
  asset_throughput: [
    { asset_id: 'bg_medical_mappings', chart_id: chartId, state: 'lit', last_built_at: observedAt },
    { asset_id: 'bg_sign_medical', chart_id: chartId, state: 'lit', last_built_at: observedAt },
    { asset_id: 'bg_nakshatra_medical', chart_id: chartId, state: 'lit', last_built_at: observedAt },
  ],
  build_runs: [
    {
      id: producerRunId, chart_id: chartId, action: 'rebuild', state: 'completed', current_asset_id: null,
      created_at: observedAt, started_at: observedAt, triggered_by: 'nirmana-campaign',
    },
    {
      id: activeRunId, chart_id: chartId, action: 'rebuild', state: 'running', current_asset_id: 'bg_prashna_rules',
      created_at: '2026-08-26T00:01:00.000Z', started_at: '2026-08-26T00:01:00.000Z', triggered_by: 'nirmana-campaign',
    },
  ],
  build_run_assets: [
    { run_id: producerRunId, asset_id: 'bg_medical_mappings', position: 0, state: 'complete', started_at: observedAt, ended_at: observedAt, error: null },
    { run_id: activeRunId, asset_id: 'bg_prashna_rules', position: 0, state: 'building', started_at: '2026-08-26T00:01:00.000Z', ended_at: null, error: null },
  ],
  build_substep_progress: [],
  campaign_definitions: [{
    campaign_id: 'nirmana-elevation', definition_revision: 'v1', definition_status: 'frozen', manifest,
    manifest_sha256: canonicalManifestDigest(manifest), created_at: observedAt,
  }],
  campaign_events: campaignEvents,
  asset_labels: labels,
}

const releaseStatus: NirmanaReleaseStatus = {
  release: {
    main_sha: 'a'.repeat(40), deployed_sha: 'a'.repeat(40), deployed_revision: 'amjis-web-fixture',
    production_in_sync: true, observed_at: '2026-08-26T00:02:30.000Z',
  },
  sources: [
    { source_id: 'github_main', provenance: 'GitHub commits API/feed', state: 'fresh' as const, observed_at: '2026-08-26T00:02:30.000Z', age_seconds: 30, error_code: null, error_message: null },
    { source_id: 'cloud_run_web', provenance: 'Cloud Run Service traffic via ADC', state: 'fresh' as const, observed_at: '2026-08-26T00:02:30.000Z', age_seconds: 30, error_code: null, error_message: null },
    { source_id: 'artifact_registry_commit', provenance: 'Serving revision immutable commit provenance', state: 'fresh' as const, observed_at: '2026-08-26T00:02:30.000Z', age_seconds: 30, error_code: null, error_message: null },
  ],
  gaps: [],
}

function makeSnapshot(overrides: Partial<NirmanaElevationRawSources> = {}) {
  return projectNirmanaElevationSnapshot({ ...raw, ...overrides }, {
    generatedAt: '2026-08-26T00:03:00.000Z',
    releaseStatus,
  })
}

const definitionSha256 = canonicalManifestDigest(manifest)
const inSyncObservation = {
  id: '44444444-4444-4444-8444-444444444444',
  observed_at: '2026-08-26T00:02:00.000Z',
  status: 'in_sync' as const,
  affected_asset_ids: [],
  current_definition_sha256: definitionSha256,
  candidate_definition_sha256: definitionSha256,
  candidate_catalogue_sha256: labelDigest,
  source_state: 'available' as const,
  source_observed_at: '2026-08-26T00:02:00.000Z',
  freshness_state: 'fresh' as const,
  freshness_deadline_at: '2026-08-26T00:17:00.000Z',
  source_error_code: null,
  runtime_liveness: 'quiet' as const,
}

/** No monitor receipt is deliberately distinct from the complete program-sync fixtures below. */
export const fixtureV2 = makeSnapshot()

/** An identity-only frozen baseline is synchronized, not positioned in the campaign. */
export const frozenBaselineInSyncSnapshot = makeSnapshot({
  campaign_events: [],
  monitor_observations: [inSyncObservation],
})

/** Drift is projected as review-required; it never mutates the accepted denominator. */
export const planAdaptationSnapshot = makeSnapshot({
  monitor_observations: [{
    ...inSyncObservation,
    id: '55555555-5555-4555-8555-555555555555',
    status: 'plan_adaptation_required',
    affected_asset_ids: ['ga_positions'],
    candidate_definition_sha256: '9'.repeat(64),
  }],
})

export const NIRMANA_ELEVATION_SNAPSHOT_V2_FIXTURE = fixtureV2
