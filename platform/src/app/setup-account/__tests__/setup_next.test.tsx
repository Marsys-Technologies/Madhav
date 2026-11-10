import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'

const { getProfile, query, push } = vi.hoisted(() => ({
  getProfile: vi.fn(),
  query: vi.fn(),
  push: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: getProfile }))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('next/navigation', () => ({
  redirect: (path: string) => { throw new Error(`REDIRECT:${path}`) },
  useRouter: () => ({ push, refresh: vi.fn() }),
}))

import SetupPage from '../page'

const destination = '/clients/chart-123/edit'

beforeEach(() => {
  vi.clearAllMocks()
  getProfile.mockResolvedValue({ user: { uid: 'test-user' }, profile: { status: 'active' } })
  query.mockResolvedValue({ rows: [{ username: null, email: 'test@example.test' }] })
})
afterEach(() => vi.unstubAllGlobals())

function openSetup(next?: string | string[]) {
  return SetupPage({ searchParams: Promise.resolve({ next }) })
}

describe('username setup return', () => {
  it.each([
    { next: destination, expected: destination },
    { next: '//example.test', expected: '/dashboard' },
    { next: [destination, '/share/AbC123xyz0'], expected: '/dashboard' },
  ])('continues to $expected after saving the username with next=$next', async ({ next, expected }) => {
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) =>
      Response.json(init?.method === 'PATCH' ? { ok: true } : { available: true }),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(await openSetup(next))
    fireEvent.change(screen.getByRole('textbox', { name: 'Username' }), { target: { value: 'reader-one' } })
    await screen.findByText('Available')
    expect(push).not.toHaveBeenCalled()
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Save username and continue' }))
    })
    expect(push).toHaveBeenCalledWith(expected)
  })

  it('carries the safe destination back to sign-in if the session expires during setup', async () => {
    getProfile.mockResolvedValue(null)
    await expect(openSetup(destination)).rejects.toThrow('REDIRECT:/login?setup=1&next=%2Fclients%2Fchart-123%2Fedit')
  })
})
