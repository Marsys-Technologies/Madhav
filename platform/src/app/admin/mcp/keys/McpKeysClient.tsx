'use client'

/**
 * McpKeysClient — MCP API key management UI.
 *
 * Lists all MCP API keys. Provides:
 *   - "Create new key" button → opens a form, after creation shows the
 *     full key in a one-time display with a copy button.
 *   - "Revoke" button per key row (soft-delete, sets revoked_at).
 *
 * Pattern mirrors AdminClient.tsx (useQuery + mutation via fetch).
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { McpApiKeyRow, McpKeyCreatedResponse } from '@/lib/mcp/types'

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: { message: res.statusText } }))
    throw new Error(body?.error?.message ?? `HTTP ${res.status}`)
  }
  return (await res.json()) as T
}

// ── Key list table ────────────────────────────────────────────────────────────

function KeyRow({ k, onRevoke }: { k: McpApiKeyRow; onRevoke: (id: string) => void }) {
  const revoked = !!k.revoked_at
  return (
    <tr className={revoked ? 'opacity-40' : ''}>
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{k.key_id}</td>
      <td className="px-3 py-2 text-sm">{k.label ?? '—'}</td>
      <td className="px-3 py-2 text-sm">{k.user_uid.slice(0, 12)}…</td>
      <td className="px-3 py-2 text-xs">{k.audience_tier}</td>
      <td className="px-3 py-2 text-xs text-muted-foreground">
        {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : '—'}
      </td>
      <td className="px-3 py-2 text-xs text-muted-foreground">
        {new Date(k.created_at).toLocaleDateString()}
      </td>
      <td className="px-3 py-2">
        {revoked ? (
          <span className="text-xs text-red-500">Revoked</span>
        ) : (
          <button
            onClick={() => onRevoke(k.key_id)}
            className="rounded bg-red-900/30 px-2 py-1 text-xs text-red-400 hover:bg-red-900/60 transition"
          >
            Revoke
          </button>
        )}
      </td>
    </tr>
  )
}

// ── Create key dialog ─────────────────────────────────────────────────────────

interface CreateResult {
  key_id: string
  full_key: string
  label: string | null
  audience_tier: string
  user_uid: string
}

function CreatedKeyModal({ result, onClose }: { result: CreateResult; onClose: () => void }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(result.full_key).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-lg border border-border bg-background p-6 shadow-xl">
        <h2 className="mb-2 font-serif text-xl font-medium text-brand-gold-cream">
          Key created — copy it now
        </h2>
        <p className="mb-4 text-sm text-red-400">
          This is the only time the full key will be shown. It cannot be retrieved again.
        </p>
        <div className="mb-4 flex items-center gap-2 rounded bg-muted px-3 py-2">
          <code className="flex-1 break-all font-mono text-xs text-foreground">
            {result.full_key}
          </code>
          <button
            onClick={copy}
            className="shrink-0 rounded bg-accent px-2 py-1 text-xs text-accent-foreground hover:opacity-80 transition"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <dl className="mb-4 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <dt>Key ID</dt>
          <dd className="font-mono">{result.key_id}</dd>
          <dt>Label</dt>
          <dd>{result.label ?? '—'}</dd>
          <dt>Tier</dt>
          <dd>{result.audience_tier}</dd>
          <dt>User</dt>
          <dd className="truncate">{result.user_uid}</dd>
        </dl>
        <button
          onClick={onClose}
          className="w-full rounded bg-muted px-4 py-2 text-sm hover:opacity-80 transition"
        >
          Done (I&apos;ve saved the key)
        </button>
      </div>
    </div>
  )
}

// ── Main client component ─────────────────────────────────────────────────────

export function McpKeysClient() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [createLabel, setCreateLabel] = useState('')
  const [createTier, setCreateTier] = useState<'client' | 'super_admin'>('client')
  const [createUserUid, setCreateUserUid] = useState('')
  const [createdKey, setCreatedKey] = useState<CreateResult | null>(null)

  const keysQuery = useQuery({
    queryKey: ['admin', 'mcp-keys'],
    queryFn: () => fetchJson<{ keys: McpApiKeyRow[] }>('/api/mcp/keys'),
  })

  const createMutation = useMutation({
    mutationFn: (body: { label?: string; audience_tier: string; user_uid?: string }) =>
      fetchJson<McpKeyCreatedResponse>('/api/mcp/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      setCreatedKey({
        key_id: data.key_id,
        full_key: data.full_key,
        label: data.label,
        audience_tier: data.audience_tier,
        user_uid: data.user_uid,
      })
      setShowCreate(false)
      setCreateLabel('')
      setCreateTier('client')
      setCreateUserUid('')
      queryClient.invalidateQueries({ queryKey: ['admin', 'mcp-keys'] })
    },
  })

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) =>
      fetchJson(`/api/mcp/keys/${keyId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'mcp-keys'] })
    },
  })

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate({
      label: createLabel || undefined,
      audience_tier: createTier,
      user_uid: createUserUid || undefined,
    })
  }

  const keys = keysQuery.data?.keys ?? []
  const activeKeys = keys.filter(k => !k.revoked_at)
  const revokedKeys = keys.filter(k => !!k.revoked_at)

  return (
    <div className="space-y-6">
      {createdKey && (
        <CreatedKeyModal result={createdKey} onClose={() => setCreatedKey(null)} />
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-3xl font-medium tracking-wide text-brand-gold-cream">
            MCP API Keys
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Bearer tokens for external Claude Chat and Cowork integrations.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(v => !v)}
          className="rounded bg-accent px-4 py-2 text-sm text-accent-foreground hover:opacity-80 transition"
        >
          {showCreate ? 'Cancel' : 'Create new key'}
        </button>
      </div>

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="rounded-lg border border-border bg-muted/30 p-4 space-y-3"
        >
          <h2 className="text-sm font-medium">New API key</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Label (optional)</label>
              <input
                value={createLabel}
                onChange={e => setCreateLabel(e.target.value)}
                placeholder="e.g. claude-chat-laptop"
                className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-accent"
                maxLength={128}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Audience tier</label>
              <select
                value={createTier}
                onChange={e => setCreateTier(e.target.value as 'client' | 'super_admin')}
                className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-accent"
              >
                <option value="client">client</option>
                <option value="super_admin">super_admin</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs text-muted-foreground">
                User UID (leave blank for yourself)
              </label>
              <input
                value={createUserUid}
                onChange={e => setCreateUserUid(e.target.value)}
                placeholder="Firebase UID"
                className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
          </div>
          {createMutation.isError && (
            <p className="text-xs text-red-400">{String(createMutation.error)}</p>
          )}
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="rounded bg-accent px-4 py-2 text-sm text-accent-foreground hover:opacity-80 disabled:opacity-50 transition"
          >
            {createMutation.isPending ? 'Creating…' : 'Create key'}
          </button>
        </form>
      )}

      {keysQuery.isError && (
        <p className="text-sm text-red-400">Could not load keys: {String(keysQuery.error)}</p>
      )}

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Key ID</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Label</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">User</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Tier</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Last used</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Created</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {keysQuery.isLoading && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-sm text-muted-foreground">
                  Loading…
                </td>
              </tr>
            )}
            {!keysQuery.isLoading && activeKeys.length === 0 && revokedKeys.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-sm text-muted-foreground">
                  No keys yet. Create one above.
                </td>
              </tr>
            )}
            {activeKeys.map(k => (
              <KeyRow key={k.key_id} k={k} onRevoke={id => revokeMutation.mutate(id)} />
            ))}
            {revokedKeys.map(k => (
              <KeyRow key={k.key_id} k={k} onRevoke={id => revokeMutation.mutate(id)} />
            ))}
          </tbody>
        </table>
      </div>

      {revokeMutation.isError && (
        <p className="text-xs text-red-400">Revoke failed: {String(revokeMutation.error)}</p>
      )}
    </div>
  )
}
