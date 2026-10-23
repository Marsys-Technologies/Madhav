/** K7 composites read stored stages in one published-head snapshot. No astrology here. */
import { query } from '@/lib/db/client'
import { isVerifiedPassStatus, VERIFICATION_PASS_STATUS_VOCAB, VERIFIED_PASS_STATUSES } from '../../../envelope'
import { qualifyStoryConvergence } from './story_source'
import { classifyEmptyLayer, type EmptyLayerEvidence } from './empty_layer_reason'
import { MUHURTA_UNDERTAKINGS } from '@/generated/muhurta_undertakings.generated'
import type { CapabilityContext, CapabilityDescriptor, CapabilityHandler, InputSchema, ToolResult } from '../../types'

export type ViewName = 'now' | 'ahead' | 'priority' | 'elect' | 'story' | 'ritual' | 'explain'
export type PublicViewName = `kala_${ViewName}_get`

// Executable identities, also source evidence for the unchanged estate census.
// Keep the public compatibility face separate from its stored-stage reader.
const viewRoutes = {
  now: { stage_uri: 'marsys://tool/L3/now_read', public_uri: 'marsys://tool/L3/kala_now_get', public_name: 'kala_now_get' },
  ahead: { stage_uri: 'marsys://tool/L3/ahead_read', public_uri: 'marsys://tool/L3/kala_ahead_get', public_name: 'kala_ahead_get' },
  priority: { stage_uri: 'marsys://tool/L3/priority_read', public_uri: 'marsys://tool/L3/kala_priority_get', public_name: 'kala_priority_get' },
  elect: { stage_uri: 'marsys://tool/L3/elect_read', public_uri: 'marsys://tool/L3/kala_elect_get', public_name: 'kala_elect_get' },
  story: { stage_uri: 'marsys://tool/L3/story_read', public_uri: 'marsys://tool/L3/kala_story_get', public_name: 'kala_story_get' },
  ritual: { stage_uri: 'marsys://tool/L3/ritual_read', public_uri: 'marsys://tool/L3/kala_ritual_get', public_name: 'kala_ritual_get' },
  explain: { stage_uri: 'marsys://tool/L3/explain_read', public_uri: 'marsys://tool/L3/kala_explain_get', public_name: 'kala_explain_get' },
} as const

/** KYD-123: public names describe the established request/envelope contract.
 * They are NOT synonyms for the stage readers. K7-1b supplies the actual legacy
 * adapter in its authenticated MCP boundary; no web adapter is installed here.
 * Clock/horizon defaults, mortality/Mode-3 routing and validation stay with the
 * established handler. Never turn a domain into an assertion ID, an undertaking
 * into an event class, or a date into an arbitrary instant. */
