/**
 * Post-login `next` validator (SS N-379 item iv).
 *
 * The ONLY function that may turn an untrusted `next` value into a navigation
 * target. Same-origin RELATIVE paths only; anything else returns null and the
 * caller falls back to its default page. Never trust the raw value.
 *
 * A value is accepted only if ALL hold:
 *  - it is a string of 1..512 characters;
 *  - it starts with a SINGLE `/` (never `//`);
 *  - it starts with an allowlisted prefix: `/share/` or `/clients/` AND has at
 *    least one character after it (`/share`, `/share/`, `/clients` and
 *    `/clients/` are all refused: the bare directory is not a target, and the
 *    default page is the right fallback for them);
 *  - it contains no backslash, no `:` (so no scheme, no `javascript:`/`data:`),
 *    no `?` or `#` (a path only, never a query or fragment), no ASCII control
 *    character and no whitespace (any Unicode whitespace, incl. newlines/tabs);
 *  - the same holds after ONE and after TWO rounds of percent-decoding
 *    (`%2F%2F`, `%5C`, `%2e%2e`, `%00`, `%0d%0a`, `%09`, `%252e` ...); a
 *    malformed escape (`%` not followed by two hex digits) is refused;
 *  - no path segment is empty, `.` or `..` (checked on the raw value and on both
 *    decoded forms);
 *  - only URL-unreserved characters, `%` and `/` appear (final allowlist);
 *  - parsing it as `new URL(raw, 'http://localhost')` keeps the origin
 *    `http://localhost` and yields a pathname EQUAL to the input (the URL parser
 *    normalises dot segments, backslashes and tabs/newlines, so any difference
 *    means the value is not what it looks like).
 *
 * Trailing slashes are refused (`/clients/abc/` -> null) because an empty final
 * segment is rejected with the other empty segments.
 */

export const SAFE_NEXT_MAX_LENGTH = 512

const ALLOWED_PREFIXES = ['/share/', '/clients/'] as const

// Control chars (C0 + DEL + C1) and any Unicode whitespace.
const CONTROL_OR_SPACE = /[\u0000-\u001f\u007f-\u009f\s]/
const UNRESERVED_PATH = /^[A-Za-z0-9\-._~%/]+$/
const BASE = 'http://localhost'

function tryDecode(value: string): string | null {
  try {
    return decodeURIComponent(value)
  } catch {
    return null
  }
}

/** Structural checks that must hold for the raw value AND for each decoded form. */
function formIsSafe(form: string): boolean {
  if (!form.startsWith('/') || form.startsWith('//')) return false
  if (form.includes('\\')) return false
  if (form.includes(':')) return false
  if (form.includes('?') || form.includes('#')) return false
  if (CONTROL_OR_SPACE.test(form)) return false
  const segments = form.split('/').slice(1)
  for (const seg of segments) {
    if (seg === '' || seg === '.' || seg === '..') return false
  }
  return true
}

export function safeNextPath(raw: string | null | undefined): string | null {
  if (typeof raw !== 'string') return null
  if (raw.length === 0 || raw.length > SAFE_NEXT_MAX_LENGTH) return null

  const once = tryDecode(raw)
  if (once === null) return null
  const twice = tryDecode(once)
  if (twice === null) return null

  for (const form of [raw, once, twice]) {
    if (!formIsSafe(form)) return null
  }

  if (!UNRESERVED_PATH.test(raw)) return null

  if (!ALLOWED_PREFIXES.some((p) => raw.startsWith(p) && raw.length > p.length)) return null

  let parsed: URL
  try {
    parsed = new URL(raw, BASE)
  } catch {
    return null
  }
  if (parsed.origin !== BASE) return null
  if (parsed.pathname !== raw) return null
  if (parsed.search !== '' || parsed.hash !== '') return null

  return raw
}
