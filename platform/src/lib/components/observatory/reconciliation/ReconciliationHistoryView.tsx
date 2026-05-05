// Pure presentation: brand header + provider pill tabs + history table +
// (provider-conditional) CSV upload form. Server-renderable; receives the
// loaded rows as a prop so unit tests don't need to hit the DB loader.

import Link from 'next/link'
import { cn } from '@/lib/utils'
import { PROVIDER_COLORS } from '@/lib/components/observatory/charts/utils'
import type { ReconciliationHistoryRow } from '@/lib/observatory/reconciliation/types'
import { StatusChip, providerLabel } from './StatusChip'

const TAB_PROVIDERS = ['anthropic', 'openai', 'gemini', 'deepseek', 'nim'] as const
type TabProvider = (typeof TAB_PROVIDERS)[number]
const MANUAL_UPLOAD_PROVIDERS = new Set<string>(['deepseek', 'nim'])

function fmtUsd(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  })
}

function fmtPeriod(row: ReconciliationHistoryRow): string {
  if (!row.period_end || row.period_end === row.period_start) return row.period_start
  return `${row.period_start} → ${row.period_end}`
}

function fmtDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toISOString().slice(0, 19).replace('T', ' ') + 'Z'
}

function VarianceBadge({ pct }: { pct: number | null | undefined }) {
  if (pct == null || !Number.isFinite(pct)) {
    return <span className="font-mono text-[rgba(212,175,55,0.30)]">—</span>
  }
  const abs = Math.abs(pct)
  let cls: string
  if (abs <= 5) cls = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
  else if (abs <= 15) cls = 'text-amber-400 bg-amber-500/10 border-amber-500/20'
  else cls = 'text-red-400 bg-red-500/10 border-red-500/20'

  const sign = pct > 0 ? '+' : ''
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold tabular-nums',
        cls,
      )}
    >
      {sign}
      {pct.toFixed(2)}%
    </span>
  )
}

export interface ReconciliationHistoryViewProps {
  selectedProvider?: string | null
  rows: ReconciliationHistoryRow[]
  total: number
}

