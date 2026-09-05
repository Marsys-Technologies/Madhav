import 'server-only'
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { writeAuditLog } from '@/lib/admin/audit'
import {
  acceptNirmanaBaselineCandidate,
  createNirmanaElevationDefinition,
  NirmanaElevationDefinitionConflictError,
  NirmanaElevationEvidenceConflictError,
  NirmanaElevationEvidenceValidationError,
  NirmanaAssetAnalysisEvidenceSchema,
  NirmanaFreezeEvidenceSchema,
  NirmanaImplementationEvidenceSchema,
  NirmanaIntegrityEvidenceSchema,
  NirmanaFoundationLaneEvidenceSchema,
  NirmanaElevationManifestSchema,
  NirmanaNonBuildDispositionEvidenceSchema,
  NirmanaOptimizationVerdictEvidenceSchema,
  NirmanaProbeEvidenceSchema,
  NirmanaProducerCoverageEvidenceSchema,
  NirmanaRebuildEvidenceSchema,
  NirmanaStageTransitionEvidenceSchema,
  freezeNirmanaElevationDefinition,
  recordNirmanaElevationEvidence,
  supersedeNirmanaElevationDefinition,
} from '@/lib/nirmana-elevation/definitions'
import {
  NirmanaLabelCatalogueInputSchema,
  recordNirmanaElevationLabelCatalogue,
} from '@/lib/nirmana-elevation/labels'
import { checkRateLimit } from '@/lib/mcp/rate_limiter'
import { publishCockpitEvent } from '@/lib/nirmana-elevation/cockpit-events'
import { NIRMANA_STAGE_IDS } from '@/lib/nirmana-elevation/vocab'

// This schema and dispatch function are shared verbatim between the
// browser-session evidence route and the non-browser (OIDC) executor route:
// the command contract and every lifecycle invariant it enforces must be
// identical regardless of which authentication boundary accepted the call.
// Only the actor identity and how it was authenticated differ between callers.

