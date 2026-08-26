import 'server-only'
import { createHash } from 'node:crypto'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { getPool, query } from '@/lib/db/client'
import { getNirmanaL0AnalysisReceiptBase } from '@/generated/nirmana-l0-analysis-receipts'

const LayerSchema = z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5'])
const layerPrefixes = { L0: 'bg_', L1: 'ga_', L2: 'bo_', L3: 'ka_', L4: 'ph_', L5: 'mi_' } as const
const layerRanks = { L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5 } as const
const registryLayers = { brahmagyan: 'L0', ganita: 'L1', bodha: 'L2', kala: 'L3', phala: 'L4', mimamsa: 'L5' } as const
const legacyLayerIdentityExceptions = new Map([['lel_events', 'L5']])
const fixedNonBuildDispositions = new Map([
  ['bg_gochara_citation_resolution', 'static_acceptance'],
  ['bg_sarvatobhadra_grid', 'empty_acceptance'],
  ['lel_events', 'source_acceptance'],
])
const fixedProducerCoverage = new Map([
  ['bg_sign_medical', 'bg_medical_mappings'],
  ['bg_nakshatra_medical', 'bg_medical_mappings'],
  ['bg_transit_engine', 'bg_transit_rules'],
])
export const CANONICAL_NIRMANA_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

const RegistryContractSchema = z.object({
  sort_order: z.number().int(),
  scope: z.enum(['global', 'per_chart']),
  asset_kind: z.enum(['data', 'service', 'artifact']),
  catalog_status: z.enum(['CURRENT', 'DRAFT', 'RETIRED']),
  is_active: z.boolean(),
  has_writer: z.boolean(),
  target_table: z.string().min(1).nullable(),
  count_sql: z.string().min(1).nullable(),
  integrity_check_sql: z.string().min(1).nullable(),
  health_probe: z.record(z.string(), z.unknown()).nullable(),
  natural_key_partition: z.string().min(1).nullable(),
  superseded_by: z.string().min(1).nullable(),
  data_disposition: z.enum(['RETAINED_AS_CAPITAL', 'SUPERSEDED_IN_PLACE', 'DROPPABLE']).nullable(),
  dead_flag: z.boolean().nullable(),
}).strict()

const ManifestAssetSchema = z.object({
  asset_id: z.string().min(1),
  layer: LayerSchema,
  wave_index: z.number().int().nonnegative().optional(),
  execution_obligation: z.enum(['build', 'probe', 'producer_covered', 'static_acceptance', 'source_acceptance', 'empty_acceptance', 'retired_with_disposition', 'unresolved']).optional(),
  depends_on: z.array(z.string().min(1)).optional(),
  registry_contract: RegistryContractSchema.optional(),
  registry_fingerprint_sha256: z.string().regex(/^[a-f0-9]{64}$/).optional(),
  producer_id: z.string().optional(),
  covered_asset_ids: z.array(z.string()).optional(),
}).strict()

const RegistryFingerprintInputSchema = z.object({
  asset_id: z.string().min(1),
  layer: LayerSchema,
  depends_on: z.array(z.string().min(1)),
  registry_contract: RegistryContractSchema,
}).strict()

export interface NirmanaRegistryContractRow {
  asset_id: string
  layer: keyof typeof registryLayers
  depends_on: string[] | null
  sanskrit_name?: string | null
  english_name?: string | null
  english_description?: string | null
  sort_order: number
  scope: 'global' | 'per_chart'
  asset_kind: 'data' | 'service' | 'artifact'
  catalog_status: 'CURRENT' | 'DRAFT' | 'RETIRED'
  is_active: boolean
  has_writer: boolean
  target_table: string | null
  count_sql: string | null
  integrity_check_sql: string | null
  health_probe: Record<string, unknown> | null
  natural_key_partition: string | null
  superseded_by: string | null
  data_disposition: 'RETAINED_AS_CAPITAL' | 'SUPERSEDED_IN_PLACE' | 'DROPPABLE' | null
  dead_flag: boolean | null
}

export type NirmanaExecutionObligation = Exclude<
  NirmanaElevationManifest['assets'][number]['execution_obligation'],
  undefined
>

/**
 * Applies the same source-audited non-build and producer-coverage decisions
 * enforced by assertFreezableManifest. Unknown shapes remain unresolved so a
 * baseline candidate cannot silently invent an execution disposition.
 */
export function nirmanaExecutionContractForRegistryRow(row: NirmanaRegistryContractRow): {
  execution_obligation: NirmanaExecutionObligation
  producer_id?: string
  covered_asset_ids?: string[]
} {
  const fixedDisposition = fixedNonBuildDispositions.get(row.asset_id)
  if (fixedDisposition) return { execution_obligation: fixedDisposition as NirmanaExecutionObligation }

  const producerId = fixedProducerCoverage.get(row.asset_id)
  if (producerId) return { execution_obligation: 'producer_covered', producer_id: producerId }

  const coveredAssetIds = [...fixedProducerCoverage.entries()]
    .filter(([, candidateProducerId]) => candidateProducerId === row.asset_id)
    .map(([coveredAssetId]) => coveredAssetId)
    .sort()

  if (row.catalog_status === 'RETIRED') {
    return { execution_obligation: 'retired_with_disposition' }
  }
  if (row.asset_kind === 'service' && (row.has_writer || row.health_probe)) {
    return { execution_obligation: 'probe' }
  }
  if (row.is_active && row.has_writer && row.asset_kind !== 'service') {
    return {
      execution_obligation: 'build',
      ...(coveredAssetIds.length > 0 ? { covered_asset_ids: coveredAssetIds } : {}),
    }
  }
  return { execution_obligation: 'unresolved' }
}

export function registryContractFingerprintInput(row: NirmanaRegistryContractRow) {
  return RegistryFingerprintInputSchema.parse({
    asset_id: row.asset_id,
    layer: registryLayers[row.layer],
    depends_on: row.depends_on ?? [],
    registry_contract: {
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
    },
  })
}

export function canonicalRegistryContractDigest(input: unknown): string {
  const parsed = RegistryFingerprintInputSchema.parse(input)
  return createHash('sha256').update(stableJson(parsed)).digest('hex')
}

export const NirmanaElevationManifestSchema = z.object({
  chart_id: z.literal(CANONICAL_NIRMANA_CHART_ID),
  assets: z.array(ManifestAssetSchema).min(1),
}).strict().superRefine((manifest, context) => {
  const assetIds = new Set<string>()
  for (const [index, asset] of manifest.assets.entries()) {
    const isLegacyIdentityException = legacyLayerIdentityExceptions.get(asset.asset_id) === asset.layer
    if (!asset.asset_id.startsWith(layerPrefixes[asset.layer]) && !isLegacyIdentityException) {
      context.addIssue({ code: 'custom', path: ['assets', index, 'asset_id'], message: `${asset.layer} asset IDs must begin with ${layerPrefixes[asset.layer]}.` })
    }
    if (assetIds.has(asset.asset_id)) {
      context.addIssue({ code: 'custom', path: ['assets', index, 'asset_id'], message: 'Manifest asset IDs must be unique.' })
    }
    assetIds.add(asset.asset_id)
  }

  const byId = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  for (const [index, asset] of manifest.assets.entries()) {
    if (!asset.depends_on) continue
    const dependencies = new Set(asset.depends_on)
    if (dependencies.size !== asset.depends_on.length) {
      context.addIssue({ code: 'custom', path: ['assets', index, 'depends_on'], message: 'Manifest dependencies must be unique.' })
    }
    for (const dependencyId of dependencies) {
      const dependency = byId.get(dependencyId)
      if (!dependency) {
        context.addIssue({ code: 'custom', path: ['assets', index, 'depends_on'], message: `Dependency ${dependencyId} is not present in the manifest.` })
      } else if (dependencyId === asset.asset_id) {
        context.addIssue({ code: 'custom', path: ['assets', index, 'depends_on'], message: 'An asset cannot depend on itself.' })
      } else if (layerRanks[dependency.layer] > layerRanks[asset.layer]) {
        context.addIssue({ code: 'custom', path: ['assets', index, 'depends_on'], message: `Dependency ${dependencyId} is in a later layer.` })
      }
    }
  }

  const visiting = new Set<string>()
  const visited = new Set<string>()
  const visit = (assetId: string): boolean => {
    if (visiting.has(assetId)) return true
    if (visited.has(assetId)) return false
    visiting.add(assetId)
    for (const dependencyId of byId.get(assetId)?.depends_on ?? []) {
      if (byId.has(dependencyId) && visit(dependencyId)) return true
    }
    visiting.delete(assetId)
    visited.add(assetId)
    return false
  }
  if (manifest.assets.some((asset) => visit(asset.asset_id))) {
    context.addIssue({ code: 'custom', path: ['assets'], message: 'Manifest dependency graph must be acyclic.' })
  }
})

