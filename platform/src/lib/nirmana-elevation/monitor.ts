import 'server-only'
import { createHash } from 'node:crypto'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { getPool, query } from '@/lib/db/client'
import {
  assertFreezableManifest,
  assertManifestMatchesRegistry,
  assertManifestMatchesRegistryIdentity,
  canonicalManifestDigest,
  canonicalRegistryContractDigest,
  CANONICAL_NIRMANA_CHART_ID,
  nirmanaExecutionContractForRegistryRow,
  NirmanaElevationManifestSchema,
  registryContractFingerprintInput,
  type NirmanaElevationManifest,
  type NirmanaRegistryContractRow,
} from './definitions'
import {
  NirmanaLegacyAliasSchema,
} from './label-contract'
import { loadNirmanaReleaseStatus, type NirmanaReleaseStatus } from './release'

const layerIds = {
  brahmagyan: 'L0',
  ganita: 'L1',
  bodha: 'L2',
  kala: 'L3',
  phala: 'L4',
  mimamsa: 'L5',
} as const
const registryLayerNames = {
  L0: 'brahmagyan',
  L1: 'ganita',
  L2: 'bodha',
  L3: 'kala',
  L4: 'phala',
  L5: 'mimamsa',
} as const
const layerRanks = { L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5 } as const

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (value instanceof Date) return JSON.stringify(value.toISOString())
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

function digest(value: unknown): string {
  return createHash('sha256').update(stableJson(value)).digest('hex')
}

export function canonicalNirmanaRuntimeDigest(value: unknown): string {
  return digest(value)
}

const NirmanaBaselineLabelSchema = z.object({
  asset_id: z.string().min(1),
  sanskrit_name: z.string().min(1).nullable(),
  english_name: z.string().min(1).nullable(),
  description: z.string().min(1).nullable(),
  legacy_aliases: z.array(NirmanaLegacyAliasSchema),
  source_ref: z.string().min(1).max(512),
}).strict()

export type NirmanaBaselineLabel = z.infer<typeof NirmanaBaselineLabelSchema>

function canonicalCandidateLabelCatalogueDigest(labels: NirmanaBaselineLabel[]): string {
  const parsed = z.array(NirmanaBaselineLabelSchema).min(1).parse(labels)
  if (new Set(parsed.map((label) => label.asset_id)).size !== parsed.length) {
    throw new Error('Candidate label catalogue asset IDs must be unique.')
  }
  return digest([...parsed].sort((left, right) => left.asset_id.localeCompare(right.asset_id)))
}

export interface NirmanaBaselineCandidate {
  manifest: NirmanaElevationManifest
  manifest_sha256: string
  labels: NirmanaBaselineLabel[]
  catalogue_sha256: string
  registry_identity_sha256: string
  registry_contract_sha256: string
}

export type NirmanaMonitorStatusCode =
  | 'in_sync'
  | 'baseline_missing'
  | 'plan_adaptation_required'
  | 'evidence_refresh_required'
  | 'label_refresh_required'
  | 'release_attention'
  | 'source_unavailable'

export interface NirmanaMonitorStatus {
  status: NirmanaMonitorStatusCode
  affected_asset_ids: string[]
  current_definition_sha256: string | null
  candidate_definition_sha256: string
  registry_identity_sha256: string
  registry_contract_sha256: string
  candidate_catalogue_sha256: string
}

export interface NirmanaAcceptedDefinition {
  definition_status: 'frozen'
  manifest: NirmanaElevationManifest
  manifest_sha256: string
}

export interface NirmanaMonitorComparisonObservation {
  source_error_code?: string | null
  selected_catalogue_sha256?: string | null
  selected_catalogue_asset_ids?: string[]
  incomplete_label_asset_ids?: string[]
  release_in_sync?: boolean | null
}

