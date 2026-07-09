/**
 * /api/admin/cron/refresh-panchanga-daily — R5.1 C3 scheduled monthly refresh.
 *
 * Proxies to the python-sidecar's POST /api/compute/panchanga/refresh, which
 * runs panchanga_daily_writer.write_window() (Swiss Ephemeris / pyswisseph,
 * deterministic — no LLM) to keep the rolling +12-month panchanga_daily window
 * current. Idempotent (upsert on (date) PK) — safe to call more often than
 * scheduled without side effects.
 *
 * Auth: same bearer-secret pattern as the sibling reap-pending-streams cron
 * route (src/app/api/admin/cron/reap-pending-streams/route.ts) —
 * MARSYS_CRON_SECRET, checked before any work happens.
 *
 * Intended trigger: Cloud Scheduler job `panchanga-daily-refresh` (monthly).
 * See infra/scheduler/panchanga_refresh.tf — Terraform resource authored but
 * NOT applied by this session (infra/scheduler/README.md: "Apply discipline:
 * IaC only. Apply runs on main; never from a worktree."). Flagged for the
 * conductor to `terraform apply` post-merge.
 */
import 'server-only'
import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const expected = process.env.MARSYS_CRON_SECRET
  const auth = request.headers.get('Authorization')

  if (!expected || auth !== `Bearer ${expected}`) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const sidecarUrl = process.env.PYTHON_SIDECAR_URL
  const sidecarKey = process.env.PYTHON_SIDECAR_API_KEY ?? ''
  if (!sidecarUrl) {
    return NextResponse.json({ error: 'PYTHON_SIDECAR_URL not configured' }, { status: 503 })
  }

  try {
    const resp = await fetch(`${sidecarUrl}/api/compute/panchanga/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-api-key': sidecarKey },
      body: JSON.stringify({}),
      signal: AbortSignal.timeout(120_000),
    })
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok) {
      return NextResponse.json({ ok: false, sidecar_status: resp.status, detail: data }, { status: 502 })
    }
    return NextResponse.json(data)
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err) }, { status: 502 })
  }
}
