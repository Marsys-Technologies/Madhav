'use client'

// Phase O — O.3 Export — UI panel.
//
// Mounted on the events page (/observatory/events) above the EventExplorer
// as a collapsible "Export data" section. Authored by USTAD_S3_4. OBS-UX-S5
// reskin: charcoal/gold theming, glass surface, lucide icons. All test ids
// preserved (observatory-export-{panel,toggle,form}, export-*).

import * as React from 'react'
import { ChevronRight, Download } from 'lucide-react'

import { buildExportUrl } from '@/lib/api-clients/observatory'
import {
  EXPORT_DEFAULT_LIMIT,
  EXPORT_MAX_LIMIT,
  type ExportFormat,
  type ExportParams,
} from '@/lib/observatory/export/types'

const PROVIDERS = ['anthropic', 'openai', 'gemini', 'deepseek', 'nim'] as const
const STAGES = ['classify', 'compose', 'retrieve', 'synthesize', 'audit'] as const

function isoDate(d: Date): string {
  const yyyy = d.getUTCFullYear().toString().padStart(4, '0')
  const mm = (d.getUTCMonth() + 1).toString().padStart(2, '0')
  const dd = d.getUTCDate().toString().padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function defaultDateRange(): { start: string; end: string } {
  const now = new Date()
  const end = isoDate(now)
  const startMs = now.getTime() - 29 * 24 * 60 * 60 * 1000
  const start = isoDate(new Date(startMs))
  return { start, end }
}

const INPUT_CLS =
  'rounded-md border border-[color-mix(in_oklch,var(--brand-gold)_18%,transparent)] bg-[color-mix(in_oklch,var(--brand-charcoal)_70%,transparent)] px-2 py-1 text-xs text-[var(--brand-gold-cream)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-gold)] focus:border-transparent'

export function ExportPanel(): React.ReactElement {
  const [open, setOpen] = React.useState(false)
  const initial = React.useMemo(defaultDateRange, [])
  const [dateStart, setDateStart] = React.useState(initial.start)
  const [dateEnd, setDateEnd] = React.useState(initial.end)
  const [provider, setProvider] = React.useState('')
  const [pipelineStage, setPipelineStage] = React.useState('')
  const [format, setFormat] = React.useState<ExportFormat>('csv')
  const [limit, setLimit] = React.useState(EXPORT_DEFAULT_LIMIT)
  const [busy, setBusy] = React.useState(false)

  function handleDownload(): void {
    setBusy(true)
    const params: ExportParams = {
      format,
      date_start: dateStart,
      date_end: dateEnd,
      limit,
      provider: provider || undefined,
      pipeline_stage: pipelineStage || undefined,
    }
    const url = buildExportUrl(params)
    window.location.href = url
    window.setTimeout(() => setBusy(false), 500)
  }

  return (
    <section
      data-testid="observatory-export-panel"
      data-open={open ? 'true' : 'false'}
      className="rounded-xl border border-[color-mix(in_oklch,var(--brand-gold)_14%,transparent)] bg-[oklch(0.115_0.012_70)]"
    >
      <button
        type="button"
        data-testid="observatory-export-toggle"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className="group flex w-full items-center justify-between rounded-xl px-4 py-3 text-left transition-colors hover:bg-[color-mix(in_oklch,var(--brand-gold)_5%,transparent)]"
      >
        <span className="flex items-center gap-2">
          <Download size={14} className="text-[var(--brand-gold)] opacity-80" aria-hidden />
          <span className="bt-label bt-label-upper text-[var(--brand-gold-cream)]">Export data</span>
        </span>
        <ChevronRight
          size={14}
          aria-hidden
          className={`text-[rgba(212,175,55,0.55)] transition-transform ${open ? 'rotate-90' : ''}`}
        />
      </button>

      {open ? (
        <div
          data-testid="observatory-export-form"
          className="grid gap-3 border-t border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] px-4 py-4 sm:grid-cols-6 sm:items-end"
        >
          <label className="flex flex-col gap-1 text-xs text-[rgba(212,175,55,0.65)]">
            <span>Date start</span>
            <input
              type="date"
              data-testid="export-date-start"
              value={dateStart}
              onChange={(e) => setDateStart(e.target.value)}
              className={INPUT_CLS}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-[rgba(212,175,55,0.65)]">
            <span>Date end</span>
            <input
              type="date"
              data-testid="export-date-end"
              value={dateEnd}
              onChange={(e) => setDateEnd(e.target.value)}
              className={INPUT_CLS}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-[rgba(212,175,55,0.65)]">
            <span>Provider</span>
            <select
              data-testid="export-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className={INPUT_CLS}
            >
              <option value="">All</option>
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-[rgba(212,175,55,0.65)]">
            <span>Pipeline stage</span>
            <select
              data-testid="export-pipeline-stage"
              value={pipelineStage}
              onChange={(e) => setPipelineStage(e.target.value)}
              className={INPUT_CLS}
            >
              <option value="">All</option>
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <fieldset className="flex flex-col gap-1 text-xs text-[rgba(212,175,55,0.65)]">
            <legend>Format</legend>
            <div data-testid="export-format" className="flex items-center gap-3 text-[var(--brand-gold-cream)]">
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  name="export-format"
                  value="csv"
                  data-testid="export-format-csv"
                  checked={format === 'csv'}
                  onChange={() => setFormat('csv')}
                  className="accent-[var(--brand-gold)]"
                />
                CSV
              </label>
              <label className="flex items-center gap-1">
                <input
                  type="radio"
                  name="export-format"
                  value="json"
                  data-testid="export-format-json"
                  checked={format === 'json'}
                  onChange={() => setFormat('json')}
                  className="accent-[var(--brand-gold)]"
                />
                JSON
              </label>
            </div>
          </fieldset>
          <label className="flex flex-col gap-1 text-xs text-[rgba(212,175,55,0.65)]">
            <span>Limit (max {EXPORT_MAX_LIMIT.toLocaleString()})</span>
            <input
              type="number"
              data-testid="export-limit"
              min={1}
              max={EXPORT_MAX_LIMIT}
              value={limit}
              onChange={(e) => {
                const next = Number(e.target.value)
                if (Number.isFinite(next)) setLimit(next)
              }}
              className={INPUT_CLS}
            />
          </label>
          <div className="sm:col-span-6">
            <button
              type="button"
              data-testid="export-download"
              onClick={handleDownload}
              disabled={busy || !dateStart || !dateEnd}
              className="brand-cta rounded-md px-4 py-2 text-[11px] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? 'Preparing…' : 'Download export'}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  )
}
