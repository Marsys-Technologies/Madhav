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
// itself.
//
// IMPORTANT (confirmed live, 2026-09-01): a *human* Google identity cannot
// mint an audience-bound OIDC ID token at all -- `gcloud auth
// print-identity-token --audiences=...` fails with "Invalid account type
// ... Requires valid service account" for a user account, and there is no
// other GCP-supported path to one: `iam.serviceAccounts.getOpenIdToken`
// (what backs audience-scoped ID token minting) is a service-account-only
// capability. This is a GCP IAM design constraint, not a CLI inconvenience.
// So while the auth check below is correctly implemented and this route is
// live and reachable (unauthenticated calls confirmed 401 in production),
// nothing -- not even the native himself, from a shell -- can currently
// present a token this route would accept. This is not yet the "non-browser
// authenticated submission path" the campaign asked for; it is the route
// half of it, waiting on the credential half: either the dedicated
// service-account identity (the two-person IaC path above) or a change to
// this route's auth model. Until one of those lands, this constant stays
// a placeholder, not a functioning credential path.
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
