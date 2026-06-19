import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('server-only', () => ({}))

vi.mock('@/lib/config', () => ({
  getFlag: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({
  getServerUserWithProfile: vi.fn(),
}))

import { getFlag } from '@/lib/config'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AuthGate } from '../AuthGate'
import * as ObservatoryClient from '@/lib/api-clients/observatory'
import type { SummaryResponse } from '@/lib/observatory/types'

async function renderAsync(node: Promise<React.ReactElement>) {
  const resolved = await node
  return render(resolved)
}

describe('AuthGate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the disabled message when the flag is off; children not rendered', async () => {
    vi.mocked(getFlag).mockReturnValue(false)
    await renderAsync(
      AuthGate({ children: <span data-testid="protected-child" /> }) as Promise<React.ReactElement>,
    )
    expect(screen.getByTestId('observatory-disabled')).toBeInTheDocument()
    expect(screen.getByText(/Observatory is disabled/i)).toBeInTheDocument()
    expect(screen.queryByTestId('protected-child')).not.toBeInTheDocument()
    expect(getServerUserWithProfile).not.toHaveBeenCalled()
  })

  it('renders Unauthorized when the flag is on but the user is not super-admin', async () => {
    vi.mocked(getFlag).mockReturnValue(true)
    vi.mocked(getServerUserWithProfile).mockResolvedValue({
      user: { uid: 'u1' } as never,
      profile: { id: 'u1', role: 'guest', status: 'active' },
    })
    await renderAsync(
      AuthGate({ children: <span data-testid="protected-child" /> }) as Promise<React.ReactElement>,
    )
    expect(screen.getByTestId('observatory-unauthorized')).toBeInTheDocument()
    expect(screen.getByText(/Unauthorized/i)).toBeInTheDocument()
    expect(screen.queryByTestId('protected-child')).not.toBeInTheDocument()
  })

  it('renders Unauthorized when the flag is on and there is no authenticated user', async () => {
    vi.mocked(getFlag).mockReturnValue(true)
    vi.mocked(getServerUserWithProfile).mockResolvedValue(null)
    await renderAsync(
      AuthGate({ children: <span data-testid="protected-child" /> }) as Promise<React.ReactElement>,
    )
    expect(screen.getByTestId('observatory-unauthorized')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-child')).not.toBeInTheDocument()
  })

  it('renders children when the flag is on and the user is an active super-admin', async () => {
    vi.mocked(getFlag).mockReturnValue(true)
    vi.mocked(getServerUserWithProfile).mockResolvedValue({
      user: { uid: 'admin-1' } as never,
      profile: { id: 'admin-1', role: 'super_admin', status: 'active' },
    })
    await renderAsync(
      AuthGate({ children: <span data-testid="protected-child">ok</span> }) as Promise<React.ReactElement>,
    )
    expect(screen.getByTestId('protected-child')).toBeInTheDocument()
    expect(screen.queryByTestId('observatory-disabled')).not.toBeInTheDocument()
    expect(screen.queryByTestId('observatory-unauthorized')).not.toBeInTheDocument()
  })
})

// Compile-time-only verification: the typed API client's getSummary returns
// a value assignable to SummaryResponse. This is a no-op at runtime but
// fails the build if the client drifts from the openapi.yaml types.
describe('Observatory API client (compile-time types)', () => {
  it('getSummary returns Promise<SummaryResponse>', () => {
    const _check: (
      params: Parameters<typeof ObservatoryClient.getSummary>[0],
    ) => Promise<SummaryResponse> = ObservatoryClient.getSummary
    expect(typeof _check).toBe('function')
  })
})
