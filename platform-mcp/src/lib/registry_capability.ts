/**
 * Shared raw registry RPC for MCP tools and resources. Returns the capability's
 * ToolResult (outer HTTP .content), not its inner payload. Callers own ToolResult
 * validation. Uses the existing canonical 20s timeout and dispatcher cache policy.
 */
import type { Principal } from '../types.js'

const PLATFORM_URL = (
  process.env['PLATFORM_URL'] ?? 'http://localhost:3000'
).replace(/\/$/, '')

// Service-to-service token — must match MCP_INTERNAL_TOKEN on amjis-web.
// Required by /api/retrieval/capability (F1 gate, M0.5).
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

/**
 * R5.1 C2 item 3 (Denial ≠ empty): when the platform route already built a distinct
 * `entitlement_denied` McpErrorEnvelope (denial block present), preserve that signal in the
 * thrown error's message instead of collapsing it to a generic "failed (401): <truncated
 * text>" — the whole point of the distinct envelope is lost if the MCP-facing error message
 * can't be told apart from any other 401. Falls back to the generic message for every other
 * error shape (never assumes denial when the body doesn't say so).
 */
export function describeProxyFailure(tool: string, status: number, bodyText: string): string {
  try {
    const parsed = JSON.parse(bodyText) as { error?: { class?: string; message?: string }; denial?: { chart_id?: string; permission_required?: string } }
    if (parsed?.error?.class === 'entitlement_denied' || parsed?.denial) {
      const chartId = parsed.denial?.chart_id ?? 'unknown'
      const required = parsed.denial?.permission_required ?? 'view'
      return `[registry_bridge] ENTITLEMENT_DENIED: '${tool}' — caller lacks ${required} access to chart ${chartId} ` +
        `(distinct from an empty result — this denial does not determine whether the chart exists). ${parsed.error?.message ?? ''}`.trim()
    }
  } catch {
    // Not JSON / not the denial shape — fall through to the generic message below.
  }
  return `[registry_bridge] primitive call '${tool}' failed (${status}): ${bodyText.slice(0, 200)}`
}

// ── Registry capability caller ────────────────────────────────────────────────

/**
 * Call a registry capability via the platform's /api/retrieval/capability endpoint.
 *
 * The MCP server is a separate Node package (platform-mcp) and cannot import
 * the Next.js platform's TypeScript modules directly. Instead, it calls the
 * platform's HTTP API, which holds the live registry and DB connection.
 *
 * Endpoint: POST /api/retrieval/capability
 * Body: { uri, args }
 * Response: { ok: boolean, content: unknown, error?: string }
 */
export async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  _chartId: string | undefined,   // chart_id is already in args; kept for call-site clarity
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding): the previous generic message embedded the raw HTTP
    // status code as literal text ("capability call failed (401): ...") — the battery's own
    // "no_raw_401_403_text" assertion correctly flags that as a leak of transport-layer
    // detail into the MCP-facing error text. describeProxyFailure already produces the
    // clean, denial-specific message for the entitlement case (and a generic-but-status-
    // code-free message otherwise) — callPlatformPrimitive already used it; this call site
    // never did. Same fix, same file, finally applied uniformly.
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) {
    throw new Error(`[registry_bridge] capability error: ${data.error ?? 'unknown'}`)
  }
  return data.content
}