export type NirmanaElevationManifest = z.infer<typeof NirmanaElevationManifestSchema>

export function parseNirmanaElevationManifest(manifest: unknown): NirmanaElevationManifest | null {
  const parsed = NirmanaElevationManifestSchema.safeParse(manifest)
  return parsed.success ? parsed.data : null
}

export function canonicalManifestDigest(manifest: unknown): string {
  const parsed = NirmanaElevationManifestSchema.parse(manifest)
  return createHash('sha256').update(stableJson(parsed)).digest('hex')
}

export function assertFreezableManifest(manifest: NirmanaElevationManifest): void {
  const byId = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  const waveMemo = new Map<string, number>()
  const expectedWave = (assetId: string): number => {
    const memoized = waveMemo.get(assetId)
    if (memoized !== undefined) return memoized
    const asset = byId.get(assetId)
    if (!asset) return 0
    const sameLayerDependencies = (asset.depends_on ?? [])
      .map((dependencyId) => byId.get(dependencyId))
      .filter((dependency): dependency is NonNullable<typeof dependency> => dependency?.layer === asset.layer)
    const wave = sameLayerDependencies.length === 0
      ? 0
      : Math.max(...sameLayerDependencies.map((dependency) => expectedWave(dependency.asset_id))) + 1
    waveMemo.set(assetId, wave)
    return wave
  }

  for (const asset of manifest.assets) {
    if (!asset.execution_obligation) throw new Error(`Frozen manifest asset ${asset.asset_id} is missing an execution obligation.`)
    if (asset.execution_obligation === 'unresolved') throw new Error(`Frozen manifest asset ${asset.asset_id} cannot retain an unresolved execution obligation.`)
    if (asset.wave_index === undefined) throw new Error(`Frozen manifest asset ${asset.asset_id} is missing a wave index.`)
    if (!asset.depends_on) throw new Error(`Frozen manifest asset ${asset.asset_id} is missing its dependency contract.`)
    if (!asset.registry_contract) throw new Error(`Frozen manifest asset ${asset.asset_id} is missing its registry contract.`)
    if (!asset.registry_fingerprint_sha256) throw new Error(`Frozen manifest asset ${asset.asset_id} is missing its registry fingerprint.`)
    const registryFingerprint = canonicalRegistryContractDigest({
      asset_id: asset.asset_id,
      layer: asset.layer,
      depends_on: asset.depends_on,
      registry_contract: asset.registry_contract,
    })
    if (registryFingerprint !== asset.registry_fingerprint_sha256) {
      throw new Error(`Frozen manifest asset ${asset.asset_id} has a mismatched registry fingerprint.`)
    }
    if (asset.wave_index !== expectedWave(asset.asset_id)) {
      throw new Error(`Frozen manifest asset ${asset.asset_id} has wave ${asset.wave_index}; expected ${expectedWave(asset.asset_id)} from its same-layer dependencies.`)
    }
    if (asset.asset_id === 'lel_events' && (asset.layer !== 'L5' || asset.execution_obligation !== 'source_acceptance')) {
      throw new Error('The legacy lel_events identity is permitted only as the L5 user-authored source disposition.')
    }
    const fixedDisposition = fixedNonBuildDispositions.get(asset.asset_id)
    if (fixedDisposition !== undefined && asset.execution_obligation !== fixedDisposition) {
      throw new Error(`Asset ${asset.asset_id} must retain its adjudicated ${fixedDisposition} obligation.`)
    }
    if (['static_acceptance', 'source_acceptance', 'empty_acceptance'].includes(asset.execution_obligation)
      && fixedDisposition !== asset.execution_obligation) {
      throw new Error(`Asset ${asset.asset_id} is not an adjudicated ${asset.execution_obligation} exception.`)
    }
    if (asset.execution_obligation === 'build'
      && (!asset.registry_contract.is_active
        || !asset.registry_contract.has_writer
        || asset.registry_contract.catalog_status === 'RETIRED'
        || asset.registry_contract.asset_kind === 'service')) {
      throw new Error(`Build asset ${asset.asset_id} is not an active non-service registry writer.`)
    }
    if (asset.execution_obligation === 'probe'
      && (asset.registry_contract.asset_kind !== 'service'
        || (!asset.registry_contract.has_writer && !asset.registry_contract.health_probe))) {
      throw new Error(`Probe asset ${asset.asset_id} must have either a service writer or a registry health probe.`)
    }
    if (asset.execution_obligation === 'retired_with_disposition'
      && (asset.registry_contract.catalog_status !== 'RETIRED'
        || asset.registry_contract.is_active
        || !asset.registry_contract.superseded_by
        || !asset.registry_contract.data_disposition)) {
      throw new Error(`Retired asset ${asset.asset_id} is missing its successor or data disposition.`)
    }
    if (asset.execution_obligation === 'producer_covered') {
      if (!asset.producer_id || asset.producer_id === asset.asset_id) throw new Error(`Producer-covered asset ${asset.asset_id} must name a distinct producer.`)
      if (fixedProducerCoverage.get(asset.asset_id) !== asset.producer_id) throw new Error(`Producer-covered asset ${asset.asset_id} is not pinned to its source-audited producer.`)
      const producer = byId.get(asset.producer_id)
      if (!producer || producer.execution_obligation !== 'build') throw new Error(`Producer-covered asset ${asset.asset_id} must name an in-manifest build producer.`)
      if (producer.covered_asset_ids && !producer.covered_asset_ids.includes(asset.asset_id)) throw new Error(`Producer ${asset.producer_id} does not declare coverage of ${asset.asset_id}.`)
    } else if (asset.producer_id) {
      throw new Error(`Only producer-covered asset ${asset.asset_id} may name a producer.`)
    }
    if (asset.covered_asset_ids) {
      const covered = new Set(asset.covered_asset_ids)
      if (covered.size !== asset.covered_asset_ids.length || [...covered].some((id) => id === asset.asset_id || !byId.has(id))) {
        throw new Error(`Asset ${asset.asset_id} has an invalid covered-asset reference.`)
      }
      if (asset.execution_obligation !== 'build' || asset.covered_asset_ids.some((id) => byId.get(id)?.execution_obligation !== 'producer_covered' || byId.get(id)?.producer_id !== asset.asset_id)) {
        throw new Error(`Asset ${asset.asset_id} has a non-reciprocal covered-asset reference.`)
      }
      const expectedCovered = [...fixedProducerCoverage.entries()]
        .filter(([, producerId]) => producerId === asset.asset_id)
        .map(([coveredId]) => coveredId)
        .sort()
      if (expectedCovered.join('\0') !== [...asset.covered_asset_ids].sort().join('\0')) {
        throw new Error(`Asset ${asset.asset_id} does not match its source-audited coverage set.`)
      }
    }
  }
}

