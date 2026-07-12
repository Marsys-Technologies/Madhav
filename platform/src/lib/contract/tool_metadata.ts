/**
 * tool_metadata.ts — single-source tool ↔ asset reconciliation table
 * (Unit 3.tool_asset_recon, sets G6_tool_coverage).
 *
 * Every retrieval / MCP tool live in the system declares HERE which data
 * asset(s) it serves and which ayanamsha frame it reads. This is the
 * authoritative map the G6 gate audits for:
 *
 *   - **coverage**     — every live asset has ≥1 appropriate tool
 *   - **redundancy**   — no two tools share the same (asset, intent) pair
 *   - **orphans**      — no tool maps to a retired/changed asset shape
 *
 * Post-2a asset shape:
 *   T1 structural       chart_facts (planet/house/asc/panchanga/sp/dasha + 27 categories)
 *   L2.5 deterministic  l25_msr_signals  (3-column coefficient: deterministic_strength,
 *                                          verification_certainty, computed_salience)
 *                       l25_cdlm_links   (shared-factor graph — Gemini keeper)
 *                       l25_cgm_nodes    (graha + house nodes)
 *                       l25_cgm_edges    (rules + occupies edges)
 *                       l25_rm_resonances (structural_condition keys)
 *                       l25_ucn_sections  (computed_signature sha256 digest)
 *   L1.5 indexes        panchang_daily, ephemeris (date-keyed Phase 4A/4C)
 *   Ground truth        life_events (LEL)
 *   Corpus              rag_chunks (BPHS/Jaimini/KP/Tajaka)
 *                       multi_school_signals, school_convergence_index
 *                       remedial_codex (mantras + remedies)
 *   Sidecar             python-sidecar engines (muhurat, drishti, transit search, ...)
 *   Operational         mcp_audit_findings, traces, observatory, manifest
 *
 * Everything is (chart_id, ayanamsha_id)-keyed at the T1/L2.5 layer. Tools that
 * read those tables MUST declare an `ayanamsha_role` (canonical | kp | reference)
 * and MUST NOT read across roles. The audit asserts the no-cross-roles invariant.
 */

import type { DataDependency, AyanamshaRole } from './types'

/**
 * Tool surface — which channel(s) expose the canonical name.
 *  - `portal`  RETRIEVAL_TOOLS registry (Channel A — server-side route.ts)
 *  - `mcp`     platform-mcp/src/server.ts (Channel C — Claude Code IDE)
 *  - `both`    parity tool exposed on both channels under the same name
 */
export type ToolSurface = 'portal' | 'mcp' | 'both'

/**
 * Tool intent — coarse semantic verb. Used for redundancy detection:
 * two tools sharing the same (data_dependency, intent) pair are redundant.
 * Intents are deliberately coarse; fine-grained sub-intent disambiguation
 * lives in the tool description, not here.
 */
export type ToolIntent =
  | 'fact_lookup'        // parametric T1 chart_facts read
  | 'signal_query'       // MSR signal filter / aggregate
  | 'signal_state'       // signal state (lit/ripening/dormant) read
  | 'cdlm_link'          // CDLM shared-factor lookup
  | 'cgm_walk'           // CGM graph traversal / subgraph fetch
  | 'rm_lookup'          // RM resonance lookup
  | 'ucn_read'           // UCN digest / section read
  | 'panchang_daily'     // L1.5 panchang lookup
  | 'ephemeris_lookup'   // L1.5 ephemeris lookup
  | 'life_event'         // LEL ground-truth read
  | 'corpus_search'      // RAG vector / text search
  | 'classical_lookup'   // classical text targeted read
  | 'classical_attribution' // multi-school attribution lookup
  | 'convergence'        // school convergence index
  | 'multi_school_signal' // multi_school signals corpus
  | 'remedial_corpus'    // remedial codex / mantra search
  | 'transit_event'      // transit search (when does X happen?)
  | 'transit_natal'      // transit-to-natal window
  | 'eclipse_event'      // eclipse-specific transit
  | 'planet_war'         // graha yuddha
  | 'yoga_active'        // active yoga lookup
  | 'dasha_period'       // dasha schedule lookup
  | 'dasha_active'       // current dasha interpretation
  | 'dasha_predictions'  // classical MD/AD predictions
  | 'jaimini_chara'      // Jaimini Chara dasha
  | 'jaimini_drishti'    // Jaimini rashi drishti
  | 'jaimini_drekkana'   // Jaimini drekkana drishti
  | 'kp_ruling'          // KP ruling planets
  | 'kp_query'           // KP generic query (cusp/sublord)
  | 'varshphal'          // Varshaphala annual chart
  | 'tara_balam'         // Tara Bala lookup
  | 'chandra_balam'      // Chandra Bala lookup
  | 'muhurta'            // Muhurta finder
  | 'avastha'            // planet avastha
  | 'shadbala'           // shadbala roll-up
  | 'saham'              // sahams
  | 'divisional'         // raw divisional chart positions
  | 'divisional_career'  // D10 career
  | 'divisional_karma'   // D60 shashtiamsha
  | 'cross_varga_dignity' // CSI cross-divisional dignity
  | 'domain_report'      // domain-bundled report
  | 'pattern_register'   // pattern register
  | 'resonance_register' // resonance register
  | 'cluster_atlas'      // cluster atlas
  | 'contradiction_register' // contradiction register
  | 'temporal'           // temporal aggregation
  | 'timeline'           // chronological timeline merge
  | 'msr_aggregate'      // MSR aggregate (vs msr_sql parametric)
  | 'chart_summary'      // top-of-funnel chart summary
  | 'holistic_bundle'    // L2.5 bundle synthesizer
  | 'multi_school_bundle' // multi-school bundle synthesizer
  | 'asset_read'         // raw asset / classical_artifact read
  | 'asset_list'         // list known assets
  | 'manifest_list'      // list canonical artifact versions
  | 'manifest_query'     // manifest query (registry walk)
  | 'trace_lookup'       // get_trace / list_recent_queries
  | 'tool_health'        // tool health metrics
  | 'data_coverage'      // data coverage audit
  | 'log_prediction'     // write — log a prediction
  | 'record_outcome'     // write — outcome
  | 'flag_disagreement'  // write — disagreement

