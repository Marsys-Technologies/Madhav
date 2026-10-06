import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { onlineManager, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AiAccessTab } from '../AiAccessTab'
import type { AdminCliGrant, AdminUser } from '../types'

const users: AdminUser[] = [
  {
    id: 'admin-1', role: 'super_admin', status: 'active', name: 'Asha Rao', username: 'asha',
    email: 'asha@example.test', created_at: '2026-09-27T10:00:00.000Z', approved_at: '2026-09-27T10:00:00.000Z',
  },
  {
    id: 'guest-1', role: 'guest', status: 'active', name: 'Biren Sen', username: 'biren',
    email: 'biren@example.test', created_at: '2026-09-27T10:00:00.000Z', approved_at: '2026-09-27T10:00:00.000Z',
  },
  {
    id: 'disabled-1', role: 'guest', status: 'disabled', name: 'Chitra Das', username: 'chitra',
    email: 'chitra@example.test', created_at: '2026-09-27T10:00:00.000Z', approved_at: '2026-09-27T10:00:00.000Z',
  },
]

function grants(overrides: Partial<Record<AdminCliGrant['cliId'], boolean>> = {}): AdminCliGrant[] {
  return [
    { cliId: 'codex', productName: 'Codex CLI', granted: overrides.codex ?? false, hostState: 'unavailable' },
    { cliId: 'claude_code', productName: 'Claude Code', granted: overrides.claude_code ?? false, hostState: 'reachable' },
    { cliId: 'gemini_antigravity', productName: 'Gemini / Antigravity', granted: overrides.gemini_antigravity ?? false, hostState: 'unavailable' },
    { cliId: 'kimi_code', productName: 'Kimi Code', granted: overrides.kimi_code ?? false, hostState: 'unavailable' },
  ]
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function setup(options: {
  grantsByUser?: Record<string, AdminCliGrant[]>
  failPatch?: boolean
  pendingPatch?: boolean
  pendingAudit?: boolean
  hostilePayload?: boolean
  initialUserId?: string
} = {}) {
  const grantsByUser: Record<string, AdminCliGrant[]> = options.grantsByUser ?? {
    'admin-1': grants(),
    'guest-1': grants(),
    'disabled-1': grants({ claude_code: true }),
  }
  const calls: Array<{ url: string; init?: RequestInit }> = []
  const events: string[] = []
  let settlePatch: (() => void) | null = null
  let settleAudit: (() => void) | null = null

  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    calls.push({ url, init })
    const match = url.match(/^\/api\/admin\/users\/([^/]+)\/ai-cli-grants$/)
    if (!match) return json({ error: 'unexpected_endpoint' }, 500)
    const userId = decodeURIComponent(match[1])
    if (init?.method === 'PATCH') {
      events.push(`patch:${userId}`)
      if (options.failPatch) {
        return json({ error: { detail: 'sk-hostile-raw-provider-error' } }, 500)
      }
      const body = JSON.parse(String(init.body)) as { cliId: AdminCliGrant['cliId']; granted: boolean }
      const apply = () => {
        grantsByUser[userId] = grantsByUser[userId].map(grant =>
          grant.cliId === body.cliId ? { ...grant, granted: body.granted } : grant,
        )
      }
      if (options.pendingPatch) {
        return await new Promise<Response>(resolve => {
          settlePatch = () => {
            apply()
            resolve(json(body))
          }
        })
      }
      apply()
      return json(body)
    }
    events.push(`get:${userId}`)
    const safeGrants = grantsByUser[userId] ?? []
    return json(options.hostilePayload ? {
      grants: safeGrants.map(grant => ({
        ...grant,
        apiKey: 'sk-never-render-this',
        provider: 'secret-provider',
        authToken: 'auth-never-render-this',
        version: 'private-version',
        model: 'private-model',
        executablePath: '/private/server/path',
      })),
      credential: 'credential-never-render-this',
    } : { grants: safeGrants })
  }))

  const onAuditRefetch = vi.fn(() => {
    events.push('audit')
    if (!options.pendingAudit) return Promise.resolve()
    return new Promise<void>(resolve => { settleAudit = resolve })
  })
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const invalidate = vi.spyOn(client, 'invalidateQueries')
  render(
    <QueryClientProvider client={client}>
      <AiAccessTab users={users} initialUserId={options.initialUserId} onAuditRefetch={onAuditRefetch} />
    </QueryClientProvider>,
  )
  return {
    user: userEvent.setup(),
    calls,
    events,
    client,
    invalidate,
    onAuditRefetch,
    resolvePatch: () => settlePatch?.(),
    resolveAudit: () => settleAudit?.(),
  }
}