export function parseFreezableNirmanaElevationManifest(manifest: unknown): NirmanaElevationManifest | null {
  const parsed = parseNirmanaElevationManifest(manifest)
  if (!parsed) return null
  try {
    assertFreezableManifest(parsed)
    return parsed
  } catch {
    return null
  }
}

export function assertManifestMatchesRegistry(
  manifest: NirmanaElevationManifest,
  registryRows: NirmanaRegistryContractRow[],
): void {
  const manifestById = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  const registryById = new Map(registryRows.map((row) => [row.asset_id, row]))
  if (manifestById.size !== registryById.size) {
    throw new Error(`Frozen manifest contains ${manifestById.size} assets but the live registry contains ${registryById.size}.`)
  }
  for (const [assetId, asset] of manifestById) {
    const registryRow = registryById.get(assetId)
    if (!registryRow) throw new Error(`Frozen manifest asset ${assetId} is absent from the live registry.`)
    const liveFingerprint = canonicalRegistryContractDigest(registryContractFingerprintInput(registryRow))
    if (liveFingerprint !== asset.registry_fingerprint_sha256) {
      throw new Error(`Frozen manifest asset ${assetId} does not match the live registry contract.`)
    }
  }
}

/**
 * Revalidates the immutable denominator/DAG identity after a definition has
 * frozen. Operational registry contracts are intentionally excluded here:
 * the per-asset method requires reviewed correctness/integrity changes after
 * T0, and those changes are accepted through fingerprinted analysis evidence.
 * Adding/removing an asset, moving its layer, or changing its dependency set
 * still invalidates the denominator globally.
 */
export function assertManifestMatchesRegistryIdentity(
  manifest: NirmanaElevationManifest,
  registryRows: NirmanaRegistryContractRow[],
): void {
  const manifestById = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  const registryById = new Map(registryRows.map((row) => [row.asset_id, row]))
  if (manifestById.size !== registryById.size) {
    throw new Error(`Frozen manifest contains ${manifestById.size} assets but the live registry contains ${registryById.size}.`)
  }
  for (const [assetId, asset] of manifestById) {
    const registryRow = registryById.get(assetId)
    if (!registryRow) throw new Error(`Frozen manifest asset ${assetId} is absent from the live registry.`)
    if (registryLayers[registryRow.layer] !== asset.layer) {
      throw new Error(`Frozen manifest asset ${assetId} changed layer in the live registry.`)
    }
    const frozenDependencies = [...(asset.depends_on ?? [])].sort()
    const liveDependencies = [...(registryRow.depends_on ?? [])].sort()
    if (stableJson(frozenDependencies) !== stableJson(liveDependencies)) {
      throw new Error(`Frozen manifest asset ${assetId} changed its dependency set in the live registry.`)
    }
  }
}

export interface CreateNirmanaElevationDefinitionInput {
  campaign_id: string
  definition_revision: string
  definition_status: 'reconciling'
  manifest: unknown
  manifest_sha256: string
  created_by: string
}

export class NirmanaElevationDefinitionConflictError extends Error {
  constructor(message = 'Campaign definition revision already exists with different immutable contents.') {
    super(message)
  }
}

export class NirmanaElevationEvidenceConflictError extends Error {
  constructor() {
    super('Evidence idempotency key already exists with different immutable contents.')
  }
}

export class NirmanaElevationEvidenceValidationError extends Error {}

function nirmanaRevisionLockKey(campaignId: string, definitionRevision: string): string {
  return `nirmana-elevation:${campaignId}:${definitionRevision}`
}

async function acquireNirmanaRevisionLock(
  client: PoolClient,
  campaignId: string,
  definitionRevision: string,
): Promise<void> {
  await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [
    nirmanaRevisionLockKey(campaignId, definitionRevision),
  ])
}

export function assertNirmanaGitCommitMatchesDeployment(
  sourceRef: string,
  runtime: { nodeEnv?: string; deployedSha?: string } = {
    nodeEnv: process.env.NODE_ENV,
    deployedSha: process.env.NIRMANA_DEPLOYED_SHA,
  },
): void {
  if (!gitCommitSourceRef.test(sourceRef)) {
    throw new NirmanaElevationEvidenceValidationError('Evidence requires source_kind=git_commit and an exact git:<40-hex> commit source.')
  }
  const deployedSha = runtime.deployedSha?.trim().toLowerCase()
  if (deployedSha !== undefined && !/^[a-f0-9]{40}$/.test(deployedSha)) {
    throw new NirmanaElevationEvidenceValidationError('NIRMANA_DEPLOYED_SHA must be an exact 40-hex commit SHA.')
  }
  if (!deployedSha) {
    if (runtime.nodeEnv === 'production') {
      throw new NirmanaElevationEvidenceValidationError('NIRMANA_DEPLOYED_SHA is required to accept Git-backed evidence in production.')
    }
    return
  }
  if (sourceRef !== `git:${deployedSha}`) {
    throw new NirmanaElevationEvidenceValidationError('Evidence Git source does not match the currently deployed commit.')
  }
}

/**
 * The sole server-side insertion seam for campaign definitions. Callers must
 * supply the digest they received with the evidence; it is checked before the
 * INSERT, so a valid-looking but mismatched hash cannot freeze a denominator.
 */
export async function createNirmanaElevationDefinition(input: CreateNirmanaElevationDefinitionInput): Promise<'created' | 'idempotent'> {
  const manifest = NirmanaElevationManifestSchema.parse(input.manifest)
  const canonicalDigest = canonicalManifestDigest(manifest)
  if (input.manifest_sha256 !== canonicalDigest) {
    throw new Error('Campaign definition manifest digest does not match its canonical manifest.')
  }
  const inserted = await query(
    `INSERT INTO nirmana_elevation_campaign_definitions
       (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
     VALUES ($1, $2, $3, $4::jsonb, $5, $6)
     ON CONFLICT (campaign_id, definition_revision) DO NOTHING
     RETURNING definition_revision`,
    [input.campaign_id, input.definition_revision, input.definition_status, JSON.stringify(manifest), canonicalDigest, input.created_by],
  )
  if (inserted.rowCount === 1) return 'created'

  const existing = await query<{ definition_status: string; manifest_sha256: string }>(
    `SELECT definition_status, manifest_sha256
       FROM nirmana_elevation_campaign_definitions
      WHERE campaign_id = $1 AND definition_revision = $2`,
    [input.campaign_id, input.definition_revision],
  )
  if (existing.rows[0]?.definition_status === input.definition_status && existing.rows[0]?.manifest_sha256 === canonicalDigest) {
    return 'idempotent'
  }
  throw new NirmanaElevationDefinitionConflictError()
}

export interface FreezeNirmanaElevationDefinitionInput {
  campaign_id: string
  definition_revision: string
  manifest: unknown
  manifest_sha256: string
}

export interface SupersedeNirmanaElevationDefinitionInput {
  campaign_id: string
  expected_current_revision: string
  expected_current_manifest_sha256: string
  new_definition_revision: string
  new_manifest: unknown
  new_manifest_sha256: string
  created_by: string
}

