import 'server-only'
import { createHash } from 'node:crypto'
import { z } from 'zod'
import { query } from '@/lib/db/client'

const LayerSchema = z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5'])
const layerPrefixes = { L0: 'bg_', L1: 'ga_', L2: 'bo_', L3: 'ka_', L4: 'ph_', L5: 'mi_' } as const
export const CANONICAL_NIRMANA_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const ManifestAssetSchema = z.object({
  asset_id: z.string().min(1),
  layer: LayerSchema,
  wave_index: z.number().int().nonnegative().optional(),
  execution_obligation: z.enum(['build', 'probe', 'producer_covered', 'static_acceptance', 'source_acceptance', 'empty_acceptance', 'retired_with_disposition', 'unresolved']).optional(),
  producer_id: z.string().optional(),
  covered_asset_ids: z.array(z.string()).optional(),
})

export const NirmanaElevationManifestSchema = z.object({
  chart_id: z.literal(CANONICAL_NIRMANA_CHART_ID),
  assets: z.array(ManifestAssetSchema).min(1),
}).strict().superRefine((manifest, context) => {
  const assetIds = new Set<string>()
  for (const [index, asset] of manifest.assets.entries()) {
    if (!asset.asset_id.startsWith(layerPrefixes[asset.layer])) {
      context.addIssue({ code: 'custom', path: ['assets', index, 'asset_id'], message: `${asset.layer} asset IDs must begin with ${layerPrefixes[asset.layer]}.` })
    }
    if (assetIds.has(asset.asset_id)) {
      context.addIssue({ code: 'custom', path: ['assets', index, 'asset_id'], message: 'Manifest asset IDs must be unique.' })
    }
    assetIds.add(asset.asset_id)
  }
})

export type NirmanaElevationManifest = z.infer<typeof NirmanaElevationManifestSchema>

export function parseNirmanaElevationManifest(manifest: unknown): NirmanaElevationManifest | null {
  const parsed = NirmanaElevationManifestSchema.safeParse(manifest)
  return parsed.success ? parsed.data : null
}

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

export function canonicalManifestDigest(manifest: unknown): string {
  const parsed = NirmanaElevationManifestSchema.parse(manifest)
  return createHash('sha256').update(stableJson(parsed)).digest('hex')
}

function assertFreezableManifest(manifest: NirmanaElevationManifest): void {
  const byId = new Map(manifest.assets.map((asset) => [asset.asset_id, asset]))
  for (const asset of manifest.assets) {
    if (!asset.execution_obligation) throw new Error(`Frozen manifest asset ${asset.asset_id} is missing an execution obligation.`)
    if (asset.execution_obligation === 'producer_covered') {
      if (!asset.producer_id || asset.producer_id === asset.asset_id) throw new Error(`Producer-covered asset ${asset.asset_id} must name a distinct producer.`)
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
