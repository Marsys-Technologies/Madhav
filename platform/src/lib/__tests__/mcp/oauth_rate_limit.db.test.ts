/**
 * RATE-07 — REAL Postgres proof of cross-instance atomicity and TTL cleanup.
 *
 * SKIPPED unless MCP_RATE_LIMIT_DB_TEST=1 AND DATABASE_URL is set. Designed for
 * a THROWAWAY / local Postgres, never the shared production or dev database: it
 * applies migration 580's DDL idempotently in `beforeAll` and deletes only the
 * rows whose bucket_key it created.
 *
 * WHY THIS FILE EXISTS SEPARATELY FROM `oauth_rate_limit.test.ts`:
 * that file proves the SQL's SHAPE and models concurrency against a fake. A fake
 * cannot establish that Postgres genuinely serialises `ON CONFLICT DO UPDATE` on
 * the conflicting row — and the whole rate limiter rests on that claim. Asserting
 * it from a fake would be a signal with no detector behind it (CLAUDE.md §N.8).
 * This file is the detector. It is opt-in because CI has no Postgres, which is an
 * honest gap, not a satisfied requirement: a reviewer wanting the atomicity
 * evidence must run it.
 *
 * Run locally:
 *   MCP_RATE_LIMIT_DB_TEST=1 DATABASE_URL=postgres://... \
 *     npx vitest run src/lib/__tests__/mcp/oauth_rate_limit.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { randomUUID } from 'node:crypto'

const ENABLED = process.env.MCP_RATE_LIMIT_DB_TEST === '1' && !!process.env.DATABASE_URL

// Unique per run so a failed run never poisons the next one.
const RUN = randomUUID()
const ROUTE = `test_${RUN.slice(0, 8)}`

const DDL = `
CREATE TABLE IF NOT EXISTS mcp_rate_buckets (
  bucket_key      TEXT        PRIMARY KEY,
  route           TEXT        NOT NULL,
  subject_kind    TEXT        NOT NULL,
  window_start    TIMESTAMPTZ NOT NULL,
  window_seconds  INTEGER     NOT NULL,
  hits            INTEGER     NOT NULL,
  expires_at      TIMESTAMPTZ NOT NULL,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT mcp_rate_buckets_hits_nonneg     CHECK (hits >= 0),
  CONSTRAINT mcp_rate_buckets_window_positive CHECK (window_seconds > 0)
);
CREATE INDEX IF NOT EXISTS mcp_rate_buckets_expires_at_idx ON mcp_rate_buckets (expires_at);
`

describe.skipIf(!ENABLED)('RATE-07 — real Postgres', () => {
  let consumeRateBucket: typeof import('@/lib/mcp/oauth_rate_limit').consumeRateBucket
  let pruneExpiredRateBuckets: typeof import('@/lib/mcp/oauth_rate_limit').pruneExpiredRateBuckets
  let bucketKey: typeof import('@/lib/mcp/oauth_rate_limit').bucketKey
  let query: typeof import('@/lib/db/client').query

  beforeAll(async () => {
    ;({ consumeRateBucket, pruneExpiredRateBuckets, bucketKey } = await import('@/lib/mcp/oauth_rate_limit'))
    ;({ query } = await import('@/lib/db/client'))
    await query(DDL)
  })

  afterAll(async () => {
    if (!ENABLED) return
    await query('DELETE FROM mcp_rate_buckets WHERE route LIKE $1', [`test_${RUN.slice(0, 8)}%`])
  })

  it('ATOMICITY: 50 concurrent charges on one key produce hits 1..50 with no duplicates', async () => {
    const subject = `atom-${RUN}`
    const N = 50
    const LIMIT = 10

    const decisions = await Promise.all(
      Array.from({ length: N }, () =>
        consumeRateBucket({ route: ROUTE, subjectKind: 'ip', subject, limit: LIMIT, windowSeconds: 300 })
      )
    )

    const hits = decisions.map((d) => d.hits).sort((a, b) => a - b)
    // The load-bearing assertion: every concurrent caller saw a DIFFERENT count.
    // A lost update (read-then-write) shows up here as a duplicate.
    expect(new Set(hits).size).toBe(N)
    expect(hits).toEqual(Array.from({ length: N }, (_, i) => i + 1))
    expect(decisions.filter((d) => d.allowed)).toHaveLength(LIMIT)

    // And exactly ONE row exists for the whole burst.
    const rows = await query('SELECT hits FROM mcp_rate_buckets WHERE bucket_key = $1', [
      bucketKey(ROUTE, 'ip', subject),
    ])
    expect(rows.rows).toHaveLength(1)
    expect(Number(rows.rows[0]!.hits)).toBe(N)
  }, 30_000)

  it('WINDOW ROLLOVER reuses the row in place rather than accumulating a second one', async () => {
    const subject = `roll-${RUN}`
    // A 1-second window so the rollover is observable in test time.
    await consumeRateBucket({ route: ROUTE, subjectKind: 'ip', subject, limit: 5, windowSeconds: 1 })
    await new Promise((r) => setTimeout(r, 1_600))
    const second = await consumeRateBucket({ route: ROUTE, subjectKind: 'ip', subject, limit: 5, windowSeconds: 1 })

    expect(second.hits, 'a new window must reset the counter').toBe(1)
    const rows = await query('SELECT count(*)::int AS n FROM mcp_rate_buckets WHERE bucket_key = $1', [
      bucketKey(ROUTE, 'ip', subject),
    ])
    expect(Number(rows.rows[0]!.n), 'a recurring subject must occupy exactly one row forever').toBe(1)
  }, 15_000)

  it('TTL CLEANUP removes long-expired rows and leaves live ones alone', async () => {
    const deadKey = bucketKey(ROUTE, 'ip', `dead-${RUN}`)
    const liveSubject = `live-${RUN}`

    // A row already well past its grace interval.
    await query(
      `INSERT INTO mcp_rate_buckets
         (bucket_key, route, subject_kind, window_start, window_seconds, hits, expires_at, updated_at)
       VALUES ($1, $2, 'ip', now() - interval '2 hours', 60, 5, now() - interval '119 minutes', now())
       ON CONFLICT (bucket_key) DO NOTHING`,
      [deadKey, ROUTE]
    )
    await consumeRateBucket({ route: ROUTE, subjectKind: 'ip', subject: liveSubject, limit: 5, windowSeconds: 300 })

    await pruneExpiredRateBuckets()

    const dead = await query('SELECT 1 FROM mcp_rate_buckets WHERE bucket_key = $1', [deadKey])
    const live = await query('SELECT 1 FROM mcp_rate_buckets WHERE bucket_key = $1', [
      bucketKey(ROUTE, 'ip', liveSubject),
    ])
    expect(dead.rows, 'an expired bucket must be reclaimed').toHaveLength(0)
    expect(live.rows, 'a live bucket must survive the prune').toHaveLength(1)
  }, 15_000)

  it('the window boundary is derived from the SERVER clock, not the caller', async () => {
    const subject = `clock-${RUN}`
    await consumeRateBucket({ route: ROUTE, subjectKind: 'ip', subject, limit: 5, windowSeconds: 60 })
    const rows = await query<{ aligned: boolean }>(
      `SELECT (extract(epoch FROM window_start)::bigint % 60 = 0) AS aligned
         FROM mcp_rate_buckets WHERE bucket_key = $1`,
      [bucketKey(ROUTE, 'ip', subject)]
    )
    expect(rows.rows[0]!.aligned, 'window_start must land on a window boundary').toBe(true)
  }, 15_000)

  it('the raw subject is never stored — only its hash', async () => {
    const subject = `secret-ip-${RUN}`
    await consumeRateBucket({ route: ROUTE, subjectKind: 'ip', subject, limit: 5, windowSeconds: 300 })
    const rows = await query('SELECT * FROM mcp_rate_buckets WHERE bucket_key = $1', [
      bucketKey(ROUTE, 'ip', subject),
    ])
    expect(JSON.stringify(rows.rows[0])).not.toContain(subject)
  }, 15_000)
})
