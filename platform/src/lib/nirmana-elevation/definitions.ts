import 'server-only'
import { createHash } from 'node:crypto'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { getNirmanaCampaignControlWriterPool } from './campaign-control-writer'
import { getNirmanaAnalysisReceiptBase } from '@/generated/nirmana-analysis-receipts'
import { getNirmanaEvidenceIngressPool } from './evidence-ingress'
import { loadNirmanaReleaseStatus, verifyNirmanaCiRun } from './release'
import { NIRMANA_STAGE_IDS } from './vocab'

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
    depends_on: [...(row.depends_on ?? [])].sort(),
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

function canonicalRegistryContractComparisonInput(input: unknown) {
  const parsed = RegistryFingerprintInputSchema.parse(input)
  return {
    ...parsed,
    depends_on: [...parsed.depends_on].sort(),
  }
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
    const frozenContract = canonicalRegistryContractComparisonInput({
      asset_id: asset.asset_id,
      layer: asset.layer,
      depends_on: asset.depends_on ?? [],
      registry_contract: asset.registry_contract,
    })
    const liveContract = canonicalRegistryContractComparisonInput(registryContractFingerprintInput(registryRow))
    if (stableJson(frozenContract) !== stableJson(liveContract)) {
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
  constructor(message = 'Evidence idempotency key already exists with different immutable contents.') {
    super(message)
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
  const client = await (await getNirmanaCampaignControlWriterPool()).connect()
  try {
  const inserted = await client.query(
    `INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions
       (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
     VALUES ($1, $2, $3, $4::jsonb, $5, $6)
     ON CONFLICT (campaign_id, definition_revision) DO NOTHING
     RETURNING definition_revision`,
    [input.campaign_id, input.definition_revision, input.definition_status, JSON.stringify(manifest), canonicalDigest, input.created_by],
  )
  if (inserted.rowCount === 1) return 'created'

  const existing = await client.query<{ definition_status: string; manifest_sha256: string }>(
    `SELECT definition_status, manifest_sha256
       FROM nirmana_evidence.nirmana_elevation_campaign_definitions
      WHERE campaign_id = $1 AND definition_revision = $2`,
    [input.campaign_id, input.definition_revision],
  )
  if (existing.rows[0]?.definition_status === input.definition_status && existing.rows[0]?.manifest_sha256 === canonicalDigest) {
    return 'idempotent'
  }
  throw new NirmanaElevationDefinitionConflictError()
  } finally {
    client.release()
  }
}

export interface FreezeNirmanaElevationDefinitionInput {
  campaign_id: string
  definition_revision: string
  manifest: unknown
  manifest_sha256: string
}

export interface SupersedeNirmanaElevationDefinitionInput {
  campaign_id: 'nirmana-elevation'
  expected_current_revision: string
  expected_current_manifest_sha256: string
  source_observation_id: string
  expected_candidate_sha256: string
  expected_candidate_catalogue_sha256: string
  new_definition_revision: string
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

  const client = await (await getNirmanaCampaignControlWriterPool()).connect()
  try {
    await client.query('BEGIN')
    await client.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [
      `nirmana-elevation:${input.campaign_id}:baseline-acceptance`,
    ])

    const stored = await client.query<StoredNirmanaDefinition>(
      `SELECT definition_revision, definition_status, manifest, manifest_sha256,
              created_by, superseded_at
         FROM nirmana_evidence.nirmana_elevation_campaign_definitions
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
        WHERE id = $1`,
      [input.source_observation_id],
    )
    const sourceObservation = observations.rows[0]
    // Plain SELECT, not FOR SHARE: nirmana_campaign_control_writer is
    // deliberately granted SELECT-only (no UPDATE) on asset_registry, and
    // PostgreSQL's row-locking clauses require UPDATE privilege, not just
    // SELECT -- FOR SHARE would fail closed with "permission denied for
    // table asset_registry" for this role, by the same design that keeps it
    // read-only here. No lock is needed for correctness either way: this
    // transaction already runs at SERIALIZABLE isolation, which detects any
    // conflicting concurrent write to asset_registry via SSI and aborts the
    // transaction -- the same protection FOR SHARE would add under a weaker
    // isolation level, already provided here without it.
    const registry = await client.query<NirmanaRegistryContractRow>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
              sanskrit_name, english_name, english_description,
              sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
              target_table, count_sql, integrity_check_sql, health_probe,
              natural_key_partition, superseded_by, data_disposition, dead_flag
         FROM asset_registry
        ORDER BY asset_id`,
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
      `INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
       VALUES ($1, $2, 'reconciling', $3::jsonb, $4, $5)
       RETURNING definition_revision`,
      [input.campaign_id, input.definition_revision, JSON.stringify(candidate.manifest),
        candidate.manifest_sha256, input.created_by],
    )
    if (inserted.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()

    const frozen = await client.query(
      `UPDATE nirmana_evidence.nirmana_elevation_campaign_definitions
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

  const client = await (await getNirmanaCampaignControlWriterPool()).connect()
  try {
  const registry = await client.query<NirmanaRegistryContractRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
            sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
            target_table, count_sql, integrity_check_sql, health_probe,
            natural_key_partition, superseded_by, data_disposition, dead_flag
       FROM asset_registry
      ORDER BY asset_id`,
  )
  assertManifestMatchesRegistry(manifest, registry.rows)

  const frozen = await client.query(
    `UPDATE nirmana_evidence.nirmana_elevation_campaign_definitions
        SET definition_status = 'frozen'
      WHERE campaign_id = $1
        AND definition_revision = $2
        AND definition_status = 'reconciling'
        AND manifest_sha256 = $3
     RETURNING definition_revision`,
    [input.campaign_id, input.definition_revision, canonicalDigest],
  )
  if (frozen.rowCount === 1) return 'frozen'

  const existing = await client.query<{ definition_status: string; manifest_sha256: string }>(
    `SELECT definition_status, manifest_sha256
       FROM nirmana_evidence.nirmana_elevation_campaign_definitions
      WHERE campaign_id = $1 AND definition_revision = $2`,
    [input.campaign_id, input.definition_revision],
  )
  if (existing.rows[0]?.definition_status === 'frozen' && existing.rows[0]?.manifest_sha256 === canonicalDigest) return 'idempotent'
  throw new NirmanaElevationDefinitionConflictError()
  } finally {
    client.release()
  }
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
  if (input.expected_current_revision === input.new_definition_revision
    || !/^[a-f0-9]{64}$/.test(input.expected_current_manifest_sha256)
    || !z.string().uuid().safeParse(input.source_observation_id).success
    || !/^[a-f0-9]{64}$/.test(input.expected_candidate_sha256)
    || !/^[a-f0-9]{64}$/.test(input.expected_candidate_catalogue_sha256)) {
    throw new NirmanaElevationDefinitionConflictError()
  }
  const client = await (await getNirmanaCampaignControlWriterPool()).connect()
  try {
    await client.query('BEGIN')
    await client.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    await acquireNirmanaRevisionLock(client, input.campaign_id, input.expected_current_revision)
    const stored = await client.query<StoredNirmanaDefinition>(
      `SELECT definition_revision, definition_status, manifest, manifest_sha256, created_by, superseded_at
         FROM nirmana_evidence.nirmana_elevation_campaign_definitions
        WHERE campaign_id = $1 AND definition_revision = ANY($2::text[])
        ORDER BY definition_revision FOR UPDATE`,
      [input.campaign_id, [input.expected_current_revision, input.new_definition_revision]],
    )
    const current = stored.rows.find((row) => row.definition_revision === input.expected_current_revision)
    const replacement = stored.rows.find((row) => row.definition_revision === input.new_definition_revision)
    const observation = await client.query<StoredNirmanaBaselineObservation & { release_state: string; runtime_liveness: string }>(
      `SELECT id::text, observed_at, status, current_definition_sha256, candidate_definition_sha256,
              registry_identity_sha256, registry_contract_sha256, candidate_catalogue_sha256,
              source_state, source_observed_at, freshness_state, freshness_deadline_at, source_error_code,
              release_state, runtime_liveness,
              (freshness_state = 'fresh' AND freshness_deadline_at >= transaction_timestamp()) AS currently_fresh
         FROM nirmana_elevation_monitor_observations WHERE id = $1`,
      [input.source_observation_id],
    )
    const source = observation.rows[0]
    const observedAt = canonicalObservationInstant(source?.observed_at ?? null)
    const sourceObservedAt = canonicalObservationInstant(source?.source_observed_at ?? null)
    const deadlineAt = canonicalObservationInstant(source?.freshness_deadline_at ?? null)
    const registryIdentitySha256 = source?.registry_identity_sha256 ?? null
    const registryContractSha256 = source?.registry_contract_sha256 ?? null
    const provenance = observedAt && sourceObservedAt && deadlineAt
      && typeof registryIdentitySha256 === 'string' && typeof registryContractSha256 === 'string' ? {
      source_observation_id: input.source_observation_id,
      source_observation_observed_at: observedAt,
      source_snapshot_observed_at: sourceObservedAt,
      source_freshness_deadline_at: deadlineAt,
      candidate_manifest_sha256: input.expected_candidate_sha256,
      registry_identity_sha256: registryIdentitySha256,
      registry_contract_sha256: registryContractSha256,
      candidate_catalogue_sha256: input.expected_candidate_catalogue_sha256,
    } : null
    const observationMatches = source?.id === input.source_observation_id
      && source.status === 'plan_adaptation_required'
      && source.current_definition_sha256 === input.expected_current_manifest_sha256
      && source.candidate_definition_sha256 === input.expected_candidate_sha256
      && source.candidate_catalogue_sha256 === input.expected_candidate_catalogue_sha256
      && source.source_state === 'available' && source.source_error_code === null
      && source.freshness_state === 'fresh'
      && source.release_state === 'in_sync'
      && source.runtime_liveness === 'quiet'
      && provenance !== null
      && typeof source.registry_identity_sha256 === 'string'
      && typeof source.registry_contract_sha256 === 'string'
    if (!observationMatches) {
      throw new NirmanaElevationDefinitionConflictError('Supersession requires the exact plan-adaptation monitor observation and candidate digests.')
    }
    const exactRetry = current?.definition_status === 'superseded' && current.superseded_at !== null
      && current.manifest_sha256 === input.expected_current_manifest_sha256
      && replacement?.definition_status === 'frozen' && replacement.superseded_at === null
      && replacement.manifest_sha256 === input.expected_candidate_sha256
    if (exactRetry) {
      const replacementManifest = NirmanaElevationManifestSchema.parse(replacement.manifest)
      if (canonicalManifestDigest(replacementManifest) !== replacement.manifest_sha256) throw new NirmanaElevationDefinitionConflictError()
      const { verifyNirmanaElevationLabelCatalogueInTransaction } = await import('./labels')
      if (!await verifyNirmanaElevationLabelCatalogueInTransaction(client, {
        campaign_id: input.campaign_id, definition_revision: input.new_definition_revision,
        catalogue_revision: input.new_definition_revision, catalogue_sha256: input.expected_candidate_catalogue_sha256,
      }, provenance)) throw new NirmanaElevationDefinitionConflictError('Supersession retry does not have the exact accepted label catalogue.')
      await client.query('COMMIT')
      return 'idempotent'
    }
    if (replacement || current?.definition_status !== 'frozen' || current.superseded_at !== null
      || current.manifest_sha256 !== input.expected_current_manifest_sha256
      || source.freshness_state !== 'fresh' || source.currently_fresh !== true
      || source.release_state !== 'in_sync' || source.runtime_liveness !== 'quiet') {
      throw new NirmanaElevationDefinitionConflictError('Supersession requires a fresh in-sync quiet plan-adaptation observation.')
    }
    const oldManifest = NirmanaElevationManifestSchema.parse(current.manifest)
    for (const key of [...new Set(oldManifest.assets.filter((asset) => asset.execution_obligation === 'build' && asset.wave_index !== undefined)
      .map((asset) => `${input.campaign_id}:${input.expected_current_revision}:${asset.layer}:wave-${asset.wave_index}`))].sort()) {
      await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [key])
    }
    const usage = await client.query<{ event_count: number; build_run_count: number }>(
      `SELECT (SELECT count(*)::int FROM nirmana_evidence.nirmana_elevation_campaign_events WHERE campaign_id = $1 AND definition_revision = $2) AS event_count,
              (SELECT count(*)::int FROM build_runs WHERE plan_manifest #>> '{campaign_control,campaign_id}' = $1 AND plan_manifest #>> '{campaign_control,definition_revision}' = $2) AS build_run_count`,
      [input.campaign_id, input.expected_current_revision],
    )
    if ((usage.rows[0]?.event_count ?? 0) !== 0 || (usage.rows[0]?.build_run_count ?? 0) !== 0) {
      throw new NirmanaElevationDefinitionConflictError('Expected frozen campaign definition already has campaign events or build runs and cannot be superseded.')
    }
    // Plain SELECT, not FOR SHARE -- see the identical comment in
    // acceptNirmanaBaselineCandidate above: nirmana_campaign_control_writer
    // is deliberately SELECT-only on asset_registry, and the SERIALIZABLE
    // isolation this transaction already runs under provides the same
    // conflict protection FOR SHARE would, without needing UPDATE privilege.
    const registry = await client.query<NirmanaRegistryContractRow>(
      `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on, sanskrit_name, english_name, english_description,
              sort_order, scope, asset_kind, catalog_status, is_active, has_writer, target_table, count_sql,
              integrity_check_sql, health_probe, natural_key_partition, superseded_by, data_disposition, dead_flag
         FROM asset_registry ORDER BY asset_id`,
    )
    const { buildNirmanaBaselineCandidate } = await import('./monitor')
    const candidate = buildNirmanaBaselineCandidate(registry.rows)
    if (candidate.manifest_sha256 !== input.expected_candidate_sha256
      || candidate.catalogue_sha256 !== input.expected_candidate_catalogue_sha256
      || source.registry_identity_sha256 !== candidate.registry_identity_sha256
      || source.registry_contract_sha256 !== candidate.registry_contract_sha256) {
      throw new NirmanaElevationDefinitionConflictError('Supersession candidate changed; refresh the monitor observation before retrying.')
    }
    const superseded = await client.query(
      `UPDATE nirmana_evidence.nirmana_elevation_campaign_definitions SET definition_status = 'superseded', superseded_at = clock_timestamp()
        WHERE campaign_id = $1 AND definition_revision = $2 AND definition_status = 'frozen' AND superseded_at IS NULL AND manifest_sha256 = $3 RETURNING definition_revision`,
      [input.campaign_id, input.expected_current_revision, input.expected_current_manifest_sha256],
    )
    if (superseded.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()
    const inserted = await client.query(
      `INSERT INTO nirmana_evidence.nirmana_elevation_campaign_definitions
         (campaign_id, definition_revision, definition_status, manifest, manifest_sha256, created_by)
       VALUES ($1, $2, 'frozen', $3::jsonb, $4, $5) RETURNING definition_revision`,
      [input.campaign_id, input.new_definition_revision, JSON.stringify(candidate.manifest), candidate.manifest_sha256, input.created_by],
    )
    if (inserted.rowCount !== 1) throw new NirmanaElevationDefinitionConflictError()
    const { recordNirmanaElevationLabelCatalogueInTransaction } = await import('./labels')
    if (await recordNirmanaElevationLabelCatalogueInTransaction(client, {
      campaign_id: input.campaign_id, definition_revision: input.new_definition_revision,
      catalogue_revision: input.new_definition_revision, labels: candidate.labels, catalogue_sha256: candidate.catalogue_sha256,
      recorded_by: input.created_by,
    }, provenance) !== 'created') throw new NirmanaElevationDefinitionConflictError('Supersession candidate label catalogue conflicts with existing evidence.')
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

/**
 * Every post-analysis lifecycle receipt is tied to the same immutable
 * registry/analysis pair that the accepted optimization decision reviewed.
 * This keeps a later implementation, probe, integrity, or freeze receipt
 * from silently promoting a stale asset contract.
 */
export const NirmanaLifecycleBindingSchema = z.object({
  registry_fingerprint_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  analysis_digest: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export const NirmanaImplementationEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  decision_digest: z.string().regex(/^[a-f0-9]{64}$/),
  implementation_digest: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export const NirmanaRebuildEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  build_run_id: z.string().uuid(),
  wave_index: z.number().int().nonnegative(),
  authorization_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  decision_digest: z.string().regex(/^[a-f0-9]{64}$/),
  implementation_digest: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
  output_digest: z.string().regex(/^[a-f0-9]{64}$/),
  output_digest_spec_sha256: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export const NirmanaProducerCoverageEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  producer_asset_id: z.string().min(1).max(256),
  producer_layer: LayerSchema,
  producer_run_id: z.string().uuid(),
  producer_rebuild_digest: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export const NirmanaProbeEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  probe_contract_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  response_digest: z.string().regex(/^[a-f0-9]{64}$/),
  detector_observation: z.unknown().optional(),
}).strict()

export const NirmanaNonBuildDispositionEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  disposition: z.enum(['static_acceptance', 'source_acceptance', 'empty_acceptance', 'retired_with_disposition']),
  disposition_digest: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export const NirmanaIntegrityEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  integrity_contract_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  result_digest: z.string().regex(/^[a-f0-9]{64}$/),
  detector_observation: z.unknown().optional(),
}).strict()

export const NirmanaFreezeEvidenceSchema = NirmanaLifecycleBindingSchema.extend({
  lifecycle_digest: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export function canonicalNirmanaOptimizationVerdictDigest(payload: unknown): string {
  return createHash('sha256').update(stableJson(NirmanaOptimizationVerdictEvidenceSchema.parse(payload))).digest('hex')
}

export function canonicalNirmanaRebuildEvidenceDigest(payload: unknown): string {
  return createHash('sha256').update(stableJson(NirmanaRebuildEvidenceSchema.parse(payload))).digest('hex')
}

/** The runner persists this digest with its immutable, dispatch-time plan. */
export function canonicalNirmanaRunPlanManifestDigest(planManifest: unknown): string {
  if (planManifest === null || typeof planManifest !== 'object' || Array.isArray(planManifest)) {
    throw new NirmanaElevationEvidenceValidationError('Build run plan_manifest must be a JSON object.')
  }
  // The dispatcher writes Python's json.dumps(..., ensure_ascii=True,
  // sort_keys=True, separators=(',', ':')) digest.  Escape non-ASCII here so
  // the verifier checks precisely those immutable bytes, not a JS variant.
  const dispatcherCanonicalJson = stableJson(planManifest).replace(/[\u0080-\uFFFF]/g,
    (character) => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`)
  return createHash('sha256').update(dispatcherCanonicalJson).digest('hex')
}

export function canonicalNirmanaProbeContractDigest(healthProbe: unknown): string {
  return createHash('sha256').update(stableJson({ health_probe: healthProbe })).digest('hex')
}

export function canonicalNirmanaProbeResponseDigest(healthProbe: unknown, observation: unknown): string {
  return createHash('sha256').update(stableJson({ health_probe: healthProbe, observation })).digest('hex')
}

export function canonicalNirmanaIntegrityContractDigest(registryContract: unknown): string {
  return createHash('sha256').update(stableJson(RegistryContractSchema.parse(registryContract))).digest('hex')
}

export function canonicalNirmanaIntegrityResultDigest(registryContract: unknown, observation: unknown): string {
  return createHash('sha256').update(stableJson({ registry_contract: RegistryContractSchema.parse(registryContract), observation })).digest('hex')
}

const NirmanaAssetAnalysisReceiptSchema = z.object({
  schema_version: z.literal('nirmana-asset-analysis-receipt/v1'),
  base: z.object({
    schema_version: z.literal('nirmana-asset-analysis-receipt-base/v1'),
    asset_id: z.string().min(1),
    // Was z.literal('L0'). Generalised per adjudication #1715: the spine is
    // layer-generic, and the LAYER IS STILL BOUND -- it is part of the hashed
    // receipt, so an L1 base can never satisfy an L2 claim.
    layer: LayerSchema,
    writer_digest_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
    grounding: z.object({
      convergence_commit: z.string().regex(/^[a-f0-9]{40}$/),
      // The former unqualified value is a durable accepted-receipt identifier;
      // it is not interpreted as executable SQL.  New code reads the physical
      // relation through the qualified query paths below.
      frozen_manifest_source: z.union([
        z.literal('nirmana_elevation_campaign_definitions.manifest'),
        z.literal('nirmana_evidence.nirmana_elevation_campaign_definitions.manifest'),
      ]),
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
  const manifestAsset = ManifestAssetSchema.parse(frozenManifestAsset)
  // The layer comes from the frozen manifest and is cross-checked against the
  // live registry row. Previously only `=== 'L0'` was asserted, so the two
  // could disagree unnoticed; requiring agreement is a strengthening, and it is
  // what lets the receipt lookup be layer-addressed rather than id-addressed.
  if (manifestAsset.asset_id !== assetId || manifestAsset.layer !== registryLayers[registryRow.layer]) {
    throw new NirmanaElevationEvidenceValidationError(`Frozen manifest asset ${assetId} does not match its deployed analysis receipt base.`)
  }
  const receiptBase = getNirmanaAnalysisReceiptBase(assetId, manifestAsset.layer)
  if (!receiptBase) {
    throw new NirmanaElevationEvidenceValidationError(`No deployed ${manifestAsset.layer} analysis receipt base exists for ${assetId}.`)
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

const NirmanaReceiptSha256 = z.string().regex(/^[a-f0-9]{64}$/)
const NirmanaGitSha = z.string().regex(/^[a-f0-9]{40}$/)
const NirmanaServingRevision = z.string().regex(/^[a-z][a-z0-9-]{2,62}$/)
const NirmanaCiRunId = z.string().regex(/^[1-9][0-9]{0,18}$/)
const NirmanaEvidenceControlMigration = z.literal('592_nirmana_elevation_campaign_evidence.sql')
const NIRMANA_EVIDENCE_CONTROL_MIGRATION_SHA256 = '56a86201d15a0d91cf35455758416391e36960e71043cc84fbdb11ff3b72a53e'

/**
 * F0 receipts deliberately contain only identities that the writer can
 * reconstruct from authoritative sources.  They are not operator-supplied
 * acceptance hashes.
 */
export const NirmanaFoundationLaneEvidenceSchema = z.discriminatedUnion('lane_id', [
  z.object({
    schema_version: z.literal('nirmana-foundation-lane-receipt/v1'), lane_id: z.literal('A'),
    manifest_sha256: NirmanaReceiptSha256, asset_count: z.number().int().positive(),
  }).strict(),
  z.object({
    schema_version: z.literal('nirmana-foundation-lane-receipt/v1'), lane_id: z.literal('B'),
    manifest_sha256: NirmanaReceiptSha256, build_run_count: z.number().int().nonnegative(),
    terminal_build_run_count: z.number().int().nonnegative(),
  }).strict(),
  z.object({
    schema_version: z.literal('nirmana-foundation-lane-receipt/v1'), lane_id: z.literal('C'),
    manifest_sha256: NirmanaReceiptSha256, registry_fingerprint_set_sha256: NirmanaReceiptSha256,
    manifest_asset_count: z.number().int().positive(), live_registry_asset_count: z.number().int().positive(),
    invalidated_analysis_count: z.literal(0),
  }).strict(),
  z.object({
    schema_version: z.literal('nirmana-foundation-lane-receipt/v1'), lane_id: z.literal('D'),
    manifest_sha256: NirmanaReceiptSha256,
    main_sha: NirmanaGitSha, serving_sha: NirmanaGitSha,
    serving_revision: NirmanaServingRevision, ci_run_id: NirmanaCiRunId,
  }).strict(),
  z.object({
    schema_version: z.literal('nirmana-foundation-lane-receipt/v1'), lane_id: z.literal('E'),
    manifest_sha256: NirmanaReceiptSha256,
    migration_filename: NirmanaEvidenceControlMigration, migration_sha256: NirmanaReceiptSha256,
  }).strict(),
])

export const NirmanaStageTransitionEvidenceSchema = z.object({
  schema_version: z.literal('nirmana-stage-transition-receipt/v1'),
  from_stage: z.enum(NIRMANA_STAGE_IDS).nullable(),
  to_stage: z.enum(NIRMANA_STAGE_IDS),
  manifest_sha256: NirmanaReceiptSha256,
}).strict()

interface CurrentAssetAnalysisContext {
  registryFingerprint: string
  analysisDigest: string
  registryContract: z.infer<typeof RegistryContractSchema>
}

async function loadCurrentAssetAnalysisContext(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<CurrentAssetAnalysisContext> {
  // Was gated on `input.layer !== 'L0'`, which made every non-L0 terminal event
  // structurally unreachable (adjudication #1715). The gate that MATTERS is
  // kept and is now the only one: a receipt base must exist for this asset IN
  // THIS LAYER, so a layer whose writer inventory has drifted off its pin still
  // fails closed -- per layer, not globally.
  const parsedLayer = LayerSchema.safeParse(input.layer)
  const receiptBase = parsedLayer.success
    ? getNirmanaAnalysisReceiptBase(input.entity_id, parsedLayer.data)
    : undefined
  if (!receiptBase) {
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
       JOIN nirmana_evidence.nirmana_elevation_campaign_definitions definition
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
    registryContract: registryContractFingerprintInput(registryRow).registry_contract,
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
       FROM nirmana_evidence.nirmana_elevation_campaign_events
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

type CurrentLifecycleContext = CurrentAssetAnalysisContext & { manifestAsset: NirmanaElevationManifest['assets'][number] }

async function loadCurrentLifecycleContext(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<CurrentLifecycleContext> {
  const current = await loadCurrentAssetAnalysisContext(client, input)
  const definition = await loadFrozenReceiptDefinition(client, input)
  const manifest = NirmanaElevationManifestSchema.parse(definition.manifest)
  const manifestAsset = manifest.assets.find((asset) => asset.asset_id === input.entity_id && asset.layer === input.layer)
  if (!manifestAsset?.registry_fingerprint_sha256) {
    throw new NirmanaElevationEvidenceValidationError('Lifecycle evidence requires the exact asset in the frozen registry-bound manifest.')
  }
  return { ...current, manifestAsset }
}

function assertLifecycleBinding(
  payload: z.infer<typeof NirmanaLifecycleBindingSchema>,
  current: CurrentLifecycleContext,
  eventType: string,
): void {
  if (payload.registry_fingerprint_sha256 !== current.registryFingerprint
    || payload.analysis_digest !== current.analysisDigest) {
    throw new NirmanaElevationEvidenceValidationError(`${eventType} does not bind the current frozen registry and canonical analysis receipt.`)
  }
}

interface AcceptedDecisionReceipt {
  payload: NirmanaOptimizationVerdictEvidence
  observed_at: string
  recorded_at: string
}

function occursAfter(input: { observed_at: string; recorded_at?: string }, predecessor: { observed_at: string; recorded_at: string }): boolean {
  return Date.parse(input.observed_at) > Date.parse(predecessor.observed_at)
    && Date.parse(input.observed_at) > Date.parse(predecessor.recorded_at)
}

async function loadCurrentAcceptedDecision(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
  current: CurrentLifecycleContext,
): Promise<AcceptedDecisionReceipt> {
  const decisions = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'optimization_verdict_accepted'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
  )
  const exact = decisions.rows.flatMap((decision) => {
    const parsed = NirmanaOptimizationVerdictEvidenceSchema.safeParse(decision.evidence_payload)
    return parsed.success
      && decision.source_kind === 'git_commit'
      && gitCommitSourceRef.test(decision.source_ref)
      && parsed.data.registry_fingerprint_sha256 === current.registryFingerprint
      && parsed.data.analysis_digest === current.analysisDigest
      ? [{ payload: parsed.data, observed_at: decision.observed_at, recorded_at: decision.recorded_at }] : []
  })
  if (exact.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('Lifecycle evidence requires exactly one current accepted optimization decision.')
  }
  return exact[0]
}

function changeIsRequired(decision: NirmanaOptimizationVerdictEvidence): boolean {
  return decision.proposal.action === 'optimize'
    || decision.proposal.action === 'correct'
    || decision.proposal.action === 'optimize_and_correct'
}

async function loadCurrentAcceptedAnalysis(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
  current: CurrentLifecycleContext,
): Promise<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }> {
  const analyses = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'asset_analysis_accepted'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
  )
  const exact = analyses.rows.filter((analysis) => {
    const parsed = NirmanaAssetAnalysisEvidenceSchema.safeParse(analysis.evidence_payload)
    return parsed.success && analysis.source_kind === 'git_commit' && gitCommitSourceRef.test(analysis.source_ref)
      && parsed.data.registry_fingerprint_sha256 === current.registryFingerprint
      && parsed.data.analysis_digest === current.analysisDigest
  })
  if (exact.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('Lifecycle evidence requires exactly one current accepted asset analysis.')
  }
  return exact[0]
}

async function requireImplementationProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaImplementationEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'git_commit') {
    throw new NirmanaElevationEvidenceValidationError('implementation_accepted requires a typed deployed Git-commit receipt.')
  }
  assertNirmanaGitCommitMatchesDeployment(input.source_ref)
  const current = await loadCurrentLifecycleContext(client, input)
  if (!['build', 'probe'].includes(current.manifestAsset.execution_obligation ?? '')) {
    throw new NirmanaElevationEvidenceValidationError('implementation_accepted is only valid for build or probe obligations.')
  }
  assertLifecycleBinding(payload.data, current, 'implementation_accepted')
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  if (!occursAfter(input, decision)
    || !changeIsRequired(decision.payload)
    || payload.data.decision_digest !== canonicalNirmanaOptimizationVerdictDigest(decision.payload)) {
    throw new NirmanaElevationEvidenceValidationError('implementation_accepted requires the exact current change-required optimization decision.')
  }
}

function normalizeDetectorValue(value: unknown): unknown {
  if (value === null || typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return value
  if (value instanceof Date) return value.toISOString()
  if (Array.isArray(value)) return value.map(normalizeDetectorValue)
  if (typeof value === 'object') {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, nested]) => [key, normalizeDetectorValue(nested)]))
  }
  return String(value)
}

async function collectProbeObservation(assetId: string, healthProbe: Record<string, unknown> | null): Promise<{ observation: unknown; observed_at: string }> {
  if (healthProbe === null || typeof healthProbe.probe_type !== 'string' || !/^[a-z][a-z0-9_]{1,127}$/.test(healthProbe.probe_type)) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a current typed health_probe probe_type contract.')
  }
  const probeType = healthProbe.probe_type
  const execution = await runAuthoritativeHealthProbe(assetId, healthProbe)
  const normalized = normalizeDetectorValue(execution.payload)
  const parsed = z.object({
    asset_id: z.literal(assetId),
    probe_contract_sha256: z.literal(canonicalNirmanaProbeContractDigest(healthProbe)),
    observed_at: z.string().datetime(),
    runner_revision: z.string().min(1),
    result: z.object({
      status: z.enum(['GREEN', 'degraded', 'down']),
      message: z.string(),
      checks: z.array(z.object({ check: z.string(), passed: z.boolean() }).passthrough()),
    }),
  }).safeParse(normalized)
  if (!parsed.success || parsed.data.result.status !== 'GREEN' || parsed.data.result.checks.length === 0 || parsed.data.result.checks.some((check) => !check.passed)) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a passing authoritative typed health-probe verdict.')
  }
  return {
    observation: {
      runner_revision: parsed.data.runner_revision,
      probe_type: probeType,
      result: parsed.data.result,
      request_started_at: execution.request_started_at,
      request_ended_at: execution.request_ended_at,
    },
    observed_at: parsed.data.observed_at,
  }
}

async function runAuthoritativeHealthProbe(assetId: string, healthProbe: Record<string, unknown>): Promise<{
  payload: unknown
  request_started_at: string
  request_ended_at: string
}> {
  const runnerUrl = process.env.NIRMANA_PROBE_RUNNER_URL
  let parsedRunnerUrl: URL
  try {
    parsedRunnerUrl = new URL(runnerUrl ?? '')
  } catch {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a configured HTTPS deployed typed probe runner.')
  }
  if (parsedRunnerUrl.protocol !== 'https:' || parsedRunnerUrl.pathname !== '/internal/nirmana/probe') {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a configured HTTPS deployed typed probe runner.')
  }
  const apiKey = process.env.NIRMANA_PROBE_RUNNER_API_KEY ?? process.env.PYTHON_SIDECAR_API_KEY
  if (!apiKey) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires an authenticated deployed typed probe runner credential.')
  }
  const probeContractSha256 = canonicalNirmanaProbeContractDigest(healthProbe)
  const request_started_at = new Date().toISOString()
  let response: Response
  try {
    response = await fetch(parsedRunnerUrl.toString(), {
      method: 'POST', cache: 'no-store', signal: AbortSignal.timeout(15_000),
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
      },
      body: JSON.stringify({ asset_id: assetId, probe_contract_sha256: probeContractSha256, health_probe: healthProbe }),
    })
  } catch (error) {
    throw new NirmanaElevationEvidenceValidationError(`authoritative typed health-probe runner was unreachable: ${error instanceof Error ? error.message : String(error)}`)
  }
  if (!response.ok) {
    throw new NirmanaElevationEvidenceValidationError(`authoritative typed health-probe runner rejected the request with HTTP ${response.status}.`)
  }
  const payload = z.object({
    asset_id: z.string().min(1),
    probe_contract_sha256: NirmanaReceiptSha256,
    observed_at: z.string().datetime(),
    runner_revision: z.string().min(1).max(256),
    result: z.unknown(),
  }).strict().safeParse(await response.json().catch(() => null))
  if (!payload.success || payload.data.asset_id !== assetId || payload.data.probe_contract_sha256 !== probeContractSha256) {
    throw new NirmanaElevationEvidenceValidationError('authoritative typed health-probe runner response does not bind the requested asset and current contract.')
  }
  const request_ended_at = new Date().toISOString()
  return { payload: payload.data, request_started_at, request_ended_at }
}

/**
 * Structural read-only guard for a registry integrity/count detector query.
 *
 * The naive `!/^\s*select\b/ || includes(';')` check false-rejects legitimate
 * single read-only queries in the real registry corpus: a `source_citation`
 * string literal may contain a `;`, an integrity_check_sql may be a read-only
 * `WITH ... SELECT` CTE, and a `--` comment may contain both `''` and `;`.
 *
 * This walks the SQL once, correctly resolving the `''` empty-string vs
 * escaped-quote ambiguity and skipping `--` line and block comments, to build
 * a "code-only" view with string-literal contents removed. It then requires:
 *  - the statement to start with SELECT or WITH (read-only shapes),
 *  - no statement-separator `;` outside literals/comments (single statement;
 *    one trailing `;` is tolerated), and
 *  - no DML/DDL keyword outside literals/comments -- an explicit read-only
 *    guarantee the original guard LACKED, so this is a hardening, not a
 *    relaxation: it accepts richer real queries while rejecting anything that
 *    could modify data.
 *
 * Known limitation: E-string backslash-escaped quotes (`E'...\''...'`) are not
 * modeled (the corpus uses only `E'\n'`-style escapes); a mis-pairing there
 * tends toward rejection, never a false accept of a modifying statement.
 */
function nirmanaDetectorSqlCodeOnly(sql: string): string {
  let out = ''
  let inStr = false
  for (let i = 0; i < sql.length; i++) {
    const c = sql[i]
    if (!inStr && c === '-' && sql[i + 1] === '-') {
      while (i < sql.length && sql[i] !== '\n') i++
      continue
    }
    if (!inStr && c === '/' && sql[i + 1] === '*') {
      i += 2
      while (i < sql.length && !(sql[i] === '*' && sql[i + 1] === '/')) i++
      i++
      continue
    }
    if (c === "'") {
      if (inStr && sql[i + 1] === "'") { i++; continue }
      inStr = !inStr
      if (!inStr) out += "''"
      continue
    }
    if (!inStr) out += c
  }
  return out
}

/**
 * True when a detector query carries a bind placeholder (`$1`, `$2`, ...) outside string
 * literals and comments.
 *
 * The freeze-time detector is executed with **no parameter array** (see
 * `collectIntegrityObservation`), so a parameterised query cannot be evaluated at all. Every
 * `per_chart` asset's `count_sql` is of the form `... WHERE chart_id = $1`, and when
 * `integrity_check_sql` is NULL the detector falls back to exactly that — which meant, for 81
 * of 128 assets, that `integrity_verified` failed with an opaque `there is no parameter $1`
 * raised from deep inside a query call, naming nothing a caller could act on.
 *
 * This is a hardening, not a relaxation: it accepts nothing new. It converts a Postgres
 * mystery into an error that names the artifact that is actually missing.
 *
 * Dollar-quoted bodies are not unwrapped, so a `$1` inside one is reported. That errs toward
 * rejection, which is the same direction `nirmanaDetectorSqlCodeOnly` already documents for
 * its own known limitation.
 */
export function nirmanaDetectorSqlHasBindPlaceholder(detectorSql: string): boolean {
  return /\$\d+/.test(nirmanaDetectorSqlCodeOnly(detectorSql))
}

export function nirmanaReadOnlyDetectorSqlAcceptable(detectorSql: string): boolean {
  const code = nirmanaDetectorSqlCodeOnly(detectorSql).trim().replace(/;\s*$/, '')
  return /^\s*(select|with)\b/i.test(code)
    && !code.includes(';')
    && !/\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|merge|call|do)\b/i.test(code)
}

async function collectIntegrityObservation(
  client: PoolClient,
  assetId: string,
  registryContract: z.infer<typeof RegistryContractSchema>,
  obligation: z.infer<typeof ManifestAssetSchema>['execution_obligation'],
): Promise<{ observation: unknown; observed_at: string }> {
  // Probe-obligation assets are services with no table and therefore no SQL
  // detector by contract (integrity_check_sql and count_sql are both null).
  // Their integrity detector is the same authenticated deployed typed
  // health-probe runner that probe_accepted uses, re-run here at freeze time.
  // This is an independent re-verification, not a relaxation: the runner
  // executes real server-side, collectProbeObservation requires a GREEN
  // verdict with every check passing, and this path throws otherwise -- an
  // asset whose live service is degraded or down cannot pass its freeze-time
  // integrity check. It never invents a detector for an asset that should
  // have had a SQL one: it fires only for the frozen `probe` obligation and
  // only when both SQL detectors are genuinely null.
  if (obligation === 'probe' && registryContract.integrity_check_sql === null
    && registryContract.count_sql === null) {
    if (registryContract.health_probe === null) {
      throw new NirmanaElevationEvidenceValidationError('integrity_verified requires a current registry health probe for a probe-obligation service asset.')
    }
    const probe = await collectProbeObservation(assetId, registryContract.health_probe)
    return { observation: probe.observation, observed_at: probe.observed_at }
  }
  const detectorSql = registryContract.integrity_check_sql ?? registryContract.count_sql
  if (typeof detectorSql !== 'string' || !nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)) {
    throw new NirmanaElevationEvidenceValidationError('integrity_verified requires a read-only current registry integrity detector query.')
  }
  // The detector runs with no parameter array (see the client.query call below), so a query
  // carrying a bind placeholder cannot be evaluated. Say so, naming the missing artifact,
  // instead of letting Postgres raise `there is no parameter $1` from inside the call.
  if (nirmanaDetectorSqlHasBindPlaceholder(detectorSql)) {
    throw new NirmanaElevationEvidenceValidationError(
      registryContract.integrity_check_sql === null
        ? 'integrity_verified requires an explicit chart-agnostic integrity_check_sql; the count_sql fallback is parameterised and cannot be evaluated.'
        : 'integrity_verified requires a chart-agnostic integrity_check_sql; the current one is parameterised and cannot be evaluated.',
    )
  }
  const result = await client.query(detectorSql)
  const verdict = integrityDetectorVerdict(result.rows, registryContract.integrity_check_sql !== null, obligation)
  return {
    observation: { detector_sql_sha256: createHash('sha256').update(detectorSql).digest('hex'), rows: normalizeDetectorValue(result.rows), verdict },
    observed_at: new Date().toISOString(),
  }
}

function integrityDetectorVerdict(
  rows: unknown[],
  explicitIntegrityCheck: boolean,
  obligation: z.infer<typeof ManifestAssetSchema>['execution_obligation'],
): { kind: 'boolean' | 'positive_count' | 'empty_count'; value: true | number } {
  if (rows.length !== 1 || rows[0] === null || typeof rows[0] !== 'object' || Array.isArray(rows[0])) {
    throw new NirmanaElevationEvidenceValidationError('integrity_verified requires exactly one typed detector result row.')
  }
  const row = rows[0] as Record<string, unknown>
  for (const key of ['integrity_passed', 'passed', 'ok', 'success']) {
    if (key in row) {
      if (row[key] !== true) throw new NirmanaElevationEvidenceValidationError('integrity_verified authoritative detector returned a failing boolean verdict.')
      return { kind: 'boolean', value: true }
    }
  }
  if (explicitIntegrityCheck) {
    // No named column matched. Fall back to the orchestrator's own frozen
    // convention (asset_runner.py's integrity/health check: "a single row
    // whose first column is truthy") rather than requiring a rename --
    // most integrity_check_sql values predate this evidence-chain validator
    // and were authored against that convention (e.g. migration 611's
    // unaliased row-count + content-digest boolean expression).
    const [firstValue] = Object.values(row)
    if (firstValue === true) {
      return { kind: 'boolean', value: true }
    }
    if (typeof firstValue === 'boolean') {
      throw new NirmanaElevationEvidenceValidationError('integrity_verified authoritative detector returned a failing boolean verdict.')
    }
  }
  if (!explicitIntegrityCheck && 'count' in row) {
    const raw = row.count
    const count = typeof raw === 'number' ? raw : typeof raw === 'string' ? Number(raw) : NaN
    if (!Number.isSafeInteger(count) || (obligation === 'empty_acceptance' ? count !== 0 : count <= 0)) {
      throw new NirmanaElevationEvidenceValidationError(obligation === 'empty_acceptance'
        ? 'integrity_verified empty-acceptance count detector must return exactly zero.'
        : 'integrity_verified count detector must return a positive integer result.')
    }
    return { kind: obligation === 'empty_acceptance' ? 'empty_count' : 'positive_count', value: count }
  }
  throw new NirmanaElevationEvidenceValidationError('integrity_verified requires an explicit true integrity verdict or a positive count result.')
}

async function normalizeDetectorEvidence(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<RecordNirmanaElevationEvidenceInput> {
  if (input.event_type !== 'probe_accepted' && input.event_type !== 'integrity_verified') return input
  const current = await loadCurrentLifecycleContext(client, input)
  if (input.event_type === 'probe_accepted') {
    const payload = NirmanaProbeEvidenceSchema.parse(input.evidence_payload)
    if (input.source_kind !== 'server_reconstructed' || input.source_ref !== `nirmana-elevation:health-probe:${input.entity_id}`
      || current.manifestAsset.execution_obligation !== 'probe' || current.registryContract.health_probe === null) {
      throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a frozen typed probe obligation and server-reconstructed source.')
    }
    assertLifecycleBinding(payload, current, 'probe_accepted')
    // Validate the entire current generation before dispatch. The provenance
    // check below additionally proves that its server observation is inside a
    // request window which began after these receipts, so a mid-flight decision
    // cannot be retroactively credited.
    await loadCurrentProbePrerequisites(client, input, current)
    const observation = await collectProbeObservation(input.entity_id, current.registryContract.health_probe)
    return {
      ...input,
      observed_at: observation.observed_at,
      evidence_payload: {
        ...payload,
        detector_observation: observation.observation,
        response_digest: canonicalNirmanaProbeResponseDigest(current.registryContract.health_probe, observation.observation),
      },
    }
  }
  const payload = NirmanaIntegrityEvidenceSchema.parse(input.evidence_payload)
  const observation = await collectIntegrityObservation(client, input.entity_id, current.registryContract, current.manifestAsset.execution_obligation)
  return {
    ...input,
    observed_at: observation.observed_at,
    evidence_payload: {
      ...payload,
      detector_observation: observation.observation,
      result_digest: canonicalNirmanaIntegrityResultDigest(current.registryContract, observation.observation),
    },
  }
}

type CurrentProbePrerequisites = {
  analysis: { observed_at: string; recorded_at: string }
  decision: AcceptedDecisionReceipt
  implementation: { observed_at: string; recorded_at: string } | null
}

async function loadCurrentProbePrerequisites(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
  current: CurrentLifecycleContext,
): Promise<CurrentProbePrerequisites> {
  const analysis = await loadCurrentAcceptedAnalysis(client, input, current)
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  if (!changeIsRequired(decision.payload)) return { analysis, decision, implementation: null }
  const implementations = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'implementation_accepted'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
  )
  const matching = implementations.rows.filter((implementation) => {
    const parsed = NirmanaImplementationEvidenceSchema.safeParse(implementation.evidence_payload)
    return parsed.success && implementation.source_kind === 'git_commit' && gitCommitSourceRef.test(implementation.source_ref)
      && parsed.data.registry_fingerprint_sha256 === current.registryFingerprint
      && parsed.data.analysis_digest === current.analysisDigest
      && parsed.data.decision_digest === canonicalNirmanaOptimizationVerdictDigest(decision.payload)
      && occursAfter(implementation, decision)
  })
  if (matching.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires exactly one current implementation after its change-required decision.')
  }
  return { analysis, decision, implementation: matching[0] }
}

function requireProbeObservationTiming(
  input: RecordNirmanaElevationEvidenceInput,
  prerequisites: CurrentProbePrerequisites,
): void {
  const observation = z.object({
    request_started_at: z.string().datetime(),
    request_ended_at: z.string().datetime(),
  }).passthrough().safeParse((input.evidence_payload as { detector_observation?: unknown }).detector_observation)
  if (!observation.success) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires persisted server request start and end timestamps.')
  }
  const requestStarted = Date.parse(observation.data.request_started_at)
  const requestEnded = Date.parse(observation.data.request_ended_at)
  const observed = Date.parse(input.observed_at)
  if (!Number.isFinite(requestStarted) || !Number.isFinite(requestEnded)
    || requestEnded < requestStarted || observed < requestStarted || observed > requestEnded) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted server observation must be inside its authoritative request window.')
  }
  for (const prerequisite of [prerequisites.analysis, prerequisites.decision, prerequisites.implementation]) {
    if (prerequisite && (requestStarted <= Date.parse(prerequisite.observed_at)
      || requestStarted <= Date.parse(prerequisite.recorded_at)
      || observed <= Date.parse(prerequisite.observed_at)
      || observed <= Date.parse(prerequisite.recorded_at))) {
      throw new NirmanaElevationEvidenceValidationError('probe_accepted server observation must follow the current analysis, decision, and required implementation before dispatch.')
    }
  }
}

async function requireProbeProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaProbeEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'server_reconstructed' || input.source_ref !== `nirmana-elevation:health-probe:${input.entity_id}`) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a typed server-reconstructed health-probe receipt.')
  }
  const current = await loadCurrentLifecycleContext(client, input)
  if (current.manifestAsset.execution_obligation !== 'probe' || current.registryContract.health_probe === null) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires a frozen probe obligation with a registry health probe.')
  }
  assertLifecycleBinding(payload.data, current, 'probe_accepted')
  const prerequisites = await loadCurrentProbePrerequisites(client, input, current)
  requireProbeObservationTiming(input, prerequisites)
  if (payload.data.probe_contract_sha256 !== canonicalNirmanaProbeContractDigest(current.registryContract.health_probe)) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted does not bind the frozen registry health-probe contract.')
  }
  if (payload.data.detector_observation === undefined
    || payload.data.response_digest !== canonicalNirmanaProbeResponseDigest(current.registryContract.health_probe, payload.data.detector_observation)) {
    throw new NirmanaElevationEvidenceValidationError('probe_accepted requires the persisted server detector observation and its recomputed digest.')
  }
}