export interface NirmanaMonitorObservation {
  id: string
  observed_at: string
  status: NirmanaMonitorStatusCode
  affected_asset_ids: string[]
  current_definition_sha256: string | null
  candidate_definition_sha256: string | null
  registry_identity_sha256: string | null
  registry_contract_sha256: string | null
  candidate_catalogue_sha256: string | null
  selected_catalogue_sha256: string | null
  runtime_sha256: string | null
  release_sha256: string | null
  source_state: 'available' | 'unavailable'
  source_observed_at: string | null
  source_age_seconds: number | null
  freshness_state: 'fresh' | 'stale' | 'unavailable'
  freshness_deadline_at: string | null
  runtime_liveness: 'active' | 'quiet' | 'unavailable'
  release_state: 'in_sync' | 'out_of_sync' | 'unknown' | 'unavailable'
  release_observed_at: string | null
  release_age_seconds: number | null
  public_detail: string
  source_error_code: string | null
}

interface StoredFrozenDefinition {
  definition_revision: string
  definition_status: 'frozen'
  manifest: NirmanaElevationManifest
  manifest_sha256: string
}

interface AcceptedCatalogueReceipt {
  catalogue_revision: string
  catalogue_sha256: string
}

interface SelectedLabelRow {
  asset_id: string
  sanskrit_name: string | null
  english_name: string | null
  description: string | null
  legacy_aliases: NirmanaBaselineLabel['legacy_aliases']
  source_ref: string
  label_digest: string
}

const MONITOR_PUBLIC_DETAIL: Record<NirmanaMonitorStatusCode, string> = {
  in_sync: 'Program sources are synchronized.',
  baseline_missing: 'No accepted frozen program definition exists.',
  plan_adaptation_required: 'Registry identity or dependencies differ from the accepted definition.',
  evidence_refresh_required: 'Registry execution contracts require refreshed evidence.',
  label_refresh_required: 'The governed label catalogue requires refresh.',
  release_attention: 'Release reconciliation requires attention.',
  source_unavailable: 'Authoritative source is unavailable.',
}

const SOURCE_UNAVAILABLE_CODE = 'NIRMANA_SOURCE_UNAVAILABLE'
const FRESHNESS_WINDOW_SECONDS = 15 * 60
const EMPTY_CATALOGUE_SHA256 = digest([])

function orderedRegistryRows(rows: NirmanaRegistryContractRow[]): NirmanaRegistryContractRow[] {
  return [...rows].sort((left, right) => {
    const layerOrder = layerRanks[layerIds[left.layer]] - layerRanks[layerIds[right.layer]]
    if (layerOrder !== 0) return layerOrder
    const sortOrder = left.sort_order - right.sort_order
    return sortOrder !== 0 ? sortOrder : left.asset_id.localeCompare(right.asset_id)
  })
}

function deriveWaveIndices(manifest: NirmanaElevationManifest): Map<string, number> {
  const byId = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  const memo = new Map<string, number>()
  const waveFor = (assetId: string): number => {
    const existing = memo.get(assetId)
    if (existing !== undefined) return existing
    const asset = byId.get(assetId)
    if (!asset) return 0
    const sameLayerDependencies = (asset.depends_on ?? [])
      .map((dependencyId) => byId.get(dependencyId))
      .filter((dependency): dependency is NonNullable<typeof dependency> => dependency?.layer === asset.layer)
    const wave = sameLayerDependencies.length === 0
      ? 0
      : Math.max(...sameLayerDependencies.map((dependency) => waveFor(dependency.asset_id))) + 1
    memo.set(assetId, wave)
    return wave
  }
  for (const asset of manifest.assets) waveFor(asset.asset_id)
  return memo
}

