/**
 * client_ip.ts — the ONE place the platform derives a client IP from
 * `X-Forwarded-For` for rate limiting (SS N-373 / PR-S1, item 4).
 *
 * ── THE RULE ────────────────────────────────────────────────────────────────
 * Every proxy hop APPENDS to `X-Forwarded-For`. A client that sends
 * `X-Forwarded-For: 1.2.3.4` reaches the app as `1.2.3.4, <peer Google saw>`.
 * So the LEFTMOST entry is fully client-controlled and is NEVER used. The
 * trusted identity is the entry appended by our own infrastructure: counted from
 * the RIGHT, `TRUSTED_PROXY_HOPS` entries in (1 = the rightmost entry).
 * Single-value headers (`X-Real-IP`, `CF-Connecting-IP`, `True-Client-IP`) are
 * ignored: behind Cloud Run they are verbatim caller input.
 *
 * ── THE HOP COUNT (documented decision) ─────────────────────────────────────
 * `TRUSTED_PROXY_HOPS = 1`. amjis-web runs on Cloud Run; Google's front end
 * appends the address it received the connection from as the last
 * `X-Forwarded-For` entry. This is the same value and the same reasoning the
 * MCP service already ships (`MCP_TRUSTED_PROXY_HOPS`, platform-mcp/src/lib/
 * oauth_rate_limit.ts, PARISESA V4 GA-2 ruling section 3.2).
 *
 * DISCLOSED, NOT RESOLVED FROM THE REPO: the public hostname is served through
 * Firebase Hosting (`firebase.json` rewrites `**` to amjis-web), in addition to
 * the direct `*.run.app` URL. If that path appends a further hop, the rightmost
 * entry is the Hosting front end rather than the visitor, and the visitors on
 * that path share ONE bucket. That failure is conservative (over-restrictive,
 * never permissive, and not steerable onto a chosen third party), which is why
 * the count is an explicit operator setting: set `MARSYS_TRUSTED_PROXY_HOPS` to
 * match the verified live chain. Raising it without verifying would trust an
 * entry a caller can forge, which is the permissive direction.
 *
 * Fewer entries than hops, an empty header, or a non-IP value at the trusted
 * position all return `null`: the caller then uses ONE shared bucket
 * (`ipRateLimitKey(null)`), never a client-chosen key.
 */
import { isIP } from 'node:net'

/** Number of proxy hops in front of the app that append to X-Forwarded-For. */
export const TRUSTED_PROXY_HOPS = 1

const MAX_HOPS = 8

/** Operator override (`MARSYS_TRUSTED_PROXY_HOPS`); anything not 1..8 falls back to the default. */
export function trustedProxyHops(
  env: Record<string, string | undefined> = process.env,
): number {
  const raw = env.MARSYS_TRUSTED_PROXY_HOPS
  if (raw === undefined || raw.trim() === '') return TRUSTED_PROXY_HOPS
  const n = Number(raw)
  if (!Number.isInteger(n) || n < 1 || n > MAX_HOPS) return TRUSTED_PROXY_HOPS
  return n
}

function normalise(entry: string): string | null {
  let ip = entry.trim().toLowerCase()
  if (ip.startsWith('::ffff:') && isIP(ip.slice(7)) === 4) ip = ip.slice(7)
  return isIP(ip) === 0 ? null : ip
}

/**
 * The client IP appended by our own infrastructure, or `null` when it cannot be
 * established. Never reads the leftmost (client-controlled) entry unless the
 * chain is exactly as long as the trusted hop count.
 */
export function getTrustedClientIp(
  headers: { get(name: string): string | null },
  hops: number = trustedProxyHops(),
): string | null {
  const raw = headers.get('x-forwarded-for')
  if (!raw) return null
  const entries = raw.split(',').map((e) => e.trim()).filter((e) => e.length > 0)
  const index = entries.length - hops
  if (index < 0) return null
  return normalise(entries[index])
}

function expandIpv6(ip: string): number[] | null {
  let text = ip
  const dotted = text.match(/^(.*:)(\d+\.\d+\.\d+\.\d+)$/)
  if (dotted) {
    const o = dotted[2].split('.').map(Number)
    text = `${dotted[1]}${((o[0] << 8) | o[1]).toString(16)}:${((o[2] << 8) | o[3]).toString(16)}`
  }
  const halves = text.split('::')
  if (halves.length > 2) return null
  const head = halves[0] ? halves[0].split(':') : []
  const tail = halves.length === 2 && halves[1] ? halves[1].split(':') : []
  const fill = 8 - head.length - tail.length
  if (halves.length === 1 ? head.length !== 8 : fill < 0) return null
  const groups = [...head, ...Array<string>(halves.length === 2 ? fill : 0).fill('0'), ...tail]
  const nums = groups.map((g) => parseInt(g, 16))
  return nums.length === 8 && nums.every((n) => Number.isInteger(n) && n >= 0 && n <= 0xffff) ? nums : null
}

/**
 * Rate-limit bucket key for a trusted IP. IPv6 collapses to its /64: a single
 * subscriber is routinely handed a whole /64, so keying on the full address
 * would let one attacker rotate through 2^64 buckets. `null` (no trusted IP)
 * maps to one shared bucket.
 */
export function ipRateLimitKey(ip: string | null): string {
  if (!ip) return 'unknown'
  if (isIP(ip) !== 6) return ip
  const g = expandIpv6(ip)
  if (!g) return ip
  return `${g.slice(0, 4).map((n) => n.toString(16)).join(':')}::/64`
}
