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

import { useId, useRef, useState, type RefObject } from 'react'
import { PageTitle } from '@/components/journey1/Titles'
import { useObservatoryScope } from '@/components/observatory/ObservatoryScope'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { McpApiKeyRow, McpKeyCreatedResponse } from '@/lib/mcp/types'
import styles from './keys.module.css'

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
    <tr className={revoked ? styles.revoked : undefined}>
      <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{k.key_id}</td>
      <td className="px-3 py-2 text-sm">{k.label ?? '—'}</td>
      <td className="px-3 py-2 text-sm">{k.user_uid.slice(0, 12)}…</td>
      <td className="px-3 py-2 text-xs text-muted-foreground">
        {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : '—'}
      </td>
      <td className="px-3 py-2 text-xs text-muted-foreground">
        {new Date(k.created_at).toLocaleDateString()}
      </td>
      <td className="px-3 py-2">
        {revoked ? (
          <span className={`${styles.error} text-xs`}>Revoked</span>
        ) : (
          <button
            onClick={() => onRevoke(k.key_id)}
            className={`${styles.dangerAction} text-xs`}
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
  user_uid: string
}

function CreatedKeyModal({ result, onClose, returnFocus }: {
  result: CreateResult
  onClose: () => void
  returnFocus: RefObject<HTMLButtonElement | null>
}) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'manual'>('idle')
  const keyField = useRef<HTMLTextAreaElement>(null)

  async function copy() {
    try {
      await navigator.clipboard.writeText(result.full_key)
      setCopyState('copied')
    } catch {
      setCopyState('manual')
      keyField.current?.focus()
      keyField.current?.select()
    }
  }

  return (
    <Dialog open disablePointerDismissal>
      <DialogContent showCloseButton={false} initialFocus={keyField} finalFocus={returnFocus} className="max-h-[calc(100dvh-2rem)] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Key created — copy it now</DialogTitle>
          <DialogDescription>This is the only time the full key will be shown. It cannot be retrieved again.</DialogDescription>
        </DialogHeader>
        <div className="flex flex-wrap items-center gap-2">
          <textarea
            ref={keyField}
            aria-label="MCP API key"
            value={result.full_key}
            rows={3}
            readOnly
            spellCheck={false}
            onFocus={event => event.currentTarget.select()}
            className="min-w-0 flex-1 rounded border border-border bg-muted p-2 font-mono text-xs text-foreground"
          />
          <button
            type="button"
            onClick={copy}
            className="min-h-11 shrink-0 rounded bg-accent px-3 text-sm text-accent-foreground hover:opacity-80"
          >
            Copy
          </button>
        </div>
        {copyState === 'copied' && <p role="status">Key copied.</p>}
        {copyState === 'manual' && <p role="alert">Clipboard access was unavailable. Copy the key manually from the selected field.</p>}
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <dt>Key ID</dt>
          <dd className="font-mono">{result.key_id}</dd>
          <dt>Label</dt>
          <dd>{result.label ?? '—'}</dd>
          <dt>User</dt>
          <dd className="truncate">{result.user_uid}</dd>
        </dl>
        <button
          type="button"
          onClick={onClose}
          className="min-h-11 w-full rounded bg-muted px-4 py-2 text-sm hover:opacity-80"
        >
          Done (I&apos;ve saved the key)
        </button>
      </DialogContent>
    </Dialog>
  )
}

// ── Main client component ─────────────────────────────────────────────────────

