import 'server-only'
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { verifyOidcToken } from '@/lib/auth/oidc'
import {
  evaluateNirmanaConductor,
  NIRMANA_CONDUCTOR_AUDIENCE,
  NIRMANA_CONDUCTOR_PRINCIPAL,
  NIRMANA_VERIFIER_PRINCIPAL,
  recordNirmanaUnattendedReadiness,
  verifyNirmanaUnattendedReadiness,
} from '@/lib/nirmana-elevation/conductor'

const command = z.object({ command: z.enum(['evaluate', 'verify_readiness']) }).strict()

export async function POST(request: Request) {
  const authorization = request.headers.get('Authorization')
  if (!authorization?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401, headers: { 'Cache-Control': 'no-store' } })
  }
  let body: z.infer<typeof command>
  try { body = command.parse(await request.json()) } catch {
    return NextResponse.json({ error: 'invalid_request' }, { status: 400, headers: { 'Cache-Control': 'no-store' } })
  }

  const expectedPrincipal = body.command === 'evaluate' ? NIRMANA_CONDUCTOR_PRINCIPAL : NIRMANA_VERIFIER_PRINCIPAL
  try {
    const identity = await verifyOidcToken(authorization.slice('Bearer '.length), {
      expectedAudience: NIRMANA_CONDUCTOR_AUDIENCE,
      expectedServiceAccount: expectedPrincipal,
    })
    if (!identity) return NextResponse.json({ error: 'forbidden' }, { status: 403, headers: { 'Cache-Control': 'no-store' } })
  } catch {
    return NextResponse.json({ error: 'forbidden' }, { status: 403, headers: { 'Cache-Control': 'no-store' } })
  }

  try {
    if (body.command === 'verify_readiness') {
      const result = await verifyNirmanaUnattendedReadiness()
      await recordNirmanaUnattendedReadiness(NIRMANA_VERIFIER_PRINCIPAL, result)
      return NextResponse.json({ ok: true, command: body.command, verdict: result.verdict, expires_at: result.expires_at, checks: result.checks }, { headers: { 'Cache-Control': 'no-store' } })
    }
    const result = await evaluateNirmanaConductor(NIRMANA_CONDUCTOR_PRINCIPAL)
    return NextResponse.json({ ok: true, command: body.command, ...result }, { headers: { 'Cache-Control': 'no-store' } })
  } catch {
    return NextResponse.json({ ok: false, error: 'conductor_unavailable' }, { status: 503, headers: { 'Cache-Control': 'no-store' } })
  }
}
