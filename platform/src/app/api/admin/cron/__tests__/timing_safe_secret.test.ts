// @vitest-environment node
/**
 * SS N-373 item 5 — every MARSYS_CRON_SECRET comparison goes through the shared
 * timing-safe helper and FAILS CLOSED when the secret is unset.
 *
 * `crypto.timingSafeEqual` is wrapped in a spy so the test proves the compare
 * actually reached it (a plain `!==` never does).
 */
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const tse = vi.hoisted(() => ({ calls: 0 }))
vi.mock('crypto', async (importOriginal) => {
  const actual = await importOriginal<typeof import('crypto')>()
  return {
    ...actual,
    default: actual,
    timingSafeEqual: (a: NodeJS.ArrayBufferView, b: NodeJS.ArrayBufferView) => {
      tse.calls++
      return actual.timingSafeEqual(a, b)
    },
  }
})

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [], rowCount: 0 }),
  getPool: vi.fn(),
  pool: {},
}))
vi.mock('@/lib/config', () => ({ getFlag: () => false }))
vi.mock('@/lib/ai-console/revalidation', () => ({
  revalidateStaleConnections: vi.fn().mockResolvedValue({}),
}))

const SECRET = 'cron-secret-value-0123456789'

interface Case {
  name: string
  load: () => Promise<{ POST: (r: Request) => Promise<Response> }>
  /** How the caller presents the secret. */
  header: (value: string) => Record<string, string>
}

const custom = (v: string) => ({ 'x-marsys-cron-secret': v })
const CASES: Case[] = [
  { name: 'cron/reap-pending-streams', load: () => import('@/app/api/admin/cron/reap-pending-streams/route'), header: custom },
  { name: 'cron/refresh-panchanga-daily', load: () => import('@/app/api/admin/cron/refresh-panchanga-daily/route'), header: custom },
  { name: 'cron/revalidate-ai-connections', load: () => import('@/app/api/admin/cron/revalidate-ai-connections/route'), header: custom },
  { name: 'cron/run-canary-battery', load: () => import('@/app/api/admin/cron/run-canary-battery/route'), header: custom },
  { name: 'internal/refresh-mv (custom header)', load: () => import('@/app/api/admin/internal/refresh-mv/route'), header: (v) => ({ 'x-marsys-cron-secret': v }) },
  { name: 'internal/refresh-mv (bearer)', load: () => import('@/app/api/admin/internal/refresh-mv/route'), header: (v) => ({ authorization: `Bearer ${v}` }) },
  { name: 'internal/spine-bundle-refresh (custom header)', load: () => import('@/app/api/admin/internal/spine-bundle-refresh/route'), header: (v) => ({ 'x-marsys-cron-secret': v }) },
  { name: 'internal/spine-bundle-refresh (bearer)', load: () => import('@/app/api/admin/internal/spine-bundle-refresh/route'), header: (v) => ({ authorization: `Bearer ${v}` }) },
]

function post(headers: Record<string, string>): Request {
  return new Request('http://localhost/api/admin/x', { method: 'POST', headers, body: '{}' })
}

const savedEnv = { ...process.env }
beforeEach(() => {
  vi.resetModules()
  tse.calls = 0
  process.env.MARSYS_CRON_SECRET = SECRET
  delete process.env.PYTHON_SIDECAR_URL
  delete process.env.MCP_CANARY_KEY
})
afterEach(() => {
  process.env = { ...savedEnv }
})

async function call(c: Case, headers: Record<string, string>): Promise<number | 'threw'> {
  const mod = await c.load()
  try {
    return (await mod.POST(post(headers))).status
  } catch {
    return 'threw' // got past the secret check and failed later: not a 401
  }
}

describe('MARSYS_CRON_SECRET comparisons (SS N-373 item 5)', () => {
  for (const c of CASES) {
    describe(c.name, () => {
      it('wrong secret of the same length -> 401', async () => {
        expect(await call(c, c.header('X'.repeat(SECRET.length)))).toBe(401)
      })

      it('wrong secret of a different length -> 401 (no throw)', async () => {
        expect(await call(c, c.header('short'))).toBe(401)
        expect(await call(c, c.header(SECRET + 'extra'))).toBe(401)
      })

      it('no credential at all -> 401', async () => {
        expect(await call(c, {})).toBe(401)
      })

      it('empty credential -> 401', async () => {
        expect(await call(c, c.header(''))).toBe(401)
      })

      it('FAIL CLOSED: an UNSET secret rejects every request, even one presenting an empty or arbitrary value', async () => {
        delete process.env.MARSYS_CRON_SECRET
        expect(await call(c, {})).toBe(401)
        expect(await call(c, c.header(''))).toBe(401)
        expect(await call(c, c.header('anything'))).toBe(401)
        expect(await call(c, c.header('undefined'))).toBe(401)
      })

      it('FAIL CLOSED: an EMPTY-string secret rejects every request', async () => {
        process.env.MARSYS_CRON_SECRET = ''
        expect(await call(c, {})).toBe(401)
        expect(await call(c, c.header(''))).toBe(401)
      })

      it('correct secret -> passes the gate (not a 401)', async () => {
        expect(await call(c, c.header(SECRET))).not.toBe(401)
      })

      it('the comparison runs through crypto.timingSafeEqual', async () => {
        await call(c, c.header(SECRET))
        expect(tse.calls).toBeGreaterThan(0)
      })
    })
  }
})
