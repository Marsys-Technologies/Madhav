'use client'

import { useState, useEffect, useCallback } from 'react'

/**
 * SharingPanel — super-admin grant/revoke UI for a single chart
 * (Unit 3.consult_nav, Commit 3).
 *
 * Talks to /api/clients/[id]/grants. View-only permission (the only kind
 * supported by chart_grants today). On revoke, the row is removed; the next
 * authorizeChartAccess call for that principal returns 'deny' and the page
 * route's redirect kicks in — no client-side polling needed.
 *
 * No tier/depth controls — tier excision is a concurrent workstream.
 */

export interface SharingGrant {
  id: string
  principal_id: string
  permission: 'view'
  granted_by: string
  granted_at: string
}

export interface SharingPanelProps {
  chartId: string
  /** Pre-loaded grants from the server, optional. */
  initialGrants?: SharingGrant[]
  /** Optional fetch override for testing. */
  fetcher?: typeof fetch
}

export function SharingPanel({ chartId, initialGrants, fetcher }: SharingPanelProps) {
  const [grants, setGrants] = useState<SharingGrant[]>(initialGrants ?? [])
  const [loading, setLoading] = useState(initialGrants === undefined)
  const [newPrincipal, setNewPrincipal] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchFn = fetcher ?? (typeof window !== 'undefined' ? window.fetch.bind(window) : fetch)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const r = await fetchFn(`/api/clients/${chartId}/grants`)
      if (!r.ok) throw new Error(`http_${r.status}`)
      const body = await r.json() as { grants: SharingGrant[] }
      setGrants(body.grants ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'fetch_failed')
    } finally {
      setLoading(false)
    }
  }, [chartId, fetchFn])

  useEffect(() => {
    if (initialGrants === undefined) {
      void refresh()
    }
  }, [initialGrants, refresh])

  async function handleGrant(e: React.FormEvent) {
    e.preventDefault()
    if (!newPrincipal.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const r = await fetchFn(`/api/clients/${chartId}/grants`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ principal_id: newPrincipal.trim() }),
      })
      if (!r.ok) {
        const body = await r.json().catch(() => ({})) as { error?: string }
        throw new Error(body.error ?? `http_${r.status}`)
      }
      setNewPrincipal('')
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'grant_failed')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRevoke(principalId: string) {
    setSubmitting(true)
    setError(null)
    try {
      const r = await fetchFn(
        `/api/clients/${chartId}/grants?principal_id=${encodeURIComponent(principalId)}`,
        { method: 'DELETE' }
      )
      if (!r.ok) {
        const body = await r.json().catch(() => ({})) as { error?: string }
        throw new Error(body.error ?? `http_${r.status}`)
      }
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'revoke_failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      data-testid="sharing-panel"
      data-chart-id={chartId}
      className="rounded-lg border border-[rgba(212,175,55,0.20)] bg-[#1a1408] p-4"
    >
      <h3 className="text-sm font-serif text-[var(--brand-gold-cream)] mb-3">
        Sharing — view-only access
      </h3>

      <form onSubmit={handleGrant} className="flex gap-2 mb-3" data-testid="grant-form">
        <input
          type="text"
          aria-label="Principal ID (Firebase UID) to grant view access to"
          placeholder="Firebase UID of guest"
          value={newPrincipal}
          onChange={(e) => setNewPrincipal(e.target.value)}
          disabled={submitting}
          data-testid="grant-principal-input"
          className="flex-1 rounded-md border border-[rgba(212,175,55,0.28)] bg-transparent px-3 py-1.5 text-xs text-[var(--brand-gold)] placeholder:opacity-50 outline-none focus:border-[var(--brand-gold)]"
        />
        <button
          type="submit"
          disabled={submitting || !newPrincipal.trim()}
          data-testid="grant-submit-button"
          className="rounded-md border border-[rgba(212,175,55,0.32)] bg-[rgba(212,175,55,0.08)] px-3 py-1.5 text-xs font-medium text-[var(--brand-gold)] hover:bg-[rgba(212,175,55,0.16)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Grant
        </button>
      </form>

      {error && (
        <div role="alert" data-testid="sharing-error" className="mb-2 text-xs text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div data-testid="sharing-loading" className="text-xs opacity-50">Loading…</div>
      ) : grants.length === 0 ? (
        <div data-testid="sharing-empty" className="text-xs opacity-50">
          No active grants. The chart is private to its owner + super-admin.
        </div>
      ) : (
        <ul className="flex flex-col gap-1" data-testid="grants-list">
          {grants.map((g) => (
            <li
              key={g.id}
              data-testid="grant-row"
              data-principal-id={g.principal_id}
              className="flex items-center justify-between rounded-md border border-[rgba(212,175,55,0.14)] px-3 py-1.5 text-xs"
            >
              <span className="truncate font-mono text-[var(--brand-gold)] opacity-80">
                {g.principal_id}
              </span>
              <button
                type="button"
                onClick={() => handleRevoke(g.principal_id)}
                disabled={submitting}
                data-testid="grant-revoke-button"
                aria-label={`Revoke view access for ${g.principal_id}`}
                className="ml-3 rounded border border-[rgba(212,175,55,0.20)] px-2 py-0.5 text-[10px] uppercase tracking-wider text-[rgba(212,175,55,0.75)] hover:border-red-400 hover:text-red-400 disabled:opacity-50"
              >
                Revoke
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
