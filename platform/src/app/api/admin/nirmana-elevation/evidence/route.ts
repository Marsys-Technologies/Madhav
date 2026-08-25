import { NextResponse } from 'next/server'
import { z } from 'zod'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { writeAuditLog } from '@/lib/admin/audit'
import {
  createNirmanaElevationDefinition,
  NirmanaElevationDefinitionConflictError,
  NirmanaElevationEvidenceConflictError,
  NirmanaElevationManifestSchema,
  freezeNirmanaElevationDefinition,
  recordNirmanaElevationEvidence,
} from '@/lib/nirmana-elevation/definitions'

const campaignId = z.literal('nirmana-elevation')
const revision = z.string().regex(/^[A-Za-z0-9._-]{1,128}$/)
const receipt = z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.enum([
    'asset_analysis_accepted',
    'optimization_verdict_accepted',
    'accepted_rebuild_observed',
    'integrity_verified',
    'asset_frozen',
    'source_accepted',
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
})

const definition = z.object({
  command: z.literal('record_definition'),
  campaign_id: campaignId,
  definition_revision: revision,
  definition_status: z.literal('reconciling'),
  manifest: NirmanaElevationManifestSchema,
  manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
})
const freeze = definition.omit({ command: true, definition_status: true }).extend({ command: z.literal('freeze_definition') })

const command = z.discriminatedUnion('command', [definition, freeze, receipt])

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

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
    if (error instanceof NirmanaElevationDefinitionConflictError || error instanceof NirmanaElevationEvidenceConflictError) {
      return NextResponse.json({ error: error.message }, { status: 409, headers: { 'Cache-Control': 'no-store' } })
    }
    console.error('[api/admin/nirmana-elevation/evidence] write failed', error)
    return NextResponse.json({ error: 'failed to record Nirmana evidence' }, { status: 500, headers: { 'Cache-Control': 'no-store' } })
  }
}
