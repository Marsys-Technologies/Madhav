import 'server-only'
import { query } from '@/lib/db/client'
import type { QueryResultRow } from 'pg'
import { PROGRAMME_O_WAVE_WPS, PROGRAMME_POST_WAVE_ADDENDA } from '@/lib/nirmana-elevation/programme'

export const OPERATION_SECTIONS = ['foundation', 'health', 'assets', 'programme', 'learning'] as const
export type OperationSection = typeof OPERATION_SECTIONS[number]
export type EvidenceRow = Record<string, string | number | boolean | null>
export interface EvidenceSource { title: string; source: string; available: boolean; rows: EvidenceRow[]; note: string }
export interface OperationsEvidence { generatedAt: string; sources: EvidenceSource[]; notes: string[] }
export type EvidenceReader = (sql: string) => Promise<{ rows: QueryResultRow[] }>

const LAYERS: Record<string, string> = { L0: 'Brahmagyan', L1: 'Gaṇita', L2: 'Bodha', L3: 'Kāla', L4: 'Phala', L5: 'Mīmāṃsā' }
async function source(title: string, origin: string, sql: string, note: string, read: EvidenceReader,
  transform?: (row: QueryResultRow) => EvidenceRow): Promise<EvidenceSource> {
  try {
    const { rows } = await read(sql)
    return { title, source: origin, available: true, rows: rows.map(row => transform ? transform(row) : row as EvidenceRow), note }
  } catch {
    // Internal database errors may contain connection details. Never return them.
    return { title, source: origin, available: false, rows: [], note: 'This source could not be read. Its state is unavailable, not empty or healthy.' }
  }
}