export function ReconciliationHistoryView({
  selectedProvider,
  rows,
  total,
}: ReconciliationHistoryViewProps) {
  const active = selectedProvider ?? null
  const showUpload = active === null || MANUAL_UPLOAD_PROVIDERS.has(active)

  return (
    <section
      data-testid="reconciliation-history-page"
      className="flex flex-col gap-6"
    >
      {/* Deliverable 6 — brand header */}
      <div>
        <h1 className="font-heading text-xl font-semibold text-[#fce29a] tracking-wide">
          Reconciliation
        </h1>
        <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">
          Per-provider cost reconciliation against authoritative billing ·{' '}
          {total} total run{total === 1 ? '' : 's'}
        </p>
      </div>

      {/* Deliverable 2 — pill-style provider tabs */}
      <nav
        data-testid="reconciliation-tabs"
        aria-label="Provider filter"
        className="flex flex-wrap items-center gap-1.5"
      >
        <Link
          href="/observatory/reconciliation"
          data-testid="reconciliation-tab-all"
          aria-current={active === null ? 'page' : undefined}
          className={cn(
            'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
            active === null
              ? 'border-[rgba(212,175,55,0.30)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
              : 'border-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.45)] hover:border-[rgba(212,175,55,0.20)] hover:text-[#d4af37]',
          )}
        >
          All
        </Link>

        {TAB_PROVIDERS.map((p: TabProvider) => {
          const dotColor =
            PROVIDER_COLORS[p as keyof typeof PROVIDER_COLORS] ?? '#64748b'
          const isActiveProv = active === p
          return (
            <Link
              key={p}
              href={`/observatory/reconciliation?provider=${p}`}
              data-testid={`reconciliation-tab-${p}`}
              aria-current={isActiveProv ? 'page' : undefined}
              className={cn(
                'flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
                isActiveProv
                  ? 'border-[rgba(212,175,55,0.30)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
                  : 'border-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.45)] hover:border-[rgba(212,175,55,0.20)] hover:text-[#d4af37]',
              )}
            >
              <span
                aria-hidden="true"
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor: dotColor,
                  opacity: isActiveProv ? 1 : 0.6,
                }}
              />
              {providerLabel(p)}
            </Link>
          )
        })}
      </nav>

      {rows.length === 0 ? (
        /* Deliverable 7 — brand empty state */
        <div
          data-testid="reconciliation-empty"
          className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-[rgba(212,175,55,0.15)] py-16 text-center"
        >
          <span className="text-3xl opacity-20">⚖</span>
          <p className="text-sm font-medium text-[rgba(212,175,55,0.45)]">
            No reconciliation runs yet
          </p>
          <p className="text-xs text-[rgba(212,175,55,0.30)]">
            Trigger a reconciliation from the API, or upload a CSV below for DeepSeek / NIM
          </p>
        </div>
      ) : (
        /* Deliverable 3 — brand-styled table */
        <div
          data-testid="reconciliation-table-wrapper"
          className="overflow-x-auto rounded-xl border border-[rgba(212,175,55,0.10)]"
        >
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[rgba(212,175,55,0.10)]">
                {['Date', 'Provider', 'Period', 'Status', 'Authoritative', 'Computed', 'Variance %'].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.reconciliation_id}
                  data-testid={`reconciliation-row-${row.reconciliation_id}`}
                  className="border-b border-[rgba(212,175,55,0.06)] transition-colors hover:bg-[rgba(212,175,55,0.03)]"
                >
                  <td className="px-4 py-3 font-mono text-[10px] text-[rgba(212,175,55,0.50)]">
                    {fmtDate(row.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-2">
                      <span
                        aria-hidden="true"
                        className="h-2 w-2 rounded-full shrink-0"
                        style={{
                          backgroundColor:
                            PROVIDER_COLORS[
                              row.provider as keyof typeof PROVIDER_COLORS
                            ] ?? '#64748b',
                        }}
                      />
                      <span className="text-xs text-[rgba(212,175,55,0.70)] capitalize">
                        {providerLabel(row.provider)}
                      </span>
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-[10px] text-[rgba(212,175,55,0.50)]">
                    {fmtPeriod(row)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusChip
                      provider={row.provider}
                      status={row.status}
                      variancePct={row.variance_pct}
                    />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-[rgba(212,175,55,0.70)]">
                    {fmtUsd(row.authoritative_cost_usd)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-[rgba(212,175,55,0.70)]">
                    {fmtUsd(row.computed_cost_usd)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <VarianceBadge pct={row.variance_pct} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Deliverable 5 — brand CSV upload form */}
      {showUpload && (
        <section className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-5">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-[#fce29a]">
              Manual reconciliation upload
            </h2>
            <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.40)]">
              DeepSeek and NIM don't expose billing APIs. Upload the invoice CSV for the period.
            </p>
          </div>

          <form
            data-testid="reconciliation-upload-form"
            action="/api/admin/observatory/reconciliation/upload"
            method="POST"
            encType="multipart/form-data"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
          >
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
                Provider
              </label>
              <select
                name="provider"
                defaultValue={
                  active && MANUAL_UPLOAD_PROVIDERS.has(active) ? active : 'deepseek'
                }
                data-testid="reconciliation-upload-provider"
                className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
              >
                <option value="deepseek">DeepSeek</option>
                <option value="nim">NIM</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
                Period start
              </label>
              <input
                type="date"
                name="period_start"
                required
                data-testid="reconciliation-upload-period-start"
                className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
                Period end
              </label>
              <input
                type="date"
                name="period_end"
                required
                data-testid="reconciliation-upload-period-end"
                className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
                CSV file
              </label>
              <input
                type="file"
                name="file"
                accept=".csv,text/csv"
                required
                data-testid="reconciliation-upload-file"
                className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.55)] file:mr-3 file:rounded file:border-0 file:bg-[rgba(212,175,55,0.12)] file:px-2 file:py-1 file:text-xs file:font-medium file:text-[#d4af37]"
              />
            </div>

            <div className="sm:col-span-2 lg:col-span-4">
              <button
                type="submit"
                data-testid="reconciliation-upload-submit"
                className="rounded-lg bg-gradient-to-r from-[#d4af37] to-[#fce29a] px-5 py-2 text-xs font-semibold text-[oklch(0.10_0.012_70)] transition-opacity hover:opacity-90"
              >
                Upload &amp; reconcile
              </button>
            </div>
          </form>
        </section>
      )}
    </section>
  )
}
