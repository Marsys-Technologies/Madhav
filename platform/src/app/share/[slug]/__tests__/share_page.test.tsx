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
 * SS N-379 follow-up:
 *  ii. share viewers get ONLY rendered text: no tool-call / data-* parts, no
 *      message metadata, an opaque display role (never the raw role / isAdmin),
 *      checked in container.innerHTML AND in the props handed to the client.
 * iii. the conversation read is `SELECT title, chart_id` (no SELECT *).
 *  iv. a refused visitor is sent to /login?next=<encoded /share/<slug>>.
 *   v. the STORED hide options are applied even with R10_SELECTIVE_SHARE off.
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
      return { rows: [{ title: 'My chat', chart_id: 'chart-1' }] }
    if (/FROM charts/i.test(sql)) return { rows: [{ name: 'Chart Name' }] }
    return { rows: [] }
  })
  loadMessagesMock.mockImplementation(async () => {
    callLog.push('loadMessages')
    return messagesOverride ?? conversationMessages()
  })
}

let messagesOverride: unknown[] | null = null


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

const SLUG = 'abc1234567'
const LOGIN_NEXT = `/login?next=${encodeURIComponent(`/share/${SLUG}`)}`

async function renderPage(slug = SLUG) {
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
  messagesOverride = null
  delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
})
afterEach(() => {
  cleanup()
  delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
})

describe('share page requires a verified, active session (item 1)', () => {
  it('no verified session -> redirect to /login and NO share/conversation/chart/message read', async () => {
    setup({ user: null })
    await expect(renderPage()).rejects.toThrow(`NEXT_REDIRECT:${LOGIN_NEXT}`)
    expect(redirectMock).toHaveBeenCalledWith(LOGIN_NEXT)
    expect(shareReadsCount()).toBe(0)
    expect(loadMessagesMock).not.toHaveBeenCalled()
  })

  it('verified user whose profile is missing -> redirect, no data read', async () => {
    setup({ profile: null })
    await expect(renderPage()).rejects.toThrow(`NEXT_REDIRECT:${LOGIN_NEXT}`)
    expect(shareReadsCount()).toBe(0)
    expect(loadMessagesMock).not.toHaveBeenCalled()
  })

  it.each(['pending', 'disabled'])('profile status %s is refused like elsewhere', async (status) => {
    setup({ profile: { id: 'viewer-1', role: 'guest', status } })
    await expect(renderPage()).rejects.toThrow(`NEXT_REDIRECT:${LOGIN_NEXT}`)
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

  it('MARSYS_FLAG_R10_SELECTIVE_SHARE=false does NOT un-hide: the stored options are still applied', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    setup({ share: shareHiding(true, true) })
    const el = await renderPage()
    const serialized = serializeProps(el)
    expect(serialized).toContain(VISIBLE_ANSWER)
    expect(serialized).not.toContain(REASONING_TEXT)
    expect(serialized).not.toContain(METHODOLOGY_TEXT)
    const { container } = render(el as React.ReactElement)
    expect(container.innerHTML).not.toContain(REASONING_TEXT)
    expect(container.innerHTML).not.toContain(METHODOLOGY_TEXT)
  })

  it('flag off + each option alone: still independent and still applied', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    setup({ share: shareHiding(true, false) })
    let ser = serializeProps(await renderPage())
    expect(ser).not.toContain(REASONING_TEXT)
    expect(ser).toContain(METHODOLOGY_TEXT)
    setup({ share: shareHiding(false, true) })
    ser = serializeProps(await renderPage())
    expect(ser).toContain(REASONING_TEXT)
    expect(ser).not.toContain(METHODOLOGY_TEXT)
  })

  it('flag off + nothing stored as hidden: everything shows (the flag never hides either)', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    setup({ share: shareHiding(false, false) })
    const ser = serializeProps(await renderPage())
    expect(ser).toContain(REASONING_TEXT)
    expect(ser).toContain(METHODOLOGY_TEXT)
  })
})

describe('login redirect carries a safe next (SS N-379 iv)', () => {
  it('a refused visitor is sent to /login?next=<encoded /share/slug>', async () => {
    setup({ user: null })
    await expect(renderPage()).rejects.toThrow(`NEXT_REDIRECT:${LOGIN_NEXT}`)
    expect(LOGIN_NEXT).toBe('/login?next=%2Fshare%2Fabc1234567')
  })

  it('the emitted next survives the shared validator unchanged', async () => {
    const { safeNextPath } = await import('@/lib/auth/safe_next')
    const next = new URL(LOGIN_NEXT, 'http://localhost').searchParams.get('next')
    expect(safeNextPath(next)).toBe(`/share/${SLUG}`)
  })

  it.each(['short', 'abc1234567x', '..%2f..%2fetc', 'abc123456/', '//evil.com', 'abc12345 67'])(
    'a slug without the minted shape (%s) never goes into next: plain /login',
    async (slug) => {
      setup({ user: null })
      await expect(renderPage(slug)).rejects.toThrow('NEXT_REDIRECT:/login')
      expect(redirectMock).toHaveBeenCalledWith('/login')
    },
  )
})