/**
 * Live asset id — the canonical id of each post-2a asset the audit walks.
 * If you retire an asset, drop its id here AND in EXPECTED_ASSETS below.
 */
export type LiveAssetId =
  // T1 structural (chart_id, ayanamsha_id)-keyed
  | 'chart_facts'
  // L2.5 deterministic (chart_id, ayanamsha_id)-keyed
  | 'l25_msr_signals'
  | 'l25_cdlm_links'
  | 'l25_cgm_nodes'
  | 'l25_cgm_edges'
  | 'l25_rm_resonances'
  | 'l25_ucn_sections'
  // L1.5 / L1 indexes
  | 'panchang_daily'
  | 'ephemeris'
  | 'life_events'
  // Corpus
  | 'rag_chunks'
  | 'multi_school_signals'
  | 'school_convergence_index'
  | 'remedial_codex'
  | 'classical_text'
  // Sidecar / engines
  | 'sidecar'
  // Operational
  | 'capability_manifest'
  | 'observatory'
  | 'mcp_audit'

/**
 * EXPECTED_ASSETS — the live asset portfolio the G6 audit walks for coverage.
 * Each entry declares the asset id and the ayanamsha-roles a tool may use to
 * read it. `null` in the roles list means "non-chart-binding" assets where
 * ayanamsha is N/A (corpus, classical text, sidecar, observability).
 */
export const EXPECTED_ASSETS: ReadonlyArray<{
  asset: LiveAssetId
  /** Acceptable ayanamsha_role(s) for tools that read this asset. */
  ayanamsha_roles: readonly AyanamshaRole[]
  /** Human-readable description for audit reports. */
  description: string
}> = [
  // T1 structural
  {
    asset: 'chart_facts',
    ayanamsha_roles: ['canonical', 'kp'],
    description: 'T1 structural facts — planet/house/asc/panchanga/sp/dasha + 27 categories (chart_id, ayanamsha_id)-keyed',
  },
  // L2.5 deterministic
  {
    asset: 'l25_msr_signals',
    ayanamsha_roles: ['canonical'],
    description: 'MSR signals with 3-column coefficient (deterministic_strength / verification_certainty / computed_salience)',
  },
  {
    asset: 'l25_cdlm_links',
    ayanamsha_roles: ['canonical'],
    description: 'CDLM shared-factor links — domains sharing planets/houses/sign-lord',
  },
  {
    asset: 'l25_cgm_nodes',
    ayanamsha_roles: ['canonical'],
    description: 'CGM graph nodes — graha + house nodes',
  },
  {
    asset: 'l25_cgm_edges',
    ayanamsha_roles: ['canonical'],
    description: 'CGM graph edges — rules + occupies edges',
  },
  {
    asset: 'l25_rm_resonances',
    ayanamsha_roles: ['canonical'],
    description: 'RM resonance structural_condition lookup keys',
  },
  {
    asset: 'l25_ucn_sections',
    ayanamsha_roles: ['canonical'],
    description: 'UCN computed_signature digest + signature_payload',
  },
  // L1.5 / L1 indexes
  {
    asset: 'panchang_daily',
    ayanamsha_roles: ['canonical'],
    description: 'Sunrise-anchored daily panchanga (L1.5)',
  },
  {
    asset: 'ephemeris',
    ayanamsha_roles: ['reference', 'canonical'],
    description: 'Date-indexed ephemeris (L1.5). Pure ephemeris reads are reference-frame; chart-overlaid transit reads (transit_natal) use canonical.',
  },
  {
    asset: 'life_events',
    ayanamsha_roles: [null, 'canonical'],
    description: 'LEL ground-truth life events. Raw LEL reads are non-chart-binding (null); timeline overlays use canonical to merge with active signals.',
  },
  // Corpus
  {
    asset: 'rag_chunks',
    ayanamsha_roles: [null],
    description: 'RAG corpus (BPHS / Jaimini / KP / Tajaka indexed)',
  },
  {
    asset: 'multi_school_signals',
    ayanamsha_roles: [null],
    description: 'Multi-school signal corpus (attribution per school)',
  },
  {
    asset: 'school_convergence_index',
    ayanamsha_roles: [null],
    description: 'School convergence index — claim ↔ school agreement',
  },
  {
    asset: 'remedial_codex',
    ayanamsha_roles: [null],
    description: 'Remedial codex — mantras + remedies corpus',
  },
  {
    asset: 'classical_text',
    ayanamsha_roles: [null],
    description: 'Classical text raw read (BPHS / Jaimini Sutram / KP Reader / Tajaka Neelakanthi)',
  },
  // Sidecar
  {
    asset: 'sidecar',
    ayanamsha_roles: ['canonical', 'reference'],
    description: 'Python sidecar engines (muhurat, drishti, transit search, ...)',
  },
  // Operational
  {
    asset: 'capability_manifest',
    ayanamsha_roles: [null],
    description: 'CAPABILITY_MANIFEST.json — canonical artifact catalog',
  },
  {
    asset: 'observatory',
    ayanamsha_roles: [null],
    description: 'Observatory traces + query history',
  },
  {
    asset: 'mcp_audit',
    ayanamsha_roles: [null],
    description: 'MCP audit findings + tool caveats + health metrics',
  },
] as const

