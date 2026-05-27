/**
 * Stream C / Unit 2d — POST /cockpit/command-center/api/edit
 *
 * Super-admin-only endpoint that writes a gate override via
 * configService.setGate (or resets it via resetGate). Danger gates require
 * `confirm: true` in the body; otherwise the call 422s.
 *
 * Body:
 *   { key, value, chartId?, reason?, confirm? }
 *   { key, reset: true, chartId?, reason?, confirm? }
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { getGateSpec } from '@/lib/gates/gate_registry'
import { setGate, resetGate, GateWriteError } from '@/lib/config/configService'

interface EditBody {
  key?: string
  value?: unknown
  reset?: boolean
  chartId?: string
  reason?: string
  confirm?: boolean
}

export async function POST(req: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  let body: EditBody
  try {
    body = (await req.json()) as EditBody
  } catch {
    return NextResponse.json(
      { error: { code: 'BAD_BODY', message: 'invalid JSON' } },
      { status: 400 },
    )
  }

  const key = body.key
  if (!key || typeof key !== 'string') {
    return NextResponse.json(
      { error: { code: 'KEY_REQUIRED', message: 'body.key is required' } },
      { status: 400 },
    )
  }

  let spec
  try {
    spec = getGateSpec(key)
  } catch {
    return NextResponse.json(
      { error: { code: 'UNKNOWN_GATE', message: `unknown gate "${key}"` } },
      { status: 404 },
    )
  }

  // Danger guard — every danger:true gate edit needs an explicit confirm flag.
  if (spec.danger && body.confirm !== true) {
    return NextResponse.json(
      {
        error: {
          code: 'CONFIRM_REQUIRED',
          message: `gate "${key}" is danger:true — body.confirm must be true`,
        },
      },
      { status: 422 },
    )
  }

  const principalUid = auth.user.uid

  try {
    if (body.reset === true) {
      await resetGate(key, principalUid, {
        chartId: body.chartId,
        reason: body.reason,
      })
    } else {
      await setGate(key, body.value, principalUid, {
        chartId: body.chartId,
        reason: body.reason,
      })
    }
  } catch (err) {
    if (err instanceof GateWriteError) {
      return NextResponse.json(
        { error: { code: err.code, message: err.message } },
        { status: 422 },
      )
    }
    return NextResponse.json(
      {
        error: {
          code: 'INTERNAL',
          message: err instanceof Error ? err.message : 'unknown error',
        },
      },
      { status: 500 },
    )
  }

  return NextResponse.json({ ok: true })
}
