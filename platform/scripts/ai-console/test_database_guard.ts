import { isIP } from 'node:net'
import { parse as parsePgConnectionString } from 'pg-connection-string'

const ERROR = 'AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL'

function loopback(host: string): boolean {
  const value = host.startsWith('[') && host.endsWith(']') ? host.slice(1, -1) : host
  return value.toLowerCase() === 'localhost' || value === '::1'
    || (isIP(value) === 4 && value.split('.')[0] === '127')
}

export function assertDisposableAiConsoleDatabaseUrl(value: string): string {
  try {
    const url = new URL(value)
    if (!['postgres:', 'postgresql:'].includes(url.protocol) || url.search || url.hash
      || !url.hostname || !loopback(url.hostname)) throw new Error(ERROR)
    const parsed = parsePgConnectionString(value)
    const database = parsed.database ?? ''
    const host = parsed.host ?? ''
    if (!loopback(host) || !/^ai_console_test_[A-Za-z0-9_]+$/.test(database)) throw new Error(ERROR)
    const urlDatabase = decodeURIComponent(url.pathname.slice(1))
    const urlHost = url.hostname.startsWith('[') && url.hostname.endsWith(']')
      ? url.hostname.slice(1, -1) : url.hostname
    const parsedHost = host.startsWith('[') && host.endsWith(']') ? host.slice(1, -1) : host
    if (database !== urlDatabase || parsedHost.toLowerCase() !== urlHost.toLowerCase()) throw new Error(ERROR)
    return value
  } catch {
    throw new Error(ERROR)
  }
}