export interface AcceptNirmanaBaselineCandidateInput {
  campaign_id: 'nirmana-elevation'
  source_observation_id: string
  definition_revision: string
  expected_candidate_sha256: string
  expected_candidate_catalogue_sha256: string
  created_by: string
}

interface StoredNirmanaBaselineObservation {
  id: string
  observed_at: string | Date
  status: string
  current_definition_sha256: string | null
  candidate_definition_sha256: string | null
  registry_identity_sha256: string | null
  registry_contract_sha256: string | null
  candidate_catalogue_sha256: string | null
  source_state: string
  source_observed_at: string | Date | null
  freshness_state: string
  freshness_deadline_at: string | Date | null
  source_error_code: string | null
  currently_fresh: boolean
}

function canonicalObservationInstant(value: string | Date | null): string | null {
  if (value === null) return null
  const instant = value instanceof Date ? value : new Date(value)
  return Number.isNaN(instant.getTime()) ? null : instant.toISOString()
}

/**
 * Accepts the exact live-registry baseline candidate, its frozen definition,
 * and its governed label catalogue as one serializable transaction. This path
 * records no stage transition or asset-lifecycle receipt.
 */
export async function acceptNirmanaBaselineCandidate(
  input: AcceptNirmanaBaselineCandidateInput,
): Promise<'created' | 'idempotent'> {
  if (!z.string().uuid().safeParse(input.source_observation_id).success
    || !/^[A-Za-z0-9._-]{1,128}$/.test(input.definition_revision)
    || !/^[a-f0-9]{64}$/.test(input.expected_candidate_sha256)
    || !/^[a-f0-9]{64}$/.test(input.expected_candidate_catalogue_sha256)) {
    throw new NirmanaElevationDefinitionConflictError('Baseline candidate acceptance input is invalid.')
  }

  const client = await (await getPool()).connect()
  try {
    await client.query('BEGIN')
    await client.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [
      `nirmana-elevation:${input.campaign_id}:baseline-acceptance`,
    ])

    const stored = await client.query<StoredNirmanaDefinition>(
      `SELECT definition_revision, definition_status, manifest, manifest_sha256,
              created_by, superseded_at
         FROM nirmana_elevation_campaign_definitions
        WHERE campaign_id = $1
        ORDER BY definition_revision
        FOR UPDATE`,
      [input.campaign_id],
    )
    const observations = await client.query<StoredNirmanaBaselineObservation>(
      `SELECT id::text, observed_at, status, current_definition_sha256,
              candidate_definition_sha256, registry_identity_sha256,
              registry_contract_sha256, candidate_catalogue_sha256,
              source_state, source_observed_at, freshness_state,
              freshness_deadline_at, source_error_code,
              (freshness_state = 'fresh'
                AND freshness_deadline_at >= transaction_timestamp()) AS currently_fresh
         FROM nirmana_elevation_monitor_observations
        WHERE id = $1
        FOR SHARE`,
      [input.source_observation_id],
    )
    const sourceObservation = observations.rows[0]
    const registry = await client.query<NirmanaRegistryContractRow>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
              sanskrit_name, english_name, english_description,
              sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
              target_table, count_sql, integrity_check_sql, health_probe,
              natural_key_partition, superseded_by, data_disposition, dead_flag
         FROM asset_registry
        ORDER BY asset_id
        FOR SHARE`,
    )

    let candidate: Awaited<ReturnType<typeof import('./monitor')['buildNirmanaBaselineCandidate']>>
    try {
      const { buildNirmanaBaselineCandidate } = await import('./monitor')
      candidate = buildNirmanaBaselineCandidate(registry.rows)
    } catch {
      throw new NirmanaElevationDefinitionConflictError('Live registry cannot produce a freezable baseline candidate.')
    }
    if (candidate.manifest_sha256 !== input.expected_candidate_sha256
      || candidate.catalogue_sha256 !== input.expected_candidate_catalogue_sha256) {
      throw new NirmanaElevationDefinitionConflictError('Baseline candidate changed; refresh both candidate digests before acceptance.')
    }

    const observationObservedAt = canonicalObservationInstant(sourceObservation?.observed_at ?? null)
    const sourceObservedAt = canonicalObservationInstant(sourceObservation?.source_observed_at ?? null)
    const freshnessDeadlineAt = canonicalObservationInstant(sourceObservation?.freshness_deadline_at ?? null)
    const exactSourceObservation = sourceObservation !== undefined
      && sourceObservation.id === input.source_observation_id
      && sourceObservation.status === 'baseline_missing'
      && sourceObservation.current_definition_sha256 === null
      && sourceObservation.source_state === 'available'
      && sourceObservation.source_error_code === null
      && sourceObservation.freshness_state === 'fresh'
      && observationObservedAt !== null
      && sourceObservedAt !== null
      && freshnessDeadlineAt !== null
      && sourceObservation.candidate_definition_sha256 === input.expected_candidate_sha256
      && sourceObservation.candidate_definition_sha256 === candidate.manifest_sha256
      && sourceObservation.candidate_catalogue_sha256 === input.expected_candidate_catalogue_sha256
      && sourceObservation.candidate_catalogue_sha256 === candidate.catalogue_sha256
      && sourceObservation.registry_identity_sha256 === candidate.registry_identity_sha256
      && sourceObservation.registry_contract_sha256 === candidate.registry_contract_sha256
    if (!exactSourceObservation) {
      throw new NirmanaElevationDefinitionConflictError('Baseline acceptance requires the exact source-available baseline_missing monitor observation and its candidate digests.')
    }

    const target = stored.rows.find((row) => row.definition_revision === input.definition_revision)
    const current = stored.rows.find((row) => row.superseded_at === null)
    const exactDefinitionRetry = target !== undefined
      && target === current
      && target.definition_status === 'frozen'
      && target.manifest_sha256 === candidate.manifest_sha256
      && stableJson(target.manifest) === stableJson(candidate.manifest)

    const { recordNirmanaElevationLabelCatalogueInTransaction } = await import('./labels')
    const catalogueInput = {
      campaign_id: input.campaign_id,
      definition_revision: input.definition_revision,
      catalogue_revision: input.definition_revision,
      labels: candidate.labels,
      catalogue_sha256: candidate.catalogue_sha256,
      recorded_by: input.created_by,
    }
    const receiptProvenance = {
      source_observation_id: input.source_observation_id,
      source_observation_observed_at: observationObservedAt,
      source_snapshot_observed_at: sourceObservedAt,
      source_freshness_deadline_at: freshnessDeadlineAt,
      candidate_manifest_sha256: candidate.manifest_sha256,
      registry_identity_sha256: candidate.registry_identity_sha256,
      registry_contract_sha256: candidate.registry_contract_sha256,
      candidate_catalogue_sha256: candidate.catalogue_sha256,
    }

    if (exactDefinitionRetry) {
      let catalogueOutcome: 'created' | 'idempotent'
      try {
        catalogueOutcome = await recordNirmanaElevationLabelCatalogueInTransaction(client, catalogueInput, receiptProvenance)
      } catch {
        throw new NirmanaElevationDefinitionConflictError('Frozen baseline candidate does not have the exact accepted label catalogue.')
      }
      if (catalogueOutcome !== 'idempotent') {
        throw new NirmanaElevationDefinitionConflictError('Frozen baseline candidate does not have the exact accepted label catalogue.')
      }
      await client.query('COMMIT')
      return 'idempotent'
    }

    if (target !== undefined || current !== undefined) {
      throw new NirmanaElevationDefinitionConflictError('A different current campaign definition already exists.')
    }
    if (sourceObservation.currently_fresh !== true) {
      throw new NirmanaElevationDefinitionConflictError('Baseline monitor observation is no longer fresh; refresh the proposal before acceptance.')
    }

    const inserted = await client.query(
      `INSERT INTO nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
       VALUES ($1, $2, 'reconciling', $3::jsonb, $4, $5)
       RETURNING definition_revision`,
      [input.campaign_id, input.definition_revision, JSON.stringify(candidate.manifest),
        candidate.manifest_sha256, input.created_by],
    )
    if (inserted.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()

    const frozen = await client.query(
      `UPDATE nirmana_elevation_campaign_definitions
          SET definition_status = 'frozen'
        WHERE campaign_id = $1
          AND definition_revision = $2
          AND definition_status = 'reconciling'
          AND manifest_sha256 = $3
      RETURNING definition_revision`,
      [input.campaign_id, input.definition_revision, candidate.manifest_sha256],
    )
    if (frozen.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()

    let catalogueOutcome: 'created' | 'idempotent'
    try {
      catalogueOutcome = await recordNirmanaElevationLabelCatalogueInTransaction(client, catalogueInput, receiptProvenance)
    } catch {
      throw new NirmanaElevationDefinitionConflictError('Baseline candidate label catalogue is not acceptable.')
    }
    if (catalogueOutcome !== 'created') {
      throw new NirmanaElevationDefinitionConflictError('Baseline candidate label catalogue conflicts with existing evidence.')
    }

    await client.query('COMMIT')
    return 'created'
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

/** Freezes only the exact previously recorded reconciling definition revision. */
export async function freezeNirmanaElevationDefinition(input: FreezeNirmanaElevationDefinitionInput): Promise<'frozen' | 'idempotent'> {
  const manifest = NirmanaElevationManifestSchema.parse(input.manifest)
  assertFreezableManifest(manifest)
  const canonicalDigest = canonicalManifestDigest(manifest)
  if (input.manifest_sha256 !== canonicalDigest) throw new Error('Campaign definition manifest digest does not match its canonical manifest.')

  const registry = await query<NirmanaRegistryContractRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
            sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
            target_table, count_sql, integrity_check_sql, health_probe,
            natural_key_partition, superseded_by, data_disposition, dead_flag
       FROM asset_registry
      ORDER BY asset_id`,
  )
  assertManifestMatchesRegistry(manifest, registry.rows)

  const frozen = await query(
    `UPDATE nirmana_elevation_campaign_definitions
        SET definition_status = 'frozen'
      WHERE campaign_id = $1
        AND definition_revision = $2
        AND definition_status = 'reconciling'
        AND manifest_sha256 = $3
     RETURNING definition_revision`,
    [input.campaign_id, input.definition_revision, canonicalDigest],
  )
  if (frozen.rowCount === 1) return 'frozen'

  const existing = await query<{ definition_status: string; manifest_sha256: string }>(
    `SELECT definition_status, manifest_sha256
       FROM nirmana_elevation_campaign_definitions
      WHERE campaign_id = $1 AND definition_revision = $2`,
    [input.campaign_id, input.definition_revision],
  )
  if (existing.rows[0]?.definition_status === 'frozen' && existing.rows[0]?.manifest_sha256 === canonicalDigest) return 'idempotent'
  throw new NirmanaElevationDefinitionConflictError()
}