export interface LegacyViewAdapter {
  authorize: (chart_id: string, context?: CapabilityContext) => Promise<boolean>
  invoke: (tool: PublicViewName, args: Record<string, unknown>, context?: CapabilityContext) => Promise<ToolResult>
}
const legacyCommon: InputSchema = {
  chart_id: { type: 'string', required: true, description: 'Explicit chart UUID; no chart default.' },
  published_request: { type: 'object', description: 'Explicit published-stage selectors. Opts into the stage response; omitted requests retain the legacy contract.',
    properties: {
      at: { type: 'string' }, date_from: { type: 'string' }, date_to: { type: 'string' },
      event_class: { type: 'string' }, assertion_id: { type: 'string' },
      source_table: { type: 'string' }, record_id: { type: 'string' },
      limit: { type: 'number' }, offset: { type: 'number' },
    } },
  question_frame: { type: 'object', description: 'Forwarded without reinterpretation to the established handler.',
    properties: Object.fromEntries(['domain', 'entity', 'horizon', 'intent_verb', 'stakes', 'comparison_target']
      .map(key => [key, { type: 'string' }])) },
}
const ayanamsha: InputSchema = {
  ayanamsha_id: { type: 'string', description: 'Established default: lahiri_chitrapaksha.' },
}
const budget: InputSchema = {
  budget_kb: { type: 'number', description: 'Established response ceiling: 1..200 KB, default 40.' },
}
const legacySchemas: Record<ViewName, InputSchema> = {
  now: { ...legacyCommon, ...ayanamsha,
    as_of: { type: 'string', description: 'YYYY-MM-DD; omission retains the legacy today default.' },
    at: { type: 'string', description: 'Optional exact ISO instant with timezone for an additive published_now snapshot; never inferred from as_of.' } },
  ahead: { ...legacyCommon, ...ayanamsha,
    horizon_years: { type: 'number', description: 'Integer 1..20; legacy default 5.' },
    domain: { type: 'string' }, max_items: { type: 'number', description: 'Integer 1..200; legacy default 20.' } },
  priority: { ...legacyCommon, ...ayanamsha,
    date_from: { type: 'string', description: 'YYYY-MM-DD; legacy default today.' },
    date_to: { type: 'string', description: 'YYYY-MM-DD; legacy default today+90 days.' },
    top_k: { type: 'number', description: 'Integer 1..100; legacy default 20.' },
    preference: { type: 'array', items: { type: 'string' }, description: 'Declared Tulana presentation order.' },
    domain: { type: 'string' }, domains: { type: 'array', items: { type: 'string' } } },
  elect: { ...legacyCommon, ...budget,
    undertaking: { type: 'string', enum: [...MUHURTA_UNDERTAKINGS], description: 'Legacy default general.' },
    date_range: { type: 'object', description: 'Legacy default today..today+90 days; maximum 90 days.',
      properties: { start: { type: 'string', required: true }, end: { type: 'string', required: true } } },
    min_score: { type: 'number', description: '0..1; legacy default 0.' },
    limit: { type: 'number', description: 'Integer 1..45; legacy default 5.' },
    native_janma_nakshatra: { type: 'string' },
    target_graha: { type: 'string', enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] } },
  story: { ...legacyCommon, ...budget,
    top_k: { type: 'number', description: 'Integer 1..739; omission retains all source rows before dedup.' } },
  ritual: { ...legacyCommon, ...budget,
    horizon: { type: 'string', description: 'Legacy parser and its explicit fallback disclosure are preserved.' },
    sky_pattern_spec: { type: 'object' },
    undertaking: { type: 'string', description: 'Legacy Mode-3 redirect to kala_elect_get; never a stage class.' },
    activity_class: { type: 'string', enum: ['vivah', 'griha_pravesh', 'vyapara', 'yatra', 'property_purchase',
      'mantra_initiation', 'upaya_ritual', 'sadhana_initiation'], description: 'Legacy default upaya_ritual.' },
    limit: { type: 'number', description: 'Integer 1..50; legacy default 10.' } },
  explain: { ...legacyCommon, ...ayanamsha,
    domain: { type: 'string', description: 'Legacy PACT domain; never an assertion identity.' },
    bhava: { type: 'number', description: 'Integer 1..12; required when domain is omitted.' },
    as_of_date: { type: 'string', description: 'YYYY-MM-DD; legacy default today.' },
    max_signals: { type: 'number', description: 'Integer 1..50; legacy default 15.' } },
}
export function legacyViewContract(view: ViewName) {
  return {
    public_name: viewRoutes[view].public_name,
    stage_uri: viewRoutes[view].stage_uri,
    input_schema: legacySchemas[view],
    // There is no sourced mapping for these identities/time semantics yet.
    unavailable_stage_bindings: view === 'now' ? ['at']
      : view === 'ahead' ? ['date_from', 'date_to', 'domain_filter']
      : view === 'priority' ? ['date_from', 'date_to', 'domain_filter']
      : view === 'elect' ? ['event_class', 'date_from', 'date_to']
      : view === 'ritual' ? ['event_class', 'date_from', 'date_to', 'sky_pattern_spec']
      : view === 'explain' ? ['assertion_id_or_record_drill'] : ['legacy_chapter_envelope'],
    response_policy: 'legacy_verbatim' as const,
    cutover_policy: 'retain_legacy_until_published_generation_golden_equivalence' as const,
  }
}
export function makeLegacyViewHandler(view: ViewName, adapter?: LegacyViewAdapter): CapabilityHandler {
  const contract = legacyViewContract(view)
  const refusal = (args: Record<string, unknown>, reason: string): ToolResult => ({ is_error: true, content: {
    tool: contract.public_name, chart_id: args.chart_id ?? null, manifest_id: null, empty_reason: reason,
    stage_capability: contract.stage_uri, unavailable_stage_bindings: contract.unavailable_stage_bindings,
  } })
  return async (args, context) => {
    if (typeof args.chart_id !== 'string' || !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(args.chart_id)) {
      return refusal(args, 'invalid_request')
    }
    if (!adapter) return refusal(args, 'legacy_adapter_unavailable')
    try {
      if (await adapter.authorize(args.chart_id, context) !== true) return refusal(args, 'authorization_denied')
    } catch { return refusal(args, 'authorization_unavailable') }
    try {
      // Exact forwarding deliberately leaves legacy defaults and special routes
      // with the established handler. Neither inputs nor successful/error
      // envelopes gain invented manifest IDs, dates, identities or scores.
      return await adapter.invoke(contract.public_name, args, context)
    } catch { return refusal(args, 'legacy_query_failed') }
  }
}
export function makePublicView(view: ViewName): CapabilityDescriptor {
  const contract = legacyViewContract(view)
  const uri = viewRoutes[view].public_uri
  return {
    uri, name: contract.public_name, type: 'tool', layer: 'L3',
    description: `Kāla ${view}: explicit published_request selectors serve ${contract.stage_uri}'s published-stage envelope. Requests without published_request retain the legacy contract, whose web adapter is unavailable.`,
    scope: 'per_chart', archetype: 'temporal', traversal_level: 'L-OVERVIEW', tool_role: 'umbrella',
    emits_references: false, grounds_to: { l1_fact_ids: false }, lel_capable: false,
    required_inputs: ['chart_id'], input_schema: contract.input_schema,
    annotations: { read_only: true, idempotent: true, destructive: false, open_world: false },
    // Applies to explicit published_request responses; legacy envelopes remain verbatim.
    density_contract: { paginated: true, facets: ['event_class', 'source_table'], empty_reason: true },
    semantic_capabilities: [{
      scu_id: `scu.catalog.${contract.public_name}`, version: 1, label: `Kāla ${view} public compatibility contract`,
      description: 'Explicit published_request selectors opt into the published-stage envelope. Established requests retain their authenticated legacy contract.',
      kind: 'temporal', domains: ['timing'], concepts: [contract.public_name, 'kala'],
      intents: ['assess', 'sequence', 'verify'], horizons: ['historical', 'current', 'future'], scope: 'chart',
      inputs: Object.keys(contract.input_schema).map(key => key === 'chart_id' ? key : `${key}?`),
      outputs: ['empty_reason', 'unavailable_stage_bindings', 'manifest_id', 'generation', 'rows', 'density', 'coverage', 'pagination'], primary_binding_uri: uri,
      provenance_requirements: ['chart_id'], freshness_policy: 'No answer-readiness claim from name resolution alone.',
      entitlement: 'native', safety_notes: ['No implicit legacy identity/time conversion or successful empty envelope.'],
      known_gaps: ['The authenticated MCP adapter and unchanged-generator bridge regeneration belong to K7-1b.',
        'The web registry has no installed legacy adapter; requests without published_request return an explicit unavailable error.',
        'No implicit legacy-to-stage conversion or production acceptance is enabled by the explicit request path.'],
      availability_dispositions: [{ binding_id: `registry:${uri}`, status: 'deliberately_dark',
        reason: 'Name reach is additive; legacy execution and published-generation equivalence are separate evidence gates.',
        source_refs: ['platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts'] }], editorial: true,
    }],
    async handler(args, context) {
      if (Object.hasOwn(args, 'published_request')) {
        const { servePublishedRequest } = await import('./published_request')
        return servePublishedRequest(view, args, context)
      }
      return makeLegacyViewHandler(view)(args, context)
    },
  }
}
type Data = Record<string, unknown>
type Density = 'confirmed' | 'testimony' | 'catalog_only' | null
export interface Manifest extends Data { manifest_id: string; generation: string }
export interface ViewSnapshot {
  manifest: Manifest | null
  coverage: Data[]
  sources: { table: string; total: number; rows: Data[]; layer?: SourceLayerCounts }[]
}
/** Measured per source by viewSql, before any selector filter (SR-EMPTY-REASON); absent = not measured. */
export interface SourceLayerCounts {
  rows_in_published_generation: number | string | null
  rows_any_partition: number | string | null
  asset_state: string | null
}
export interface ViewSpec {
  name: ViewName
  description: string
  sources: SourceTable[]
  required: ('at' | 'date_from' | 'date_to' | 'event_class' | 'assertion_id')[]
}
type SourceTable = keyof typeof SOURCES
const SOURCES = {
  kala_darshana: { id: 's.id', assertion: true, generation: true, asset: 'ka_kala_darshana',
    start: 'COALESCE(s.interval_start, s.window_start::timestamp AT TIME ZONE \'UTC\')',
    end: 'COALESCE(s.interval_end, (s.window_end + 1)::timestamp AT TIME ZONE \'UTC\')' },
  kala_obstruction: { id: 's.id', assertion: true, generation: true, asset: 'ka_vighnakara',
    start: 's.interval_start', end: 's.interval_end' },
  // No single writer asset (ka_gochara_v3/v4_41/v5 all write it): the build state is not consulted.
  kala_gochara_contacts: { id: 's.contact_id', assertion: false, generation: true, asset: null,
    start: 's.t_in', end: 's.t_out' },
  kala_bhavishya: { id: 's.id', assertion: false, generation: false, asset: 'ka_bhavishya_lekha',
    start: 's.window_start::timestamp AT TIME ZONE \'UTC\'', end: '(s.window_end + 1)::timestamp AT TIME ZONE \'UTC\'' },
  kala_convergence: { id: 's.convergence_id', assertion: false, generation: false, asset: 'ka_sangam',
    start: 's.window_start::timestamp AT TIME ZONE \'UTC\'', end: '(s.window_end + 1)::timestamp AT TIME ZONE \'UTC\'' },
  kala_jivana_parva: { id: 's.id', assertion: false, generation: false, asset: 'ka_jivana_parva',
    start: 'make_date(s.start_year, 1, 1)::timestamp AT TIME ZONE \'UTC\'',
    end: 'make_date(s.end_year + 1, 1, 1)::timestamp AT TIME ZONE \'UTC\'' },
} as const
const object = (v: unknown): Data => v && typeof v === 'object' && !Array.isArray(v) ? v as Data : {}

