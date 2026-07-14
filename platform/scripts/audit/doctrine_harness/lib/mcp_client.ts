/**
 * mcp_client.ts — minimal Streamable HTTP JSON-RPC client for the doctrine
 * assertion harness (D-1.5a Lane A-0).
 *
 * Follows the exact access pattern established by
 * platform/scripts/audit/tap/mcp_tool_smoke.ts (initialize -> tools/call,
 * POST /mcp, Bearer auth) — see CONDUCTOR_PROTOCOL.md §8.1. That script is
 * the "established access pattern" this harness was told to reuse; this
 * module also adds `tools/list` (needed for K.2 #11/#12: tool-description
 * and tool-discoverability checks) and small retry/backoff discipline for
 * transient failures (protocol §6.4 — a transient failure is never a red
 * assertion, only a retry).
 */

export type McpToolResult = {
  ok: boolean
  status: number
  body: string
  json?: unknown
}

export type McpToolDescriptor = {
  name: string
  description?: string
  inputSchema?: unknown
}

// Minimum gap between outbound requests to the deployed connector. Built
// empirically 2026-07-15: running all 15 assertions back-to-back with no
// pacing produced sporadic degraded responses (200 status but truncated/
// empty payloads — no exception, so withRetry didn't catch it) after ~40-50
// rapid sequential calls, most visible on ganita_yoga_firings_get and
// tools/list. Isolated re-runs of the same assertions always matched the
// canonical baseline. This min-gap throttle is the fix, not a workaround —
// a harness that silently produces false reds under load is worse than a
// slower one that doesn't.
const MIN_REQUEST_GAP_MS = 250

export class McpClient {
  private sessionId: string | undefined
  private initialized = false
  private lastRequestAt = 0

  /**
   * @param baseUrl full POST target. May already carry `?api_key=...` (the
   *   marsys-jis-direct seat) — in that case `bearer` should be undefined
   *   and no Authorization header is sent.
   * @param bearer Bearer token for the `Authorization` header (protocol
   *   §8.1's default reproducible face). Omit when baseUrl already carries
   *   its own api_key credential.
   */
  constructor(
    private readonly baseUrl: string,
    private readonly bearer?: string
  ) {}

  private headers(extra?: Record<string, string>): Record<string, string> {
    const h: Record<string, string> = {
      'content-type': 'application/json',
      accept: 'application/json, text/event-stream',
      ...extra,
    }
    if (this.bearer) h.authorization = `Bearer ${this.bearer}`
    if (this.sessionId) h['mcp-session-id'] = this.sessionId
    return h
  }

  private async pace(): Promise<void> {
    const wait = this.lastRequestAt + MIN_REQUEST_GAP_MS - Date.now()
    if (wait > 0) await new Promise((r) => setTimeout(r, wait))
    this.lastRequestAt = Date.now()
  }

