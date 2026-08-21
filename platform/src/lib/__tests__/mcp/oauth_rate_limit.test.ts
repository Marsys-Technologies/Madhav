/**
 * RATE-07 — the shared bucket store (PARIŚEṢA-V4 GA-2 ruling).
 *
 * Two things are proved here, and one is deliberately NOT:
 *
 *   PROVED (structural): the check-and-increment is a SINGLE statement with no
 *     SELECT-then-UPDATE shape, the window boundary is computed server-side, the
 *     counter saturates rather than overflowing, and the prune is bounded. These
 *     are properties of the SQL text and are exactly what a regression would
 *     silently break, so they are asserted against the SQL text itself.
 *
 *   PROVED (behavioural, against a fake): concurrency semantics, argument
 *     validation, the allowed/denied boundary, and fail-closed-on-no-row. The
 *     fake models Postgres's ON CONFLICT row-level serialisation.
 *
 *   NOT PROVED HERE: that a real Postgres actually serialises the way the fake
 *     assumes. A fake cannot establish that, and asserting it from here would be
 *     exactly the "signal with no detector behind it" §N.8 forbids. That is what
 *     `oauth_rate_limit.db.test.ts` is for — a real, concurrent, opt-in run
 *     against a live Postgres.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import {
  bucketKey,
  consumeRateBucket,
  pruneExpiredRateBuckets,
  shouldPrune,
  CONSUME_BUCKET_SQL,
  PRUNE_BUCKETS_SQL,
  PRUNE_BATCH_SIZE,
  PRUNE_PROBABILITY_DENOMINATOR,
  RateBucketArgumentError,
  SUBJECT_KINDS,
  MAX_LIMIT,
  MAX_WINDOW_SECONDS,
} from '@/lib/mcp/oauth_rate_limit'

beforeEach(() => {
  queryMock.mockReset()
})

// ── Structural proof: the atomicity contract lives in the SQL ────────────────

describe('RATE-07 — SQL structural contract', () => {
  it('is a single INSERT ... ON CONFLICT DO UPDATE ... RETURNING statement', () => {
    expect(CONSUME_BUCKET_SQL).toMatch(/INSERT INTO mcp_rate_buckets/)
    expect(CONSUME_BUCKET_SQL).toMatch(/ON CONFLICT \(bucket_key\) DO UPDATE/)
    expect(CONSUME_BUCKET_SQL).toMatch(/RETURNING/)
    // Exactly one statement — no semicolon-separated second statement.
    expect(CONSUME_BUCKET_SQL.replace(/;\s*$/, '')).not.toContain(';')
  })

  it('contains NO read-then-write shape — the whole defect class this replaces', () => {
    // A bare `SELECT ... FROM mcp_rate_buckets` followed by an UPDATE is the
    // race the single statement exists to eliminate. The CTE's SELECT reads
    // now(), not the table, so scope the assertion to table reads.
    expect(CONSUME_BUCKET_SQL).not.toMatch(/SELECT[\s\S]*FROM\s+mcp_rate_buckets/i)
    expect(CONSUME_BUCKET_SQL).not.toMatch(/\bUPDATE\s+mcp_rate_buckets\b/i)
    expect(CONSUME_BUCKET_SQL).not.toMatch(/FOR\s+UPDATE/i)
  })

  it('computes the window boundary server-side (clock skew across instances)', () => {
    expect(CONSUME_BUCKET_SQL).toMatch(/floor\(extract\(epoch FROM now\(\)\)/)
    // No caller-supplied timestamp parameter anywhere.
    expect(CONSUME_BUCKET_SQL).not.toMatch(/window_start\s*=\s*\$/)
  })

  it('resets rather than accumulating a second row when the window rolls over', () => {
    expect(CONSUME_BUCKET_SQL).toMatch(/WHEN b\.window_start = EXCLUDED\.window_start/)
    expect(CONSUME_BUCKET_SQL).toMatch(/ELSE 1/)
  })

  it('saturates hits instead of overflowing INTEGER into a negative (= "allowed")', () => {
    expect(CONSUME_BUCKET_SQL).toMatch(/LEAST\(b\.hits \+ 1, \$5::int\)/)
  })

  it('returns a Retry-After that is never below 1 second', () => {
    expect(CONSUME_BUCKET_SQL).toMatch(/GREATEST\(1,/)
  })

  it('the prune is bounded by a LIMIT and leaves a boundary grace interval', () => {
    expect(PRUNE_BUCKETS_SQL).toMatch(/LIMIT \$1/)
    expect(PRUNE_BUCKETS_SQL).toMatch(/expires_at < now\(\) - interval/)
    expect(PRUNE_BATCH_SIZE).toBeLessThanOrEqual(1000)
    expect(PRUNE_PROBABILITY_DENOMINATOR).toBeGreaterThan(1)
  })
})

// ── Key derivation ───────────────────────────────────────────────────────────

describe('RATE-07 — bucket key', () => {
  it('is a fixed-width sha256 hex regardless of subject length', () => {
    const short = bucketKey('oauth_token', 'ip', '1.2.3.4', 60)
    const huge = bucketKey('oauth_token', 'ip', 'x'.repeat(8192), 60)
    expect(short).toMatch(/^[0-9a-f]{64}$/)
    expect(huge).toMatch(/^[0-9a-f]{64}$/)
  })

  it('separates route, kind and subject so they cannot be confused with each other', () => {
    expect(bucketKey('oauth_token', 'ip', 'a', 60)).not.toBe(bucketKey('oauth_token', 'client', 'a', 60))
    expect(bucketKey('oauth_token', 'ip', 'a', 60)).not.toBe(bucketKey('oauth_authorize', 'ip', 'a', 60))
    // A subject containing the delimiter must not be able to impersonate
    // another (route, kind) pair.
    expect(bucketKey('oauth_token', 'ip', 'a|b', 60)).not.toBe(bucketKey('oauth_token|ip', 'ip', 'a' as never, 60))
  })

  it('separates windows, so one subject charged with two window lengths cannot collide', () => {
    // Without this, `window_seconds = EXCLUDED.window_seconds` in the upsert
    // would let a 3600s call silently re-stamp a 60s bucket's window.
    expect(bucketKey('oauth_token', 'ip', 'a', 60)).not.toBe(bucketKey('oauth_token', 'ip', 'a', 3600))
  })

  it('is stable', () => {
    expect(bucketKey('r', 'ip', 's', 60)).toBe(bucketKey('r', 'ip', 's', 60))
  })
})

// ── Argument validation ──────────────────────────────────────────────────────

describe('RATE-07 — argument bounds (a limit of 1e9 is not a limit)', () => {
  const base = { route: 'oauth_token', subjectKind: 'ip' as const, subject: '1.1.1.1', limit: 10, windowSeconds: 60 }

  it.each([
    ['empty route', { route: '' }],
    ['over-long route', { route: 'x'.repeat(65) }],
    ['unknown subject kind', { subjectKind: 'wishful' as never }],
    ['zero limit', { limit: 0 }],
    ['limit above MAX_LIMIT', { limit: MAX_LIMIT + 1 }],
    ['fractional limit', { limit: 1.5 }],
    ['zero window', { windowSeconds: 0 }],
    ['window above MAX_WINDOW_SECONDS', { windowSeconds: MAX_WINDOW_SECONDS + 1 }],
    ['NaN limit', { limit: Number.NaN }],
  ])('rejects %s', async (_label, override) => {
    await expect(consumeRateBucket({ ...base, ...override })).rejects.toBeInstanceOf(RateBucketArgumentError)
    expect(queryMock, 'an invalid request must never reach the database').not.toHaveBeenCalled()
  })

  it('accepts every declared subject kind', async () => {
    for (const kind of SUBJECT_KINDS) {
      queryMock.mockResolvedValueOnce({ rows: [{ hits: 1, window_seconds: 60, retry_after_seconds: 60 }] })
      await expect(consumeRateBucket({ ...base, subjectKind: kind })).resolves.toMatchObject({ allowed: true })
    }
  })
})

// ── Decision semantics ───────────────────────────────────────────────────────

describe('RATE-07 — allowed/denied boundary', () => {
  const args = { route: 'oauth_authorize', subjectKind: 'ip' as const, subject: '1.1.1.1', limit: 3, windowSeconds: 60 }

  it('allows exactly `limit` requests and denies the next one', async () => {
    for (const hits of [1, 2, 3]) {
      queryMock.mockResolvedValueOnce({ rows: [{ hits, window_seconds: 60, retry_after_seconds: 30 }] })
      const d = await consumeRateBucket(args)
      expect(d.allowed, `hit ${hits} of limit 3`).toBe(true)
      expect(d.remaining).toBe(3 - hits)
    }
    queryMock.mockResolvedValueOnce({ rows: [{ hits: 4, window_seconds: 60, retry_after_seconds: 30 }] })
    const denied = await consumeRateBucket(args)
    expect(denied.allowed).toBe(false)
    expect(denied.remaining).toBe(0)
    expect(denied.retryAfterSeconds).toBe(30)
  })

  it('charges rejected requests too — a flood never earns a free window reset', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ hits: 999, window_seconds: 60, retry_after_seconds: 5 }] })
    const d = await consumeRateBucket(args)
    expect(d.allowed).toBe(false)
    expect(d.hits).toBe(999)
    // The statement that produced it is an INSERT/UPDATE — the charge happened.
    expect(queryMock.mock.calls[0]![0]).toBe(CONSUME_BUCKET_SQL)
  })

  it('never reports retryAfterSeconds below 1', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ hits: 9, window_seconds: 60, retry_after_seconds: 0 }] })
    expect((await consumeRateBucket(args)).retryAfterSeconds).toBe(1)
  })

  it('THROWS rather than assuming "allowed" when the upsert returns no row', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    await expect(consumeRateBucket(args)).rejects.toThrow(/refusing to assume/)
  })

  it('propagates a database error rather than swallowing it into allowed=true', async () => {
    queryMock.mockRejectedValueOnce(new Error('connection terminated'))
    await expect(consumeRateBucket(args)).rejects.toThrow('connection terminated')
  })

  it('passes the saturation cap as a bind parameter, not inline', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ hits: 1, window_seconds: 60, retry_after_seconds: 60 }] })
    await consumeRateBucket(args)
    const params = queryMock.mock.calls[0]![1] as unknown[]
    expect(params).toHaveLength(5)
    expect(params[0]).toBe(bucketKey('oauth_authorize', 'ip', '1.1.1.1', 60))
    expect(params[1]).toBe('oauth_authorize')
    expect(params[2]).toBe('ip')
    expect(params[3]).toBe(60)
    expect(Number(params[4])).toBeGreaterThan(1_000_000_000)
    // The subject itself is NEVER sent to the database in cleartext.
    expect(params).not.toContain('1.1.1.1')
  })
})

// ── Concurrency, against a fake that models ON CONFLICT serialisation ────────

describe('RATE-07 — concurrent charges each observe a distinct count', () => {
  it('N concurrent requests yield hits 1..N and exactly `limit` allowed', async () => {
    // Models Postgres: ON CONFLICT DO UPDATE takes a row lock, so concurrent
    // upserts on the same key serialise and each RETURNS its own post-increment
    // value. (That Postgres genuinely behaves this way is proved by the opt-in
    // db test, not asserted here.)
    const store = new Map<string, number>()
    queryMock.mockImplementation(async (_sql: string, params: unknown[]) => {
      const key = params[0] as string
      const next = (store.get(key) ?? 0) + 1
      store.set(key, next)
      return { rows: [{ hits: next, window_seconds: 60, retry_after_seconds: 60 }] }
    })

    const LIMIT = 5
    const N = 20
    const decisions = await Promise.all(
      Array.from({ length: N }, () =>
        consumeRateBucket({ route: 'oauth_token', subjectKind: 'ip', subject: '9.9.9.9', limit: LIMIT, windowSeconds: 60 }),
      ),
    )

    expect(new Set(decisions.map((d) => d.hits)).size, 'every charge must see a distinct count').toBe(N)
    expect(decisions.filter((d) => d.allowed)).toHaveLength(LIMIT)
    expect(decisions.filter((d) => !d.allowed)).toHaveLength(N - LIMIT)
  })

  it('different subjects do not share a counter', async () => {
    const store = new Map<string, number>()
    queryMock.mockImplementation(async (_sql: string, params: unknown[]) => {
      const key = params[0] as string
      const next = (store.get(key) ?? 0) + 1
      store.set(key, next)
      return { rows: [{ hits: next, window_seconds: 60, retry_after_seconds: 60 }] }
    })

    const a = await consumeRateBucket({ route: 'oauth_token', subjectKind: 'ip', subject: 'a', limit: 1, windowSeconds: 60 })
    const b = await consumeRateBucket({ route: 'oauth_token', subjectKind: 'ip', subject: 'b', limit: 1, windowSeconds: 60 })
    expect(a.allowed).toBe(true)
    expect(b.allowed).toBe(true)
    expect(store.size).toBe(2)
  })
})

// ── Prune ────────────────────────────────────────────────────────────────────

describe('RATE-07 — TTL cleanup', () => {
  it('deletes a bounded batch and reports the count', async () => {
    queryMock.mockResolvedValueOnce({ rows: [], rowCount: 37 })
    expect(await pruneExpiredRateBuckets()).toBe(37)
    expect(queryMock.mock.calls[0]![0]).toBe(PRUNE_BUCKETS_SQL)
    expect(queryMock.mock.calls[0]![1]).toEqual([PRUNE_BATCH_SIZE])
  })

  it('a prune failure is swallowed — garbage collection must not fail live requests', async () => {
    queryMock.mockRejectedValueOnce(new Error('deadlock detected'))
    await expect(pruneExpiredRateBuckets()).resolves.toBe(0)
  })

  it('shouldPrune fires on roughly 1 call in PRUNE_PROBABILITY_DENOMINATOR', () => {
    expect(shouldPrune(() => 0)).toBe(true)
    expect(shouldPrune(() => 1 / PRUNE_PROBABILITY_DENOMINATOR - 1e-9)).toBe(true)
    expect(shouldPrune(() => 1 / PRUNE_PROBABILITY_DENOMINATOR)).toBe(false)
    expect(shouldPrune(() => 0.999)).toBe(false)
  })
})
