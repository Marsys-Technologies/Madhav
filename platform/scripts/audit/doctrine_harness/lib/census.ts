/**
 * census.ts — D-2 Lane V-0, BIND_D-2.md §F1.7 ledger rows 2 + 5.
 *
 * Full sweep of the deployed connector's live tools/list (135 tools at BIND_D-2.md §B.5,
 * superseding the ~126 planning figure) reporting PASS/DEGRADED/EMPTY/FAIL per tool with byte
 * sizes recorded — there was no per-tool byte-size baseline before this (§B.1's oversize
 * observations on judgment_query/ref_dasha_systems_get were anecdote, not a recorded baseline).
 *
 * HARD DESIGN REQUIREMENT (BRIEF_D2.md §F1 Lane V-0): the deployed connector rate-limits under
 * sustained assertion load (D-1.5b Gate-B 429 cascade at 32 sequential calls; 17-call batches
 * ran clean). The mcp_client.ts 429-retry (D15b-F1) is necessary but NOT sufficient for a
 * 135-tool sweep — this module adds the missing PROACTIVE half:
 *   - batches sized <= DEFAULT_BATCH_SIZE (17, the empirically-clean threshold);
 *   - an inter-batch throttle (on top of mcp_client's own per-call MIN_REQUEST_GAP_MS pacing);
 *   - a checkpoint written to disk after every batch, so an interrupted sweep (crash, API
 *     glitch, ceiling hit) RESUMES from the last completed batch on next invocation rather than
 *     restarting the whole 135-tool sweep and re-hammering the connector;
 *   - TRANSPORT-vs-TOOL error separation (CONDUCTOR_PROTOCOL §6.4): a 429/5xx/network failure
 *     that survives mcp_client's own retries is recorded as TRANSPORT_ERROR, never folded into
 *     FAIL — "a census that trips the limiter and reports false reds is a harness defect, not an
 *     estate defect" (BRIEF_D2.md §F1 Lane V-0, verbatim).
 *
 * Status classification per tool (the four statuses the ledger names, plus the two
 * protocol-required side-channels SKIPPED/TRANSPORT_ERROR which are reported but never counted
 * as FAIL):
 *   PASS      — non-error response, non-empty payload, within the size ceiling.
 *   DEGRADED  — non-error response but payload exceeds OVERSIZE_BYTES (64KB, the Gate-Ś ceiling
 *               BIND_D-2.md §B.1 already found judgment_query(v3)/ref_dasha_systems_get past).
 *   EMPTY     — non-error response with zero servable rows/signals; HONEST if the payload itself
 *               names an `empty_reason` (the ref_yogas_get domain-vocabulary trap from §B.5),
 *               else recorded as an unexplained empty (still not FAIL — B.10 forbids treating an
 *               honest empty as a defect, but an unexplained one is flagged for V-3's
 *               errors-that-teach class).
 *   FAIL      — the tool call reached the server and returned an explicit tool-level error
 *               (isToolError, or a non-transport 4xx).
 *   SKIPPED   — this harness could not safely synthesize a required-argument set for the tool
 *               (never silently treated as a pass — CLAUDE.md B.10 spirit).
 *   TRANSPORT_ERROR — the connector-level failure class (429 exhausted, 5xx exhausted, network)
 *               — kept OUT of the FAIL tally per the hard design requirement above.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'
import type { McpClient, McpToolDescriptor } from './mcp_client'
import { RateLimitedError } from './mcp_client'

export const DEFAULT_BATCH_SIZE = 17
export const DEFAULT_INTER_BATCH_MS = 3_000
export const OVERSIZE_BYTES = 64 * 1024 // Gate-Ś ceiling, BIND_D-2.md §B.1

export type CensusStatus = 'PASS' | 'DEGRADED' | 'EMPTY' | 'FAIL' | 'SKIPPED' | 'TRANSPORT_ERROR'

export type CensusToolResult = {
  tool: string
  status: CensusStatus
  bytes: number | null
  empty_reason?: string | null
  detail: string
}

export type CensusCheckpoint = {
  target: string
  chart_id: string
  started_at: string
  updated_at: string
  total_tools: number
  results: Record<string, CensusToolResult>
}

/**
 * Best-effort safe-argument synthesizer for a census probe call. Mirrors the pattern already
 * established live in platform/scripts/audit/alias_conformance_check.ts's synthesizeArgs (out
 * of this lane's may_touch — reimplemented narrowly here, scoped to a single chart_id probe
 * rather than a pair-conformance probe). Returns null when a required field cannot be safely
 * fabricated — the caller records SKIPPED, never guesses.
 */
