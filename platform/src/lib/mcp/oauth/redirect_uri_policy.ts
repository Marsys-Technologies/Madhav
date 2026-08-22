/**
 * platform/src/lib/mcp/oauth/redirect_uri_policy.ts
 *
 * SF-004 (PARIŚEṢA-V4): registration-time URI policy for `redirect_uris`.
 * See `00_ARCHITECTURE/briefs/parisesa/SF004_OAUTH_BINDING_CONTRACT_v1_0.md` §5
 * for the full rationale and adversarial self-review.
 *
 * Deliberately duplicated (not imported) in
 * `platform-mcp/src/oauth/redirect_uri_policy.ts` — the two packages do not
 * share a module boundary, the same reason `platform-mcp/src/oauth/types.ts`
 * already duplicates this package's oauth types (see that file's own header).
 * Keep both copies in lockstep if this policy ever changes.
 *
 * This function governs REGISTRATION only. It does not perform the exact-match
 * comparison used at /authorize and /token — that is a separate, simpler
 * string-equality check (see authorize.ts / token.ts), deliberately with no
 * normalization of its own.
 */

/**
 * Returns true iff `uriString` is allowed to be registered as an OAuth client
 * redirect_uri under the SF-004 policy:
 *   1. Must parse as an absolute URI.
 *   2. No fragment (RFC 6749 §3.1.2.2) — checked on the raw string too, not
 *      only the parsed `.hash`.
 *   3. No literal '*' (rejects wildcard host/path patterns outright).
 *   4. Scheme is 'https:', OR scheme is 'http:' AND host is a loopback
 *      address (localhost / 127.0.0.1 / ::1) — the RFC 8252 §7.3 dev-loopback
 *      carve-out. Every other scheme (including custom app-private schemes,
 *      javascript:, data:, file:, non-loopback http:) is rejected.
 *   5. Non-empty host for the schemes permitted by rule 4.
 */
export function isRegistrableRedirectUri(uriString: string): boolean {
  if (typeof uriString !== 'string' || uriString.length === 0) return false

  // Rule 2 (raw-string check, before parsing — belt and suspenders against
  // any parser leniency around fragment placement).
  if (uriString.includes('#')) return false

  // Rule 3.
  if (uriString.includes('*')) return false

  let url: URL
  try {
    url = new URL(uriString)
  } catch {
    return false
  }

  // Rule 2, defensive re-check against the parsed form.
  if (url.hash) return false

  const scheme = url.protocol // lower-cased by the URL parser; includes trailing ':'
  const host = url.hostname.toLowerCase()

  if (scheme === 'https:') {
    return host.length > 0
  }

  if (scheme === 'http:') {
    // WHATWG URL keeps the brackets on a parsed IPv6 hostname (`[::1]`, not
    // `::1`) — checked against both forms defensively.
    return host === 'localhost' || host === '127.0.0.1' || host === '::1' || host === '[::1]'
  }

  // javascript:, data:, file:, custom app-private schemes, anything else.
  return false
}