/**
 * The reconciliation entry — single declarative source.
 *
 *   data_dependency  — the primary asset the tool serves (one of EXPECTED_ASSETS.asset)
 *   ayanamsha_role   — the engine frame the tool reads in
 *   intent           — the semantic verb (for redundancy detection)
 *   surface          — which channel(s) advertise the canonical_name
 *   description      — disambiguator (matches the live tool description)
 */
export interface ToolReconciliationEntry {
  canonical_name: string
  data_dependency: DataDependency
  /** Primary asset id (subset of LiveAssetId — the asset the audit treats as covered). */
  primary_asset: LiveAssetId
  /** Secondary assets the tool also reads (e.g. classical_lookup → rag_chunks + classical_text). */
  secondary_assets?: readonly LiveAssetId[]
  ayanamsha_role: AyanamshaRole
  intent: ToolIntent
  surface: ToolSurface
  description: string
  /** True if the tool requires chart_id in its input (per Gate G4). */
  per_chart: boolean
  /** True if this entry intentionally shares (asset, intent) with another tool (alias). */
  is_alias?: boolean
  /** Canonical alias target — when `is_alias` is true, the alias collapses to this name in redundancy detection. */
  alias_of?: string
}

/**
 * TOOL_METADATA — every live tool, exhaustively.
 *
 * INVARIANT: when a tool's data_dependency or ayanamsha_role changes, this
 * table is the place to update. The G6 test asserts:
 *   1. every canonical_name in either RETRIEVAL_TOOLS or MCP CATALOG has an entry
 *   2. every entry's primary_asset is in EXPECTED_ASSETS
 *   3. every entry's ayanamsha_role is acceptable for its primary_asset
 *   4. no two NON-ALIAS entries share the same (primary_asset, intent) pair
 *   5. every EXPECTED_ASSETS asset has ≥1 entry pointing at it
 */