export function synthesizeCensusArgs(
  tool: McpToolDescriptor,
  chartId: string
): Record<string, unknown> | null {
  const schema = (tool.inputSchema ?? {}) as { properties?: Record<string, { type?: string }>; required?: string[] }
  const required = schema.required ?? []
  const properties = schema.properties ?? {}
  const args: Record<string, unknown> = {}
  for (const field of required) {
    const propType = properties[field]?.type
    if (field === 'chart_id') {
      args[field] = chartId
    } else if (/date/i.test(field) && field !== 'date_range') {
      args[field] = '2026-07-16'
    } else if (field === 'date_range') {
      args[field] = { start: '2020-01-01', end: '2032-12-31' }
    } else if (/planet|graha/i.test(field)) {
      args[field] = 'Saturn'
    } else if (/domain/i.test(field)) {
      args[field] = 'wealth'
    } else if (/latitude/i.test(field)) {
      args[field] = 20.2961
    } else if (/longitude/i.test(field)) {
      args[field] = 85.8245
    } else if (/datetime_iso|^dob$/i.test(field)) {
      args[field] = '1984-02-05T10:43:00+05:30'
    } else if (propType === 'string') {
      return null // unknown required string field — cannot safely fabricate
    } else if (propType === 'number' || propType === 'integer') {
      return null
    } else if (propType === 'boolean') {
      args[field] = true
    } else {
      return null
    }
  }
  return args
}

/** Extracts a row/signal count from a census probe's unwrapped content, best-effort, across the
 *  several shapes this harness's assertions.ts already had to learn (content.rows, content.signals,
 *  content.content.rows, top-level rows/results/anchors, or a `total`/`coverage.served` field). */
function extractServedCount(content: unknown): { count: number | null; emptyReason: string | null } {
  if (content === null || content === undefined) return { count: null, emptyReason: null }
  const top = content as Record<string, unknown>
  const emptyReason =
    (top.empty_reason as string | undefined) ??
    ((top.content as Record<string, unknown> | undefined)?.empty_reason as string | undefined) ??
    null
  const candidates: unknown[] = [
    (top.content as { rows?: unknown[] } | undefined)?.rows,
    (top.content as { signals?: unknown[] } | undefined)?.signals,
    (top.content as { content?: { rows?: unknown[] } } | undefined)?.content?.rows,
    (top.content as { anchors?: unknown[] } | undefined)?.anchors,
    (top.content as { facts?: unknown[] } | undefined)?.facts,
    (top.content as { results?: unknown[] } | undefined)?.results,
    top.rows,
    top.results,
    top.tools, // tools/list-shaped
  ]
  for (const c of candidates) {
    if (Array.isArray(c)) return { count: c.length, emptyReason }
  }
  // No array field recognized — fall back to "non-empty object with keys" as a coarse signal
  // rather than declaring EMPTY on a shape this harness simply doesn't parse yet (never
  // fabricate absence from an unparsed shape — the truncation-honesty rule applied to shape
  // recognition, not just pagination).
  const keys = Object.keys(top.content && typeof top.content === 'object' ? (top.content as object) : top)
  return { count: keys.length > 0 ? keys.length : null, emptyReason }
}

function loadCheckpoint(path: string): CensusCheckpoint | null {
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf8')) as CensusCheckpoint
  } catch {
    return null // corrupt checkpoint — treated as absent, sweep restarts (never crash-loop on a bad file)
  }
}

function saveCheckpoint(path: string, cp: CensusCheckpoint): void {
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, JSON.stringify(cp, null, 2), 'utf8')
}

export type CensusOptions = {
  batchSize?: number
  interBatchMs?: number
  checkpointPath: string
  chartId: string
  /** When true, an existing checkpoint for a DIFFERENT target is discarded rather than reused
   *  (prevents silently mixing two different connectors' results under one checkpoint file). */
  target: string
}

/**
 * Runs (or resumes) a full census sweep. Returns once every tool in `tools` has a recorded
 * result (from this run or a prior checkpoint) — never re-probes an already-checkpointed tool,
 * which is what makes an interrupted sweep resume instead of restart.
 */