const dispositionEventByObligation = {
  static_acceptance: 'static_accepted',
  source_acceptance: 'source_accepted',
  empty_acceptance: 'empty_accepted',
  retired_with_disposition: 'retired_with_disposition',
} as const

function isCurrentOperationalPrerequisite(
  event: { evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string },
  eventType: string,
  current: CurrentLifecycleContext,
  entityId: string,
  decision: { payload: NirmanaOptimizationVerdictEvidence; observed_at: string; recorded_at: string },
  implementations: { evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }[],
): boolean {
  const bindingMatches = (payload: { registry_fingerprint_sha256: string; analysis_digest: string }) =>
    payload.registry_fingerprint_sha256 === current.registryFingerprint
      && payload.analysis_digest === current.analysisDigest
  if (eventType === 'accepted_rebuild_observed') {
    const payload = NirmanaRebuildEvidenceSchema.safeParse(event.evidence_payload)
    return payload.success && event.source_kind === 'build_run'
      && event.source_ref.toLowerCase() === `build_run:${payload.data.build_run_id.toLowerCase()}`
      && bindingMatches(payload.data)
      && payload.data.decision_digest === canonicalNirmanaOptimizationVerdictDigest(decision.payload)
      && occursAfter(event, decision)
      && (changeIsRequired(decision.payload)
        ? payload.data.implementation_digest !== null && implementations.some((implementation) => {
          const parsedImplementation = NirmanaImplementationEvidenceSchema.safeParse(implementation.evidence_payload)
          return parsedImplementation.success && implementation.source_kind === 'git_commit' && gitCommitSourceRef.test(implementation.source_ref)
            && parsedImplementation.data.registry_fingerprint_sha256 === current.registryFingerprint
            && parsedImplementation.data.analysis_digest === current.analysisDigest
            && parsedImplementation.data.decision_digest === payload.data.decision_digest
            && parsedImplementation.data.implementation_digest === payload.data.implementation_digest
            && occursAfter(event, implementation)
        })
        : payload.data.implementation_digest === null)
  }
  if (eventType === 'probe_accepted') {
    const payload = NirmanaProbeEvidenceSchema.safeParse(event.evidence_payload)
    return payload.success && event.source_kind === 'server_reconstructed'
      && event.source_ref === `nirmana-elevation:health-probe:${entityId}`
      && bindingMatches(payload.data)
      && payload.data.probe_contract_sha256 === canonicalNirmanaProbeContractDigest(current.registryContract.health_probe)
  }
  const payload = NirmanaNonBuildDispositionEvidenceSchema.safeParse(event.evidence_payload)
  return payload.success && event.source_kind === 'git_commit' && gitCommitSourceRef.test(event.source_ref)
    && bindingMatches(payload.data)
    && payload.data.disposition === current.manifestAsset.execution_obligation
    && decision.payload.verdict === 'non_build_disposition'
    && decision.payload.proposal.action === 'formal_disposition'
    && occursAfter(event, decision)
}