/** The binding is the selected table's own stored status, never a candidate
 * join, upstream verdict, confidence or operator role. No current producer
 * promotes: they persist UNVERIFIED_DEFAULT from verification_vocab.py.
 * (I) INTERPRETATION: every recognized unverified status remains catalog-only;
 * legacy/unbound rows retain null density, even when they contain a status.
 */
function rowDensity(table: string, row: Data, manifest: Manifest): { density: Density; context: boolean; reason: string | null } {
  const generationBound = Object.hasOwn(SOURCES, table) && SOURCES[table as SourceTable].generation
  const context = !generationBound || !row.generation || row.generation === '3.0' || row.generation !== manifest.generation
    || (table === 'kala_gochara_contacts' && row.build_id !== manifest.manifest_id)
  if (!Object.hasOwn(SOURCES, table) || row.verification_pass_status == null) {
    return { density: null, context, reason: 'stored_tier_contract_unavailable' }
  }
  if (context) return { density: null, context, reason: 'unbound_generation' }
  const status = VERIFICATION_PASS_STATUS_VOCAB.find(entry => entry.status === row.verification_pass_status)
  if (!status) return { density: null, context, reason: 'invalid_stored_tier' }
  return { density: isVerifiedPassStatus(status.status) ? 'confirmed' : 'catalog_only', context, reason: null }
}

