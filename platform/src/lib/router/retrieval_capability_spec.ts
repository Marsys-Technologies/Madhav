/**
 * Retrieval Capability Spec (RCS) — BHISMA Stream 2 §4.1
 *
 * A compact, machine-readable description of every retrieval tool the LLM-first
 * planner can call. The planner reads this spec at every plan() invocation and
 * uses it to decide WHICH tools to call and WHAT parameters to pass.
 *
 * The spec is the planner's *only* knowledge of what data exists in the corpus —
 * keep entries accurate, current, and grounded in the actual tool implementations
 * under `platform/src/lib/retrieve/`. When a tool's params change, this file is
 * the matching pair to update.
 *
 * Source of truth for tool implementations: platform/src/lib/retrieve/index.ts
 * (RETRIEVAL_TOOLS registry, 18 tools as of 2026-05-10 — VARGA-ETL-FULL-S1-CPA
 * added cross_varga_dignity_query for the §3.15 CSI ledger).
 */

export type CostTier = 'low' | 'medium' | 'high'

export interface RetrievalCapabilityEntry {
  /** Exact tool name as registered in RETRIEVAL_TOOLS. */
  tool_name: string
  /** What this tool retrieves, in 1–2 sentences. */
  description: string
  /** What schema / data surface the tool reads. Layer + main fields. */
  data_surface: string
  /** Human-readable param list with types. The planner emits params in this shape. */
  supported_params: string
  /** 3–5 example query patterns showing optimal usage. */
  optimal_patterns: string[]
  /** Relative token cost: low (<2k tokens typical), medium (2–10k), high (>10k). */
  cost_tier: CostTier
  /** True if this tool needs dasha or transit context to be useful. */
  requires_temporal: boolean
}

// ────────────────────────────────────────────────────────────────────────────
// L2.5 Synthesis-layer SQL tools
// ────────────────────────────────────────────────────────────────────────────

const msr_sql: RetrievalCapabilityEntry = {
  tool_name: 'msr_sql',
  description:
    'Primary signal retrieval from the Master Signal Register (MSR v3.0, 499 signals). Each signal carries a forensic claim, source citations, confidence, and significance score. Always available; the workhorse of every interpretive query.',
  data_surface:
    'L2.5 — table msr_signals: signal_id (SIG.MSR.NNN), title, forensic_claim, sources[], confidence, significance, domains[], planets[], houses[], dasha_activation[], temporal_window.',
  supported_params:
    '{ planets?: string[]; houses?: number[]; domains?: string[]; signal_ids?: string[]; min_significance?: number (0–1); limit?: number (default 20); keyword?: string; dasha_activation?: string[] }',
  optimal_patterns: [
    'Career interpretation: {domains:["career"], min_significance:0.7, limit:25}',
    'Planet drill-down: {planets:["Saturn"], min_significance:0.6, limit:30}',
    'Specific signal: {signal_ids:["SIG.MSR.142","SIG.MSR.207"]}',
    'Cross-domain: {domains:["career","relationships"], min_significance:0.75, limit:40}',
    'Keyword: {keyword:"vipareeta raja yoga", limit:10}',
  ],
  cost_tier: 'medium',
  requires_temporal: false,
}

