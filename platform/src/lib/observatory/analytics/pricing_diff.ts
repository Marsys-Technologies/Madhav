// Phase O — O.4 Analytics — pricing diff alerter.
//
// Authored by USTAD_S4_4_PRICING_DIFF. Monitors the health of the per-provider
// pricing model and surfaces two failure modes:
//
//   (A) STALE_PRICING — the latest llm_pricing_versions row for a provider
//       is older than STALE_PRICING_THRESHOLD_DAYS. Real provider prices drift;
//       a stale table accrues silent variance.
//
//   (B) SYSTEMATIC_VARIANCE — the rolling 7-day mean ABS(variance_pct) from
//       llm_cost_reconciliation exceeds SYSTEMATIC_VARIANCE_THRESHOLD_PCT for
//       a provider. The pricing model is wrong for that provider.
//
// Discipline:
//   - Both checks run in SQL with bound parameters; one query per check, both
//     grouped by provider.
//   - Alert dispatch is direct (no budget rule framework round-trip): if
//     OBSERVATORY_ALERT_WEBHOOK_URL is set, POST with a 5s timeout; otherwise
//     console.warn. Webhook failures are swallowed (never throw) — the
//     console.warn always fires regardless.
//   - QueryFn injection mirrors `budget/evaluate.ts` so tests can swap the
//     pg pool for a vi.fn().

import 'server-only'
import { query } from '../../db/client'

export const STALE_PRICING_THRESHOLD_DAYS = 30
export const SYSTEMATIC_VARIANCE_THRESHOLD_PCT = 5.0
const WEBHOOK_TIMEOUT_MS = 5_000

export type PricingHealthStatus =
  | 'ok'
  | 'stale_pricing'
  | 'systematic_variance'
  | 'both'

export type PricingWebhookResult =
  | 'not_attempted'
  | 'not_configured'
  | 'http_accepted'
  | 'http_error'
  | 'unknown'

export interface ProviderPricingHealth {
  provider: string
  last_pricing_update: string | null
  pricing_age_days: number
  is_pricing_stale: boolean
  avg_7d_variance_pct: number | null
  has_systematic_variance: boolean
  status: PricingHealthStatus
  alert_fired: boolean
  /** HTTP 2xx indicates transport acceptance only. */
  alert_webhook_result?: PricingWebhookResult
}

export interface PricingDiffResult {
  checked_at: string
  providers: ProviderPricingHealth[]
  stale_count: number
  variance_alert_count: number
  all_healthy: boolean
}

interface QueryFn {
  <R = unknown>(sql: string, params?: unknown[]): Promise<{ rows: R[] }>
}

interface PricingFreshnessRow {
  provider: string
  last_pricing_update: string | null
}

interface VarianceRow {
  provider: string
  avg_abs_variance_pct: number | null
}

function classify(
  isStale: boolean,
  hasVariance: boolean,
): PricingHealthStatus {
  if (isStale && hasVariance) return 'both'
  if (isStale) return 'stale_pricing'
  if (hasVariance) return 'systematic_variance'
  return 'ok'
}

function ageDays(latestIso: string | null, nowMs: number): number {
  if (!latestIso) return Number.POSITIVE_INFINITY
  const t = Date.parse(latestIso)
  if (!Number.isFinite(t)) return Number.POSITIVE_INFINITY
  return Math.floor((nowMs - t) / 86_400_000)
}

async function dispatchPricingAlert(
  provider: string,
  status: PricingHealthStatus,
  detail: ProviderPricingHealth,
): Promise<PricingWebhookResult> {
  console.warn(
    `[PricingDiffAlert] provider=${provider} status=${status} ` +
      `pricing_age_days=${
        Number.isFinite(detail.pricing_age_days)
          ? detail.pricing_age_days
          : 'inf'
      } ` +
      `avg_7d_variance_pct=${detail.avg_7d_variance_pct ?? 'null'}`,
  )
  const target = process.env.OBSERVATORY_ALERT_WEBHOOK_URL
  if (!target) return 'not_configured'
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), WEBHOOK_TIMEOUT_MS)
  try {
    const response = await fetch(target, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, status, detail }),
      signal: controller.signal,
    })
    return response.ok ? 'http_accepted' : 'http_error'
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.warn(
      `[PricingDiffAlert] webhook dispatch failed for provider=${provider}: ${message}`,
    )
    return 'unknown'
  } finally {
    clearTimeout(timeout)
  }
}

