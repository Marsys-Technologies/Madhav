import 'server-only'
import { NextResponse } from 'next/server'
import { verifyOidcToken } from '@/lib/auth/oidc'
import { handleNirmanaEvidenceCommand, nirmanaEvidenceCommand, type NirmanaEvidenceCommand } from '@/lib/nirmana-elevation/evidence-command'

// Non-browser submission path for the Nirmana elevation campaign's evidence
// and definition commands (record_definition, freeze_definition,
// supersede_definition, record_label_catalogue, accept_baseline_candidate,
// record_evidence). Mirrors the proven nirmana-elevation-monitor OIDC
// pattern: a fixed Cloud Run audience, both hardcoded rather than
// environment-configurable, so a misconfigured deployment cannot widen who
// this route accepts.
const EXECUTOR_OIDC_AUDIENCE = 'https://amjis-web-938361928218.asia-south1.run.app'

// Two dedicated identities, not one -- see infra/nirmana_elevation_executor
// (Terraform: two service accounts, serviceAccountTokenCreator granted only
// to the native's own Google identity for on-demand impersonation; no
// standing trigger, no key file, no invoker grant -- amjis-web already
// grants roles/run.invoker to allUsers, verified live, so every route here
// does its own app-layer authorization).
//
// This makes implementer != certifier identity-enforced at the HTTP layer,
// not only DB-role-enforced: `requiredPrincipalFor` below mirrors the exact
// same split the DB-layer trigger already makes
// (nirmana_elevation_guard_server_reconstructed_insert: source_kind =
// 'server_reconstructed' -> must be the ingress writer session; else -> must
// be the control writer session). The executor SA is the HTTP-layer
// counterpart of the control writer; the verifier SA is the HTTP-layer
// counterpart of the ingress writer.
//
// HONEST RESIDUAL (recorded in CAMPAIGN_STATE.md): the native currently
// holds serviceAccountTokenCreator on both identities, so this allowlist
// enforces separation of *what a given authenticated call may submit*, not
// separation between disjoint human principals. The campaign's own
// fresh-context-verification protocol (a terminal capsule is only ever
// minted after independent reconstruction, never by the session that did
// the implementation) is what carries the rest of implementer != certifier
// today. WIF attribute-condition-based separation is a later option, not
// applied here.
const EXECUTOR_PRINCIPAL = 'amjis-nirmana-executor@madhav-astrology.iam.gserviceaccount.com'
const VERIFIER_PRINCIPAL = 'amjis-nirmana-verifier@madhav-astrology.iam.gserviceaccount.com'

function requiredPrincipalFor(command: NirmanaEvidenceCommand): string {
  // Every record_evidence event_type whose schema requires
  // source_kind='server_reconstructed' (probe_accepted, integrity_verified,
  // asset_frozen, stage_transition_accepted, foundation_lane_accepted) is
  // exactly the set the DB trigger already routes to the ingress writer.
  // Checking the actual submitted source_kind (rather than hardcoding an
  // event_type list) keeps this in sync with that schema by construction.
  if (command.command === 'record_evidence' && command.source_kind === 'server_reconstructed') {
    return VERIFIER_PRINCIPAL
  }
  return EXECUTOR_PRINCIPAL
}

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const authorization = request.headers.get('Authorization')
  if (!authorization?.startsWith('Bearer ')) {
    return NextResponse.json(
      { error: 'unauthorized' },
      { status: 401, headers: { 'Cache-Control': 'no-store' } },
    )
  }

  // Verify the token is a genuine, non-expired, correctly-audienced Google ID
  // token before touching the body -- but do not pin expectedServiceAccount
  // yet: which of the two principals is *required* depends on the command,
  // which lives in the body. This still rejects any caller without a valid
  // token for this audience up front, regardless of body content.
  let actorEmail: string
  try {
    const identity = await verifyOidcToken(authorization.slice('Bearer '.length), {
      expectedAudience: EXECUTOR_OIDC_AUDIENCE,
    })
    if (!identity || ![EXECUTOR_PRINCIPAL, VERIFIER_PRINCIPAL].includes(identity.email)) {
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

  if (actorEmail !== requiredPrincipalFor(parsed.data)) {
    return NextResponse.json(
      { error: 'principal not authorized for this command' },
      { status: 403, headers: { 'Cache-Control': 'no-store' } },
    )
  }

  const response = await handleNirmanaEvidenceCommand(parsed.data, `nirmana-executor:${actorEmail}`)
  response.headers.set('Cache-Control', 'no-store')
  return response
}
