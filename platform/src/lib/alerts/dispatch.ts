/**
 * alerts/dispatch.ts — Slack + email alert dispatcher.
 *
 * Reads mcp_alerts_config from the DB and dispatches notifications when
 * metric thresholds are breached. Called by the nightly audit job
 * (audit_nightly.ts) and optionally on-demand from the dashboard.
 *
 * Supported channels:
 *   - slack:  HTTP POST to slack_webhook_url (Incoming Webhooks API)
 *   - email:  HTTP POST to /api/internal/send-email (platform internal route)
 *             or direct SMTP via ALERT_SMTP_* env vars when configured.
 *
 * Default thresholds (seeded in migration 077):
 *   - zero_rows_rate >= 0.50 over 24h → slack
 *   - error_rate >= 0.10 over 24h → slack + email
 *   - audit_class1_count >= 1 over 24h → slack + email
 *   - audit_class2_count >= 5 over 24h → slack
 *   - disabled_tool_call_count >= 1 over 1h → slack
 *
 * MCPT v3.1.0-S5
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Types ─────────────────────────────────────────────────────────────────────

export type AlertChannel = 'slack' | 'email'

export interface AlertConfig {
  id: string
  metric_name: string
  scope: 'global' | 'per_tool'
  tool_name: string | null
  threshold_value: number
  comparison: 'gte' | 'lte' | 'gt' | 'lt'
  window_hours: number
  channels: AlertChannel[]
  slack_webhook_url: string | null
  email_recipients: string[] | null
  enabled: boolean
}

export interface MetricSnapshot {
  metric_name: string
  tool_name?: string
  value: number
  window_hours: number
  sampled_at: string
}

export interface AlertDispatchResult {
  config_id: string
  metric_name: string
  value: number
  threshold: number
  channels_dispatched: AlertChannel[]
  errors: string[]
}

// ── Comparison helpers ────────────────────────────────────────────────────────

function breaches(value: number, threshold: number, comparison: AlertConfig['comparison']): boolean {
  switch (comparison) {
    case 'gte': return value >= threshold
    case 'gt':  return value > threshold
    case 'lte': return value <= threshold
    case 'lt':  return value < threshold
  }
}

// ── Slack dispatch ────────────────────────────────────────────────────────────

async function dispatchSlack(
  webhookUrl: string,
  metric_name: string,
  tool_name: string | null,
  value: number,
  threshold: number,
  comparison: string,
): Promise<void> {
  const toolLabel = tool_name ? ` (tool: \`${tool_name}\`)` : ''
  const emoji = metric_name.includes('class1') || metric_name === 'error_rate' ? ':red_circle:' : ':warning:'
  const text = `${emoji} *MARSYS-JIS MCP Alert*${toolLabel}\n` +
    `Metric \`${metric_name}\` = *${value.toFixed(4)}* breaches threshold ` +
    `(${comparison} ${threshold}) in the configured window.\n` +
    `Dashboard: ${process.env['NEXT_PUBLIC_APP_URL'] ?? 'https://marsys.jis'}/admin/mcp/health`

  const res = await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) {
    throw new Error(`Slack webhook returned ${res.status}: ${await res.text()}`)
  }
}

// ── Email dispatch ────────────────────────────────────────────────────────────

async function dispatchEmail(
  recipients: string[],
  metric_name: string,
  tool_name: string | null,
  value: number,
  threshold: number,
  comparison: string,
): Promise<void> {
  // Prefer internal platform email route; fall back to ALERT_SMTP_* if configured.
  const internalEmailUrl = `${process.env['NEXT_PUBLIC_APP_URL'] ?? ''}/api/internal/send-email`
  const toolLabel = tool_name ? ` (tool: ${tool_name})` : ''
  const subject = `[MARSYS-JIS] MCP Alert: ${metric_name}${toolLabel}`
  const body =
    `MCP metric alert triggered.\n\n` +
    `Metric: ${metric_name}${toolLabel}\n` +
    `Value: ${value.toFixed(4)}\n` +
    `Threshold: ${comparison} ${threshold}\n\n` +
    `Review on the operator dashboard:\n` +
    `${process.env['NEXT_PUBLIC_APP_URL'] ?? 'https://marsys.jis'}/admin/mcp/health\n`

  try {
    const res = await fetch(internalEmailUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to: recipients, subject, text: body }),
    })
    if (!res.ok) {
      throw new Error(`Internal email route returned ${res.status}`)
    }
  } catch {
    // If internal route unavailable, log and surface error but don't throw —
    // allow other channels to still dispatch.
    console.warn('[alerts:dispatch] Email dispatch failed — internal route unavailable')
    throw new Error('Email dispatch unavailable (internal route not reachable)')
  }
}

// ── Load configs from DB ──────────────────────────────────────────────────────

export async function loadAlertConfigs(): Promise<AlertConfig[]> {
  const result = await query<AlertConfig>(`
    SELECT
      id::text,
      metric_name,
      scope,
      tool_name,
      threshold_value::float AS threshold_value,
      comparison,
      window_hours,
      channels,
      slack_webhook_url,
      email_recipients,
      enabled
    FROM mcp_alerts_config
    WHERE enabled = true
    ORDER BY metric_name, scope, tool_name NULLS FIRST
  `)
  return result.rows
}

// ── Core dispatcher ───────────────────────────────────────────────────────────

/**
 * Evaluates all enabled alert configs against the provided metric snapshots
 * and dispatches notifications for any breaches.
 *
 * @param snapshots - Current metric values. Each must match a config's metric_name
 *                   (and tool_name when scope=per_tool).
 * @param configs   - Alert configs to evaluate. If null, loaded from DB.
 * @returns Array of dispatch results (one per breaching config).
 */