// Additive local descriptor fields keep the frozen shared interface untouched.
type StageDensityContract = NonNullable<CapabilityDescriptor['density_contract']> & {
  stored_tier_columns: string[]
  unavailable_sources: SourceTable[]
  publication_bindings: { table: SourceTable; generation_column: string | null; build_id_column: string | null }[]
}
function stageDensityContract(sources: SourceTable[]): StageDensityContract {
  return { paginated: true, facets: ['event_class', 'source_table'], empty_reason: true,
    stored_tier_columns: sources.map(table => `${table}.verification_pass_status`), unavailable_sources: [],
    publication_bindings: sources.map(table => ({ table, generation_column: SOURCES[table].generation ? 'generation' : null,
      build_id_column: table === 'kala_gochara_contacts' ? 'build_id' : null })) }
}

/** Per-source empty reason from the counts viewSql measured; a snapshot that carries none is an honest unreadable. */
function sourceEmpty(source: ViewSnapshot['sources'][number]): { empty_reason: string; layer_state: EmptyLayerEvidence } {
  const num = (v: number | string | null | undefined) => v === null || v === undefined || v === '' ? null : Number(v)
  const asset = Object.hasOwn(SOURCES, source.table) ? SOURCES[source.table as SourceTable].asset : null
  const evidence: EmptyLayerEvidence = {
    rows_any_partition: num(source.layer?.rows_any_partition),
    rows_served_unfiltered: num(source.layer?.rows_in_published_generation),
    asset_state: source.layer?.asset_state ?? null,
    asset_state_measurable: asset !== null,
  }
  return { empty_reason: classifyEmptyLayer(evidence), layer_state: evidence }
}

