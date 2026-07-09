/**
 * /api/admin/cron/run-canary-battery — R5.1 C5.2 daily scheduled canary battery.
 *
 * Runs the ported P1-P8 canary probe set (platform/src/lib/canary/canary_probes.ts,
 * ported from evals/r5-w0a-canary/canary_runner.ts's R5 W0a §14 eight-probe audit)
 * LIVE against prod amjis-mcp via read-only MCP tool calls — no writes, no chart-data
 * mutation, no migrations. Persists every probe result to `system_health` (migration
 * 366) and, when a probe that PASSED on the immediately-prior run FAILS on this run
 * (a regression, not just an ongoing known-fail), dispatches an alert through the
 * EXISTING mcp_alerts_config + checkAndDispatch mechanism (src/lib/alerts/dispatch.ts)
 * — the same Slack/email path already used by the nightly MCP audit job. No new alert
 * channel is invented here.
 *
 * Auth: MARSYS_CRON_SECRET, checked via the x-marsys-cron-secret header before any
 * work happens (R5.2 A4 live-verification finding: Cloud Scheduler's HTTP target
 * does not deliver a custom Authorization header to amjis-web unmolested — see
 * refresh-panchanga-daily/route.ts's identical header for the full finding).
 * Reuses the SAME secret (mcpt-scheduler-secret in Secret Manager) rather than
 * minting a new one, per this repo's established scheduler-auth precedent.
 *
 * MCP credential: MCP_CANARY_KEY env var — the read-only `probe-service-account` test
 * credential provisioned in R5 W0a (00_ARCHITECTURE/R5_RUN_LEDGER_v1_0.md P0-iii),
 * granted `view` on both canonical charts. NOT wired into the Cloud Run service yet —
 * see infra/scheduler/canary_battery.tf header comment for the exact provisioning
 * command the conductor needs to run.
 *
 * Intended trigger: Cloud Scheduler job `canary-battery-daily` (daily). See
 * infra/scheduler/canary_battery.tf — Terraform resource authored but NOT applied by
 * this session (infra/scheduler/README.md: "Apply discipline: IaC only. Apply runs on
 * main; never from a worktree."). Flagged for the conductor to `terraform apply`
 * post-merge, same pattern as C3's panchanga_refresh.tf.
 */
import 'server-only'
import { randomUUID } from 'crypto'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { runCanaryBattery, type ProbeResult, type ProbeStatus } from '@/lib/canary/canary_probes'
import { checkAndDispatch } from '@/lib/alerts/dispatch'

export const maxDuration = 60

const COMPONENT = 'canary_battery'

interface PriorStatusRow {
  probe_id: string
  chart_id: string
  status: ProbeStatus
}

async function loadPriorStatuses(): Promise<Map<string, ProbeStatus>> {
  // Most recent row per (probe_id, chart_id) BEFORE this run — DISTINCT ON relies on
  // the system_health_probe_recency index (component, probe_id, chart_id, checked_at DESC).
  const result = await query<PriorStatusRow>(
    `SELECT DISTINCT ON (probe_id, chart_id) probe_id, chart_id, status
     FROM system_health
     WHERE component = $1
     ORDER BY probe_id, chart_id, checked_at DESC`,
    [COMPONENT],
  )
  const map = new Map<string, ProbeStatus>()
  for (const row of result.rows) {
    map.set(`${row.probe_id}::${row.chart_id}`, row.status)
  }
  return map
}

async function persistResults(runId: string, results: ProbeResult[]): Promise<void> {
  for (const r of results) {
    await query(
      `INSERT INTO system_health (component, probe_id, chart_id, status, detail, latency_ms, run_id)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [COMPONENT, r.probe_id, r.chart_id, r.status, r.detail, r.latency_ms, runId],
    )
  }
}

export async function POST(request: Request) {
  const expected = process.env.MARSYS_CRON_SECRET
  const auth = request.headers.get('x-marsys-cron-secret')

  if (!expected || auth !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  const mcpUrl = process.env.MCP_CANARY_URL ?? 'https://amjis-mcp-qm256lasva-el.a.run.app/mcp'
  const mcpKey = process.env.MCP_CANARY_KEY ?? ''
  if (!mcpKey) {
    return NextResponse.json({ error: 'MCP_CANARY_KEY not configured' }, { status: 503 })
  }

  const runId = randomUUID()
  const runAt = new Date().toISOString()

  try {
    const priorStatuses = await loadPriorStatuses()
    const results = await runCanaryBattery(mcpUrl, mcpKey)
    await persistResults(runId, results)

    const regressions = results.filter((r) => {
      const prior = priorStatuses.get(`${r.probe_id}::${r.chart_id}`)
      return prior === 'pass' && r.status !== 'pass'
    })
    const failing = results.filter((r) => r.status !== 'pass')

    const alertResults = await checkAndDispatch([
      { metric_name: 'canary_probe_regression_count', value: regressions.length, window_hours: 1, sampled_at: runAt },
      { metric_name: 'canary_probe_fail_count', value: failing.length, window_hours: 1, sampled_at: runAt },
    ])

    return NextResponse.json({
      ok: true,
      run_id: runId,
      run_at: runAt,
      probes_total: results.length,
      probes_pass: results.length - failing.length,
      probes_fail: failing.filter((r) => r.status === 'fail').length,
      probes_error: failing.filter((r) => r.status === 'error').length,
      regressions: regressions.map((r) => ({ probe_id: r.probe_id, chart_tag: r.chart_tag, name: r.name })),
      alerts_dispatched: alertResults,
    })
  } catch (err) {
    console.error('[run-canary-battery]', err)
    return NextResponse.json({ ok: false, error: String(err) }, { status: 502 })
  }
}
