import { NextResponse } from 'next/server'
import { z } from 'zod'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { writeAuditLog } from '@/lib/admin/audit'
import {
  createNirmanaElevationDefinition,
  NirmanaElevationDefinitionConflictError,
  NirmanaElevationEvidenceConflictError,
  NirmanaElevationEvidenceValidationError,
  NirmanaAssetAnalysisEvidenceSchema,
  NirmanaElevationManifestSchema,
  NirmanaOptimizationVerdictEvidenceSchema,
  freezeNirmanaElevationDefinition,
  recordNirmanaElevationEvidence,
  supersedeNirmanaElevationDefinition,
} from '@/lib/nirmana-elevation/definitions'
import {
  NirmanaLabelCatalogueInputSchema,
  recordNirmanaElevationLabelCatalogue,
} from '@/lib/nirmana-elevation/labels'
import { NIRMANA_STAGE_IDS } from '@/lib/nirmana-elevation/vocab'

const campaignId = z.literal('nirmana-elevation')
const revision = z.string().regex(/^[A-Za-z0-9._-]{1,128}$/)
const assetReceipt = z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.enum([
    'asset_analysis_accepted',
    'optimization_verdict_accepted',
    'implementation_accepted',
    'accepted_rebuild_observed',
    'integrity_verified',
    'asset_frozen',
    'probe_accepted',
    'static_accepted',
    'source_accepted',
    'empty_accepted',
    'retired_with_disposition',
    'producer_covered',
  ]),
  entity_type: z.literal('asset'),
  entity_id: z.string().min(1).max(256),
  layer: z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5']).nullable(),
  evidence_payload: z.record(z.string(), z.unknown()).default({}),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
}).superRefine((value, context) => {
  if (['accepted_rebuild_observed', 'producer_covered'].includes(value.event_type) && !value.source_ref.startsWith('build_run:')) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: `${value.event_type} requires an exact build_run:<id> source reference.` })
  }
  if (value.event_type === 'accepted_rebuild_observed') {
    if (!/^build_run:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.source_ref)) {
      context.addIssue({ code: 'custom', path: ['source_ref'], message: 'accepted_rebuild_observed requires an exact build_run UUID source reference.' })
    }
    const payload = z.object({
      output_digest: z.string().regex(/^[a-f0-9]{64}$/),
      output_digest_spec_sha256: z.string().regex(/^[a-f0-9]{64}$/),
    }).strict().safeParse(value.evidence_payload)
    if (!payload.success) {
      context.addIssue({ code: 'custom', path: ['evidence_payload'], message: 'accepted_rebuild_observed requires only output_digest and output_digest_spec_sha256 SHA-256 fields.' })
    }
  }
  if (value.event_type === 'asset_analysis_accepted') {
    const payload = NirmanaAssetAnalysisEvidenceSchema.safeParse(value.evidence_payload)
    if (!payload.success) {
      context.addIssue({ code: 'custom', path: ['evidence_payload'], message: 'asset_analysis_accepted requires only registry_fingerprint_sha256 and analysis_digest SHA-256 fields.' })
    }
    if (value.source_kind !== 'git_commit' || !/^git:[0-9a-f]{40}$/.test(value.source_ref)) {
      context.addIssue({ code: 'custom', path: ['source_ref'], message: 'asset_analysis_accepted requires source_kind=git_commit and an exact git:<40-hex> source reference.' })
    }
    if (value.layer === null) {
      context.addIssue({ code: 'custom', path: ['layer'], message: 'asset_analysis_accepted requires the asset layer.' })
    }
  }
  if (value.event_type === 'optimization_verdict_accepted') {
    const payload = NirmanaOptimizationVerdictEvidenceSchema.safeParse(value.evidence_payload)
    if (!payload.success) {
      context.addIssue({ code: 'custom', path: ['evidence_payload'], message: 'optimization_verdict_accepted requires a strict registry/analysis-bound verdict, basis, and proposal.' })
    }
    if (value.source_kind !== 'git_commit' || !/^git:[0-9a-f]{40}$/.test(value.source_ref)) {
      context.addIssue({ code: 'custom', path: ['source_ref'], message: 'optimization_verdict_accepted requires source_kind=git_commit and an exact git:<40-hex> source reference.' })
    }
    if (value.layer === null) {
      context.addIssue({ code: 'custom', path: ['layer'], message: 'optimization_verdict_accepted requires the asset layer.' })
    }
  }
})

const campaignStageReceipt = z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.literal('stage_transition_accepted'),
  entity_type: z.literal('campaign_stage'),
  entity_id: z.enum(NIRMANA_STAGE_IDS),
  layer: z.null(),
  evidence_payload: z.object({
    from_stage: z.enum(NIRMANA_STAGE_IDS).nullable(),
    to_stage: z.enum(NIRMANA_STAGE_IDS),
    prerequisites_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict(),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
}).strict().superRefine((value, context) => {
  if (value.entity_id !== value.evidence_payload.to_stage) {
    context.addIssue({ code: 'custom', path: ['entity_id'], message: 'Campaign-stage entity_id must equal evidence_payload.to_stage.' })
  }
  if (value.evidence_payload.from_stage === null) {
    if (value.evidence_payload.to_stage !== 'BOOTSTRAP') {
      context.addIssue({ code: 'custom', path: ['evidence_payload', 'from_stage'], message: 'Only BOOTSTRAP may have a null source stage.' })
    }
    return
  }
  const fromIndex = NIRMANA_STAGE_IDS.indexOf(value.evidence_payload.from_stage)
  const toIndex = NIRMANA_STAGE_IDS.indexOf(value.evidence_payload.to_stage)
  if (toIndex !== fromIndex + 1) {
    context.addIssue({ code: 'custom', path: ['evidence_payload', 'to_stage'], message: 'Campaign stages must advance exactly once in canonical order.' })
  }
})

