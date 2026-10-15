/**
 * SS N-379 (iv) — the login page honours a SAFE `next` after a successful sign-in.
 * The raw value is never trusted: it goes through safeNextPath at the point of the
 * final navigation; a bad value falls back to the default page (/dashboard).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import React from 'react'

const pushMock = vi.fn()
const refreshMock = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock, refresh: refreshMock, replace: vi.fn() }),
}))
vi.mock('next/link', () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}))
vi.mock('@/lib/firebase/client', () => ({ auth: { signOut: vi.fn(async () => {}) } }))
vi.mock('firebase/auth', () => ({
  signInWithEmailAndPassword: vi.fn(async () => ({ user: { getIdToken: async () => 'id-token' } })),
}))

import LoginPage from '../page'

function setLocationSearch(search: string) {
  window.history.pushState({}, '', `/login${search}`)
}

async function signIn(sessionBody: Record<string, unknown> = {}) {
  global.fetch = vi.fn(async (url: string) => {
    if (url === '/api/auth/session') return { ok: true, json: async () => sessionBody } as Response
    return { ok: false, json: async () => ({}) } as Response
  }) as unknown as typeof fetch
  render(<LoginPage />)
  fireEvent.click(screen.getByRole('button', { name: 'Email' }))
  fireEvent.change(document.querySelector('input[type="email"]') as HTMLInputElement, {
    target: { value: 'a@b.co' },
  })
  fireEvent.change(document.querySelector('input[type="password"]') as HTMLInputElement, {
    target: { value: 'pw-pw-pw-pw' },
  })
  await act(async () => {
    fireEvent.submit(document.querySelector('form') as HTMLFormElement)
  })
  await act(async () => {})
}

beforeEach(() => {
  pushMock.mockClear()
  refreshMock.mockClear()
})
afterEach(() => {
  cleanup()
  window.history.pushState({}, '', '/')
})

describe('login redirect after sign-in honours only a safe next', () => {
  it('a good next (/share/<slug>) is navigated to', async () => {
    setLocationSearch(`?next=${encodeURIComponent('/share/AbC123xyz0')}`)
    await signIn()
    expect(pushMock).toHaveBeenCalledTimes(1)
    expect(pushMock).toHaveBeenCalledWith('/share/AbC123xyz0')
  })

  it('a good /clients/ next is navigated to', async () => {
    setLocationSearch(`?next=${encodeURIComponent('/clients/abc-123/edit')}`)
    await signIn()
    expect(pushMock).toHaveBeenCalledWith('/clients/abc-123/edit')
  })

  it.each([
    '//evil.com',
    '/\\evil.com',
    'https://evil.com',
    'javascript:alert(1)',
    '/%2Fevil.com',
    '/share/../evil',
    '/dashboard',
    '',
  ])('a bad next (%s) falls back to /dashboard', async (bad) => {
    setLocationSearch(`?next=${encodeURIComponent(bad)}`)
    await signIn()
    expect(pushMock).toHaveBeenCalledTimes(1)
    expect(pushMock).toHaveBeenCalledWith('/dashboard')
  })

  it('no next -> /dashboard', async () => {
    setLocationSearch('')
    await signIn()
    expect(pushMock).toHaveBeenCalledWith('/dashboard')
  })

  it('a raw (unencoded) hostile next never reaches the router', async () => {
    setLocationSearch('?next=//evil.com/share/x')
    await signIn()
    expect(pushMock).not.toHaveBeenCalledWith(expect.stringContaining('evil.com'))
    expect(pushMock).toHaveBeenCalledWith('/dashboard')
  })

  it('username setup still takes precedence over next', async () => {
    setLocationSearch(`?next=${encodeURIComponent('/share/AbC123xyz0')}`)
    await signIn({ username_setup_required: true })
    expect(pushMock).toHaveBeenCalledWith('/setup-account')
  })
})