export async function checkPricingHealth(
  queryFn: QueryFn = query as QueryFn,
): Promise<PricingDiffResult> {
  const checkedAt = new Date()
  const checkedAtIso = checkedAt.toISOString()
  const nowMs = checkedAt.getTime()

  // Per-provider freshness: newest effective_from in llm_pricing_versions.
  const freshnessSql =
    'SELECT provider, MAX(effective_from)::text AS last_pricing_update' +
    ' FROM llm_pricing_versions' +
    ' GROUP BY provider'
  const freshnessRes = await queryFn<PricingFreshnessRow>(freshnessSql)

  // Per-provider 7-day mean ABS(variance_pct) from llm_cost_reconciliation.
  const varianceSql =
    'SELECT provider, AVG(ABS(variance_pct)) AS avg_abs_variance_pct' +
    ' FROM llm_cost_reconciliation' +
    " WHERE reconciliation_date >= (NOW() - INTERVAL '7 days')::date" +
    '   AND variance_pct IS NOT NULL' +
    ' GROUP BY provider'
  const varianceRes = await queryFn<VarianceRow>(varianceSql)

  const varianceMap = new Map<string, number | null>()
  for (const row of varianceRes.rows) {
    const v =
      row.avg_abs_variance_pct === null || row.avg_abs_variance_pct === undefined
        ? null
        : Number(row.avg_abs_variance_pct)
    varianceMap.set(row.provider, v)
  }

  // Union of providers across both queries — variance-only providers (no
  // pricing rows at all) are included with last_pricing_update=null.
  const providerSet = new Set<string>()
  for (const r of freshnessRes.rows) providerSet.add(r.provider)
  for (const r of varianceRes.rows) providerSet.add(r.provider)
  const freshnessMap = new Map(
    freshnessRes.rows.map((r) => [r.provider, r.last_pricing_update]),
  )

  const providers: ProviderPricingHealth[] = []
  for (const provider of Array.from(providerSet).sort()) {
    const lastUpdate = freshnessMap.get(provider) ?? null
    const age = ageDays(lastUpdate, nowMs)
    const isStale = age > STALE_PRICING_THRESHOLD_DAYS
    const avgVariance = varianceMap.has(provider)
      ? varianceMap.get(provider) ?? null
      : null
    const hasVariance =
      avgVariance !== null && avgVariance > SYSTEMATIC_VARIANCE_THRESHOLD_PCT
    const status = classify(isStale, hasVariance)

    const health: ProviderPricingHealth = {
      provider,
      last_pricing_update: lastUpdate,
      pricing_age_days: Number.isFinite(age) ? age : Number.MAX_SAFE_INTEGER,
      is_pricing_stale: isStale,
      avg_7d_variance_pct: avgVariance,
      has_systematic_variance: hasVariance,
      status,
      alert_fired: false,
    }

    let webhookResult: PricingWebhookResult = 'not_attempted'
    if (status !== 'ok') {
      webhookResult = 'unknown'
      try {
        webhookResult = await dispatchPricingAlert(provider, status, health)
      } catch {
        // Keep health reporting available if alerting itself fails.
      }
      health.alert_fired = true
    }

    health.alert_webhook_result = webhookResult
    providers.push(health)
  }

  let staleCount = 0
  let varianceAlertCount = 0
  for (const p of providers) {
    if (p.is_pricing_stale) staleCount += 1
    if (p.has_systematic_variance) varianceAlertCount += 1
  }

  return {
    checked_at: checkedAtIso,
    providers,
    stale_count: staleCount,
    variance_alert_count: varianceAlertCount,
    all_healthy: providers.every((p) => p.status === 'ok'),
  }
}
