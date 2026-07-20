/**
 * tools/scan_fetch_signals.ts — D-2 Lane V-3, the servable two-pass channel (ledger row 20).
 *
 * Fronts the large bodha_msr_signals surface (≈9.9K rows/ayanamsha — the 234KB class) with the
 * scan_fetch two-pass channel (lib/scan_fetch.ts):
 *   mode="scan"  → ultra-dense subject-bearing index lines (~60B/row) over the whole matched set.
 *   mode="fetch" → full signal rows for a set of ids picked from the scan.
 * Deterministic view over query_signals output — never re-ranks or drops silently (B.10); the scan
 * reports the true total and flags truncation with an authoritative count (§F1.7 truncation honesty).
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { scan, fetchByIds, type ScanFetchConfig } from '../lib/scan_fetch.js'
import { budgetMcpContent } from '../lib/response_budget.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callSignals(args: Record<string, unknown>, principal: Principal): Promise<Record<string, unknown>[]> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri: 'marsys://tool/L2/query_signals', args }),
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) throw new Error(`scan_fetch: query_signals → ${res.status}`)
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`scan_fetch: ${data.error ?? 'unknown'}`)
  const content = (data.content as Record<string, unknown>)?.['content'] ?? data.content
  const inner = content as Record<string, unknown>
  const rows = inner?.['signals']
  return Array.isArray(rows) ? rows as Record<string, unknown>[] : []
}

/** Stable id for a signal row (first available id-like field, else a content hash-ish fallback). */
function signalId(r: Record<string, unknown>): string {
  for (const k of ['signal_id', 'msr_signal_id', 'signal_uid', 'id']) {
    if (r[k] != null) return String(r[k])
  }
  // deterministic fallback: class + first constituent fact + tier
  const facts = Array.isArray(r['constituent_facts_array']) ? r['constituent_facts_array'] as string[] : []
  return `${r['signal_type_class'] ?? 'sig'}:${facts[0] ?? 'na'}:${r['signature_tier'] ?? '0'}`
}

const SIGNAL_SCAN: ScanFetchConfig<Record<string, unknown>> = {
  id: signalId,
  columns: [
    { key: 'class', get: (r) => r['signal_type_class'] },
    { key: 'tier', get: (r) => r['signature_tier'] },
    { key: 'salience', get: (r) => r['salience'] ?? r['top_k_salience_rank'] },
    { key: 'subject', get: (r) => (Array.isArray(r['constituent_facts_array']) ? (r['constituent_facts_array'] as string[])[0] : r['subject']) },
    { key: 'domain', get: (r) => (Array.isArray(r['domains_affected_array']) ? (r['domains_affected_array'] as string[])[0] : r['domain']) },
  ],
}

export function registerScanFetchTool(server: McpServer, principal: Principal): void {
  server.tool(
    'scan_fetch_signals',
    'Two-pass channel over the large bodha signals surface. mode="scan" returns one ultra-dense ' +
    'index line (~60B) per matched signal so you can survey the WHOLE set cheaply (with the true ' +
    'total + honest truncation flag); mode="fetch" returns FULL rows for the ids you picked from the ' +
    'scan. Use scan to decide, fetch to read — instead of paging full rows or accepting a ' +
    'salience-truncated top-K. Facets (domain/signal_type_class/min_salience) pass through to ' +
    'query_signals before the scan.',
    {
      chart_id: z.string().uuid().describe('Chart UUID'),
      mode: z.enum(['scan', 'fetch']).describe('scan = dense index lines; fetch = full rows by id'),
      ids: z.array(z.string()).optional().describe('fetch mode: the ids (from a prior scan) to resolve to full rows'),
      ayanamsha_id: z.string().optional(),
      domain: z.string().optional(),
      signal_type_class: z.string().optional(),
      min_salience: z.number().min(0).max(1).optional(),
      max_scan_bytes: z.number().int().min(1000).max(60_000).optional().describe('scan mode: byte cap for the index (default 20000)'),
    },
    async (params) => {
      const p = params as Record<string, unknown>
      const chart_id = p['chart_id'] as string
      if (!chart_id) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: 'chart_id is required' }) }], isError: true }
      }
      try {
        const args: Record<string, unknown> = {
          chart_id,
          ayanamsha_id: (p['ayanamsha_id'] as string) ?? 'lahiri_chitrapaksha',
          limit: 25000, offset: 0,
        }
        for (const k of ['domain', 'signal_type_class', 'min_salience']) if (p[k] != null) args[k] = p[k]
        const rows = await callSignals(args, principal)

        if (p['mode'] === 'fetch') {
          const ids = Array.isArray(p['ids']) ? p['ids'] as string[] : []
          if (ids.length === 0) {
            return { content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: 'fetch mode requires ids[] (get them from a mode="scan" call first)' }) }], isError: true }
          }
          // fetch mode's full rows are only bounded by the size of ids[] the caller passed
          // (scan mode already self-limits via max_scan_bytes) — budgetMcpContent is the
          // backstop for a caller that fetches a large id set.
          const result = budgetMcpContent(fetchByIds(rows, ids, SIGNAL_SCAN), 'scan_fetch_signals')
          return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
        }

        const maxBytes = (p['max_scan_bytes'] as number) ?? 20_000
        const result = scan(rows, SIGNAL_SCAN, maxBytes)
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        return { content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: String(err), chart_id }) }], isError: true }
      }
    }
  )
}
