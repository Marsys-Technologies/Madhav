/**
 * SS N-379 (v) — R10_SELECTIVE_SHARE only controls whether the hide options are
 * OFFERED on a NEW share: the dialog shows the two checkboxes only while the GET
 * reports selective_share_enabled !== false, and posts no hide fields otherwise.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, render } from '@testing-library/react'
import React from 'react'
import { ShareButton } from '../ShareButton'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

async function open(getBody: Record<string, unknown>) {
  const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
    if (init?.method === 'POST') return { ok: true, json: async () => ({ slug: 'AbC123xyz0' }) }
    return { ok: true, json: async () => getBody }
  })
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  global.fetch = fetchMock as any
  render(<ShareButton conversationId="conv-1" />)
  await act(async () => {
    ;(document.querySelector('[aria-label="Share conversation"]') as HTMLElement).click()
  })
  await act(async () => {})
  return fetchMock
}

describe('selective-share options are offered only while the flag is on', () => {
  it('flag on: both checkboxes are offered and the POST carries the hide fields', async () => {
    const fetchMock = await open({ share: null, selective_share_enabled: true })
    expect(document.querySelector('[data-testid="v2-share-show-reasoning"]')).not.toBeNull()
    expect(document.querySelector('[data-testid="v2-share-show-methodology"]')).not.toBeNull()
    await act(async () => {
      ;(document.querySelector('[data-testid="v2-share-create-btn"]') as HTMLElement).click()
    })
    const post = fetchMock.mock.calls.find(([, i]) => i?.method === 'POST')!
    expect(JSON.parse(String(post[1]!.body))).toEqual({ hide_reasoning: false, hide_methodology: false })
  })

  it('flag off: no checkboxes, and the POST carries no hide fields', async () => {
    const fetchMock = await open({ share: null, selective_share_enabled: false })
    expect(document.querySelector('[data-testid="v2-share-show-reasoning"]')).toBeNull()
    expect(document.querySelector('[data-testid="v2-share-show-methodology"]')).toBeNull()
    await act(async () => {
      ;(document.querySelector('[data-testid="v2-share-create-btn"]') as HTMLElement).click()
    })
    const post = fetchMock.mock.calls.find(([, i]) => i?.method === 'POST')!
    expect(JSON.parse(String(post[1]!.body))).toEqual({})
  })

  it('an older server that does not report the flag keeps offering the options', async () => {
    await open({ share: null })
    expect(document.querySelector('[data-testid="v2-share-show-reasoning"]')).not.toBeNull()
  })
})