export function composeView(view: ViewName, chart_id: string, snapshot: ViewSnapshot, offset = 0) {
  const manifest = snapshot.manifest
  const sources = manifest ? snapshot.sources : []
  const density = { scope: 'page' as const, confirmed: 0, testimony: 0, catalog_only: 0, context_only: 0, unknown: 0 }
  const rows = sources.flatMap(source => source.rows.map(stored => {
    const data = source.table === 'kala_jivana_parva' ? qualifyStoryConvergence(stored) : stored
    const tier = rowDensity(source.table, data, manifest!)
    if (tier.density === null) density.unknown++
    else density[tier.density]++
    if (tier.context) density.context_only++
    const assertion_id = typeof data.assertion_id === 'string' ? data.assertion_id : object(data.assertion).assertion_id
    const id = data.id ?? data.convergence_id ?? data.contact_id ?? assertion_id
    return { source_table: source.table, record_id: String(id), density: tier.density,
      density_reason: tier.reason,
      verification: { column: `${source.table}.verification_pass_status`, status: data.verification_pass_status ?? null,
        generation: data.generation ?? null, manifest_id: tier.context ? null : manifest!.manifest_id },
      qualification: tier.context ? 'context_only' : 'published', data,
      drill: typeof assertion_id === 'string'
        ? { capability: 'marsys://tool/L3/explain_read', args: { chart_id, assertion_id } }
        : { capability: 'marsys://tool/L3/explain_read', args: { chart_id, source_table: source.table, record_id: String(id) } },
    }
  }))
  const order = { confirmed: 0, testimony: 1, catalog_only: 2 }
  rows.sort((a, b) => (a.density === null ? 3 : order[a.density]) - (b.density === null ? 3 : order[b.density]) || a.source_table.localeCompare(b.source_table) || a.record_id.localeCompare(b.record_id))
  const total_matching = sources.reduce((n, source) => n + Number(source.total), 0)
  return { view, chart_id, manifest_id: manifest?.manifest_id ?? null, manifest,
    generation: manifest?.generation ?? null, empty_reason: !manifest ? 'unpublished' : !rows.length ? 'no_matching_rows' : null,
    rows, density, catalog_only_rows_in_page: density.catalog_only + density.unknown, coverage: manifest ? snapshot.coverage : [],
    pagination: { total_matching, returned: rows.length, more_available: sources.some(source => Number(source.total) > offset + source.rows.length) },
    // SR-EMPTY-REASON: a source that contributed nothing says which kind of nothing (the page-level empty_reason is
    // set only when EVERY source is empty, so one silent empty source beside a populated one read as "none").
    sources: sources.map(s => ({ table: s.table, total_matching: Number(s.total), returned: s.rows.length,
      ...(Number(s.total) === 0 && s.rows.length === 0 ? sourceEmpty(s) : {}) })),
    judgment_flags: [ ...(density.catalog_only + density.unknown ? ['catalog_only_rows_present'] : []),
      ...(density.unknown ? ['stored_tier_contract_unavailable'] : []),
      ...(density.context_only ? ['context_only_rows_present'] : []), ...(!snapshot.coverage.length ? ['coverage_unavailable'] : []) ],
  }
}

