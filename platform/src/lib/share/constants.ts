/**
 * Share-link constants (SS N-376 / PR-S4).
 *
 * A share link is an authenticated convenience link, not a public capability:
 * the viewer must hold a verified, active session (see `app/share/[slug]/page.tsx`)
 * AND the slug. The slug (10 chars, ~59 bits) is not a strong enough credential on
 * its own to leave valid forever, so every NEW share expires.
 *
 * Existing rows are deliberately untouched (no migration, no data change): rows
 * with `expires_at IS NULL` keep working until the owner revokes them.
 */
export const SHARE_DEFAULT_TTL_DAYS = 30

/** Share create/revoke calls allowed per verified user per window. */
export const SHARE_MUTATION_LIMIT = 20
export const SHARE_MUTATION_WINDOW_MS = 60 * 60 * 1000
/** Hard cap on live per-user counters held in memory by the share limiter. */
export const SHARE_MUTATION_MAX_ENTRIES = 2000
