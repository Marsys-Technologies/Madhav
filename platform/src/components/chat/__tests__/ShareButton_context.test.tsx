import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, onTestFinished, vi } from 'vitest'
import { ShareButton } from '../ShareButton'

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (error: Error) => void
  const promise = new Promise<T>((accept, refuse) => { resolve = accept; reject = refuse })
  return { promise, resolve, reject }
}

interface Pending {
  url: string
  init: RequestInit
  reply: ReturnType<typeof deferred<Response>>
}

function mockRequests() {
  const requests: Pending[] = []
  vi.stubGlobal('fetch', vi.fn((url: string, init: RequestInit = {}) => {
    const reply = deferred<Response>()
    requests.push({ url, init, reply })
    // Deliberately allow the transport to finish even after abort.
    return reply.promise
  }))
  return (id: string, method = 'GET', index = 0) => {
    const matches = requests.filter(({ url, init }) =>
      url === `/api/conversations/${id}/share` && (init.method ?? 'GET') === method)
    expect(matches[index]).toBeDefined()
    return matches[index]
  }
}

async function answer(request: Pending, response: Response) {
  await act(async () => request.reply.resolve(response))
}

function share(slug: string | null) {
  return Response.json({ share: slug ? { slug } : null })
}

function url(slug: string) {
  return `${window.location.origin}/share/${slug}`
}

async function toggleShare() {
  await act(async () => screen.getByRole('button', { name: 'Share conversation' }).click())
}

function create() {
  return screen.getByRole('button', { name: 'Create share link' })
}