const pattern_register: RetrievalCapabilityEntry = {
  tool_name: 'pattern_register',
  description:
    'Named chart patterns (yogas, planetary configurations, structural motifs) from PATTERN_REGISTER_v1_0. Each pattern is named, scored, and linked to the signals it activates.',
  data_surface:
    'L2.5 — table patterns: pattern_id (PAT.NNN), name, description, member_planets[], strength, supporting_signals[], domains[].',
  supported_params:
    '{ pattern_ids?: string[]; planets?: string[]; min_strength?: number (0–1); domains?: string[]; limit?: number (default 15) }',
  optimal_patterns: [
    'Holistic discovery: {min_strength:0.7, limit:20}',
    'Planet-anchored: {planets:["Jupiter","Venus"], min_strength:0.6}',
    'Specific yoga: {pattern_ids:["PAT.001","PAT.014"]}',
    'Domain patterns: {domains:["wealth"], min_strength:0.5}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const resonance_register: RetrievalCapabilityEntry = {
  tool_name: 'resonance_register',
  description:
    'Cross-signal resonances — places where two or more MSR signals reinforce each other. Use when the query asks about confluence, amplification, or thematic clustering.',
  data_surface:
    'L2.5 — table resonances: resonance_id (RES.NNN), member_signal_ids[], strength, theme, supports[], contradicts[].',
  supported_params:
    '{ resonance_ids?: string[]; signal_ids?: string[]; min_strength?: number; theme?: string; limit?: number (default 10) }',
  optimal_patterns: [
    'Confluence around a theme: {theme:"public_recognition", min_strength:0.7}',
    'Anchored to a signal: {signal_ids:["SIG.MSR.142"], min_strength:0.6}',
    'High-strength only: {min_strength:0.8, limit:8}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const cluster_atlas: RetrievalCapabilityEntry = {
  tool_name: 'cluster_atlas',
  description:
    'Pattern clusters from CLUSTER_ATLAS — the meta-layer above PATTERN_REGISTER showing how patterns group into recognisable life-shapes. Required for discovery and cross_native queries.',
  data_surface:
    'L2.5 — table clusters: cluster_id (CLU.NNN), name, member_pattern_ids[], dominant_themes[], rarity_score (0–1).',
  supported_params:
    '{ cluster_ids?: string[]; min_rarity?: number; theme?: string; limit?: number (default 10) }',
  optimal_patterns: [
    'Discovery: {min_rarity:0.7, limit:15}',
    'Theme drill: {theme:"renunciation_arc"}',
    'Specific: {cluster_ids:["CLU.003","CLU.008"]}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const contradiction_register: RetrievalCapabilityEntry = {
  tool_name: 'contradiction_register',
  description:
    'Known contradictions across the chart — places where two signals or patterns push in opposite directions. Essential for cross_domain and holistic queries; surfacing tension is the point.',
  data_surface:
    'L2.5 — table contradictions: contradiction_id (CONT.NNN), tension_summary, signal_a_id, signal_b_id, severity (0–1), domains[], resolution_hint.',
  supported_params:
    '{ contradiction_ids?: string[]; signal_ids?: string[]; domains?: string[]; min_severity?: number; limit?: number (default 12) }',
  optimal_patterns: [
    'Cross-domain tension: {domains:["career","relationships"], min_severity:0.6}',
    'Anchored: {signal_ids:["SIG.MSR.142"], min_severity:0.5}',
    'High-severity sweep: {min_severity:0.75, limit:10}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const temporal: RetrievalCapabilityEntry = {
  tool_name: 'temporal',
  description:
    'Time-indexed dasha and transit lookups (Vimshottari MD/AD/PD chains, Saturn-over-Moon Sade Sati phases, eclipses, retrogrades, multi-day transit windows). The mandatory tool for predictive queries.',
  data_surface:
    'L1 — ephemeris_daily (660K rows), eclipses, retrogrades, sade_sati_phases tables; v1.1 sidecars: dasha_chain, sade_sati_query, eclipse_query, retrograde_query.',
  supported_params:
    '{ time_window?: {start: ISO_date, end: ISO_date}; dasha_context_required?: boolean; sade_sati_query?: boolean; eclipse_query?: boolean; retrograde_query?: boolean; retrograde_planet?: string }',
  optimal_patterns: [
    'Predictive question: {time_window:{start:"2026-05-01",end:"2028-12-31"}, dasha_context_required:true}',
    'Sade Sati check: {sade_sati_query:true}',
    'Eclipse window: {eclipse_query:true, time_window:{start:"2026-01-01",end:"2026-12-31"}}',
    'Retrograde planet: {retrograde_query:true, retrograde_planet:"Mercury"}',
    'Pure dasha chain on date: {dasha_context_required:true, time_window:{start:"2026-05-01",end:"2026-05-01"}}',
  ],
  cost_tier: 'medium',
  requires_temporal: true,
}

const query_msr_aggregate: RetrievalCapabilityEntry = {
  tool_name: 'query_msr_aggregate',
  description:
    'Cross-chart MSR aggregation — counts and rollups across multiple charts. Required for cross_native research queries ("across charts with similar Saturn placements, what patterns are common?").',
  data_surface:
    'L2.5 — aggregated views over msr_signals × charts. Returns counts, distributions, and signal-prevalence statistics.',
  supported_params:
    '{ planets?: string[]; houses?: number[]; nakshatras?: string[]; domains?: string[]; min_significance?: number; group_by?: "domain"|"planet"|"house"|"nakshatra"; limit?: number (default 25) }',
  optimal_patterns: [
    'Saturn placements: {planets:["Saturn"], group_by:"house", limit:12}',
    'Nakshatra cohorts: {nakshatras:["Hasta","Pushya"], group_by:"domain"}',
    'Domain prevalence: {domains:["career"], min_significance:0.7, group_by:"planet"}',
  ],
  cost_tier: 'medium',
  requires_temporal: false,
}

// ────────────────────────────────────────────────────────────────────────────
// L2.5 Graph + semantic tools
// ────────────────────────────────────────────────────────────────────────────

const cgm_graph_walk: RetrievalCapabilityEntry = {
  tool_name: 'cgm_graph_walk',
  description:
    'Traverse the Chart Graph Model (CGM v9.0) from seed nodes outward via typed edges (DISPOSITED_BY, NAKSHATRA_LORD_IS, ASPECTS_*, SUPPORTS, CONTRADICTS, YOGA_MEMBERSHIP, DASHA_ACTIVATION, DIVISIONAL_CONFIRMATION). Use whenever the query names specific chart entities and you want to surface their relational neighbourhood.',
  data_surface:
    'L2.5 — cgm_nodes (PLN/HSE/SGN/NAK/YOG/KRK/SEN/DSH/DVS/UCN/KARAKA prefixes) + cgm_edges (typed). Returns a sub-graph: nodes + edges within depth.',
  supported_params:
    '{ seeds: string[] (CGM node IDs, e.g. ["PLN.SATURN","HSE.10"]); depth?: number (1–5, default 3); edge_types?: string[] (filter; empty = all); max_nodes?: number (default 50) }',
  optimal_patterns: [
    'Planet ego-net: {seeds:["PLN.SATURN"], depth:2}',
    'Dispositor chain: {seeds:["PLN.MERCURY"], depth:5, edge_types:["DISPOSITED_BY"]}',
    'House neighbourhood: {seeds:["HSE.10","HSE.7"], depth:2}',
    'Aspect web of Mars: {seeds:["PLN.MARS"], edge_types:["ASPECTS_3RD","ASPECTS_4TH","ASPECTS_8TH"]}',
    'Yoga membership: {seeds:["YOG.SARASWATI"], edge_types:["YOGA_MEMBERSHIP"]}',
  ],
  cost_tier: 'medium',
  requires_temporal: false,
}

const manifest_query: RetrievalCapabilityEntry = {
  tool_name: 'manifest_query',
  description:
    'Look up entries in CAPABILITY_MANIFEST.json by canonical_id, layer, status, or path substring. Use this only when the user asks meta-questions about the corpus itself ("what artifacts cover topic X?").',
  data_surface:
    'Governance — CAPABILITY_MANIFEST.json entries (~112 rows). Returns matching AssetEntry rows with path, layer, status, fingerprint, preferred_for tags.',
  supported_params:
    '{ canonical_ids?: string[]; layer?: string; status?: string; path_substring?: string; preferred_for?: string[]; limit?: number (default 20) }',
  optimal_patterns: [
    'Meta-corpus: {layer:"L2.5", status:"CURRENT"}',
    'Domain reports: {path_substring:"REPORT_", limit:30}',
    'Lookup by id: {canonical_ids:["MSR_v3_0","UCN_v4_0"]}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const vector_search: RetrievalCapabilityEntry = {
  tool_name: 'vector_search',
  description:
    'Semantic search across the embedded corpus (L1 facts, UCN sections, MSR signals, CDLM cells, CGM nodes, domain reports, remedial codex). Always include for factual / interpretive / holistic / cross_domain queries; skip for pure predictive (timing) queries.',
  data_surface:
    'Multi-layer — pgvector indexes over: l1_fact, ucn_section, msr_signal, cdlm_cell, cgm_node, domain_report, rm_element, l4_remedial. Returns top-k semantically similar chunks with source_canonical_id and significance.',
  supported_params:
    '{ query_hint?: string (additional retrieval hint); doc_type?: ("l1_fact"|"ucn_section"|"msr_signal"|"cdlm_cell"|"cgm_node"|"domain_report"|"rm_element"|"l4_remedial")[]; layer?: ("L1"|"L2.5"|"L3"|"L4"|"L5"); top_k?: number (default 20, max 50) }',
  optimal_patterns: [
    'Factual lookup: {layer:"L1", doc_type:["l1_fact"], top_k:10}',
    'Interpretive synthesis: {doc_type:["l1_fact","ucn_section","msr_signal","cdlm_cell"], top_k:25}',
    'Discovery: {doc_type:["msr_signal","ucn_section","domain_report"], top_k:30}',
    'Remedial: {doc_type:["l4_remedial","domain_report"], top_k:15}',
    'Holistic (omit filter for breadth): {top_k:40}',
  ],
  cost_tier: 'medium',
  requires_temporal: false,
}

// ────────────────────────────────────────────────────────────────────────────
// L1 quantitative chart-fact tools
// ────────────────────────────────────────────────────────────────────────────

const chart_facts_query: RetrievalCapabilityEntry = {
  tool_name: 'chart_facts_query',
  description:
    'PRIMARY tool for quantitative chart-fact retrieval — queries 795 chart_facts rows across 37 categories (shadbala, ashtakavarga, bhava bala, sahams, yogas, longevity indicators, upagrahas, mrityu bhaga, avastha, planet placements, house contents). Use for any strength ranking, BAV bindu count, yoga register lookup, or quantitative placement question.',
  data_surface:
    'L1 — chart_facts table (795 rows × 37 categories). Each row has category, planet, house, sign, nakshatra, divisional_chart, value, ranking_field.',
  supported_params:
    '{ category?: string (e.g. "shadbala","ashtakavarga_bav","bhava_bala","saham","yoga","planet","house","longevity_indicator","upagraha","mrityu_bhaga","avastha"); planet?: string; house?: number; sign?: string; nakshatra?: string; divisional_chart?: string ("D1".."D60"); keyword?: string; rank_by?: string; limit?: number (default 10, range 5–20) }',
  optimal_patterns: [
    'Strength ranking: {category:"shadbala", rank_by:"total_rupas", limit:9}',
    'BAV by planet+sign: {category:"ashtakavarga_bav", planet:"Mars", sign:"Capricorn"}',
    'Yoga register: {category:"yoga"}',
    'Saham lookup: {category:"saham", keyword:"Vivaha"}',
    'House contents: {category:"house", house:7}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const kp_query: RetrievalCapabilityEntry = {
  tool_name: 'kp_query',
  description:
    'KP (Krishnamurti Paddhati) cusp and planet significator lookup. Returns star-lord / sub-lord chains and cusp significators. Use ONLY for KP-system queries — do not use for traditional Vedic queries.',
  data_surface:
    'L1 — kp_significators table. Returns cusp/planet → star-lord, sub-lord, sub-sub-lord chain + significator houses.',
  supported_params:
    '{ cusp?: number (1–12); planet?: string; depth?: number (1–4, default 3) }',
  optimal_patterns: [
    'Cusp significators: {cusp:7}',
    'Planet significator: {planet:"Saturn"}',
    'Deep chain: {cusp:10, depth:4}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const saham_query: RetrievalCapabilityEntry = {
  tool_name: 'saham_query',
  description:
    'Tajika Saham (Lot / Arabic Part) lookup for all 36 sahams. Use for any lot/part/saham query (Vivaha, Putra, Mrityu, Raja, Dhana, etc.).',
  data_surface:
    'L1 — sahams table. Returns saham name, longitude, sign, house, dispositor, formula.',
  supported_params:
    '{ saham_name?: string; limit?: number (default 36 = all) }',
  optimal_patterns: [
    'Specific saham: {saham_name:"Vivaha"}',
    'All sahams: {} (returns full register)',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const divisional_query: RetrievalCapabilityEntry = {
  tool_name: 'divisional_query',
  description:
    'Divisional chart (varga) placement lookup for D1–D60. Use when a specific varga chart is named (D9 navamsha, D10 dasamsha, D7 saptamsha, etc.).',
  data_surface:
    'L1 — divisional_placements table. Returns varga × planet → sign, house, nakshatra, dispositor.',
  supported_params:
    '{ varga: string ("D1".."D60"); planet?: string; limit?: number (default 9 = all planets) }',
  optimal_patterns: [
    'Full D9: {varga:"D9"}',
    'Single planet: {varga:"D10", planet:"Saturn"}',
    'D60 atmakaraka check: {varga:"D60"}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

const cross_varga_dignity_query: RetrievalCapabilityEntry = {
  tool_name: 'cross_varga_dignity_query',
  description:
    'Returns the §3.15 CSI cross-divisional dignity ledger — per-planet D1/D9/D10 sign + dignity ' +
    '(exalted/debilitated/own_sign/mooltrikona/neutral) and vargottama status. Priority-1 for any ' +
    'query mentioning "navamsha comparison", "strength across charts", "vargottama", "three-state ' +
    'dignity", or "how does X planet behave across charts". Always schedule alongside divisional_query ' +
    'for D9 and D10 to give the synthesis layer the cross-walk it needs.',
  data_surface:
    'L1 — chart_facts CSI.* (§3.15 ledger) + D9.* + D10.* per-planet rows. Returns a structured per-planet ' +
    'record: {planet, d1_sign, d1_dignity, d9_sign, d9_dignity, d10_sign, d10_house, d10_dignity, vargottama, fact_ids}.',
  supported_params:
    '{ planets?: string[] (canonical names: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu; omit for all 9) }',
  optimal_patterns: [
    'All planets: {}',
    'Saturn three-state: {planets:["Saturn"]}',
    'Cross-varga comparison: {planets:["Sun","Moon","Saturn"]}',
    'Vargottama check: {} then filter result by vargottama=true',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

// ────────────────────────────────────────────────────────────────────────────
// L3+ synthesis-document tools
// ────────────────────────────────────────────────────────────────────────────

const domain_report_query: RetrievalCapabilityEntry = {
  tool_name: 'domain_report_query',
  description:
    'Domain synthesis — pulls relevant sections from the L3 domain reports (career_dharma, children, financial, health_longevity, parents, psychology_mind, relationships, spiritual, travel). Use when the query is domain-scoped and expects synthesis (not just raw facts).',
  data_surface:
    'L3 — REPORT_<DOMAIN>_v* documents, indexed by section. Returns matching report sections with provenance.',
  supported_params:
    '{ domains: string[] (canonical: career, dharma, children, financial, wealth, health, longevity, parents, psychology, mind, relationships, marriage, spiritual, travel); keyword?: string; limit?: number (default 8) }',
  optimal_patterns: [
    'Career synthesis: {domains:["career"], limit:6}',
    'Health overview: {domains:["health","longevity"]}',
    'Themed: {domains:["relationships"], keyword:"timing of marriage"}',
  ],
  cost_tier: 'high',
  requires_temporal: false,
}

const remedial_codex_query: RetrievalCapabilityEntry = {
  tool_name: 'remedial_codex_query',
  description:
    'Remedial prescription lookup from the Remedial Codex v2.0 (Parts 1 & 2). Returns gemstones, mantras, yantras, devata practices, dinacharya, and propitiation rituals indexed by planet and practice type.',
  data_surface:
    'L4 — REMEDIAL_CODEX_v2_0_PART1 + PART2 documents. Returns matching remedial entries with planet, practice_type, scripture citation, contraindications.',
  supported_params:
    '{ planet?: string; practice_type?: ("gemstone"|"mantra"|"yantra"|"devata"|"dinacharya"|"propitiation"); keyword?: string; limit?: number (default 6) }',
  optimal_patterns: [
    'Saturn remedies: {planet:"Saturn", limit:8}',
    'Mantras only: {practice_type:"mantra", limit:5}',
    'Specific: {planet:"Mercury", practice_type:"gemstone"}',
  ],
  cost_tier: 'medium',
  requires_temporal: false,
}

const timeline_query: RetrievalCapabilityEntry = {
  tool_name: 'timeline_query',
  description:
    'Life-arc synthesis for a named dasha period. Returns the structural narrative for a specific MD or AD (themes, expected challenges, opportunity windows). Use for long-horizon "what does my X dasha show" questions. IMPORTANT: next MD after Mercury MD is KETU MD (2027-08-21 → 2034-08-21); never suggest Saturn MD as upcoming (Saturn MD was historical 1992–2010).',
  data_surface:
    'L5 — LIFETIME_TIMELINE_v1_0 + per-dasha narrative arcs. Returns the dasha arc structure: themes, sub-period markers, key transits.',
  supported_params:
    '{ dasha_name: string (e.g. "Mercury MD","Ketu MD","Venus MD"); time_window?: {start: ISO_date, end: ISO_date}; limit?: number (default 1) }',
  optimal_patterns: [
    'Current MD arc: {dasha_name:"Mercury MD"}',
    'Upcoming KETU MD: {dasha_name:"Ketu MD"}',
    'Bounded window: {dasha_name:"Mercury MD", time_window:{start:"2026-05-01",end:"2027-08-20"}}',
  ],
  cost_tier: 'medium',
  requires_temporal: true,
}

// ────────────────────────────────────────────────────────────────────────────
// M8-G — Classical corpus tools (tools 25 + 26)
// ────────────────────────────────────────────────────────────────────────────

const classical_text_search: RetrievalCapabilityEntry = {
  tool_name: 'classical_text_search',
  description:
    'Semantic search over the classical Jyotish text corpus — BPHS, Phaladeepika, Saravali, ' +
    'Uttara Kalamrita, Jaimini Sutra, and 5 Tier-3 texts (10 texts, ~7150 chunks). Returns ' +
    'top-K relevant passage chunks with chapter, verse reference, and confidence baseline. ' +
    'Use when the query requires classical textual authority, source verse citation, or ' +
    'cross-tradition validation of astrological principles. Triggers query_class=classical_grounding.',
  data_surface:
    'L8 — tables classical_chunks JOIN classical_texts. ' +
    'Fields: text_key, title, author, tradition, school, tier, chapter, verse_range, content, ' +
    'attribution_baseline_confidence, similarity (1 − cosine_distance from pgvector).',
  supported_params:
    '{ query?: string (default: user query); schools?: string[] (e.g. ["parashari","jaimini","bnn"]); ' +
    'tier_max?: number (1=mandatory, 2=high, 3=standard, 4=nadi/bnn); limit?: number (default 5, max 20) }',
  optimal_patterns: [
    'Classical source for Saturn: {query:"Saturn exalted Libra yoga", tier_max:2, limit:5}',
    'BPHS only: {schools:["parashari"], limit:8}',
    'Nadi/BNN search: {schools:["bnn","nadi"], limit:5}',
    'Classical grounding for career: {query:"tenth house profession Saturn karma", limit:8}',
    'Verse cross-check: {query:"Rahu seventh house partnership", tier_max:3, limit:10}',
  ],
  cost_tier: 'high',
  requires_temporal: false,
}

const classical_attribution_lookup: RetrievalCapabilityEntry = {
  tool_name: 'classical_attribution_lookup',
  description:
    'Structured lookup of MSR signal attributions in the classical_attributions table. ' +
    'For given MSR signal IDs (SIG.MSR.NNN), returns which classical texts confirm, contradict, ' +
    'extend, or are silent on each signal, with chapter, verse_range, confidence tier, and ' +
    'translation cross-check status. Use when the query requires classical authority for specific ' +
    'MSR signals or to show the user which texts support/refute a given astrological claim.',
  data_surface:
    'L8 — table classical_attributions JOIN classical_chunks JOIN classical_texts. ' +
    'Fields: msr_signal_id, text_key, title, author, chapter, verse_range, content, ' +
    'attribution_type (confirms/contradicts/partial/extends/silent), confidence, confidence_tier ' +
    '(HIGH/MEDIUM/LOW), derivation_notes, translation_cross_checked.',
  supported_params:
    '{ signal_ids: string[] (required, e.g. ["SIG.MSR.001","SIG.MSR.042"]); ' +
    'attribution_type?: "confirms"|"contradicts"|"partial"|"extends"|"silent"; ' +
    'confidence_tier?: "HIGH"|"MEDIUM"|"LOW" }',
  optimal_patterns: [
    'All attributions for a signal: {signal_ids:["SIG.MSR.001"]}',
    'Only confirmations: {signal_ids:["SIG.MSR.042"], attribution_type:"confirms"}',
    'High-confidence citations only: {signal_ids:["SIG.MSR.001","SIG.MSR.042"], confidence_tier:"HIGH"}',
    'Check classical basis: {signal_ids:["SIG.MSR.100","SIG.MSR.200","SIG.MSR.300"]}',
  ],
  cost_tier: 'low',
  requires_temporal: false,
}

// ────────────────────────────────────────────────────────────────────────────
// Registry — preserves the order from RETRIEVAL_TOOLS in retrieve/index.ts
// ────────────────────────────────────────────────────────────────────────────

export const RETRIEVAL_CAPABILITY_SPEC: readonly RetrievalCapabilityEntry[] = [
  msr_sql,
  pattern_register,
  resonance_register,
  cluster_atlas,
  contradiction_register,
  temporal,
  query_msr_aggregate,
  cgm_graph_walk,
  manifest_query,
  vector_search,
  kp_query,
  saham_query,
  divisional_query,
  chart_facts_query,
  cross_varga_dignity_query,
  domain_report_query,
  remedial_codex_query,
  timeline_query,
  classical_text_search,
  classical_attribution_lookup,
] as const

/**
 * Render the spec as a single string suitable for embedding in the planner
 * system prompt. Each tool gets a clearly-delimited block so the LLM can
 * scan and reference them by name.
 */
export function renderRetrievalCapabilitySpec(
  spec: readonly RetrievalCapabilityEntry[] = RETRIEVAL_CAPABILITY_SPEC,
): string {
  return spec
    .map((e) => {
      const patterns = e.optimal_patterns.map((p) => `  - ${p}`).join('\n')
      return [
        `### ${e.tool_name}`,
        e.description,
        '',
        `**Data surface:** ${e.data_surface}`,
        `**Params:** ${e.supported_params}`,
        `**Cost tier:** ${e.cost_tier}${e.requires_temporal ? ' · requires temporal context' : ''}`,
        `**Optimal patterns:**`,
        patterns,
      ].join('\n')
    })
    .join('\n\n')
}

/** Lookup helper. */
export function getCapability(toolName: string): RetrievalCapabilityEntry | undefined {
  return RETRIEVAL_CAPABILITY_SPEC.find((e) => e.tool_name === toolName)
}

// ────────────────────────────────────────────────────────────────────────────
// DOMAIN_VARGA_MAP — domain → divisional chart routing (VARGA-ETL-FULL-S1 D18)
// ────────────────────────────────────────────────────────────────────────────

/**
 * Mapping from canonical (and alias) domain codes to the divisional charts that
 * MUST appear in retrieval context for a domain-scoped query, and the secondary
 * vargas that strengthen the read.
 *
 * Used by the planner to schedule `divisional_query` for the mandatory vargas
 * and (where applicable) `cross_varga_dignity_query` alongside them. Used by
 * the synthesis layer (DIVISIONAL_INTEGRATION_GATE) to decide whether the
 * mandatory varga context is present before answering.
 *
 * Canonical keys are the L3 domain-report names (career_dharma, health_longevity,
 * etc.). Aliases (career, marriage, etc.) resolve to the same entry to keep the
 * planner robust against naming drift.
 */
export interface DomainVargaEntry {
  /** Vargas that MUST appear in the retrieval bundle for an acharya-grade read. */
  mandatory: readonly string[]
  /** Vargas that materially strengthen the read but are not blocking. */
  secondary: readonly string[]
}

export const DOMAIN_VARGA_MAP: Readonly<Record<string, DomainVargaEntry>> = {
  // Career / status (D10 dasamsha)
  career: { mandatory: ['D10'], secondary: ['D9'] },
  career_dharma: { mandatory: ['D10', 'D9'], secondary: ['D24'] },
  status: { mandatory: ['D10'], secondary: ['D9'] },

  // Dharma / marriage / relationships (D9 navamsha)
  dharma: { mandatory: ['D9'], secondary: ['D10'] },
  marriage: { mandatory: ['D9'], secondary: ['D7'] },
  partner: { mandatory: ['D9'], secondary: ['D7'] },
  relationships: { mandatory: ['D9'], secondary: ['D7', 'D10'] },

  // Children (D7 saptamsha)
  children: { mandatory: ['D7'], secondary: ['D9'] },

  // Parents / ancestry (D12 dvadashamsa)
  parents: { mandatory: ['D12'], secondary: ['D9'] },
  ancestry: { mandatory: ['D12'], secondary: ['D60'] },

  // Education / knowledge (D24 siddhamsa)
  education: { mandatory: ['D24'], secondary: ['D9'] },
  knowledge: { mandatory: ['D24'], secondary: ['D9'] },

  // Spiritual / moksha (D20 vimsamsha)
  spiritual: { mandatory: ['D20'], secondary: ['D9', 'D60'] },
  moksha: { mandatory: ['D20'], secondary: ['D9', 'D60'] },
  spirit: { mandatory: ['D20'], secondary: ['D9'] },

  // Health / longevity (D30 trimsamsha)
  health: { mandatory: ['D30'], secondary: ['D9'] },
  longevity: { mandatory: ['D30'], secondary: ['D9'] },
  health_longevity: { mandatory: ['D30'], secondary: ['D9'] },

  // Finance / wealth (D2 hora)
  finance: { mandatory: ['D2'], secondary: ['D9', 'D10'] },
  wealth: { mandatory: ['D2'], secondary: ['D9', 'D10'] },
  financial: { mandatory: ['D2'], secondary: ['D9', 'D10'] },

  // Vehicles / comforts (D16 shodashamsha)
  vehicles_comforts: { mandatory: ['D16'], secondary: ['D9'] },
  comforts: { mandatory: ['D16'], secondary: ['D9'] },

  // Auspiciousness (D40 khavedamsha)
  auspiciousness: { mandatory: ['D40'], secondary: ['D9'] },

  // Purity (D45 akshavedamsha)
  purity: { mandatory: ['D45'], secondary: ['D9'] },

  // Past karma (D60 shashtyamsha) — D60 mandatory; D45 + D9 strengthen
  past_karma: { mandatory: ['D60'], secondary: ['D45', 'D9'] },
} as const

/** Resolve a domain code (or alias) to its mandatory + secondary vargas. */
export function getDomainVargas(domain: string): DomainVargaEntry | undefined {
  return DOMAIN_VARGA_MAP[domain]
}
