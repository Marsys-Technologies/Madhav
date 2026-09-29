/**
 * retrieval/register_gochara_contact_ledger.ts — WP7 P-4 contact-ledger +
 * coverage read capability (density-layered, hardFloor on confirmed).
 *
 * New read capability over `kala_gochara_contacts` + `kala_gochara_coverage`
 * (the two WP6 relations, migration 1081; shapes pinned in WP1_CONTRACTS.md
 * §3.1/§4.1). This is the interface future readers (S-2's Saṅgam path, the
 * reading checklist, MCP drill tools) opt into. It is §N.6-shaped from the
 * start: confirmed episodes are NEVER flattened with catalog-only rows, and a
 * budget trim never sacrifices the confirmed floor — if the confirmed set
 * exceeds the transport budget the tool returns `not_computed` +
 * `floor_overflow:true`, an honest refusal, not a silent tail cut (H-5).
 *
 * Layering rules (normative, from PACKET_P4 §3):
 *   1. `hard_floor.confirmed` and `context_layer.catalog_only` are disjoint BY
 *      CONSTRUCTION — the query filters (confirmed predicate in SQL), the
 *      caller never re-separates.
 *   2. `hard_floor` is trim-proof: budget pressure trims `context_layer` and
 *      the page size, never the confirmed floor.
 *   3. `coverage.searched_horizon` is exposed per request; a `moon_on_demand`
 *      partition's requested/completed horizons are quoted exactly (H-3) with
 *      `unsearched_reason` present when completion fell short.
 *   4. `status='unpublished'` is served as a FULL coverage object (empty
 *      partitions + manifest null + note), never as an error and never as 'v1'
 *      (N-10: explicit kala_gochara_authority read, no COALESCE default).
 *
 * Moon (R7): Moon contacts are not persisted by default. `moon='on_demand'`
 * here serves the `moon_on_demand` COVERAGE record for the requested interval
 * (so L3-Q08 — "what was actually searched" — is answerable for Moon classes)
 * and any persisted moon episodes (none by default). LIVE Moon derivation is
 * S-1's `find_episodes` (python-sidecar, separate packet) — this tool does not
 * re-scan an ephemeris; when S-1 lands, callers wanting live Moon episodes
 * route there. This tool says so in `coverage.searched_horizon`'s companion
 * note rather than fabricating a 0-contact answer.
 *
 * DB ACCESS: same contract as register_gochara_windows.ts — no direct DB
 * connection; SELECT-only server-authored SQL proxied through the platform's
 * whitelisted /api/mcp/db/query route. `kala_gochara_contacts` was added to
 * that route's ALLOWED_TABLES by this packet (dated comment there); coverage +
 * publication were whitelisted by P-1.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import { remoteAuthorize } from '../../lib/authz.js'

// ── Platform DB proxy (identical contract to register_gochara_windows.ts) ────

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
    throw new Error(`[gochara_contact_ledger] platform DB query failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

// ── Served shapes (PACKET_P4 §2–§3, verbatim field names) ────────────────────

export interface ContactEpisode {
  contact_id: string
  independence_group: string
  body: string
  relation: string
  aspect_deg: number | null
  target_type: string
  target_ref: string
  target_resolution_state: string
  t_in: string
  t_exact: string
  t_out: string
  branch: string
  orb_max_deg: number
  completeness_state: string
  epistemic_class: string
  operator_role: string
  claim_grain: string
  comparable_with: string
  convention_id: string
  classical_citation: string | null
  uncited_extension: boolean
  truncated_at_horizon: 'start' | 'end' | null
}

export interface CoveragePartition {
  partition_kind: string
  partition_key: string
  requested_horizon: string
  completed_horizon: string
  resolution: number | null
  relations_searched: string[]
  targets_requested: number
  targets_resolved: number
  targets_unresolved: number
  target_resolution_state_counts: Record<string, number>
  unavailable_inputs: Record<string, unknown>
  unsearched_reason: string | null
}

export interface ContactLedgerResult {
  status: 'ok' | 'unpublished' | 'not_computed'
  floor_overflow?: boolean
  generation: string | null
  manifest: {
    manifest_id: string
    convention_id: string
    content_digest: string
    status: string
  } | null
  hard_floor: {
    confirmed: ContactEpisode[]
    count: number
  }
  context_layer?: {
    catalog_only: ContactEpisode[]
    unqualified_count: number
    note: string
  }
  coverage: {
    partitions: CoveragePartition[]
    searched_horizon: string | null
    unavailable_inputs: Record<string, unknown>
    note?: string
  }
  page: { returned: number; next_cursor: string | null; confirmed_returned: number }
}

// F06 confirmed set — same ambiguity resolution as P-2
// (reading_checklist.ts): the writer vocab (gochara_kernel/episodes.py,
// gochara_v3/interval_solver.py) uses 'qualified'; the packet fixtures use
// 'confirmed'. Both count; 'unqualified'/'unavailable'/'unexplored' never do.
const CONFIRMED_COMPLETENESS_STATES = new Set(['confirmed', 'qualified'])

// Transport budget for the confirmed floor. The floor is trim-proof: a
// confirmed set larger than this is served as not_computed + floor_overflow,
// never tail-cut (H-5 / §N.6: trim at serve time, never truncate as absence).
const CONFIRMED_FLOOR_BUDGET = 200

// ── SQL ──────────────────────────────────────────────────────────────────────

// The confirmed predicate lives IN THE QUERY (layering rule 1: layers disjoint
// by construction). Columns mirror ContactEpisode one-for-one.
const EPISODE_COLUMNS = `
  contact_id, independence_group, body, relation, aspect_deg,
  target_type, target_ref, target_resolution_state,
  t_in, t_exact, t_out, branch, orb_max_deg, completeness_state,
  epistemic_class, operator_role, claim_grain, comparable_with,
  convention_id, classical_citation, uncited_extension, truncated_at_horizon`

const CONFIRMED_PREDICATE = `completeness_state IN ('confirmed', 'qualified') AND target_resolution_state = 'resolved'`

interface PartitionFilter {
  body?: string
  target_type?: string
  target_ref?: string
  relation?: string
  event_class?: string
  interval?: [string, string]
}

function buildFilterClauses(
  filter: PartitionFilter | undefined,
  params: unknown[],
  startIndex: number
): { clauses: string[]; nextIndex: number } {
  const clauses: string[] = []
  let i = startIndex
  if (filter?.body) {
    params.push(filter.body)
    clauses.push(`body = $${i++}`)
  }
  if (filter?.target_type) {
    params.push(filter.target_type)
    clauses.push(`target_type = $${i++}`)
  }
  if (filter?.target_ref) {
    params.push(filter.target_ref)
    clauses.push(`target_ref = $${i++}`)
  }
  if (filter?.relation) {
    params.push(filter.relation)
    clauses.push(`relation = $${i++}`)
  }
  if (filter?.interval) {
    params.push(filter.interval[0], filter.interval[1])
    clauses.push(`t_in <= $${i++}::timestamptz AND t_out >= $${i++}::timestamptz`)
  }
  return { clauses, nextIndex: i }
}

function rowToEpisode(r: Record<string, unknown>): ContactEpisode {
  return {
    contact_id: r['contact_id'] as string,
    independence_group: r['independence_group'] as string,
    body: r['body'] as string,
    relation: r['relation'] as string,
    aspect_deg: r['aspect_deg'] == null ? null : Number(r['aspect_deg']),
    target_type: r['target_type'] as string,
    target_ref: r['target_ref'] as string,
    target_resolution_state: r['target_resolution_state'] as string,
    t_in: String(r['t_in']),
    t_exact: String(r['t_exact']),
    t_out: String(r['t_out']),
    branch: r['branch'] as string,
    orb_max_deg: Number(r['orb_max_deg']),
    completeness_state: r['completeness_state'] as string,
    epistemic_class: r['epistemic_class'] as string,
    operator_role: r['operator_role'] as string,
    claim_grain: r['claim_grain'] as string,
    comparable_with: r['comparable_with'] as string,
    convention_id: r['convention_id'] as string,
    classical_citation: (r['classical_citation'] as string | null) ?? null,
    uncited_extension: Boolean(r['uncited_extension']),
    truncated_at_horizon: (r['truncated_at_horizon'] as 'start' | 'end' | null) ?? null,
  }
}

function rowToCoveragePartition(r: Record<string, unknown>): CoveragePartition {
  return {
    partition_kind: r['partition_kind'] as string,
    partition_key: r['partition_key'] as string,
    requested_horizon: String(r['requested_horizon']),
    completed_horizon: String(r['completed_horizon']),
    resolution: r['resolution'] == null ? null : Number(r['resolution']),
    relations_searched: (r['relations_searched'] as string[]) ?? [],
    targets_requested: Number(r['targets_requested'] ?? 0),
    targets_resolved: Number(r['targets_resolved'] ?? 0),
    targets_unresolved: Number(r['targets_unresolved'] ?? 0),
    target_resolution_state_counts: (r['target_resolution_state_counts'] as Record<string, number>) ?? {},
    unavailable_inputs: (r['unavailable_inputs'] as Record<string, unknown>) ?? {},
    unsearched_reason: (r['unsearched_reason'] as string | null) ?? null,
  }
}

// ── The capability core (exported for tests + future non-MCP callers) ────────

export interface ContactLedgerQueryInput {
  chart_id: string
  generation?: string
  partition?: PartitionFilter
  horizon?: { start: string; end: string }
  moon?: 'on_demand'
  include_context?: boolean
  page?: { limit: number; cursor?: string }
}

export async function queryContactLedger(
  input: ContactLedgerQueryInput,
  principal: Principal
): Promise<ContactLedgerResult> {
  // Generation: explicit kala_gochara_authority read unless the caller pinned
  // one. ABSENT row = unpublished full coverage object — never a 'v1' default
  // (N-10), never an error (layering rule 4).
  let generation = input.generation ?? null
  if (!generation) {
    const { rows } = await platformQuery(
      `SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = $1::uuid`,
      [input.chart_id],
      principal
    )
    generation = (rows[0]?.['authoritative_generation'] as string | undefined) ?? null
  }

  if (!generation) {
    return {
      status: 'unpublished',
      generation: null,
      manifest: null,
      hard_floor: { confirmed: [], count: 0 },
      coverage: {
        partitions: [],
        searched_horizon: null,
        unavailable_inputs: {},
        note:
          'unpublished — no kala_gochara_authority row for this chart (N-10). ' +
          'Nothing authoritative is served; this is a full coverage object, ' +
          'never an error and never a v1 default.',
      },
      page: { returned: 0, next_cursor: null, confirmed_returned: 0 },
    }
  }

  // Manifest (null for legacy generations — the publication ledger only
  // carries '4.x' rows; a lookup miss is manifest-null, not an error).
  const { rows: manifestRows } = await platformQuery(
    `SELECT manifest_id, convention_id, content_digest, status
       FROM kala_gochara_publication
      WHERE chart_id = $1::uuid AND generation = $2`,
    [input.chart_id, generation],
    principal
  )
  const manifest = manifestRows[0]
    ? {
        manifest_id: String(manifestRows[0]['manifest_id']),
        convention_id: String(manifestRows[0]['convention_id']),
        content_digest: String(manifestRows[0]['content_digest']),
        status: String(manifestRows[0]['status']),
      }
    : null

  const limit = Math.min(Math.max(input.page?.limit ?? 50, 1), CONFIRMED_FLOOR_BUDGET)

  // ── Confirmed floor: true count first (independent of page), then the page.
  const countParams: unknown[] = [input.chart_id, generation]
  const countFilter = buildFilterClauses(input.partition, countParams, 3)
  const { rows: countRows } = await platformQuery(
    `SELECT COUNT(*)::text AS n FROM kala_gochara_contacts
      WHERE chart_id = $1::uuid AND generation = $2 AND ${CONFIRMED_PREDICATE}` +
      (countFilter.clauses.length ? ` AND ${countFilter.clauses.join(' AND ')}` : ''),
    countParams,
    principal
  )
  const confirmedCount = Number(countRows[0]?.['n'] ?? 0)

  // Layering rule 2: the floor is trim-proof. If the confirmed set exceeds the
  // transport budget (the caller's page limit, itself capped at
  // CONFIRMED_FLOOR_BUDGET), refuse honestly — never a truncated confirmed list.
  if (confirmedCount > limit) {
    return {
      status: 'not_computed',
      floor_overflow: true,
      generation,
      manifest,
      hard_floor: { confirmed: [], count: confirmedCount },
      coverage: { partitions: [], searched_horizon: null, unavailable_inputs: {} },
      page: { returned: 0, next_cursor: null, confirmed_returned: 0 },
    }
  }

  // Keyset pagination: cursor = "<t_exact ISO>|<contact_id>" (PACKET_P4 §2).
  const pageParams: unknown[] = [input.chart_id, generation]
  const pageFilter = buildFilterClauses(input.partition, pageParams, 3)
  const clauses = [`chart_id = $1::uuid`, `generation = $2`, CONFIRMED_PREDICATE, ...pageFilter.clauses]
  let idx = pageFilter.nextIndex
  if (input.page?.cursor) {
    const sep = input.page.cursor.indexOf('|')
    if (sep > 0) {
      const cursorT = input.page.cursor.slice(0, sep)
      const cursorId = input.page.cursor.slice(sep + 1)
      pageParams.push(cursorT, cursorId)
      clauses.push(`(t_exact, contact_id) > ($${idx++}::timestamptz, $${idx++})`)
    }
  }
  pageParams.push(limit + 1) // one extra row to detect the next page
  const { rows: confirmedRows } = await platformQuery(
    `SELECT ${EPISODE_COLUMNS} FROM kala_gochara_contacts
      WHERE ${clauses.join(' AND ')}
      ORDER BY t_exact, contact_id
      LIMIT $${idx}`,
    pageParams,
    principal
  )
  const hasNext = confirmedRows.length > limit
  const pageRows = hasNext ? confirmedRows.slice(0, limit) : confirmedRows
  const confirmed = pageRows.map(rowToEpisode)
  const last = confirmed[confirmed.length - 1]
  const nextCursor = hasNext && last ? `${last.t_exact}|${last.contact_id}` : null

  // ── Context layer: only when asked (include_context, default false).
  let contextLayer: ContactLedgerResult['context_layer']
  if (input.include_context) {
    const ctxParams: unknown[] = [input.chart_id, generation]
    const ctxFilter = buildFilterClauses(input.partition, ctxParams, 3)
    const { rows: ctxRows } = await platformQuery(
      `SELECT ${EPISODE_COLUMNS} FROM kala_gochara_contacts
        WHERE chart_id = $1::uuid AND generation = $2 AND NOT (${CONFIRMED_PREDICATE})` +
        (ctxFilter.clauses.length ? ` AND ${ctxFilter.clauses.join(' AND ')}` : '') +
        ` ORDER BY t_exact, contact_id LIMIT ${CONFIRMED_FLOOR_BUDGET}`,
      ctxParams,
      principal
    )
    const catalogOnly = ctxRows.map(rowToEpisode)
    contextLayer = {
      catalog_only: catalogOnly,
      unqualified_count: catalogOnly.filter((e) => e.completeness_state === 'unqualified').length,
      note:
        'catalog-only rows are structural context, not timing claims (§N.6) — ' +
        'unqualified / unavailable / unresolved-target episodes served separately ' +
        'from the confirmed floor, never interleaved.',
    }
  }

  // ── Coverage: partitions for (chart, generation), optionally narrowed.
  const covParams: unknown[] = [input.chart_id, generation]
  const covClauses = ['chart_id = $1::uuid', 'generation = $2']
  let covIdx = 3
  if (input.partition?.event_class) {
    covParams.push('event_class', input.partition.event_class)
    covClauses.push(`partition_kind = $${covIdx++}`, `partition_key = $${covIdx++}`)
  }
  if (input.moon === 'on_demand') {
    covParams.push('moon_on_demand')
    covClauses.push(`partition_kind = $${covIdx++}`)
  }
  const { rows: covRows } = await platformQuery(
    `SELECT partition_kind, partition_key, requested_horizon::text, completed_horizon::text,
            resolution, relations_searched, targets_requested, targets_resolved,
            targets_unresolved, target_resolution_state_counts, unavailable_inputs,
            unsearched_reason
       FROM kala_gochara_coverage
      WHERE ${covClauses.join(' AND ')}
      ORDER BY partition_kind, partition_key`,
    covParams,
    principal
  )
  const partitions = covRows.map(rowToCoveragePartition)

  // searched_horizon (H-3): for moon_on_demand requests, the moon partition's
  // own record quoted exactly — the interval ACTUALLY searched, with
  // unsearched_reason present when completed ⊊ requested. Otherwise null.
  const moonPartition = partitions.find((p) => p.partition_kind === 'moon_on_demand')
  const unavailableInputs = partitions.reduce<Record<string, unknown>>(
    (acc, p) => ({ ...acc, ...p.unavailable_inputs }),
    {}
  )
  const coverageNote =
    input.moon === 'on_demand'
      ? moonPartition
        ? 'moon_on_demand coverage quoted exactly (H-3): requested vs completed ' +
          'horizon and unsearched_reason are the writer\'s own record. Moon episodes ' +
          'are not persisted (R7); live Moon derivation routes via S-1 find_episodes.'
        : 'no moon_on_demand coverage row exists for this (chart, generation) — the ' +
          'requested Moon interval has NOT been searched; this is stated, not served ' +
          'as a 0-contact answer (F06). Live Moon derivation routes via S-1 find_episodes.'
      : undefined

  return {
    status: 'ok',
    generation,
    manifest,
    hard_floor: { confirmed, count: confirmedCount },
    ...(contextLayer ? { context_layer: contextLayer } : {}),
    coverage: {
      partitions,
      searched_horizon:
        input.moon === 'on_demand'
          ? moonPartition
            ? moonPartition.completed_horizon
            : input.horizon
              ? `[${input.horizon.start}, ${input.horizon.end}]`
              : null
          : null,
      unavailable_inputs: unavailableInputs,
      ...(coverageNote ? { note: coverageNote } : {}),
    },
    page: {
      returned: confirmed.length + (contextLayer?.catalog_only.length ?? 0),
      next_cursor: nextCursor,
      confirmed_returned: confirmed.length,
    },
  }
}

// ── MCP tool registration ────────────────────────────────────────────────────

const ContactLedgerInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  generation: z
    .string()
    .optional()
    .describe("Pin a generation (e.g. '4.0'). Default: the chart's authoritative generation per kala_gochara_authority (explicit read; absent row = unpublished, never a 'v1' default)."),
  partition: z
    .object({
      body: z.string().optional().describe("Agent graha, e.g. 'Saturn', 'Moon'."),
      target_type: z.string().optional().describe('WP1 §5.3 target_type vocabulary.'),
      target_ref: z.string().optional(),
      relation: z.string().optional().describe('conjunction | drishti_contact | sign_ingress | nakshatra_ingress | kakshya_cell_crossing | return'),
      event_class: z.string().optional().describe('Narrows the coverage side to one event_class partition.'),
      interval: z
        .tuple([z.string(), z.string()])
        .optional()
        .describe('ISO timestamps; overlaps t_in/t_out.'),
    })
    .optional(),
  horizon: z
    .object({ start: z.string(), end: z.string() })
    .optional()
    .describe('For moon=on_demand: the searched interval (ISO dates/timestamps).'),
  moon: z
    .literal('on_demand')
    .optional()
    .describe("R7: serve the moon_on_demand coverage record for the horizon. Moon episodes are not persisted; live Moon derivation routes via S-1 find_episodes — a missing moon partition is stated, never served as a 0-contact answer."),
  include_context: z
    .boolean()
    .optional()
    .describe('Default false: context layer (catalog-only rows) omitted unless asked.'),
  page: z
    .object({
      limit: z.number().int().min(1).max(200).describe('Page size. NOTE: this is also the confirmed-floor transport budget — a confirmed set larger than the limit returns not_computed + floor_overflow, never a truncated floor (H-5).'),
      cursor: z.string().optional().describe('Keyset cursor from a previous page: "<t_exact>|<contact_id>".'),
    })
    .optional(),
})

export function registerGocharaContactLedgerTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_contact_ledger_get',
    'What it does: density-layered read over the WP6 contact ledger ' +
      '(kala_gochara_contacts) + search-coverage manifest (kala_gochara_coverage) — ' +
      'the per-contact episode grain under the gochara windows, with `contact_id` ' +
      'identity (Q01: the same claim is re-identifiable across rebuilds/republishes).\n\n' +
      'Output layers (§N.6, disjoint BY CONSTRUCTION): hard_floor.confirmed = ' +
      'completeness_state in the confirmed set AND target_resolution_state=resolved ' +
      '(trim-PROOF: a confirmed set larger than the page limit returns ' +
      'not_computed + floor_overflow, never a truncated floor); context_layer ' +
      '(only with include_context=true) = catalog-only rows (unqualified/unavailable/ ' +
      'unresolved) — structural context, never timing claims. `coverage` quotes the ' +
      'writer\'s own requested/completed horizons exactly (H-3) with ' +
      'unsearched_reason when completion fell short — an empty episode list is ' +
      'always accompanied by what was actually searched.\n\n' +
      'Moon (R7): moon=on_demand serves the moon_on_demand coverage record; Moon ' +
      'episodes are not persisted and live derivation routes via S-1 find_episodes — ' +
      'a missing moon partition is stated, never a fabricated 0-contact answer.\n\n' +
      'A chart with no kala_gochara_authority row returns status=unpublished with a ' +
      'full coverage object — never an error, never a v1 default (N-10).\n\n' +
      'Requires: chart_id (UUID).',
    ContactLedgerInputSchema.shape,
    async (params) => {
      const input = ContactLedgerInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      try {
        const result = await queryContactLedger(input, principal)
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_contact_ledger_get' }) }],
          isError: true,
        }
      }
    }
  )
}
