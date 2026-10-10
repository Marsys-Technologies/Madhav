/**
 * SS N-376 / PR-S4 — the share PAGE is authenticated by design.
 *
 *  1. The page verifies a real session itself (getServerUser -> firebase-admin
 *     verifySessionCookie with revocation check) BEFORE any share/conversation/
 *     chart/message read. proxy.ts only checks the cookie's SHAPE, so a forged
 *     cookie used to reach this page with no check of its own.
 *  4. The charts SELECT no longer reads birth_date / birth_place (unused).
 *  3. The page exports noindex / nofollow / no-referrer metadata.
 *  5. Selective share is honoured BY DEFAULT and the hidden sections are really
 *     absent: not in the rendered DOM and not in the element props the server
 *     component hands to the client component (the RSC payload).
 *
 * Every test here fails against the pre-PR page.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render } from '@testing-library/react'
import React from 'react'

vi.mock('server-only', () => ({}))

class RedirectError extends Error {
  constructor(public readonly url: string) {
    super(`NEXT_REDIRECT:${url}`)
  }
}
class NotFoundError extends Error {
  constructor() {
    super('NEXT_NOT_FOUND')
  }
}
const redirectMock = vi.fn((url: string) => {
  throw new RedirectError(url)
})
const notFoundMock = vi.fn(() => {
  throw new NotFoundError()
})
vi.mock('next/navigation', () => ({
  redirect: (url: string) => redirectMock(url),
  notFound: () => notFoundMock(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
  usePathname: () => '/share/slug',
  useSearchParams: () => new URLSearchParams(),
}))

const getServerUserMock = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: () => getServerUserMock() }))

const callLog: string[] = []
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (sql: string, params?: unknown[]) => queryMock(sql, params),
}))

const loadMessagesMock = vi.fn()
vi.mock('@/lib/persistence/conversation_writer', () => ({
  loadConversationMessagesV2: (id: string) => loadMessagesMock(id),
}))

const REASONING_TEXT = 'SECRET_REASONING_CHAIN_alpha'
const METHODOLOGY_TEXT = 'SECRET_METHODOLOGY_BLOCK_beta'
const VISIBLE_ANSWER = 'The visible answer about Saturn.'

function conversationMessages() {
  return [
    { id: 'u1', role: 'user', parts: [{ type: 'text', text: 'What about Saturn?' }], metadata: {} },
    {
      id: 'a1',
      role: 'assistant',
      parts: [
        { type: 'reasoning', text: REASONING_TEXT },
        {
          type: 'text',
          text:
            `${VISIBLE_ANSWER}\n\n` +
            '```marsys_methodology_block\n' +
            `${METHODOLOGY_TEXT}\n` +
            '```\n',
        },
      ],
      metadata: { methodology_block: METHODOLOGY_TEXT },
    },
  ]
}

interface Setup {
  user?: { uid: string } | null
  profile?: { id: string; role: string; status: string } | null
  share?: Record<string, unknown> | null
}

function setup({ user = { uid: 'viewer-1' }, profile, share }: Setup = {}) {
  getServerUserMock.mockImplementation(async () => {
    callLog.push('getServerUser')
    return user
  })
  const prof = profile === undefined ? { id: 'viewer-1', role: 'guest', status: 'active' } : profile
  const shareRow =
    share === undefined
      ? {
          conversation_id: 'conv-1',
          revoked_at: null,
          expires_at: null,
          hide_reasoning: false,
          hide_methodology: false,
        }
      : share
  queryMock.mockImplementation(async (sql: string) => {
    callLog.push(`query:${sql.slice(0, 60)}`)
    if (/FROM profiles/i.test(sql)) return { rows: prof ? [prof] : [] }
    if (/FROM conversation_shares/i.test(sql)) return { rows: shareRow ? [shareRow] : [] }
    if (/FROM conversations/i.test(sql))
      return { rows: [{ id: 'conv-1', title: 'My chat', chart_id: 'chart-1', created_at: 't' }] }
    if (/FROM charts/i.test(sql)) return { rows: [{ name: 'Chart Name' }] }
    return { rows: [] }
  })
  loadMessagesMock.mockImplementation(async () => {
    callLog.push('loadMessages')
    return conversationMessages()
  })
}


/**
 * Serialize what a server component hands to the client: the element tree's
 * PROPS (what the RSC payload carries). Element `type`s are skipped (they are
 * module references, not data).
 */
function serializeProps(node: unknown): string {
  const walk = (n: unknown): unknown => {
    if (n === null || typeof n !== 'object') return typeof n === 'function' ? undefined : n
    if (Array.isArray(n)) return n.map(walk)
    const rec = n as Record<string, unknown>
    if ('$$typeof' in rec) return { props: walk(rec.props) }
    return Object.fromEntries(Object.entries(rec).map(([k, v]) => [k, walk(v)]))
  }
  return JSON.stringify(walk(node))
}

async function importPage() {
  vi.resetModules()
  return await import('../page')
}

async function renderPage(slug = 'abc1234567') {
  const mod = await importPage()
  return mod.default({ params: Promise.resolve({ slug }) })
}

function shareReadsCount() {
  return queryMock.mock.calls.filter(([sql]) =>
    /FROM (conversation_shares|conversations|charts)/i.test(String(sql)),
  ).length
}

beforeEach(() => {
  callLog.length = 0
  for (const m of [redirectMock, notFoundMock, getServerUserMock, queryMock, loadMessagesMock]) m.mockClear()
  delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
})
afterEach(() => {
  cleanup()
  delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
})