export function McpKeysClient() {
  const queryClient = useQueryClient()
  const {userId,users} = useObservatoryScope()
  const [showCreate, setShowCreate] = useState(false)
  const [createLabel, setCreateLabel] = useState('')
  const [createUserUid, setCreateUserUid] = useState('')
  const [createdKey, setCreatedKey] = useState<CreateResult | null>(null)
  const createButton = useRef<HTMLButtonElement>(null)
  const labelId = useId()

  const keysQuery = useQuery({
    queryKey: ['admin', userId, 'mcp-keys'],
    queryFn: () => fetchJson<{ keys: McpApiKeyRow[] }>('/api/mcp/keys'),
  })

  const createMutation = useMutation({
    mutationFn: (body: { label?: string; user_uid?: string }) =>
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
        user_uid: data.user_uid,
      })
      setShowCreate(false)
      setCreateLabel('')
      setCreateUserUid('')
      queryClient.invalidateQueries({ queryKey: ['admin', userId, 'mcp-keys'] })
    },
  })

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) =>
      fetchJson(`/api/mcp/keys/${keyId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', userId, 'mcp-keys'] })
    },
  })

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate({
      label: createLabel || undefined,
      user_uid: createUserUid || undefined,
    })
  }

  const keys = keysQuery.isError ? [] : keysQuery.data?.keys ?? []
  const activeKeys = keys.filter(k => !k.revoked_at)
  const revokedKeys = keys.filter(k => !!k.revoked_at)

  return (
    <div className={`${styles.keys} space-y-6`}>
      {createdKey && (
        <CreatedKeyModal result={createdKey} returnFocus={createButton} onClose={() => {setCreatedKey(null);createMutation.reset()}} />
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <PageTitle name="mcpKeys" />
          <p className="mt-1 text-sm text-muted-foreground">
            User-associated keys for external clients. Permissions come from the account and chart grants; a key does not create a new role.
          </p>
        </div>
        <button
          ref={createButton}
          type="button"
          onClick={() => setShowCreate(v => !v)}
          className={styles.primary}
        >
          {showCreate ? 'Cancel' : 'Create new key'}
        </button>
      </div>

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className={`${styles.createForm} space-y-3`}
        >
          <h2 className="text-sm font-medium">New API key</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor={labelId} className="mb-1 block text-xs text-muted-foreground">Label (optional)</label>
              <input
                id={labelId}
                value={createLabel}
                onChange={e => setCreateLabel(e.target.value)}
                placeholder="e.g. claude-chat-laptop"
                className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-accent"
                maxLength={128}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs text-muted-foreground">
                Active account
                <select value={createUserUid} onChange={e => setCreateUserUid(e.target.value)} className="mt-1 w-full rounded border px-3 py-1.5 text-sm"><option value="">Your account</option>{users.filter(user=>user.id!==userId && user.status==='active').map(user=><option key={user.id} value={user.id}>{user.name}</option>)}</select>
              </label>
            </div>
          </div>
          {createMutation.isError && (
            <p role="alert" className={`${styles.error} text-xs`}>{String(createMutation.error)}</p>
          )}
          <button
            type="submit"
            disabled={createMutation.isPending}
            className={styles.primary}
          >
            {createMutation.isPending ? 'Creating…' : 'Create key'}
          </button>
        </form>
      )}

      {keysQuery.isError && (
        <div role="alert" className="flex flex-wrap items-center gap-3 text-sm">
          <p className={styles.error}>Could not load keys.</p>
          <button type="button" className={styles.primary} disabled={keysQuery.isFetching} onClick={() => void keysQuery.refetch()}>
            {keysQuery.isFetching ? 'Retrying…' : 'Try again'}
          </button>
        </div>
      )}

      <div className={styles.results} role="region" aria-label="MCP key list" tabIndex={0}>
        <table className="w-full text-left">
          <thead>
            <tr className={styles.tableHeading}>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Key ID</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Label</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">User</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Last used</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Created</th>
              <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {keysQuery.isLoading && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-center text-sm text-muted-foreground">
                  <span role="status">Loading keys…</span>
                </td>
              </tr>
            )}
            {!keysQuery.isLoading && !keysQuery.isError && activeKeys.length === 0 && revokedKeys.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-center text-sm text-muted-foreground">
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
        <p role="alert" className={`${styles.error} text-xs`}>Revoke failed: {String(revokeMutation.error)}</p>
      )}
    </div>
  )
}
