/**
 * auth_url_token.ts — pure request-framing helper for the ?api_key= URL-token
 * fallback auth path.
 *
 * B-MCP-LOG-REDACT (DVA Ruling 64 / SAMAPTI_DVARAPALA_LEDGER.md INC-4): this logic
 * used to live inline in server.ts's POST /mcp handler. Extracted here, unchanged in
 * behavior, so the URL-token → Bearer-header synthesis can be unit-tested directly
 * (see __tests__/auth_url_token.test.ts) WITHOUT round-tripping a real credential
 * through a live, Cloud-Run-logged URL.
 *
 * Why this extraction matters: Cloud Run's automatic HTTP request logging captures
 * `httpRequest.requestUrl` (full path + query string, as received) for every request,
 * independent of anything this application logs itself — platform-mcp's own structured
 * logger (lib/logger.ts) never logs the raw request URL. That means the ONLY way to
 * verify "does a request shaped like `POST /mcp?api_key=<key>` authenticate correctly"
 * without writing a live credential into that automatically-captured field is to stop
 * sending it over the network altogether and verify the code path in-process instead.
 * `scripts/operator/mcp_end_to_end_smoke.sh`'s old Probe 4 did the network round-trip
 * on every deploy using the real `mcp-canary-key` Secret Manager value — the recurring
 * leak INC-4 documents. The smoke script's new Probe 4 no longer does that; this module
 * + its test is where the positive-path "the URL-token path is wired correctly"
 * assertion now lives.
 *
 * @module auth_url_token
 */

/**
 * Resolve the effective Authorization header for an incoming /mcp request, honoring
 * the ?api_key= URL-token fallback when no Authorization header is present.
 *
 * Precedence: a real `Authorization` header always wins; `?api_key=` is a fallback
 * for MCP clients that cannot set custom headers.
 *
 * @param headerAuthorization  Raw `Authorization` header value, if present.
 * @param queryApiKey          Raw `api_key` query-string value, if present.
 * @returns  The synthesized Authorization header (or undefined if neither was
 *           supplied) plus whether it was sourced from the URL-token fallback.
 */
export function resolveAuthHeader(
  headerAuthorization: string | undefined,
  queryApiKey: string | undefined
): { authHeader: string | undefined; fromUrlParam: boolean } {
  const fromUrlParam = !headerAuthorization && !!queryApiKey
  const authHeader = headerAuthorization ?? (queryApiKey ? `Bearer ${queryApiKey}` : undefined)
  return { authHeader, fromUrlParam }
}
