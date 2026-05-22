/**
 * PredictionsCalibration tab — placeholder for v3.4-P6.
 *
 * The calibration materialized view (mv_calibration_score) requires:
 *   - mcp_prediction_outcomes to have meaningful data (accumulates over time)
 *   - The calibration scoring function to run (migration + nightly job, v3.4)
 *   - Wilson confidence interval PostgreSQL functions (v3.4-S1 migration)
 *
 * This tab ships as a clearly-described placeholder so the dashboard surface
 * exists at v3.1.0-S5 close. The tab body is replaced when v3.4-P6 lands.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useQuery } from '@tanstack/react-query'

async function fetchPredictionsPreview() {
  // Fetch basic prediction count as a preview until calibration MV is ready
  const res = await fetch('/api/admin/mcp/predictions-summary')
  if (!res.ok) return null
  return res.json() as Promise<{
    total_predictions: number
    pending: number
    realized: number
    disconfirmed: number
    partial: number
  }>
}

export function PredictionsCalibration() {
  const summaryQuery = useQuery({
    queryKey: ['admin', 'mcp', 'predictions-summary'],
    queryFn: fetchPredictionsPreview,
    staleTime: 300_000,
    retry: false,
  })

  const summary = summaryQuery.data

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium">Predictions / Calibration</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Per-confidence-band calibration scores require the v3.4-P6 calibration
          materialized view (<code className="text-xs">mv_calibration_score</code>) and
          accumulated prediction outcomes over time.
        </p>
      </div>

      {/* Status callout */}
      <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-yellow-400 text-lg">⏳</span>
          <h3 className="font-semibold text-yellow-300">Calibration data available in v3.4</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          The calibration loop requires:
        </p>
        <ol className="text-sm text-muted-foreground list-decimal list-inside space-y-1">
          <li>Prediction logging via <code className="text-xs">log_prediction</code> MCP tool (active now)</li>
          <li>Outcome recording via <code className="text-xs">record_outcome</code> tool (active now)</li>
          <li>
            <code className="text-xs">mv_calibration_score</code> materialized view +
            Wilson CI SQL functions (v3.4-S1)
          </li>
          <li>Sufficient predictions past their horizon window (accumulates over time)</li>
        </ol>
        <p className="text-xs text-muted-foreground italic">
          Per perf brief §9: cells with &lt;10 observations are shown with wide confidence intervals;
          per-band-per-domain-per-horizon cells will have small N until client volume grows.
        </p>
      </div>

      {/* Live prediction counts preview */}
      {summary && (
        <div className="rounded-lg border border-border/50 p-5 space-y-3">
          <h3 className="font-medium text-sm">Logged predictions (live)</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            {[
              { label: 'Total', value: summary.total_predictions, cls: 'text-foreground' },
              { label: 'Pending', value: summary.pending, cls: 'text-muted-foreground' },
              { label: 'Realized', value: summary.realized, cls: 'text-green-400' },
              { label: 'Disconfirmed', value: summary.disconfirmed, cls: 'text-red-400' },
              { label: 'Partial', value: summary.partial, cls: 'text-yellow-400' },
            ].map(({ label, value, cls }) => (
              <div key={label} className="text-center">
                <p className={`text-2xl font-bold tabular-nums ${cls}`}>{value ?? 0}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
              </div>
            ))}
          </div>
          {(summary.realized + summary.disconfirmed) > 0 && (
            <p className="text-xs text-muted-foreground">
              Preliminary realized rate (not calibrated):&nbsp;
              <span className="text-foreground font-medium">
                {((summary.realized / (summary.realized + summary.disconfirmed)) * 100).toFixed(1)}%
              </span>
              &nbsp;(N={summary.realized + summary.disconfirmed}; calibration scores computed at v3.4)
            </p>
          )}
        </div>
      )}

      {/* What the full tab will show */}
      <div className="rounded-lg border border-border/30 p-5 space-y-3">
        <h3 className="font-medium text-sm text-muted-foreground">Preview: what v3.4-P6 will show</h3>
        <p className="text-xs text-muted-foreground">
          After v3.4-S1 closes, this tab will show a table per confidence band × domain × horizon bucket:
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-muted-foreground/60 border-collapse">
            <thead>
              <tr className="border-b border-border/20">
                <th className="py-1 text-left">Band</th>
                <th className="py-1 text-left">Domain</th>
                <th className="py-1 text-left">Horizon</th>
                <th className="py-1 text-left">N predictions</th>
                <th className="py-1 text-left">Realized rate (95% CI)</th>
                <th className="py-1 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['0.7–0.8', 'career', '31–180d', '—', '— (no data)', '⏳ pending v3.4'],
                ['0.6–0.7', 'health', '<=30d', '—', '— (no data)', '⏳ pending v3.4'],
                ['0.5–0.6', 'relationship', '>730d', '—', '— (no data)', '⏳ pending v3.4'],
              ].map(([band, domain, horizon, n, rate, status]) => (
                <tr key={`${band}-${domain}`} className="border-b border-border/10">
                  <td className="py-1 pr-3">{band}</td>
                  <td className="py-1 pr-3">{domain}</td>
                  <td className="py-1 pr-3">{horizon}</td>
                  <td className="py-1 pr-3">{n}</td>
                  <td className="py-1 pr-3">{rate}</td>
                  <td className="py-1">{status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
