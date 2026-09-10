/**
 * oauth_rate_limit.ts — RATE-07 fleet-wide rate-limit buckets (PARIŚEṢA-V4).
 *
 * ── WHY THIS IS NOT `rate_limiter_core.ts` ──────────────────────────────────
 * `rate_limiter_core.ts`'s header carries a "never a second implementation"
 * rule, and it is right to. This file is not a second implementation of THAT
 * limiter — it is a different limiter with a different contract, and the two
 * differ on every property that matters for OAuth:
 *
 *   rate_limiter_core.checkRpm     this module
 *   ---------------------------    ------------------------------------------
 *   in-process Map                 shared Postgres table (fleet-wide)
 *   per-instance count             exact count across every Cloud Run instance
 *   no eviction (grows forever)    bounded: row reuse + expires_at prune
 *   sync, cannot fail              async, CAN fail — and fails CLOSED
 *   caller-supplied opaque key     structured (route, subject_kind, subject)
 *
 * `checkRpm` remains the right tool for the authenticated tool path, and this
 * change does not touch it. It is the wrong tool for an unauthenticated OAuth
 * mutation endpoint, because "limit × instance_count" is not a limit and a
 * counter with no eviction is a memory leak an anonymous caller can drive.
 *
 * ── THE ATOMICITY CONTRACT ──────────────────────────────────────────────────
 * `consumeRateBucket` performs the whole check-and-increment in ONE SQL
 * statement: `INSERT ... ON CONFLICT (bucket_key) DO UPDATE ... RETURNING`.
 * Postgres takes a row lock on the conflicting tuple, so concurrent callers
 * serialise and each observes a distinct `hits` value. There is deliberately
 * NO `SELECT` here: a read-then-write pair, even inside a transaction at READ
 * COMMITTED, lets two instances read the same count and both decide "allowed".
 * Anyone editing this file must preserve the single-statement property; the
 * structural guard in `src/lib/__tests__/mcp/oauth_rate_limit.test.ts`
 * ("SQL structural contract") fails the build if a SELECT-then-UPDATE shape
 * reappears.
 *
 * ── WINDOW SEMANTICS ────────────────────────────────────────────────────────
 * Fixed window, not sliding. `window_start = floor(now / window_seconds)` is
 * computed IN SQL so instances with skewed clocks agree on the boundary. A
 * fixed window admits the standard boundary burst (up to 2× limit across two
 * adjacent windows); that is an accepted, documented property, not an oversight
 * — these are abuse ceilings, not fairness quotas, and a sliding-window
 * implementation would need either a per-request row (unbounded) or a
 * read-then-write (races).
 *
 * @module oauth_rate_limit
 */

import 'server-only'
import { createHash } from 'node:crypto'

import { query } from '@/lib/db/client'

// ── Bounds on caller-supplied parameters ─────────────────────────────────────
// The only caller is the MCP sidecar, authenticated by MCP_INTERNAL_TOKEN. These
// bounds still exist because "the caller is trusted" is a property that decays:
// a bug (or a compromised token) that asked for limit=1_000_000_000 would
// silently disable the control while every log line still said "rate limited".

export const MIN_WINDOW_SECONDS = 1
export const MAX_WINDOW_SECONDS = 86_400
export const MIN_LIMIT = 1
export const MAX_LIMIT = 100_000

/** Identity classes a bucket may be keyed on. */
export const SUBJECT_KINDS = ['ip', 'client', 'principal', 'route_global'] as const
export type SubjectKind = (typeof SUBJECT_KINDS)[number]

export interface ConsumeRateBucketArgs {
  /** Logical route being limited, e.g. 'oauth_authorize'. */
  route: string
  /** Identity class of `subject`. */
  subjectKind: SubjectKind
  /**
   * The identity value. Hashed into `bucket_key` and never stored in cleartext.
   * For `route_global` this is conventionally the empty string.
   */
  subject: string
  /** Max requests allowed per window. */
  limit: number
  /** Window length in seconds. */
  windowSeconds: number
}