/** The legacy (generation IS NULL) rows a view serves beside the published generation. kala_obstruction's legacy
 * partition is REPLACED by the head once the head holds obstruction rows (SR-K9-WRITE-SCOPE: the K9 build writes the
 * full set under its generation, so serving both would double every window); kala_darshana keeps serving both. */
function legacyRows(table: SourceTable): string {
  return table === 'kala_obstruction'
    ? ' OR (s.generation IS NULL AND NOT EXISTS (SELECT 1 FROM kala_obstruction h WHERE h.chart_id = s.chart_id AND h.generation = p.generation))'
    : ' OR s.generation IS NULL'
}

/** Which of a source's rows belong to the published generation (legacy rows included where the view serves them). */
function generationClause(table: SourceTable): string {
  const source = SOURCES[table]
  return source.generation ? `AND (s.generation = p.generation${source.assertion ? legacyRows(table) : ''})`
    : "AND (to_jsonb(s)->>'generation' IS NULL OR to_jsonb(s)->>'generation' = p.generation)"
}

/** $1 chart, $2 at, $3/$4 horizon, $5 class, $6 assertion, $7 limit, $8 offset,
 * $9 table, $10 record. All identifiers come from the fixed source inventory. */
export function viewSql(spec: ViewSpec): string {
  const ctes = spec.sources.map((table, i) => {
    const source = SOURCES[table]
    const assertionFilter = source.assertion
      ? `($5::text IS NULL OR s.assertion->'subject'->>'event_class' = $5)
         AND ($6::text IS NULL OR s.assertion_id = $6)`
      : table === 'kala_gochara_contacts'
        ? `(($5::text IS NULL AND $6::text IS NULL) OR EXISTS (
           SELECT 1 FROM kala_darshana d WHERE d.chart_id = p.chart_id AND d.generation = p.generation
             AND ($5::text IS NULL OR d.assertion->'subject'->>'event_class' = $5)
             AND ($6::text IS NULL OR d.assertion_id = $6)
             AND d.assertion->'roots'->'contact_ids' ? s.contact_id))`
        : '($5::text IS NULL AND $6::text IS NULL)'
    // JSON projection is pre-migration-safe: an absent column stays NULL.
    // Rank before pagination by the same canonical stored-status mapping.
    const tier = "to_jsonb(s)->>'verification_pass_status'"
    const bound = (source.generation ? "to_jsonb(s)->>'generation' = p.generation AND p.generation <> '3.0'" : 'FALSE')
      + (table === 'kala_gochara_contacts' ? " AND to_jsonb(s)->>'build_id' = p.manifest_id" : '')
    const quoted = (statuses: readonly string[]) => statuses.map(status => `'${status.replaceAll("'", "''")}'`).join(',')
    const rank = `CASE WHEN ${bound} AND ${tier} IN (${quoted(VERIFIED_PASS_STATUSES)}) THEN 0
      WHEN ${bound} AND ${tier} IN (${quoted(VERIFICATION_PASS_STATUS_VOCAB.map(entry => entry.status))}) THEN 2 ELSE 3 END`
    return `source_${i} AS NOT MATERIALIZED (
      SELECT to_jsonb(s) || jsonb_build_object('verification_pass_status', to_jsonb(s)->>'verification_pass_status')${table === 'kala_jivana_parva' ? ` || jsonb_build_object('convergence_source_available',
        EXISTS (SELECT 1 FROM kala_convergence WHERE chart_id = $1::uuid AND COALESCE(to_jsonb(kala_convergence)->>'generation', 'legacy') = COALESCE((SELECT generation FROM kala_layer_head WHERE chart_id = $1::uuid), 'legacy')))` : ''} AS data, ${source.id}::text AS record_id, ${rank} AS tier_order
      FROM ${table} s CROSS JOIN published p
      WHERE s.chart_id = $1::uuid
        ${generationClause(table)}
        AND ($2::timestamptz IS NULL OR (${source.start} <= $2::timestamptz AND ${source.end} > $2::timestamptz))
        AND ($3::timestamptz IS NULL OR ${source.end} > $3::timestamptz)
        AND ($4::timestamptz IS NULL OR ${source.start} < $4::timestamptz)
        AND ${assertionFilter}
        AND ($9::text IS NULL OR ($9 = '${table}' AND ${source.id}::text = $10))
    )`
  })
  return `WITH published AS (
    SELECT h.chart_id, h.generation, c.build_id::text AS manifest_id,
           c.model_digest, c.rule_registry_version, c.conventions, h.published_at
    FROM kala_layer_head h JOIN kala_layer_candidate c
      ON c.chart_id = h.chart_id AND c.generation = h.generation
    WHERE h.chart_id = $1::uuid AND c.state = 'published'
  ), ${ctes.join(',\n')}
  SELECT (SELECT to_jsonb(p) FROM published p) AS manifest,
    COALESCE((SELECT jsonb_agg(to_jsonb(g) ORDER BY g.grain_key)
      FROM kala_layer_candidate_grain g JOIN published p USING (chart_id, generation)), '[]'::jsonb)
    || COALESCE((SELECT jsonb_agg(to_jsonb(g) ORDER BY g.partition_kind, g.partition_key)
      FROM kala_gochara_coverage g JOIN published p USING (chart_id, generation)), '[]'::jsonb) AS coverage,
    jsonb_build_array(${spec.sources.map((table, i) => `jsonb_build_object(
      'table', '${table}', 'total', (SELECT count(*) FROM source_${i}),
      'layer', jsonb_build_object(
        'rows_in_published_generation', (SELECT count(*) FROM ${table} s CROSS JOIN published p WHERE s.chart_id = $1::uuid ${generationClause(table)}),
        'rows_any_partition', (SELECT count(*) FROM ${table} WHERE chart_id = $1::uuid),
        'asset_state', ${SOURCES[table].asset ? `(SELECT state FROM asset_throughput WHERE chart_id = $1::uuid AND asset_id = '${SOURCES[table].asset}' LIMIT 1)` : 'NULL::text'}),
      'rows', COALESCE((SELECT jsonb_agg(page.data ORDER BY page.tier_order, page.record_id)
        FROM (SELECT * FROM source_${i} ORDER BY tier_order, record_id LIMIT $7 OFFSET $8) page), '[]'::jsonb))`).join(',\n')}) AS sources`
}

