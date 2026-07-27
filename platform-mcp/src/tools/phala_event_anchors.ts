/**
 * phala_event_anchors.ts — BRAHMA-PH-4-1: phala.anchors
 *
 * L4 Phala: calibrated ensemble of classical predictors → falsifiable
 * probabilistic event anchors.
 *
 * Contract (BRAHMA PH-4-1):
 *   Table:  phala_anchors (chart_id UUID, anchor_id TEXT, window_start DATE,
 *           window_end DATE, theme TEXT, confidence FLOAT CHECK(0<=confidence<=1),
 *           falsifier TEXT NOT NULL, contributing_dashas JSONB,
 *           contributing_signals JSONB, source_citation TEXT NOT NULL)
 *   Tool:   event_anchors(chart_id, date_range, min_confidence?)
 *           → {anchors:[{window,theme,confidence,falsifier,provenance}], provenance_envelope}
 *   Algorithm: score = dasha_quality × signal_strength × convergence_score
 *   Gates:
 *     - >= 3 anchors for native 2026-2030 period
 *     - all falsifiers non-empty (Learning Layer rule #4)
 *     - all source_citations non-empty (B.3 mandate)
 *     - confidence in [0.0, 1.0]
 *
 * Reference birth: 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *
 * L1 ground-truth:
 *   chart_facts DB table (dasha-period rows DSH.V.023–028, Vimshottari dasha 2024-2030) —
 *   MC-003 (ŚODHANA T1): FORENSIC v8.0 markdown was deleted (PR #187 Legacy Teardown);
 *   chart_facts is the live canonical source, not the retired document.
 *   MSR v5.0 SIG.09/SIG.14/SIG.08/SIG.12/SIG.04/SIG.11 (signal ensemble)
 *
 * Wiring: registerPhalaEventAnchorsTool(server) → server.ts during L4 Phala registration.
 *
 * BRAHMA-PH-4-1
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { finalizeMcpBudget, type TrimmableSection } from '../lib/response_budget.js'

// ── Environment ────────────────────────────────────────────────────────────────

const PYTHON_SIDECAR_URL = (
  process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
).replace(/\/$/, '')

const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''
const TOOL_TIMEOUT_MS = 30_000

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AnchorWindow {
  start: string // ISO date
  end: string   // ISO date
}

export interface PredictionAnchor {
  anchor_id: string
  window: AnchorWindow
  theme: string
  confidence: number   // in [0.0, 1.0]
  falsifier: string    // non-null: "If [event] does not occur by [date], this prediction is false"
  contributing_dashas: string[]
  contributing_signals: string[]
  source_citation: string // non-null (B.3 mandate)
  prediction_state: 'open' | 'confirmed' | 'falsified' | 'expired'
  outcome_note: string | null
}

export interface ProvenanceEnvelope {
  source: string
  asset: string
  algorithm: string
  min_confidence_applied: number
  chart_id: string
  queried_at: string // ISO datetime
  l1_ground_truth: string
  b3_citation_compliant: boolean
  all_falsifiers_present: boolean
}

export interface EventAnchorsResult {
  ok: boolean
  chart_id: string
  query_window: AnchorWindow
  anchors: PredictionAnchor[]
  anchor_count: number
  provenance_envelope: ProvenanceEnvelope
}

// ── T-6 / R-1 fix: dedup + pagination at the TS serving boundary ───────────────
//
// T-6 (register): "Duplicate-anchor spam, no serve-time cap on drill-down aliases —
// phala_anchors_get 421KB, EVERY row identical window 2026-07-08→2026-10-06 + confidence
// 0.322". The true source-of-truth fix belongs in the Python ph_nimitta writer (out of
// scope for this TS-estate lane — a separate parallel data-rebuild effort owns that), but
// this is the EARLIEST point this lane can dedupe: right where the sidecar response is
// received, before any caller ever sees a duplicate row. See anchorDedupKey below for the
// exact dedup fingerprint (widened past the register's own theme/window/confidence
// description per a Ring-2 flagged false-merge risk).
// R6 3b-budgets (Ring-2 flagged risk): theme+window+confidence ALONE can false-merge two
// genuinely distinct anchors that happen to share those 3 fields by coincidence (e.g. two
// real predictions in the same theme/window with the same computed confidence but different
// falsifiers/contributing evidence). Widened the key to also include falsifier text +
// contributing_dashas + contributing_signals (sorted, so array ORDER never causes a false
// non-match) — a genuine content fingerprint, not just the 3 fields the register's own
// "every row identical" description happened to call out. The register's actual observed
// bug (every field byte-identical across duplicate rows) still dedupes cleanly under this
// wider key, since true duplicates share ALL of these fields too; it only stops merging rows
// that differ in the fields that matter (what is actually being predicted and why).
function anchorDedupKey(a: PredictionAnchor): string {
  const dashas = [...(a.contributing_dashas ?? [])].sort().join('|')
  const signals = [...(a.contributing_signals ?? [])].sort().join('|')
  return `${a.theme}::${a.window?.start}::${a.window?.end}::${a.confidence}::${a.falsifier}::${dashas}::${signals}`
}

function dedupeAnchors(anchors: PredictionAnchor[]): { deduped: PredictionAnchor[]; duplicates_removed: number } {
  const seen = new Set<string>()
  const deduped: PredictionAnchor[] = []
  for (const a of anchors) {
    const key = anchorDedupKey(a)
    if (seen.has(key)) continue
    seen.add(key)
    deduped.push(a)
  }
  return { deduped, duplicates_removed: anchors.length - deduped.length }
}

// R-1: event_anchors had NO pagination params at all (register: "620KB with no pagination
// at all"). Added here as the serve-time bound; sections trimmed via the same shared
// response_budget mechanism every other fixed tool in this lane uses.
function anchorsSection(): TrimmableSection<Record<string, unknown>> {
  return {
    path: 'anchors', label: 'anchors', minKeep: 10,
    getArray: (c) => { const arr = c['anchors']; return Array.isArray(arr) ? arr : undefined },
    setArray: (c, kept) => { c['anchors'] = kept },
    recover: { instrument: 'event_anchors', hint: 'call again with a narrower date_range, or paginate via offset/limit' },
  }
}

// ── Sidecar call ───────────────────────────────────────────────────────────────

async function callSidecar<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  const url = `${PYTHON_SIDECAR_URL}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (SIDECAR_API_KEY) {
    headers['X-API-Key'] = SIDECAR_API_KEY
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TOOL_TIMEOUT_MS)

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      const text = await response.text().catch(() => '')
      throw new Error(
        `Sidecar HTTP ${response.status} from ${path}: ${text.slice(0, 300)}`
      )
    }

    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

// ── Core query functions ───────────────────────────────────────────────────────

/**
 * Fetch calibrated event anchors for a chart and date window.
 *
 * Each anchor carries:
 *   - window: {start, end} (ISO dates for the 6-month prediction window)
 *   - theme: the predicted life-domain category
 *   - confidence: float [0.0, 1.0] — dasha_quality × signal_strength × convergence_score
 *   - falsifier: explicit non-null falsification condition
 *   - contributing_dashas: array of dasha strings (e.g. "DSH.V.023: Mercury MD Saturn AD …")
 *   - contributing_signals: array of signal IDs/names (e.g. "SIG.09 Mercury 8-system convergence")
 *   - source_citation: L1 citation string (non-null, B.3 compliant)
 *
 * Returns the full EventAnchorsResult with provenance_envelope.
 */
