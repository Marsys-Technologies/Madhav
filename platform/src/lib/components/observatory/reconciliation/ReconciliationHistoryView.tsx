// Pure presentation: provider pill tabs + history table + (provider-conditional)
// CSV upload drop zone. Server-renderable; receives the loaded rows as a prop
// so unit tests don't need to hit the DB loader.
// OBS-UX-S5: glass tabs, semantic-token status colors, drop zone styling. The
// brand header is now provided by ObsPageShell at the page level.

import Link from 'next/link'
import { UploadCloud } from 'lucide-react'
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
  if (abs <= 5)
    cls =
      'text-[var(--status-success)] bg-[var(--status-success-bg)] border-[color-mix(in_oklch,var(--status-success)_25%,transparent)]'
  else if (abs <= 15)
    cls =
      'text-[var(--status-warn)] bg-[var(--status-warn-bg)] border-[color-mix(in_oklch,var(--status-warn)_25%,transparent)]'
  else
    cls =
      'text-[var(--status-halt)] bg-[var(--status-halt-bg)] border-[color-mix(in_oklch,var(--status-halt)_25%,transparent)]'

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

const TAB_BASE =
  'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors'

const TAB_ACTIVE =
  'obs-glass text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_color-mix(in_oklch,var(--brand-gold)_30%,transparent)]'

const TAB_IDLE =
  'text-[rgba(212,175,55,0.50)] hover:bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)] hover:text-[var(--brand-gold)]'

const FORM_INPUT =
  'rounded-lg border border-[color-mix(in_oklch,var(--brand-gold)_18%,transparent)] bg-[color-mix(in_oklch,var(--brand-charcoal)_70%,transparent)] px-3 py-2 text-sm text-[var(--brand-gold-cream)] focus:border-[var(--brand-gold)] focus:outline-none focus:ring-2 focus:ring-[color-mix(in_oklch,var(--brand-gold)_30%,transparent)]'

export interface ReconciliationHistoryViewProps {
  selectedProvider?: string | null
  rows: ReconciliationHistoryRow[]
  total: number
}

export function ReconciliationHistoryView({
  selectedProvider,
  rows,
}: ReconciliationHistoryViewProps) {
  const active = selectedProvider ?? null
  const showUpload = active === null || MANUAL_UPLOAD_PROVIDERS.has(active)

  return (
    <section
      data-testid="reconciliation-history-page"
      className="flex flex-col gap-6"
    >
      {/* Pill provider tabs */}
      <nav
        data-testid="reconciliation-tabs"
        aria-label="Provider filter"
        className="flex flex-wrap items-center gap-1.5"
      >
        <Link
          href="/observatory/reconciliation"
          data-testid="reconciliation-tab-all"
          aria-current={active === null ? 'page' : undefined}
          className={cn(TAB_BASE, active === null ? TAB_ACTIVE : TAB_IDLE)}
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
              className={cn(TAB_BASE, isActiveProv ? TAB_ACTIVE : TAB_IDLE)}
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
        <div
          data-testid="reconciliation-empty"
          className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-[color-mix(in_oklch,var(--brand-gold)_18%,transparent)] bg-[oklch(0.115_0.012_70)] py-16 text-center"
        >
          <span className="text-3xl text-[var(--brand-gold)] opacity-30">⚖</span>
          <p className="text-sm font-medium text-[rgba(212,175,55,0.50)]">
            No reconciliation runs yet
          </p>
          <p className="text-xs text-[rgba(212,175,55,0.35)]">
            Trigger a reconciliation from the API, or upload a CSV below for DeepSeek / NIM
          </p>
        </div>
      ) : (
        <div
          data-testid="reconciliation-table-wrapper"
          className="overflow-x-auto rounded-xl border border-[color-mix(in_oklch,var(--brand-gold)_12%,transparent)] bg-[oklch(0.115_0.012_70)]"
        >
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)]">
                {['Date', 'Provider', 'Period', 'Status', 'Authoritative', 'Computed', 'Variance %'].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left bt-label bt-label-upper text-[rgba(212,175,55,0.45)]"
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
                  className="border-b border-[color-mix(in_oklch,var(--brand-gold)_5%,transparent)] transition-colors hover:bg-[color-mix(in_oklch,var(--brand-gold)_4%,transparent)]"
                >
                  <td className="px-4 py-3 font-mono text-[10px] text-[rgba(212,175,55,0.55)]">
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
                      <span className="text-xs text-[var(--brand-gold-cream)] capitalize">
                        {providerLabel(row.provider)}
                      </span>
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-[10px] text-[rgba(212,175,55,0.55)]">
                    {fmtPeriod(row)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusChip
                      provider={row.provider}
                      status={row.status}
                      variancePct={row.variance_pct}
                    />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-[var(--brand-gold-cream)]">
                    {fmtUsd(row.authoritative_cost_usd)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-[var(--brand-gold-cream)]">
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

      {showUpload && (
        <section className="rounded-xl border border-dashed border-[color-mix(in_oklch,var(--brand-gold)_22%,transparent)] bg-[oklch(0.115_0.012_70)] p-6">
          <div className="mb-5 flex items-start gap-3">
            <UploadCloud
              size={20}
              aria-hidden
              className="mt-0.5 text-[var(--brand-gold)] opacity-80"
            />
            <div>
              <h2 className="bt-heading text-[var(--brand-gold-cream)]">
                Manual reconciliation upload
              </h2>
              <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.50)]">
                DeepSeek and NIM don&apos;t expose billing APIs. Upload the invoice CSV for the period.
              </p>
            </div>
          </div>

          <form
            data-testid="reconciliation-upload-form"
            action="/api/admin/observatory/reconciliation/upload"
            method="POST"
            encType="multipart/form-data"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
          >
            <div className="flex flex-col gap-1.5">
              <label className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">
                Provider
              </label>
              <select
                name="provider"
                defaultValue={
                  active && MANUAL_UPLOAD_PROVIDERS.has(active) ? active : 'deepseek'
                }
                data-testid="reconciliation-upload-provider"
                className={FORM_INPUT}
              >
                <option value="deepseek">DeepSeek</option>
                <option value="nim">NIM</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">
                Period start
              </label>
              <input
                type="date"
                name="period_start"
                required
                data-testid="reconciliation-upload-period-start"
                className={FORM_INPUT}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">
                Period end
              </label>
              <input
                type="date"
                name="period_end"
                required
                data-testid="reconciliation-upload-period-end"
                className={FORM_INPUT}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">
                CSV file
              </label>
              <input
                type="file"
                name="file"
                accept=".csv,text/csv"
                required
                data-testid="reconciliation-upload-file"
                className={cn(
                  FORM_INPUT,
                  'file:mr-3 file:rounded file:border-0 file:bg-[color-mix(in_oklch,var(--brand-gold)_15%,transparent)] file:px-2 file:py-1 file:text-xs file:font-medium file:text-[var(--brand-gold)]',
                )}
              />
            </div>

            <div className="sm:col-span-2 lg:col-span-4">
              <button
                type="submit"
                data-testid="reconciliation-upload-submit"
                className="brand-cta rounded-lg px-5 py-2 text-xs"
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