/** Read-only projections of existing records; never dispatches tools, builds or publication. */
export async function readOperations(section: OperationSection, read: EvidenceReader = query): Promise<OperationsEvidence> {
  let sources: EvidenceSource[] = []
  const notes: string[] = []
  if (section === 'foundation') {
    sources = await Promise.all([
      source('Database presence', 'information_schema', `SELECT table_name AS component, true AS present
        FROM information_schema.tables WHERE table_schema='public' AND table_name IN
        ('charts','profiles','asset_registry','build_runs','ai_metering_attempts','ai_metering_receipts') ORDER BY table_name`,
        'Only listed tables are present. Presence does not prove their migrations, contents or serving health.', read),
      source('Recent migration receipts', '_migrations_applied', `SELECT filename, applied_at::text AS applied_at, sha256
        FROM _migrations_applied ORDER BY applied_at DESC, filename LIMIT 50`,
        'Last 50 recorded applications. These receipts do not independently verify current schema or every pending migration.', read),
    ])
    sources.push({ title: 'Runtime configuration', source: 'runtime presence checks', available: true,
      rows: ['GCS_BUCKET_NAME', 'BRAHMA_GCS_BUCKET', 'BRAHMA_ARTIFACT_BUCKET'].map((key, index) => ({
        component: ['Upload storage', 'Asset storage', 'Build artifacts'][index], configured: Boolean(process.env[key]), reachability: 'Not measured' })),
      note: 'Configuration presence only. Values and credentials are never returned.' })
    sources.push({title:'Serving release identity',source:'Cloud Run runtime metadata',available:true,
      rows:[{revision:process.env.K_REVISION ?? null,source_commit:process.env.NIRMANA_DEPLOYED_SHA ?? null}],
      note:'Runtime-declared revision and source identity. This does not independently measure service readiness or current traffic.'})
    notes.push('No storage probe or build is triggered by opening this page.')
  } else if (section === 'health') {
    sources = await Promise.all([
      source('Registered tools', 'capability_tool_registry', `SELECT tool_name, description, updated_at::text AS registry_updated_at
        FROM capability_tool_registry ORDER BY tool_name LIMIT 1000`,
        'Stored tool catalogue, at most 1,000 rows. Registration is not proof of response health. Functional grouping remains unratified.', read),
      source('Tool measurements · 24-hour view', 'mv_tool_metrics_24h', `SELECT mcp_tool_name AS tool, source,
        audience_tier AS historical_group, calls_24h AS calls,
        error_calls AS failed, CASE WHEN calls_24h>0 THEN error_calls::float/calls_24h ELSE NULL END AS failure_rate,
        p50_latency_ms AS median_ms, last_call_at::text AS last_call_at FROM mv_tool_metrics_24h ORDER BY mcp_tool_name,source,audience_tier LIMIT 1000`,
        'A rolling aggregate view, not historical time-series data. Source and historical group identify each population; historical tiers do not grant permissions. Refresh freshness is not independently measured.', read),
      source('Recorded session aggregates', 'mv_session_summary', `SELECT mcp_key_id AS key_reference,
        audience_tier AS historical_group, session_hour::text AS recorded_hour, unique_primitives,
        primitive_calls,bundle_calls,sub_tool_calls,zero_rows_calls FROM mv_session_summary
        ORDER BY session_hour DESC,mcp_key_id,audience_tier LIMIT 50`,
        'Last 50 stored session groups. These historical groups are not current roles. The view’s refresh freshness is unverified; use recorded query traces for step evidence.', read),
    ])
    sources.splice(2,0,{title:'Grounding findings',source:'retired grounding aggregate',available:false,rows:[],note:'The earlier grounding view was retired in the canonical baseline. A current measured source is unavailable.'})
    notes.push('Coverage measurements are unavailable: the earlier coverage tables were retired. No healthy or zero-coverage result is inferred.',
      'Use Query Trace for recorded sessions and Learning Review for calibration evidence. Historical health lines require a measured time-series source.')
  } else if (section === 'assets') {
    sources = await Promise.all([
      source('Asset register', 'asset_registry', `SELECT asset_id, layer, sanskrit_name, english_name, scope, asset_kind,
        catalog_status, is_active, (count_sql IS NOT NULL) AS has_count_contract FROM asset_registry ORDER BY layer, sort_order, asset_id LIMIT 1000`,
        'Canonical definitions, at most 1,000 rows. A count contract is configuration, not a measured count. Open a chart preparation workspace for its canonical counts.', read,
        row => ({ asset: [row.sanskrit_name, row.english_name].filter(Boolean).join(' · ') || row.asset_id,
          id: row.asset_id, layer: LAYERS[String(row.layer)] ?? 'Unmapped', scope: row.scope, kind: row.asset_kind,
          catalogue: row.catalog_status, active: row.is_active, count_contract: row.has_count_contract })),
      source('Recent build records', 'build_runs / build_run_assets', `SELECT b.id::text AS run, b.chart_id::text AS chart_id,
        c.subject_name AS chart, b.state AS state, b.started_at::text AS started_at, b.ended_at::text AS ended_at,
        COUNT(a.asset_id)::int AS planned_assets, COUNT(a.asset_id) FILTER (WHERE a.state='complete')::int AS completed_assets
        FROM build_runs b LEFT JOIN charts c ON c.id=b.chart_id LEFT JOIN build_run_assets a ON a.run_id=b.id
        GROUP BY b.id,c.subject_name ORDER BY b.created_at DESC,b.id LIMIT 50`,
        'Last 50 recorded runs; completed asset records do not by themselves prove chart readiness or quality.', read),
    ])
    notes.push('Chart preparation owns count evaluation and build actions. This register creates no second build writer.')
  } else if (section === 'programme') {
    sources.push({ title: 'Historical programme changes', source: 'governed Nirmāṇa programme declarations', available: true,
      rows: [...PROGRAMME_O_WAVE_WPS, ...PROGRAMME_POST_WAVE_ADDENDA].map(record => ({
        change: record.name, recorded_status: record.status, merged_at: record.merged_pr?.merged_at ?? null,
        pull_request: record.merged_pr?.number ?? null, provenance: record.note })),
      note: 'Historical Nirmāṇa record; the earlier elevation programme is superseded. These declarations do not establish current campaign acceptance.' })
    notes.push('Current successor campaigns retain their own governed ledgers and authority. Opening this record does not resume, rebuild or advance any campaign.')
  } else {
    sources = await Promise.all([
      source('Calibration snapshot evidence', 'mimamsa_calibration_snapshot', `SELECT snapshot_id::text AS snapshot,
        chart_id::text AS chart_id, formula_version, publication_status, two_key_complete,
        (chart_context_stale_at IS NOT NULL) AS stale_context, snapshot_at::text AS recorded_at
        FROM mimamsa_calibration_snapshot ORDER BY snapshot_at DESC,snapshot_id LIMIT 100`,
        'Last 100 recorded snapshots. Publication labels are stored state, not certification of independent co-sign authority.', read),
      source('Outcome records by chart', 'mimamsa_adjudication_log', `SELECT chart_id::text AS chart_id, outcome,
        COUNT(*)::int AS records, MAX(adjudicated_at)::text AS latest_recorded_at
        FROM mimamsa_adjudication_log GROUP BY chart_id,outcome ORDER BY MAX(adjudicated_at) DESC,chart_id,outcome LIMIT 100`,
        'Recorded outcomes, at most 100 chart/outcome groups. This is not a quality score or statistical validation.', read),
    ])
    notes.push('Read-only review. Publication controls await verified independent co-sign authority and stale-context rules.',
      'Chart review, follow-up and quarantined resonance retain their existing chart-level workflow. No feedback or weight update is performed here.')
  }
  return { generatedAt: new Date().toISOString(), sources, notes }
}
