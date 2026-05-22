/**
 * AuditFindings tab — findings table with drill-down modal.
 *
 * Fetches from /api/admin/mcp/audit-findings (new endpoint wired to
 * mcp_audit_findings table built in S4 migration 074).
 * Shows unresolved class_1/class_2/warn findings with resolve action.
 * Drill-down modal shows: trace_id, finding description, evidence JSON,
 * cited vs available vs fabricated signal IDs.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuditFinding {
  id: string
  trace_id: string
  mcp_key_id: string | null
  audience_tier: string | null
  finding_class: string
  severity: 'info' | 'warn' | 'class_1' | 'class_2'
  description: string
  evidence: Record<string, unknown>
  available_signal_ids: string[] | null
  cited_signal_ids: string[] | null
  fabricated_cite_ids: string[] | null
  numerical_claims: unknown | null
  attached_at: string
  resolved_at: string | null
  resolved_by: string | null
  resolution_note: string | null
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────

async function fetchFindings(showResolved: boolean): Promise<AuditFinding[]> {
  const url = showResolved
    ? '/api/admin/mcp/audit-findings?include_resolved=true'
    : '/api/admin/mcp/audit-findings'
  const res = await fetch(url)
  if (!res.ok) {
    if (res.status === 404) return [] // endpoint not yet deployed
    throw new Error(`Failed to fetch audit findings: ${res.status}`)
  }
  const data = await res.json() as { findings?: AuditFinding[] }
  return data.findings ?? []
}

async function resolveFinding(
  id: string,
  resolution: string
): Promise<void> {
  const res = await fetch(`/api/admin/mcp/audit-findings/${id}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resolution_note: resolution }),
  })
  if (!res.ok) throw new Error(`Failed to resolve finding: ${res.status}`)
}

// ── Severity badge ────────────────────────────────────────────────────────────

function SeverityBadge({ severity }: { severity: AuditFinding['severity'] }) {
  const cls =
    severity === 'class_1' ? 'bg-red-500/20 text-red-300 ring-1 ring-red-500/40'
    : severity === 'class_2' ? 'bg-orange-500/20 text-orange-300'
    : severity === 'warn'   ? 'bg-yellow-500/20 text-yellow-300'
    : 'bg-muted text-muted-foreground'
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {severity}
    </span>
  )
}

// ── Drill-down modal ──────────────────────────────────────────────────────────

function FindingModal({
  finding,
  onClose,
  onResolve,
}: {
  finding: AuditFinding
  onClose: () => void
  onResolve: (id: string, note: string) => void
}) {
  const [resolutionNote, setResolutionNote] = useState('')
  const [resolving, setResolving] = useState(false)

  async function handleResolve() {
    if (!resolutionNote.trim()) return
    setResolving(true)
    try {
      await onResolve(finding.id, resolutionNote)
    } finally {
      setResolving(false)
    }
  }

  const fabricated = finding.fabricated_cite_ids ?? []
  const cited = finding.cited_signal_ids ?? []
  const available = finding.available_signal_ids ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="relative max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background p-6 shadow-xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
        >
          ✕
        </button>
        <h3 className="text-base font-semibold mb-1">Audit Finding Detail</h3>
        <p className="text-xs text-muted-foreground font-mono mb-4">{finding.id}</p>

        <div className="grid grid-cols-2 gap-3 text-sm mb-4">
          <div><span className="text-muted-foreground">Class:</span> <code>{finding.finding_class}</code></div>
          <div><span className="text-muted-foreground">Severity:</span> <SeverityBadge severity={finding.severity} /></div>
          <div><span className="text-muted-foreground">Trace:</span> <code className="text-xs">{finding.trace_id}</code></div>
          <div><span className="text-muted-foreground">Tier:</span> {finding.audience_tier ?? '—'}</div>
          <div><span className="text-muted-foreground">Attached:</span> {new Date(finding.attached_at).toLocaleString()}</div>
          {finding.resolved_at && (
            <div><span className="text-muted-foreground">Resolved:</span> {new Date(finding.resolved_at).toLocaleString()} by {finding.resolved_by}</div>
          )}
        </div>

        <div className="mb-4 rounded-md bg-muted/20 p-3 text-sm">
          <p className="font-medium mb-1">Description</p>
          <p className="text-muted-foreground">{finding.description}</p>
        </div>

        {fabricated.length > 0 && (
          <div className="mb-3 rounded-md border border-red-500/30 bg-red-500/5 p-3">
            <p className="text-xs font-semibold text-red-400 mb-1">Fabricated citations ({fabricated.length})</p>
            <div className="flex flex-wrap gap-1">
              {fabricated.map(id => (
                <code key={id} className="text-xs bg-red-500/10 text-red-300 rounded px-1 py-0.5">{id}</code>
              ))}
            </div>
          </div>
        )}

        {cited.length > 0 && (
          <div className="mb-3 rounded-md border border-green-500/20 bg-green-500/5 p-3">
            <p className="text-xs font-semibold text-green-400 mb-1">Grounded citations ({cited.length})</p>
            <div className="flex flex-wrap gap-1">
              {cited.slice(0, 20).map(id => (
                <code key={id} className="text-xs bg-green-500/10 text-green-300 rounded px-1 py-0.5">{id}</code>
              ))}
              {cited.length > 20 && <span className="text-xs text-muted-foreground">+{cited.length - 20} more</span>}
            </div>
          </div>
        )}

        {available.length > 0 && (
          <div className="mb-3 rounded-md border border-border/50 p-3">
            <p className="text-xs font-semibold text-muted-foreground mb-1">Available signal IDs ({available.length})</p>
            <p className="text-xs text-muted-foreground">{available.slice(0, 5).join(', ')}{available.length > 5 ? ` … +${available.length - 5}` : ''}</p>
          </div>
        )}

        {Object.keys(finding.evidence).length > 0 && (
          <details className="mb-4">
            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">Evidence JSON</summary>
            <pre className="mt-2 text-xs bg-muted/20 p-2 rounded overflow-x-auto">
              {JSON.stringify(finding.evidence, null, 2)}
            </pre>
          </details>
        )}

        {!finding.resolved_at && (
          <div className="border-t border-border/40 pt-4 space-y-2">
            <p className="text-xs font-medium">Resolve this finding</p>
            <select
              value={resolutionNote}
              onChange={e => setResolutionNote(e.target.value)}
              className="w-full text-xs rounded border border-border/50 bg-background px-2 py-1.5"
            >
              <option value="">— Select resolution —</option>
              <option value="false_positive">False positive (heuristic was wrong)</option>
              <option value="fixed_in_next_backfill">Fixed in next backfill</option>
              <option value="house_rules_updated">House-rules updated to prevent</option>
              <option value="needs_investigation">Needs investigation</option>
              <option value="accepted_risk">Accepted risk</option>
            </select>
            <button
              onClick={handleResolve}
              disabled={!resolutionNote || resolving}
              className="text-xs px-3 py-1.5 rounded bg-brand-gold-cream text-black font-medium disabled:opacity-40 hover:opacity-90"
            >
              {resolving ? 'Resolving…' : 'Mark resolved'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export function AuditFindings() {
  const queryClient = useQueryClient()
  const [showResolved, setShowResolved] = useState(false)
  const [selectedFinding, setSelectedFinding] = useState<AuditFinding | null>(null)
  const [filterClass, setFilterClass] = useState<string>('all')

  const findingsQuery = useQuery({
    queryKey: ['admin', 'mcp', 'audit-findings', showResolved],
    queryFn: () => fetchFindings(showResolved),
    staleTime: 60_000,
  })

  const resolveMutation = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) => resolveFinding(id, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'audit-findings'] })
      setSelectedFinding(null)
    },
  })

  const findings = findingsQuery.data ?? []
  const filtered = filterClass === 'all' ? findings : findings.filter(f => f.finding_class === filterClass)

  const findingClasses = [...new Set(findings.map(f => f.finding_class))].sort()

  const classCounts = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.severity] = (acc[f.severity] ?? 0) + 1
    return acc
  }, {})

  if (findingsQuery.isError) {
    return <p className="text-sm text-red-400">Failed to load audit findings.</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-medium">Audit Findings</h2>
          {/* Summary badges */}
          {['class_1', 'class_2', 'warn'].map(s => classCounts[s] ? (
            <SeverityBadge key={s} severity={s as AuditFinding['severity']} />
          ) : null)}
          {Object.values(classCounts).every(v => v === 0) && !findingsQuery.isLoading && (
            <span className="text-xs text-green-400">No unresolved findings</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-xs text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={e => setShowResolved(e.target.checked)}
              className="rounded"
            />
            Show resolved
          </label>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'audit-findings'] })}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Refresh
          </button>
        </div>
      </div>

      {findingClasses.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Filter by class:</span>
          <select
            value={filterClass}
            onChange={e => setFilterClass(e.target.value)}
            className="text-xs rounded border border-border/50 bg-background px-2 py-1"
          >
            <option value="all">All classes</option>
            {findingClasses.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      )}

      {findingsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground animate-pulse">Loading audit findings…</p>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg border border-border/30 p-6 text-center">
          <p className="text-sm text-muted-foreground">
            {findings.length === 0
              ? 'No audit findings. Run the nightly audit job to generate findings.'
              : 'No findings match the current filter.'}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border/50">
          <table className="w-full text-sm">
            <thead className="border-b border-border/50 bg-muted/30">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Severity</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Class</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Trace</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Description</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Attached</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {filtered.map(finding => (
                <tr
                  key={finding.id}
                  className="hover:bg-muted/20 cursor-pointer"
                  onClick={() => setSelectedFinding(finding)}
                >
                  <td className="px-4 py-3">
                    <SeverityBadge severity={finding.severity} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {finding.finding_class}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {finding.trace_id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3 text-sm max-w-xs truncate">
                    {finding.description}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(finding.attached_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {finding.resolved_at ? (
                      <span className="text-xs text-green-400">Resolved</span>
                    ) : (
                      <span className="text-xs text-muted-foreground">Open</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedFinding && (
        <FindingModal
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
          onResolve={(id, note) => resolveMutation.mutateAsync({ id, note })}
        />
      )}
    </div>
  )
}