async function requireNonBuildDispositionProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaNonBuildDispositionEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'git_commit') {
    throw new NirmanaElevationEvidenceValidationError('Non-build disposition evidence requires a typed deployed Git-commit receipt.')
  }
  assertNirmanaGitCommitMatchesDeployment(input.source_ref)
  const current = await loadCurrentLifecycleContext(client, input)
  const obligation = current.manifestAsset.execution_obligation
  if (!obligation || !(obligation in dispositionEventByObligation)
    || dispositionEventByObligation[obligation as keyof typeof dispositionEventByObligation] !== input.event_type
    || payload.data.disposition !== obligation) {
    throw new NirmanaElevationEvidenceValidationError('Non-build evidence must match the exact frozen asset disposition and event type.')
  }
  assertLifecycleBinding(payload.data, current, input.event_type)
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  if (!occursAfter(input, decision)
    || decision.payload.verdict !== 'non_build_disposition' || decision.payload.proposal.action !== 'formal_disposition') {
    throw new NirmanaElevationEvidenceValidationError('Non-build disposition evidence requires the current formal-disposition optimization decision.')
  }
}

async function requireProducerCoverageProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaProducerCoverageEvidenceSchema.safeParse(input.evidence_payload)
  const sourceMatch = buildRunSourceRef.exec(input.source_ref)
  if (!payload.success || input.source_kind !== 'build_run' || !sourceMatch
    || sourceMatch[1].toLowerCase() !== payload.data.producer_run_id.toLowerCase()) {
    throw new NirmanaElevationEvidenceValidationError('producer_covered requires a typed exact producer build-run receipt.')
  }
  const current = await loadCurrentLifecycleContext(client, input)
  if (current.manifestAsset.execution_obligation !== 'producer_covered'
    || current.manifestAsset.producer_id !== payload.data.producer_asset_id) {
    throw new NirmanaElevationEvidenceValidationError('producer_covered must name the frozen asset producer relation.')
  }
  assertLifecycleBinding(payload.data, current, 'producer_covered')
  const analysis = await loadCurrentAcceptedAnalysis(client, input, current)
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  const definition = await loadFrozenReceiptDefinition(client, input)
  const manifest = NirmanaElevationManifestSchema.parse(definition.manifest)
  const producer = manifest.assets.find((asset) => asset.asset_id === payload.data.producer_asset_id && asset.layer === payload.data.producer_layer)
  if (!producer || producer.execution_obligation !== 'build' || !producer.covered_asset_ids?.includes(input.entity_id)) {
    throw new NirmanaElevationEvidenceValidationError('producer_covered requires the reciprocal frozen producer-to-covered-asset relation.')
  }
  const producerInput = { ...input, entity_id: producer.asset_id, layer: producer.layer }
  const producerCurrent = await loadCurrentLifecycleContext(client, producerInput)
  const producerAnalysis = await loadCurrentAcceptedAnalysis(client, producerInput, producerCurrent)
  const producerDecision = await loadCurrentAcceptedDecision(client, producerInput, producerCurrent)
  const producerImplementations = changeIsRequired(producerDecision.payload)
    ? await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
      `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
         FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'implementation_accepted'
          AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
      [input.campaign_id, input.definition_revision, producer.asset_id, producer.layer],
    )
    : { rows: [] as { evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }[] }
  const rebuilds = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'accepted_rebuild_observed'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, producer.asset_id, producer.layer],
  )
  const producerRebuilds = rebuilds.rows.filter((rebuild) => {
    const parsed = NirmanaRebuildEvidenceSchema.safeParse(rebuild.evidence_payload)
    return parsed.success && rebuild.source_kind === 'build_run'
      && rebuild.source_ref.toLowerCase() === `build_run:${payload.data.producer_run_id.toLowerCase()}`
      && parsed.data.build_run_id.toLowerCase() === payload.data.producer_run_id.toLowerCase()
      && canonicalNirmanaRebuildEvidenceDigest(parsed.data) === payload.data.producer_rebuild_digest
      && parsed.data.registry_fingerprint_sha256 === producerCurrent.registryFingerprint
      && parsed.data.analysis_digest === producerCurrent.analysisDigest
      && parsed.data.decision_digest === canonicalNirmanaOptimizationVerdictDigest(producerDecision.payload)
      && (changeIsRequired(producerDecision.payload)
        ? parsed.data.implementation_digest !== null && producerImplementations.rows.some((implementation) => {
          const implementationPayload = NirmanaImplementationEvidenceSchema.safeParse(implementation.evidence_payload)
          return implementationPayload.success && implementation.source_kind === 'git_commit'
            && implementationPayload.data.registry_fingerprint_sha256 === producerCurrent.registryFingerprint
            && implementationPayload.data.analysis_digest === producerCurrent.analysisDigest
            && implementationPayload.data.decision_digest === parsed.data.decision_digest
            && implementationPayload.data.implementation_digest === parsed.data.implementation_digest
            && occursAfter(rebuild, implementation)
        })
        : parsed.data.implementation_digest === null)
      && occursAfter(rebuild, producerAnalysis)
      && occursAfter(rebuild, producerDecision)
  })
  if (producerRebuilds.length !== 1 || !occursAfter(input, analysis)
    || !occursAfter(input, decision) || !occursAfter(input, producerRebuilds[0])) {
    throw new NirmanaElevationEvidenceValidationError('producer_covered requires one prior accepted producer rebuild after the covered asset analysis.')
  }
}

async function loadCurrentProducerCoverage(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
  current: CurrentLifecycleContext,
): Promise<{
  coverage: { observed_at: string; recorded_at: string }
  execution: { observed_at: string; recorded_at: string }
}> {
  if (current.manifestAsset.execution_obligation !== 'producer_covered' || !current.manifestAsset.producer_id) {
    throw new NirmanaElevationEvidenceValidationError('Producer-covered lifecycle ingress requires a frozen producer relation.')
  }
  const analysis = await loadCurrentAcceptedAnalysis(client, input, current)
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  const definition = await loadFrozenReceiptDefinition(client, input)
  const manifest = NirmanaElevationManifestSchema.parse(definition.manifest)
  const producer = manifest.assets.find((asset) => asset.asset_id === current.manifestAsset.producer_id)
  if (!producer || producer.execution_obligation !== 'build' || !producer.covered_asset_ids?.includes(input.entity_id)) {
    throw new NirmanaElevationEvidenceValidationError('Producer-covered lifecycle ingress requires the reciprocal frozen producer relation.')
  }
  const producerInput = { ...input, entity_id: producer.asset_id, layer: producer.layer }
  const producerCurrent = await loadCurrentLifecycleContext(client, producerInput)
  const producerAnalysis = await loadCurrentAcceptedAnalysis(client, producerInput, producerCurrent)
  const producerDecision = await loadCurrentAcceptedDecision(client, producerInput, producerCurrent)
  const producerImplementations = changeIsRequired(producerDecision.payload)
    ? await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
      `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
         FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'implementation_accepted'
          AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
      [input.campaign_id, input.definition_revision, producer.asset_id, producer.layer],
    )
    : { rows: [] as { evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }[] }
  const coverageRows = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'producer_covered'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
  )
  const rebuildRows = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'accepted_rebuild_observed'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, producer.asset_id, producer.layer],
  )
  const valid = coverageRows.rows.flatMap((coverage) => {
    const payload = NirmanaProducerCoverageEvidenceSchema.safeParse(coverage.evidence_payload)
    if (!payload.success || coverage.source_kind !== 'build_run'
      || coverage.source_ref.toLowerCase() !== `build_run:${payload.data.producer_run_id.toLowerCase()}`
      || payload.data.producer_asset_id !== producer.asset_id || payload.data.producer_layer !== producer.layer
      || payload.data.registry_fingerprint_sha256 !== current.registryFingerprint || payload.data.analysis_digest !== current.analysisDigest) return []
    const rebuild = rebuildRows.rows.filter((candidate) => {
      const parsed = NirmanaRebuildEvidenceSchema.safeParse(candidate.evidence_payload)
      return parsed.success && candidate.source_kind === 'build_run'
        && candidate.source_ref.toLowerCase() === coverage.source_ref.toLowerCase()
        && parsed.data.build_run_id.toLowerCase() === payload.data.producer_run_id.toLowerCase()
        && canonicalNirmanaRebuildEvidenceDigest(parsed.data) === payload.data.producer_rebuild_digest
        && parsed.data.registry_fingerprint_sha256 === producerCurrent.registryFingerprint
        && parsed.data.analysis_digest === producerCurrent.analysisDigest
        && parsed.data.decision_digest === canonicalNirmanaOptimizationVerdictDigest(producerDecision.payload)
        && (changeIsRequired(producerDecision.payload)
          ? parsed.data.implementation_digest !== null && producerImplementations.rows.some((implementation) => {
            const implementationPayload = NirmanaImplementationEvidenceSchema.safeParse(implementation.evidence_payload)
            return implementationPayload.success && implementation.source_kind === 'git_commit'
              && implementationPayload.data.registry_fingerprint_sha256 === producerCurrent.registryFingerprint
              && implementationPayload.data.analysis_digest === producerCurrent.analysisDigest
              && implementationPayload.data.decision_digest === parsed.data.decision_digest
              && implementationPayload.data.implementation_digest === parsed.data.implementation_digest
              && occursAfter(candidate, implementation)
          })
          : parsed.data.implementation_digest === null)
        && occursAfter(candidate, producerAnalysis)
        && occursAfter(candidate, producerDecision)
        && occursAfter(coverage, candidate)
    })
    return rebuild.length === 1 && occursAfter(coverage, analysis) && occursAfter(coverage, decision)
      ? [{ coverage, execution: rebuild[0] }]
      : []
  })
  if (valid.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('Producer-covered integrity/freeze requires exactly one current coverage receipt and producer rebuild.')
  }
  return valid[0]
}