const campaignId = z.literal('nirmana-elevation')
const revision = z.string().regex(/^[A-Za-z0-9._-]{1,128}$/)
const buildRunSourceRef = /^build_run:([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i
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
  if (['accepted_rebuild_observed', 'producer_covered'].includes(value.event_type) && !buildRunSourceRef.test(value.source_ref)) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: `${value.event_type} requires an exact build_run UUID source reference.` })
  }
  if (value.event_type === 'accepted_rebuild_observed') {
    const payload = NirmanaRebuildEvidenceSchema.safeParse(value.evidence_payload)
    if (!payload.success) {
      context.addIssue({ code: 'custom', path: ['evidence_payload'], message: 'accepted_rebuild_observed requires a strict run, lifecycle, decision, implementation, and output-digest receipt.' })
    } else if (buildRunSourceRef.exec(value.source_ref)?.[1].toLowerCase() !== payload.data.build_run_id.toLowerCase()) {
      context.addIssue({ code: 'custom', path: ['evidence_payload', 'build_run_id'], message: 'accepted_rebuild_observed build_run_id must equal the build_run source UUID.' })
    }
    if (value.source_kind !== 'build_run') {
      context.addIssue({ code: 'custom', path: ['source_kind'], message: 'accepted_rebuild_observed requires source_kind=build_run.' })
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
  const typedLifecyclePayloads: Partial<Record<typeof value.event_type, z.ZodType>> = {
    implementation_accepted: NirmanaImplementationEvidenceSchema,
    probe_accepted: NirmanaProbeEvidenceSchema,
    static_accepted: NirmanaNonBuildDispositionEvidenceSchema,
    source_accepted: NirmanaNonBuildDispositionEvidenceSchema,
    empty_accepted: NirmanaNonBuildDispositionEvidenceSchema,
    retired_with_disposition: NirmanaNonBuildDispositionEvidenceSchema,
    integrity_verified: NirmanaIntegrityEvidenceSchema,
    asset_frozen: NirmanaFreezeEvidenceSchema,
    producer_covered: NirmanaProducerCoverageEvidenceSchema,
  }
  const typedPayload = typedLifecyclePayloads[value.event_type]
  if (typedPayload && !typedPayload.safeParse(value.evidence_payload).success) {
    context.addIssue({ code: 'custom', path: ['evidence_payload'], message: `${value.event_type} requires its strict lifecycle receipt payload.` })
  }
  if (['implementation_accepted', 'static_accepted', 'source_accepted', 'empty_accepted', 'retired_with_disposition'].includes(value.event_type)
    && (value.source_kind !== 'git_commit' || !/^git:[0-9a-f]{40}$/.test(value.source_ref))) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: `${value.event_type} requires source_kind=git_commit and an exact deployed git source reference.` })
  }
  if (value.event_type === 'probe_accepted'
    && (value.source_kind !== 'server_reconstructed' || value.source_ref !== `nirmana-elevation:health-probe:${value.entity_id}`)) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: 'probe_accepted requires the exact server-reconstructed health-probe source.' })
  }
  if (value.event_type === 'producer_covered') {
    const payload = NirmanaProducerCoverageEvidenceSchema.safeParse(value.evidence_payload)
    if (payload.success && buildRunSourceRef.exec(value.source_ref)?.[1].toLowerCase() !== payload.data.producer_run_id.toLowerCase()) {
      context.addIssue({ code: 'custom', path: ['evidence_payload', 'producer_run_id'], message: 'producer_covered producer_run_id must equal the build_run source UUID.' })
    }
    if (value.source_kind !== 'build_run') {
      context.addIssue({ code: 'custom', path: ['source_kind'], message: 'producer_covered requires source_kind=build_run.' })
    }
  }
  if (value.event_type === 'integrity_verified'
    && (value.source_kind !== 'server_reconstructed' || value.source_ref !== `nirmana-elevation:integrity:${value.entity_id}`)) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: 'integrity_verified requires the exact server-reconstructed integrity source.' })
  }
  if (value.event_type === 'asset_frozen'
    && (value.source_kind !== 'server_reconstructed' || value.source_ref !== `nirmana-elevation:freeze:${value.entity_id}`)) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: 'asset_frozen requires the exact server-reconstructed freeze source.' })
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
  evidence_payload: NirmanaStageTransitionEvidenceSchema,
  source_kind: z.literal('server_reconstructed'),
  source_ref: z.literal('nirmana-elevation:stage-spine'),
  observed_at: z.string().datetime(),
}).strict().superRefine((value, context) => {
  if (value.entity_id !== value.evidence_payload.to_stage) {
    context.addIssue({ code: 'custom', path: ['entity_id'], message: 'Campaign-stage entity_id must equal evidence_payload.to_stage.' })
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
  evidence_payload: NirmanaFoundationLaneEvidenceSchema,
  source_kind: z.literal('server_reconstructed'),
  source_ref: z.string().regex(/^nirmana-elevation:foundation-lane:[A-E]$/),
  observed_at: z.string().datetime(),
}).strict().superRefine((value, context) => {
  if (value.entity_id !== value.evidence_payload.lane_id) {
    context.addIssue({ code: 'custom', path: ['entity_id'], message: 'Foundation-lane entity_id must equal the typed receipt lane.' })
  }
  if (value.source_ref !== `nirmana-elevation:foundation-lane:${value.evidence_payload.lane_id}`) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: 'Foundation-lane source_ref must identify its exact typed lane.' })
  }
})

const buildRunAuthorizationReceipt = z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.literal('build_run_authorized'),
  entity_type: z.literal('build_run'),
  entity_id: z.string().uuid(),
  layer: z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5']),
  evidence_payload: z.object({
    wave_index: z.number().int().nonnegative(),
    asset_ids: z.array(z.string().min(1).max(256)).min(1).max(256),
    authorization_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict(),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
}).strict().superRefine((value, context) => {
  const match = buildRunSourceRef.exec(value.source_ref)
  if (!match || match[1].toLowerCase() !== value.entity_id.toLowerCase()) {
    context.addIssue({ code: 'custom', path: ['source_ref'], message: 'Build-run authorization must reference its exact entity UUID.' })
  }
  if (new Set(value.evidence_payload.asset_ids).size !== value.evidence_payload.asset_ids.length) {
    context.addIssue({ code: 'custom', path: ['evidence_payload', 'asset_ids'], message: 'Authorized asset IDs must be unique.' })
  }
})

