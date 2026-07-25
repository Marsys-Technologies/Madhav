/**
 * _mcp_client.ts — shared minimal MCP Streamable-HTTP JSON-RPC client for the
 * α (SATYA) Lane-K1 serving-side CI gates in this directory.
 *
 * DELIBERATELY SELF-CONTAINED. `platform/scripts/audit/tap/lib/mcp_client.ts` and
 * `platform/scripts/audit/doctrine_harness/lib/mcp_client.ts` already implement very
 * similar clients, but `platform/scripts/audit/**` is owned by STREAM β (GAṆITA) per
 * `ELEVATION_CAMPAIGN_CHARTER_v2_1.md §4` — importing from there would create a
 * cross-manifest runtime dependency this lane does not own and cannot guarantee is
 * stable for the duration of the overnight campaign. This module duplicates the
 * essential, minimal subset of that pattern (initialize → tools/call / tools/list,
 * Bearer or ?api_key= auth, SSE-or-plain-JSON body parsing) so every gate script in
 * THIS directory (α's own territory) has zero outside-manifest runtime imports.
 *
 * Key difference from the two existing clients (deliberate, per this lane's task
 * spec): every call takes an explicit per-call timeout (`AbortSignal.timeout(ms)`,
 * default 30_000ms per Lane-K1's task-1 instruction: "any HTTP 500 or hang (set a
 * reasonable timeout, e.g. 30s per tool) is a failure"). A timeout is reported as its
 * own distinct outcome (`timed_out: true`), never silently retried into a false pass
 * or a false generic failure — callers decide how to score it.
 */

export type McpCallOutcome = {
  ok: boolean
  status: number
  body: string
  json?: unknown
  timed_out: boolean
  elapsed_ms: number
  error?: string
}

export type McpToolDescriptor = {
  name: string
  description?: string
  inputSchema?: unknown
}

export const DEFAULT_TOOL_TIMEOUT_MS = 30_000

/**
 * Resolves the live MCP server target from environment. Two supported shapes,
 * matching the two live faces already used elsewhere in this repo (mcp_client.ts's
 * own header comment):
 *   - MCP_SERVER_URL + MCP_BEARER          → Authorization: Bearer <token>
 *   - MCP_SERVER_URL already carrying `?api_key=...` (the marsys-jis-direct seat),
 *     MCP_BEARER unset                     → no Authorization header sent.
 */
export function resolveMcpTarget(): { baseUrl: string; bearer?: string } | null {
  const baseUrl = process.env['MCP_SERVER_URL']
  if (!baseUrl) return null
  const bearer = process.env['MCP_BEARER'] || process.env['MCP_SMOKE_BEARER_TOKEN'] || undefined
  return { baseUrl, bearer }
}

export class ElevMcpClient {
  private sessionId: string | undefined

  constructor(
    private readonly baseUrl: string,
    private readonly bearer?: string,
    private readonly timeoutMs: number = DEFAULT_TOOL_TIMEOUT_MS,
  ) {}

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      'content-type': 'application/json',
      accept: 'application/json, text/event-stream',
    }
    if (this.bearer) h['authorization'] = `Bearer ${this.bearer}`
    if (this.sessionId) h['mcp-session-id'] = this.sessionId
    return h
  }

  private async post(body: unknown, timeoutMs: number): Promise<McpCallOutcome> {
    const started = Date.now()
    try {
      const res = await fetch(this.baseUrl, {
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(timeoutMs),
      })
      const text = await res.text()
      let json: unknown
      try {
        // Streamable HTTP responses are sometimes SSE-framed
        // ("event: message\ndata: {...}"); handle both shapes.
        const dataLine = text.split('\n').find((l) => l.startsWith('data:'))
        const raw = dataLine ? dataLine.slice('data:'.length).trim() : text
        json = raw ? JSON.parse(raw) : undefined
      } catch {
        json = undefined
      }
      return { ok: res.ok, status: res.status, body: text, json, timed_out: false, elapsed_ms: Date.now() - started }
    } catch (err) {
      const isAbort = err instanceof Error && (err.name === 'AbortError' || err.name === 'TimeoutError')
      return {
        ok: false,
        status: 0,
        body: '',
        timed_out: isAbort,
        elapsed_ms: Date.now() - started,
        error: err instanceof Error ? err.message : String(err),
      }
    }
  }

  /** Best-effort handshake — non-fatal; the deployed connector is confirmed stateless. */
  async init(): Promise<void> {
    const res = await this.post(
      {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'elev-gates-k1', version: '1.0.0' } },
      },
      this.timeoutMs,
    )
    // Streamable HTTP session id, when issued, arrives as a response header — this
    // minimal client does not read headers off `post()`'s return today (body/json
    // only). Stateless deployed connector does not require session continuity
    // (confirmed live by the existing doctrine_harness client); omitted here rather
    // than half-implemented.
    void res
  }

  async listTools(timeoutMs = this.timeoutMs): Promise<{ tools: McpToolDescriptor[] } | { error: string }> {
    const raw = await this.post({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }, timeoutMs)
    if (raw.timed_out) return { error: `tools/list timed out after ${timeoutMs}ms` }
    if (!raw.ok) return { error: `tools/list HTTP ${raw.status}` }
    const tools = (raw.json as { result?: { tools?: McpToolDescriptor[] } } | undefined)?.result?.tools
    if (!tools) return { error: 'tools/list returned no tools array' }
    return { tools }
  }

  /** Calls one tool with an explicit per-call timeout. Never throws — every failure mode
   *  (hang, transport error, tool-level error) is reported as data. */
  async callTool(name: string, args: Record<string, unknown>, timeoutMs = this.timeoutMs): Promise<McpCallOutcome> {
    return this.post({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name, arguments: args } }, timeoutMs)
  }
}

/** Unwraps the MCP tool-result envelope down to the tool's own JSON payload, mirroring
 *  the resolution order confirmed live against the deployed connector (prefer
 *  structuredContent.object; fall back to parsing content[0].text as JSON). */
export function unwrapToolPayload(outcome: McpCallOutcome): { payload: unknown; isToolError: boolean } {
  const envelope = (outcome.json as { result?: unknown; error?: unknown } | undefined) ?? {}
  const result = (envelope as { result?: { isError?: boolean; content?: Array<{ text?: string }>; structuredContent?: { object?: unknown } } }).result
  const isToolError = Boolean(result?.isError) || Boolean((envelope as { error?: unknown }).error)
  let payload: unknown = envelope
  if (result?.structuredContent && typeof result.structuredContent === 'object' && 'object' in result.structuredContent) {
    payload = (result.structuredContent as { object: unknown }).object
  } else if (Array.isArray(result?.content) && result.content[0]?.text) {
    try {
      payload = JSON.parse(result.content[0].text as string)
    } catch {
      payload = result.content[0].text
    }
  }
  return { payload, isToolError }
}

export const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
// Never write/use this — documented dead phantom (CLAUDE.md §B). Exported only so a
// gate script can grep-assert it never appears in a call plan or a live payload.
export const DEAD_PHANTOM_CHART_ID = '362f9f17-'

export function envOrDefault(name: string, fallback: string): string {
  const v = process.env[name]
  return v && v.length > 0 ? v : fallback
}
