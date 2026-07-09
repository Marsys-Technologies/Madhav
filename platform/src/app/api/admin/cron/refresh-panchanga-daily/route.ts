/**
 * /api/admin/cron/refresh-panchanga-daily — R5.1 C3 scheduled monthly refresh.
 *
 * Proxies to the python-sidecar's POST /api/compute/panchanga/refresh, which
 * runs panchanga_daily_writer.write_window() (Swiss Ephemeris / pyswisseph,
 * deterministic — no LLM) to keep the rolling +12-month panchanga_daily window
 * current. Idempotent (upsert on (date) PK) — safe to call more often than
 * scheduled without side effects.
 *
 * Auth: MARSYS_CRON_SECRET, checked via the x-marsys-cron-secret header before
 * any work happens — NOT the Authorization header (R5.2 A4 live-verification
 * finding: Cloud Scheduler's HTTP target does not deliver a custom Authorization
 * header to amjis-web unmolested — a direct curl with the identical header
 * succeeds, but the identical header sent via a live Cloud Scheduler job 401s,
 * and the pre-existing sibling amjis-pending-stream-reaper job — same
 * Authorization-header pattern, applied before this run — has been silently
 * failing in prod with the same symptom, confirmed via its own status.code=2
 * live. Mirrors the already-proven x-watchdog-auth custom-header convention
 * (src/app/api/cockpit/watchdog/route.ts), which does not hit this collision.
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
  const auth = request.headers.get('x-marsys-cron-secret')

  if (!expected || auth !== expected) {
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
