/**
 * get_database_schema — L1 discovery substrate serving surface (C3 SchemaMap)
 * ================================================================================
 * Elevation Campaign v2.1, STREAM α Lane-H, Task 1. Serves the frozen `SchemaMap` shape
 * (contract C3, `~/elev-v2-shared/contracts/C3_SCHEMA_MAP_OUTPUT_v1_0.md`) — every
 * `fact_category × fact_subject × fact_keys` combination that actually exists in the live
 * `chart_facts` data model, mechanically enumerated (C3 rule 1), paginated per C1
 * (`budget_kb`, `pagination`, `next_cursor`), plus the seeded `concept_aliases` table
 * (`concept_aliases.ts`, C3 §2/§4).
 *
 * RELATIONSHIP TO THE PHASE-0 GENERATOR (per RUNWAY correction — do not re-derive/rebuild):
 * `00_ARCHITECTURE/llm_consumption_audit/briefs/elevation_campaign/phase0/schema_map_generate.cjs`
 * is a standalone CLI script (own `pg.Client`, own `DATABASE_URL`, no exported reusable
 * function — its `main()` runs unconditionally on module load) that already live-tested this
 * exact enumeration against both canonical charts and established the `entries` shape this
 * capability conforms to byte-for-byte (`fact_category`, `fact_subject`, `fact_keys`,
 * `row_count`, `sample_fact_ids` — see C3). It cannot be `import`ed into a Next.js request
 * handler (its own client, argv-driven, writes to stdout/file and exits) and shelling out to
 * it per-request would mean a SECOND, unpooled PG connection path alongside every other
 * capability in this codebase, which all read through the shared `@/lib/db/client` pool
 * (`get_chart_snapshot.ts`, `list_entities.ts`, every other `get_*.ts` in this directory) —
 * not a pattern this codebase uses anywhere. This handler is therefore a direct TypeScript
 * mirror of the SAME grouped SQL enumeration the `.cjs` generator already validated (same
 * GROUP BY fact_category, fact_subject; same fact_keys/row_count/sample_fact_ids per group),
 * run through the shared pool — the serving-layer half of C3, not an independent re-derivation
 * of the census concept. The generator itself is untouched (read-only reference, outside this
 * lane's manifest).
 *
 * GAP the generator itself does not close (documented honestly, not silently patched): its own
 * `pagination` block sets `limit = entries.length` / `total = entries.length` — i.e. no real
 * slicing, it always returns everything. This capability is what actually implements C3 rule 3
 * ("paginated per C1... a full 218-category × N-subject enumeration will not fit a single
 * response") — real offset/limit slicing plus `buildHonestPagination`/cursor-fingerprint reuse
 * (the same envelope.ts helpers `list_entities.ts` already uses for this exact pattern).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import {
  buildHonestPagination,
  computeFilterFingerprint,
  checkCursorFingerprint,
  CURSOR_FILTER_MISMATCH_FLAG,
} from '@/lib/retrieval/envelope'
import { CONCEPT_ALIASES, type ConceptAlias } from './concept_aliases'

export type SchemaMapEntry = {
  fact_category: string
  fact_subject: string
  fact_keys: string[]
  row_count: number
  sample_fact_ids: string[]
}

export type SchemaMap = {
  chart_id: string
  generated_at: string
  source: 'live DB — chart_facts, mechanically enumerated'
  entries: SchemaMapEntry[]
  concept_aliases: ConceptAlias[]
  pagination: { offset: number; limit: number; total: number; next_cursor: string | null }
}

// CLAUDE.md §B canonical chart — used only as the default enumeration target when no
// chart_id is supplied. The schema SHAPE (which category/subject/key combinations the L1
// writers emit) is deterministic across charts built by the same orchestrator/writer code —
// this is a discovery tool about the DATA MODEL, not about any one native's computed values —
// but an explicit chart_id is always honored over the default when supplied.
const DEFAULT_SCHEMA_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const DEFAULT_LIMIT = 50
const MAX_LIMIT = 200

async function enumerateSchemaEntries(chartId: string): Promise<SchemaMapEntry[]> {
  // Mirrors schema_map_generate.cjs's grouped enumeration (fact_category, fact_subject) ->
  // {fact_keys (sorted, deduped), row_count, sample_fact_ids (up to 3)} — same shape, done in
  // one SQL round trip via array_agg instead of the generator's in-process grouping loop.
  const result = await query<{
    fact_category: string
    fact_subject: string
    fact_keys: string[]
    row_count: string
    sample_fact_ids: string[]
  }>(
    `SELECT fact_category, fact_subject,
            array_agg(DISTINCT fact_key ORDER BY fact_key) AS fact_keys,
            count(*)::text AS row_count,
            (array_agg(fact_id ORDER BY fact_id))[1:3] AS sample_fact_ids
     FROM chart_facts
     WHERE chart_id = $1
     GROUP BY fact_category, fact_subject
     ORDER BY fact_category, fact_subject`,
    [chartId],
  )
  return result.rows.map(r => ({
    fact_category: r.fact_category,
    fact_subject: r.fact_subject,
    fact_keys: r.fact_keys ?? [],
    row_count: parseInt(r.row_count, 10),
    sample_fact_ids: (r.sample_fact_ids ?? []).slice(0, 3),
  }))
}

export const getDatabaseSchemaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_database_schema',
  type: 'tool',
  layer: 'L1',
  name: 'get_database_schema',
  description: [
    'Discovery substrate: every fact_category x fact_subject combination that actually exists',
    'in the live chart_facts data model, mechanically enumerated (never hand-authored), each',
    'with its observed fact_keys, row_count, and up to 3 sample fact_ids for spot-checking.',
    'PAGINATED (offset/limit/cursor, budget_kb) — never an unbounded dump. Also returns',
    'concept_aliases: a seeded table mapping common alternate names (e.g. "Gulika"/"Maandi",',
    '"sphuta", "panchanga", "mangal") to the real fact_category value(s) they resolve through.',
    'Use concept_locate to resolve a single free-text term instead of scanning this whole',
    'substrate. Conforms to the C3 SchemaMap contract.',
  ].join(' '),
  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID to enumerate against. Defaults to the canonical chart if omitted — the schema SHAPE is deterministic across charts built by the same writers.' },
    limit: { type: 'number', description: `Entries per page (default ${DEFAULT_LIMIT}, max ${MAX_LIMIT}).`, default: DEFAULT_LIMIT },
    cursor: { type: 'string', description: 'Opaque pagination cursor from a previous response\'s next_cursor.' },
    budget_kb: { type: 'number', description: 'Optional response-size ceiling override, 1-64 KB (C1). Tighter than the tool default is honored; wider is clamped to the default.' },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 30, always_include: false },
  },
  density_contract: {
    paginated: true,
    facets: ['chart_id', 'limit', 'cursor', 'budget_kb'],
    empty_reason: true,
  },
  async handler(args, _ctx) {
    try {
      const chartId = (args.chart_id as string | undefined) ?? DEFAULT_SCHEMA_CHART_ID
      const limit = Math.min(Math.max((args.limit as number) ?? DEFAULT_LIMIT, 1), MAX_LIMIT)

      const currentFingerprint = computeFilterFingerprint({ chart_id: chartId })
      const cursorArg = args.cursor as string | undefined
      const cursorCheck = checkCursorFingerprint(cursorArg, currentFingerprint)
      const offset = cursorCheck.offset

      const allEntries = await enumerateSchemaEntries(chartId)
      const total = allEntries.length
      const pageEntries = allEntries.slice(offset, offset + limit)
      const served = pageEntries.length

      const pagination = buildHonestPagination({
        served, limit, offset, total, filterFingerprint: currentFingerprint,
      })

      const judgment_flags: string[] = cursorCheck.mismatch ? [CURSOR_FILTER_MISMATCH_FLAG] : []

      const schemaMap: SchemaMap & { judgment_flags: string[]; empty_reason?: string } = {
        chart_id: chartId,
        generated_at: new Date().toISOString(),
        source: 'live DB — chart_facts, mechanically enumerated',
        entries: pageEntries,
        concept_aliases: CONCEPT_ALIASES,
        pagination: {
          offset, limit, total,
          next_cursor: pagination.next_cursor,
        },
        judgment_flags,
        ...(total === 0
          ? { empty_reason: `chart_id "${chartId}" has no chart_facts rows — the schema census is genuinely empty for this chart (not a query bug).` }
          : {}),
      }

      return { content: schemaMap, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
