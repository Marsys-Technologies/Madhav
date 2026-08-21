/**
 * mimamsa_outcome.ts — BRAHMA-MI-5-3: mimamsa.outcome
 *
 * L5 Mīmāṃsā: outcome scoring — Brier score per prediction; calibration table.
 *
 * Contract (BRAHMA MI-5-3):
 *   Table:  mimamsa_calibration (chart_id UUID, technique TEXT, ayanamsha_id TEXT,
 *           brier_score FLOAT CHECK(0<=brier_score<=1), sample_size INT,
 *           computed_at TIMESTAMPTZ, source_citation TEXT NOT NULL)
 *   Tool:   record_outcome(prediction_id, outcome_observed) →
 *               {brier_score, updated_calibration, provenance_envelope}
 *   Scoring: Brier score = (confidence - outcome_binary)²
 *   Calibration: mean(brier_scores) per (technique, ayanamsha_id)
 *
 * NO LEAKAGE: life_events must never feed into prediction generation —
 *   only into calibration after outcomes are observed.
 *
 * Reference birth: 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *
 * L1 ground-truth:
 *   chart_facts DB table (dasha-period rows DSH.V.023–028, Vimshottari dasha 2024-2030) —
 *   MC-003 (ŚODHANA T1): FORENSIC v8.0 markdown was deleted (PR #187 Legacy Teardown);
 *   chart_facts is the live canonical source, not the retired document.
 *   LEL v1.7 (life event log — outcome ground-truth)
 *
 * Wiring: registerMimamsaOutcomeTool(server) → server.ts during L5 Mīmāṃsā registration.
 *
 * BRAHMA-MI-5-3
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { budgetMcpContent } from '../lib/response_budget.js'

// ── Environment ────────────────────────────────────────────────────────────────

const PYTHON_SIDECAR_URL = (
  process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
).replace(/\/$/, '')

const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''
const TOOL_TIMEOUT_MS = 30_000

// CR-51/CR-30 fix (D-1.6 S-1): the `query_calibration` MCP tool below used to call
// the sidecar's `/api/compute/mimamsa/query_calibration` endpoint directly
// (queryCalibration(), still exported below for any external caller that imports it
// directly), while the twin alias `mimamsa_calibration_get` (register_p1_aliases.ts)
// called the platform primitive `query_calibration` -> registry capability
// `marsys://tool/L5/query_calibration` (platform/.../L5_mimamsa/query_calibration.ts),
// which reads mimamsa_calibration + mimamsa_reliability + mimamsa_multipliers +
// mimamsa_qa_eval and returns a rich payload (verdict_distribution, reliability_curve,
// multipliers, qa_results). Confirmed live 2026-07-16 on chart 482012f1: the sidecar
// path returned `{ok:true, rows:[], row_count:0}` while mimamsa_calibration_get
// returned the full multipliers/qa_results payload for the SAME chart — two different
// answers to what a caller reasonably expects to be one capability. The registry-backed
// path is the richer, live one (it actually has data for this chart), so it is now the
// canonical face: `query_calibration`'s tool handler below delegates to the SAME
// platform primitive `mimamsa_calibration_get` uses, making the two tool names a
// strict alias pair (same handler, same payload shape) rather than two divergent
// implementations. The sidecar-backed `queryCalibration()` function is retained
// (exported) for callers that still need the raw mimamsa_calibration table view, but
// the MCP tool surface no longer uses it as the query_calibration handler.
const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callPlatformPrimitiveDirect(
  tool: string,
  params: Record<string, unknown>,
  principal: Principal,
): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/primitives/${encodeURIComponent(tool)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Audience-Tier': principal.role === 'super_admin' ? 'super_admin' : 'client',
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ params }),
    signal: AbortSignal.timeout(TOOL_TIMEOUT_MS),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[mimamsa_outcome] platform primitive "${tool}" failed: ${res.status} ${text}`)
  }
  return res.json()
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface UpdatedCalibration {
  technique: string
  ayanamsha_id: string
  brier_score: number   // mean Brier score for this (technique, ayanamsha_id) slice
  sample_size: number
  computed_at: string   // ISO datetime
}

export interface ProvenanceEnvelope {
  source: string
  asset: string
  algorithm: string
  chart_id: string
  prediction_id: string
  technique: string
  ayanamsha_id: string
  recorded_at: string      // ISO datetime
  l1_ground_truth: string
  b3_citation_compliant: boolean
  leakage_guard_passed: boolean
}

export interface RecordOutcomeResult {
  ok: boolean
  prediction_id: string
  outcome_observed: boolean
  brier_score: number          // individual Brier score for this prediction
  prediction_state: 'confirmed' | 'falsified'
  updated_calibration: UpdatedCalibration
  provenance_envelope: ProvenanceEnvelope
}

export interface CalibrationRow {
  id: number
  chart_id: string
  technique: string
  ayanamsha_id: string
  brier_score: number
  sample_size: number
  source_citation: string
  computed_at: string
}

export interface QueryCalibrationResult {
  ok: boolean
  rows: CalibrationRow[]
  row_count: number
  provenance_envelope: {
    source: string
    asset: string
    algorithm: string
    chart_id: string
    technique_filter: string | null
    ayanamsha_filter: string | null
    queried_at: string
    l1_ground_truth: string
    b3_citation_compliant: boolean
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

// ── Core functions ─────────────────────────────────────────────────────────────

/**
 * RETIRED (CR-115/CR-128, 2026-07-23, native-directed). Throws unconditionally, before
 * ever contacting the sidecar — defense-in-depth alongside the sidecar's own retirement
 * (outcome.py's record_outcome() / RecordOutcomeRetiredError, HTTP 410).
 *
 * Why: this call chain targeted phala_anchors/mimamsa_calibration columns that do not
 * exist on the live schema and was fully disconnected from the real, live calibration
 * write-surface (the mi_pramana -> mi_gunanaka orchestrator writer pair, which already
 * runs automatically as part of a chart rebuild). There is no manual outcome-recording
 * step in the real architecture. See MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-115 / CR-128
 * (both RESOLVED 2026-07-23).
 */
