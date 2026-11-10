import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { McpKeysClient } from '../McpKeysClient'

vi.mock('@/components/observatory/ObservatoryScope', () => ({
  useObservatoryScope: () => ({ userId: 'fixture-admin', users: [] }),
}))

const clipboard = Object.getOwnPropertyDescriptor(navigator, 'clipboard')

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  if (clipboard) Object.defineProperty(navigator, 'clipboard', clipboard)
  else Reflect.deleteProperty(navigator, 'clipboard')
})

function renderKeys() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={queryClient}><McpKeysClient /></QueryClientProvider>)
}

it('lets the operator recover the one-time value when clipboard access fails', async () => {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init?: RequestInit) => {
    if (init?.method === 'POST') return Response.json({
      key_id: 'fixture-id', full_key: 'local-test-placeholder', label: null, user_uid: 'fixture-admin',
    })
    return Response.json({ keys: [] })
  }))
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: vi.fn().mockRejectedValue(new Error('permission denied')) },
  })
  renderKeys()
  fireEvent.click(screen.getByRole('button', { name: 'Create new key' }))
  fireEvent.click(screen.getByRole('button', { name: 'Create key' }))

  const dialog = await screen.findByRole('dialog')
  fireEvent.click(within(dialog).getByRole('button', { name: 'Copy' }))
  expect(await within(dialog).findByRole('alert')).toHaveTextContent('Copy the key manually')
  expect(dialog).toHaveAccessibleName(/Key created/)
  expect(within(dialog).getByRole('textbox', { name: 'MCP API key' })).toHaveValue('local-test-placeholder')
})

it('labels the optional field and lets the operator retry a failed key list read', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(new Response(null, { status: 503 }))
    .mockResolvedValueOnce(Response.json({ keys: [] }))
  vi.stubGlobal('fetch', fetch)
  renderKeys()
  fireEvent.click(screen.getByRole('button', { name: 'Create new key' }))
  expect(screen.getByRole('textbox', { name: 'Label (optional)' })).toBeInTheDocument()

  const failure = await screen.findByRole('alert')
  fireEvent.click(within(failure).getByRole('button', { name: 'Try again' }))
  expect(await screen.findByText('No keys yet. Create one above.')).toBeInTheDocument()
  expect(fetch).toHaveBeenCalledTimes(2)
})