export const TOOL_METADATA: readonly ToolReconciliationEntry[] = [
  // ─── Tier 1 / 2 — MCP super-endpoint + composite bundles ───
  {
    canonical_name: 'chart_summary',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    secondary_assets: ['l25_msr_signals', 'l25_ucn_sections'],
    ayanamsha_role: 'canonical',
    intent: 'chart_summary',
    surface: 'mcp',
    description: 'Top-of-funnel chart summary — single-call snapshot of asc/Moon/Sun/lagna-lord/current dasha + key MSR signals.',
    per_chart: true,
  },
  {
    canonical_name: 'holistic_bundle',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    secondary_assets: ['l25_cdlm_links', 'l25_cgm_nodes', 'l25_cgm_edges', 'l25_rm_resonances', 'l25_ucn_sections'],
    ayanamsha_role: 'canonical',
    intent: 'holistic_bundle',
    surface: 'mcp',
    description: 'L2.5 Whole-Chart-Read bundle — MSR + UCN + CDLM + CGM + RM in one call.',
    per_chart: true,
  },
  {
    canonical_name: 'multi_school_bundle',
    data_dependency: 'rag_chunks',
    primary_asset: 'multi_school_signals',
    secondary_assets: ['school_convergence_index', 'rag_chunks'],
    ayanamsha_role: null,
    intent: 'multi_school_bundle',
    surface: 'mcp',
    description: 'Multi-school triangulation bundle — claim resolved across schools with convergence index.',
    per_chart: false,
  },

  // ─── T1 chart_facts surface ───
  {
    canonical_name: 'query_chart_facts',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'fact_lookup',
    surface: 'both',
    description: 'Parametric chart_facts lookup over 27 categories. Surgical primitive.',
    per_chart: true,
  },
  {
    canonical_name: 'chart_facts_query',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'fact_lookup',
    surface: 'portal',
    description: 'Portal-native alias for query_chart_facts. Collapses to query_chart_facts in Wave-3.',
    per_chart: true,
    is_alias: true,
    alias_of: 'query_chart_facts',
  },
  {
    canonical_name: 'query_divisional_chart',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'divisional',
    surface: 'mcp',
    description: 'Raw divisional chart positions (D1–D60).',
    per_chart: true,
  },
  {
    canonical_name: 'divisional_query',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'divisional',
    surface: 'portal',
    description: 'Portal-native alias for query_divisional_chart.',
    per_chart: true,
    is_alias: true,
    alias_of: 'query_divisional_chart',
  },
  {
    canonical_name: 'cross_varga_dignity_query',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'cross_varga_dignity',
    surface: 'portal',
    description: 'CSI cross-divisional dignity surface.',
    per_chart: true,
  },
  {
    canonical_name: 'query_dasamsha_career',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'divisional_career',
    surface: 'both',
    description: 'D10 career indicator rules — yogas + raja-yoga D10 placements.',
    per_chart: true,
  },
  {
    canonical_name: 'query_shashtiamsha',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'divisional_karma',
    surface: 'both',
    description: 'D60 Shashtiamsha karma pada analysis.',
    per_chart: true,
  },
  {
    canonical_name: 'get_planet_avastha',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'avastha',
    surface: 'both',
    description: 'Planet avastha (experiential state) lookup with 3-step fallback.',
    per_chart: true,
  },
  {
    canonical_name: 'get_shadbala_full',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'shadbala',
    surface: 'both',
    description: 'Full Shadbala 6-component roll-up with classical minimum rupa checks.',
    per_chart: true,
  },
  {
    canonical_name: 'saham_query',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'saham',
    surface: 'portal',
    description: 'Sahams lookup (Sun-derived sensitive points).',
    per_chart: true,
  },
  {
    canonical_name: 'query_drekkana_drishti',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'jaimini_drekkana',
    surface: 'both',
    description: 'Jaimini Drekkana Drishti aspects from chart_facts.',
    per_chart: true,
  },
  {
    canonical_name: 'query_jaimini_drishti',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'jaimini_drishti',
    surface: 'both',
    description: 'Jaimini rashi drishti — sidecar-backed graph over chart_facts.',
    per_chart: true,
  },
  {
    canonical_name: 'query_v7_additions',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'fact_lookup',
    surface: 'portal',
    description: 'V7 additions — sidecar wrapper for orphaned endpoints (legacy).',
    per_chart: true,
    is_alias: true,
    alias_of: 'query_chart_facts',
  },

  // ─── L2.5 MSR / signals ───
  {
    canonical_name: 'msr_sql',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'signal_query',
    surface: 'both',
    description: 'Parametric MSR signals SQL filter (post-2a 3-column coefficient).',
    per_chart: true,
  },
  {
    canonical_name: 'query_signals',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'signal_query',
    surface: 'mcp',
    description: 'MCP signals query — surfaces deterministic coefficient + verification certainty.',
    per_chart: true,
    is_alias: true,
    alias_of: 'msr_sql',
  },
  {
    canonical_name: 'query_msr_aggregate',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'msr_aggregate',
    surface: 'portal',
    description: 'MSR aggregate counts + grouped facets.',
    per_chart: true,
  },
  {
    canonical_name: 'query_signal_state',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'signal_state',
    surface: 'both',
    description: 'Signal state (lit/ripening/dormant) read.',
    per_chart: true,
  },
  {
    canonical_name: 'pattern_register',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'pattern_register',
    surface: 'both',
    description: 'Pattern register lookup over MSR signal patterns.',
    per_chart: true,
  },
  {
    canonical_name: 'resonance_register',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'resonance_register',
    surface: 'both',
    description: 'Resonance register lookup over MSR signal resonances.',
    per_chart: true,
  },
  {
    canonical_name: 'cluster_atlas',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'cluster_atlas',
    surface: 'both',
    description: 'Cluster atlas — domain clusters over MSR signals.',
    per_chart: true,
  },
  {
    canonical_name: 'contradiction_register',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    ayanamsha_role: 'canonical',
    intent: 'contradiction_register',
    surface: 'both',
    description: 'Contradiction register — surface contradictions across signals.',
    per_chart: true,
  },

  // ─── L2.5 CDLM / CGM / RM / UCN ───
  {
    canonical_name: 'query_cdlm_lookup',
    data_dependency: 'cdlm',
    primary_asset: 'l25_cdlm_links',
    ayanamsha_role: 'canonical',
    intent: 'cdlm_link',
    surface: 'both',
    description: 'CDLM shared-factor lookup — domain pairs sharing planets/houses/signs (deterministic post-2a).',
    per_chart: true,
  },
  {
    canonical_name: 'cgm_graph_walk',
    data_dependency: 'cgm',
    primary_asset: 'l25_cgm_nodes',
    secondary_assets: ['l25_cgm_edges'],
    ayanamsha_role: 'canonical',
    intent: 'cgm_walk',
    surface: 'portal',
    description: 'BFS traversal over CGM graph (l25_cgm_nodes + l25_cgm_edges).',
    per_chart: true,
  },
  {
    canonical_name: 'get_cgm_subgraph',
    data_dependency: 'cgm',
    primary_asset: 'l25_cgm_nodes',
    secondary_assets: ['l25_cgm_edges'],
    ayanamsha_role: 'canonical',
    intent: 'cgm_walk',
    surface: 'mcp',
    description: 'CGM subgraph fetch — seed-anchored neighborhood over graph nodes/edges.',
    per_chart: true,
    is_alias: true,
    alias_of: 'cgm_graph_walk',
  },
  {
    canonical_name: 'query_rm_walk',
    data_dependency: 'rm',
    primary_asset: 'l25_rm_resonances',
    ayanamsha_role: 'canonical',
    intent: 'rm_lookup',
    surface: 'both',
    description: 'RM resonance walk by structural_condition key.',
    per_chart: true,
  },
  {
    canonical_name: 'query_ucn_walk',
    data_dependency: 'ucn',
    primary_asset: 'l25_ucn_sections',
    ayanamsha_role: 'canonical',
    intent: 'ucn_read',
    surface: 'both',
    description: 'UCN walk — read computed_signature + signature_payload sections.',
    per_chart: true,
  },

  // ─── L1.5 indexes ───
  {
    canonical_name: 'query_panchanga',
    data_dependency: 'panchang_daily',
    primary_asset: 'panchang_daily',
    ayanamsha_role: 'canonical',
    intent: 'panchang_daily',
    surface: 'both',
    description: 'Sunrise-anchored daily panchanga lookup (5 limbs + enrichment). per_chart for native overlay + observer location default.',
    per_chart: true,
  },
  {
    canonical_name: 'query_ephemeris',
    data_dependency: 'ephemeris',
    primary_asset: 'ephemeris',
    ayanamsha_role: 'reference',
    intent: 'ephemeris_lookup',
    surface: 'both',
    description: 'Date-indexed ephemeris lookup.',
    per_chart: false,
  },
  {
    canonical_name: 'lel_query',
    data_dependency: 'lel',
    primary_asset: 'life_events',
    ayanamsha_role: null,
    intent: 'life_event',
    surface: 'both',
    description: 'LEL ground-truth life events lookup — chart-scoped (chart_id required) since migration 423.',
    per_chart: true,
  },

  // ─── Dasha + Jaimini ───
  {
    canonical_name: 'query_dasha_periods',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'dasha_period',
    surface: 'both',
    description: 'Surgical dasha schedule lookup — MD/AD/PD by date.',
    per_chart: true,
  },
  {
    canonical_name: 'interpret_current_dasha',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    secondary_assets: ['l25_msr_signals'],
    ayanamsha_role: 'canonical',
    intent: 'dasha_active',
    surface: 'mcp',
    description: 'Current dasha interpretation — bundle of active MD/AD + MSR signals.',
    per_chart: true,
  },
  {
    canonical_name: 'query_planetary_period_predictions',
    data_dependency: 'rag_chunks',
    primary_asset: 'rag_chunks',
    secondary_assets: ['classical_text'],
    ayanamsha_role: null,
    intent: 'dasha_predictions',
    surface: 'both',
    description: 'Classical MD/AD prediction recipes via vector_search + classical text merge.',
    per_chart: false,
  },
  {
    canonical_name: 'query_jaimini_chara_dasha',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    ayanamsha_role: 'canonical',
    intent: 'jaimini_chara',
    surface: 'both',
    description: 'Jaimini Chara Dasha active period + full timeline.',
    per_chart: true,
  },
  {
    canonical_name: 'jaimini_chara_dasha',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    ayanamsha_role: 'canonical',
    intent: 'jaimini_chara',
    surface: 'portal',
    description: 'Portal-native alias for query_jaimini_chara_dasha (active period).',
    per_chart: true,
    is_alias: true,
    alias_of: 'query_jaimini_chara_dasha',
  },
  {
    canonical_name: 'jaimini_chara_dasha_full',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    ayanamsha_role: 'canonical',
    intent: 'jaimini_chara',
    surface: 'portal',
    description: 'Portal-native alias for query_jaimini_chara_dasha (full timeline).',
    per_chart: true,
    is_alias: true,
    alias_of: 'query_jaimini_chara_dasha',
  },

  // ─── Varshaphala ───
  // WP-1.3(h)/LCA-12 §7.3: kp_query + query_kp_ruling_planets PHANTOM DROPPED from the
  // contract surface — no KP engine backs them (migration 024_kp_sublords archived; no
  // registry capability; removed from the MCP surgical whitelist by WP-1.7). Advertising
  // them here made the contract surface disagree with what actually resolves. Re-add only
  // when a real KP engine is built + registered.
  {
    canonical_name: 'query_varshphal',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'varshphal',
    surface: 'mcp',
    description: 'Varshaphala annual chart lookup — varshesha + muntha + year-lord.',
    per_chart: true,
  },
  {
    canonical_name: 'query_varshaphala',
    data_dependency: 'chart_facts',
    primary_asset: 'chart_facts',
    ayanamsha_role: 'canonical',
    intent: 'varshphal',
    surface: 'portal',
    description: 'Portal-native alias for query_varshphal.',
    per_chart: true,
    is_alias: true,
    alias_of: 'query_varshphal',
  },

  // ─── Transits + events ───
  {
    canonical_name: 'query_transit_event',
    data_dependency: 'ephemeris',
    primary_asset: 'ephemeris',
    ayanamsha_role: 'reference',
    intent: 'transit_event',
    surface: 'both',
    description: 'Transit event search — when does X transit Y?',
    per_chart: false,
  },
  {
    canonical_name: 'query_transits_over_natal',
    data_dependency: 'ephemeris',
    primary_asset: 'ephemeris',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'transit_natal',
    surface: 'both',
    description: 'Transit-to-natal windows — when does transit X aspect natal Y?',
    per_chart: true,
  },
  {
    canonical_name: 'query_eclipse_transits',
    data_dependency: 'ephemeris',
    primary_asset: 'ephemeris',
    ayanamsha_role: 'reference',
    intent: 'eclipse_event',
    surface: 'both',
    description: 'Eclipse-specific transit detection.',
    per_chart: false,
  },
  {
    canonical_name: 'query_planet_war',
    data_dependency: 'ephemeris',
    primary_asset: 'ephemeris',
    ayanamsha_role: 'reference',
    intent: 'planet_war',
    surface: 'both',
    description: 'Graha Yuddha — planetary war detection over ephemeris.',
    per_chart: false,
  },
  {
    canonical_name: 'query_yogas_active_now',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    secondary_assets: ['ephemeris'],
    ayanamsha_role: 'canonical',
    intent: 'yoga_active',
    surface: 'both',
    description: 'Active yoga lookup — which yogas are activated by current transits/dasha.',
    per_chart: true,
  },
  {
    canonical_name: 'temporal',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    secondary_assets: ['ephemeris'],
    ayanamsha_role: 'canonical',
    intent: 'temporal',
    surface: 'both',
    description: 'Temporal aggregation — signal activation over time windows.',
    per_chart: true,
  },
  // WP-1.3(h)/LCA-12 §7.3: timeline_query PHANTOM DROPPED from the contract surface — no
  // LIFETIME_TIMELINE serving path exists (no registry capability; removed from the MCP
  // surgical whitelist by WP-1.7). Chronological/dasha-arc needs are served by the real
  // 'temporal' (L3/query_temporal_activation) + lel_query + get_dashas capabilities.

  // ─── Muhurta + Tara/Chandra Bala ───
  {
    canonical_name: 'muhurta_finder',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['panchang_daily'],
    ayanamsha_role: 'canonical',
    intent: 'muhurta',
    surface: 'both',
    description: 'Muhurta finder with native overlay — sidecar-backed Muhurta search.',
    per_chart: true,
  },
  {
    canonical_name: 'query_muhurat',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['panchang_daily'],
    ayanamsha_role: 'canonical',
    intent: 'muhurta',
    surface: 'portal',
    description: 'Portal-native alias for muhurta_finder.',
    per_chart: true,
    is_alias: true,
    alias_of: 'muhurta_finder',
  },
  {
    canonical_name: 'tara_balam_for_native',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'tara_balam',
    surface: 'both',
    description: 'Tara Bala (lunar mansion strength) for native.',
    per_chart: true,
  },
  {
    canonical_name: 'query_tara_balam',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'tara_balam',
    surface: 'portal',
    description: 'Portal-native alias for tara_balam_for_native.',
    per_chart: true,
    is_alias: true,
    alias_of: 'tara_balam_for_native',
  },
  {
    canonical_name: 'chandra_balam_for_native',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'chandra_balam',
    surface: 'both',
    description: 'Chandra Bala (Moon strength) for native.',
    per_chart: true,
  },
  {
    canonical_name: 'query_chandra_balam',
    data_dependency: 'sidecar',
    primary_asset: 'sidecar',
    secondary_assets: ['chart_facts'],
    ayanamsha_role: 'canonical',
    intent: 'chandra_balam',
    surface: 'portal',
    description: 'Portal-native alias for chandra_balam_for_native.',
    per_chart: true,
    is_alias: true,
    alias_of: 'chandra_balam_for_native',
  },

  // ─── Corpus / classical ───
  {
    canonical_name: 'vector_search',
    data_dependency: 'rag_chunks',
    primary_asset: 'rag_chunks',
    ayanamsha_role: null,
    intent: 'corpus_search',
    surface: 'both',
    description: 'Vector search over RAG corpus (BPHS / Jaimini / KP / Tajaka).',
    per_chart: false,
  },
  {
    canonical_name: 'read_classical_text',
    data_dependency: 'classical_text',
    primary_asset: 'classical_text',
    ayanamsha_role: null,
    intent: 'classical_lookup',
    surface: 'mcp',
    description: 'Classical text targeted read (verse/section level).',
    per_chart: false,
  },
  {
    canonical_name: 'classical_text_search',
    data_dependency: 'rag_chunks',
    primary_asset: 'rag_chunks',
    secondary_assets: ['classical_text'],
    ayanamsha_role: null,
    intent: 'classical_lookup',
    surface: 'portal',
    description: 'Classical text search — RAG retrieval over indexed classical corpus.',
    per_chart: false,
    is_alias: true,
    alias_of: 'read_classical_text',
  },
  {
    canonical_name: 'classical_attribution_lookup',
    data_dependency: 'rag_chunks',
    primary_asset: 'multi_school_signals',
    secondary_assets: ['rag_chunks'],
    ayanamsha_role: null,
    intent: 'classical_attribution',
    surface: 'portal',
    description: 'Classical attribution lookup — which school claims which signal.',
    per_chart: false,
  },
  {
    canonical_name: 'cross_school_lookup',
    data_dependency: 'rag_chunks',
    primary_asset: 'multi_school_signals',
    secondary_assets: ['school_convergence_index'],
    ayanamsha_role: null,
    intent: 'classical_attribution',
    surface: 'mcp',
    description: 'Cross-school lookup — claim resolved across BPHS / Jaimini / KP / Tajaka.',
    per_chart: false,
    is_alias: true,
    alias_of: 'classical_attribution_lookup',
  },
  {
    canonical_name: 'multi_school_signal_lookup',
    data_dependency: 'rag_chunks',
    primary_asset: 'multi_school_signals',
    ayanamsha_role: null,
    intent: 'multi_school_signal',
    surface: 'portal',
    description: 'Multi-school signal lookup corpus — claim → school × signal mapping.',
    per_chart: false,
  },
  {
    canonical_name: 'convergence_score_lookup',
    data_dependency: 'rag_chunks',
    primary_asset: 'school_convergence_index',
    ayanamsha_role: null,
    intent: 'convergence',
    surface: 'portal',
    description: 'School convergence index — agreement score per claim.',
    per_chart: false,
  },

  // ─── Remedial ───
  {
    canonical_name: 'remedial_codex_query',
    data_dependency: 'rag_chunks',
    primary_asset: 'remedial_codex',
    ayanamsha_role: null,
    intent: 'remedial_corpus',
    surface: 'portal',
    description: 'Remedial codex search — mantras + remedies corpus.',
    per_chart: false,
  },
  {
    canonical_name: 'query_remedial_mantras',
    data_dependency: 'rag_chunks',
    primary_asset: 'remedial_codex',
    ayanamsha_role: null,
    intent: 'remedial_corpus',
    surface: 'mcp',
    description: 'Remedial mantra corpus search (planet/deity/affliction).',
    per_chart: false,
    is_alias: true,
    alias_of: 'remedial_codex_query',
  },
  {
    canonical_name: 'query_remedies_prescribed',
    data_dependency: 'rag_chunks',
    primary_asset: 'remedial_codex',
    ayanamsha_role: null,
    intent: 'remedial_corpus',
    surface: 'both',
    description: 'Remedial prescription cross-reference from remedies table.',
    per_chart: true,
    is_alias: true,
    alias_of: 'remedial_codex_query',
  },

  // ─── Reports + bundles ───
  {
    canonical_name: 'domain_report_query',
    data_dependency: 'msr',
    primary_asset: 'l25_msr_signals',
    secondary_assets: ['l25_cdlm_links', 'l25_rm_resonances'],
    ayanamsha_role: 'canonical',
    intent: 'domain_report',
    surface: 'portal',
    description: 'Domain-bundled report — signals + CDLM + RM for a single domain.',
    per_chart: true,
  },

  // ─── Asset / manifest / observability ───
  {
    canonical_name: 'read_asset',
    data_dependency: 'classical_text',
    primary_asset: 'capability_manifest',
    secondary_assets: ['classical_text'],
    ayanamsha_role: null,
    intent: 'asset_read',
    surface: 'mcp',
    description: 'Raw asset read by canonical_id (manifest-aware).',
    per_chart: false,
  },
  {
    canonical_name: 'list_assets',
    data_dependency: 'none',
    primary_asset: 'capability_manifest',
    ayanamsha_role: null,
    intent: 'asset_list',
    surface: 'mcp',
    description: 'List all assets in the capability manifest.',
    per_chart: false,
  },
  {
    canonical_name: 'list_canonical_artifact_versions',
    data_dependency: 'none',
    primary_asset: 'capability_manifest',
    ayanamsha_role: null,
    intent: 'manifest_list',
    surface: 'mcp',
    description: 'List canonical artifact versions from the manifest.',
    per_chart: false,
  },
  {
    canonical_name: 'manifest_query',
    data_dependency: 'none',
    primary_asset: 'capability_manifest',
    ayanamsha_role: null,
    intent: 'manifest_query',
    surface: 'portal',
    description: 'Manifest query — registry walk over capability manifest entries.',
    per_chart: false,
  },
  {
    canonical_name: 'get_trace',
    data_dependency: 'observatory',
    primary_asset: 'observatory',
    ayanamsha_role: null,
    intent: 'trace_lookup',
    surface: 'mcp',
    description: 'Get a specific query trace by id.',
    per_chart: false,
  },
  {
    canonical_name: 'list_recent_queries',
    data_dependency: 'observatory',
    primary_asset: 'observatory',
    ayanamsha_role: null,
    intent: 'trace_lookup',
    surface: 'mcp',
    description: 'List recent queries (observability).',
    per_chart: false,
    is_alias: true,
    alias_of: 'get_trace',
  },
  {
    canonical_name: 'tool_health',
    data_dependency: 'observatory',
    primary_asset: 'mcp_audit',
    secondary_assets: ['observatory'],
    ayanamsha_role: null,
    intent: 'tool_health',
    surface: 'mcp',
    description: 'Aggregate tool health metrics over the last N hours.',
    per_chart: false,
  },
  {
    canonical_name: 'data_coverage',
    data_dependency: 'observatory',
    primary_asset: 'mcp_audit',
    secondary_assets: ['observatory'],
    ayanamsha_role: null,
    intent: 'data_coverage',
    surface: 'mcp',
    description: 'Data coverage audit — expected vs actual per tool/category + asset coverage map.',
    per_chart: false,
  },

  // ─── Write tools ───
  {
    canonical_name: 'log_prediction',
    data_dependency: 'observatory',
    primary_asset: 'observatory',
    ayanamsha_role: null,
    intent: 'log_prediction',
    surface: 'mcp',
    description: 'Log a prospective prediction.',
    per_chart: false,
  },
  {
    canonical_name: 'record_outcome',
    data_dependency: 'observatory',
    primary_asset: 'observatory',
    ayanamsha_role: null,
    intent: 'record_outcome',
    surface: 'mcp',
    description: 'Record an observed outcome against a prior prediction.',
    per_chart: false,
  },
  {
    canonical_name: 'flag_disagreement',
    data_dependency: 'observatory',
    primary_asset: 'observatory',
    ayanamsha_role: null,
    intent: 'flag_disagreement',
    surface: 'mcp',
    description: 'Flag a disagreement (cross-school / cross-tool / cross-session).',
    per_chart: false,
  },
] as const

