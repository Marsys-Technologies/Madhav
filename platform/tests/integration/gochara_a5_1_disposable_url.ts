/**
 * Pravāha A5.1 — the disposable-database boundary for the live-DB migration
 * suite (ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 F10).
 *
 * The suite DROPs charts / coverage / publication / the migration ledger with
 * CASCADE, so it must never be pointed at anything that is not obviously a
 * throwaway. The round-2 guard searched the WHOLE connection string for the
 * token `gochara_a51_test`, which a query string, user name or host could
 * satisfy while the database was still `production`. This helper PARSES the
 * URL and validates the actual database target:
 *
 *   - scheme is postgres:// or postgresql://;
 *   - the database name (the path, minus the leading slash) is EXACTLY
 *     `gochara_a51_test`;
 *   - the host is a loopback address (localhost / 127.0.0.1 / ::1) or empty
 *     (unix socket) — a remote host is never a disposable boundary here.
 *
 * Nothing in the user name, password, query string or fragment can satisfy
 * the check. Pure: it connects to nothing.
 */

export const DISPOSABLE_DB_NAME = 'gochara_a51_test'

const LOOPBACK_HOSTS = new Set(['', 'localhost', '127.0.0.1', '::1', '[::1]'])

export class DisposableDbUrlError extends Error {
  constructor(reason: string) {
    super(
      `GOCHARA_A51_TEST_DATABASE_URL is not a disposable database boundary: ${reason}. ` +
      `This suite creates and DROPs schema objects with CASCADE and must only run against a ` +
      `loopback database named exactly \`${DISPOSABLE_DB_NAME}\`.`,
    )
    this.name = 'DisposableDbUrlError'
  }
}

/** Throws DisposableDbUrlError unless `raw` names the disposable database on a loopback host. */
export function assertDisposableA51DatabaseUrl(raw: string | undefined): void {
  if (!raw) throw new DisposableDbUrlError('no URL supplied')
  let url: URL
  try {
    url = new URL(raw)
  } catch {
    throw new DisposableDbUrlError('the value is not a parseable URL')
  }
  if (url.protocol !== 'postgres:' && url.protocol !== 'postgresql:') {
    throw new DisposableDbUrlError(`scheme "${url.protocol}" is not postgres:// or postgresql://`)
  }
  const dbName = decodeURIComponent(url.pathname.replace(/^\/+/, ''))
  if (dbName !== DISPOSABLE_DB_NAME) {
    throw new DisposableDbUrlError(`the database in the path is "${dbName || '(none)'}", not "${DISPOSABLE_DB_NAME}"`)
  }
  if (!LOOPBACK_HOSTS.has(url.hostname)) {
    throw new DisposableDbUrlError(`host "${url.hostname}" is not a loopback address`)
  }
}