function inputs(spec: ViewSpec, args: Data): unknown[] {
  const text = (key: string) => typeof args[key] === 'string' ? (args[key] as string).trim() : ''
  if (!text('chart_id')) throw new Error('chart_id is required')
  for (const key of spec.required) {
    if (key === 'assertion_id' && text('source_table') && text('record_id')) continue
    if (!text(key)) throw new Error(`${key} is required`)
  }
  const instant = (key: string) => {
    if (args[key] === undefined || args[key] === null) return null
    const value = text(key)
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) || !Number.isFinite(Date.parse(value))) {
      throw new Error(`${key} must be an explicit ISO instant with timezone`)
    }
    const [year, month, day] = value.slice(0, 10).split('-').map(Number)
    if (new Date(Date.UTC(year, month - 1, day)).getUTCDate() !== day) throw new Error(`${key} has an invalid calendar date`)
    return value
  }
  const at = instant('at'), from = instant('date_from'), to = instant('date_to')
  if (!!from !== !!to || (from && to && Date.parse(from) >= Date.parse(to))) throw new Error('date_from/date_to must form a nonempty interval')
  const limit = args.limit ?? 25, offset = args.offset ?? 0
  if (typeof limit !== 'number' || !Number.isInteger(limit) || limit < 1 || limit > 50 ||
      typeof offset !== 'number' || !Number.isSafeInteger(offset) || offset < 0) throw new Error('limit must be 1..50 and offset nonnegative')
  const table = text('source_table'), record = text('record_id')
  if (!!table !== !!record || (table && !spec.sources.includes(table as SourceTable))) throw new Error('source_table/record_id must name a supported source')
  return [text('chart_id'), at, from, to, text('event_class') || null, text('assertion_id') || null, limit, offset, table || null, record || null]
}

