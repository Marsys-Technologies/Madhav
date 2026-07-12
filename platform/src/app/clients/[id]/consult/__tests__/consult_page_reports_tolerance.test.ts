/**
 * WP-1.1 / LCA-2 — consult PAGE reports-tolerance regression.
 *
 * The two consult server components previously issued an unconditional
 * `SELECT * FROM reports …` inside a Promise.all. `reports` was RETIRED (DDL only
 * in platform/migrations/_archive; ABSENT from deployed Cloud SQL), so that read
 * raised a permanent 42P01 (undefined_table) that crashed the page render for
 * EVERY chart. Unlike the sibling pyramid_layers read, it was not .catch-guarded.
 *
 * Fix: the `reports` read is none-safed to an empty result (table NOT resurrected).
 *
 * This suite pins that neither page ever queries `reports` and both render even
 * when the DB would raise 42P01 on any `reports` access. The `query` mock THROWS
 * a 42P01 for any `FROM reports` SQL — so if either page ever reintroduces the
 * read, these tests fail loudly.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const issuedSql: string[] = []

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })),
}))

vi.mock('@/lib/auth/chart-page-guard', () => ({
  resolveChartPageAccess: vi.fn(async () => ({
    user: { uid: 'tester-uid' },
    permission: 'view',
    role: 'super_admin',
  })),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    issuedSql.push(sql)
    // Faithful to production: the retired relation raises a permanent 42P01.
    if (/from\s+reports\b/i.test(sql)) {
      const e = new Error('relation "reports" does not exist') as Error & { code?: string }
      e.code = '42P01'
      throw e
    }
    if (/from\s+charts\b/i.test(sql)) {
      return { rows: [{ name: 'Abhisek Mohanty', birth_date: '1984-02-05', birth_place: 'Bhubaneswar', client_id: 'tester-uid' }] }
    }
    if (/from\s+profiles\b/i.test(sql)) return { rows: [{ role: 'super_admin' }] }
    if (/from\s+pyramid_layers\b/i.test(sql)) return { rows: [{ layer_key: 'L1', status: 'built' }] }
    return { rows: [] }
  }),
}))

vi.mock('@/lib/conversations', () => ({
  listConversations: vi.fn(async () => []),
  getConversation: vi.fn(async () => ({ chart_id: CHART })),
}))

vi.mock('@/lib/persistence/conversation_writer', () => ({
  loadConversationMessagesV2: vi.fn(async () => []),
}))

vi.mock('@/lib/config/index', () => ({
  configService: { getFlag: vi.fn(() => false) },
}))

// Stub the (client) chat component so the page module import stays light and the
// returned React element builds without pulling the full UI tree.
vi.mock('@/components/consume/ConsumeChat', () => ({
  ConsumeChat: () => null,
}))

// next/navigation redirect/notFound throw to halt rendering in Next; if either
// fires on the happy path that is a bug, so make them throw a labelled error.
vi.mock('next/navigation', () => ({
  redirect: vi.fn((to: string) => { throw new Error(`unexpected redirect(${to})`) }),
  notFound: vi.fn(() => { throw new Error('unexpected notFound()') }),
}))

import ConsultPage from '../page'
import ConsultConversationPage from '../[conversationId]/page'

beforeEach(() => {
  issuedSql.length = 0
})

describe('WP-1.1 / LCA-2 — consult page tolerates absent `reports` relation', () => {
  it('list page renders without touching `reports`', async () => {
    const el = await ConsultPage({
      params: Promise.resolve({ id: CHART }),
      searchParams: Promise.resolve({}),
    })
    // Rendered a React element — did not throw on the retired relation.
    expect(el).toBeTruthy()
    expect(issuedSql.some(s => /from\s+reports\b/i.test(s))).toBe(false)
    // Live reads still happened.
    expect(issuedSql.some(s => /from\s+charts\b/i.test(s))).toBe(true)
  })

  it('conversation page renders without touching `reports`', async () => {
    const el = await ConsultConversationPage({
      params: Promise.resolve({ id: CHART, conversationId: 'conv-1' }),
    })
    expect(el).toBeTruthy()
    expect(issuedSql.some(s => /from\s+reports\b/i.test(s))).toBe(false)
    expect(issuedSql.some(s => /from\s+charts\b/i.test(s))).toBe(true)
  })
})