/** Convenience lookup by canonical_name. */
export const TOOL_METADATA_BY_NAME = new Map<string, ToolReconciliationEntry>(
  TOOL_METADATA.map(t => [t.canonical_name, t])
)

/** Convenience: every canonical_name in the table. */
export const TOOL_METADATA_NAMES: readonly string[] = TOOL_METADATA.map(t => t.canonical_name)

/** Convenience: get the metadata entry for a tool. */
export function getToolMetadata(canonical_name: string): ToolReconciliationEntry | undefined {
  return TOOL_METADATA_BY_NAME.get(canonical_name)
}

// ─────────────────────────────────────────────────────────────────────────────
// Audit helpers — the G6_tool_coverage gate.
// ─────────────────────────────────────────────────────────────────────────────

export interface CoverageReport {
  total_assets: number
  total_tools: number
  /** Assets with at least one tool pointing at them. */
  covered_assets: LiveAssetId[]
  /** Assets with NO tool pointing at them. */
  uncovered_assets: LiveAssetId[]
  /** Tools whose primary_asset is not in EXPECTED_ASSETS — orphans. */
  orphaned_tools: string[]
  /** Pairs (primary_asset, intent) shared by multiple NON-ALIAS tools. */
  redundancies: Array<{ primary_asset: LiveAssetId; intent: ToolIntent; tools: string[] }>
  /** Ayanamsha-role mismatches — tool reads asset under a role the asset disallows. */
  ayanamsha_mismatches: Array<{ tool: string; primary_asset: LiveAssetId; ayanamsha_role: AyanamshaRole; allowed_roles: readonly AyanamshaRole[] }>
}

