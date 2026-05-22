'use client'
/**
 * PredictionsCalibration — Dashboard Tab 4 (Track B — v3.4-S1)
 *
 * Renders the calibration grid from mv_calibration_score:
 *   - Per (confidence_band × domain × horizon_bucket) cell: N, realized rate,
 *     Wilson 95% CI, discrepancy flag.
 *   - Colour-codes cells: green (within CI of band midpoint), amber (borderline),
 *     red (discrepancy | N ≥ 10 and |realized - midpoint| > 0.15).
 *   - Empty state: no predictions logged yet (normal at v3.1 start).
 *   - Refresh button triggers Cloud Scheduler nightly job on demand.
 *
 * Data source: GET /api/admin/mcp/health/calibration
 * Replaces v3.1.0-S5 placeholder (see brief §5).
 */

import { useQuery } from '@tanstack/react-query'
import type { CalibrationRow } from '@/lib/perf/mv_refresh'

// ── API shape ─────────────────────────────────────────────────────────────────

interface CalibrationApiResponse {
  rows: CalibrationRow[]
  refreshed_at: string | null
  grounding_pct: number | null
}

async function fetchCalibration(): Promise<CalibrationApiResponse> {
  const res = await fetch('/api/admin/mcp/health/calibration', { cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ── Confidence-band midpoints (per perf brief §9) ─────────────────────────────

const BAND_MIDPOINT: Record<string, number> = {
  high:   0.70,
  medium: 0.50,
  low:    0.30,
}

const BAND_ORDER = ['high', 'medium', 'low']
const HORIZON_ORDER = ['<=30d', '31-180d', '181-730d', '>730d']

// ── Helpers ───────────────────────────────────────────────────────────────────

function discrepancyClass(row: CalibrationRow): string {
  const n = row.realized + row.disconfirmed
  if (n < 10 || row.realized_rate === null) return ''
  const mid = BAND_MIDPOINT[row.confidence_band] ?? 0.50
  const diff = Math.abs(row.realized_rate - mid)
  if (diff > 0.20) return 'bg-red-50 border-red-300 text-red-800'
  if (diff > 0.10) return 'bg-amber-50 border-amber-300 text-amber-800'
  return 'bg-green-50 border-green-300 text-green-800'
}

function pct(v: number | null): string {
  if (v === null || v === undefined) return '—'
  return `${(v * 100).toFixed(0)}%`
}

function ciStr(low: number | null, high: number | null): string {
  if (low === null || high === null) return '—'
  return `[${pct(low)}, ${pct(high)}]`
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border p-10 text-center">
      <p className="text-sm text-muted-foreground">No predictions logged yet.</p>
      <p className="mt-1 text-xs text-muted-foreground">
        Calibration data accumulates as predictions are logged via{' '}
        <code className="font-mono">log_prediction</code> and outcomes are recorded
        via <code className="font-mono">record_outcome</code>.
      </p>
    </div>
  )
}

// ── Cell component ────────────────────────────────────────────────────────────

function CalibrationCell({ row }: { row: CalibrationRow | undefined }) {
  if (!row) {
    return (
      <td className="border border-border px-2 py-2 text-center text-xs text-muted-foreground align-top">
        —
      </td>
    )
  }

  const n = row.realized + row.disconfirmed
  const cls = discrepancyClass(row)

  return (
    <td className={`border border-border px-2 py-2 text-xs align-top ${cls}`}>
      <div className="font-semibold">{pct(row.realized_rate)}</div>
      <div className="text-[10px] text-muted-foreground">
        {ciStr(row.realized_rate_ci_low, row.realized_rate_ci_high)}
      </div>
      <div className="text-[10px] mt-0.5">
        N={n} · {row.realized}✓ {row.disconfirmed}✗ {row.pending}⏳
      </div>
    </td>
  )
}

// ── Domain × horizon grid ─────────────────────────────────────────────────────

function CalibrationGrid({ rows }: { rows: CalibrationRow[] }) {
  const domains = [...new Set(rows.map(r => r.domain))].sort()

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse border border-border">
        <thead>
          <tr className="bg-muted/50">
            <th className="border border-border px-2 py-1 text-left font-medium">Band</th>
            <th className="border border-border px-2 py-1 text-left font-medium">Domain</th>
            {HORIZON_ORDER.map(h => (
              <th key={h} className="border border-border px-2 py-1 text-center font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {BAND_ORDER.map(band => {
            const bandRows = rows.filter(r => r.confidence_band === band)
            const domainsInBand = domains.filter(d => bandRows.some(r => r.domain === d))
            if (domainsInBand.length === 0) {
              return (
                <tr key={band}>
                  <td className="border border-border px-2 py-1 font-medium capitalize" rowSpan={1}>{band}</td>
                  <td className="border border-border px-2 py-1 text-muted-foreground italic" colSpan={HORIZON_ORDER.length + 1}>
                    no predictions in this band
                  </td>
                </tr>
              )
            }
            return domainsInBand.map((domain, di) => (
              <tr key={`${band}-${domain}`} className="hover:bg-muted/30">
                {di === 0 && (
                  <td
                    className="border border-border px-2 py-1 font-semibold capitalize align-top"
                    rowSpan={domainsInBand.length}
                  >
                    {band}
                    <div className="text-[10px] text-muted-foreground font-normal">
                      midpoint: {pct(BAND_MIDPOINT[band])}
                    </div>
                  </td>
                )}
                <td className="border border-border px-2 py-1 text-muted-foreground">{domain}</td>
                {HORIZON_ORDER.map(h => {
                  const cell = bandRows.find(r => r.domain === domain && r.horizon_bucket === h)
                  return <CalibrationCell key={h} row={cell} />
                })}
              </tr>
            ))
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Legend ────────────────────────────────────────────────────────────────────

function Legend() {
  return (
    <div className="flex gap-4 text-xs text-muted-foreground mt-2">
      <span className="flex items-center gap-1">
        <span className="inline-block w-3 h-3 rounded bg-green-100 border border-green-300" />
        Within CI of midpoint
      </span>
      <span className="flex items-center gap-1">
        <span className="inline-block w-3 h-3 rounded bg-amber-100 border border-amber-300" />
        Borderline discrepancy
      </span>
      <span className="flex items-center gap-1">
        <span className="inline-block w-3 h-3 rounded bg-red-100 border border-red-300" />
        Discrepancy (N≥10)
      </span>
      <span className="ml-2">Cell: realized rate · [CI] · N=total resolved · ✓realized ✗disconfirmed ⏳pending</span>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function PredictionsCalibration() {
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['mcp-calibration'],
    queryFn: fetchCalibration,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Predictions / Calibration</h2>
          <p className="text-sm text-muted-foreground">
            Per-confidence-band realized rate vs. expected midpoint. Wilson 95% CI.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data?.refreshed_at && (
            <span className="text-xs text-muted-foreground">
              MV refreshed {new Date(data.refreshed_at).toLocaleString()}
            </span>
          )}
          {data?.grounding_pct !== null && data?.grounding_pct !== undefined && (
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${
              data.grounding_pct >= 0.95
                ? 'bg-green-100 text-green-800'
                : 'bg-amber-100 text-amber-800'
            }`}>
              MSR grounding: {(data.grounding_pct * 100).toFixed(1)}%
              {data.grounding_pct >= 0.95 ? ' ✓' : ' (target: 95%)'}
            </span>
          )}
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="text-xs px-3 py-1 rounded border border-border hover:bg-muted disabled:opacity-50"
          >
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="text-sm text-muted-foreground py-8 text-center">
          Loading calibration data…
        </div>
      )}

      {error && (
        <div className="rounded border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          Failed to load: {(error as Error).message}
        </div>
      )}

      {data && data.rows.length === 0 && <EmptyState />}

      {data && data.rows.length > 0 && (
        <>
          <CalibrationGrid rows={data.rows} />
          <Legend />
          <div className="text-xs text-muted-foreground mt-2">
            <b>Operator note:</b> Calibration data is sparse at v3.1 start. Wilson CIs on
            small N are very wide — interpret with caution. See perf brief §9 for
            house-rules iteration guidance. Red cells (N≥10) signal the calibration
            claims needing attention in this domain/band/horizon combination.
          </div>
        </>
      )}
    </div>
  )
}
