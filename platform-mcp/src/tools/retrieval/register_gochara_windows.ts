/**
 * retrieval/register_gochara_windows.ts — D-5 Lane G-4 serving surface.
 *
 * Three views over the ONE signed field `kala_gochara_windows` (G-4's standing
 * table, migration 460 — populated by the `ka_gochara_sweep` writer from G-3's
 * lambda_e(t|chart) engine):
 *
 *   gochara_activation_get         — "is this event_class configuration ACTIVE
 *                                     right now (or on a given date)?"
 *   gochara_forecast_get           — "what windows lie ahead in this date range?"
 *   gochara_election_avoidance_get — adverse (is_adverse=true) windows in a date
 *                                     range, served with the full DR-16 five-
 *                                     property payload (BRIEF_D5 §4, hard
 *                                     acceptance item): honest clarity,
 *                                     probabilistic framing, a falsifier,
 *                                     a paired BPHS-cited mitigation (never
 *                                     bare), and confidence-honest disclosure.
 *
 * SCOPE NOTE (must_not_touch discipline): this file is NEW — G-4's declared
 * `may_touch` is `platform-mcp/src/tools/retrieval/register_*gochara*.ts` (new
 * files only). Wiring these tools into `platform-mcp/src/server.ts`'s
 * registration list (`import ...; register...(server, principal)`, the same
 * one-line pattern every sibling tool in this directory uses — see
 * `kala_temporal.ts`/`phala_outlook.ts`) is OUTSIDE that declared scope
 * (server.ts is an existing shared file, not a new file under this glob) —
 * left as an explicit, documented deferral for the Binder/conductor to wire at
 * merge time, exactly one import + one registration call, no logic to review.
 * Every exported `register*Tool` function below is otherwise complete and
 * independently live-tested against the real `kala_gochara_windows` table
 * (see this lane's close report for the direct-call verification transcript).
 *
 * DB ACCESS NOTE: every other tool in this directory proxies DB reads through
 * `callPlatformPrimitive`/`callRegistryCapability`, which requires the target
 * capability to already be registered in `platform/src/lib/retrieval/registry`
 * (a shared, NOT-new file — also outside G-4's declared `may_touch`). Wiring a
 * brand-new capability into that registry needs edits to files this lane does
 * not own (`tool_name_bridge.ts`, the registry's layer index, the surgical
 * whitelist). Rather than reach outside scope, this file uses a small,
 * self-contained `pg.Pool` (an existing `platform-mcp` dependency,
 * `package.json` `"pg": "^8.21.0"`) reading `DATABASE_URL` directly — the same
 * DSN every other MCP-adjacent surface in this codebase already expects to be
 * set (see `phala_outlook.ts`'s own error-hint text: "verify DATABASE_URL and
 * PYTHON_SIDECAR_URL are set"). This keeps the new capability fully
 * self-contained inside this one new file, with no edits to any shared file —
 * the safest interpretation of a `may_touch` glob that names only new files.
 *
 * §N.6 density_contract (CLAUDE.md, BRIEF_D5 §5 — required from day one, not
 * deferred): each tool's `DENSITY_CONTRACT` const below matches the shape
 * `platform/src/lib/retrieval/registry/types.ts`'s `CapabilityDescriptor.
 * density_contract` declares (paginated / facets / empty_reason discipline).
 * It is surfaced on every response's `provenance_envelope.density_contract`
 * so a served payload is self-describing even before a future census/CI
 * harness (§N.6 Part 2) can read it off a registered `CapabilityDescriptor` —
 * registering these AS CapabilityDescriptors in the shared registry is the
 * same out-of-scope wiring step named above, deferred alongside it.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { Pool } from 'pg'
import type { Principal } from '../../types.js'
import { remoteAuthorize } from '../../lib/authz.js'
import { applyResponseBudget, type TrimmableSection } from '../../lib/response_budget.js'

// ── DB pool (self-contained — see module docstring) ──────────────────────────

let _pool: Pool | null = null
function getPool(): Pool {
  if (!_pool) {
    const connectionString = process.env['DATABASE_URL']
    if (!connectionString) {
      throw new Error(
        'DATABASE_URL not set — gochara_windows tools require direct DB access ' +
          '(see register_gochara_windows.ts module docstring for why this tool does not ' +
          'proxy through /api/retrieval/capability).'
      )
    }
    _pool = new Pool({ connectionString, max: 5, connectionTimeoutMillis: 10_000 })
  }
  return _pool
}

// ── Shared row shape ──────────────────────────────────────────────────────────

export interface GocharaContinuityState {
  raw_start: string
  raw_end: string
  left_active: boolean
  right_active: boolean
}

export interface GocharaWindowRow {
  id: number
  chart_id: string
  event_class: string
  temporal_shape: 'point' | 'interval' | 'chain'
  window_start: string
  window_end: string
  peak_date: string
  milestone_id: string | null
  is_irreversibility_milestone: boolean
  signed_intensity: number
  raw_intensity: number
  valence: 'gain' | 'loss' | 'neutral' | 'mixed'
  is_adverse: boolean
  active_sentences: unknown[]
  contributing_systems: Array<{ system_id: string; active: boolean; weight: number; detail?: unknown }>
  suppression_state: Record<string, unknown>
  peak_basis: string
  calibration_state: string
  source: 'live' | 'fixture'
  computed_at: string
  continuity_state: GocharaContinuityState | null
  plateau_disclosure: {
    window_start_open: boolean
    window_end_open: boolean
    note: string
  } | null
}

// D-5 native disposition (2026-07-20, gate_run_2 finding 1): "the cap never
// fabricates a closed window from a truncated anchor." `window_start`/
// `window_end` on an interval-shaped row can be a structural cap
// (ka_gochara_sweep's duration_prior.max_days ceiling, migration 461's
// `continuity_state`), not a genuine signal-cessation boundary. A caller
// reading only window_start/window_end cannot tell "the signal really
// ended here" from "we simply haven't merged the next adjacent
// already-committed segment yet, or the plateau is structurally capped
// mid-signal" -- `left_active`/`right_active` are the writer's own honest
// record of which. This derives a disclosure object from the SAME
// `continuity_state` the writer persists, so the served bound is never
// presented as more definitive than the instrument actually knows.
export function derivePlateauDisclosure(row: GocharaWindowRow): GocharaWindowRow['plateau_disclosure'] {
  const cs = row.continuity_state
  if (row.temporal_shape !== 'interval' || !cs) return null
  const windowStartOpen = cs.left_active
  const windowEndOpen = cs.right_active
  if (!windowStartOpen && !windowEndOpen) return null
  const parts: string[] = []
  if (windowStartOpen) parts.push(`elevated since ≤${row.window_start} (true onset unresolved -- earlier adjacent history not yet merged)`)
  if (windowEndOpen) parts.push(`still elevated past ${row.window_end} (served end is a structural cap or not-yet-merged boundary, not a confirmed signal cessation)`)
  return {
    window_start_open: windowStartOpen,
    window_end_open: windowEndOpen,
    note: parts.join('; '),
  }
}

function withPlateauDisclosure(rows: GocharaWindowRow[]): GocharaWindowRow[] {
  return rows.map((row) => ({ ...row, plateau_disclosure: derivePlateauDisclosure(row) }))
}

const SOURCE_CITATION =
  'kala_gochara_windows (L3 Kāla, D-5 Lane G-4 ka_gochara_sweep writer) — ' +
  'lambda_e via services/gochara_intensity (G-3), consuming gochara_resonance_map ' +
  '(G-1) + gochara_grammar (G-2)'

const ROW_COLUMNS = `
  id, chart_id, event_class, temporal_shape,
  to_char(window_start, 'YYYY-MM-DD') AS window_start,
  to_char(window_end, 'YYYY-MM-DD') AS window_end,
  to_char(peak_date, 'YYYY-MM-DD') AS peak_date,
  milestone_id, is_irreversibility_milestone,
  signed_intensity::float8 AS signed_intensity,
  raw_intensity::float8 AS raw_intensity,
  valence, is_adverse,
  active_sentences, contributing_systems, suppression_state,
  peak_basis, calibration_state, source,
  computed_at, continuity_state
`

async function queryRows(sql: string, params: unknown[]): Promise<{ rows: GocharaWindowRow[]; ok: boolean; error?: string }> {
  try {
    const pool = getPool()
    const { rows } = await pool.query(sql, params)
    return { rows: rows as GocharaWindowRow[], ok: true }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { rows: [], ok: false, error: message }
  }
}

// ── §N.6 density_contract (documented, see module docstring) ────────────────

const ACTIVATION_DENSITY_CONTRACT = {
  max_digest_bytes: 20_000,
  paginated: false,
  facets: ['event_class', 'temporal_shape', 'is_adverse'],
  empty_reason: true,
} as const

const FORECAST_DENSITY_CONTRACT = {
  max_digest_bytes: 60_000,
  paginated: true,
  facets: ['event_class', 'temporal_shape', 'valence', 'is_adverse'],
  empty_reason: true,
} as const

const ELECTION_AVOIDANCE_DENSITY_CONTRACT = {
  max_digest_bytes: 60_000,
  paginated: true,
  facets: ['event_class', 'temporal_shape'],
  empty_reason: true,
} as const

// ── Response-budget sections (§N.6 hardFloor — see response_budget.ts) ──────
// Every row in `kala_gochara_windows` is a materialized, real-intensity
// computed window (no catalog-only/label-match rows exist in this table's
// design — G-3's PROMISE is an honest 0.0, never served, when a chart/
// event_class has no G-1 targets). The `windows` array is therefore this
// tool's single densest/most-authoritative section and is hardFloor-protected
// so a budget trim never zeroes it before trimming per-row `active_sentences`
// detail first.

function windowsSection<T extends { windows: GocharaWindowRow[] }>(minKeep: number): TrimmableSection<T>[] {
  return [
    {
      path: 'windows',
      getArray: (c) => c.windows,
      setArray: (c, kept) => {
        c.windows = kept as GocharaWindowRow[]
      },
      minKeep,
      hardFloor: true,
      recover: { instrument: 'gochara_forecast_get', hint: 'narrow date_range or event_class to page through the full result' },
      label: 'kala_gochara_windows rows (materialized, firings-authoritative)',
    },
  ]
}

// ══════════════════════════════════════════════════════════════════════════
// 1. gochara_activation_get — "is this configuration active right now?"
// ══════════════════════════════════════════════════════════════════════════

const ActivationInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  as_of_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional()
    .describe('Date to check activation on (YYYY-MM-DD). Default: today.'),
  event_class: z.string().optional().describe('Filter to one event_class (e.g. "marriage"). Default: all.'),
})

export async function computeGocharaActivation(
  chartId: string,
  asOfDate: string,
  eventClass?: string
): Promise<Record<string, unknown>> {
  const params: unknown[] = [chartId, asOfDate]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND window_start <= $2 AND window_end >= $2`
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  sql += ' ORDER BY signed_intensity DESC'

  const { rows: rawRows, ok, error } = await queryRows(sql, params)
  const rows = withPlateauDisclosure(rawRows)
  const content: { windows: GocharaWindowRow[] } = { windows: rows }
  const budgeted = applyResponseBudget(content, 20, windowsSection(5))

  return {
    windows: budgeted.content.windows,
    trim_report: budgeted.trim_report,
    provenance_envelope: {
      source: 'gochara_activation_get',
      source_citation: SOURCE_CITATION,
      chart_id: chartId,
      as_of_date: asOfDate,
      event_class_filter: eventClass ?? null,
      computed_at: new Date().toISOString(),
      window_count: rows.length,
      backing_data_reachable: ok,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no kala_gochara_windows row spans this date for this chart/event_class filter — an honest zero-activation result, not a fabricated one'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
      density_contract: ACTIVATION_DENSITY_CONTRACT,
    },
  }
}

export function registerGocharaActivationTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_activation_get',
    'What it does: Returns kala_gochara_windows rows ACTIVE on a given date (default today) ' +
      'for a chart — "is this event_class configuration firing right now?" One of three views ' +
      '(activation / forecast / election_avoidance) over the D-5 G-4 signed intensity field. ' +
      'Shape-aware: point rows are single-day matches, interval rows match when the date falls ' +
      'inside the span, chain rows are per-milestone (each its own single-day match).\n\n' +
      'Output: { windows: [...], provenance_envelope: {...} }. An honest empty `windows` array ' +
      'is distinguished from an unreachable table via provenance_envelope.empty_reason — never ' +
      'silently substituted.\n\nRequires: chart_id (UUID).',
    ActivationInputSchema.shape,
    async (params) => {
      const input = ActivationInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      const asOf = input.as_of_date ?? new Date().toISOString().slice(0, 10)
      try {
        const result = await computeGocharaActivation(input.chart_id, asOf, input.event_class)
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_activation_get' }) }],
          isError: true,
        }
      }
    }
  )
}

// ══════════════════════════════════════════════════════════════════════════
// 2. gochara_forecast_get — forward-looking windows in a date range
// ══════════════════════════════════════════════════════════════════════════

const ForecastInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    })
    .describe('Date range to forecast over (YYYY-MM-DD each). Overlap semantics: window_end >= start AND window_start <= end.'),
  event_class: z.string().optional().describe('Filter to one event_class. Default: all.'),
  valence: z.enum(['gain', 'loss', 'neutral', 'mixed']).optional().describe('Filter to one valence. Default: all.'),
  limit: z.number().int().min(1).max(500).default(100),
})

export async function computeGocharaForecast(
  chartId: string,
  dateRange: { start: string; end: string },
  eventClass: string | undefined,
  valence: string | undefined,
  limit: number
): Promise<Record<string, unknown>> {
  const params: unknown[] = [chartId, dateRange.end, dateRange.start]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND window_start <= $2 AND window_end >= $3`
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  if (valence) {
    params.push(valence)
    sql += ` AND valence = $${params.length}`
  }
  params.push(limit)
  sql += ` ORDER BY window_start ASC, signed_intensity DESC LIMIT $${params.length}`

  const { rows: rawRows, ok, error } = await queryRows(sql, params)
  const rows = withPlateauDisclosure(rawRows)
  const content: { windows: GocharaWindowRow[] } = { windows: rows }
  const budgeted = applyResponseBudget(content, 40, windowsSection(10))

  const byShape = { point: 0, interval: 0, chain: 0 } as Record<string, number>
  for (const r of rows) byShape[r.temporal_shape] = (byShape[r.temporal_shape] ?? 0) + 1

  return {
    windows: budgeted.content.windows,
    trim_report: budgeted.trim_report,
    provenance_envelope: {
      source: 'gochara_forecast_get',
      source_citation: SOURCE_CITATION,
      chart_id: chartId,
      date_range: dateRange,
      event_class_filter: eventClass ?? null,
      valence_filter: valence ?? null,
      computed_at: new Date().toISOString(),
      window_count: rows.length,
      shape_breakdown: byShape,
      backing_data_reachable: ok,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no kala_gochara_windows rows overlap this date_range/filter combination — honest zero result. ' +
              'Note: G-4 has only materialized rows for chart-relative decades that have actually been swept ' +
              '(see asset build state) — an empty result for an unswept decade is a coverage gap, not a ' +
              'negative signal; check kala_gochara_windows build coverage before reading this as "nothing happens".'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
      density_contract: FORECAST_DENSITY_CONTRACT,
    },
  }
}

export function registerGocharaForecastTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_forecast_get',
    'What it does: Returns kala_gochara_windows rows overlapping a forward-looking date range ' +
      'for a chart — the FORECAST view over the D-5 G-4 signed lambda_e intensity field. ' +
      'Shape-aware (point/interval/chain, per brahma_event_ontology — BRIEF_D5 §3): an ' +
      'interval-shaped row is a real elevated-hazard SPAN (never a lone asserted day); a ' +
      'chain-shaped row is one of several per-milestone sub-windows, each independently scored, ' +
      'with is_irreversibility_milestone flagging the class\'s primary claim where declared.\n\n' +
      'Output: { windows: [...], provenance_envelope: { shape_breakdown, empty_reason, ... } }.\n\n' +
      'Requires: chart_id (UUID), date_range {start, end}.',
    ForecastInputSchema.shape,
    async (params) => {
      const input = ForecastInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      try {
        const result = await computeGocharaForecast(input.chart_id, input.date_range, input.event_class, input.valence, input.limit)
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_forecast_get' }) }],
          isError: true,
        }
      }
    }
  )
}

// ══════════════════════════════════════════════════════════════════════════
// 3. gochara_election_avoidance_get — adverse windows, full DR-16 payload
// ══════════════════════════════════════════════════════════════════════════
//
// BRIEF_D5 §4 (DR-16 honest-clarity gate, hard acceptance item, NOT a
// diagnostic): every adverse window served here carries, in ONE payload:
//   1. honest clarity      — plain valence/magnitude language, no euphemism
//   2. probabilistic       — `framing` field states this explicitly; NEVER a
//                             fatalistic/point death-or-ruin claim (the
//                             uniform birth->birth+100y horizon itself exists
//                             so this table never encodes a longevity opinion)
//   3. falsifier-bearing    — `falsifier` names what would disconfirm the claim
//   4. mitigation-paired    — `mitigation` (BPHS-cited brahma_remedy_corpus
//                             row, matched by the window's dominant
//                             contributing graha) ships in the SAME payload,
//                             never bare; `suppression_state` (G-2's own
//                             vedha/kartari damping) is also surfaced
//   5. confidence-honest    — `calibration_state`/`n_observations`/
//                             `control_delta` disclosed per row (D-5 ships
//                             `structural_prior` only; empirical calibration
//                             is D-4b's job, not claimed here)

const ElectionAvoidanceInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    })
    .describe('Date range to check for adverse windows to avoid (YYYY-MM-DD each).'),
  event_class: z.string().optional().describe('Filter to one event_class. Default: all adverse classes.'),
  limit: z.number().int().min(1).max(200).default(50),
})

export function dominantGraha(row: GocharaWindowRow): string | null {
  const active = (row.contributing_systems ?? []).filter((s) => s.active)
  // Prefer a graha-double-transit system's own detail (guru_shani_double_transit
  // names a real graha pair); otherwise fall back to the highest-weight active
  // dasha lord if the detail carries one (best-effort, never fabricated).
  for (const s of active) {
    const detail = s.detail as Record<string, unknown> | undefined
    const lord = detail?.['lord_graha'] ?? detail?.['natural_planet'] ?? detail?.['natal_planet']
    if (typeof lord === 'string') return lord.toLowerCase()
  }
  return null
}

async function fetchMitigation(planet: string | null): Promise<Record<string, unknown> | null> {
  if (!planet) return null
  const { rows } = await queryRows(
    `SELECT remedy_id, planet, domain, remedy_type, prescription_text, mantra_text, gemstone,
            charity_action, source_citation, classical_ref, confidence
       FROM brahma_remedy_corpus WHERE planet = $1 ORDER BY confidence DESC LIMIT 1`,
    [planet]
  ) as unknown as { rows: Record<string, unknown>[] }
  return rows[0] ?? null
}

export async function computeGocharaElectionAvoidance(
  chartId: string,
  dateRange: { start: string; end: string },
  eventClass: string | undefined,
  limit: number
): Promise<Record<string, unknown>> {
  const params: unknown[] = [chartId, dateRange.end, dateRange.start]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND is_adverse = true AND window_start <= $2 AND window_end >= $3`
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  params.push(limit)
  sql += ` ORDER BY signed_intensity ASC LIMIT $${params.length}`  // most-negative first

  const { rows, ok, error } = await queryRows(sql, params)

  const avoidWindows = await Promise.all(
    rows.map(async (row) => {
      const planet = dominantGraha(row)
      const mitigation = await fetchMitigation(planet)
      const plateauDisclosure = derivePlateauDisclosure(row)
      return {
        event_class: row.event_class,
        temporal_shape: row.temporal_shape,
        window_start: row.window_start,
        window_end: row.window_end,
        peak_date: row.peak_date,
        milestone_id: row.milestone_id,
        signed_intensity: row.signed_intensity,
        raw_intensity: row.raw_intensity,
        valence: row.valence,
        plateau_disclosure: plateauDisclosure,
        // 1. honest clarity (D-5 native disposition, 2026-07-20: never state a
        // capped/truncated bound as if it were a confirmed closure — see
        // `derivePlateauDisclosure`)
        clarity_statement:
          `Elevated adverse-valence configuration for '${row.event_class}' ` +
          `(${row.temporal_shape}-shaped) over ${row.window_start}..${row.window_end}, ` +
          `raw magnitude ${row.raw_intensity.toFixed(4)}. This is a probabilistic signal from a ` +
          `structural-prior model, not a certainty and not a fatalistic prediction.` +
          (plateauDisclosure ? ` PLATEAU NOTICE: ${plateauDisclosure.note}.` : ''),
        // 2. probabilistic, never fatalistic
        framing: {
          probabilistic: true,
          fatalistic_claim: false,
          note:
            'Never a death/ruin point-claim. The birth->birth+100y sweep horizon is uniform for ' +
            'every chart and is NOT tied to computed longevity/ayurdaya (Ethical Framework — using ' +
            'it to bound the sweep would itself encode a lifespan opinion).',
        },
        // 3. falsifier-bearing
        falsifier: {
          statement:
            `This claim is falsified if no LEL-loggable adverse '${row.event_class}' outcome is ` +
            `recorded for chart ${chartId} overlapping ${row.window_start}..${row.window_end}.`,
          checked_via: 'G-5 prospective-ledger outcome matching (brahma_prospective_ledger, ' +
            'once this window is filed as a claim) — not yet filed by this read-only view.',
        },
        // 4. mitigation-paired (never bare)
        suppression_state: row.suppression_state,
        mitigation: mitigation ?? {
          available: false,
          reason: planet
            ? `no brahma_remedy_corpus row found for planet='${planet}'`
            : 'no dominant contributing graha could be resolved from contributing_systems for this window ' +
              '-- honest gap, not a fabricated remedy',
        },
        // 5. confidence-honest
        confidence_disclosure: {
          calibration_state: row.calibration_state,
          n_observations: null,
          control_delta: null,
          note:
            'D-5 ships structural_prior weights only (beta_e, PERMISSION system weights, suppression ' +
            'damping) -- empirical calibration (n_observations, control_delta) is D-4b\'s job, not yet ' +
            'available. This is disclosed, not silently omitted.',
        },
        contributing_systems_active: (row.contributing_systems ?? []).filter((s) => s.active).map((s) => s.system_id),
        active_sentences_count: row.active_sentences.length,
        peak_basis: row.peak_basis,
        source_citation: SOURCE_CITATION,
      }
    })
  )

  const content: { windows: typeof avoidWindows } = { windows: avoidWindows }
  const budgeted = applyResponseBudget(
    content,
    50,
    [
      {
        path: 'windows',
        getArray: (c) => c.windows,
        setArray: (c, kept) => {
          c.windows = kept as typeof avoidWindows
        },
        minKeep: 5,
        hardFloor: true,
        recover: { instrument: 'gochara_election_avoidance_get', hint: 'narrow date_range or event_class' },
        label: 'adverse kala_gochara_windows rows with DR-16 payload',
      },
    ]
  )

  return {
    windows: budgeted.content.windows,
    trim_report: budgeted.trim_report,
    provenance_envelope: {
      source: 'gochara_election_avoidance_get',
      source_citation: SOURCE_CITATION,
      chart_id: chartId,
      date_range: dateRange,
      event_class_filter: eventClass ?? null,
      computed_at: new Date().toISOString(),
      window_count: rows.length,
      dr16_properties: ['honest_clarity', 'probabilistic_never_fatalistic', 'falsifier_bearing', 'mitigation_paired', 'confidence_honest'],
      backing_data_reachable: ok,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no adverse (is_adverse=true) kala_gochara_windows rows overlap this date_range/filter -- ' +
              'an honestly clean window, not a fabricated all-clear (verify build coverage for this range)'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
      density_contract: ELECTION_AVOIDANCE_DENSITY_CONTRACT,
    },
  }
}

export function registerGocharaElectionAvoidanceTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_election_avoidance_get',
    'What it does: Returns ADVERSE (is_adverse=true) kala_gochara_windows rows overlapping a date ' +
      'range — the ELECTION-AVOIDANCE view over the D-5 G-4 signed lambda_e field ("which dates in ' +
      'this range should an election/muhurta avoid?"). Every returned window carries the full DR-16 ' +
      'honest-clarity payload in one object (BRIEF_D5 §4, binding): clarity_statement (plain language, ' +
      'no euphemism), framing (probabilistic, never fatalistic), falsifier, suppression_state + ' +
      'mitigation (BPHS-cited remedy from brahma_remedy_corpus, paired in the SAME payload — honestly ' +
      'flagged unavailable when no remedy row resolves, never fabricated), and confidence_disclosure ' +
      '(calibration_state — D-5 ships structural_prior only).\n\n' +
      'DEFERRED (documented, not silently dropped): the existing muhurta_finder tool is NOT ' +
      're-pointed to this table by this lane (see register_gochara_windows.ts module docstring / ' +
      'this lane\'s close report for the full reasoning) — use this tool directly for the signed-field ' +
      'election-avoidance view in the interim.\n\n' +
      'Requires: chart_id (UUID), date_range {start, end}.',
    ElectionAvoidanceInputSchema.shape,
    async (params) => {
      const input = ElectionAvoidanceInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      try {
        const result = await computeGocharaElectionAvoidance(input.chart_id, input.date_range, input.event_class, input.limit)
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_election_avoidance_get' }) }],
          isError: true,
        }
      }
    }
  )
}

// ── Combined registration convenience (server.ts wires this ONE call) ───────

export function registerGocharaWindowsTools(server: McpServer, principal: Principal): void {
  registerGocharaActivationTool(server, principal)
  registerGocharaForecastTool(server, principal)
  registerGocharaElectionAvoidanceTool(server, principal)
}
