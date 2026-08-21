-- Migration 580: RATE-07 — fleet-wide rate-limit buckets for the OAuth mutation
-- endpoints. PARIŚEṢA-V4 · GA-2 architecture ruling · 2026-08-21
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHY THIS EXISTS
-- ══════════════════════════════════════════════════════════════════════════════
-- The five OAuth mutation endpoints on the `amjis-mcp` Cloud Run service —
--   POST /mcp/oauth/authorize · GET /mcp/oauth/callback · POST /mcp/oauth/token
--   POST /mcp/oauth/refresh   · POST /mcp/oauth/register
-- had NO rate limiting of any kind. The sidecar's only limiter
-- (`platform-mcp/src/lib/rate_limiter.ts`) is an in-process Map keyed on
-- `key_id`, wired to exactly one call site (`POST /mcp`, server.ts) and only
-- AFTER principal resolution — OAuth mutations carry no `key_id` at all, and
-- four of the five are entirely unauthenticated. That Map is also per-instance
-- (amjis-mcp runs `--min-instances=1 --concurrency=80` and autoscales) and has
-- no eviction, so it is neither fleet-wide nor bounded and must not be
-- represented as either.
--
-- `POST /mcp/oauth/authorize` is the sharpest edge: unauthenticated, and it
-- writes one `mcp_oauth_auth_codes` row per call for an arbitrary, unvalidated
-- `client_id`.
--
-- This table is the shared, atomic, TTL-backed counter that makes a fleet-wide
-- limit expressible. Postgres was chosen over Memorystore/Redis (route 1) and
-- over a Cloud Armor edge policy (route 2) because these exact endpoints ALREADY
-- hard-depend on Postgres-via-the-platform-API for every operation they perform
-- (createDbAuthCode / validateOAuthClient / consumeDbAuthCode / issueDbTokens /
-- refreshDbAccessToken all round-trip to `amjis-web`), so this limiter adds no
-- new failure domain — whereas Redis would. Full ruling, with the rejected
-- alternatives stated:
--   00_ARCHITECTURE/briefs/parisesa/PARISESA_V4_GA2_RULING_RATE07_v1_0.md
--
-- ══════════════════════════════════════════════════════════════════════════════
-- SHAPE — why a single-statement upsert, not a read-then-write
-- ══════════════════════════════════════════════════════════════════════════════
-- Fixed-window counters. One row per (route × subject × window), addressed by a
-- SHA-256 hash so the primary key has bounded width no matter how long or how
-- adversarial the subject string is. `hits` is incremented by ONE
-- `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` statement, which Postgres
-- serialises on the conflicting row: there is no read-then-write window, so the
-- count is exact across every Cloud Run instance. Application code MUST NOT
-- SELECT-then-UPDATE this table — that reintroduces precisely the race the
-- single statement exists to eliminate.
--
-- `window_start` is computed IN SQL as floor(now() / window_seconds), so
-- instances with skewed clocks agree on the window boundary. The client never
-- supplies a timestamp.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- BOUNDEDNESS / RETENTION — no cron job
-- ══════════════════════════════════════════════════════════════════════════════
--   1. A recurring subject contributes exactly ONE row forever: when its window
--      rolls over, the ON CONFLICT branch RESETS hits and re-stamps window_start
--      in place rather than inserting a new row.
--   2. Subjects that never return are reclaimed by a bounded opportunistic prune
--      (`pruneExpiredRateBuckets`, lib/mcp/oauth_rate_limit.ts) over the
--      expires_at index below — a small, LIMITed DELETE run probabilistically on
--      a fraction of checks. There is no scheduled job to forget to provision.
--
-- ══════════════════════════════════════════════════════════════════════════════
-- WHAT THIS MIGRATION DOES *NOT* DO
-- ══════════════════════════════════════════════════════════════════════════════
--   1. It does not touch the authenticated tool path. `lib/mcp/rate_limiter.ts`
--      and `rate_limiter_core.ts` keep their existing in-process RPM window for
--      `POST /mcp` and `/api/mcp/primitives/*`; those are out of RATE-07's scope
--      and are unchanged.
--   2. No ALTER, no DROP, no backfill, no change to any existing table, column,
--      index, policy or grant. This migration only ever adds.
--   3. RLS is neither created nor enabled. This table holds no chart-scoped or
--      user-attributable data (see the subject_kind comment below — the subject
--      VALUE is never stored, only its hash), and it is written exclusively by
--      the app role through one server-side helper.
--
-- Idempotent: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`.
-- Safe to re-run.
-- §N.4: surgical, verified. NEVER edit this file after it has been applied.

BEGIN;

-- ══════════════════════════════════════════════════════════════════════════════
-- 1. THE BUCKET TABLE
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS mcp_rate_buckets (
  -- SHA-256 hex of 'v1|<route>|<subject_kind>|<subject>'. Fixed 64 chars, so a
  -- hostile subject (a 4 KB forged header value) can never widen the key or the
  -- index. This is the ONLY place the subject participates in the schema.
  bucket_key      TEXT        PRIMARY KEY,

  -- Denormalised for operator diagnosis only; NEVER read by the limit decision.
  route           TEXT        NOT NULL,
  subject_kind    TEXT        NOT NULL,

  -- Fixed window: window_start = floor(now / window_seconds), computed in SQL.
  window_start    TIMESTAMPTZ NOT NULL,
  window_seconds  INTEGER     NOT NULL,
  hits            INTEGER     NOT NULL,

  -- window_start + window_seconds. Drives both Retry-After and the prune.
  expires_at      TIMESTAMPTZ NOT NULL,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT mcp_rate_buckets_hits_nonneg     CHECK (hits >= 0),
  CONSTRAINT mcp_rate_buckets_window_positive CHECK (window_seconds > 0)
);

-- Supports the bounded prune of rolled-over rows. Not used by the hot path
-- (which is a primary-key upsert).
CREATE INDEX IF NOT EXISTS mcp_rate_buckets_expires_at_idx
  ON mcp_rate_buckets (expires_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- 2. DOCUMENTATION ON THE OBJECT ITSELF
-- ══════════════════════════════════════════════════════════════════════════════

COMMENT ON TABLE mcp_rate_buckets IS
  'RATE-07 fleet-wide fixed-window rate-limit counters for the five OAuth '
  'mutation endpoints on amjis-mcp. One row per (route x subject x window), '
  'keyed by a SHA-256 hash of the identity so key width is bounded. Incremented '
  'ONLY by the single-statement upsert in '
  'platform/src/lib/mcp/oauth_rate_limit.ts, which Postgres serialises per row '
  '-- do NOT read-then-write this table from application code, that '
  'reintroduces the race the single statement exists to avoid. Rows are reused '
  'across windows and pruned opportunistically by expires_at; no cron job '
  'maintains this table. Ruling: '
  '00_ARCHITECTURE/briefs/parisesa/PARISESA_V4_GA2_RULING_RATE07_v1_0.md';

COMMENT ON COLUMN mcp_rate_buckets.bucket_key IS
  'SHA-256 hex of ''v1|<route>|<subject_kind>|<subject>''. The subject is hashed '
  'rather than stored so (a) the key is fixed-width regardless of input and '
  '(b) client IP addresses do not accumulate here in cleartext.';

COMMENT ON COLUMN mcp_rate_buckets.subject_kind IS
  'Identity CLASS only (ip | client | principal | route_global). The subject '
  'VALUE is intentionally absent from this table -- it exists only inside the '
  'bucket_key hash. Never add a raw-subject column here without a retention '
  'decision: these subjects include client IP addresses.';

COMMENT ON COLUMN mcp_rate_buckets.hits IS
  'Requests counted in the CURRENT window. Charged on every checked request, '
  'INCLUDING ones that are ultimately rejected, so a sustained flood never earns '
  'itself a free reset. Saturates rather than overflowing (see the LEAST() in '
  'the upsert); a saturated counter is by definition already far over any limit.';

COMMENT ON COLUMN mcp_rate_buckets.window_start IS
  'floor(now() / window_seconds), computed server-side in SQL so that Cloud Run '
  'instances with skewed clocks agree on the window boundary. Never supplied by '
  'the caller.';

COMMIT;

-- ══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — non-destructive to any pre-existing object
-- ══════════════════════════════════════════════════════════════════════════════
--   BEGIN;
--     DROP INDEX IF EXISTS mcp_rate_buckets_expires_at_idx;
--     DROP TABLE IF EXISTS mcp_rate_buckets;
--   COMMIT;
--
-- Dropping this table disables fleet-wide OAuth rate limiting. Because the
-- limiter is FAIL-CLOSED, dropping it while the application still calls the
-- limiter will cause the five OAuth mutation endpoints to reject with 503 --
-- set MCP_OAUTH_RATE_LIMIT_ENABLED=false BEFORE rolling this back.
