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
 * DB ACCESS NOTE (SARVA-SIDDHI W-1 T-1, 2026-07-24 — root-cause fix, replaces
 * the original self-contained-pg.Pool approach): the D-5 G-4 lane originally
 * opened a self-contained `pg.Pool` here reading `process.env['DATABASE_URL']`,
 * to stay inside a `may_touch` glob that named only new files. That was the
 * defect: the deployed `amjis-mcp` Cloud Run service has NO direct DB path by
 * design — `deploy.yml`'s `deploy-mcp` job sets only PLATFORM_URL /
 * PYTHON_SIDECAR_URL / MCP_BASE_URL, never DATABASE_URL and no Cloud SQL
 * attachment — so `getPool()` threw "DATABASE_URL not set" and all three tools
 * served `backing_data_reachable:false` in production (register CR-131). Every
 * OTHER MCP tool honors the invariant "the MCP server does not hold a direct DB
 * connection" and proxies reads through the platform, which does hold the
 * connection. This file now does the same: it routes its (already-parameterized,
 * server-authored, SELECT-only) SQL through `POST ${PLATFORM_URL}/api/mcp/db/query`
 * via the exact `platformQuery(sql, params, principal)` pattern
 * `register_p1_synthesis.ts` uses — two-layer auth (X-MCP-Internal-Token +
 * X-MCP-User/X-MCP-Key-Id) and table-level whitelisting on the platform side.
 * `kala_gochara_windows` and `brahma_remedy_corpus` were added to that route's
 * ALLOWED_TABLES read-only whitelist. No `pg` dependency, no DATABASE_URL, no
 * infra change to amjis-mcp — the fix conforms the tool to the platform's
 * established DB-access contract rather than bolting DB creds onto a publicly-
 * invokable serving process.
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
 *
 * SATYA-ŚEṢA W2/W3 (2026-07-25 — S4-05 fix, UAT-DARPANA worst veto): this
 * sweep has NO health event class (only career_advancement/marriage/major_gain
 * are populated for the canonical chart today). Before this change, a
 * health-filtered/health-adjacent query against these three tools got a bare
 * "clean" empty that read identically to a genuinely-swept, genuinely-clear
 * result — "I didn't look" served as "there is nothing" (the exact failure
 * mode SATYA_SHESHA_BRIEF_v1_0.md §0 names). Two additions close it:
 *   W2 — every response now carries `coverage` (mechanically derived every
 *        call from gochara_resonance_map ∩ brahma_event_ontology — see
 *        `computeGocharaCoverage` below — never hand-maintained), and a
 *        `domain` filter that, when it names a domain outside the covered
 *        set, short-circuits to a `not_covered` refusal (cross-pointing to
 *        `kala_windows_get`, the domain-capable instrument) INSTEAD of
 *        running a scan that can only look empty.
 *   W3 — `active_sentences` (the true size driver — up to 11.5KB/row observed
 *        live, dwarfing every other field) is capped at construction time
 *        (`capActiveSentences`, disclosed via `active_sentences_total_count`),
 *        and the full response (windows + coverage + provenance_envelope +
 *        drill_pointers) is now measured and trimmed as ONE object via
 *        `finalizeMcpBudget` — the previous `applyResponseBudget` call only
 *        ever measured `{windows}` in isolation, so a response could report
 *        "trimmed to budget" while the actually-served envelope (windows +
 *        trim_report + provenance_envelope stapled on afterward, unmeasured)
 *        was still far over it (114KB observed live for a 10-row "floored"
 *        forecast response against a nominal 40KB ceiling).
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import { remoteAuthorize } from '../../lib/authz.js'
import { finalizeMcpBudget, type TrimmableSection } from '../../lib/response_budget.js'