const receipt = z.union([assetReceipt, campaignStageReceipt, foundationLaneReceipt, buildRunAuthorizationReceipt])

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
  source_observation_id: z.string().uuid(),
  expected_candidate_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  expected_candidate_catalogue_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  new_definition_revision: revision,
}).strict()
const labelCatalogue = NirmanaLabelCatalogueInputSchema
  .omit({ recorded_by: true })
  .extend({ command: z.literal('record_label_catalogue') })
const baselineCandidateAcceptance = z.object({
  command: z.literal('accept_baseline_candidate'),
  source_observation_id: z.string().uuid(),
  definition_revision: revision,
  expected_candidate_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  expected_candidate_catalogue_sha256: z.string().regex(/^[a-f0-9]{64}$/),
}).strict()

export const nirmanaEvidenceCommand = z.union([definition, freeze, supersede, labelCatalogue, baselineCandidateAcceptance, receipt])
export type NirmanaEvidenceCommand = z.infer<typeof nirmanaEvidenceCommand>

/**
 * Shared dispatch for every Nirmana evidence/definition mutation. Identical
 * for the browser-session route and the non-browser (OIDC) executor route:
 * only `actorId` (and how it was authenticated) differs between callers. The
 * underlying writer functions still enforce their own DB-role/source_kind
 * separation (server_reconstructed -> ingress writer, else -> control
 * writer) regardless of which HTTP boundary accepted the call.
 */
