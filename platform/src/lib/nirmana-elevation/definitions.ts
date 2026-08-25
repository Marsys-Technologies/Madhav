import 'server-only'
import { createHash } from 'node:crypto'
import { z } from 'zod'
import { query } from '@/lib/db/client'

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

export interface CreateNirmanaElevationDefinitionInput {
  campaign_id: string
  definition_revision: string
  definition_status: 'reconciling'
  manifest: unknown
  manifest_sha256: string
  created_by: string
}

export class NirmanaElevationDefinitionConflictError extends Error {
  constructor() {
    super('Campaign definition revision already exists with different immutable contents.')
  }
}

export class NirmanaElevationEvidenceConflictError extends Error {
  constructor() {
    super('Evidence idempotency key already exists with different immutable contents.')
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

/** Appends a receipt; an idempotent retry deliberately leaves the first receipt intact. */
export async function recordNirmanaElevationEvidence(input: RecordNirmanaElevationEvidenceInput): Promise<'created' | 'idempotent'> {
  if (Number.isNaN(Date.parse(input.observed_at))) {
    throw new Error('Evidence observed_at must be an ISO-8601 timestamp.')
  }
  const inserted = await query(
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
  if (inserted.rowCount === 1) return 'created'
  const existing = await query<RecordNirmanaElevationEvidenceInput>(
    `SELECT campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
            layer, evidence_payload, source_kind, source_ref, observed_at, recorded_by
       FROM nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2 AND idempotency_key = $3`,
    [input.campaign_id, input.definition_revision, input.idempotency_key],
  )
  const receipt = existing.rows[0]
  if (receipt
    && receipt.event_type === input.event_type
    && receipt.entity_type === input.entity_type
    && receipt.entity_id === input.entity_id
    && receipt.layer === input.layer
    && stableJson(receipt.evidence_payload) === stableJson(input.evidence_payload)
    && receipt.source_kind === input.source_kind
    && receipt.source_ref === input.source_ref
    && new Date(receipt.observed_at).toISOString() === new Date(input.observed_at).toISOString()
    && receipt.recorded_by === input.recorded_by
  ) return 'idempotent'
  throw new NirmanaElevationEvidenceConflictError()
}