export async function fetchEventAnchors(
  chartId: string,
  dateRange: { start: string; end: string },
  opts: {
    minConfidence?: number
    predictionState?: 'open' | 'confirmed' | 'falsified' | 'expired'
  } = {}
): Promise<EventAnchorsResult> {
  const body: Record<string, unknown> = {
    chart_id: chartId,
    date_range: dateRange,
  }
  if (opts.minConfidence !== undefined) {
    body.min_confidence = opts.minConfidence
  }
  if (opts.predictionState) {
    body.prediction_state = opts.predictionState
  }

  return callSidecar<EventAnchorsResult>('/api/compute/phala/event_anchors', body)
}

/**
 * Seed pre-calibrated phala anchors for a chart (idempotent).
 * Calls seed_native_phala_anchors() SQL function via the sidecar.
 */
export async function seedNativeAnchors(
  chartId: string
): Promise<{ ok: boolean; rows_inserted: number; chart_id: string }> {
  return callSidecar('/api/compute/phala/seed_anchors', { chart_id: chartId })
}

// ── Tool registration ──────────────────────────────────────────────────────────

const TOOL_NAME = 'event_anchors'

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart. Must be a valid chart UUID from the charts table.'
    ),

  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe('ISO date YYYY-MM-DD'),
    })
    .describe(
      'Query window for anchor retrieval. Anchors whose 6-month window overlaps this range ' +
        'are returned. For full 2026-2030 coverage: {"start":"2026-01-01","end":"2030-12-31"}.'
    ),

  min_confidence: z
    .number()
    .min(0.0)
    .max(1.0)
    .optional()
    .describe(
      'Minimum confidence threshold [0.0–1.0]. Default 0.0 (all anchors). ' +
        'Confidence = dasha_quality × signal_strength × convergence_score. ' +
        'High ≥ 0.65; Medium 0.45–0.64; Low < 0.45.'
    ),

  prediction_state: z
    .enum(['open', 'confirmed', 'falsified', 'expired'])
    .optional()
    .describe(
      'Filter anchors by their prediction lifecycle state. ' +
        'open = not yet evaluated; confirmed = event occurred; ' +
        'falsified = falsifier condition triggered; expired = window passed without evaluation.'
    ),

  // R6 3b-budgets (R-1): event_anchors previously had NO pagination params at all
  // (register-measured 620KB, unbounded). limit/offset added as real pagination over the
  // (deduped) anchor list; default limit keeps the common case well under budget while a
  // caller who genuinely wants the full 2026-2030 sweep can raise it explicitly.
  limit: z.number().int().min(1).max(500).optional().describe('Max anchors to return (default 50).'),
  offset: z.number().int().min(0).optional().describe('Pagination offset into the (deduped) anchor list (default 0).'),
})