export function buildNirmanaBaselineCandidate(rows: NirmanaRegistryContractRow[]): NirmanaBaselineCandidate {
  const orderedRows = orderedRegistryRows(rows)
  const manifestWithoutWaves = NirmanaElevationManifestSchema.parse({
    chart_id: CANONICAL_NIRMANA_CHART_ID,
    assets: orderedRows.map((row) => {
      const dependsOn = [...(row.depends_on ?? [])].sort()
      const registryFingerprintInput = registryContractFingerprintInput({ ...row, depends_on: dependsOn })
      return {
        asset_id: row.asset_id,
        layer: layerIds[row.layer],
        depends_on: dependsOn,
        ...nirmanaExecutionContractForRegistryRow(row),
        registry_contract: registryFingerprintInput.registry_contract,
        registry_fingerprint_sha256: canonicalRegistryContractDigest(registryFingerprintInput),
      }
    }),
  })
  const waveIndices = deriveWaveIndices(manifestWithoutWaves)
  const manifest = NirmanaElevationManifestSchema.parse({
    ...manifestWithoutWaves,
    assets: manifestWithoutWaves.assets.map((asset) => ({
      ...asset,
      wave_index: waveIndices.get(asset.asset_id),
    })),
  })
  assertFreezableManifest(manifest)

  const labels = orderedRows.map((row) => {
    const sanskritName = row.sanskrit_name ?? null
    const englishName = row.english_name ?? null
    const englishDescription = row.english_description ?? null
    return NirmanaBaselineLabelSchema.parse({
      asset_id: row.asset_id,
      sanskrit_name: sanskritName,
      english_name: englishName,
      description: sanskritName === null && englishName === null && englishDescription === null
        ? 'Not yet catalogued'
        : englishDescription,
      legacy_aliases: [],
      source_ref: `asset_registry:${row.asset_id}`,
    })
  })
  const identity = manifest.assets.map((asset) => ({
    asset_id: asset.asset_id,
    layer: asset.layer,
    depends_on: [...(asset.depends_on ?? [])].sort(),
  })).sort((left, right) => left.asset_id.localeCompare(right.asset_id))
  const contracts = manifest.assets.map((asset) => ({
    asset_id: asset.asset_id,
    registry_fingerprint_sha256: asset.registry_fingerprint_sha256,
  })).sort((left, right) => left.asset_id.localeCompare(right.asset_id))

  return {
    manifest,
    manifest_sha256: canonicalManifestDigest(manifest),
    labels,
    catalogue_sha256: canonicalCandidateLabelCatalogueDigest(labels),
    registry_identity_sha256: digest(identity),
    registry_contract_sha256: digest(contracts),
  }
}

function registryRowsFromCandidate(candidate: NirmanaBaselineCandidate): NirmanaRegistryContractRow[] {
  return candidate.manifest.assets.map((asset) => {
    if (!asset.registry_contract) throw new Error(`Candidate asset ${asset.asset_id} is missing its registry contract.`)
    return {
      asset_id: asset.asset_id,
      layer: registryLayerNames[asset.layer],
      depends_on: asset.depends_on ?? [],
      ...asset.registry_contract,
    }
  })
}

function affectedIdentityAssets(
  current: NirmanaElevationManifest,
  candidate: NirmanaElevationManifest,
): string[] {
  const identityById = (manifest: NirmanaElevationManifest) => new Map(manifest.assets.map((asset) => [
    asset.asset_id,
    stableJson({ layer: asset.layer, depends_on: [...(asset.depends_on ?? [])].sort() }),
  ]))
  const currentById = identityById(current)
  const candidateById = identityById(candidate)
  return [...new Set([...currentById.keys(), ...candidateById.keys()])]
    .filter((assetId) => currentById.get(assetId) !== candidateById.get(assetId))
    .sort()
}

function affectedContractAssets(
  current: NirmanaElevationManifest,
  candidate: NirmanaElevationManifest,
): string[] {
  const currentById = new Map(current.assets.map((asset) => [asset.asset_id, asset.registry_fingerprint_sha256]))
  return candidate.assets
    .filter((asset) => currentById.get(asset.asset_id) !== asset.registry_fingerprint_sha256)
    .map((asset) => asset.asset_id)
    .sort()
}

function affectedPlanAssets(
  current: NirmanaElevationManifest,
  candidate: NirmanaElevationManifest,
): string[] {
  const planById = (manifest: NirmanaElevationManifest) => new Map(manifest.assets.map((asset) => [
    asset.asset_id,
    stableJson({
      wave_index: asset.wave_index ?? null,
      execution_obligation: asset.execution_obligation ?? null,
      producer_id: asset.producer_id ?? null,
      covered_asset_ids: [...(asset.covered_asset_ids ?? [])].sort(),
    }),
  ]))
  const currentById = planById(current)
  const candidateById = planById(candidate)
  return [...new Set([...currentById.keys(), ...candidateById.keys()])]
    .filter((assetId) => currentById.get(assetId) !== candidateById.get(assetId))
    .sort()
}

