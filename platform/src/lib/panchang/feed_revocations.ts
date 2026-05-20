/**
 * feed_revocations.ts — Per-user iCal feed token revocation list.
 *
 * Strategy: per-user revocation list stored in `panchang_feed_tokens` table.
 * Each issued token gets a row keyed by jti (token ID from the payload).
 * The jti is the only token identifier — no user PII is stored in the token payload.
 * User association (user_id) is stored only in this DB table.
 *
 * Revoke marks rows as revoked. verifyNotRevoked checks if jti is revoked.
 *
 * The table is auto-created on first use (CREATE IF NOT EXISTS) to avoid
 * requiring a migration in this session.
 *
 * Phase: 4C-7 (Item 7)
 */

import { query } from '@/lib/db/client'

// ── Ensure table exists ───────────────────────────────────────────────────────

const CREATE_TABLE_SQL = `
  CREATE TABLE IF NOT EXISTS panchang_feed_tokens (
    id            SERIAL PRIMARY KEY,
    user_id       TEXT        NOT NULL,
    jti           TEXT        NOT NULL UNIQUE,
    location      TEXT        NOT NULL DEFAULT '',
    issued_at     BIGINT      NOT NULL,
    expires_at    BIGINT      NOT NULL,
    revoked_at    BIGINT      DEFAULT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_pft_user_id ON panchang_feed_tokens(user_id);
  CREATE INDEX IF NOT EXISTS idx_pft_jti ON panchang_feed_tokens(jti);
`

async function ensureTable(): Promise<void> {
  await query(CREATE_TABLE_SQL)
}

// ── Register a newly issued token ─────────────────────────────────────────────

export async function registerFeedToken(opts: {
  user_id: string
  jti: string
  location: string
  issued_at: number
  expires_at: number
}): Promise<void> {
  await ensureTable()
  await query(
    `INSERT INTO panchang_feed_tokens (user_id, jti, location, issued_at, expires_at)
     VALUES ($1, $2, $3, $4, $5)
     ON CONFLICT (jti) DO NOTHING`,
    [opts.user_id, opts.jti, opts.location, opts.issued_at, opts.expires_at],
  )
}

// ── Check revocation ──────────────────────────────────────────────────────────

/**
 * Returns true if the token (identified by its jti) has been revoked.
 * Returns false if the token is active OR if the row doesn't exist (backward-compat).
 */
export async function isTokenRevoked(jti: string): Promise<boolean> {
  try {
    await ensureTable()
    const result = await query<{ revoked_at: number | null }>(
      `SELECT revoked_at FROM panchang_feed_tokens WHERE jti = $1`,
      [jti],
    )
    if (result.rows.length === 0) return false // unknown token = not revoked (legacy)
    return result.rows[0].revoked_at !== null
  } catch {
    // DB error — fail open (don't block feed delivery for DB issues)
    return false
  }
}

// ── List active tokens for a user ─────────────────────────────────────────────

export interface FeedTokenRecord {
  jti: string
  location: string
  issued_at: number
  expires_at: number
  revoked_at: number | null
}

export async function listUserTokens(user_id: string): Promise<FeedTokenRecord[]> {
  await ensureTable()
  const result = await query<FeedTokenRecord>(
    `SELECT jti, location, issued_at, expires_at, revoked_at
     FROM panchang_feed_tokens
     WHERE user_id = $1
     ORDER BY issued_at DESC`,
    [user_id],
  )
  return result.rows
}

// ── Revoke tokens for a user ──────────────────────────────────────────────────

/**
 * Revoke all active tokens for a user.
 * After calling this, all previously-signed feed URLs for the user will return 401.
 */
export async function revokeAllUserTokens(user_id: string): Promise<number> {
  await ensureTable()
  const now = Math.floor(Date.now() / 1000)
  const result = await query<{ id: number }>(
    `UPDATE panchang_feed_tokens
     SET revoked_at = $2
     WHERE user_id = $1 AND revoked_at IS NULL
     RETURNING id`,
    [user_id, now],
  )
  return result.rowCount ?? 0
}

/**
 * Revoke a specific token by its jti.
 */
export async function revokeToken(user_id: string, jti: string): Promise<boolean> {
  await ensureTable()
  const now = Math.floor(Date.now() / 1000)
  const result = await query(
    `UPDATE panchang_feed_tokens
     SET revoked_at = $3
     WHERE user_id = $1 AND jti = $2 AND revoked_at IS NULL`,
    [user_id, jti, now],
  )
  return (result.rowCount ?? 0) > 0
}