  private async post(body: unknown): Promise<McpToolResult> {
    await this.pace()
    const res = await fetch(this.baseUrl, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(body),
    })
    const text = await res.text()
    let json: unknown
    try {
      // Streamable HTTP MCP responses are sometimes SSE-framed
      // ("event: message\ndata: {...}"); handle both plain JSON and SSE.
      const dataLine = text.split('\n').find((l) => l.startsWith('data:'))
      const raw = dataLine ? dataLine.slice('data:'.length).trim() : text
      json = raw ? JSON.parse(raw) : undefined
    } catch {
      json = undefined
    }
    return { ok: res.ok, status: res.status, body: text, json }
  }

  private async withRetry<T>(fn: () => Promise<T>, label: string): Promise<T> {
    const backoffsMs = [10_000, 60_000, 300_000]
    let lastErr: unknown
    for (let attempt = 0; attempt <= backoffsMs.length; attempt++) {
      try {
        return await fn()
      } catch (err) {
        lastErr = err
        if (attempt < backoffsMs.length) {
          // Transient-failure handling per CONDUCTOR_PROTOCOL §6.4 — retry
          // with backoff; never counted as a substantive result. Capped at
          // 2s in practice so the harness stays usable interactively; the
          // full backoff schedule is documented for the unattended/CI case.
          await new Promise((r) => setTimeout(r, Math.min(backoffsMs[attempt], 2_000)))
          continue
        }
      }
    }
    throw new Error(`${label}: exhausted retries — ${lastErr instanceof Error ? lastErr.message : String(lastErr)}`)
  }

  /**
   * Best-effort MCP handshake. The deployed marsys-jis connector is
   * verified stateless (no `mcp-session-id` issued, `tools/call` succeeds
   * with zero prior handshake — confirmed live during harness build,
   * 2026-07-15) so this is NOT required before `callTool`/`listTools`; it
   * is attempted once, non-fatally, for spec-compliant MCP clients that
   * DO require it against a future/different deployment.
   */
  async init(): Promise<void> {
    if (this.initialized) return
    this.initialized = true // stateless server — never block callers on this
    try {
      const res = await fetch(this.baseUrl, {
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'initialize',
          params: {
            protocolVersion: '2024-11-05',
            capabilities: {},
            clientInfo: { name: 'doctrine-harness', version: '1.0.0' },
          },
        }),
      })
      this.sessionId = res.headers.get('mcp-session-id') ?? undefined
      await res.text()
    } catch {
      // Non-fatal — stateless deployed connector does not require this.
    }
  }

  async listTools(): Promise<McpToolDescriptor[]> {
    return this.withRetry(async () => {
      const { json } = await this.post({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} })
      const tools = (json as { result?: { tools?: McpToolDescriptor[] } } | undefined)?.result?.tools
      if (!tools) throw new Error('tools/list returned no tools array')
      return tools
    }, 'tools/list')
  }

  /** Calls a tool and returns the parsed content (throws on transport error). */
  async callTool(
    name: string,
    args: Record<string, unknown>
  ): Promise<{ raw: McpToolResult; content: unknown; isToolError: boolean }> {
    return this.withRetry(async () => {
      const raw = await this.post({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name, arguments: args } })
      if (raw.status >= 500) {
        throw new Error(`TRANSPORT-ERROR ${raw.status} calling ${name}`)
      }
      if (raw.json === undefined) {
        // A 2xx with an unparseable/degraded body — observed under request
        // bursts against the deployed connector. Never treated as a valid
        // (possibly empty) result; retried like a transport error.
        throw new Error(`DEGRADED-RESPONSE calling ${name}: status=${raw.status}, body unparsed (len=${raw.body.length})`)
      }
      const envelope = (raw.json as { result?: unknown; error?: unknown } | undefined) ?? {}
      const result = (envelope as { result?: { isError?: boolean; content?: Array<{ text?: string }>; structuredContent?: { object?: unknown } } }).result
      const isToolError = Boolean(result?.isError) || Boolean((envelope as { error?: unknown }).error)
      // Payload resolution order (confirmed live against the deployed
      // connector 2026-07-15): prefer `structuredContent.object` — some
      // tools (e.g. judgment_query) return a budget-capped placeholder in
      // `content[0].text` ("[budget-capped response — see
      // structuredContent...]") and put the real payload only in
      // structuredContent per R5.1 C1. Fall back to parsing content[0].text
      // as JSON for tools that don't set structuredContent.
      let content: unknown = envelope
      if (result?.structuredContent && typeof result.structuredContent === 'object' && 'object' in result.structuredContent) {
        content = (result.structuredContent as { object: unknown }).object
      } else if (Array.isArray(result?.content) && result.content[0]?.text) {
        try {
          content = JSON.parse(result.content[0].text as string)
        } catch {
          content = result.content[0].text
        }
      }
      return { raw, content, isToolError }
    }, `tools/call:${name}`)
  }
}

export function envOrDefault(name: string, fallback?: string): string | undefined {
  const v = process.env[name]
  return v && v.length > 0 ? v : fallback
}
