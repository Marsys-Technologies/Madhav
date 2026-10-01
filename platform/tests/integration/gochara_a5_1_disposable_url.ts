/**
 * Pravāha A5.1 — the disposable-database boundary for the live-DB migration
 * suite (ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 F10, v1_2 N11).
 *
 * The suite DROPs charts / coverage / publication / the migration ledger with
 * CASCADE, so it must never be pointed at anything that is not obviously a
 * throwaway. Round 3 parsed the WHATWG URL; the reviewer showed the DRIVER
 * (pg-connection-string 2.12.0) resolves a different target for
 * `?host=…` overrides and doubled path slashes. This helper therefore
 * validates the driver's OWN parse of the connection string and returns the
 * fully resolved configuration the suite must hand to `new Pool(...)` — the
 * raw string is never given to the driver.
 *
 * Accepted iff, in the driver's view:
 *   - scheme is postgres:// or postgresql://;
 *   - the database is EXACTLY `gochara_a51_test` (so `//gochara_a51_test`,
 *     which the driver reads as `/gochara_a51_test`, is refused);
 *   - the host is an EXPLICIT loopback address (localhost / 127.0.0.1 / ::1) —
 *     empty/default hosts and every remote host are refused;
 *   - the port is explicit (no library default decides the target);
 *   - the query string carries no target-changing or default-dependent option
 *     (only `application_name` and `sslmode` are allowed; `host`, `hostaddr`,
 *     `dbname`, `options`, `service`, `passfile`, `port`, … are refused);
 *   - there is no fragment.
 * Pure: it connects to nothing.
 */
import { parse } from 'pg-connection-string'

export const DISPOSABLE_DB_NAME = 'gochara_a51_test'

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '::1', '[::1]'])
const ALLOWED_QUERY_KEYS = new Set(['application_name', 'sslmode'])

export interface DisposableA51Config {
  host: string
  port: number
  database: string
  user?: string
  password?: string
  application_name?: string
  ssl?: false
}

export class DisposableDbUrlError extends Error {
  constructor(reason: string) {
    super(
      `GOCHARA_A51_TEST_DATABASE_URL is not a disposable database boundary: ${reason}. ` +
      `This suite creates and DROPs schema objects with CASCADE and must only run against an ` +
      `explicit loopback host:port and a database named exactly \`${DISPOSABLE_DB_NAME}\`.`,
    )
    this.name = 'DisposableDbUrlError'
  }
}

/**
 * Validates `raw` against the driver's effective configuration and returns the resolved
 * config to connect with. Throws DisposableDbUrlError otherwise. Connects to nothing.
 */
export function resolveDisposableA51Config(raw: string | undefined): DisposableA51Config {
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
  if (url.hash) throw new DisposableDbUrlError('a URL fragment is not allowed')
  for (const key of url.searchParams.keys()) {
    if (!ALLOWED_QUERY_KEYS.has(key)) {
      throw new DisposableDbUrlError(`query option "${key}" is not allowed (it can change the effective target)`)
    }
  }

  // The driver's view (pg-connection-string): this is what node-postgres would connect to.
  const driver = parse(raw)
  const database = driver.database ?? ''
  if (database !== DISPOSABLE_DB_NAME) {
    throw new DisposableDbUrlError(`the driver would connect to database "${database || '(none)'}", not "${DISPOSABLE_DB_NAME}"`)
  }
  const host = driver.host ?? ''
  if (!host) throw new DisposableDbUrlError('the driver would use a default host — an explicit loopback host is required')
  if (!LOOPBACK_HOSTS.has(host)) {
    throw new DisposableDbUrlError(`the driver would connect to host "${host}", which is not a loopback address`)
  }
  const portText = driver.port ?? ''
  if (!/^[0-9]{1,5}$/.test(portText)) {
    throw new DisposableDbUrlError('an explicit numeric port is required (no library default decides the target)')
  }
  const port = Number(portText)
  if (port < 1 || port > 65535) throw new DisposableDbUrlError(`port ${portText} is out of range`)

  const config: DisposableA51Config = {
    host: host === '[::1]' ? '::1' : host,
    port,
    database,
  }
  if (driver.user) config.user = driver.user
  if (driver.password) config.password = driver.password
  if (typeof driver.application_name === 'string' && driver.application_name) {
    config.application_name = driver.application_name
  }
  if (url.searchParams.has('sslmode')) {
    if (url.searchParams.get('sslmode') !== 'disable') {
      throw new DisposableDbUrlError('only sslmode=disable is allowed for the loopback disposable database')
    }
    config.ssl = false
  }
  return config
}

/** Backwards-compatible assertion form (throws or returns nothing). */
export function assertDisposableA51DatabaseUrl(raw: string | undefined): void {
  resolveDisposableA51Config(raw)
}
