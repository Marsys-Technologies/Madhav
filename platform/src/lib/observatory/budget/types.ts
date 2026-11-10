// Phase O — O.3 Budgets — types for the budget-rules framework.
//
// Authored by USTAD_S3_1_BUDGET_RULES_FRAMEWORK. Mirrors the row shape declared
// in `@/lib/db/schema/observatory` (which is itself 1:1 with migration 038's
// `llm_budget_rules` table) so the API surface round-trips cleanly to the DB.
//
// Field-naming note. The S3.1 execution brief specified `threshold_usd` /
// `is_active` for the input shape; the migration-038 columns are `amount_usd`
// / `active`. The DB schema is frozen (`platform/src/lib/db/schema/**`,
// `platform/migrations/**`); this module aligns to the DB column names so
// callers don't pay a translation tax at every boundary. The same goes for
// scope vocabulary: the brief listed `conversation | user | stage | provider |
// global` but the migration's CHECK constraint restricts scope to
// `total | provider | model | pipeline_stage`. The evaluator only emits
// statuses against the four DB-supported scopes — `user` / `conversation`
// budgets are out of v1 scope and would require a migration bump.

import type {
  LlmBudgetPeriod,
  LlmBudgetRuleRow,
  LlmBudgetScope,
} from '../../db/schema/observatory'

// ---------------------------------------------------------------------------
// Shared scalars (re-export the DB-frozen vocabulary so call sites have one
// import path for the budget feature surface).
// ---------------------------------------------------------------------------

export type BudgetScope = LlmBudgetScope
export type BudgetPeriod = LlmBudgetPeriod

/** App-layer view of a single alert threshold inside a budget rule.
 *
 *  This is a superset of the DB-level `LlmBudgetAlertThreshold`: it adds
 *  `channel_target` (the webhook URL when `channel === 'webhook'`; unused
 *  otherwise). The field is optional and additive — the DB layer treats the
 *  whole `alert_thresholds` value as JSONB, so widening the app-layer type is
 *  safe. Authored by USTAD_S3_2_ALERT_DISPATCHER. */
export interface AlertThreshold {
  pct: number
  channel: string
  /** Webhook URL for `channel === 'webhook'`. Unused for `log` / `email`. */
  channel_target?: string
}

/** ok: pct_used is below every alert_threshold.
 *  warning: pct_used is at-or-above the lowest alert_threshold but below the
 *           highest.
 *  alert:   pct_used is at-or-above the highest alert_threshold (and below 100).
 *  exceeded: pct_used >= 100. */
export type BudgetStatus = 'ok' | 'warning' | 'alert' | 'exceeded'

// ---------------------------------------------------------------------------
// API input shape for POST/PATCH.
// ---------------------------------------------------------------------------

export interface BudgetRuleInput {
  name: string
  scope: BudgetScope
  /** Required for non-`total` scopes. The CHECK on the migration does not
   *  enforce this — the API does. */
  scope_value?: string | null
  period: BudgetPeriod
  amount_usd: number
  alert_thresholds: AlertThreshold[]
  active?: boolean
}

// ---------------------------------------------------------------------------
// API output for evaluator
// ---------------------------------------------------------------------------

export interface BudgetEvaluationResult {
  rule_id: string
  name: string
  scope: BudgetScope
  scope_value: string | null
  period: BudgetPeriod
  /** ISO date (YYYY-MM-DD) for the start of the period currently being
   *  evaluated; computed from `period` + `as_of`. */
  period_start: string
  period_end: string
  amount_usd: number
  current_spend_usd: number
  /** current_spend_usd / amount_usd * 100. Clamped to 0 when amount_usd == 0
   *  to avoid division-by-zero — that rule would always be "exceeded" anyway,
   *  which the status field still surfaces. */
  pct_used: number
  status: BudgetStatus
  /** Subset of the rule's alert_thresholds whose `pct` is at or below
   *  `pct_used` — i.e. thresholds that have been crossed. */
  alerts_triggered: AlertThreshold[]
}

export type BudgetRuleRow = LlmBudgetRuleRow
