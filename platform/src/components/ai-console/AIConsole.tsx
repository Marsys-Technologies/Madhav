'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import '@/components/pariprashna/pariprashna.css'
import './ai-console.css'
import { ProviderConnectionsSection } from './ProviderConnectionsSection'
import { CustomConfigurationsSection } from './CustomConfigurationsSection'
import { LocalClisSection } from './LocalClisSection'
import type { AiChoice, AiConsoleStateDto, CliStateDto, ConsoleMutation } from './types'

const CONSOLE_QUERY_KEY = ['ai-console', 'state'] as const
const CLI_QUERY_KEY = ['ai-console', 'clis'] as const

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

export function AIConsole() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState('')
  const [announcedStatus, setAnnouncedStatus] = useState('')

  const stateQuery = useQuery({
    queryKey: CONSOLE_QUERY_KEY,
    queryFn: ({ signal }) => fetchJson<AiConsoleStateDto>('/api/ai-console', { signal }),
  })
  const cliQuery = useQuery({
    queryKey: CLI_QUERY_KEY,
    queryFn: ({ signal }) => fetchJson<CliStateDto>('/api/ai-console/clis', { signal }),
  })

  useEffect(() => {
    const timer = window.setTimeout(() => setAnnouncedStatus(status), 180)
    return () => window.clearTimeout(timer)
  }, [status])

  const mutation = useMutation({
    mutationFn: ({ url, init }: { url: string; init: RequestInit }) => fetchJson<unknown>(url, init),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: CONSOLE_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: CLI_QUERY_KEY }),
      ])
    },
  })

  const mutate: ConsoleMutation = async (url, init, successMessage) => {
    setStatus('Working…')
    try {
      const result = await mutation.mutateAsync({ url, init })
      setStatus(successMessage)
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

  const stateStatus = stateQuery.isSuccess ? 'ready' : stateQuery.isError ? 'error' : 'loading'
  const cliStatus = cliQuery.isSuccess ? 'ready' : cliQuery.isError ? 'error' : 'loading'
  const state = stateQuery.isSuccess ? stateQuery.data : undefined
  const clis = cliQuery.isSuccess ? cliQuery.data.clis : []
  const loading = stateStatus === 'loading' || cliStatus === 'loading'

  return (
    <div className="pp-root min-h-full">
      <div className="aic-page">
        <header className="aic-header">
          <p className="aic-eyebrow">Cockpit instrument</p>
          <h1 className="aic-title">AI Console</h1>
          <p className="aic-intro">
            Connect your own providers, compose named four-role configurations, and choose one exact default for Madhav’s AI work.
          </p>
        </header>

        <div className="aic-sections" aria-busy={loading}>
          <ProviderConnectionsSection
            state={state}
            loading={stateStatus === 'loading'}
            error={stateStatus === 'error'}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
          />
          <CustomConfigurationsSection
            state={state}
            clis={clis}
            loading={stateStatus === 'loading'}
            error={stateStatus === 'error'}
            cliStatus={cliStatus}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
          />
          <LocalClisSection
            state={state}
            clis={clis}
            loading={cliStatus === 'loading'}
            error={cliStatus === 'error'}
            aggregateStatus={stateStatus}
            mutationPending={mutation.isPending}
            mutate={mutate}
            onSelectDefault={selectDefault}
          />
        </div>
        <div className="aic-live" role="status" aria-live="polite" aria-atomic="true">{announcedStatus}</div>
      </div>
    </div>
  )
}