async function requireIntegrityProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaIntegrityEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'server_reconstructed' || input.source_ref !== `nirmana-elevation:integrity:${input.entity_id}`) {
    throw new NirmanaElevationEvidenceValidationError('integrity_verified requires a typed server-reconstructed integrity receipt.')
  }
  const current = await loadCurrentLifecycleContext(client, input)
  assertLifecycleBinding(payload.data, current, 'integrity_verified')
  if (payload.data.integrity_contract_sha256 !== canonicalNirmanaIntegrityContractDigest(current.registryContract)) {
    throw new NirmanaElevationEvidenceValidationError('integrity_verified does not bind the frozen registry integrity contract.')
  }
  if (payload.data.detector_observation === undefined
    || payload.data.result_digest !== canonicalNirmanaIntegrityResultDigest(current.registryContract, payload.data.detector_observation)) {
    throw new NirmanaElevationEvidenceValidationError('integrity_verified requires the persisted server detector observation and its recomputed digest.')
  }
  const obligation = current.manifestAsset.execution_obligation
  const producerCoverage = obligation === 'producer_covered'
    ? await loadCurrentProducerCoverage(client, input, current)
    : null
  if (producerCoverage) {
    if (!occursAfter(input, producerCoverage.execution)) {
      throw new NirmanaElevationEvidenceValidationError('Producer-covered integrity_verified must follow the exact current producer execution receipt.')
    }
    return
  }
  const operationEvent = obligation === 'probe' ? 'probe_accepted'
    : obligation && obligation in dispositionEventByObligation ? dispositionEventByObligation[obligation as keyof typeof dispositionEventByObligation]
      : obligation === 'build' ? 'accepted_rebuild_observed' : null
  if (!operationEvent) throw new NirmanaElevationEvidenceValidationError('integrity_verified requires a supported frozen execution obligation.')
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  const implementations = obligation === 'build' && changeIsRequired(decision.payload)
    ? (await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
      `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
         FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'implementation_accepted'
          AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
      [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
    )).rows
    : []
  const prerequisites = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2 AND event_type = $3
        AND entity_type = 'asset' AND entity_id = $4 AND layer = $5`,
    [input.campaign_id, input.definition_revision, operationEvent, input.entity_id, input.layer],
  )
  const valid = prerequisites.rows.filter((event) =>
    isCurrentOperationalPrerequisite(event, operationEvent, current, input.entity_id, decision, implementations) && occursAfter(input, event))
  if (valid.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('integrity_verified requires exactly one prior current typed execution or disposition receipt.')
  }
}

