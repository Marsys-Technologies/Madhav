'use client'

// New-budget-rule form. Scope vocabulary aligns to the migration-038 DB CHECK
// (total | provider | model | pipeline_stage) — the S3.3 brief listed the
// older `global | stage | user | conversation` set but the S3.1 types.ts
// already noted user/conversation are out of v1 scope until a migration bump.
// "Global" is the friendly label for `total`.

import { useState, type FormEvent } from 'react'

import { createBudgetRule } from '@/lib/api-clients/observatory'
import {
  PIPELINE_STAGE_OPTIONS,
  PROVIDER_OPTIONS,
} from '@/lib/components/observatory/filters/types'
import type {
  AlertThreshold,
  BudgetPeriod,
  BudgetRuleInput,
  BudgetScope,
} from '@/lib/observatory/budget/types'

const SCOPES: ReadonlyArray<{ value: BudgetScope; label: string }> = [
  { value: 'total', label: 'Global (total)' },
  { value: 'provider', label: 'Provider' },
  { value: 'pipeline_stage', label: 'Pipeline stage' },
  { value: 'model', label: 'Model' },
]

const PERIODS: ReadonlyArray<BudgetPeriod> = ['daily', 'weekly', 'monthly']

const CHANNELS = ['log', 'webhook', 'email'] as const
type Channel = (typeof CHANNELS)[number]

interface ThresholdRow {
  pct: number
  channel: Channel
  /** Local-only: webhook URL. Not submitted until backend supports it. */
  channel_target: string
}

const DEFAULT_THRESHOLDS: ThresholdRow[] = [
  { pct: 80, channel: 'log', channel_target: '' },
  { pct: 95, channel: 'email', channel_target: '' },
]

const INPUT_CLASS =
  'rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] placeholder:text-[rgba(212,175,55,0.25)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none'

export interface CreateBudgetRuleFormProps {
  onCreated: () => void
}