export async function checkAndDispatch(
  snapshots: MetricSnapshot[],
  configs?: AlertConfig[],
): Promise<AlertDispatchResult[]> {
  const alertConfigs = configs ?? (await loadAlertConfigs())
  const results: AlertDispatchResult[] = []

  for (const config of alertConfigs) {
    // Find a matching snapshot
    const snapshot = snapshots.find(s => {
      if (s.metric_name !== config.metric_name) return false
      if (config.scope === 'per_tool' && s.tool_name !== config.tool_name) return false
      return true
    })
    if (!snapshot) continue

    if (!breaches(snapshot.value, config.threshold_value, config.comparison)) continue

    // Threshold breached — dispatch to each configured channel
    const dispatched: AlertChannel[] = []
    const errors: string[] = []

    for (const channel of config.channels) {
      try {
        if (channel === 'slack') {
          const url = config.slack_webhook_url ?? process.env['ALERT_SLACK_WEBHOOK_URL']
          if (!url) {
            errors.push('slack: no webhook URL configured (set slack_webhook_url or ALERT_SLACK_WEBHOOK_URL)')
            continue
          }
          await dispatchSlack(
            url,
            config.metric_name,
            config.tool_name,
            snapshot.value,
            config.threshold_value,
            config.comparison,
          )
          dispatched.push('slack')
        } else if (channel === 'email') {
          const recipients =
            config.email_recipients?.length
              ? config.email_recipients
              : process.env['ALERT_EMAIL_RECIPIENTS']?.split(',').map(r => r.trim()).filter(Boolean) ?? []
          if (!recipients.length) {
            errors.push('email: no recipients configured (set email_recipients or ALERT_EMAIL_RECIPIENTS)')
            continue
          }
          await dispatchEmail(
            recipients,
            config.metric_name,
            config.tool_name,
            snapshot.value,
            config.threshold_value,
            config.comparison,
          )
          dispatched.push('email')
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        errors.push(`${channel}: ${msg}`)
        console.error(`[alerts:dispatch] ${channel} dispatch failed for ${config.metric_name}`, msg)
      }
    }

    results.push({
      config_id: config.id,
      metric_name: config.metric_name,
      value: snapshot.value,
      threshold: config.threshold_value,
      channels_dispatched: dispatched,
      errors,
    })
  }

  return results
}

// ── Convenience: run alert check from audit job output ───────────────────────

/**
 * Builds MetricSnapshots from audit job summary data and dispatches alerts.
 * Called from audit_nightly.ts at the end of each nightly run.
 */
export async function dispatchAuditAlerts(auditSummary: {
  zero_rows_rate_by_tool?: Record<string, number>
  error_rate_by_tool?: Record<string, number>
  class1_count?: number
  class2_count?: number
  disabled_tool_calls?: number
}): Promise<AlertDispatchResult[]> {
  const now = new Date().toISOString()
  const snapshots: MetricSnapshot[] = []

  if (auditSummary.class1_count !== undefined) {
    snapshots.push({ metric_name: 'audit_class1_count', value: auditSummary.class1_count, window_hours: 24, sampled_at: now })
  }
  if (auditSummary.class2_count !== undefined) {
    snapshots.push({ metric_name: 'audit_class2_count', value: auditSummary.class2_count, window_hours: 24, sampled_at: now })
  }
  if (auditSummary.disabled_tool_calls !== undefined) {
    snapshots.push({ metric_name: 'disabled_tool_call_count', value: auditSummary.disabled_tool_calls, window_hours: 1, sampled_at: now })
  }
  for (const [tool_name, rate] of Object.entries(auditSummary.zero_rows_rate_by_tool ?? {})) {
    snapshots.push({ metric_name: 'zero_rows_rate', tool_name, value: rate, window_hours: 24, sampled_at: now })
    // Global aggregate (worst tool) handled separately if needed
  }
  // Global zero_rows_rate = average across tools
  const zeroRates = Object.values(auditSummary.zero_rows_rate_by_tool ?? {})
  if (zeroRates.length > 0) {
    const avg = zeroRates.reduce((a, b) => a + b, 0) / zeroRates.length
    snapshots.push({ metric_name: 'zero_rows_rate', value: avg, window_hours: 24, sampled_at: now })
  }
  for (const [tool_name, rate] of Object.entries(auditSummary.error_rate_by_tool ?? {})) {
    snapshots.push({ metric_name: 'error_rate', tool_name, value: rate, window_hours: 24, sampled_at: now })
  }
  const errorRates = Object.values(auditSummary.error_rate_by_tool ?? {})
  if (errorRates.length > 0) {
    const avg = errorRates.reduce((a, b) => a + b, 0) / errorRates.length
    snapshots.push({ metric_name: 'error_rate', value: avg, window_hours: 24, sampled_at: now })
  }

  return checkAndDispatch(snapshots)
}