export interface RateBucketDecision {
  allowed: boolean
  limit: number
  /** Hits recorded in the current window INCLUDING this request. */
  hits: number
  /** `limit - hits`, floored at 0. */
  remaining: number
  windowSeconds: number
  /** Seconds until the current window expires. Always >= 1 when not allowed. */
  retryAfterSeconds: number
}

/**
 * `hits` is a 32-bit INTEGER. A flood that is already thousands of times over
 * any limit must not be able to overflow the column and wrap to a negative
 * value (which would read as "allowed"). Saturating is safe: any value at or
 * above this cap is, by construction, far past every limit we permit.
 */
const HITS_SATURATION_CAP = 2_000_000_000

/** Namespaced so a future key-scheme change can be rolled without collisions. */
const BUCKET_KEY_VERSION = 'v1'

/**
 * Derive the fixed-width primary key. Exported for tests and for the sidecar's
 * documentation only — the hash is computed here, server-side; the sidecar
 * sends the plain subject over the internal-token channel.
 */
export function bucketKey(
  route: string,
  subjectKind: SubjectKind,
  subject: string,
  windowSeconds: number,
): string {
  // `windowSeconds` participates in the key so that two call sites charging the
  // same (route, kind, subject) with DIFFERENT window lengths cannot collide on
  // one row and silently re-stamp each other's window. No current call site does
  // that; including it makes the invariant structural instead of conventional.
  return createHash('sha256')
    .update(`${BUCKET_KEY_VERSION}|${route}|${subjectKind}|${subject}|${windowSeconds}`)
    .digest('hex')
}

/**
 * The one statement. Extracted as a constant so the structural guard test can
 * assert its shape without executing it against a database.
 *
 * $1 bucket_key · $2 route · $3 subject_kind · $4 window_seconds · $5 hits cap
 */
export const CONSUME_BUCKET_SQL = `
WITH w AS (
  SELECT
    to_timestamp(floor(extract(epoch FROM now()) / $4::numeric) * $4::numeric) AS window_start
)
INSERT INTO mcp_rate_buckets AS b
  (bucket_key, route, subject_kind, window_start, window_seconds, hits, expires_at, updated_at)
SELECT
  $1, $2, $3,
  w.window_start,
  $4::int,
  1,
  w.window_start + make_interval(secs => $4::int),
  now()
FROM w
ON CONFLICT (bucket_key) DO UPDATE SET
  -- Same window -> increment (saturating). Rolled-over window -> reset to 1 and
  -- re-stamp in place, so a recurring subject never accumulates a second row.
  hits = CASE
           WHEN b.window_start = EXCLUDED.window_start
             THEN LEAST(b.hits + 1, $5::int)
           ELSE 1
         END,
  route          = EXCLUDED.route,
  subject_kind   = EXCLUDED.subject_kind,
  window_start   = EXCLUDED.window_start,
  window_seconds = EXCLUDED.window_seconds,
  expires_at     = EXCLUDED.expires_at,
  updated_at     = now()
RETURNING
  hits,
  window_seconds,
  GREATEST(1, CEIL(EXTRACT(EPOCH FROM (expires_at - now())))::int) AS retry_after_seconds
`

/**
 * Bounded prune of rolled-over rows. `LIMIT` inside a ctid sub-select because
 * `DELETE ... LIMIT` is not valid Postgres. The grace interval keeps a row
 * around slightly past its window so a request landing right on the boundary
 * cannot delete the bucket it is about to be counted in.
 */
export const PRUNE_BUCKETS_SQL = `
DELETE FROM mcp_rate_buckets
WHERE ctid IN (
  SELECT ctid FROM mcp_rate_buckets
  WHERE expires_at < now() - interval '5 minutes'
  LIMIT $1
)
`

/** Rows removed per prune pass. Small enough to never hold a long lock. */
export const PRUNE_BATCH_SIZE = 500

/** Roughly 1 call in N triggers a prune pass. */
export const PRUNE_PROBABILITY_DENOMINATOR = 64

export class RateBucketArgumentError extends Error {}