function confirmRevoke() {
  fireEvent.click(screen.getByRole('button', { name: 'Revoke link' }))
  return screen.getByRole('button', { name: 'Revoke' })
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('ShareButton conversation context', () => {
  it('keeps B’s link when an aborted A GET finishes after B', async () => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    const a = request('a')
    view.rerender(<ShareButton conversationId="b" />)
    const b = request('b')
    await answer(b, share('B-new-link'))
    await answer(a, share('A-old-link'))
    expect(screen.getByText(url('B-new-link'))).toBeInTheDocument()
    expect(screen.queryByText(url('A-old-link'))).toBeNull()
    expect(a.init.signal?.aborted).toBe(true)
    expect(b.init.cache).toBe('no-store')
  })

  it('removes A’s link and confirmation immediately, including when B GET fails', async () => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share('A-visible-link'))
    confirmRevoke()
    view.rerender(<ShareButton conversationId="b" />)
    expect(screen.queryByText(url('A-visible-link'))).toBeNull()
    expect(screen.queryByRole('button', { name: 'Revoke' })).toBeNull()
    await answer(request('b'), new Response(null, { status: 503 }))
    expect(screen.queryByText(url('A-visible-link'))).toBeNull()
    expect(create()).toBeEnabled()
  })

  it('distinguishes two A visits with B in between, including a body decoded late', async () => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    const original = request('a')
    const body = deferred<{ share: { slug: string } }>()
    const oldResponse = share('unused')
    const json = vi.spyOn(oldResponse, 'json').mockReturnValue(body.promise)
    await answer(original, oldResponse)
    expect(json).toHaveBeenCalledOnce()

    view.rerender(<ShareButton conversationId="b" />)
    const b = request('b')
    view.rerender(<ShareButton conversationId="a" />)
    await answer(request('a', 'GET', 1), share('A-second-visit'))
    await answer(b, share('B-abandoned'))
    await act(async () => body.resolve({ share: { slug: 'A-first-visit' } }))

    expect(screen.getByText(url('A-second-visit'))).toBeInTheDocument()
    expect(screen.queryByText(url('A-first-visit'))).toBeNull()
    expect(original.init.signal?.aborted).toBe(true)
    expect(b.init.signal?.aborted).toBe(true)
  })

  it('ignores A POST and keeps B’s own create operation pending', async () => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share(null))
    fireEvent.click(create())
    const a = request('a', 'POST')

    view.rerender(<ShareButton conversationId="b" />)
    await answer(request('b'), Response.json({ share: null, selective_share_enabled: false }))
    expect(create()).toBeEnabled()
    fireEvent.click(create())
    const b = request('b', 'POST')
    expect(JSON.parse(String(a.init.body))).toEqual({ hide_reasoning: false, hide_methodology: false })
    expect(JSON.parse(String(b.init.body))).toEqual({})
    await answer(a, Response.json({ slug: 'A-created' }))
    expect(screen.queryByText(url('A-created'))).toBeNull()
    expect(create()).toBeDisabled()
    expect(a.init.signal?.aborted).toBe(true)

    await answer(b, Response.json({ slug: 'B-created' }))
    expect(screen.getByText(url('B-created'))).toBeInTheDocument()
  })

  it('keeps B’s link when A POST finishes after the switch', async () => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share(null))
    fireEvent.click(create())
    const a = request('a', 'POST')
    view.rerender(<ShareButton conversationId="b" />)
    await answer(request('b'), share('B-existing'))
    await answer(a, Response.json({ slug: 'A-created-late' }))
    expect(screen.getByText(url('B-existing'))).toBeInTheDocument()
    expect(screen.queryByText(url('A-created-late'))).toBeNull()
  })

  it.each([204, 503, 'network'])('ignores a late A DELETE %s without clearing B’s link or confirmation', async status => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share('A-before-delete'))
    fireEvent.click(confirmRevoke())
    const a = request('a', 'DELETE')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    view.rerender(<ShareButton conversationId="b" />)
    await answer(request('b'), share('B-not-revoked'))
    const bConfirm = confirmRevoke()
    if (typeof status === 'number') await answer(a, new Response(null, { status }))
    else await act(async () => a.reply.reject(new Error('fixture network failure')))
    expect(screen.getByText(url('B-not-revoked'))).toBeInTheDocument()
    expect(bConfirm).toBeInTheDocument()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(a.init.signal?.aborted).toBe(true)
  })

  it('keeps a new link when its older GET completes after POST', async () => {
    const request = mockRequests()
    render(<ShareButton conversationId="a" />)
    await toggleShare()
    const read = request('a')
    fireEvent.click(create())
    await answer(request('a', 'POST'), Response.json({ slug: 'A-just-created' }))
    await answer(read, share(null))
    expect(screen.getByText(url('A-just-created'))).toBeInTheDocument()
    expect(read.init.signal?.aborted).toBe(true)
  })

  it('does not restore a revoked link from an older refresh in the same conversation', async () => {
    const request = mockRequests()
    render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share('A-to-revoke'))
    await toggleShare()
    await toggleShare()
    const refresh = request('a', 'GET', 1)
    fireEvent.click(confirmRevoke())
    await answer(request('a', 'DELETE'), new Response(null, { status: 204 }))
    await answer(refresh, share('A-to-revoke'))
    expect(screen.queryByText(url('A-to-revoke'))).toBeNull()
    expect(create()).toBeEnabled()
    expect(refresh.init.signal?.aborted).toBe(true)
  })

  it('can retry a failed current create using the same explicit options', async () => {
    const request = mockRequests()
    render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share(null))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Show reasoning' }))
    fireEvent.click(create())
    const failed = request('a', 'POST')
    await answer(failed, new Response(null, { status: 503 }))
    expect(create()).toBeEnabled()
    fireEvent.click(create())
    const retried = request('a', 'POST', 1)
    expect(JSON.parse(String(failed.init.body))).toEqual({ hide_reasoning: true, hide_methodology: false })
    expect(retried.init.body).toBe(failed.init.body)
    await answer(retried, Response.json({ slug: 'A-retry-created' }))
    expect(screen.getByText(url('A-retry-created'))).toBeInTheDocument()
  })

  it('keeps pending clipboard feedback scoped to the copied link', async () => {
    const request = mockRequests()
    const copy = deferred<void>()
    const writeText = vi.fn().mockImplementationOnce(() => copy.promise).mockResolvedValue(undefined)
    const original = Object.getOwnPropertyDescriptor(window.navigator, 'clipboard')
    Object.defineProperty(window.navigator, 'clipboard', { configurable: true, value: { writeText } })
    onTestFinished(() => {
      if (original) Object.defineProperty(window.navigator, 'clipboard', original)
      else Reflect.deleteProperty(window.navigator, 'clipboard')
    })
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    await answer(request('a'), share('A-copied'))
    fireEvent.click(screen.getByRole('button', { name: 'Copy link' }))
    expect(writeText).toHaveBeenCalledWith(url('A-copied'))

    view.rerender(<ShareButton conversationId="b" />)
    await answer(request('b'), share('B-current'))
    await act(async () => copy.resolve(undefined))
    expect(screen.queryByRole('button', { name: 'Copied' })).toBeNull()
    await act(async () => screen.getByRole('button', { name: 'Copy link' }).click())
    expect(writeText).toHaveBeenLastCalledWith(url('B-current'))
    expect(screen.getByRole('button', { name: 'Copied' })).toBeInTheDocument()
  })

  it.each(['GET', 'POST', 'DELETE'])('aborts a pending %s when the button unmounts', async method => {
    const request = mockRequests()
    const view = render(<ShareButton conversationId="a" />)
    await toggleShare()
    if (method === 'POST') {
      await answer(request('a'), share(null))
      fireEvent.click(create())
    } else if (method === 'DELETE') {
      await answer(request('a'), share('A-before-unmount'))
      fireEvent.click(confirmRevoke())
    }
    const pending = request('a', method)
    view.unmount()
    expect(pending.init.signal?.aborted).toBe(true)
    await answer(pending, method === 'DELETE' ? new Response(null, { status: 204 }) : share('late'))
  })
})