export function makeView(spec: ViewSpec): CapabilityDescriptor & { density_contract: StageDensityContract } {
  const density_contract = stageDensityContract(spec.sources)
  return {
    uri: viewRoutes[spec.name].stage_uri, type: 'tool', layer: 'L3', name: `${spec.name}_read`,
    description: `${spec.description} Reads published Kāla stages and manifest; older unbound rows are context only.`,
    scope: 'per_chart', archetype: 'temporal', traversal_level: 'L-OVERVIEW', tool_role: 'umbrella',
    emits_references: true, grounds_to: { l1_fact_ids: true }, lel_capable: false,
    required_inputs: ['chart_id', ...spec.required.filter(k => k !== 'assertion_id')],
    drill_children: spec.name === 'explain' ? [] : ['marsys://tool/L3/explain_read'],
    semantic_capabilities: [{
      scu_id: `scu.catalog.${spec.name}_read`, version: 1, label: `Kāla ${spec.name} view`,
      description: spec.description, kind: 'temporal', domains: ['timing'],
      concepts: [`${spec.name}_read`, 'kala', 'published_temporal_assertions'],
      intents: ['assess', 'sequence', 'verify'], horizons: ['historical', 'current', 'future'], scope: 'chart',
      inputs: ['chart_id', ...spec.required, 'limit?', 'offset?'],
      outputs: ['manifest_id', 'manifest', 'rows', 'density', 'coverage', 'pagination', 'empty_reason'],
      primary_binding_uri: `marsys://tool/L3/${spec.name}_read`,
      primary_binding_details: { pagination: 'bounded_unverified',
        route_evidence: `platform/src/lib/retrieval/registry/layers/L3_kala/view_${spec.name}.ts`,
      },
      provenance_requirements: ['chart_id', 'manifest_id', 'generation', 'assertion.roots'],
      freshness_policy: 'Read one current published-head SQL snapshot; no private candidate is an answer.',
      entitlement: 'native', safety_notes: ['Legacy rows are context only; Unbound geometry has unknown density.'],
      known_gaps: ['MCP aliases and public bridge activation belong to K7-1b.',
        'Published-generation availability has no planner receipt contract in this fixture slice.',
        'Per-source pagination is bounded; a page count is not a whole-result evidence count.',
        'Existing/pre-migration rows retain null proof; new producers store single, with no independent verification credit.'],
      availability_dispositions: [{ binding_id: `registry:marsys://tool/L3/${spec.name}_read`,
        status: 'deliberately_dark', reason: 'Registry fixture reach is tested; planner answer readiness awaits a published-generation receipt contract and the serving handover.',
        source_refs: ['00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md#§5',
          'platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts'],
      }], editorial: true,
    }],
    annotations: { read_only: true, idempotent: true, destructive: false, open_world: false },
    density_contract: density_contract,
    input_schema: {
      chart_id: { type: 'string', required: true, description: 'Explicit chart UUID.' },
      at: { type: 'string', description: 'Exact ISO instant with timezone for NOW; intervals are half open.' },
      date_from: { type: 'string', description: 'Inclusive ISO horizon start with timezone.' },
      date_to: { type: 'string', description: 'Exclusive ISO horizon end with timezone.' },
      event_class: { type: 'string', description: 'Stored assertion subject class; required for ELECT/RITUAL.' },
      assertion_id: { type: 'string', description: 'Stored assertion identity for EXPLAIN, or use source_table and record_id.' },
      source_table: { type: 'string', description: 'Stored context/contact source named by a drill pointer.' },
      record_id: { type: 'string', description: 'Record identity paired with source_table.' },
      limit: { type: 'number', description: 'Rows per source, default 25, maximum 50.' },
      offset: { type: 'number', description: 'Nonnegative row offset per source.' },
    },
    async handler(args) {
      let params: unknown[]
      try { params = inputs(spec, args) } catch (error) {
        return { content: { view: spec.name, manifest_id: null, empty_reason: 'invalid_request', error: (error as Error).message }, is_error: true }
      }
      try {
        const result = await query<ViewSnapshot & import('pg').QueryResultRow>(viewSql(spec), params)
        const content = composeView(spec.name, String(params[0]), result.rows[0] ?? { manifest: null, coverage: [], sources: [] }, Number(params[7]))
        return { content: { ...content, density_contract, pagination: { ...content.pagination, limit_per_source: params[6], offset_per_source: params[7] } }, is_error: false }
      } catch {
        return { content: { view: spec.name, chart_id: params[0], manifest_id: null, empty_reason: 'query_failed', error: 'Kāla view query failed' }, is_error: true }
      }
    },
  }
}