function validate(args: ConsumeRateBucketArgs): void {
  if (!args.route || args.route.length > 64) {
    throw new RateBucketArgumentError('route must be a non-empty string of at most 64 chars')
  }
  if (!SUBJECT_KINDS.includes(args.subjectKind)) {
    throw new RateBucketArgumentError(`subject_kind must be one of: ${SUBJECT_KINDS.join(', ')}`)
  }
  if (typeof args.subject !== 'string') {
    throw new RateBucketArgumentError('subject must be a string')
  }
  if (!Number.isInteger(args.limit) || args.limit < MIN_LIMIT || args.limit > MAX_LIMIT) {
    throw new RateBucketArgumentError(`limit must be an integer in [${MIN_LIMIT}, ${MAX_LIMIT}]`)
  }
  if (
    !Number.isInteger(args.windowSeconds) ||
    args.windowSeconds < MIN_WINDOW_SECONDS ||
    args.windowSeconds > MAX_WINDOW_SECONDS
  ) {
    throw new RateBucketArgumentError(
      `window_seconds must be an integer in [${MIN_WINDOW_SECONDS}, ${MAX_WINDOW_SECONDS}]`
    )
  }
}

/**
 * Charge one request against a bucket and report whether it is allowed.
 *
 * THROWS on database failure. It does not swallow the error and return
 * `allowed: true` — this limiter is the authority for an unauthenticated
 * mutation surface, and a limiter that fails open is indistinguishable from no
 * limiter at exactly the moment (a database under load) an attacker most wants
 * it gone. Callers translate the throw into a fail-closed rejection.
 *
 * NOTE the charge-then-decide order: a request over the limit is still counted.
 * That is deliberate. If rejected requests were not counted, a caller pinned at
 * the limit would see its window drain and refill at the natural boundary while
 * still hammering the endpoint; counting them keeps the window pinned for as
 * long as the abuse continues.
 */
export async function consumeRateBucket(args: ConsumeRateBucketArgs): Promise<RateBucketDecision> {
  validate(args)

  const key = bucketKey(args.route, args.subjectKind, args.subject, args.windowSeconds)

  const result = await query<{
    hits: number
    window_seconds: number
    retry_after_seconds: number
  }>(CONSUME_BUCKET_SQL, [
    key,
    args.route,
    args.subjectKind,
    args.windowSeconds,
    HITS_SATURATION_CAP,
  ])

  const row = result.rows[0]
  if (!row) {
    // An upsert with RETURNING always returns exactly one row. No row means the
    // statement did not do what this module believes it does — fail closed
    // rather than invent a permissive answer (CLAUDE.md §N.8).
    throw new Error('[oauth_rate_limit] upsert returned no row — refusing to assume "allowed"')
  }

  const hits = Number(row.hits)
  const allowed = hits <= args.limit

  return {
    allowed,
    limit: args.limit,
    hits,
    remaining: Math.max(0, args.limit - hits),
    windowSeconds: Number(row.window_seconds),
    retryAfterSeconds: Math.max(1, Number(row.retry_after_seconds)),
  }
}

/**
 * Delete a bounded batch of long-expired buckets. Best-effort: a prune failure
 * is logged and swallowed, because failing a legitimate request over garbage
 * collection would be a worse outcome than a slightly larger table. This is the
 * ONE place in this module where swallowing is correct — it does not touch the
 * limit decision.
 */
export async function pruneExpiredRateBuckets(batchSize = PRUNE_BATCH_SIZE): Promise<number> {
  try {
    const result = await query(PRUNE_BUCKETS_SQL, [batchSize])
    return result.rowCount ?? 0
  } catch (err) {
    console.warn('[oauth_rate_limit] prune failed (non-fatal):', err)
    return 0
  }
}

/** True on roughly 1 call in {@link PRUNE_PROBABILITY_DENOMINATOR}. */
export function shouldPrune(random: () => number = Math.random): boolean {
  return random() < 1 / PRUNE_PROBABILITY_DENOMINATOR
}