export async function handleNirmanaEvidenceCommand(
  parsedData: NirmanaEvidenceCommand,
  actorId: string,
): Promise<NextResponse> {
  if (parsedData.command === 'accept_baseline_candidate' || parsedData.command === 'supersede_definition') {
    const isSupersession = parsedData.command === 'supersede_definition'
    let rateLimit
    try {
      rateLimit = await checkRateLimit(`admin:nirmana_${parsedData.command}:${actorId}`)
    } catch {
      // This explicit mutation fails closed when the shared limiter is
      // unavailable. Never open the acceptance transaction without a decision,
      // and never log a raw database error from this boundary.
      console.error(`[nirmana-elevation/evidence-command] ${isSupersession ? 'supersession' : 'baseline acceptance'} rate limiter unavailable`)
      return NextResponse.json(
        { error: isSupersession ? 'supersession rate limiter unavailable' : 'baseline acceptance rate limiter unavailable' },
        { status: 503, headers: { 'Cache-Control': 'no-store', 'Retry-After': '60' } },
      )
    }
    if (!rateLimit.allowed) {
      return NextResponse.json(
        { error: isSupersession ? 'supersession rate limit exceeded' : 'baseline acceptance rate limit exceeded' },
        {
          status: 429,
          headers: {
            'Cache-Control': 'no-store',
            'Retry-After': String(rateLimit.retry_after_seconds ?? 60),
          },
        },
      )
    }
  }

  try {
    if (parsedData.command === 'record_definition') {
      const outcome = await createNirmanaElevationDefinition({ ...parsedData, created_by: actorId })
      await writeAuditLog(actorId, 'nirmana_definition_recorded', null, {
        campaign_id: parsedData.campaign_id,
        definition_revision: parsedData.definition_revision,
        definition_status: parsedData.definition_status,
        manifest_sha256: parsedData.manifest_sha256,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsedData.command === 'freeze_definition') {
      const outcome = await freezeNirmanaElevationDefinition(parsedData)
      await writeAuditLog(actorId, 'nirmana_definition_recorded', null, {
        campaign_id: parsedData.campaign_id,
        definition_revision: parsedData.definition_revision,
        definition_status: 'frozen',
        manifest_sha256: parsedData.manifest_sha256,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'frozen' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsedData.command === 'supersede_definition') {
      const outcome = await supersedeNirmanaElevationDefinition({ ...parsedData, created_by: actorId })
      await writeAuditLog(actorId, 'nirmana_definition_recorded', null, {
        command: 'supersede_definition',
        campaign_id: parsedData.campaign_id,
        expected_current_revision: parsedData.expected_current_revision,
        expected_current_manifest_sha256: parsedData.expected_current_manifest_sha256,
        source_observation_id: parsedData.source_observation_id,
        candidate_manifest_sha256: parsedData.expected_candidate_sha256,
        candidate_catalogue_sha256: parsedData.expected_candidate_catalogue_sha256,
        new_definition_revision: parsedData.new_definition_revision,
        outcome,
      })
      if (outcome === 'superseded') {
        await publishCockpitEvent({ type: 'nirmana.definition_superseded', definition_revision: parsedData.new_definition_revision })
      }
      return NextResponse.json({ outcome }, { status: outcome === 'superseded' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsedData.command === 'record_label_catalogue') {
      const outcome = await recordNirmanaElevationLabelCatalogue({
        campaign_id: parsedData.campaign_id,
        definition_revision: parsedData.definition_revision,
        catalogue_revision: parsedData.catalogue_revision,
        labels: parsedData.labels,
        catalogue_sha256: parsedData.catalogue_sha256,
        recorded_by: actorId,
      })
      await writeAuditLog(actorId, 'nirmana_label_catalogue_recorded', null, {
        campaign_id: parsedData.campaign_id,
        definition_revision: parsedData.definition_revision,
        catalogue_revision: parsedData.catalogue_revision,
        catalogue_sha256: parsedData.catalogue_sha256,
        asset_count: parsedData.labels.length,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    if (parsedData.command === 'accept_baseline_candidate') {
      const outcome = await acceptNirmanaBaselineCandidate({
        campaign_id: 'nirmana-elevation',
        source_observation_id: parsedData.source_observation_id,
        definition_revision: parsedData.definition_revision,
        expected_candidate_sha256: parsedData.expected_candidate_sha256,
        expected_candidate_catalogue_sha256: parsedData.expected_candidate_catalogue_sha256,
        created_by: actorId,
      })
      // Normative audit provenance is the append-only
      // asset_label_catalogue_accepted campaign receipt committed by the same
      // serializable transaction as the frozen definition and labels. This
      // admin audit row is intentionally secondary/operator-facing and remains
      // best-effort; acceptance never depends on the unrelated admin table.
      await writeAuditLog(actorId, 'nirmana_definition_recorded', null, {
        command: 'accept_baseline_candidate',
        campaign_id: 'nirmana-elevation',
        source_observation_id: parsedData.source_observation_id,
        definition_revision: parsedData.definition_revision,
        candidate_manifest_sha256: parsedData.expected_candidate_sha256,
        candidate_catalogue_sha256: parsedData.expected_candidate_catalogue_sha256,
        outcome,
      })
      return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
    }

    const outcome = await recordNirmanaElevationEvidence({ ...parsedData, recorded_by: actorId })
    await writeAuditLog(actorId, 'nirmana_evidence_recorded', null, {
      campaign_id: parsedData.campaign_id,
      definition_revision: parsedData.definition_revision,
      idempotency_key: parsedData.idempotency_key,
      event_type: parsedData.event_type,
      entity_id: parsedData.entity_id,
      source_ref: parsedData.source_ref,
      outcome,
    })
    if (outcome === 'created') {
      await publishCockpitEvent({
        type: 'nirmana.evidence_accepted',
        event_type: parsedData.event_type,
        asset_id: parsedData.entity_id,
        layer: parsedData.layer,
      })
    }
    return NextResponse.json({ outcome }, { status: outcome === 'created' ? 201 : 200, headers: { 'Cache-Control': 'no-store' } })
  } catch (error) {
    if (error instanceof NirmanaElevationDefinitionConflictError
      || error instanceof NirmanaElevationEvidenceConflictError
      || error instanceof NirmanaElevationEvidenceValidationError) {
      return NextResponse.json({ error: error.message }, { status: 409, headers: { 'Cache-Control': 'no-store' } })
    }
    console.error('[nirmana-elevation/evidence-command] write failed', error)
    return NextResponse.json({ error: 'failed to record Nirmana evidence' }, { status: 500, headers: { 'Cache-Control': 'no-store' } })
  }
}