function statusResult(
  status: NirmanaMonitorStatusCode,
  candidate: NirmanaBaselineCandidate,
  currentDefinitionSha256: string | null,
  affectedAssetIds: string[] = [],
): NirmanaMonitorStatus {
  return {
    status,
    affected_asset_ids: [...new Set(affectedAssetIds)].sort(),
    current_definition_sha256: currentDefinitionSha256,
    candidate_definition_sha256: candidate.manifest_sha256,
    registry_identity_sha256: candidate.registry_identity_sha256,
    registry_contract_sha256: candidate.registry_contract_sha256,
    candidate_catalogue_sha256: candidate.catalogue_sha256,
  }
}

export function classifyNirmanaDivergence(input: {
  definition: NirmanaAcceptedDefinition | null
  candidate: NirmanaBaselineCandidate
  observation: NirmanaMonitorComparisonObservation | null
}): NirmanaMonitorStatus {
  const { candidate, definition, observation } = input
  if (observation?.source_error_code) {
    return statusResult('source_unavailable', candidate, definition?.manifest_sha256 ?? null)
  }
  if (!definition) return statusResult('baseline_missing', candidate, null)

  const currentManifest = NirmanaElevationManifestSchema.parse(definition.manifest)
  const currentDigest = canonicalManifestDigest(currentManifest)
  if (currentDigest !== definition.manifest_sha256) {
    throw new Error('Current frozen definition digest does not match its canonical manifest.')
  }
  const candidateRegistryRows = registryRowsFromCandidate(candidate)

  try {
    assertManifestMatchesRegistryIdentity(currentManifest, candidateRegistryRows)
  } catch {
    return statusResult(
      'plan_adaptation_required',
      candidate,
      currentDigest,
      affectedIdentityAssets(currentManifest, candidate.manifest),
    )
  }

  try {
    assertManifestMatchesRegistry(currentManifest, candidateRegistryRows)
  } catch {
    return statusResult(
      'evidence_refresh_required',
      candidate,
      currentDigest,
      affectedContractAssets(currentManifest, candidate.manifest),
    )
  }

  const planDrift = affectedPlanAssets(currentManifest, candidate.manifest)
  if (planDrift.length > 0) {
    return statusResult('plan_adaptation_required', candidate, currentDigest, planDrift)
  }

  const candidateLabelAssetIds = candidate.labels.map((label) => label.asset_id)
  const selectedLabelAssetIds = observation?.selected_catalogue_asset_ids
  const labelCoverageDrift = selectedLabelAssetIds === undefined
    ? []
    : [...new Set([...candidateLabelAssetIds, ...selectedLabelAssetIds])]
      .filter((assetId) => candidateLabelAssetIds.includes(assetId) !== selectedLabelAssetIds.includes(assetId))
  const labelDigestDrift = observation?.selected_catalogue_sha256 !== undefined
    && observation.selected_catalogue_sha256 !== candidate.catalogue_sha256
  const incompleteLabelAssetIds = observation?.incomplete_label_asset_ids ?? []
  if (labelDigestDrift || labelCoverageDrift.length > 0 || incompleteLabelAssetIds.length > 0) {
    return statusResult(
      'label_refresh_required',
      candidate,
      currentDigest,
      [
        ...(labelDigestDrift ? [...candidateLabelAssetIds, ...(selectedLabelAssetIds ?? [])] : []),
        ...labelCoverageDrift,
        ...incompleteLabelAssetIds,
      ],
    )
  }

  if (observation?.release_in_sync !== undefined && observation.release_in_sync !== true) {
    return statusResult('release_attention', candidate, currentDigest)
  }

  return statusResult('in_sync', candidate, currentDigest)
}

type MonitorReadClient = Pick<PoolClient, 'query'>

