'use client'

import {describeDefault} from './default-summary'
import {useAiAccountKeys} from '@/components/account/useAiAccountState'
import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, KeyRound, TerminalSquare } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import '@/components/pariprashna/pariprashna.css'
import './ai-console.css'
import { ProviderConnectionsSection } from './ProviderConnectionsSection'
import { CustomConfigurationsSection } from './CustomConfigurationsSection'
import { LocalClisSection } from './LocalClisSection'
import { hasCurrentProviderConfirmation, type AiChoice, type AiConsoleStateDto, type CliStateDto, type ConsoleMutation, type CatalogRefreshStatus, type CatalogRefresh } from './types'



const SAFE_MESSAGES: Record<string, string> = {
  unauthorized: 'Please sign in again to manage AI connections.',
  account_inactive: 'This account is not active.',
  not_found: 'AI Console is not available.',
  name_conflict: 'That name is already in use. Choose a different name.',
  invalid_request: 'Check the highlighted fields and try again.',
  request_too_large: 'That entry is too large.',
  confirmation_required: 'Review the dependencies and confirm deletion.',
  rate_limited: 'Too many requests. Wait a moment and try again.',
  AI_CONNECTION_INVALID: 'The provider rejected this credential. Replace it and test again.',
  AI_PERMISSION_DENIED: 'The provider denied access to this model.',
  AI_BILLING_UNAVAILABLE: 'Provider billing or credits are unavailable.',
  AI_RATE_LIMITED: 'The provider rate limit was reached. Try again later.',
  AI_PROVIDER_UNREACHABLE: 'The provider could not be reached. Try again later.',
  AI_CLI_NOT_GRANTED: 'Access to this local CLI has not been granted.',
  AI_CLI_UNREACHABLE: 'The local CLI could not be reached.',
  AI_MODEL_UNAVAILABLE: 'This model is no longer available.',
  AI_EXECUTION_FAILED: 'The request could not be completed.',
}

class SafeRequestError extends Error {
  constructor(message: string) { super(message); this.name = 'SafeRequestError' }
}

async function fetchJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url, { ...init, headers: { 'Content-Type': 'application/json', ...init.headers } })
  const payload = await response.json().catch(() => null) as { error?: unknown } | null
  if (!response.ok) {
    const discriminator = typeof payload?.error === 'string'
      ? payload.error
      : typeof payload?.error === 'object' && payload.error !== null && 'code' in payload.error
        ? String((payload.error as { code: unknown }).code)
        : ''
    throw new SafeRequestError(SAFE_MESSAGES[discriminator] ?? 'The request could not be completed safely.')
  }
  return payload as T
}

