/**
 * observability/budget_guard.ts — Cloud Billing budget alert handler +
 * kill-switch hook.
 *
 * Cloud Billing posts budget notifications to a Pub/Sub topic in JSON form:
 *
 *   {
 *     "budgetDisplayName": "marsys-monthly-cap",
 *     "alertThresholdExceeded": 0.8,           // 0.5 / 0.8 / 1.0 / 1.2 ...
 *     "costAmount": 412.55,
 *     "costIntervalStart": "2026-05-01T00:00:00Z",
 *     "budgetAmount": 500.00,
 *     "budgetAmountType": "SPECIFIED_AMOUNT",
 *     "currencyCode": "USD"
 *   }
 *
 * A Cloud Function (or Cloud Run handler) subscribes to that topic and calls
 * `handleBudgetAlert(payload)` below. Two effects:
 *
 *   1. At or above the kill-switch threshold (default 1.0 = 100% of budget),
 *      we flip the gate `BUDGET_KILL_SWITCH_ENABLED=true` via the same
 *      configService.setGate() substrate used by the cockpit. Application
 *      code consults this gate before invoking any paid LLM / Vertex call.
 *
 *   2. We always write a `gate_status` row recording the budget breach
 *      with the alert payload, so the operator dashboard surfaces it and the
 *      audit trail is preserved (matches the brief: "writes a gate_status
 *      row on fire").
 *
 * Stream B / unit 4.observability (Wave 4 platform-modernization).
 */

import 'server-only'
import { query } from '@/lib/db/client'
import { setGate } from '@/lib/config/configService'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BudgetAlertPayload {
  budgetDisplayName: string
  alertThresholdExceeded: number // ratio: 0.5, 0.8, 1.0, 1.2, ...
  costAmount: number
  budgetAmount: number
  currencyCode: string
  costIntervalStart?: string
}

export interface BudgetGuardResult {
  killSwitchFlipped: boolean
  gateStatusRowId: string
  thresholdRatio: number
  reason: string
}

// ── Config ────────────────────────────────────────────────────────────────────

/** Above this ratio (default 1.0 = 100% of budget) we flip the kill-switch. */
const DEFAULT_KILL_THRESHOLD = 1.0

/** Principal used when budget alerts auto-flip the gate. */
const BUDGET_GUARD_PRINCIPAL = 'system:budget-guard'

/** Gate flipped when the kill threshold is breached. */
export const BUDGET_KILL_SWITCH_GATE = 'BUDGET_KILL_SWITCH_ENABLED'

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Process an incoming Cloud Billing budget alert payload.
 *
 * Always writes a gate_status row. Flips the kill-switch gate when the alert
 * threshold meets/exceeds the configured kill threshold.
 */
export async function handleBudgetAlert(
  payload: BudgetAlertPayload,
  opts: { killThreshold?: number } = {},
): Promise<BudgetGuardResult> {
  const killThreshold = opts.killThreshold ?? DEFAULT_KILL_THRESHOLD
  const breach = payload.alertThresholdExceeded >= killThreshold

  const reason =
    `budget=${payload.budgetDisplayName} ` +
    `threshold=${(payload.alertThresholdExceeded * 100).toFixed(0)}% ` +
    `cost=${payload.costAmount.toFixed(2)}${payload.currencyCode} / ` +
    `${payload.budgetAmount.toFixed(2)}${payload.currencyCode}`

  // Write gate_status row first so the audit trail is preserved even if the
  // gate flip throws.
  const result = await query<{ id: string }>(
    `INSERT INTO gate_status (event_type, gate_key, payload, reason, created_at)
     VALUES ('budget_alert', $1, $2::jsonb, $3, now())
     RETURNING id::text`,
    [BUDGET_KILL_SWITCH_GATE, JSON.stringify(payload), reason],
  )
  const gateStatusRowId = result.rows[0]?.id ?? ''

  let killSwitchFlipped = false
  if (breach) {
    try {
      await setGate(BUDGET_KILL_SWITCH_GATE, true, BUDGET_GUARD_PRINCIPAL, {
        reason: `budget kill-switch — ${reason}`,
      })
      killSwitchFlipped = true
    } catch (err) {
      // If the gate doesn't exist in the spec yet, log + continue — the
      // gate_status row is still durable and operator can flip manually.
      const msg = err instanceof Error ? err.message : String(err)
      // eslint-disable-next-line no-console
      console.error('[budget_guard] setGate failed (gate may be unregistered):', msg)
    }
  }

  return {
    killSwitchFlipped,
    gateStatusRowId,
    thresholdRatio: payload.alertThresholdExceeded,
    reason,
  }
}

/**
 * Returns true when the kill-switch is engaged. Application code calls this
 * before any paid LLM / Vertex call; on `true`, short-circuit and surface a
 * 503 with a "budget-cap engaged" message.
 *
 * Tolerant of a missing gate spec — returns false (i.e. "allow") when the
 * gate hasn't been registered yet, so introducing this guard before the
 * gate ships is safe.
 */
export async function isBudgetKillSwitchEngaged(): Promise<boolean> {
  // Dynamic import to avoid a circular-import risk during testing.
  const cfg = await import('@/lib/config/configService')
  try {
    const v = await cfg.getGate(BUDGET_KILL_SWITCH_GATE)
    return v === true
  } catch {
    return false
  }
}