export async function recordOutcome(
  _predictionId: string,
  _outcomeObserved: boolean,
  _opts: {
    technique?: string
    ayanamshaId?: string
    chartId?: string
    outcomeNote?: string
  } = {}
): Promise<RecordOutcomeResult> {
  throw new Error(
    'record_outcome is RETIRED (CR-115/CR-128, 2026-07-23, native-directed) — it targeted ' +
      'phantom phala_anchors/mimamsa_calibration columns disconnected from the real pipeline. ' +
      'Calibration is computed automatically by the mi_pramana -> mi_gunanaka orchestrator ' +
      'writers from LEL-event provenance; there is no manual outcome-recording step. See ' +
      'MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-115 / CR-128 (both RESOLVED 2026-07-23).'
  )
}

/**
 * Query the mimamsa_calibration table for current calibration state.
 * Returns rows ordered by computed_at DESC (most recent first).
 */
export async function queryCalibration(
  opts: {
    chartId?: string
    technique?: string
    ayanamshaId?: string
    limit?: number
  } = {}
): Promise<QueryCalibrationResult> {
  const body: Record<string, unknown> = {}
  if (opts.chartId) body.chart_id = opts.chartId
  if (opts.technique) body.technique = opts.technique
  if (opts.ayanamshaId) body.ayanamsha_id = opts.ayanamshaId
  if (opts.limit) body.limit = opts.limit

  return callSidecar<QueryCalibrationResult>('/api/compute/mimamsa/query_calibration', body)
}

// ── Tool registration ──────────────────────────────────────────────────────────

// Valid enums for input validation
const TECHNIQUES = [
  'vimshottari', 'yogini', 'kp', 'jaimini_chara',
  'transit_outer', 'transit_inner', 'sade_sati', 'ashtakavarga', 'ensemble',
] as const

