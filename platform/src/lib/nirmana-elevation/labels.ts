import 'server-only'
import { createHash } from 'node:crypto'
import type { PoolClient } from 'pg'
import { z } from 'zod'
import { getNirmanaCampaignControlWriterPool } from './campaign-control-writer'
import { NirmanaLegacyAliasSchema } from './label-contract'

export { NirmanaLegacyAliasSchema } from './label-contract'

export const NirmanaAssetLabelSchema = z.object({
  asset_id: z.string().min(1),
  sanskrit_name: z.string().min(1).nullable(),
  english_name: z.string().min(1).nullable(),
  description: z.string().min(1).nullable(),
  legacy_aliases: z.array(NirmanaLegacyAliasSchema),
  source_ref: z.string().min(1).max(512),
}).strict().refine(
  (value) => value.sanskrit_name !== null || value.english_name !== null || value.description !== null,
  'At least one governed human-readable label is required.',
)

export const NirmanaLabelCatalogueInputSchema = z.object({
  campaign_id: z.literal('nirmana-elevation'),
  definition_revision: z.string().regex(/^[A-Za-z0-9._-]{1,128}$/),
  catalogue_revision: z.string().regex(/^[A-Za-z0-9._-]{1,128}$/),
  labels: z.array(NirmanaAssetLabelSchema).min(1),
  catalogue_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  recorded_by: z.string().min(1),
}).strict()