// ── Platform DB proxy (see module DB ACCESS NOTE) ────────────────────────────
// The MCP server holds no direct DB connection; it proxies SELECT-only,
// server-authored SQL through the platform's whitelisted /api/mcp/db/query
// route, which owns the live PG connection. Same helper shape as
// register_p1_synthesis.ts's `platformQuery`.

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function platformQuery(
  sql: string,
  params: unknown[],
  principal: Principal
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[gochara_windows] platform DB query failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
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
  // W3: present once `capActiveSentences` has run; absent (undefined) means
  // the row's active_sentences array is already whole (never fabricated).
  active_sentences_total_count?: number
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

// W3 (SATYA-ŚEṢA, root-cause size fix): `active_sentences` is the dominant
// byte cost of a GocharaWindowRow by a wide margin — a single row's array
// measured 11.5KB serialized (30 entries, each carrying a full classical_
// citation string) against ~1.4KB for every OTHER field on the row combined.
// The prior budget mechanism only ever trimmed the ROW COUNT (`windows`
// array length); with 10 rows hardFloor-protected at that minKeep, 10 ×
// 11.5KB alone (114KB) blew straight through a 40KB ceiling with no lever
// left to pull. This caps the array at construction time — before any
// row-count budget trim runs — to the N most classically-load-bearing
// entries (cited over uncited: `uncited_extension === false` sentences,
// which are the two-pass-verifiable claims per DR-16-family discipline
// elsewhere in this file, are kept first). The true count is disclosed via
// `active_sentences_total_count`, never silently hidden (B.10) — the
// dropped entries are NOT independently recoverable via a drill instrument
// today (this table has no per-sentence lookup surface), which this
// function's caller states honestly rather than promising a recovery path
// that does not exist.
const ACTIVE_SENTENCES_CAP = 4

function capActiveSentences(rows: GocharaWindowRow[]): GocharaWindowRow[] {
  return rows.map((row) => {
    const all = row.active_sentences ?? []
    if (all.length <= ACTIVE_SENTENCES_CAP) return row
    const cited = all.filter((s) => (s as Record<string, unknown>)['uncited_extension'] === false)
    const uncited = all.filter((s) => (s as Record<string, unknown>)['uncited_extension'] !== false)
    const kept = [...cited, ...uncited].slice(0, ACTIVE_SENTENCES_CAP)
    return { ...row, active_sentences: kept, active_sentences_total_count: all.length }
  })
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

async function queryRows(
  sql: string,
  params: unknown[],
  principal: Principal
): Promise<{ rows: GocharaWindowRow[]; ok: boolean; error?: string }> {
  try {
    const { rows } = await platformQuery(sql, params, principal)
    return { rows: rows as unknown as GocharaWindowRow[], ok: true }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { rows: [], ok: false, error: message }
  }
}

// ══════════════════════════════════════════════════════════════════════════
// W2 — Category-coverage attestation (SATYA-ŚEṢA, S4-05 mechanism fix)
// ══════════════════════════════════════════════════════════════════════════
//
// Distinguishes the two axes EL-60b conflated: EXECUTION coverage (how many
// of the sweep's planned substeps have committed — `sweep_completeness`
// below) vs CATEGORY coverage (which domains the sweep's event-class
// universe even includes in the first place — `event_classes_covered` /
// `domains_not_covered`). A tool can be 100% complete on the first axis and
// structurally silent on the second; both used to read as "clean". Every
// value here is a live query result, never a hand-maintained literal —
// re-run this and the answer changes the moment G-1's resonance map (or the
// domain ontology) does, with no code change required.

export interface GocharaCoverage {
  event_classes_covered: string[]
  domains_not_covered: string[]
  universe_source: string
  sweep_completeness: {
    substeps_committed: number
    source: string
    note: string
  }
}

export interface GocharaNotCovered {
  domain: string
  cross_pointer: { instrument: string; hint: string }
}

const COVERAGE_UNIVERSE_SOURCE =
  'event_classes_covered = DISTINCT gochara_resonance_map.event_class for this chart_id (G-1\'s own ' +
  'record of which event classes the D-5 sweep populated targets for, and therefore substepped over — ' +
  'the writer\'s docstring: "one substep per populated gochara_resonance_map event_class x decade" — ' +
  'more precise than kala_gochara_windows itself, which can under-report a class that was swept but ' +
  'produced zero rows), resolved to brahma_event_ontology.domain; domains_not_covered = DISTINCT ' +
  'brahma_event_ontology.domain minus that covered set. Mechanically derived fresh every call from ' +
  'live table state — never hand-maintained.'

/** Chart-scoped: which event classes did THIS chart's sweep actually look at, which domains does
 *  that leave structurally dark, and how much of the sweep's own execution has committed. Never
 *  throws — a query failure degrades to an honestly-empty coverage object with `ok: false` so the
 *  caller can distinguish "we checked and it's genuinely uncovered" from "coverage itself could
 *  not be computed this call" rather than silently presenting the former when it is really the
 *  latter. */
export async function computeGocharaCoverage(
  chartId: string,
  principal: Principal
): Promise<{ coverage: GocharaCoverage; ok: boolean }> {
  const [classesResp, universeResp, substepResp] = await Promise.all([
    platformQuery(
      `SELECT DISTINCT rm.event_class AS event_class, eo.domain AS domain
         FROM gochara_resonance_map rm
         LEFT JOIN brahma_event_ontology eo ON eo.event_class_id = rm.event_class
        WHERE rm.chart_id = $1
        ORDER BY 1`,
      [chartId],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const })).catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
    platformQuery(
      `SELECT DISTINCT domain FROM brahma_event_ontology WHERE domain IS NOT NULL ORDER BY 1`,
      [],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const })).catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
    platformQuery(
      `SELECT COUNT(*)::int AS substeps_committed FROM build_substep_progress WHERE chart_id = $1 AND asset_id = 'ka_gochara_sweep'`,
      [chartId],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const })).catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
  ])

  const eventClasses = [...new Set(classesResp.rows.map((r) => r['event_class']).filter((v): v is string => typeof v === 'string'))].sort()
  const coveredDomains = new Set(classesResp.rows.map((r) => r['domain']).filter((d): d is string => typeof d === 'string'))
  const universeDomains = universeResp.rows.map((r) => r['domain']).filter((d): d is string => typeof d === 'string').sort()
  const domainsNotCovered = universeDomains.filter((d) => !coveredDomains.has(d))
  const substepsCommitted = Number(substepResp.rows[0]?.['substeps_committed'] ?? 0)

  const ok = classesResp.ok && universeResp.ok && substepResp.ok

  return {
    ok,
    coverage: {
      event_classes_covered: eventClasses,
      domains_not_covered: domainsNotCovered,
      universe_source: COVERAGE_UNIVERSE_SOURCE,
      sweep_completeness: {
        substeps_committed: substepsCommitted,
        source: 'build_substep_progress (asset_id=ka_gochara_sweep, chart-scoped)',
        note:
          'Execution completeness ONLY — how many sweep substeps have committed for THIS chart. ' +
          'NOT the same axis as the category coverage above (which domains the sweep can ever ' +
          'surface at all, per event_classes_covered/domains_not_covered) — a fully-executed sweep ' +
          '(every substep committed) still structurally excludes any domain in domains_not_covered. ' +
          'No total-planned-substep denominator is reported here: that figure is not independently ' +
          'queryable post-build without re-deriving the writer\'s own planning logic, and this field ' +
          'will not fabricate one.',
      },
    },
  }
}