const AYANAMSHAS = [
  'lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta',
] as const

/**
 * Register both MI-5-3 MCP tools on an McpServer:
 *   1. record_outcome — record an observed outcome + update calibration
 *   2. query_calibration — query mimamsa_calibration table
 *
 * Called from server.ts during L5 Mīmāṃsā registration.
 *
 * Example:
 *   import { registerMimamsaOutcomeTool } from './tools/mimamsa_outcome.js'
 *   registerMimamsaOutcomeTool(server)
 */
export function registerMimamsaOutcomeTool(server: McpServer, principal: Principal): void {
  // ── Tool 1: record_outcome ─────────────────────────────────────────────────

  server.tool(
    'record_outcome',
    '[DEPRECATED — RETIRED, CR-115/CR-128, 2026-07-23] This tool always fails. It used to ' +
      'target phala_anchors/mimamsa_calibration columns that do not exist on the live schema, ' +
      'disconnected from the real calibration pipeline. Calibration is computed automatically ' +
      'by the mi_pramana -> mi_gunanaka orchestrator writers from LEL-event provenance as part ' +
      'of a normal chart rebuild — there is no manual outcome-recording step. To inspect current ' +
      'calibration state, use query_calibration / mimamsa_calibration_get instead. See ' +
      'MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-115 / CR-128 (both RESOLVED) for the full record.',
    {
      prediction_id: z
        .string()
        .min(1)
        .describe(
          'anchor_id from phala_anchors (e.g. "PH-4-1.2026H1.CAREER"). ' +
            'This is the prediction being evaluated.'
        ),

      outcome_observed: z
        .boolean()
        .describe(
          'Whether the predicted event actually occurred. ' +
            'true = event occurred (prediction "confirmed"). ' +
            'false = event did not occur (prediction "falsified").'
        ),

      technique: z
        .enum(TECHNIQUES)
        .optional()
        .describe(
          'Dasha/technique used for this prediction. Default: "vimshottari". ' +
            'Options: vimshottari | yogini | kp | jaimini_chara | transit_outer | ' +
            'transit_inner | sade_sati | ashtakavarga | ensemble.'
        ),

      ayanamsha_id: z
        .enum(AYANAMSHAS)
        .optional()
        .describe(
          'Ayanamsha used for chart computation. Default: "lahiri". ' +
            'Options: lahiri | true_chitra | kp | raman | surya_siddhanta.'
        ),

      chart_id: z
        .string()
        .uuid()
        .optional()
        .describe(
          'Chart UUID. Must be a valid chart UUID from the charts table.'
        ),

      outcome_note: z
        .string()
        .optional()
        .describe(
          'Optional operator annotation on what actually happened. ' +
            'Stored in phala_anchors.outcome_note. ' +
            'Used by the Learning Layer for correction analysis.'
        ),
    },
    async (params) => {
      if (params.chart_id) {
        const authorized = await remoteAuthorize(principal, params.chart_id, 'all')
        if (!authorized) {
          return {
            content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to write outcomes for this chart' }],
            isError: true,
          }
        }
      }
      try {
        const result = await recordOutcome(
          params.prediction_id,
          params.outcome_observed,
          {
            technique: params.technique,
            ayanamshaId: params.ayanamsha_id,
            chartId: params.chart_id,
            outcomeNote: params.outcome_note,
          }
        )

        const budgeted = budgetMcpContent(result, 'record_outcome')
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
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  error: true,
                  tool: 'record_outcome',
                  message,
                  prediction_id: params.prediction_id,
                  outcome_observed: params.outcome_observed,
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

  // ── Tool 2: query_calibration ──────────────────────────────────────────────
  // CR-51/CR-30 fix (D-1.6 S-1): canonical-face unification. `query_calibration` now
  // delegates to the SAME platform primitive as `mimamsa_calibration_get`
  // (marsys://tool/L5/query_calibration) so both tool names return an identical
  // payload shape — the two are a strict alias pair, not two divergent
  // implementations. See the CR-51/CR-30 comment above `callPlatformPrimitiveDirect`
  // for the full before/after.

  server.tool(
    'query_calibration',
    '[Canonical alias of mimamsa_calibration_get — CR-51/CR-30 unification] ' +
      'Query calibration state for a chart (MI-5-3): verdict distribution, reliability ' +
      'curve, Learning-Layer multipliers (LL1 family weights), and QA eval results ' +
      '(degenerate-distribution / negative-control / control-window checks). ' +
      'Each multiplier row: {weight_id, mechanism, target_kind, target_ref, domain, ' +
      'applied_multiplier, raw_multiplier, n_observations, promotion_status, ' +
      'gate_passed, kill_switch_state, divergence_from_classical}.\n\n' +
      'Calibration = mean((confidence - outcome_binary)²) per (technique, ayanamsha_id).\n' +
      'Uninformative baseline = 0.25 (equivalent to random 50/50 at 0.5 confidence).\n\n' +
      // MC-003 (ŚODHANA T1): FORENSIC v8.0 markdown was deleted (PR #187 Legacy
      // Teardown) — the live L1 ground-truth source is the chart_facts DB table.
      'L1 ground-truth: chart_facts DB table (dasha-period rows DSH.V.023–028) + LEL v1.7.\n' +
      'BRAHMA-MI-5-3 | mimamsa.outcome contract.',
    {
      // CR-51/CR-30: chart_id is now REQUIRED (matches mimamsa_calibration_get and the
      // underlying marsys://tool/L5/query_calibration capability's required_inputs).
      // technique/ayanamsha_id are no longer accepted params — the richer canonical
      // capability scores the whole chart's calibration scorecard (verdict distribution +
      // reliability curve + multipliers + QA results), not a per-technique row slice; the
      // old sidecar-backed technique/ayanamsha_id filtering is retained only on the
      // separately-exported queryCalibration() helper for any caller that still needs the
      // raw mimamsa_calibration table view.
      chart_id: z
        .string()
        .uuid()
        .describe(
          'Chart UUID. Required — must be a valid chart UUID from the charts table.'
        ),

      // F-27 (PARIŚEṢA V4): `domain`, `limit` and `offset` used to be declared here and
      // forwarded to the platform primitive. All three were complete no-ops — the
      // capability `marsys://tool/L5/query_calibration` declares
      // `required_inputs: ['chart_id']` and its handler reads only `chart_id`,
      // `include_held_out` and `promoted_only`; it never reads domain/limit/offset, so
      // two calls differing only in those fields returned a byte-identical payload.
      //
      // They are removed rather than implemented, because no honest implementation
      // exists: the scorecard's verdict rows come from `mimamsa_calibration`, which has
      // NO domain column at all (only `score_domain`, a numeric match-quality score, not
      // a domain label). The one table that does carry a `domain` column,
      // `mimamsa_multipliers`, holds NULL there for every row on the canonical chart.
      // A `domain` filter over this data would have to be invented, not derived —
      // CLAUDE.md §N.7 item 6 (an honest null beats an invented judgment) and §N.8
      // (Earned-Signal Principle: a parameter with no code path behind it is not a
      // feature, it is an unimplemented check wearing a feature's clothes).
      //
      // The twin alias `mimamsa_calibration_get` (register_p1_aliases.ts) already
      // dropped these three fields; this restores contract parity across the documented
      // CR-51/CR-30 strict-alias pair.
    },
    async (params) => {
      try {
        const result = await callPlatformPrimitiveDirect(
          'query_calibration',
          { chart_id: params.chart_id },
          principal,
        )

        const budgeted = budgetMcpContent(result, 'query_calibration')
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
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                {
                  error: true,
                  tool: 'query_calibration',
                  message,
                  chart_id: params.chart_id,
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