async function loadMonitorInputs(client: MonitorReadClient): Promise<{
  candidate: NirmanaBaselineCandidate
  definition: StoredFrozenDefinition | null
  selectedCatalogueSha256: string | null
  selectedCatalogueAssetIds: string[]
  incompleteLabelAssetIds: string[]
  runtimeSha256: string
  runtimeLiveness: 'active' | 'quiet'
  sourceObservedAt: string
}> {
  const clock = await client.query<{ source_observed_at: string }>(
    'SELECT transaction_timestamp() AS source_observed_at',
  )
  const sourceObservedAt = clock.rows[0]?.source_observed_at
  if (!sourceObservedAt || Number.isNaN(Date.parse(sourceObservedAt))) {
    throw new Error('Monitor read transaction has no valid observation timestamp.')
  }

  const registry = await client.query<NirmanaRegistryContractRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
            sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
            target_table, count_sql, integrity_check_sql, health_probe,
            natural_key_partition, superseded_by, data_disposition, dead_flag,
            sanskrit_name, english_name, english_description
       FROM asset_registry
      ORDER BY layer, sort_order, asset_id`,
  )
  const candidate = buildNirmanaBaselineCandidate(registry.rows)

  const definitions = await client.query<StoredFrozenDefinition>(
    `SELECT definition_revision, definition_status, manifest, manifest_sha256
       FROM nirmana_evidence.nirmana_elevation_campaign_definitions
      WHERE campaign_id = 'nirmana-elevation'
        AND definition_status = 'frozen'
        AND superseded_at IS NULL
      ORDER BY created_at DESC
      LIMIT 1`,
  )
  const definition = definitions.rows[0] ?? null

  const receipts = await client.query<AcceptedCatalogueReceipt>(
    `SELECT entity_id AS catalogue_revision,
            evidence_payload ->> 'catalogue_sha256' AS catalogue_sha256
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = 'nirmana-elevation'
        AND definition_revision = $1
        AND event_type = 'asset_label_catalogue_accepted'
        AND entity_type = 'label_catalogue'
      ORDER BY recorded_at DESC, observed_at DESC, event_id DESC
      LIMIT 1`,
    [definition?.definition_revision ?? null],
  )
  const receipt = receipts.rows[0] ?? null
  const labels = await client.query<SelectedLabelRow>(
    `SELECT asset_id, sanskrit_name, english_name, description, legacy_aliases,
            source_ref, label_digest
       FROM nirmana_evidence.nirmana_elevation_asset_labels
      WHERE campaign_id = 'nirmana-elevation'
        AND definition_revision = $1
        AND catalogue_revision = $2
      ORDER BY asset_id`,
    [definition?.definition_revision ?? null, receipt?.catalogue_revision ?? null],
  )
  const selectedCatalogueSha256 = receipt !== null && labels.rows.length > 0
    ? canonicalCandidateLabelCatalogueDigest(labels.rows.map((label) => ({
      asset_id: label.asset_id,
      sanskrit_name: label.sanskrit_name,
      english_name: label.english_name,
      description: label.description,
      legacy_aliases: label.legacy_aliases,
      source_ref: label.source_ref,
    })))
    : null
  const receiptDigestValid = receipt !== null
    && /^[a-f0-9]{64}$/.test(receipt.catalogue_sha256)
    && selectedCatalogueSha256 === receipt.catalogue_sha256
    && labels.rows.every((label) => label.label_digest === receipt.catalogue_sha256)
  const selectedCatalogueAssetIds = labels.rows.map((label) => label.asset_id).sort()
  const incompleteLabelAssetIds = [...new Set([
    ...labels.rows
    .filter((label) => label.sanskrit_name === null && label.english_name === null && label.description === null)
      .map((label) => label.asset_id),
    ...(!receiptDigestValid && receipt !== null ? candidate.labels.map((label) => label.asset_id) : []),
  ])].sort()

  const throughput = await client.query(
    `SELECT asset_id, chart_id, state, last_built_at
       FROM asset_throughput
      WHERE chart_id = $1 OR chart_id IS NULL
      ORDER BY asset_id, chart_id NULLS FIRST, last_built_at DESC NULLS LAST`,
    [CANONICAL_NIRMANA_CHART_ID],
  )
  const runs = await client.query(
    `SELECT id, chart_id, action, state, current_asset_id, created_at, started_at
       FROM build_runs
      WHERE chart_id = $1
        AND state IN ('planned', 'running', 'paused')
      ORDER BY created_at, id`,
    [CANONICAL_NIRMANA_CHART_ID],
  )
  const runAssets = await client.query(
    `SELECT bra.run_id, bra.asset_id, bra.position, bra.state,
            bra.started_at, bra.ended_at, bra.error
       FROM build_run_assets bra
       JOIN build_runs br ON br.id = bra.run_id
      WHERE br.chart_id = $1
        AND br.state IN ('planned', 'running', 'paused')
      ORDER BY bra.run_id, bra.position, bra.asset_id`,
    [CANONICAL_NIRMANA_CHART_ID],
  )
  const substeps = await client.query(
    `SELECT bsp.chart_id, bsp.asset_id, bsp.substep_key, bsp.build_fingerprint,
            bsp.rows_written, bsp.completed_at
       FROM build_substep_progress bsp
      WHERE bsp.chart_id = $1
        AND EXISTS (
          SELECT 1 FROM build_runs br
           WHERE br.chart_id = bsp.chart_id
             AND br.state IN ('planned', 'running', 'paused')
        )
      ORDER BY bsp.asset_id, bsp.substep_key`,
    [CANONICAL_NIRMANA_CHART_ID],
  )
  const runtimeSha256 = canonicalNirmanaRuntimeDigest({
    asset_throughput: throughput.rows,
    build_runs: runs.rows,
    build_run_assets: runAssets.rows,
    build_substep_progress: substeps.rows,
  })

  return {
    candidate,
    definition,
    selectedCatalogueSha256,
    selectedCatalogueAssetIds,
    incompleteLabelAssetIds,
    runtimeSha256,
    runtimeLiveness: runs.rows.length > 0 ? 'active' : 'quiet',
    sourceObservedAt,
  }
}

async function readMonitorInputs(): Promise<Awaited<ReturnType<typeof loadMonitorInputs>>> {
  const client = await (await getPool()).connect()
  try {
    await client.query('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    const inputs = await loadMonitorInputs(client)
    await client.query('COMMIT')
    return inputs
  } catch (error) {
    await client.query('ROLLBACK').catch(() => undefined)
    throw error
  } finally {
    client.release()
  }
}

function releaseState(release: NirmanaReleaseStatus): NirmanaMonitorObservation['release_state'] {
  if (release.release.production_in_sync === true) return 'in_sync'
  if (release.release.production_in_sync === false) return 'out_of_sync'
  if (release.sources.some((source) => source.state === 'unavailable')) return 'unavailable'
  return 'unknown'
}

function releaseAgeSeconds(release: NirmanaReleaseStatus): number {
  const ages = release.sources
    .map((source) => source.age_seconds)
    .filter((age): age is number => typeof age === 'number' && Number.isFinite(age) && age >= 0)
  return ages.length > 0 ? Math.floor(Math.max(...ages)) : 0
}

async function insertMonitorObservation(input: Omit<NirmanaMonitorObservation, 'id' | 'observed_at' | 'freshness_deadline_at'>): Promise<NirmanaMonitorObservation> {
  const affectedAssetIds = [...new Set(input.affected_asset_ids)].sort()
  const inserted = await query<NirmanaMonitorObservation>(
    `INSERT INTO nirmana_elevation_monitor_observations
       (status, affected_asset_ids, current_definition_sha256,
        candidate_definition_sha256, registry_identity_sha256,
        registry_contract_sha256, candidate_catalogue_sha256,
        selected_catalogue_sha256, runtime_sha256, release_sha256,
        source_state, source_observed_at, source_age_seconds,
        freshness_state, freshness_deadline_at, runtime_liveness,
        release_state, release_observed_at, release_age_seconds,
        public_detail, source_error_code)
     VALUES ($1, $2::text[], $3, $4, $5, $6, $7, $8, $9, $10,
             $11, $12, $13, $14, $12::timestamptz + INTERVAL '15 minutes',
             $15, $16, $17, $18, $19, $20)
     RETURNING id, observed_at, status, affected_asset_ids,
               current_definition_sha256, candidate_definition_sha256,
               registry_identity_sha256, registry_contract_sha256,
               candidate_catalogue_sha256, selected_catalogue_sha256,
               runtime_sha256, release_sha256, source_state, source_observed_at,
               source_age_seconds, freshness_state, freshness_deadline_at,
               runtime_liveness, release_state, release_observed_at,
               release_age_seconds, public_detail, source_error_code`,
    [
      input.status,
      affectedAssetIds,
      input.current_definition_sha256,
      input.candidate_definition_sha256,
      input.registry_identity_sha256,
      input.registry_contract_sha256,
      input.candidate_catalogue_sha256,
      input.selected_catalogue_sha256,
      input.runtime_sha256,
      input.release_sha256,
      input.source_state,
      input.source_observed_at,
      input.source_age_seconds,
      input.freshness_state,
      input.runtime_liveness,
      input.release_state,
      input.release_observed_at,
      input.release_age_seconds,
      input.public_detail,
      input.source_error_code,
    ],
  )
  const observation = inserted.rows[0]
  if (!observation) throw new Error('Nirmana elevation monitor observation was not recorded.')
  return observation
}

export async function runNirmanaElevationMonitor(): Promise<NirmanaMonitorObservation> {
  let observation: Omit<NirmanaMonitorObservation, 'id' | 'observed_at' | 'freshness_deadline_at'>
  try {
    const inputs = await readMonitorInputs()
    const release = await loadNirmanaReleaseStatus()
    const releaseObservedAt = release.release.observed_at
    if (!releaseObservedAt || Number.isNaN(Date.parse(releaseObservedAt))) {
      throw new Error('Release reconciliation has no valid observation timestamp.')
    }
    const releaseSha256 = digest({
      main_sha: release.release.main_sha,
      deployed_sha: release.release.deployed_sha,
      deployed_revision: release.release.deployed_revision,
      production_in_sync: release.release.production_in_sync,
    })
    const sourceAgeSeconds = Math.max(
      0,
      Math.floor((Date.now() - Date.parse(inputs.sourceObservedAt)) / 1000),
    )
    const comparison = classifyNirmanaDivergence({
      definition: inputs.definition,
      candidate: inputs.candidate,
      observation: {
        selected_catalogue_sha256: inputs.selectedCatalogueSha256,
        selected_catalogue_asset_ids: inputs.selectedCatalogueAssetIds,
        incomplete_label_asset_ids: inputs.incompleteLabelAssetIds,
        release_in_sync: release.release.production_in_sync,
      },
    })
    observation = {
      ...comparison,
      selected_catalogue_sha256: inputs.selectedCatalogueSha256 ?? EMPTY_CATALOGUE_SHA256,
      runtime_sha256: inputs.runtimeSha256,
      release_sha256: releaseSha256,
      source_state: 'available',
      source_observed_at: inputs.sourceObservedAt,
      source_age_seconds: sourceAgeSeconds,
      freshness_state: sourceAgeSeconds <= FRESHNESS_WINDOW_SECONDS ? 'fresh' : 'stale',
      runtime_liveness: inputs.runtimeLiveness,
      release_state: releaseState(release),
      release_observed_at: releaseObservedAt,
      release_age_seconds: releaseAgeSeconds(release),
      public_detail: MONITOR_PUBLIC_DETAIL[comparison.status],
      source_error_code: null,
    }
  } catch {
    console.error('[nirmana-elevation] monitor source read failed', {
      error_code: SOURCE_UNAVAILABLE_CODE,
    })
    observation = {
      status: 'source_unavailable',
      affected_asset_ids: [],
      current_definition_sha256: null,
      candidate_definition_sha256: null,
      registry_identity_sha256: null,
      registry_contract_sha256: null,
      candidate_catalogue_sha256: null,
      selected_catalogue_sha256: null,
      runtime_sha256: null,
      release_sha256: null,
      source_state: 'unavailable',
      source_observed_at: null,
      source_age_seconds: null,
      freshness_state: 'unavailable',
      runtime_liveness: 'unavailable',
      release_state: 'unavailable',
      release_observed_at: null,
      release_age_seconds: null,
      public_detail: MONITOR_PUBLIC_DETAIL.source_unavailable,
      source_error_code: SOURCE_UNAVAILABLE_CODE,
    }
  }
  return insertMonitorObservation(observation)
}