const KALA_WINDOWS_CROSS_POINTER_INSTRUMENT = 'kala_windows_get'

/** W2 server-side refusal rule: when a caller's `domain` filter names a domain this sweep's
 *  event-class universe does not cover, return the refusal shape instead of running a scan that
 *  can only ever come back empty for that domain — the response must never present that empty as
 *  a completed, domain-covering scan result (SATYA_SHESHA_BRIEF_v1_0.md §2 W2). Returns null when
 *  no domain filter was supplied, or the requested domain IS covered (normal path proceeds). */
function notCoveredFor(domain: string | undefined, coverage: GocharaCoverage): GocharaNotCovered | null {
  if (!domain) return null
  if (!coverage.domains_not_covered.includes(domain)) return null
  return {
    domain,
    cross_pointer: {
      instrument: KALA_WINDOWS_CROSS_POINTER_INSTRUMENT,
      hint:
        `${KALA_WINDOWS_CROSS_POINTER_INSTRUMENT}(chart_id, domain="${domain}") serves L3 Kāla ` +
        'temporal-activation windows for this domain — the gochara sweep\'s event-class universe ' +
        '(see coverage.event_classes_covered) does not include it for this chart. This response is ' +
        'a refusal, not a completed scan of that domain: do not read the empty `windows` array below ' +
        'as "no adverse window found" for it.',
    },
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
  max_digest_bytes: 40_000,
  paginated: true,
  facets: ['event_class', 'temporal_shape', 'valence', 'is_adverse'],
  empty_reason: true,
} as const

const ELECTION_AVOIDANCE_DENSITY_CONTRACT = {
  max_digest_bytes: 50_000,
  paginated: true,
  facets: ['event_class', 'temporal_shape'],
  empty_reason: true,
} as const

// ── SATYA-ŚEṢA W3 — declared response-budget ceilings for this family ───────
// Source-text-parsed by platform/scripts/census/elev_gates/_tool_enumeration.ts
// the same way registry_bridge.ts's MCP_RESPONSE_BUDGET_KB ledger is parsed for
// every tool registered there — kept HERE (not in registry_bridge.ts) because
// these three tools are not registered via that file's server.tool() call
// sites; each has its own file-local budget wiring (finalizeMcpBudget calls
// below). This constant is the single declared-ceiling SOURCE OF TRUTH the CI
// gate reads; keep it in sync BY HAND with the `maxKb` literals passed to
// finalizeMcpBudget in each compute* function below — the same discipline the
// MCP_RESPONSE_BUDGET_KB/call-site pairing in registry_bridge.ts already
// requires of every tool registered there.
export const GOCHARA_RESPONSE_BUDGET_KB = {
  gochara_activation_get: 20,
  gochara_forecast_get: 40,
  gochara_election_avoidance_get: 50,
} as const

// ── Response-budget sections (§N.6 hardFloor — see response_budget.ts) ──────
// Every row in `kala_gochara_windows` is a materialized, real-intensity
// computed window (no catalog-only/label-match rows exist in this table's
// design — G-3's PROMISE is an honest 0.0, never served, when a chart/
// event_class has no G-1 targets). The `windows` array is therefore this
// tool's single densest/most-authoritative section and is hardFloor-protected
// so a budget trim never zeroes it — `capActiveSentences` above is what keeps
// per-row detail from dominating the budget instead, run BEFORE this section
// is ever measured.
//
// `coverage` (W2) is deliberately NOT declared as a trimmable section here —
// response_budget.ts's own `IMMUNE_HONESTY_FIELDS` set already names
// `coverage` as a frozen-immune honesty field (never auto-detected as
// trimmable, never string-truncated by the last-resort walk), and this file's
// explicit-sections design means it is simply never handed to the trimmer at
// all — the strongest possible guarantee (nothing to override) rather than a
// declared floor that PASS 2 could in principle still touch.

// Non-generic over Record<string, unknown> (not the narrow {windows: GocharaWindowRow[]}
// shape the original applyResponseBudget-only version used) — the content object each
// compute* function now hands to finalizeMcpBudget also carries coverage/drill_pointers/
// provenance_envelope, so it is typed Record<string, unknown> throughout; this matches
// FinalizeMcpBudgetOptions<T>.sections: TrimmableSection<T>[] for that same T.
function windowsSection(
  toolName: string,
  minKeep: number
): TrimmableSection<Record<string, unknown>>[] {
  return [
    {
      path: 'windows',
      getArray: (c) => (Array.isArray(c['windows']) ? (c['windows'] as unknown[]) : undefined),
      setArray: (c, kept) => {
        c['windows'] = kept
      },
      minKeep,
      hardFloor: true,
      recover: { instrument: toolName, hint: 'narrow date_range or event_class to page through the full result' },
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
  domain: z
    .string()
    .optional()
    .describe(
      'Filter to event classes in this life domain (e.g. "health", "career"). If this sweep does ' +
        'not cover the domain for this chart, the response returns a `not_covered` refusal naming ' +
        'the capable instrument (kala_windows_get) instead of a misleading empty scan.'
    ),
})

export async function computeGocharaActivation(
  chartId: string,
  asOfDate: string,
  principal: Principal,
  eventClass?: string,
  domain?: string
): Promise<Record<string, unknown>> {
  const { coverage, ok: coverageOk } = await computeGocharaCoverage(chartId, principal)
  const notCovered = notCoveredFor(domain, coverage)

  const baseEnvelope = {
    source: 'gochara_activation_get',
    source_citation: SOURCE_CITATION,
    chart_id: chartId,
    as_of_date: asOfDate,
    event_class_filter: eventClass ?? null,
    domain_filter: domain ?? null,
    computed_at: new Date().toISOString(),
    density_contract: ACTIVATION_DENSITY_CONTRACT,
  }

  if (notCovered) {
    return {
      windows: [],
      not_covered: notCovered,
      coverage,
      drill_pointers: [notCovered.cross_pointer],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  const params: unknown[] = [chartId, asOfDate]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND window_start <= $2 AND window_end >= $2`
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  if (domain) {
    params.push(domain)
    sql += ` AND EXISTS (SELECT 1 FROM brahma_event_ontology eo WHERE eo.event_class_id = kala_gochara_windows.event_class AND eo.domain = $${params.length})`
  }
  sql += ' ORDER BY signed_intensity DESC'

  const { rows: rawRows, ok, error } = await queryRows(sql, params, principal)
  const rows = capActiveSentences(withPlateauDisclosure(rawRows))

  const content: Record<string, unknown> = {
    windows: rows,
    coverage,
    drill_pointers: [] as unknown[],
    provenance_envelope: {
      ...baseEnvelope,
      window_count: rows.length,
      backing_data_reachable: ok && coverageOk,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no kala_gochara_windows row spans this date for this chart/event_class/domain filter — an honest zero-activation result, not a fabricated one'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
    },
  }

  return finalizeMcpBudget(content, {
    maxKb: GOCHARA_RESPONSE_BUDGET_KB.gochara_activation_get,
    sections: windowsSection('gochara_activation_get', 5),
  })
}

export function registerGocharaActivationTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_activation_get',
    'What it does: Returns kala_gochara_windows rows ACTIVE on a given date (default today) ' +
      'for a chart — "is this event_class configuration firing right now?" One of three views ' +
      '(activation / forecast / election_avoidance) over the D-5 G-4 signed intensity field. ' +
      'Shape-aware: point rows are single-day matches, interval rows match when the date falls ' +
      'inside the span, chain rows are per-milestone (each its own single-day match).\n\n' +
      'Output: { windows: [...], coverage: {...}, provenance_envelope: {...} }. Every response ' +
      'carries `coverage` (event_classes_covered / domains_not_covered / sweep_completeness), ' +
      'mechanically derived per call — this sweep does NOT cover every life domain (e.g. it may ' +
      'have no health event class for this chart); a `domain` filter naming an uncovered domain ' +
      'returns a `not_covered` refusal (with a cross_pointer to kala_windows_get) instead of a ' +
      'misleading empty. An honest empty `windows` array is distinguished from an unreachable ' +
      'table via provenance_envelope.empty_reason — never silently substituted.\n\n' +
      'Requires: chart_id (UUID).',
    ActivationInputSchema.shape,
    async (params) => {
      const input = ActivationInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      const asOf = input.as_of_date ?? new Date().toISOString().slice(0, 10)
      try {
        const result = await computeGocharaActivation(input.chart_id, asOf, principal, input.event_class, input.domain)
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
  domain: z
    .string()
    .optional()
    .describe(
      'Filter to event classes in this life domain (e.g. "health", "career"). If this sweep does ' +
        'not cover the domain for this chart, the response returns a `not_covered` refusal naming ' +
        'the capable instrument (kala_windows_get) instead of a misleading empty scan — this is the ' +
        'S4-05 fix: "is there a rough patch coming for my health?" must never read this tool\'s ' +
        'silence on health as an all-clear.'
    ),
  limit: z.number().int().min(1).max(500).default(100),
})

export async function computeGocharaForecast(
  chartId: string,
  dateRange: { start: string; end: string },
  eventClass: string | undefined,
  valence: string | undefined,
  limit: number,
  principal: Principal,
  domain?: string
): Promise<Record<string, unknown>> {
  const { coverage, ok: coverageOk } = await computeGocharaCoverage(chartId, principal)
  const notCovered = notCoveredFor(domain, coverage)

  const baseEnvelope = {
    source: 'gochara_forecast_get',
    source_citation: SOURCE_CITATION,
    chart_id: chartId,
    date_range: dateRange,
    event_class_filter: eventClass ?? null,
    valence_filter: valence ?? null,
    domain_filter: domain ?? null,
    computed_at: new Date().toISOString(),
    density_contract: FORECAST_DENSITY_CONTRACT,
  }

  if (notCovered) {
    return {
      windows: [],
      not_covered: notCovered,
      coverage,
      drill_pointers: [notCovered.cross_pointer],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        shape_breakdown: {},
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

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
  if (domain) {
    params.push(domain)
    sql += ` AND EXISTS (SELECT 1 FROM brahma_event_ontology eo WHERE eo.event_class_id = kala_gochara_windows.event_class AND eo.domain = $${params.length})`
  }
  params.push(limit)
  sql += ` ORDER BY window_start ASC, signed_intensity DESC LIMIT $${params.length}`

  const { rows: rawRows, ok, error } = await queryRows(sql, params, principal)
  const rows = capActiveSentences(withPlateauDisclosure(rawRows))

  const byShape = { point: 0, interval: 0, chain: 0 } as Record<string, number>
  for (const r of rawRows) byShape[r.temporal_shape] = (byShape[r.temporal_shape] ?? 0) + 1

  const content: Record<string, unknown> = {
    windows: rows,
    coverage,
    drill_pointers: [] as unknown[],
    provenance_envelope: {
      ...baseEnvelope,
      window_count: rawRows.length,
      shape_breakdown: byShape,
      backing_data_reachable: ok && coverageOk,
      empty_reason: rawRows.length === 0
        ? (ok
            ? 'no kala_gochara_windows rows overlap this date_range/filter combination — honest zero result. ' +
              'Note: G-4 has only materialized rows for chart-relative decades that have actually been swept ' +
              '(see coverage.sweep_completeness) — an empty result for an unswept decade is a coverage gap, not ' +
              'a negative signal; check kala_gochara_windows build coverage before reading this as "nothing happens".'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
    },
  }

  return finalizeMcpBudget(content, {
    maxKb: GOCHARA_RESPONSE_BUDGET_KB.gochara_forecast_get,
    sections: windowsSection('gochara_forecast_get', 10),
  })
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
      'CATEGORY COVERAGE (S4-05 fix): this sweep does not necessarily cover every life domain — ' +
      'every response carries `coverage.event_classes_covered` / `coverage.domains_not_covered`, ' +
      'mechanically derived per call. A silent/empty result for a domain NOT in event_classes_covered ' +
      'is NOT a clearance for that domain (e.g. "no adverse window" here says nothing about health if ' +
      'health is absent from coverage) — pass `domain` to get an explicit `not_covered` refusal with a ' +
      'cross_pointer to the capable instrument (kala_windows_get) instead of relying on silence.\n\n' +
      'Output: { windows: [...], coverage: {...}, provenance_envelope: { shape_breakdown, empty_reason, ... } }.\n\n' +
      'Requires: chart_id (UUID), date_range {start, end}.',
    ForecastInputSchema.shape,
    async (params) => {
      const input = ForecastInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      try {
        const result = await computeGocharaForecast(
          input.chart_id,
          input.date_range,
          input.event_class,
          input.valence,
          input.limit,
          principal,
          input.domain
        )
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
  domain: z
    .string()
    .optional()
    .describe(
      'Filter to event classes in this life domain (e.g. "health", "career"). If this sweep does ' +
        'not cover the domain for this chart, the response returns a `not_covered` refusal naming ' +
        'the capable instrument (kala_windows_get) instead of a misleading empty scan.'
    ),
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

async function fetchMitigation(planet: string | null, principal: Principal): Promise<Record<string, unknown> | null> {
  if (!planet) return null
  const { rows } = await queryRows(
    `SELECT remedy_id, planet, domain, remedy_type, prescription_text, mantra_text, gemstone,
            charity_action, source_citation, classical_ref, confidence
       FROM brahma_remedy_corpus WHERE planet = $1 ORDER BY confidence DESC LIMIT 1`,
    [planet],
    principal
  ) as unknown as { rows: Record<string, unknown>[] }
  return rows[0] ?? null
}

export async function computeGocharaElectionAvoidance(
  chartId: string,
  dateRange: { start: string; end: string },
  eventClass: string | undefined,
  limit: number,
  principal: Principal,
  domain?: string
): Promise<Record<string, unknown>> {
  const { coverage, ok: coverageOk } = await computeGocharaCoverage(chartId, principal)
  const notCovered = notCoveredFor(domain, coverage)

  const baseEnvelope = {
    source: 'gochara_election_avoidance_get',
    source_citation: SOURCE_CITATION,
    chart_id: chartId,
    date_range: dateRange,
    event_class_filter: eventClass ?? null,
    domain_filter: domain ?? null,
    computed_at: new Date().toISOString(),
    dr16_properties: ['honest_clarity', 'probabilistic_never_fatalistic', 'falsifier_bearing', 'mitigation_paired', 'confidence_honest'],
    density_contract: ELECTION_AVOIDANCE_DENSITY_CONTRACT,
  }

  if (notCovered) {
    return {
      windows: [],
      not_covered: notCovered,
      coverage,
      drill_pointers: [notCovered.cross_pointer],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  const params: unknown[] = [chartId, dateRange.end, dateRange.start]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND is_adverse = true AND window_start <= $2 AND window_end >= $3`
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  if (domain) {
    params.push(domain)
    sql += ` AND EXISTS (SELECT 1 FROM brahma_event_ontology eo WHERE eo.event_class_id = kala_gochara_windows.event_class AND eo.domain = $${params.length})`
  }
  params.push(limit)
  sql += ` ORDER BY signed_intensity ASC LIMIT $${params.length}`  // most-negative first

  const { rows, ok, error } = await queryRows(sql, params, principal)

  const avoidWindows = await Promise.all(
    rows.map(async (row) => {
      const planet = dominantGraha(row)
      const mitigation = await fetchMitigation(planet, principal)
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

  const content: Record<string, unknown> = {
    windows: avoidWindows,
    coverage,
    drill_pointers: [] as unknown[],
    provenance_envelope: {
      ...baseEnvelope,
      window_count: rows.length,
      backing_data_reachable: ok && coverageOk,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no adverse (is_adverse=true) kala_gochara_windows rows overlap this date_range/filter -- ' +
              'an honestly clean window, not a fabricated all-clear (verify coverage.sweep_completeness ' +
              'for this range)'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
    },
  }

  return finalizeMcpBudget(content, {
    maxKb: GOCHARA_RESPONSE_BUDGET_KB.gochara_election_avoidance_get,
    sections: windowsSection('gochara_election_avoidance_get', 5),
  })
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
      'CATEGORY COVERAGE (S4-05 fix): every response carries `coverage` (mechanically derived); a ' +
      '`domain` filter naming a domain outside coverage.event_classes_covered/domains returns a ' +
      '`not_covered` refusal (cross-pointing to kala_windows_get) instead of a misleading empty.\n\n' +
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
        const result = await computeGocharaElectionAvoidance(
          input.chart_id,
          input.date_range,
          input.event_class,
          input.limit,
          principal,
          input.domain
        )
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
