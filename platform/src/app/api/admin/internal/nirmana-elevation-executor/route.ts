import 'server-only'
import { NextResponse } from 'next/server'
import { verifyOidcToken } from '@/lib/auth/oidc'
import { handleNirmanaEvidenceCommand, nirmanaEvidenceCommand } from '@/lib/nirmana-elevation/evidence-command'

// Non-browser submission path for the Nirmana elevation campaign's evidence
// and definition commands (record_definition, freeze_definition,
// supersede_definition, record_label_catalogue, accept_baseline_candidate,
// record_evidence). Mirrors the proven nirmana-elevation-monitor OIDC
// pattern: a fixed Cloud Run audience and a fixed expected principal, both
// hardcoded rather than environment-configurable, so a misconfigured
// deployment cannot widen who this route accepts. This authenticates *who
// may call the route*; the underlying writers still separately enforce
// DB-role identity separation by source_kind (server_reconstructed ->
// nirmana_evidence_ingress_writer, else -> nirmana_campaign_control_writer)
// regardless of which HTTP-layer principal made the call.
const EXECUTOR_OIDC_AUDIENCE = 'https://amjis-web-938361928218.asia-south1.run.app'
// The native's own Google identity. No dedicated service account exists for
// this route yet: provisioning one is a GCP IAM change and, per
// infra/nirmana_elevation_monitor/README.md, requires the two-person
// saved-plan apply discipline (named approved operator + independent
// reviewer + recorded approval reference) that this session cannot satisfy
// itself. Until that identity is provisioned, this route accepts only the
// native's own already-privileged principal, minted directly (e.g. `gcloud
// auth print-identity-token --audiences=...`) rather than through a browser
// session.
const EXECUTOR_PRINCIPAL = 'mail.abhisek.mohanty@gmail.com'

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const authorization = request.headers.get('Authorization')
  if (!authorization?.startsWith('Bearer ')) {
    return NextResponse.json(
      { error: 'unauthorized' },
      { status: 401, headers: { 'Cache-Control': 'no-store' } },
    )
  }

  let actorEmail: string
  try {
    const identity = await verifyOidcToken(authorization.slice('Bearer '.length), {
      expectedAudience: EXECUTOR_OIDC_AUDIENCE,
      expectedServiceAccount: EXECUTOR_PRINCIPAL,
    })
    if (!identity) {
      return NextResponse.json(
        { error: 'forbidden' },
        { status: 403, headers: { 'Cache-Control': 'no-store' } },
      )
    }
    actorEmail = identity.email
  } catch {
    return NextResponse.json(
      { error: 'forbidden' },
      { status: 403, headers: { 'Cache-Control': 'no-store' } },
    )
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'invalid JSON body' }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }
  const parsed = nirmanaEvidenceCommand.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: 'invalid Nirmana evidence command', issues: parsed.error.issues }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }

  const response = await handleNirmanaEvidenceCommand(parsed.data, `nirmana-executor:${actorEmail}`)
  response.headers.set('Cache-Control', 'no-store')
  return response
}