export function CreateBudgetRuleForm({ onCreated }: CreateBudgetRuleFormProps) {
  const [name, setName] = useState('')
  const [scope, setScope] = useState<BudgetScope>('total')
  const [scopeValue, setScopeValue] = useState('')
  const [period, setPeriod] = useState<BudgetPeriod>('monthly')
  const [amount, setAmount] = useState<number>(100)
  const [thresholds, setThresholds] = useState<ThresholdRow[]>(DEFAULT_THRESHOLDS)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function reset() {
    setName('')
    setScope('total')
    setScopeValue('')
    setPeriod('monthly')
    setAmount(100)
    setThresholds(DEFAULT_THRESHOLDS)
    setError(null)
  }

  function updateThreshold(idx: number, patch: Partial<ThresholdRow>) {
    setThresholds((prev) =>
      prev.map((row, i) => (i === idx ? { ...row, ...patch } : row)),
    )
  }

  function addThreshold() {
    if (thresholds.length >= 3) return
    setThresholds((prev) => [
      ...prev,
      { pct: 100, channel: 'log', channel_target: '' },
    ])
  }

  function removeThreshold(idx: number) {
    setThresholds((prev) => prev.filter((_, i) => i !== idx))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload: BudgetRuleInput = {
        name: name.trim() || `${scope} ${period} budget`,
        scope,
        scope_value: scope === 'total' ? null : scopeValue.trim() || null,
        period,
        amount_usd: amount,
        alert_thresholds: thresholds.map<AlertThreshold>((t) => ({
          pct: t.pct,
          channel: t.channel,
        })),
        active: true,
      }
      await createBudgetRule(payload)
      reset()
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create rule')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-6">
      <div className="mb-5">
        <h2 className="text-sm font-semibold text-[#fce29a]">Create budget rule</h2>
        <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.40)]">
          Set a spend limit and alert thresholds for a scope and period.
        </p>
      </div>

      <form
        data-testid="create-budget-rule-form"
        onSubmit={handleSubmit}
        className="space-y-5"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label
              htmlFor="budget-rule-name"
              className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]"
            >
              Name
            </label>
            <input
              id="budget-rule-name"
              data-testid="create-budget-rule-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Monthly Anthropic cap"
              className={INPUT_CLASS}
            />
          </div>

          <div className="flex flex-col gap-1">
            <label
              htmlFor="budget-rule-scope"
              className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]"
            >
              Scope
            </label>
            <select
              id="budget-rule-scope"
              data-testid="create-budget-rule-scope"
              value={scope}
              onChange={(e) => {
                setScope(e.target.value as BudgetScope)
                setScopeValue('')
              }}
              className={INPUT_CLASS}
            >
              {SCOPES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {scope !== 'total' && (
            <div className="flex flex-col gap-1">
              <label
                htmlFor="budget-rule-scope-value"
                className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]"
              >
                Scope value
              </label>
              {scope === 'provider' ? (
                <select
                  id="budget-rule-scope-value"
                  data-testid="create-budget-rule-scope-value"
                  data-scope-value-type="provider"
                  value={scopeValue}
                  onChange={(e) => setScopeValue(e.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="">Select provider…</option>
                  {PROVIDER_OPTIONS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              ) : scope === 'pipeline_stage' ? (
                <select
                  id="budget-rule-scope-value"
                  data-testid="create-budget-rule-scope-value"
                  data-scope-value-type="pipeline_stage"
                  value={scopeValue}
                  onChange={(e) => setScopeValue(e.target.value)}
                  className={INPUT_CLASS}
                >
                  <option value="">Select stage…</option>
                  {PIPELINE_STAGE_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  id="budget-rule-scope-value"
                  data-testid="create-budget-rule-scope-value"
                  data-scope-value-type="text"
                  type="text"
                  value={scopeValue}
                  onChange={(e) => setScopeValue(e.target.value)}
                  placeholder={scope === 'model' ? 'e.g. claude-sonnet-4-6' : ''}
                  className={INPUT_CLASS}
                />
              )}
            </div>
          )}

          <div className="flex flex-col gap-1">
            <label
              htmlFor="budget-rule-period"
              className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]"
            >
              Period
            </label>
            <select
              id="budget-rule-period"
              data-testid="create-budget-rule-period"
              value={period}
              onChange={(e) => setPeriod(e.target.value as BudgetPeriod)}
              className={INPUT_CLASS}
            >
              {PERIODS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label
              htmlFor="budget-rule-amount"
              className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]"
            >
              Threshold (USD)
            </label>
            <input
              id="budget-rule-amount"
              data-testid="create-budget-rule-amount"
              type="number"
              min={0.01}
              step={0.01}
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className={`${INPUT_CLASS} tabular-nums`}
            />
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
            Alert thresholds
          </p>
          {thresholds.map((row, idx) => (
            <div
              key={idx}
              data-testid={`create-budget-rule-threshold-${idx}`}
              className="flex flex-wrap items-center gap-2"
            >
              <input
                data-testid={`create-budget-rule-threshold-pct-${idx}`}
                type="number"
                min={0}
                max={200}
                step={1}
                value={row.pct}
                onChange={(e) =>
                  updateThreshold(idx, { pct: Number(e.target.value) })
                }
                className={`${INPUT_CLASS} w-20 tabular-nums`}
              />
              <span className="text-xs text-[rgba(212,175,55,0.40)]">%</span>
              <select
                data-testid={`create-budget-rule-threshold-channel-${idx}`}
                value={row.channel}
                onChange={(e) =>
                  updateThreshold(idx, { channel: e.target.value as Channel })
                }
                className={INPUT_CLASS}
              >
                {CHANNELS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              {row.channel === 'webhook' && (
                <input
                  data-testid={`create-budget-rule-threshold-url-${idx}`}
                  type="url"
                  value={row.channel_target}
                  onChange={(e) =>
                    updateThreshold(idx, { channel_target: e.target.value })
                  }
                  placeholder="https://example.com/hook"
                  className={`${INPUT_CLASS} min-w-[14rem] flex-1`}
                />
              )}
              {thresholds.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeThreshold(idx)}
                  className="rounded-lg border border-[rgba(212,175,55,0.12)] px-2.5 py-1 text-xs text-[rgba(212,175,55,0.40)] transition-colors hover:border-red-500/30 hover:text-red-400"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            data-testid="create-budget-rule-add-threshold"
            onClick={addThreshold}
            disabled={thresholds.length >= 3}
            className="rounded-lg border border-dashed border-[rgba(212,175,55,0.20)] px-3 py-1.5 text-xs text-[rgba(212,175,55,0.40)] transition-colors hover:border-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.70)] disabled:opacity-40"
          >
            + Add alert threshold
          </button>
        </div>

        {error && (
          <div role="alert" className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-400">
            {error}
          </div>
        )}

        <div>
          <button
            type="submit"
            data-testid="create-budget-rule-submit"
            disabled={submitting}
            className="rounded-lg bg-gradient-to-r from-[#d4af37] to-[#fce29a] px-5 py-2 text-xs font-semibold text-[oklch(0.10_0.012_70)] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create rule'}
          </button>
        </div>
      </form>
    </section>
  )
}