describe('share page requires a verified, active session (item 1)', () => {
  it('no verified session -> redirect to /login and NO share/conversation/chart/message read', async () => {
    setup({ user: null })
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/login')
    expect(redirectMock).toHaveBeenCalledWith('/login')
    expect(shareReadsCount()).toBe(0)
    expect(loadMessagesMock).not.toHaveBeenCalled()
  })

  it('verified user whose profile is missing -> redirect, no data read', async () => {
    setup({ profile: null })
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/login')
    expect(shareReadsCount()).toBe(0)
    expect(loadMessagesMock).not.toHaveBeenCalled()
  })

  it.each(['pending', 'disabled'])('profile status %s is refused like elsewhere', async (status) => {
    setup({ profile: { id: 'viewer-1', role: 'guest', status } })
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/login')
    expect(shareReadsCount()).toBe(0)
    expect(loadMessagesMock).not.toHaveBeenCalled()
  })

  it('session is verified BEFORE the first share/conversation read', async () => {
    setup()
    await renderPage()
    const firstUser = callLog.indexOf('getServerUser')
    const firstShareRead = callLog.findIndex((c) => /FROM (conversation_shares|conversations|charts)/i.test(c))
    expect(firstUser).toBeGreaterThanOrEqual(0)
    expect(firstShareRead).toBeGreaterThan(firstUser)
  })

  it('any verified ACTIVE user holding the slug can view (no owner check)', async () => {
    setup({ user: { uid: 'someone-else' }, profile: { id: 'someone-else', role: 'guest', status: 'active' } })
    const el = await renderPage()
    expect(el).toBeTruthy()
    expect(redirectMock).not.toHaveBeenCalled()
    expect(notFoundMock).not.toHaveBeenCalled()
  })

  it('a non-matching / revoked / expired slug stays notFound() once authenticated', async () => {
    setup({ share: null })
    await expect(renderPage('nope')).rejects.toThrow('NEXT_NOT_FOUND')
    expect(redirectMock).not.toHaveBeenCalled()
  })

  it('the share lookup filters revoked and expired rows in SQL', async () => {
    setup()
    await renderPage()
    const sql = String(queryMock.mock.calls.find(([s]) => /FROM conversation_shares/i.test(String(s)))![0])
    expect(sql).toMatch(/revoked_at IS NULL/)
    expect(sql).toMatch(/expires_at IS NULL OR expires_at > now\(\)/)
  })
})

describe('charts SELECT (item 4)', () => {
  it('reads only the name — birth_date / birth_place are no longer queried', async () => {
    setup()
    await renderPage()
    const chartSql = String(queryMock.mock.calls.find(([s]) => /FROM charts/i.test(String(s)))![0])
    expect(chartSql).toMatch(/SELECT\s+name\s+FROM charts/i)
    expect(chartSql).not.toMatch(/birth_date/)
    expect(chartSql).not.toMatch(/birth_place/)
  })
})

describe('noindex / no-referrer metadata (item 3)', () => {
  it('exports robots noindex+nofollow and referrer no-referrer', async () => {
    const mod = await importPage()
    const md = (mod as unknown as { metadata?: Record<string, unknown> }).metadata
    expect(md).toBeDefined()
    expect(md!.robots).toMatchObject({ index: false, follow: false })
    expect(md!.referrer).toBe('no-referrer')
  })
})

describe('selective share is honoured by default (item 5)', () => {
  const shareHiding = (hide_reasoning: boolean, hide_methodology: boolean) => ({
    conversation_id: 'conv-1',
    revoked_at: null,
    expires_at: null,
    hide_reasoning,
    hide_methodology,
  })

  it('hide_reasoning + hide_methodology: neither secret is in the rendered DOM, visible answer remains', async () => {
    setup({ share: shareHiding(true, true) })
    const el = await renderPage()
    const { container } = render(el as React.ReactElement)
    const html = container.innerHTML
    expect(html).toContain(VISIBLE_ANSWER)
    expect(html).not.toContain(REASONING_TEXT)
    expect(html).not.toContain(METHODOLOGY_TEXT)
    expect(html).not.toContain('marsys_methodology_block')
    expect(container.textContent).not.toContain(REASONING_TEXT)
  })

  it('hidden sections are not in the props handed to the client component (RSC payload)', async () => {
    setup({ share: shareHiding(true, true) })
    const el = await renderPage()
    const serialized = serializeProps(el)
    expect(serialized).toContain(VISIBLE_ANSWER)
    expect(serialized).not.toContain(REASONING_TEXT)
    expect(serialized).not.toContain(METHODOLOGY_TEXT)
  })

  it('only reasoning hidden: reasoning gone, methodology text untouched', async () => {
    setup({ share: shareHiding(true, false) })
    const el = await renderPage()
    const serialized = serializeProps(el)
    expect(serialized).not.toContain(REASONING_TEXT)
    expect(serialized).toContain(METHODOLOGY_TEXT)
  })

  it('only methodology hidden: methodology gone, reasoning part kept', async () => {
    setup({ share: shareHiding(false, true) })
    const el = await renderPage()
    const serialized = serializeProps(el)
    expect(serialized).not.toContain(METHODOLOGY_TEXT)
    expect(serialized).toContain(REASONING_TEXT)
  })

  it('nothing hidden: everything present in the DOM data (reasoning is in the DOM)', async () => {
    setup({ share: shareHiding(false, false) })
    const el = await renderPage()
    const { container } = render(el as React.ReactElement)
    expect(container.innerHTML).toContain(REASONING_TEXT)
    expect(serializeProps(el)).toContain(METHODOLOGY_TEXT)
  })

  it('MARSYS_FLAG_R10_SELECTIVE_SHARE=false is the single off switch', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    setup({ share: shareHiding(true, true) })
    const el = await renderPage()
    expect(serializeProps(el)).toContain(REASONING_TEXT)
  })
})