/**
 * Register the event_anchors MCP tool (PH-4-1) on an McpServer.
 *
 * Returns calibrated probabilistic event anchors for a given chart and date range.
 * Each anchor: {window, theme, confidence [0-1], falsifier, contributing_dashas,
 * contributing_signals, source_citation} + provenance_envelope.
 *
 * B.3 mandate: source_citation is non-null on every anchor.
 * Learning Layer rule #4: falsifier is non-null on every anchor.
 *
 * Called from server.ts during L4 Phala registration.
 *
 * Example:
 *   import { registerPhalaEventAnchorsTool } from './tools/phala_event_anchors.js'
 *   registerPhalaEventAnchorsTool(server)
 */
export function registerPhalaEventAnchorsTool(server: McpServer, principal: Principal): void {
  server.tool(
    TOOL_NAME,
    'Return calibrated probabilistic event anchors for a chart and date range (PH-4-1).\n\n' +
      'Each anchor is an ensemble prediction over a 6-month window:\n' +
      '  confidence = dasha_quality × signal_strength × convergence_score ∈ [0.0, 1.0]\n' +
      '  falsifier  = explicit "If [event] does not occur by [date], this is false" clause\n' +
      '  contributing_dashas   = Vimshottari/Yogini dasha lords active in the window\n' +
      '  contributing_signals  = MSR signal IDs from bodha_signals grounding this anchor\n' +
      '  source_citation       = L1 chart_facts + MSR citations (non-null, B.3 compliant)\n\n' +
      // MC-003 (ŚODHANA T1): FORENSIC v8.0 markdown was deleted (PR #187 Legacy Teardown) —
      // live L1 ground-truth is the chart_facts DB table (dasha-period rows DSH.V.023–028).
      'L1 ground-truth: chart_facts DB table (dasha-period rows DSH.V.023–028, Vimshottari 2024-2030).\n' +
      'Dasha regime 2026-2030: Mercury MD/Saturn AD → Ketu MD (Ketu/Venus/Sun/Moon/Mars ADs).\n' +
      'BRAHMA-PH-4-1 | phala.anchors contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return {
          content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }],
          isError: true,
        }
      }

      try {
        const result = await fetchEventAnchors(
          input.chart_id,
          input.date_range,
          {
            minConfidence: input.min_confidence,
            predictionState: input.prediction_state,
          }
        )

        // T-6 fix: dedupe at the earliest point this lane controls (see dedupeAnchors doc).
        const { deduped, duplicates_removed } = dedupeAnchors(result.anchors ?? [])
        const limit = input.limit ?? 50
        const offset = input.offset ?? 0
        const total = deduped.length
        const paged = deduped.slice(offset, offset + limit)

        const content: Record<string, unknown> = {
          ...result,
          anchors: paged,
          anchor_count: paged.length,
          pagination: { offset, limit, total, returned_count: paged.length },
          dedup: {
            duplicates_removed,
            note: duplicates_removed > 0
              ? `${duplicates_removed} duplicate anchor row(s) collapsed at the TS serving ` +
                'boundary (same theme+window+confidence+falsifier+contributing dashas/signals) ' +
                '— T-6. The true fix belongs in the Python ph_nimitta writer; out of scope for ' +
                'this TS-estate lane.'
              : 'No duplicates found in this response.',
          },
        }

        // R-1 / W3-L5 (budget unification, W-8): migrated off bare applyResponseBudget onto
        // the self-verifying finalizeMcpBudget entry point — measures the ACTUAL final
        // object (trim_report included), not just the pre-attachment trim decision.
        const budgeted = finalizeMcpBudget(content, { maxKb: 40, sections: [anchorsSection()] })

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(budgeted, null, 2),
            },
          ],
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        // F-028: standardized error envelope { ok: false, error, tool }
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  ok: false,
                  error: message,
                  tool: TOOL_NAME,
                  chart_id: input.chart_id,
                  date_range: input.date_range,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        }
      }
    }
  )
}