/**
 * audit() — compute the full coverage report.
 *
 * Walks TOOL_METADATA against EXPECTED_ASSETS and returns the four-axis report.
 * The G6 gate asserts:
 *   - uncovered_assets.length === 0
 *   - orphaned_tools.length === 0
 *   - redundancies.length === 0
 *   - ayanamsha_mismatches.length === 0
 */
export function auditToolAssetReconciliation(): CoverageReport {
  const expectedAssetIds = new Set<LiveAssetId>(EXPECTED_ASSETS.map(a => a.asset))
  const expectedAssetMap = new Map<LiveAssetId, typeof EXPECTED_ASSETS[number]>(
    EXPECTED_ASSETS.map(a => [a.asset, a])
  )

  // Coverage: which assets are touched by ≥1 tool's primary_asset
  const coveredSet = new Set<LiveAssetId>()
  const orphans: string[] = []
  const ayanamshaMismatches: CoverageReport['ayanamsha_mismatches'] = []

  for (const t of TOOL_METADATA) {
    if (!expectedAssetIds.has(t.primary_asset)) {
      orphans.push(t.canonical_name)
      continue
    }
    coveredSet.add(t.primary_asset)
    // also count secondary_assets toward coverage
    for (const s of t.secondary_assets ?? []) {
      if (expectedAssetIds.has(s)) coveredSet.add(s)
    }
    // ayanamsha-role validation against asset's allowed roles
    const meta = expectedAssetMap.get(t.primary_asset)
    if (meta && !meta.ayanamsha_roles.includes(t.ayanamsha_role)) {
      ayanamshaMismatches.push({
        tool: t.canonical_name,
        primary_asset: t.primary_asset,
        ayanamsha_role: t.ayanamsha_role,
        allowed_roles: meta.ayanamsha_roles,
      })
    }
  }

  const uncovered = EXPECTED_ASSETS.map(a => a.asset).filter(a => !coveredSet.has(a))

  // Redundancy: group NON-ALIAS tools by (primary_asset, intent); >1 ⇒ redundant.
  const buckets = new Map<string, ToolReconciliationEntry[]>()
  for (const t of TOOL_METADATA) {
    if (t.is_alias) continue // aliases are explicit collapses — not redundant
    const key = `${t.primary_asset}::${t.intent}`
    const arr = buckets.get(key) ?? []
    arr.push(t)
    buckets.set(key, arr)
  }
  const redundancies: CoverageReport['redundancies'] = []
  for (const [key, tools] of buckets) {
    if (tools.length > 1) {
      const [primary_asset, intent] = key.split('::') as [LiveAssetId, ToolIntent]
      redundancies.push({
        primary_asset,
        intent,
        tools: tools.map(t => t.canonical_name),
      })
    }
  }

  return {
    total_assets: EXPECTED_ASSETS.length,
    total_tools: TOOL_METADATA.length,
    covered_assets: [...coveredSet].sort(),
    uncovered_assets: uncovered.sort(),
    orphaned_tools: orphans.sort(),
    redundancies,
    ayanamsha_mismatches: ayanamshaMismatches,
  }
}

/** Return TRUE if the audit reports zero issues across all four axes. */
export function isReconciliationGreen(): boolean {
  const r = auditToolAssetReconciliation()
  return (
    r.uncovered_assets.length === 0 &&
    r.orphaned_tools.length === 0 &&
    r.redundancies.length === 0 &&
    r.ayanamsha_mismatches.length === 0
  )
}
