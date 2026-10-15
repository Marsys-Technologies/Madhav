/**
 * SS N-376 / PR-S4 — the ShareButton must not promise a public link: share links
 * are authenticated by design (viewer needs a MARSYS-JIS sign-in) and expire.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, render } from '@testing-library/react'
import React from 'react'
import { ShareButton } from '../ShareButton'
import { SHARE_DEFAULT_TTL_DAYS } from '@/lib/share/constants'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('ShareButton copy tells the truth about who can open the link', () => {
  it('says signed-in users and the expiry, not "anyone with the link"', async () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ share: null }) }) as any
    render(<ShareButton conversationId="conv-1" />)
    await act(async () => {
      ;(document.querySelector('[aria-label="Share conversation"]') as HTMLElement).click()
    })
    await act(async () => {})
    const text = document.body.textContent ?? ''
    expect(text).not.toMatch(/Anyone with the link/i)
    expect(text).toMatch(/signed[- ]in/i)
    expect(text).toContain(`${SHARE_DEFAULT_TTL_DAYS} days`)
  })
})