async function requireFreezeProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const payload = NirmanaFreezeEvidenceSchema.safeParse(input.evidence_payload)
  if (!payload.success || input.source_kind !== 'server_reconstructed' || input.source_ref !== `nirmana-elevation:freeze:${input.entity_id}`) {
    throw new NirmanaElevationEvidenceValidationError('asset_frozen requires a typed server-reconstructed lifecycle receipt.')
  }
  const current = await loadCurrentLifecycleContext(client, input)
  assertLifecycleBinding(payload.data, current, 'asset_frozen')
  const producerCoverage = current.manifestAsset.execution_obligation === 'producer_covered'
    ? await loadCurrentProducerCoverage(client, input, current)
    : null
  const integrity = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2 AND event_type = 'integrity_verified'
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
  )
  const validIntegrity = integrity.rows.filter((event) => {
    const parsed = NirmanaIntegrityEvidenceSchema.safeParse(event.evidence_payload)
    return parsed.success && parsed.data.registry_fingerprint_sha256 === current.registryFingerprint
      && parsed.data.analysis_digest === current.analysisDigest
      && parsed.data.integrity_contract_sha256 === canonicalNirmanaIntegrityContractDigest(current.registryContract)
      && event.source_kind === 'server_reconstructed'
      && event.source_ref === `nirmana-elevation:integrity:${input.entity_id}`
      && occursAfter(input, event)
      && (!producerCoverage || occursAfter(event, producerCoverage.execution))
  })
  if (validIntegrity.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('asset_frozen requires exactly one current validated integrity receipt.')
  }
  if (producerCoverage && !occursAfter(input, producerCoverage.execution)) {
    throw new NirmanaElevationEvidenceValidationError('Producer-covered asset_frozen must follow the exact current producer execution receipt.')
  }
  const lifecycle = await client.query<{ event_type: string; evidence_payload: unknown; source_kind: string; source_ref: string }>(
    `SELECT event_type, evidence_payload, source_kind, source_ref
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND entity_type = 'asset' AND entity_id = $3 AND layer = $4
        AND event_type = ANY($5::text[])`,
    [
      input.campaign_id, input.definition_revision, input.entity_id, input.layer,
      ['asset_analysis_accepted', 'optimization_verdict_accepted', 'implementation_accepted',
        'accepted_rebuild_observed', 'probe_accepted', 'static_accepted', 'source_accepted',
        'empty_accepted', 'retired_with_disposition', 'integrity_verified'],
    ],
  )
  const reconstructedDigest = createHash('sha256').update(stableJson(lifecycle.rows
    .map((event) => ({
      event_type: event.event_type,
      evidence_payload: event.evidence_payload,
      source_kind: event.source_kind,
      source_ref: event.source_ref,
    }))
    .sort((left, right) => `${left.event_type}\0${stableJson(left)}`.localeCompare(`${right.event_type}\0${stableJson(right)}`)))).digest('hex')
  if (payload.data.lifecycle_digest !== reconstructedDigest) {
    throw new NirmanaElevationEvidenceValidationError('asset_frozen lifecycle digest does not match the authoritative accepted receipt set.')
  }
}