describe('conversation read is not SELECT * (SS N-379 iii)', () => {
  it('reads exactly title, chart_id, keyed by the share row conversation id', async () => {
    setup()
    await renderPage()
    const call = queryMock.mock.calls.find(([s]) => /FROM conversations/i.test(String(s)))!
    expect(String(call[0])).toMatch(/^SELECT\s+title,\s*chart_id\s+FROM conversations\s+WHERE id=\$1$/i)
    expect(String(call[0])).not.toMatch(/\*/)
    expect(call[1]).toEqual(['conv-1'])
    expect(loadMessagesMock).toHaveBeenCalledWith('conv-1')
  })
})

describe('share viewers receive only rendered text (SS N-379 ii)', () => {
  const TOOL_IN = 'RAW_RETRIEVAL_INPUT_secret'
  const TOOL_OUT = 'RAW_RETRIEVAL_OUTPUT_secret'
  const BANNED = [
    'tool-', 'dynamic-tool', 'toolCallId', 'data-', 'metadata', 'providerMetadata',
    TOOL_IN, TOOL_OUT, 'DATA_PART_secret', 'MODEL_xyz', 'STYLE_xyz', 'QID_123',
    'super_admin', 'isAdmin', 'ADMIN_ROLE_MESSAGE_TEXT', 'conv-msg-uuid',
  ]

  // The rendered DOM legitimately carries its own data-* attributes (data-role,
  // data-message-index), so the DOM check names the leaked part type instead.
  const BANNED_DOM = BANNED.map((b) => (b === 'data-' ? 'data-trace' : b))

  function richMessages() {
    return [
      {
        id: 'conv-msg-uuid-1',
        role: 'user',
        parts: [{ type: 'text', text: 'What about Saturn?' }],
        metadata: { role: 'super_admin', created_at: 't' },
      },
      {
        id: 'conv-msg-uuid-2',
        role: 'assistant',
        parts: [
          { type: 'tool-ganita_planet_get', toolCallId: 'c1', state: 'output-available', input: { q: TOOL_IN }, output: { r: TOOL_OUT } },
          { type: 'data-trace', data: { s: 'DATA_PART_secret' } },
          { type: 'text', text: VISIBLE_ANSWER },
        ],
        metadata: { role: 'super_admin', model: 'MODEL_xyz', style: 'STYLE_xyz', query_id: 'QID_123' },
      },
      { id: 'conv-msg-uuid-3', role: 'super_admin', parts: [{ type: 'text', text: 'ADMIN_ROLE_MESSAGE_TEXT' }], metadata: {} },
    ]
  }

  /** Props of the first element whose type is the SharedConversation client component. */
  function sharedConversationProps(node: unknown): Record<string, unknown> | null {
    if (!node || typeof node !== 'object') return null
    if (Array.isArray(node)) {
      for (const n of node) {
        const r = sharedConversationProps(n)
        if (r) return r
      }
      return null
    }
    const el = node as { type?: unknown; props?: Record<string, unknown> }
    if (typeof el.type === 'function' && el.type.name === 'SharedConversation') return el.props ?? {}
    return el.props ? sharedConversationProps(el.props.children) : null
  }

  it('the client component receives exactly: positional id, display role, text parts', async () => {
    messagesOverride = richMessages()
    setup()
    messagesOverride = richMessages()
    const el = await renderPage()
    const props = sharedConversationProps(el)
    expect(props).not.toBeNull()
    expect(Object.keys(props!)).toEqual(['messages'])
    expect(JSON.parse(JSON.stringify(props))).toEqual({
      messages: [
        { id: 'm0', role: 'user', parts: [{ type: 'text', text: 'What about Saturn?' }] },
        { id: 'm1', role: 'assistant', parts: [{ type: 'text', text: VISIBLE_ANSWER }] },
      ],
    })
  })

  it('serialized props: no tool/data parts, metadata, model/style/query_id, raw role or isAdmin', async () => {
    setup()
    messagesOverride = richMessages()
    const serialized = serializeProps(await renderPage())
    expect(serialized).toContain(VISIBLE_ANSWER)
    for (const banned of BANNED) expect(serialized, banned).not.toContain(banned)
  })

  it('container.innerHTML: plain text only, no tool card, no model/style chip, no admin trace flow', async () => {
    const fetchSpy = vi.fn()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    global.fetch = fetchSpy as any
    setup()
    messagesOverride = richMessages()
    const { container } = render((await renderPage()) as React.ReactElement)
    const html = container.innerHTML
    expect(html).toContain(VISIBLE_ANSWER)
    expect(html).toContain('What about Saturn?')
    for (const banned of BANNED_DOM) expect(html, banned).not.toContain(banned)
    expect(container.textContent).not.toMatch(/ganita_planet_get/)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('the same holds with both hide options stored and the flag off', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    setup({
      share: { conversation_id: 'conv-1', revoked_at: null, expires_at: null, hide_reasoning: true, hide_methodology: true },
    })
    messagesOverride = richMessages()
    const serialized = serializeProps(await renderPage())
    for (const banned of BANNED) expect(serialized, banned).not.toContain(banned)
  })
})