afterEach(() => {
  cleanup()
  onlineManager.setOnline(true)
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('AiAccessTab', () => {
  it('opens the exact bookmarked person without reading the default account grants', async () => {
    const { calls } = setup({ initialUserId: 'guest-1' })
    expect(await screen.findByRole('switch', { name: /Biren Sen.*Codex CLI/i })).toBeInTheDocument()
    expect(calls.map(call => call.url)).toEqual(['/api/admin/users/guest-1/ai-cli-grants'])
    expect(screen.getByRole('button', { name: 'Select Biren Sen' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('does not silently select another person for an unknown bookmarked identity', async () => {
    const { calls } = setup({ initialUserId: 'missing-user' })
    expect(screen.getByText('Select a user to manage AI access.')).toBeInTheDocument()
    expect(screen.queryByRole('switch')).toBeNull()
    expect(calls).toEqual([])
  })

  it('shows exactly four independent default-denied switches with coarse host state and no hostile detail', async () => {
    const { calls } = setup({ hostilePayload: true })

    const switches = await screen.findAllByRole('switch')
    expect(switches).toHaveLength(4)
    expect(switches.map(control => control.getAttribute('aria-checked'))).toEqual(['false', 'false', 'false', 'false'])
    expect(switches.map(control => control.getAttribute('type'))).toEqual(['button', 'button', 'button', 'button'])
    expect(screen.getByRole('switch', { name: /Asha Rao.*Codex CLI/i })).toBeEnabled()
    expect(screen.getAllByText('Not granted')).toHaveLength(4)
    expect(screen.getByText('Reachable')).toBeInTheDocument()
    expect(screen.getAllByText('Unavailable')).toHaveLength(3)
    expect(document.body.textContent).not.toMatch(/sk-never|secret-provider|auth-never|private-version|private-model|private\/server|credential-never/i)
    expect(calls.every(call => /^\/api\/admin\/users\/[^/]+\/ai-cli-grants$/.test(call.url))).toBe(true)
  })

  it('uses the exact selected-user query key and never reuses another user grant state', async () => {
    const { user, client } = setup({ grantsByUser: {
      'admin-1': grants({ codex: true }),
      'guest-1': grants(),
      'disabled-1': grants({ claude_code: true }),
    } })

    expect(await screen.findByRole('switch', { name: /Asha Rao.*Codex CLI/i })).toHaveAttribute('aria-checked', 'true')
    await user.click(screen.getByRole('button', { name: /Select Biren Sen/i }))
    expect(await screen.findByRole('switch', { name: /Biren Sen.*Codex CLI/i })).toHaveAttribute('aria-checked', 'false')

    expect(client.getQueryCache().findAll().map(query => query.queryKey)).toEqual(expect.arrayContaining([
      ['admin', 'ai-cli-grants', 'admin-1'],
      ['admin', 'ai-cli-grants', 'guest-1'],
    ]))
  })

  it('grants with an exact PATCH, refetches only the selected grant query, then awaits audit refresh', async () => {
    const { user, calls, events, invalidate, onAuditRefetch, resolveAudit } = setup({ pendingAudit: true })
    const control = await screen.findByRole('switch', { name: /Asha Rao.*Codex CLI/i })

    control.focus()
    await user.keyboard('{Enter}')
    await waitFor(() => expect(control).toHaveAttribute('aria-checked', 'true'))

    const patch = calls.find(call => call.init?.method === 'PATCH')
    expect(patch).toMatchObject({
      url: '/api/admin/users/admin-1/ai-cli-grants',
      init: { method: 'PATCH', headers: { 'Content-Type': 'application/json' } },
    })
    expect(JSON.parse(String(patch?.init?.body))).toEqual({ cliId: 'codex', granted: true })
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['admin', 'ai-cli-grants', 'admin-1'],
      exact: true,
      refetchType: 'active',
    })
    expect(events).toEqual(['get:admin-1', 'patch:admin-1', 'get:admin-1', 'audit'])
    expect(onAuditRefetch).toHaveBeenCalledTimes(1)
    expect(control).toBeDisabled()

    resolveAudit()
    await waitFor(() => expect(control).toBeEnabled())
  })

  it('keeps prior state and exposes only a generic safe error when a grant fails', async () => {
    const { user, onAuditRefetch } = setup({ failPatch: true })
    const control = await screen.findByRole('switch', { name: /Asha Rao.*Codex CLI/i })

    await user.click(control)

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not update AI access. Try again.')
    expect(control).toHaveAttribute('aria-checked', 'false')
    expect(document.body.textContent).not.toMatch(/sk-hostile|provider-error|500/i)
    expect(onAuditRefetch).not.toHaveBeenCalled()
  })

  it('freezes the exact revoke target, cancels without a request, and disables controls while confirming', async () => {
    const { user, calls, resolvePatch } = setup({
      grantsByUser: {
        'admin-1': grants({ claude_code: true }),
        'guest-1': grants(),
        'disabled-1': grants({ claude_code: true }),
      },
      pendingPatch: true,
    })
    const control = await screen.findByRole('switch', { name: /Asha Rao.*Claude Code/i })

    await user.click(control)
    let dialog = screen.getByRole('dialog')
    expect(dialog).toHaveTextContent('Revoke Claude Code for Asha Rao?')
    expect(dialog).toHaveTextContent('The next invocation will be blocked.')
    await user.click(within(dialog).getByRole('button', { name: 'Cancel' }))
    expect(calls.filter(call => call.init?.method === 'PATCH')).toHaveLength(0)
    await waitFor(() => expect(control).toHaveFocus())

    await user.click(control)
    dialog = screen.getByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: 'Revoke access' }))
    expect(screen.getAllByRole('switch', { hidden: true }).every(button => (button as HTMLButtonElement).disabled)).toBe(true)
    expect(JSON.parse(String(calls.find(call => call.init?.method === 'PATCH')?.init?.body))).toEqual({
      cliId: 'claude_code',
      granted: false,
    })

    resolvePatch()
    await waitFor(() => expect(control).toHaveAttribute('aria-checked', 'false'))
  })

  it('closes a failed revoke confirmation so its generic error is perceivable', async () => {
    const { user } = setup({
      grantsByUser: {
        'admin-1': grants({ claude_code: true }),
        'guest-1': grants(),
        'disabled-1': grants({ claude_code: true }),
      },
      failPatch: true,
    })
    const control = await screen.findByRole('switch', { name: /Asha Rao.*Claude Code/i })

    await user.click(control)
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Revoke access' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(screen.getByRole('alert')).toHaveTextContent('Could not update AI access. Try again.')
    expect(control).toHaveAttribute('aria-checked', 'true')
  })

  it('blocks new grants for an inactive user while preserving existing revoke authority', async () => {
    const { user } = setup()
    await screen.findByRole('switch', { name: /Asha Rao.*Codex CLI/i })

    await user.click(screen.getByRole('button', { name: /Select Chitra Das/i }))

    expect(await screen.findByRole('switch', { name: /Chitra Das.*Codex CLI/i })).toBeDisabled()
    expect(screen.getByRole('switch', { name: /Chitra Das.*Claude Code/i })).toBeEnabled()
    expect(screen.getByText(/Inactive users cannot receive new CLI grants/i)).toBeInTheDocument()
  })
})