async function requireAcceptedRebuildProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const sourceMatch = buildRunSourceRef.exec(input.source_ref)
  const payload = NirmanaRebuildEvidenceSchema.safeParse(input.evidence_payload)
  if (!sourceMatch || !payload.success || input.source_kind !== 'build_run'
    || sourceMatch[1].toLowerCase() !== payload.data.build_run_id.toLowerCase()) {
    throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed requires an exact build_run source, current lifecycle binding, and output digest/spec evidence.')
  }
  const current = await loadCurrentLifecycleContext(client, input)
  assertLifecycleBinding(payload.data, current, 'accepted_rebuild_observed')
  if (current.manifestAsset.execution_obligation !== 'build'
    || current.manifestAsset.wave_index === undefined
    || payload.data.wave_index !== current.manifestAsset.wave_index) {
    throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed must bind the exact current build asset and frozen wave.')
  }
  const decision = await loadCurrentAcceptedDecision(client, input, current)
  if (!occursAfter(input, decision)
    || payload.data.decision_digest !== canonicalNirmanaOptimizationVerdictDigest(decision.payload)) {
    throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed must bind the exact current optimization decision.')
  }
  let implementationRecordedAt: string | null = null
  if (changeIsRequired(decision.payload)) {
    if (payload.data.implementation_digest === null) {
      throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed requires the exact current implementation receipt for a change-required decision.')
    }
    const implementations = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
      `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
         FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'implementation_accepted'
          AND entity_type = 'asset' AND entity_id = $3 AND layer = $4`,
      [input.campaign_id, input.definition_revision, input.entity_id, input.layer],
    )
    const matchingImplementation = implementations.rows.filter((implementation) => {
      const parsed = NirmanaImplementationEvidenceSchema.safeParse(implementation.evidence_payload)
      return parsed.success && implementation.source_kind === 'git_commit' && gitCommitSourceRef.test(implementation.source_ref)
        && parsed.data.registry_fingerprint_sha256 === current.registryFingerprint
        && parsed.data.analysis_digest === current.analysisDigest
        && parsed.data.decision_digest === payload.data.decision_digest
        && parsed.data.implementation_digest === payload.data.implementation_digest
    })
    if (matchingImplementation.length !== 1 || !occursAfter(input, matchingImplementation[0])) {
      throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed requires exactly one current implementation receipt bound to its decision.')
    }
    implementationRecordedAt = matchingImplementation[0].recorded_at
  } else if (payload.data.implementation_digest !== null) {
    throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed must not claim an implementation for a no-change decision.')
  }
  const authorizations = await client.query<{ evidence_payload: unknown; source_kind: string; source_ref: string; observed_at: string; recorded_at: string }>(
    `SELECT evidence_payload, source_kind, source_ref, observed_at, recorded_at
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = 'build_run_authorized'
        AND entity_type = 'build_run' AND entity_id = $3 AND layer = $4`,
    [input.campaign_id, input.definition_revision, sourceMatch[1], input.layer],
  )
  const authorization = authorizations.rows.filter((event) => {
    const parsed = BuildRunAuthorizationEvidenceSchema.safeParse(event.evidence_payload)
    return parsed.success && event.source_kind === 'campaign_authorization'
      && event.source_ref.toLowerCase() === input.source_ref.toLowerCase()
      && parsed.data.wave_index === payload.data.wave_index
      && parsed.data.authorization_sha256 === payload.data.authorization_sha256
      && parsed.data.asset_ids.includes(input.entity_id)
  })
  if (authorization.length !== 1) {
    throw new NirmanaElevationEvidenceValidationError('accepted_rebuild_observed requires one exact deterministic build-run authorization for its asset and wave.')
  }
  const verified = await client.query<{ plan_manifest: unknown; plan_manifest_digest: string | null }>(
    `SELECT run.plan_manifest, run.plan_manifest_digest
         FROM build_runs run
         JOIN nirmana_evidence.nirmana_elevation_campaign_definitions definition
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
          AND run.started_at IS NOT NULL
          AND run.started_at > $7::timestamptz
          AND run.started_at > $8::timestamptz
          AND ($9::timestamptz IS NULL OR run.started_at > $9::timestamptz)
          AND run.plan_manifest #>> '{campaign_control,campaign_id}' = $5
          AND run.plan_manifest #>> '{campaign_control,definition_revision}' = $6
          AND run.plan_manifest #>> '{campaign_control,layer}' = $10
          AND (run.plan_manifest #>> '{campaign_control,wave_index}')::int = $11
          AND run.plan_manifest_digest ~ '^[a-f0-9]{64}$'
          AND EXISTS (
            SELECT 1
              FROM jsonb_array_elements(run.plan_manifest -> 'assets') AS planned_asset(value)
             WHERE planned_asset.value ->> 'asset_id' = $2
          )
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
               AND manifest_asset.value ->> 'layer' = $10
               AND (manifest_asset.value ->> 'wave_index')::int = $11
               AND manifest_asset.value ->> 'execution_obligation' = 'build'
          )
          AND ((registry.scope = 'global' AND receipt.chart_id IS NULL)
            OR (registry.scope = 'per_chart' AND receipt.chart_id = run.chart_id))`,
    [
      sourceMatch[1], input.entity_id, payload.data.output_digest, payload.data.output_digest_spec_sha256,
      input.campaign_id, input.definition_revision, authorization[0].recorded_at, decision.recorded_at,
      implementationRecordedAt, input.layer, payload.data.wave_index,
    ],
  )
  const exactRun = verified.rows.filter((run) => run.plan_manifest_digest !== null
    && canonicalNirmanaRunPlanManifestDigest(run.plan_manifest) === run.plan_manifest_digest)
  if (exactRun.length !== 1) {
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
         JOIN nirmana_evidence.nirmana_elevation_campaign_definitions definition
           ON definition.campaign_id = $2
          AND definition.definition_revision = $3
          AND definition.definition_status = 'frozen'
          AND definition.superseded_at IS NULL
        WHERE run.id = $1::uuid
          AND run.action = 'rebuild'
          AND run.state = 'planned'
          AND run.triggered_by <> 'nirmana-f0-machinery-canary'
          AND run.chart_id = (definition.manifest ->> 'chart_id')::uuid
          AND run.started_at IS NULL
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

interface FrozenReceiptDefinition {
  manifest_sha256: string
  manifest_asset_count: number
  manifest: unknown
}

async function loadFrozenReceiptDefinition(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<FrozenReceiptDefinition> {
  const definition = await client.query<FrozenReceiptDefinition>(
    `SELECT manifest, manifest_sha256, jsonb_array_length(manifest -> 'assets')::int AS manifest_asset_count
       FROM nirmana_evidence.nirmana_elevation_campaign_definitions
      WHERE campaign_id = $1
        AND definition_revision = $2
        AND definition_status = 'frozen'
        AND superseded_at IS NULL`,
    [input.campaign_id, input.definition_revision],
  )
  const row = definition.rows[0]
  if (!row) throw new NirmanaElevationEvidenceValidationError('Evidence requires the current frozen definition revision.')
  return row
}

function canonicalRegistryFingerprintSetDigest(manifest: NirmanaElevationManifest): string {
  return createHash('sha256').update(stableJson(manifest.assets
    .map(({ asset_id, registry_fingerprint_sha256 }) => ({ asset_id, registry_fingerprint_sha256 }))
    .sort((left, right) => left.asset_id.localeCompare(right.asset_id)))).digest('hex')
}

async function loadCurrentRegistryRows(client: PoolClient): Promise<NirmanaRegistryContractRow[]> {
  const registry = await client.query<NirmanaRegistryContractRow>(
    `SELECT asset_id, layer, COALESCE(depends_on, '{}') AS depends_on,
            sort_order, scope, asset_kind, catalog_status, is_active, has_writer,
            target_table, count_sql, integrity_check_sql, health_probe,
            natural_key_partition, superseded_by, data_disposition, dead_flag
       FROM asset_registry
      ORDER BY asset_id`,
  )
  return registry.rows
}

function requireTypedFoundationSource(input: RecordNirmanaElevationEvidenceInput, laneId: string): void {
  if (input.source_kind !== 'server_reconstructed' || input.source_ref !== `nirmana-elevation:foundation-lane:${laneId}`) {
    throw new NirmanaElevationEvidenceValidationError('Foundation evidence must use the server-reconstructed source identity.')
  }
}

async function requireFoundationLaneProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const parsed = NirmanaFoundationLaneEvidenceSchema.safeParse(input.evidence_payload)
  if (!parsed.success || input.entity_type !== 'foundation_lane' || input.entity_id !== parsed.data?.lane_id || input.layer !== null) {
    throw new NirmanaElevationEvidenceValidationError('foundation_lane_accepted requires a strict typed receipt for its exact lane.')
  }
  const receipt = parsed.data
  requireTypedFoundationSource(input, receipt.lane_id)
  const existingLane = await client.query<{ present: boolean }>(
    `SELECT EXISTS (
       SELECT 1 FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'foundation_lane_accepted' AND entity_type = 'foundation_lane'
          AND entity_id = $3 AND layer IS NULL
          AND evidence_payload ->> 'schema_version' = 'nirmana-foundation-lane-receipt/v1'
     ) AS present`,
    [input.campaign_id, input.definition_revision, receipt.lane_id],
  )
  if (existingLane.rows[0]?.present === true) {
    throw new NirmanaElevationEvidenceValidationError('Foundation lane already has an immutable accepted receipt; use its exact idempotency retry.')
  }
  const definition = await loadFrozenReceiptDefinition(client, input)

  if (receipt.manifest_sha256 !== definition.manifest_sha256) {
    throw new NirmanaElevationEvidenceValidationError('Foundation receipt does not bind the current frozen manifest.')
  }

  if (receipt.lane_id === 'A') {
    if (receipt.asset_count !== definition.manifest_asset_count) {
      throw new NirmanaElevationEvidenceValidationError('Foundation census asset count does not match the frozen manifest.')
    }
    return
  }

  if (receipt.lane_id === 'B') {
    const runs = await client.query<{ build_run_count: number; terminal_build_run_count: number }>(
      `SELECT count(*)::int AS build_run_count,
              count(*) FILTER (WHERE state IN ('completed', 'failed', 'cancelled'))::int AS terminal_build_run_count
         FROM build_runs
        WHERE plan_manifest #>> '{campaign_control,campaign_id}' = $1
          AND plan_manifest #>> '{campaign_control,definition_revision}' = $2`,
      [input.campaign_id, input.definition_revision],
    )
    const actual = runs.rows[0]
    if (!actual || receipt.build_run_count !== actual.build_run_count || receipt.terminal_build_run_count !== actual.terminal_build_run_count) {
      throw new NirmanaElevationEvidenceValidationError('Foundation run ledger facts do not match the authoritative build-run ledger.')
    }
    return
  }

  if (receipt.lane_id === 'C') {
    const manifest = NirmanaElevationManifestSchema.parse(definition.manifest)
    const registryRows = await loadCurrentRegistryRows(client)
    try {
      assertManifestMatchesRegistry(manifest, registryRows)
    } catch {
      throw new NirmanaElevationEvidenceValidationError('Foundation hash/invalidation receipt requires the current registry contract to match the frozen manifest.')
    }
    const liveFingerprints = new Map(registryRows.map((row) => [row.asset_id,
      canonicalRegistryContractDigest(registryContractFingerprintInput(row))]))
    const acceptedAnalyses = await client.query<{ entity_id: string; evidence_payload: unknown }>(
      `SELECT entity_id, evidence_payload
         FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'asset_analysis_accepted' AND entity_type = 'asset'`,
      [input.campaign_id, input.definition_revision],
    )
    const invalidatedAnalysisCount = acceptedAnalyses.rows.filter((event) => {
      const payload = NirmanaAssetAnalysisEvidenceSchema.safeParse(event.evidence_payload)
      return payload.success && liveFingerprints.get(event.entity_id) !== payload.data.registry_fingerprint_sha256
    }).length
    const registry = await client.query<{ live_registry_asset_count: number }>(
      `SELECT count(*)::int AS live_registry_asset_count
         FROM asset_registry registry
         JOIN LATERAL jsonb_array_elements((SELECT manifest FROM nirmana_evidence.nirmana_elevation_campaign_definitions
           WHERE campaign_id = $1 AND definition_revision = $2 AND definition_status = 'frozen' AND superseded_at IS NULL) -> 'assets') AS asset(value)
           ON asset.value ->> 'asset_id' = registry.asset_id
          AND asset.value ->> 'layer' = CASE registry.layer
            WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1' WHEN 'bodha' THEN 'L2'
            WHEN 'kala' THEN 'L3' WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END`,
      [input.campaign_id, input.definition_revision],
    )
    const actual = registry.rows[0]
    if (!actual || receipt.registry_fingerprint_set_sha256 !== canonicalRegistryFingerprintSetDigest(manifest)
      || receipt.invalidated_analysis_count !== invalidatedAnalysisCount || invalidatedAnalysisCount !== 0
      || receipt.manifest_asset_count !== definition.manifest_asset_count
      || receipt.live_registry_asset_count !== actual.live_registry_asset_count
      || receipt.manifest_asset_count !== receipt.live_registry_asset_count) {
      throw new NirmanaElevationEvidenceValidationError('Foundation hash/invalidation census does not match the current registry contract or has invalidated analysis evidence.')
    }
    return
  }

  if (receipt.lane_id === 'D') {
    const status = await loadNirmanaReleaseStatus()
    const release = status.release
    if (release.production_in_sync !== true
      || release.main_sha?.toLowerCase() !== receipt.main_sha
      || release.deployed_sha?.toLowerCase() !== receipt.serving_sha
      || release.deployed_revision !== receipt.serving_revision
      || receipt.main_sha !== receipt.serving_sha) {
      throw new NirmanaElevationEvidenceValidationError('Foundation release receipt does not match one current in-sync main and serving revision.')
    }
    try {
      await verifyNirmanaCiRun(receipt.ci_run_id, receipt.main_sha)
    } catch {
      throw new NirmanaElevationEvidenceValidationError('Foundation release receipt lacks a successful CI run for the exact serving commit.')
    }
    return
  }

  const migration = await client.query<{ applied: boolean }>(
    `SELECT EXISTS (
       SELECT 1 FROM public._migrations_applied
        WHERE filename = $1 AND sha256 = $2
     ) AS applied`,
    [receipt.migration_filename, NIRMANA_EVIDENCE_CONTROL_MIGRATION_SHA256],
  )
  if (receipt.migration_sha256 !== NIRMANA_EVIDENCE_CONTROL_MIGRATION_SHA256 || migration.rows[0]?.applied !== true) {
    throw new NirmanaElevationEvidenceValidationError('Foundation evidence-control receipt requires the exact applied migration-ledger entry.')
  }
}

async function requireStageTransitionProvenance(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const parsed = NirmanaStageTransitionEvidenceSchema.safeParse(input.evidence_payload)
  if (!parsed.success || input.entity_type !== 'campaign_stage' || input.entity_id !== parsed.data?.to_stage || input.layer !== null
    || input.source_kind !== 'server_reconstructed' || input.source_ref !== 'nirmana-elevation:stage-spine') {
    throw new NirmanaElevationEvidenceValidationError('stage_transition_accepted requires a strict server-reconstructed stage receipt.')
  }
  const receipt = parsed.data
  const definition = await loadFrozenReceiptDefinition(client, input)
  if (receipt.manifest_sha256 !== definition.manifest_sha256) {
    throw new NirmanaElevationEvidenceValidationError('Stage receipt does not bind the current frozen manifest.')
  }
  const manifest = NirmanaElevationManifestSchema.parse(definition.manifest)
  const toIndex = NIRMANA_STAGE_IDS.indexOf(receipt.to_stage)
  const expectedFrom = toIndex === 0 ? null : NIRMANA_STAGE_IDS[toIndex - 1]
  if (receipt.from_stage !== expectedFrom) {
    throw new NirmanaElevationEvidenceValidationError('Campaign stage receipt does not follow the canonical sequential spine.')
  }
  const targetExists = await client.query<{ present: boolean }>(
    `SELECT EXISTS (
       SELECT 1 FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'stage_transition_accepted' AND entity_type = 'campaign_stage'
          AND entity_id = $3 AND layer IS NULL
          AND evidence_payload ->> 'schema_version' = 'nirmana-stage-transition-receipt/v1'
     ) AS present`,
    [input.campaign_id, input.definition_revision, receipt.to_stage],
  )
  if (targetExists.rows[0]?.present === true) {
    throw new NirmanaElevationEvidenceValidationError('Campaign stage already has an immutable accepted receipt; use its exact idempotency retry.')
  }
  if (expectedFrom !== null) {
    const prior = await client.query<{ present: boolean }>(
      `SELECT EXISTS (
         SELECT 1 FROM nirmana_evidence.nirmana_elevation_campaign_events
          WHERE campaign_id = $1 AND definition_revision = $2
            AND event_type = 'stage_transition_accepted' AND entity_type = 'campaign_stage'
            AND entity_id = $3 AND layer IS NULL
            AND evidence_payload ->> 'schema_version' = 'nirmana-stage-transition-receipt/v1'
            AND evidence_payload ->> 'to_stage' = $3
       ) AS present`,
      [input.campaign_id, input.definition_revision, expectedFrom],
    )
    if (prior.rows[0]?.present !== true) {
      throw new NirmanaElevationEvidenceValidationError('Campaign stage receipt requires the immediately preceding accepted stage receipt.')
    }
  }
  if (receipt.to_stage === 'T0_CENSUS' || receipt.to_stage === 'DENOMINATOR_FROZEN') {
    const registryRows = await loadCurrentRegistryRows(client)
    try {
      if (receipt.to_stage === 'T0_CENSUS') assertManifestMatchesRegistryIdentity(manifest, registryRows)
      else assertManifestMatchesRegistry(manifest, registryRows)
    } catch {
      throw new NirmanaElevationEvidenceValidationError(`${receipt.to_stage} requires the frozen manifest to match the canonical live registry gate.`)
    }
  }
  if (receipt.to_stage === 'PLAN_FROZEN') {
    try {
      assertFreezableManifest(manifest)
    } catch {
      throw new NirmanaElevationEvidenceValidationError('PLAN_FROZEN requires a complete, freezable canonical manifest.')
    }
  }
  if (receipt.to_stage === 'L0') {
    const lanes = await client.query<{ accepted_lane_count: number }>(
      `SELECT count(DISTINCT entity_id)::int AS accepted_lane_count
         FROM nirmana_evidence.nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND event_type = 'foundation_lane_accepted' AND entity_type = 'foundation_lane' AND layer IS NULL
          AND evidence_payload ->> 'schema_version' = 'nirmana-foundation-lane-receipt/v1'`,
      [input.campaign_id, input.definition_revision],
    )
    if (lanes.rows[0]?.accepted_lane_count !== 5) {
      throw new NirmanaElevationEvidenceValidationError('L0 entry requires all five typed F0 foundation-lane receipts.')
    }
  }
  if (expectedFrom !== null && ['L0', 'L1', 'L2', 'L3', 'L4', 'L5'].includes(expectedFrom)) {
    throw new NirmanaElevationEvidenceValidationError(`Campaign stage ${expectedFrom} exit is fail-closed until a server-side freeze-lifecycle verifier reconstructs every asset receipt.`)
  }
  if (receipt.to_stage === 'COMPLETE') {
    const status = await loadNirmanaReleaseStatus()
    if (status.release.production_in_sync !== true) {
      throw new NirmanaElevationEvidenceValidationError('COMPLETE requires a current in-sync canonical release observation.')
    }
    const migration = await client.query<{ applied: boolean }>(
      `SELECT EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename = $1 AND sha256 = $2) AS applied`,
      ['592_nirmana_elevation_campaign_evidence.sql', NIRMANA_EVIDENCE_CONTROL_MIGRATION_SHA256],
    )
    if (migration.rows[0]?.applied !== true) {
      throw new NirmanaElevationEvidenceValidationError('COMPLETE requires the canonical evidence migration ledger gate.')
    }
  }
}

async function findExistingEvidenceReceipt(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<RecordNirmanaElevationEvidenceInput | undefined> {
  const existing = await client.query<RecordNirmanaElevationEvidenceInput>(
    `SELECT campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2 AND idempotency_key = $3`,
    [input.campaign_id, input.definition_revision, input.idempotency_key],
  )
  return existing.rows[0]
}

/**
 * An idempotency key is transport metadata, not a licence to create two
 * incompatible accepted facts for the same lifecycle step.  The revision lock
 * makes this read/check/write sequence serial for one campaign revision.
 */
async function findExistingLifecycleReceipt(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<RecordNirmanaElevationEvidenceInput | undefined> {
  if (input.entity_type !== 'asset') return undefined
  const existing = await client.query<RecordNirmanaElevationEvidenceInput>(
    `SELECT campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by
       FROM nirmana_evidence.nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND event_type = $3 AND entity_type = 'asset' AND entity_id = $4
        AND layer IS NOT DISTINCT FROM $5`,
    [input.campaign_id, input.definition_revision, input.event_type, input.entity_id, input.layer],
  )
  const generation = lifecycleEvidenceGeneration(input.evidence_payload)
  return existing.rows.find((receipt) => lifecycleEvidenceGeneration(receipt.evidence_payload) === generation)
}

/**
 * Lifecycle facts are immutable within the live registry/analysis generation
 * that they attest.  A contract drift legitimately starts a new generation;
 * an unbound legacy fact remains mutually exclusive rather than becoming an
 * escape hatch for duplicating an old lifecycle step.
 */
function lifecycleEvidenceGeneration(payload: unknown): string {
  if (payload !== null && typeof payload === 'object' && !Array.isArray(payload)) {
    const binding = NirmanaLifecycleBindingSchema.safeParse({
      registry_fingerprint_sha256: (payload as Record<string, unknown>).registry_fingerprint_sha256,
      analysis_digest: (payload as Record<string, unknown>).analysis_digest,
    })
    if (binding.success) {
      return `${binding.data.registry_fingerprint_sha256}:${binding.data.analysis_digest}`
    }
  }
  return 'legacy-unbound'
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

function isExactDetectorRetry(
  receipt: RecordNirmanaElevationEvidenceInput | undefined,
  input: RecordNirmanaElevationEvidenceInput,
): boolean {
  if (!receipt || !['probe_accepted', 'integrity_verified'].includes(input.event_type)
    || receipt.event_type !== input.event_type || receipt.entity_type !== input.entity_type
    || receipt.entity_id !== input.entity_id || receipt.layer !== input.layer
    || receipt.source_kind !== input.source_kind || receipt.source_ref !== input.source_ref) return false
  if (input.event_type === 'probe_accepted') {
    const existing = NirmanaProbeEvidenceSchema.safeParse(receipt.evidence_payload)
    const requested = NirmanaProbeEvidenceSchema.safeParse(input.evidence_payload)
    return existing.success && requested.success
      && existing.data.registry_fingerprint_sha256 === requested.data.registry_fingerprint_sha256
      && existing.data.analysis_digest === requested.data.analysis_digest
      && existing.data.probe_contract_sha256 === requested.data.probe_contract_sha256
  }
  const existing = NirmanaIntegrityEvidenceSchema.safeParse(receipt.evidence_payload)
  const requested = NirmanaIntegrityEvidenceSchema.safeParse(input.evidence_payload)
  return existing.success && requested.success
    && existing.data.registry_fingerprint_sha256 === requested.data.registry_fingerprint_sha256
    && existing.data.analysis_digest === requested.data.analysis_digest
    && existing.data.integrity_contract_sha256 === requested.data.integrity_contract_sha256
}

async function requireCurrentFrozenDefinition(
  client: PoolClient,
  input: RecordNirmanaElevationEvidenceInput,
): Promise<void> {
  const definition = await client.query<{ current: boolean }>(
    `SELECT EXISTS (
       SELECT 1
         FROM nirmana_evidence.nirmana_elevation_campaign_definitions
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
  const pool = input.source_kind === 'server_reconstructed'
    ? await getNirmanaEvidenceIngressPool()
    : await getNirmanaCampaignControlWriterPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    await acquireNirmanaRevisionLock(client, input.campaign_id, input.definition_revision)

    const existing = await findExistingEvidenceReceipt(client, input)
    if (existing) {
      if (!isExactEvidenceReceipt(existing, input) && !isExactDetectorRetry(existing, input)) throw new NirmanaElevationEvidenceConflictError()
      await client.query('COMMIT')
      return 'idempotent'
    }

    await requireCurrentFrozenDefinition(client, input)
    const normalizedInput = await normalizeDetectorEvidence(client, input)
    const semanticExisting = await findExistingLifecycleReceipt(client, normalizedInput)
    if (semanticExisting) {
      throw new NirmanaElevationEvidenceConflictError('A conflicting lifecycle receipt already exists for this registry/analysis generation; retry it with its original idempotency key.')
    }
    if (normalizedInput.event_type === 'foundation_lane_accepted') {
      await requireFoundationLaneProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'stage_transition_accepted') {
      await requireStageTransitionProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'accepted_rebuild_observed') {
      await requireAcceptedRebuildProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'build_run_authorized') {
      await requireBuildRunAuthorizationProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'asset_analysis_accepted' || normalizedInput.event_type === 'optimization_verdict_accepted') {
      if (normalizedInput.source_kind !== 'git_commit') {
        throw new NirmanaElevationEvidenceValidationError(`${normalizedInput.event_type} requires source_kind=git_commit.`)
      }
      assertNirmanaGitCommitMatchesDeployment(normalizedInput.source_ref)
    }
    if (normalizedInput.event_type === 'asset_analysis_accepted') {
      await requireAcceptedAssetAnalysisProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'optimization_verdict_accepted') {
      await requireAcceptedOptimizationVerdictProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'implementation_accepted') {
      await requireImplementationProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'probe_accepted') {
      await requireProbeProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'producer_covered') {
      await requireProducerCoverageProvenance(client, normalizedInput)
    }
    if (['static_accepted', 'source_accepted', 'empty_accepted', 'retired_with_disposition'].includes(normalizedInput.event_type)) {
      await requireNonBuildDispositionProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'integrity_verified') {
      await requireIntegrityProvenance(client, normalizedInput)
    }
    if (normalizedInput.event_type === 'asset_frozen') {
      await requireFreezeProvenance(client, normalizedInput)
    }
    const inserted = await client.query(
      `INSERT INTO nirmana_evidence.nirmana_elevation_campaign_events
         (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
          layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12)
       ON CONFLICT (campaign_id, definition_revision, idempotency_key) DO NOTHING
       RETURNING event_id`,
      [
        normalizedInput.campaign_id, normalizedInput.definition_revision, normalizedInput.idempotency_key,
        normalizedInput.event_type, normalizedInput.entity_type, normalizedInput.entity_id, normalizedInput.layer,
        JSON.stringify(normalizedInput.evidence_payload), normalizedInput.source_kind, normalizedInput.source_ref,
        normalizedInput.observed_at, normalizedInput.recorded_by,
      ],
    )
    if (inserted.rowCount === 1) {
      await client.query('COMMIT')
      return 'created'
    }
    const receipt = await findExistingEvidenceReceipt(client, input)
    if (!isExactEvidenceReceipt(receipt, normalizedInput) && !isExactDetectorRetry(receipt, normalizedInput)) throw new NirmanaElevationEvidenceConflictError()
    await client.query('COMMIT')
    return 'idempotent'
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    throw error
  } finally {
    client.release()
  }
}
