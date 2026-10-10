/**
 * identity_cross_check.ts — the platform-mcp side of the ONE shared identity block (SS N-360, Lahiri-primary PR-3).
 * ==============================================================================================================
 * The block (`identity_cross_check`) is the SAME labelled envelope as `ayanamsha_cross_check`
 * (platform/src/lib/retrieval/ayanamsha_cross_check.ts `buildAyanamshaCrossCheck`), restricted to the four
 * identity facts: Lagna sign, Moon sign, Moon nakshatra, current Mahadasha lord. This package NEVER compares
 * ayanamshas: there is deliberately no second five-way comparison here and therefore no builder mirror.
 *
 *   chart_snapshot  built by the platform handler (always on, compact); passes through the MCP tool untouched.
 *   graha_portrait  built by the platform handler (the Moon always; another graha only with include_cross_check).
 *   dossier         a pure pager of compiled slice bundles with no chart values of its own: its tool handler asks
 *                   the platform's chart_snapshot capability for the block (the same proxied handler) and attaches
 *                   it to page 1, UNCOMPARED, as a trimmable secondary corroboration.
 *   get_chart_header  carries NO cross-check: it rides on every envelope (noise).
 *
 * Only the response key is mirrored (parity test: platform ayanamsha_cross_check.test.ts and
 * response_budget_cross_check_first.test.ts), and the key is registered TRIMMABLE (never hardFloor) in
 * response_budget.ts `CROSS_CHECK_FIELDS`.
 */
import type { Principal } from '../types.js'
import { PRIMARY_AYANAMSHA } from './ayanamsha.js'

/** Mirrors platform `IDENTITY_CROSS_CHECK_KEY` (parity-tested). */
export const IDENTITY_CROSS_CHECK_KEY = 'identity_cross_check' as const

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

/** The honest unavailable form when the platform could not supply the block (mirrors the platform's shape). */
export function identityCrossCheckReadFailed(): Record<string, unknown> {
  return {
    not_available: true,
    reason: 'cross_check_read_failed',
    heading: 'Cross-check, not the reading',
    primary_id: PRIMARY_AYANAMSHA,
  }
}

/** Pull the identity block out of a proxied capability result (`{content, is_error}` or the bare content). */
export function extractIdentityCrossCheck(result: unknown): Record<string, unknown> | null {
  if (!result || typeof result !== 'object') return null
  const r = result as Record<string, unknown>
  if (r['is_error'] === true) return null
  const inner = (r['content'] && typeof r['content'] === 'object' ? r['content'] : r) as Record<string, unknown>
  const block = inner[IDENTITY_CROSS_CHECK_KEY]
  return block && typeof block === 'object' && !Array.isArray(block) ? (block as Record<string, unknown>) : null
}

/**
 * Ask the platform for the chart's identity block through the SAME proxied handler chart_snapshot uses (default
 * args: Lahiri-primary, D1 only). Never throws: any failure is the honest `cross_check_read_failed` form.
 */
export async function fetchDossierIdentityCrossCheck(
  chart_id: string,
  principal: Principal,
  fetchImpl: typeof fetch = fetch,
): Promise<Record<string, unknown>> {
  try {
    const res = await fetchImpl(`${PLATFORM_URL}/api/retrieval/capability`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        'X-MCP-Key-Id': principal.key_id,
      },
      body: JSON.stringify({ uri: 'marsys://tool/L1/chart_snapshot', args: { chart_id } }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) return identityCrossCheckReadFailed()
    const data = await res.json() as { ok?: boolean; content?: unknown }
    if (!data.ok) return identityCrossCheckReadFailed()
    return extractIdentityCrossCheck(data.content) ?? identityCrossCheckReadFailed()
  } catch {
    return identityCrossCheckReadFailed()
  }
}

/**
 * Attach the block to a dossier page (page 1 only: it is chart-level, not page-level, so repeating it on every
 * page would only spend the client's budget). The page's own accounting (`page_bytes`, coverage, gate) is left
 * exactly as measured. If the block does not fit the page's byte budget it is NOT attached and the shed is
 * disclosed by a judgment flag: the cross-check is secondary corroboration and never displaces the catalog page.
 */
export function attachIdentityCrossCheckToPage<P extends { page_n: number; budget_kb_applied: number; judgment_flags: string[] }>(
  page: P,
  block: Record<string, unknown>,
): P & { identity_cross_check?: Record<string, unknown> } {
  if (page.page_n !== 1) return page
  const pageBytes = Buffer.byteLength(JSON.stringify(page), 'utf8')
  const blockBytes = Buffer.byteLength(JSON.stringify({ [IDENTITY_CROSS_CHECK_KEY]: block }), 'utf8')
  if (pageBytes + blockBytes > page.budget_kb_applied * 1024) {
    return { ...page, judgment_flags: [...page.judgment_flags, 'identity_cross_check_shed_for_page_budget'] }
  }
  return { ...page, [IDENTITY_CROSS_CHECK_KEY]: block }
}