interface StoredNirmanaDefinition {
  definition_revision: string
  definition_status: 'reconciling' | 'frozen' | 'superseded'
  manifest: unknown
  manifest_sha256: string
  created_by: string
  superseded_at: string | null
}

/**
 * Replaces one exact current frozen definition with a distinct already-frozen
 * revision on one dedicated connection. The old row is superseded before the
 * insert so the one-current-definition index remains satisfied; any later
 * failure rolls the update back with the insert.
 */
export async function supersedeNirmanaElevationDefinition(
  input: SupersedeNirmanaElevationDefinitionInput,
): Promise<'superseded' | 'idempotent'> {
  if (input.expected_current_revision === input.new_definition_revision) {
    throw new NirmanaElevationDefinitionConflictError()
  }
  if (!/^[a-f0-9]{64}$/.test(input.expected_current_manifest_sha256)) {
    throw new NirmanaElevationDefinitionConflictError()
  }
  const manifest = NirmanaElevationManifestSchema.parse(input.new_manifest)
  assertFreezableManifest(manifest)
  const canonicalDigest = canonicalManifestDigest(manifest)
  if (input.new_manifest_sha256 !== canonicalDigest) {
    throw new Error('Replacement campaign definition manifest digest does not match its canonical manifest.')
  }

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await client.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    await acquireNirmanaRevisionLock(client, input.campaign_id, input.expected_current_revision)
    const stored = await client.query<StoredNirmanaDefinition>(
      `SELECT definition_revision, definition_status, manifest, manifest_sha256,
              created_by, superseded_at
         FROM nirmana_elevation_campaign_definitions
        WHERE campaign_id = $1
          AND definition_revision = ANY($2::text[])
        ORDER BY definition_revision
        FOR UPDATE`,
      [input.campaign_id, [input.expected_current_revision, input.new_definition_revision]],
    )
    const current = stored.rows.find((row) => row.definition_revision === input.expected_current_revision)
    const replacement = stored.rows.find((row) => row.definition_revision === input.new_definition_revision)

    const exactRetry = current?.definition_status === 'superseded'
      && current.superseded_at !== null
      && current.manifest_sha256 === input.expected_current_manifest_sha256
      && replacement?.definition_status === 'frozen'
      && replacement.superseded_at === null
      && replacement.manifest_sha256 === canonicalDigest
      && stableJson(replacement.manifest) === stableJson(manifest)
    if (exactRetry) {
      await client.query('COMMIT')
      return 'idempotent'
    }

    if (replacement
      || current?.definition_status !== 'frozen'
      || current.superseded_at !== null
      || current.manifest_sha256 !== input.expected_current_manifest_sha256) {
      throw new NirmanaElevationDefinitionConflictError()
    }

    const currentManifest = NirmanaElevationManifestSchema.parse(current.manifest)
    const dispatcherWaveLocks = [...new Set(currentManifest.assets
      .filter((asset) => asset.execution_obligation === 'build' && asset.wave_index !== undefined)
      .map((asset) => `${input.campaign_id}:${input.expected_current_revision}:${asset.layer}:wave-${asset.wave_index}`))]
      .sort()
    for (const lockKey of dispatcherWaveLocks) {
      await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [lockKey])
    }

    // The evidence ingress takes the same revision lock before any provenance
    // read or insert. The dispatcher takes the per-wave locks before reading the
    // definition. Together these close races within the governed ingresses;
    // table locks also stabilize the count while this transaction runs. Direct
    // writers outside these protocols still require a future DB trigger/FK.
    await client.query('LOCK TABLE nirmana_elevation_campaign_events, build_runs IN SHARE MODE')
    const usage = await client.query<{ event_count: number; build_run_count: number }>(
      `SELECT (SELECT count(*)::int
                 FROM nirmana_elevation_campaign_events
                WHERE campaign_id = $1 AND definition_revision = $2) AS event_count,
              (SELECT count(*)::int
                 FROM build_runs
                WHERE plan_manifest #>> '{campaign_control,campaign_id}' = $1
                  AND plan_manifest #>> '{campaign_control,definition_revision}' = $2) AS build_run_count`,
      [input.campaign_id, input.expected_current_revision],
    )
    if ((usage.rows[0]?.event_count ?? 0) !== 0) {
      throw new NirmanaElevationDefinitionConflictError('Expected frozen campaign definition already has campaign events and cannot be superseded.')
    }
    if ((usage.rows[0]?.build_run_count ?? 0) !== 0) {
      throw new NirmanaElevationDefinitionConflictError('Expected frozen campaign definition already has build runs and cannot be superseded.')
    }

    const registry = await client.query<NirmanaRegistryContractRow>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
              sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
              target_table, count_sql, integrity_check_sql, health_probe,
              natural_key_partition, superseded_by, data_disposition, dead_flag
         FROM asset_registry
        ORDER BY asset_id
        FOR SHARE`,
    )
    assertManifestMatchesRegistry(manifest, registry.rows)

    const superseded = await client.query(
      `UPDATE nirmana_elevation_campaign_definitions
          SET definition_status = 'superseded', superseded_at = clock_timestamp()
        WHERE campaign_id = $1
          AND definition_revision = $2
          AND definition_status = 'frozen'
          AND superseded_at IS NULL
          AND manifest_sha256 = $3
      RETURNING definition_revision`,
      [input.campaign_id, input.expected_current_revision, input.expected_current_manifest_sha256],
    )
    if (superseded.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()

    const inserted = await client.query(
      `INSERT INTO nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
       VALUES ($1, $2, 'frozen', $3::jsonb, $4, $5)
       RETURNING definition_revision`,
      [input.campaign_id, input.new_definition_revision, JSON.stringify(manifest), canonicalDigest, input.created_by],
    )
    if (inserted.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()
    await client.query('COMMIT')
    return 'superseded'
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}

export interface RecordNirmanaElevationEvidenceInput {
  campaign_id: string
  definition_revision: string
  idempotency_key: string
  event_type: string
  entity_type: string
  entity_id: string
  layer: string | null
  evidence_payload: unknown
  source_kind: string
  source_ref: string
  observed_at: string
  recorded_by: string
}

const OutputDigestEvidenceSchema = z.object({
  output_digest: z.string().regex(/^[a-f0-9]{64}$/),
  output_digest_spec_sha256: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()
export const NirmanaAssetAnalysisEvidenceSchema = z.object({
  registry_fingerprint_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  analysis_digest: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()
const OptimizationMeasurementSchema = z.object({
  status: z.enum(['measured', 'insufficient_history', 'not_applicable']),
  sample_count: z.number().int().nonnegative().nullable(),
  p50_ms: z.number().finite().nonnegative().nullable(),
  p90_ms: z.number().finite().nonnegative().nullable(),
  hotspot: z.string().min(1).max(1024).nullable(),
}).strict().superRefine((measurement, context) => {
  if (measurement.status === 'measured') {
    if (measurement.sample_count === null || measurement.sample_count < 1) {
      context.addIssue({ code: 'custom', path: ['sample_count'], message: 'Measured optimization evidence requires at least one sample.' })
    }
    if (measurement.p50_ms === null || measurement.p90_ms === null || measurement.hotspot === null) {
      context.addIssue({ code: 'custom', message: 'Measured optimization evidence requires p50_ms, p90_ms, and hotspot.' })
    }
  } else if (measurement.p50_ms !== null || measurement.p90_ms !== null) {
    context.addIssue({ code: 'custom', message: 'Unmeasured optimization evidence cannot claim p50_ms or p90_ms.' })
  }
  if (measurement.status === 'not_applicable'
    && (measurement.sample_count !== null || measurement.hotspot !== null)) {
    context.addIssue({ code: 'custom', message: 'Not-applicable optimization evidence must leave measurement fields null.' })
  }
  if (measurement.p50_ms !== null && measurement.p90_ms !== null && measurement.p90_ms < measurement.p50_ms) {
    context.addIssue({ code: 'custom', path: ['p90_ms'], message: 'p90_ms cannot be lower than p50_ms.' })
  }
})
export const NirmanaOptimizationVerdictEvidenceSchema = z.object({
  registry_fingerprint_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  analysis_digest: z.string().regex(/^[a-f0-9]{64}$/),
  verdict: z.enum(['optimize', 'correct', 'optimize_and_correct', 'examined_and_already_efficient', 'non_build_disposition']),
  basis: z.object({
    measurement: OptimizationMeasurementSchema,
    evidence_refs: z.array(z.string().min(1).max(512)).min(1).max(32),
  }).strict(),
  proposal: z.object({
    action: z.enum(['optimize', 'correct', 'optimize_and_correct', 'no_change', 'formal_disposition']),
    summary: z.string().min(1).max(2048),
    output_contract: z.enum(['digest_identical', 'correctness_change', 'not_applicable']),
  }).strict(),
}).strict().superRefine((payload, context) => {
  const expected = {
    optimize: { action: 'optimize', output_contract: 'digest_identical' },
    correct: { action: 'correct', output_contract: 'correctness_change' },
    optimize_and_correct: { action: 'optimize_and_correct', output_contract: 'correctness_change' },
    examined_and_already_efficient: { action: 'no_change', output_contract: 'digest_identical' },
    non_build_disposition: { action: 'formal_disposition', output_contract: 'not_applicable' },
  }[payload.verdict]
  if (payload.proposal.action !== expected.action) {
    context.addIssue({ code: 'custom', path: ['proposal', 'action'], message: `Verdict ${payload.verdict} requires proposal action ${expected.action}.` })
  }
  if (payload.proposal.output_contract !== expected.output_contract) {
    context.addIssue({ code: 'custom', path: ['proposal', 'output_contract'], message: `Verdict ${payload.verdict} requires output contract ${expected.output_contract}.` })
  }
})
export type NirmanaOptimizationVerdictEvidence = z.infer<typeof NirmanaOptimizationVerdictEvidenceSchema>

const NirmanaAssetAnalysisReceiptSchema = z.object({
  schema_version: z.literal('nirmana-asset-analysis-receipt/v1'),
  base: z.object({
    schema_version: z.literal('nirmana-asset-analysis-receipt-base/v1'),
    asset_id: z.string().min(1),
    layer: z.literal('L0'),
    writer_digest_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
    grounding: z.object({
      convergence_commit: z.string().regex(/^[a-f0-9]{40}$/),
      frozen_manifest_source: z.literal('nirmana_elevation_campaign_definitions.manifest'),
      writer_digest_ref: z.literal('platform/src/generated/nirmana-writer-digests.json'),
    }).strict(),
  }).strict(),
  frozen_manifest_asset: ManifestAssetSchema,
  current_registry_contract: RegistryFingerprintInputSchema,
}).strict()

export type NirmanaAssetAnalysisReceipt = z.infer<typeof NirmanaAssetAnalysisReceiptSchema>

export function canonicalNirmanaAssetAnalysisReceiptDigest(receipt: unknown): string {
  const parsed = NirmanaAssetAnalysisReceiptSchema.parse(receipt)
  return createHash('sha256').update(stableJson(parsed)).digest('hex')
}

export function canonicalNirmanaAssetAnalysisDigestForRegistryRow(
  assetId: string,
  registryRow: NirmanaRegistryContractRow,
  frozenManifestAsset: unknown,
): string {
  const receiptBase = getNirmanaL0AnalysisReceiptBase(assetId)
  if (!receiptBase) {
    throw new NirmanaElevationEvidenceValidationError(`No deployed L0 analysis receipt base exists for ${assetId}.`)
  }
  const manifestAsset = ManifestAssetSchema.parse(frozenManifestAsset)
  if (manifestAsset.asset_id !== assetId || manifestAsset.layer !== 'L0') {
    throw new NirmanaElevationEvidenceValidationError(`Frozen manifest asset ${assetId} does not match its deployed analysis receipt base.`)
  }
  return canonicalNirmanaAssetAnalysisReceiptDigest({
    schema_version: 'nirmana-asset-analysis-receipt/v1',
    base: receiptBase,
    frozen_manifest_asset: manifestAsset,
    current_registry_contract: registryContractFingerprintInput(registryRow),
  })
}
const buildRunSourceRef = /^build_run:([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i
const BuildRunAuthorizationEvidenceSchema = z.object({
  wave_index: z.number().int().nonnegative(),
  asset_ids: z.array(z.string().min(1).max(256)).min(1).max(256),
  authorization_sha256: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()
const gitCommitSourceRef = /^git:[0-9a-f]{40}$/

interface CurrentAssetAnalysisContext {
  registryFingerprint: string
  analysisDigest: string
}

async function loadCurrentAssetAnalysisContext(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<CurrentAssetAnalysisContext> {
  const receiptBase = getNirmanaL0AnalysisReceiptBase(input.entity_id)
  if (!receiptBase || input.layer !== 'L0') {
    throw new NirmanaElevationEvidenceValidationError('Evidence requires a reconstructable deployed analysis receipt for the frozen asset.')
  }
  const registry = await client.query<NirmanaRegistryContractRow & { frozen_manifest_asset: unknown }>(
    `SELECT registry.asset_id, registry.layer, COALESCE(registry.depends_on, '{}') AS depends_on,
            registry.sort_order, registry.scope, registry.asset_kind, registry.catalog_status,
            registry.is_active, registry.has_writer, registry.target_table, registry.count_sql,
            registry.integrity_check_sql, registry.health_probe, registry.natural_key_partition,
            registry.superseded_by, registry.data_disposition, registry.dead_flag,
            manifest_asset.value AS frozen_manifest_asset
       FROM asset_registry registry
       JOIN nirmana_elevation_campaign_definitions definition
         ON definition.campaign_id = $1
        AND definition.definition_revision = $2
        AND definition.definition_status = 'frozen'
        AND definition.superseded_at IS NULL
       JOIN LATERAL jsonb_array_elements(definition.manifest -> 'assets') AS manifest_asset(value)
         ON manifest_asset.value ->> 'asset_id' = registry.asset_id
        AND manifest_asset.value ->> 'layer' = $4
      WHERE registry.asset_id = $3`,
    [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
  )
  const registryRow = registry.rows[0]
  if (!registryRow) {
    throw new NirmanaElevationEvidenceValidationError('Evidence requires an asset in the current frozen definition and matching layer.')
  }
  const currentFingerprint = canonicalRegistryContractDigest(registryContractFingerprintInput(registryRow))
  return {
    registryFingerprint: currentFingerprint,
    analysisDigest: canonicalNirmanaAssetAnalysisDigestForRegistryRow(input.entity_id, registryRow, registryRow.frozen_manifest_asset),
  }
}

async function requireAcceptedAssetAnalysisProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaAssetAnalysisEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'git_commit') {
    throw new NirmanaElevationEvidenceValidationError('asset_analysis_accepted requires exact registry/analysis SHA-256 evidence and a Git commit source.')
  }
  assertNirmanaGitCommitMatchesDeployment(input.source_ref)
  const current = await loadCurrentAssetAnalysisContext(client, input)
  if (payload.data.registry_fingerprint_sha256 !== current.registryFingerprint) {
    throw new NirmanaElevationEvidenceValidationError('asset_analysis_accepted registry fingerprint does not match the current live contract.')
  }
  if (payload.data.analysis_digest !== current.analysisDigest) {
    throw new NirmanaElevationEvidenceValidationError('asset_analysis_accepted analysis digest does not match the canonical deployed analysis receipt.')
  }
}

async function requireAcceptedOptimizationVerdictProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaOptimizationVerdictEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'git_commit') {
    throw new NirmanaElevationEvidenceValidationError('optimization_verdict_accepted requires a strict typed verdict bound to a Git commit source.')
  }
  assertNirmanaGitCommitMatchesDeployment(input.source_ref)
  const current = await loadCurrentAssetAnalysisContext(client, input)
  if (payload.data.registry_fingerprint_sha256 !== current.registryFingerprint) {
    throw new NirmanaElevationEvidenceValidationError('optimization_verdict_accepted registry fingerprint does not match the current live contract.')
  }
  if (payload.data.analysis_digest !== current.analysisDigest) {
    throw new NirmanaElevationEvidenceValidationError('optimization_verdict_accepted analysis digest does not match the canonical deployed analysis receipt.')
  }
  const accepted = await client.query<{ accepted_count: number }>(
    `SELECT count(*)::int AS accepted_count
       FROM nirmana_elevation_campaign_events
      WHERE campaign_id = $1
        AND definition_revision = $2
        AND event_type = 'asset_analysis_accepted'
        AND entity_type = 'asset'
        AND entity_id = $3
        AND layer = $4
        AND evidence_payload = jsonb_build_object(
          'registry_fingerprint_sha256', $5::text,
          'analysis_digest', $6::text)
        AND source_kind = 'git_commit'
        AND source_ref = $7`,
    [
      input.campaign_id, input.definition_revision, input.entity_id, input.layer,
      current.registryFingerprint, current.analysisDigest, input.source_ref,
    ],
  )
  if ((accepted.rows[0]?.accepted_count ?? 0) > 1) {
    throw new NirmanaElevationEvidenceValidationError('optimization_verdict_accepted cannot bind ambiguous duplicate current asset analyses.')
  }
  if (accepted.rows[0]?.accepted_count !== 1) {
    throw new NirmanaElevationEvidenceValidationError('optimization_verdict_accepted requires a matching accepted asset analysis for the current live contract.')
  }
}

async function requireAcceptedRebuildProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const sourceMatch = buildRunSourceRef.exec(input.source_ref)
  const payload = OutputDigestEvidenceSchema.safeParse(input.evidence_payload)
  if (!sourceMatch || !payload.success) {
    throw new Error('accepted_rebuild_observed requires an exact build_run UUID and output digest/spec SHA-256 evidence.')
  }
  const verified = await client.query<{ proven: boolean }>(
    `SELECT EXISTS (
       SELECT 1
         FROM build_runs run
         JOIN nirmana_elevation_campaign_definitions definition
           ON definition.campaign_id = $5
          AND definition.definition_revision = $6
          AND definition.definition_status = 'frozen'
          AND definition.superseded_at IS NULL
         JOIN build_run_assets asset ON asset.run_id = run.id
         JOIN asset_registry registry ON registry.asset_id = asset.asset_id
         JOIN asset_provenance_receipts receipt
           ON receipt.build_id = run.id
          AND receipt.asset_id = asset.asset_id
        WHERE run.id = $1::uuid
          AND run.state = 'completed'
          AND run.action = 'rebuild'
          AND run.triggered_by <> 'nirmana-f0-machinery-canary'
          AND run.chart_id = (definition.manifest ->> 'chart_id')::uuid
          AND asset.asset_id = $2
          AND asset.state = 'complete'
          AND receipt.receipt_state = 'proven'
          AND receipt.receipt_version = 'nirmana-provenance-receipt-v2'
          AND receipt.output_digest = $3
          AND receipt.output_digest_spec_sha256 = $4
          AND EXISTS (
            SELECT 1
              FROM jsonb_array_elements(definition.manifest -> 'assets') AS manifest_asset(value)
             WHERE manifest_asset.value ->> 'asset_id' = $2
               AND manifest_asset.value ->> 'execution_obligation' = 'build'
          )
          AND ((registry.scope = 'global' AND receipt.chart_id IS NULL)
            OR (registry.scope = 'per_chart' AND receipt.chart_id = run.chart_id))
     ) AS proven`,
    [sourceMatch[1], input.entity_id, payload.data.output_digest, payload.data.output_digest_spec_sha256, input.campaign_id, input.definition_revision],
  )
  if (verified.rows[0]?.proven !== true) {
    throw new Error('accepted_rebuild_observed requires a completed exact run/asset with a matching proven content receipt.')
  }
}

async function requireBuildRunAuthorizationProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const sourceMatch = buildRunSourceRef.exec(input.source_ref)
  const payload = BuildRunAuthorizationEvidenceSchema.safeParse(input.evidence_payload)
  if (!sourceMatch || sourceMatch[1].toLowerCase() !== input.entity_id.toLowerCase() || !payload.success || input.layer === null) {
    throw new NirmanaElevationEvidenceValidationError('build_run_authorized requires an exact run UUID and a typed layer/wave/asset authorization.')
  }
  if (new Set(payload.data.asset_ids).size !== payload.data.asset_ids.length) {
    throw new NirmanaElevationEvidenceValidationError('build_run_authorized requires unique authorized asset IDs.')
  }
  const verified = await client.query<{ authorized: boolean }>(
    `SELECT EXISTS (
       SELECT 1
         FROM build_runs run
         JOIN nirmana_elevation_campaign_definitions definition
           ON definition.campaign_id = $2
          AND definition.definition_revision = $3
          AND definition.definition_status = 'frozen'
          AND definition.superseded_at IS NULL
        WHERE run.id = $1::uuid
          AND run.action = 'rebuild'
          AND run.triggered_by <> 'nirmana-f0-machinery-canary'
          AND run.chart_id = (definition.manifest ->> 'chart_id')::uuid
          AND EXISTS (SELECT 1 FROM build_run_assets asset WHERE asset.run_id = run.id)
          AND NOT EXISTS (
            SELECT 1
              FROM build_run_assets asset
             WHERE asset.run_id = run.id
               AND NOT EXISTS (
                 SELECT 1
                   FROM jsonb_array_elements(definition.manifest -> 'assets') AS manifest_asset(value)
                  WHERE manifest_asset.value ->> 'asset_id' = asset.asset_id
                    AND manifest_asset.value ->> 'layer' = $4
                    AND (manifest_asset.value ->> 'wave_index')::int = $5
                    AND manifest_asset.value ->> 'execution_obligation' IN ('build', 'probe')
                    AND asset.asset_id = ANY($6::text[])
               )
          )
          AND NOT EXISTS (
            SELECT 1
              FROM unnest($6::text[]) AS authorized_asset(asset_id)
             WHERE NOT EXISTS (
               SELECT 1
                 FROM build_run_assets asset
                WHERE asset.run_id = run.id
                  AND asset.asset_id = authorized_asset.asset_id
             )
          )
     ) AS authorized`,
    [sourceMatch[1], input.campaign_id, input.definition_revision, input.layer, payload.data.wave_index, payload.data.asset_ids],
  )
  if (verified.rows[0]?.authorized !== true) {
    throw new NirmanaElevationEvidenceValidationError('build_run_authorized requires an exact non-canary rebuild scoped to the frozen definition.')
  }
}

async function findExistingEvidenceReceipt(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<RecordNirmanaElevationEvidenceInput | undefined> {
  const existing = await client.query<RecordNirmanaElevationEvidenceInput>(
    `SELECT campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by
       FROM nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2 AND idempotency_key = $3`,
    [input.campaign_id, input.definition_revision, input.idempotency_key],
  )
  return existing.rows[0]
}

function isExactEvidenceReceipt(
  receipt: RecordNirmanaElevationEvidenceInput | undefined,
  input: RecordNirmanaElevationEvidenceInput,
): boolean {
  return Boolean(receipt
    && receipt.event_type === input.event_type
    && receipt.entity_type === input.entity_type
    && receipt.entity_id === input.entity_id
    && receipt.layer === input.layer
    && stableJson(receipt.evidence_payload) === stableJson(input.evidence_payload)
    && receipt.source_kind === input.source_kind
    && receipt.source_ref === input.source_ref
    && new Date(receipt.observed_at).toISOString() === new Date(input.observed_at).toISOString()
    && receipt.recorded_by === input.recorded_by)
}

async function requireCurrentFrozenDefinition(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const definition = await client.query<{ current: boolean }>(
    `SELECT EXISTS (
       SELECT 1
         FROM nirmana_elevation_campaign_definitions
        WHERE campaign_id = $1
          AND definition_revision = $2
          AND definition_status = 'frozen'
          AND superseded_at IS NULL
     ) AS current`,
    [input.campaign_id, input.definition_revision],
  )
  if (definition.rows[0]?.current !== true) {
    throw new NirmanaElevationEvidenceValidationError('Evidence requires the current frozen definition revision.')
  }
}

/** Appends a receipt; an idempotent retry deliberately leaves the first receipt intact. */
export async function recordNirmanaElevationEvidence(input: RecordNirmanaElevationEvidenceInput): Promise<'created' | 'idempotent'> {
  if (Number.isNaN(Date.parse(input.observed_at))) {
    throw new Error('Evidence observed_at must be an ISO-8601 timestamp.')
  }
  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await acquireNirmanaRevisionLock(client, input.campaign_id, input.definition_revision)

    const existing = await findExistingEvidenceReceipt(client, input)
    if (existing) {
      if (!isExactEvidenceReceipt(existing, input)) throw new NirmanaElevationEvidenceConflictError()
      await client.query('COMMIT')
      return 'idempotent'
    }

    await requireCurrentFrozenDefinition(client, input)
    if (input.event_type === 'accepted_rebuild_observed') {
      await requireAcceptedRebuildProvenance(client, input)
    }
    if (input.event_type === 'build_run_authorized') {
      await requireBuildRunAuthorizationProvenance(client, input)
    }
    if (input.event_type === 'asset_analysis_accepted' || input.event_type === 'optimization_verdict_accepted') {
      if (input.source_kind !== 'git_commit') {
        throw new NirmanaElevationEvidenceValidationError(`${input.event_type} requires source_kind=git_commit.`)
      }
      assertNirmanaGitCommitMatchesDeployment(input.source_ref)
    }
    if (input.event_type === 'asset_analysis_accepted') {
      await requireAcceptedAssetAnalysisProvenance(client, input)
    }
    if (input.event_type === 'optimization_verdict_accepted') {
      await requireAcceptedOptimizationVerdictProvenance(client, input)
    }
    const inserted = await client.query(
      `INSERT INTO nirmana_elevation_campaign_events
         (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
          layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12)
       ON CONFLICT (campaign_id, definition_revision, idempotency_key) DO NOTHING
       RETURNING event_id`,
      [
        input.campaign_id, input.definition_revision, input.idempotency_key,
        input.event_type, input.entity_type, input.entity_id, input.layer,
        JSON.stringify(input.evidence_payload), input.source_kind, input.source_ref,
        input.observed_at, input.recorded_by,
      ],
    )
    if (inserted.rowCount === 1) {
      await client.query('COMMIT')
      return 'created'
    }
    const receipt = await findExistingEvidenceReceipt(client, input)
    if (!isExactEvidenceReceipt(receipt, input)) throw new NirmanaElevationEvidenceConflictError()
    await client.query('COMMIT')
    return 'idempotent'
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}