const foundationLaneReceipt = z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.literal('foundation_lane_accepted'),
  entity_type: z.literal('foundation_lane'),
  entity_id: z.enum(['A', 'B', 'C', 'D', 'E']),
  layer: z.null(),
  evidence_payload: z.object({
    acceptance_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict(),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
}).strict()

const receipt = z.union([assetReceipt, campaignStageReceipt, foundationLaneReceipt])

const definition = z.object({
  command: z.literal('record_definition'),
  campaign_id: campaignId,
  definition_revision: revision,
  definition_status: z.literal('reconciling'),
  manifest: NirmanaElevationManifestSchema,
  manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
})
const freeze = definition.omit({ command: true, definition_status: true }).extend({ command: z.literal('freeze_definition') })
const supersede = z.object({
  command: z.literal('supersede_definition'),
  campaign_id: campaignId,
  expected_current_revision: revision,
  expected_current_manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  new_definition_revision: revision,
  new_manifest: NirmanaElevationManifestSchema,
  new_manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
})
const labelCatalogue = NirmanaLabelCatalogueInputSchema
  .omit({ recorded_by: true })
  .extend({ command: z.literal('record_label_catalogue') })

const command = z.union([definition, freeze, supersede, labelCatalogue, receipt])

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) {
    auth.headers.set('Cache-Control', 'no-store')
    return auth
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }
  const parsed = command.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: 'invalid Nirmana evidence command', issues: parsed.error.issues }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }

  try {
    if (parsed.data.command === 'record_definition') {
      const outcome = await createNirmanaElevationDefinition({ ...parsed.data, created_by: auth.user.uid })
      await writeAuditLog(auth.user.uid, 'nirmana_definition_recorded', null, {
        campaign_id: parsed.data.campaign_id,
        definition_revision: parsed.data.definition_revision,
        definition_status: parsed.data.definition_status,
        manifest_sha256: parsed.data.manifest_sha256,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsed.data.command === 'freeze_definition') {
      const outcome = await freezeNirmanaElevationDefinition(parsed.data)
      await writeAuditLog(auth.user.uid, 'nirmana_definition_recorded', null, {
        campaign_id: parsed.data.campaign_id,
        definition_revision: parsed.data.definition_revision,
        definition_status: 'frozen',
        manifest_sha256: parsed.data.manifest_sha256,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'frozen' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsed.data.command === 'supersede_definition') {
      const outcome = await supersedeNirmanaElevationDefinition({ ...parsed.data, created_by: auth.user.uid })
      await writeAuditLog(auth.user.uid, 'nirmana_definition_recorded', null, {
        command: 'supersede_definition',
        campaign_id: parsed.data.campaign_id,
        expected_current_revision: parsed.data.expected_current_revision,
        expected_current_manifest_sha256: parsed.data.expected_current_manifest_sha256,
        new_definition_revision: parsed.data.new_definition_revision,
        new_manifest_sha256: parsed.data.new_manifest_sha256,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'superseded' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsed.data.command === 'record_label_catalogue') {
      const outcome = await recordNirmanaElevationLabelCatalogue({
        campaign_id: parsed.data.campaign_id,
        definition_revision: parsed.data.definition_revision,
        catalogue_revision: parsed.data.catalogue_revision,
        labels: parsed.data.labels,
        catalogue_sha256: parsed.data.catalogue_sha256,
        recorded_by: auth.user.uid,
      })
      await writeAuditLog(auth.user.uid, 'nirmana_label_catalogue_recorded', null, {
        campaign_id: parsed.data.campaign_id,
        definition_revision: parsed.data.definition_revision,
        catalogue_revision: parsed.data.catalogue_revision,
        catalogue_sha256: parsed.data.catalogue_sha256,
        asset_count: parsed.data.labels.length,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    const outcome = await recordNirmanaElevationEvidence({ ...parsed.data, recorded_by: auth.user.uid })
    await writeAuditLog(auth.user.uid, 'nirmana_evidence_recorded', null, {
      campaign_id: parsed.data.campaign_id,
      definition_revision: parsed.data.definition_revision,
      idempotency_key: parsed.data.idempotency_key,
      event_type: parsed.data.event_type,
      entity_id: parsed.data.entity_id,
      source_ref: parsed.data.source_ref,
      outcome,
    })
    return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
  } catch (error) {
    if (error instanceof NirmanaElevationDefinitionConflictError
      || error instanceof NirmanaElevationEvidenceConflictError
      || error instanceof NirmanaElevationEvidenceValidationError) {
      return NextResponse.json({ error: error.message }, { status: 409, headers: { 'Cache-Control': 'no-store' } })
    }
    console.error('[api/admin/nirmana-elevation/evidence] write failed', error)
    return NextResponse.json({ error: 'failed to record Nirmana evidence' }, { status: 500, headers: { 'Cache-Control': 'no-store' } })
  }
}