export function AIConsole({embedded=false}:{embedded?:boolean}) {
  const queryClient = useQueryClient()
  const keys=useAiAccountKeys()
  const [status, setStatus] = useState('')
  const [announcedStatus, setAnnouncedStatus] = useState('')
  const [cliSeed, setCliSeed] = useState<{ sourceId: string; nonce: number } | null>(null)
  const [apiSeed, setApiSeed] = useState<{ sourceId: string; nonce: number } | null>(null)
  const [refreshStatus, setRefreshStatus] = useState<Record<string, CatalogRefreshStatus>>({})
  const refreshFlights = useRef(new Map<string, Promise<void>>())
  const mounted = useRef(true)
  const autoRefreshSeen = useRef(new Set<string>())
  const autoRefreshQueue = useRef(Promise.resolve())

  useEffect(() => {
    mounted.current = true
    return () => { mounted.current = false }
  }, [])

  const stateQuery = useQuery({
    queryKey: keys.state,
    queryFn: ({ signal }) => fetchJson<AiConsoleStateDto>('/api/ai-console', { signal }),
  })
  const cliQuery = useQuery({
    queryKey: keys.clis,
    queryFn: ({ signal }) => fetchJson<CliStateDto>('/api/ai-console/clis', { signal }),
  })

  const refreshCatalog: CatalogRefresh = useCallback((kind, id, force = true) => {
    const key = `${kind}:${id}`
    const existing = refreshFlights.current.get(key)
    if (existing) return existing
    setRefreshStatus(current => ({ ...current, [key]: { pending: true } }))
    const work = (async () => {
      try {
        const result = await fetchJson<{ status: string; state?: string }>(kind === 'cli'
          ? `/api/ai-console/clis/${id}/refresh` : `/api/ai-console/connections/${id}/refresh`, {
          method: 'POST', body: JSON.stringify({ force }),
        })
        setRefreshStatus(current => ({ ...current, [key]: { pending: false,
          ...(result.state === 'needs_attention' ? { error: 'Models were refreshed. Test local CLI to verify this installed version before using it.' } : {}) } }))
        if (force) setStatus(result.status === 'skipped' ? 'The model list is already current. Please wait a moment before another refresh.' : 'Models and effort levels refreshed.')
      } catch (error) {
        const message = error instanceof SafeRequestError ? error.message : 'The model list could not be refreshed.'
        setRefreshStatus(current => ({ ...current, [key]: { pending: false, error: `${message} The previous model list is retained.` } }))
      } finally {
        await Promise.allSettled([
          queryClient.invalidateQueries({ queryKey: keys.state }),
          queryClient.invalidateQueries({ queryKey: keys.clis }),
        ])
        refreshFlights.current.delete(key)
      }
    })()
    refreshFlights.current.set(key, work)
    return work
  }, [queryClient,keys])

  useEffect(() => {
    const stale = (source: { catalogRefreshedAt?: string | null; catalogAttemptedAt?: string | null; catalogErrorCode?: string | null }) => {
      const stamp = source.catalogErrorCode ? source.catalogAttemptedAt : source.catalogRefreshedAt
      const checked = stamp ? new Date(stamp).getTime() : 0
      return !Number.isFinite(checked) || Date.now() - checked >= (source.catalogErrorCode ? 60_000 : 15 * 60_000)
    }
    const enqueue = (kind: 'connection' | 'cli', id: string) => {
      const key = `${kind}:${id}`
      if (autoRefreshSeen.current.has(key)) return
      autoRefreshSeen.current.add(key)
      autoRefreshQueue.current = autoRefreshQueue.current.then(async () => {
        if (mounted.current) await refreshCatalog(kind, id, false)
      })
    }
    for (const connection of stateQuery.data?.connections ?? []) {
      if (!connection.deletedAt && ['openai', 'anthropic', 'google', 'openrouter'].includes(connection.providerId)
        && hasCurrentProviderConfirmation(connection) && stale(connection)) enqueue('connection', connection.id)
    }
    for (const cli of cliQuery.data?.clis ?? []) {
      if (cli.state !== 'not_granted' && stale(cli)) enqueue('cli', cli.cliId)
    }
  }, [stateQuery.data, cliQuery.data, refreshCatalog])

  useEffect(() => {
    const timer = window.setTimeout(() => setAnnouncedStatus(status), 180)
    return () => window.clearTimeout(timer)
  }, [status])

  const mutation = useMutation({
    mutationFn: ({ url, init }: { url: string; init: RequestInit }) => fetchJson<unknown>(url, init),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: keys.state }),
        queryClient.invalidateQueries({ queryKey: keys.clis }),
      ])
    },
  })

  const mutate: ConsoleMutation = async (url, init, successMessage) => {
    setStatus('Working…')
    try {
      const result = await mutation.mutateAsync({ url, init })
      setStatus(typeof successMessage === 'function' ? successMessage(result) : successMessage)
      return result
    } catch (error) {
      const message = error instanceof SafeRequestError ? error.message : 'The request could not be completed safely.'
      setStatus(message)
      throw new SafeRequestError(message)
    }
  }

  const selectDefault = (choice: AiChoice) => mutate('/api/ai-console/default', {
    method: 'PUT', body: JSON.stringify({ choice }),
  }, 'Default AI updated.')

  const stateStatus = stateQuery.data ? 'ready' : stateQuery.isError ? 'error' : 'loading'
  const cliStatus = cliQuery.data ? 'ready' : cliQuery.isError ? 'error' : 'loading'
  const state = stateQuery.data
  const clis = cliQuery.data?.clis ?? []
  const loading = stateStatus === 'loading' || cliStatus === 'loading'
  const defaultName = describeDefault(state, clis)

  return (
    <div className="pp-root min-h-full">
      <div className="aic-page">
        <header className="aic-header">
          {!embedded && <><p className="aic-eyebrow">AI setup</p><h1 className="aic-title">AI Console</h1></>}
          <p className="aic-intro">
            Connect your own providers, compose named four-role configurations, and choose one exact default for Madhav’s AI work.
          </p>
          <div className="aic-default-summary"><span>Current default</span><strong>{defaultName}</strong><small>{state && !state.defaultChoice ? 'Create a role setup below, then choose it as the default before using Paripraśna.' : 'Paripraśna uses this when its picker is set to Default.'}</small></div>
        </header>

        {(stateQuery.isRefetchError || cliQuery.isRefetchError) && <p className="aic-failure-guidance" role="status">The latest settings could not be reloaded. The previous view is retained; refresh the page to try again.</p>}

        <div className="aic-sections" aria-busy={loading}>
          <details className="aic-group" open>
            <summary className="aic-group-summary"><span className="aic-group-icon"><KeyRound aria-hidden="true" /></span><span><strong>API providers</strong><small>Keys, tested models, role setups, and custom API configurations</small></span><ChevronDown className="aic-chevron" aria-hidden="true" /></summary>
            <div className="aic-group-body">
          <ProviderConnectionsSection
            state={state}
            loading={stateStatus === 'loading'}
            error={stateStatus === 'error'}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
            onConfigureRoles={sourceId => setApiSeed(current => ({ sourceId, nonce: (current?.nonce ?? 0) + 1 }))}
            refreshStatus={refreshStatus}
            onRefreshCatalog={refreshCatalog}
          />
          <CustomConfigurationsSection
            key={`api-${apiSeed?.nonce ?? 0}`}
            mode="api"
            state={state}
            clis={clis}
            loading={stateStatus === 'loading'}
            error={stateStatus === 'error'}
            cliStatus={cliStatus}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
            seed={apiSeed}
            onSeedDismiss={() => setApiSeed(null)}
          />
            </div>
          </details>
          <details className="aic-group" open>
            <summary className="aic-group-summary"><span className="aic-group-icon"><TerminalSquare aria-hidden="true" /></span><span><strong>Local CLIs</strong><small>Subscription access, role setups, and custom CLI configurations</small></span><ChevronDown className="aic-chevron" aria-hidden="true" /></summary>
            <div className="aic-group-body">
          <LocalClisSection
            state={state}
            clis={clis}
            loading={cliStatus === 'loading'}
            error={cliStatus === 'error'}
            aggregateStatus={stateStatus}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
            onConfigureRoles={sourceId => setCliSeed(current => ({ sourceId, nonce: (current?.nonce ?? 0) + 1 }))}
            refreshStatus={refreshStatus}
            onRefreshCatalog={refreshCatalog}
          />
          <CustomConfigurationsSection
            key={`cli-${cliSeed?.nonce ?? 0}`}
            mode="cli"
            state={state}
            clis={clis}
            loading={stateStatus === 'loading'}
            error={stateStatus === 'error'}
            cliStatus={cliStatus}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
            seed={cliSeed}
            onSeedDismiss={() => setCliSeed(null)}
          />
            </div>
          </details>
        </div>
        <div className="aic-live" role="status" aria-live="polite" aria-atomic="true">{announcedStatus}</div>
      </div>
    </div>
  )
}