const NirmanaBaselineReceiptProvenanceSchema = z.object({
  source_observation_id: z.string().uuid(),
  source_observation_observed_at: z.string().datetime(),
  source_snapshot_observed_at: z.string().datetime(),
  source_freshness_deadline_at: z.string().datetime(),
  candidate_manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  registry_identity_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  registry_contract_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  candidate_catalogue_sha256: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

export function canonicalLabelCatalogueDigest(labels: z.infer<typeof NirmanaAssetLabelSchema>[]): string {
  const parsed = z.array(NirmanaAssetLabelSchema).min(1).parse(labels)
  const assetIds = new Set(parsed.map((label) => label.asset_id))
  if (assetIds.size !== parsed.length) throw new Error('Label catalogue asset IDs must be unique.')
  return createHash('sha256').update(stableJson([...parsed].sort((a, b) => a.asset_id.localeCompare(b.asset_id)))).digest('hex')
}

/**
 * Records a validated label catalogue on a caller-owned transaction. This is
 * the shared atomic seam used by baseline acceptance; it deliberately issues
 * no BEGIN/COMMIT/ROLLBACK of its own.
 */
export async function recordNirmanaElevationLabelCatalogueInTransaction(
  client: PoolClient,
  raw: z.input<typeof NirmanaLabelCatalogueInputSchema>,
  rawBaselineProvenance?: z.input<typeof NirmanaBaselineReceiptProvenanceSchema>,
): Promise<'created' | 'idempotent'> {
  const input = NirmanaLabelCatalogueInputSchema.parse(raw)
  const baselineProvenance = rawBaselineProvenance === undefined
    ? undefined
    : NirmanaBaselineReceiptProvenanceSchema.parse(rawBaselineProvenance)
  const digest = canonicalLabelCatalogueDigest(input.labels)
  if (digest !== input.catalogue_sha256) throw new Error('Label catalogue digest mismatch.')

  const revisionIdentity = `${input.campaign_id}:${input.definition_revision}:${input.catalogue_revision}`
  const receiptIdempotencyKey = `asset-label-catalogue:${input.catalogue_revision}`
  const receiptSourceRef = `label_catalogue:${input.catalogue_revision}`
  const receiptEvidencePayload = {
    catalogue_sha256: digest,
    asset_count: input.labels.length,
    audit_provenance: 'normative',
    ...baselineProvenance,
  }
  await client.query(
    'SELECT pg_advisory_xact_lock(hashtextextended($1, 0))',
    [revisionIdentity],
  )
  const definition = await client.query(
    `SELECT definition_status, manifest FROM nirmana_elevation_campaign_definitions
     WHERE campaign_id = $1 AND definition_revision = $2 FOR SHARE`,
    [input.campaign_id, input.definition_revision],
  )
  if (definition.rows[0]?.definition_status !== 'frozen') throw new Error('Labels require a frozen campaign definition.')
  const manifestAssetIds = new Set(
    ((definition.rows[0]?.manifest as { assets?: Array<{ asset_id?: string }> } | undefined)?.assets ?? [])
      .map((asset) => asset.asset_id)
      .filter((assetId): assetId is string => typeof assetId === 'string'),
  )
  if (input.labels.some((label) => !manifestAssetIds.has(label.asset_id))) {
    throw new Error('Label catalogue contains an asset absent from the frozen definition.')
  }

  const existingReceipt = await client.query(
    `SELECT event_type, entity_type, entity_id, layer, evidence_payload, source_kind, source_ref
       FROM nirmana_elevation_campaign_events
      WHERE campaign_id = $1 AND definition_revision = $2
        AND idempotency_key = $3
      FOR SHARE`,
    [input.campaign_id, input.definition_revision, receiptIdempotencyKey],
  )
  const existingReceiptRow = existingReceipt.rows[0] as {
    event_type: string
    entity_type: string
    entity_id: string
    layer: string | null
    evidence_payload: Record<string, unknown>
    source_kind: string
    source_ref: string
  } | undefined
  const exactReceiptIdentity = existingReceiptRow?.event_type === 'asset_label_catalogue_accepted'
    && existingReceiptRow.entity_type === 'label_catalogue'
    && existingReceiptRow.entity_id === input.catalogue_revision
    && existingReceiptRow.layer === null
    && existingReceiptRow.source_kind === 'governed_catalogue'
    && existingReceiptRow.source_ref === receiptSourceRef
  const exactReceiptPayload = existingReceiptRow
    && stableJson(existingReceiptRow.evidence_payload) === stableJson(receiptEvidencePayload)
  const exactLegacyReceiptPayload = existingReceiptRow
    && stableJson(existingReceiptRow.evidence_payload) === stableJson({
      catalogue_sha256: digest,
      asset_count: input.labels.length,
    })
  if (existingReceiptRow
    && (!exactReceiptIdentity
      || (!exactReceiptPayload && !exactLegacyReceiptPayload))) {
    throw new Error('Label catalogue revision conflicts with an existing receipt.')
  }
  const existingLabels = await client.query(
    `SELECT count(*)::int AS label_count,
            COALESCE(bool_and(label_digest = $4), false) AS digest_matches
       FROM nirmana_elevation_asset_labels
      WHERE campaign_id = $1 AND definition_revision = $2 AND catalogue_revision = $3`,
    [input.campaign_id, input.definition_revision, input.catalogue_revision, digest],
  )
  if (existingReceiptRow) {
    if (existingLabels.rows[0]?.label_count === input.labels.length
      && existingLabels.rows[0]?.digest_matches === true) {
      return 'idempotent'
    }
    throw new Error('Label catalogue revision conflicts with an existing receipt.')
  }
  if (existingLabels.rows[0]?.label_count !== 0) {
    throw new Error('Label catalogue revision conflicts with an existing receipt.')
  }

  const inserted = await client.query(
    `INSERT INTO nirmana_elevation_asset_labels
     (campaign_id, definition_revision, catalogue_revision, asset_id, sanskrit_name,
      english_name, description, legacy_aliases, source_ref, label_digest, recorded_by)
     SELECT $1, $2, $3, label.asset_id, label.sanskrit_name, label.english_name,
            label.description, label.legacy_aliases, label.source_ref, $5, $6
     FROM jsonb_to_recordset($4::jsonb) AS label(
       asset_id text, sanskrit_name text, english_name text, description text,
       legacy_aliases jsonb, source_ref text
     )
     ON CONFLICT DO NOTHING`,
    [input.campaign_id, input.definition_revision, input.catalogue_revision,
      JSON.stringify(input.labels), digest, input.recorded_by],
  )

  const receipt = await client.query(
    `INSERT INTO nirmana_elevation_campaign_events
     (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
      evidence_payload, source_kind, source_ref, observed_at, recorded_by)
     VALUES ($1, $2, $3, 'asset_label_catalogue_accepted', 'label_catalogue', $4,
             $5::jsonb, 'governed_catalogue', $6, now(), $7)
     ON CONFLICT (campaign_id, definition_revision, idempotency_key) DO NOTHING
     RETURNING event_id`,
    [input.campaign_id, input.definition_revision,
      receiptIdempotencyKey,
      input.catalogue_revision, JSON.stringify({
        ...receiptEvidencePayload,
        // This append-only campaign receipt is the normative acceptance audit:
        // it is actor-attributed and commits atomically with the frozen
        // definition and label rows. admin_audit_log is only a best-effort
        // operator index and is not part of this transaction.
      }),
      receiptSourceRef, input.recorded_by],
  )
  if (inserted.rowCount === input.labels.length && receipt.rowCount === 1) {
    return 'created'
  }
  throw new Error('Label catalogue revision conflicts with an existing receipt.')
}

export async function recordNirmanaElevationLabelCatalogue(
  raw: z.input<typeof NirmanaLabelCatalogueInputSchema>,
): Promise<'created' | 'idempotent'> {
  const client = await (await getNirmanaCampaignControlWriterPool()).connect()
  try {
    await client.query('BEGIN')
    const outcome = await recordNirmanaElevationLabelCatalogueInTransaction(client, raw)
    await client.query('COMMIT')
    return outcome
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  } finally {
    client.release()
  }
}