export async function runCensusSweep(
  client: McpClient,
  tools: McpToolDescriptor[],
  opts: CensusOptions
): Promise<{ results: CensusToolResult[]; checkpoint: CensusCheckpoint; resumed: boolean }> {
  const batchSize = opts.batchSize ?? DEFAULT_BATCH_SIZE
  const interBatchMs = opts.interBatchMs ?? DEFAULT_INTER_BATCH_MS

  let cp = loadCheckpoint(opts.checkpointPath)
  let resumed = false
  if (cp && cp.target === opts.target && cp.chart_id === opts.chartId) {
    resumed = Object.keys(cp.results).length > 0
  } else {
    cp = {
      target: opts.target,
      chart_id: opts.chartId,
      started_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      total_tools: tools.length,
      results: {},
    }
  }

  const remaining = tools.filter((t) => !(t.name in cp!.results))

  for (let i = 0; i < remaining.length; i += batchSize) {
    const batch = remaining.slice(i, i + batchSize)
    for (const tool of batch) {
      const result = await probeOneTool(client, tool, opts.chartId)
      cp.results[tool.name] = result
    }
    cp.updated_at = new Date().toISOString()
    saveCheckpoint(opts.checkpointPath, cp)
    // Inter-batch throttle — separate from mcp_client's own per-call MIN_REQUEST_GAP_MS; this
    // is the "proactive pacing between batches" half of the hard design requirement, not a
    // substitute for it. Skip the sleep after the final batch.
    if (i + batchSize < remaining.length) {
      await new Promise((r) => setTimeout(r, interBatchMs))
    }
  }

  return { results: Object.values(cp.results), checkpoint: cp, resumed }
}

async function probeOneTool(client: McpClient, tool: McpToolDescriptor, chartId: string): Promise<CensusToolResult> {
  const args = synthesizeCensusArgs(tool, chartId)
  if (args === null) {
    return { tool: tool.name, status: 'SKIPPED', bytes: null, detail: 'required argument set could not be safely synthesized' }
  }
  try {
    const { content, isToolError, raw } = await client.callTool(tool.name, args)
    const bytes = Buffer.byteLength(JSON.stringify(content ?? {}), 'utf8')
    if (isToolError || raw.status >= 400) {
      return { tool: tool.name, status: 'FAIL', bytes, detail: `tool-level error (status=${raw.status})` }
    }
    const { count, emptyReason } = extractServedCount(content)
    if (count === 0) {
      return {
        tool: tool.name,
        status: 'EMPTY',
        bytes,
        empty_reason: emptyReason,
        detail: emptyReason ? `honest empty: ${emptyReason}` : 'zero rows served, no empty_reason field found',
      }
    }
    if (bytes > OVERSIZE_BYTES) {
      return { tool: tool.name, status: 'DEGRADED', bytes, detail: `payload ${bytes}B exceeds the ${OVERSIZE_BYTES}B Gate-Ś ceiling` }
    }
    return { tool: tool.name, status: 'PASS', bytes, detail: `${count ?? '?'} row(s)/key(s), ${bytes}B` }
  } catch (err) {
    // TRANSPORT-vs-TOOL separation (protocol §6.4): a RateLimitedError or a "TRANSPORT-ERROR"/
    // "DEGRADED-RESPONSE" thrown by mcp_client.ts AFTER it already exhausted its own retries is
    // a connector-level failure, not a tool defect — recorded distinctly, never as FAIL.
    const msg = err instanceof Error ? err.message : String(err)
    const isTransport =
      err instanceof RateLimitedError ||
      /TRANSPORT-ERROR|DEGRADED-RESPONSE|exhausted retries|RATE-LIMITED/i.test(msg)
    return {
      tool: tool.name,
      status: isTransport ? 'TRANSPORT_ERROR' : 'FAIL',
      bytes: null,
      detail: msg,
    }
  }
}

export function summarizeCensus(results: CensusToolResult[]): Record<CensusStatus, number> {
  const summary: Record<CensusStatus, number> = { PASS: 0, DEGRADED: 0, EMPTY: 0, FAIL: 0, SKIPPED: 0, TRANSPORT_ERROR: 0 }
  for (const r of results) summary[r.status] += 1
  return summary
}
