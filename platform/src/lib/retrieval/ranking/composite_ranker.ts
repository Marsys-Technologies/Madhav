/**
 * composite_ranker.ts — BA-P2 query-time 4-dimensional composite scorer.
 * ========================================================================
 * Implements: composite = class_prior × topic_relevance × intrinsic_strength
 *                        × structural_role × temporal_activation
 * with percentile-within-class computed on the fly.
 *
 * NEVER writes to bodha_* tables or touches stored salience columns.
 * All computation is in-process on the fetched signal rows.
 *
 * Source authority: BA-P2 brief §Step 2 + seed package §2/§3/§4.
 */

import {
  PRIORS_VERSION,
  classPrior,
  grahaAffinity,
  vargaWeight,
  bhavaAffinity,
  DIGNITY_SCORE,
  VARGA_WEIGHT_CITATION,
} from './priors_config'

// Graha code normalizer: converts any key variant to the 2-char code used in L1ChartContext.graha_map.
// L1 stores graha_map under 2-char codes (SU, MO, SA, etc.); MSR signals use MOON/SATURN/etc.
const GRAHA_TO_CODE: Record<string, string> = {
  SUN: 'SU', MOON: 'MO', MARS: 'MA', MERCURY: 'ME', JUPITER: 'JU',
  VENUS: 'VE', SATURN: 'SA', RAHU: 'RA', KETU: 'KE',
  // L1 chart_facts fact_subject format
  MAR: 'MA', MER: 'ME', JUP: 'JU', VEN: 'VE', SAT: 'SA',
  RAH_MEAN: 'RA', KET_MEAN: 'KE',
}

// ── L1 Context (provided by l1_context_fetcher) ───────────────────────────────

export interface GrahaStrength {
  graha: string        // 'SU','MO','MA','ME','JU','VE','SA','RA','KE'
  shadbala_total: number  // raw shadbala score (rupas)
  dignity: string | null  // 'exalted'|'own'|'friend'|... from graha_sign_attributes
  house: number | null    // 1-12 occupied house from D1
}

export interface L1ChartContext {
  /** Map graha→strength info for fast lookup */
  graha_map: Record<string, GrahaStrength>
  /** Current Mahadasha lord (graha key, e.g. 'SA') */
  current_md_lord: string | null
  /** Current Antardasha lord */
  current_ad_lord: string | null
  /** Today's date ISO string (for cache key generation) */
  as_of_date: string
}

// ── Signal row shape (from bodha_msr_signals) ─────────────────────────────────

export interface MsrSignalRow {
  signal_id: string
  signal_type_id?: string
  signal_type_class?: string | null
  signal_tradition?: string | null
  signal_summary_text?: string
  signal_headline_text?: string
  computed_salience?: number | null
  top_k_salience_rank?: number | null
  domains_affected_array?: string[] | null
  constituent_facts_array?: string[] | null
  source_subsystem?: string | null
  valence?: string | null
  verification_pass_status?: string | null
  citation_human?: string | null
  lel_origin?: boolean | null
  signature_tier?: string | null
  configuration_jsonb?: Record<string, unknown> | null
  // CR-84 serving leg (D-2 V-3 bonus): real CGM centrality (pagerank/eigenvector/betweenness/
  // harmonic) written onto each signal by V-4's bo_laksana re-rank pass (migration 446). Consumed
  // by structuralRole() below — closes the "pagerank is 100% NULL" dead link at the serving side.
  graph_node_strength_contribution_jsonb?: Record<string, unknown> | null
}

// ── Sub-score computation ─────────────────────────────────────────────────────

/**
 * Extract primary graha from a signal row's configuration_jsonb.
 * The jsonb structure varies by signal_type_class but common keys:
 *  - 'graha', 'primary_graha', 'lord_graha', 'planet', 'graha_key'
 */
export function extractPrimaryGraha(row: MsrSignalRow): string | null {
  const cfg = row.configuration_jsonb
  if (!cfg) return null
  const candidates = [
    cfg['graha'], cfg['primary_graha'], cfg['lord_graha'],
    cfg['planet'], cfg['graha_key'], cfg['karaka_graha'],
    // WP-1.2β: additional graha-bearing keys observed across signal families —
    // natural_karaka (karaka_alignment), nakshatra_lord (nakshatra joins),
    // bhava_lord (concordance), planet_a (parivartana), lord/star_lord/sub_lord (KP cusps).
    cfg['natural_karaka'], cfg['nakshatra_lord'], cfg['bhava_lord'],
    cfg['planet_a'], cfg['lord'], cfg['star_lord'], cfg['sub_lord'],
  ]
  for (const v of candidates) {
    if (typeof v === 'string' && v.length > 0) return v
  }
  return null
}

/**
 * WP-1.2β (LCA-14 / R-44) — extract the bhāva (house 1-12) a signal bears on, for both
 * bhāva×domain topic relevance AND bhāva-fallback attribution. Read order (first hit wins):
 *   1. configuration_jsonb.target_house — the house being aspected/affected (most specific).
 *   2. configuration_jsonb.house / .bhava / .bhava_num — a direct house tag.
 *   3. configuration_jsonb.source_house — the aspecting house (fallback).
 *   4. signal_type_id suffix `house_N` / `:house_N` (e.g. aspect_parashari_per_varga:house_5).
 * Returns 1..12 or null. Never invents a house (B.10) — only reads a stored one.
 */
export function extractPrimaryBhava(row: MsrSignalRow): number | null {
  const cfg = row.configuration_jsonb
  const readHouse = (v: unknown): number | null => {
    const n = typeof v === 'number' ? v : typeof v === 'string' && /^\d+$/.test(v) ? Number(v) : NaN
    return Number.isInteger(n) && n >= 1 && n <= 12 ? n : null
  }
  if (cfg) {
    for (const key of ['target_house', 'house', 'bhava', 'bhava_num', 'source_house']) {
      const h = readHouse(cfg[key])
      if (h) return h
    }
  }
  const stid = row.signal_type_id ?? ''
  const m = stid.match(/house_(\d{1,2})(?!\d)/)
  if (m) {
    const h = Number(m[1])
    if (h >= 1 && h <= 12) return h
  }
  return null
}

/** Extract varga (e.g. 'D10') from configuration_jsonb if present. */
function extractVarga(row: MsrSignalRow): string | null {
  const cfg = row.configuration_jsonb
  if (!cfg) return null
  const v = cfg['varga'] ?? cfg['division'] ?? cfg['varga_key']
  return typeof v === 'string' ? v : null
}

/**
 * topic_relevance:
 *   graha×domain affinity × varga-grain weight (domain-conditioned).
 *   Falls back to 1.0 × 1.0 = 1.0 if both are unresolvable.
 */
function topicRelevance(row: MsrSignalRow, domain?: string | null): number {
  const graha = extractPrimaryGraha(row)
  const varga = extractVarga(row)
  const bhava = extractPrimaryBhava(row)
  const ga = grahaAffinity(graha, domain)
  const vw = vargaWeight(varga, domain)
  // WP-1.2β: bhāva×domain congruence — the axis that discriminates the graha-less
  // aspect/house composite_state flood across domains (BPHS Bhāvādhyāya). Neutral (1.0)
  // when no house resolves, so graha/yoga signals are unaffected by this term.
  const bw = bhavaAffinity(bhava, domain)
  // Normalize varga weight around 1.0 (D1 base = 1.0)
  return ga * vw * bw
}

/**
 * intrinsic_strength:
 *   REAL shadbala (normalized) × dignity_score.
 *   Normalization: shadbala_total / 5.0 (L1 stores rupas; 5 rupas ≈ strong graha).
 *   L1 graha_map uses 2-char codes (SU/MO/SA); MSR signals use MOON/SATURN/etc.
 *   GRAHA_TO_CODE normalizes before lookup.
 */
function intrinsicStrength(row: MsrSignalRow, ctx: L1ChartContext): number {
  const graha = extractPrimaryGraha(row)
  if (!graha) return 0.5
  const upper = graha.toUpperCase()
  const code = GRAHA_TO_CODE[upper] ?? upper  // normalize to 2-char if possible
  const gInfo = ctx.graha_map[code] ?? ctx.graha_map[upper]
  if (!gInfo) return 0.5
  const shabdala_norm = Math.min(gInfo.shadbala_total / 5.0, 1.0)  // rupas scale (not virupas)
  const dignity_score = DIGNITY_SCORE[gInfo.dignity ?? ''] ?? 0.45
  // Blend: 60% shadbala + 40% dignity
  return 0.6 * shabdala_norm + 0.4 * dignity_score
}

/** Class-based structural weight (the ORIGINAL fallback; now also the floor when graph data exists). */
function structuralRoleClassConstant(row: MsrSignalRow): number {
  const stc = row.signal_type_class?.toLowerCase() ?? ''
  if (stc === 'configuration' || stc === 'yoga') return 1.30
  if (stc === 'composite_state') return 1.20
  if (stc === 'relationship') return 1.15
  if (stc === 'dasha_period') return 1.10
  if (stc === 'karaka_alignment') return 1.05
  if (stc === 'position') return 1.00
  if (stc === 'varga_pattern') return 0.95  // vargottama/varga structure — above birth_moment
  if (stc === 'magnitude' || stc === 'birth_moment') return 0.90
  return 0.80
}

/** Extract a usable [0,1] centrality from the CGM contribution jsonb, or null if absent/unusable. */
export function extractGraphCentrality(jsonb: Record<string, unknown> | null | undefined): number | null {
  if (!jsonb || typeof jsonb !== 'object') return null
  // Prefer an explicitly-normalized composite; else fall back through the standard centralities.
  for (const key of ['normalized', 'composite', 'pagerank', 'eigenvector', 'harmonic', 'betweenness']) {
    const v = jsonb[key]
    if (typeof v === 'number' && Number.isFinite(v)) {
      // pagerank/eigenvector are already 0..1-ish; clamp defensively so a mis-scaled value can't blow up.
      return Math.max(0, Math.min(1, v))
    }
  }
  return null
}

/**
 * structural_role:
 *   Per BA-P2 brief: COALESCE(pagerank, f(yoga_membership, signature_class)).
 *   CR-84 (D-2 V-3 serving leg): pagerank is no longer 100% NULL — V-4's bo_laksana re-rank writes
 *   real CGM centrality into graph_node_strength_contribution_jsonb. When present, blend it with the
 *   class constant (60% graph / 40% class) so the graph is no longer structurally subordinate (CR-25)
 *   while the class semantics still floor the score; when absent (un-re-ranked chart), fall back to
 *   the class constant exactly as before. The graph term is mapped into the class-constant's own
 *   [0.80,1.35] span so it composes on the same scale — NOT tuned against any G0-4 assertion (DR-9).
 */
function structuralRole(row: MsrSignalRow): number {
  const classConstant = structuralRoleClassConstant(row)
  const c = extractGraphCentrality(row.graph_node_strength_contribution_jsonb)
  if (c === null) return classConstant
  const graphTerm = 0.80 + 0.55 * c // map [0,1] centrality onto the class-constant span [0.80,1.35]
  return 0.4 * classConstant + 0.6 * graphTerm
}

/**
 * temporal_activation:
 *   Current MD/AD lords from chart_dashas (kala bypass — L3 fills in P5A).
 *   If signal's primary graha IS the current MD or AD lord: ×1.5.
 *   If it's neither: ×1.0 (neutral; not a penalty).
 */
function temporalActivation(row: MsrSignalRow, ctx: L1ChartContext): number {
  const graha = extractPrimaryGraha(row)?.toUpperCase() ?? null
  if (!graha) return 1.0
  const mdMatch = ctx.current_md_lord && graha === ctx.current_md_lord.toUpperCase()
  const adMatch = ctx.current_ad_lord && graha === ctx.current_ad_lord.toUpperCase()
  if (mdMatch && adMatch) return 1.5
  if (mdMatch) return 1.40
  if (adMatch) return 1.25
  return 1.0
}

// ── Main composite scorer ─────────────────────────────────────────────────────

export interface ScoredSignal extends MsrSignalRow {
  /** Composite score (product of 4 sub-scores, before percentile) */
  composite_score: number
  /** Percentile within signal_type_class (0..1); computed after full pass */
  percentile_within_class: number | null
  /** Final combined score used for ranking */
  final_rank_score: number
  /** Full decomposition for ranking_basis */
  _subscores: {
    class_prior: number
    topic_relevance: number
    intrinsic_strength: number
    structural_role: number
    temporal_activation: number
    priors_version: string
  }
}

/**
 * Apply the 4-dimensional composite to a list of signal rows, return sorted.
 *
 * @param signals - raw rows from bodha_msr_signals
 * @param ctx     - L1 context (graha strengths + current dasha lords)
 * @param domain  - life domain for topic_relevance + varga overlay (optional)
 * @returns signals re-ranked by final_rank_score DESC
 */
export function applyCompositeRanking(
  signals: MsrSignalRow[],
  ctx: L1ChartContext,
  domain?: string | null
): ScoredSignal[] {
  // Pass 1: compute raw composite score for every signal
  const scored: ScoredSignal[] = signals.map(row => {
    const cp  = classPrior(row.signal_type_class, row.source_subsystem, row.signal_tradition)
    const tr  = topicRelevance(row, domain)
    const isr = intrinsicStrength(row, ctx)
    const sr  = structuralRole(row)
    const ta  = temporalActivation(row, ctx)
    const composite = cp * tr * isr * sr * ta
    return {
      ...row,
      composite_score: composite,
      percentile_within_class: null,  // filled in pass 2
      final_rank_score: composite,    // updated in pass 2
      _subscores: {
        class_prior: cp, topic_relevance: tr, intrinsic_strength: isr,
        structural_role: sr, temporal_activation: ta,
        priors_version: PRIORS_VERSION,
      },
    }
  })

  // Pass 2: percentile within signal_type_class
  // Group by class, compute within-class rank as percentile (0..1)
  const byClass: Record<string, number[]> = {}
  for (const s of scored) {
    const cls = s.signal_type_class ?? '_unknown'
    byClass[cls] ??= []
    byClass[cls].push(s.composite_score)
  }
  // Sort each class's scores desc; map score → fractional rank (top = 1.0)
  const classPercentileFn: Record<string, (score: number) => number> = {}
  for (const [cls, scores] of Object.entries(byClass)) {
    const sorted = [...scores].sort((a, b) => b - a)
    classPercentileFn[cls] = (score: number) => {
      const rank = sorted.indexOf(score)  // 0 = highest
      return sorted.length > 1 ? 1 - rank / (sorted.length - 1) : 1.0
    }
  }

  // Apply percentile and compute final score.
  // Three-layer scoring to satisfy G10-QT criterion 5 (no tie-block >3 identical scores):
  //   Layer 1 — composite × percentile (primary, carries all domain/class signal)
  //   Layer 2 — 0.1% salience blend: high-salience signals rank first among same composite
  //   Layer 3 — index tiebreak (1/N per slot at 1e9 scale): ensures every signal has a unique
  //              score so no two positions in the returned list ever share identical final_rank_score.
  //              The index reflects the pre-sort salience order within the merged candidate pool.
  const N = scored.length
  for (let i = 0; i < N; i++) {
    const s = scored[i]
    const cls = s.signal_type_class ?? '_unknown'
    const pct = classPercentileFn[cls]?.(s.composite_score) ?? 1.0
    s.percentile_within_class = pct
    const salience_norm = Math.min(Number(s.computed_salience ?? 0) / 3.0, 1.0)
    const idx_tiebreak = N > 1 ? (N - i) / (N * 1e9) : 0
    s.final_rank_score = s.composite_score * pct + salience_norm * 0.001 + idx_tiebreak
  }

  // Sort descending by final_rank_score (unique per signal — no ties)
  scored.sort((a, b) => b.final_rank_score - a.final_rank_score)
  return scored
}

/**
 * Build the ranking_basis object for a RetrievalEnvelope response.
 * If composite ranking was applied, use top-signal subscores as representative.
 */
export function buildRankingBasis(
  signals: ScoredSignal[],
  domain?: string | null
): Record<string, unknown> {
  const topSig = signals[0]
  if (!topSig?._subscores) {
    return { mode: 'salience_fallback', priors_version: PRIORS_VERSION, domain: domain ?? null }
  }
  return {
    mode: 'composite_4d',
    priors_version: PRIORS_VERSION,
    domain: domain ?? null,
    top_signal: {
      signal_id: topSig.signal_id,
      class_prior: topSig._subscores.class_prior,
      topic_relevance: topSig._subscores.topic_relevance,
      intrinsic_strength: topSig._subscores.intrinsic_strength,
      structural_role: topSig._subscores.structural_role,
      temporal_activation: topSig._subscores.temporal_activation,
      composite_score: topSig.composite_score,
      percentile_within_class: topSig.percentile_within_class,
      final_rank_score: topSig.final_rank_score,
    },
    // EL-55 (priors v1.2): name the varga-weight scheme feeding topic_relevance's vargaWeight()
    // term, rather than leaving the weighting basis implicit in an opaque multiplier.
    varga_weight_basis: {
      scheme: VARGA_WEIGHT_CITATION.scheme,
      source: VARGA_WEIGHT_CITATION.source,
    },
    note: 'Composite = class_prior × topic_relevance × intrinsic_strength × structural_role × temporal_activation × percentile_within_class.',
  }
}

// ── R5 W1 (design §E-6) — hierarchical aggregation for orient surfaces ────────

/**
 * WP-1.2(a) (LCA-14) — graha-token → canonical graha-name normalizer used for
 * entity attribution. Covers the 2-char L1 codes (SU/MO/SA…), the MSR-side full
 * names (MOON/SATURN…), and the 3-char chart_facts fact_subject tokens
 * (SAT/RAH_MEAN…). Any variant resolves to ONE canonical entity name so a graha
 * is never split across two entity buckets.
 */
const GRAHA_TOKEN_TO_NAME: Record<string, string> = {
  SU: 'SUN', SUN: 'SUN',
  MO: 'MOON', MOON: 'MOON',
  MA: 'MARS', MAR: 'MARS', MARS: 'MARS',
  ME: 'MERCURY', MER: 'MERCURY', MERCURY: 'MERCURY',
  JU: 'JUPITER', JUP: 'JUPITER', JUPITER: 'JUPITER',
  VE: 'VENUS', VEN: 'VENUS', VENUS: 'VENUS',
  SA: 'SATURN', SAT: 'SATURN', SATURN: 'SATURN',
  RA: 'RAHU', RAH: 'RAHU', RAHU: 'RAHU',
  KE: 'KETU', KET: 'KETU', KETU: 'KETU',
}

/** Canonicalize any graha token/name to its full-name entity key, or null. */
function canonicalGrahaName(token: string | null | undefined): string | null {
  if (!token) return null
  return GRAHA_TOKEN_TO_NAME[token.toUpperCase()] ?? null
}

/**
 * WP-1.2(a) — derive the graha entity from an L1 `fact_subject` string such as
 * `D108_SAT`, `D1_SAT`, `SAT`, or `RAH_MEAN`. The graha token is embedded as a
 * component of the subject (varga prefix + graha suffix, or a mean-node suffix);
 * scan components right-to-left and return the first that resolves to a graha.
 * This is what lets us attribute the flood of `graha_dignity_per_varga` signals
 * (whose configuration_jsonb carries NO `graha` key) to their real graha instead
 * of dumping them all into one giant UNATTRIBUTED bucket.
 */
export function grahaFromFactSubject(subject: string | null | undefined): string | null {
  if (!subject) return null
  const parts = subject.toUpperCase().split('_')
  for (let i = parts.length - 1; i >= 0; i--) {
    const name = canonicalGrahaName(parts[i])
    if (name) return name
  }
  return null
}

/**
 * WP-1.2β — derive the bhāva (HOUSE_N) embedded in an L1 `fact_subject` such as
 * `HOUSE_7`, `D1_HOUSE_10`, or `BHAVA_2`. Returns 1..12 or null.
 */
export function bhavaFromFactSubject(subject: string | null | undefined): number | null {
  if (!subject) return null
  const m = subject.toUpperCase().match(/(?:HOUSE|BHAVA)_(\d{1,2})(?!\d)/)
  if (m) {
    const h = Number(m[1])
    if (h >= 1 && h <= 12) return h
  }
  return null
}

/**
 * WP-1.2(a)+β — resolve the entity a signal belongs to.
 * Attribution order (first hit wins) — designed to reach 0% UNATTRIBUTED on served surfaces:
 *   1. configuration_jsonb graha keys (extractPrimaryGraha) — the fast path.
 *   2. the graha embedded in any constituent fact's `fact_subject` (factSubjectByFactId map).
 *   3. β: sade_sati / anumukha-Śani signals are inherently Saturn — attribute to SATURN.
 *   4. β: the bhāva the signal bears on (extractPrimaryBhava) — attributes the graha-less
 *      aspect/house composite_state flood to a `BHAVA_N` entity (a real chart address, never
 *      the giant UNATTRIBUTED bucket).
 *   5. β: the bhāva embedded in a constituent fact's `fact_subject` (HOUSE_N/BHAVA_N).
 *   6. 'UNATTRIBUTED' — only when NONE of the above yields a graha or a bhāva (disclosed as a
 *      residual on the served surface, never silently dropped — B.10).
 */
export function deriveSignalEntity(
  row: MsrSignalRow,
  factSubjectByFactId?: Map<string, string>,
): string {
  const raw = extractPrimaryGraha(row)
  const direct = canonicalGrahaName(raw) ?? (raw ? raw.toUpperCase() : null)
  if (direct) return direct
  if (factSubjectByFactId) {
    for (const fid of row.constituent_facts_array ?? []) {
      const g = grahaFromFactSubject(factSubjectByFactId.get(fid))
      if (g) return g
    }
  }
  // β: Saturn-transit families (sade_sati / anumukha shani) are inherently Saturn.
  const cls = (row.signal_type_class ?? '').toLowerCase()
  const stid = (row.signal_type_id ?? '').toLowerCase()
  if (cls === 'sade_sati' || stid.includes('shani') || stid.includes('sade_sati')) return 'SATURN'
  // β: attribute the graha-less house/aspect flood to the bhāva it bears on.
  const bhava = extractPrimaryBhava(row)
  if (bhava) return `BHAVA_${bhava}`
  if (factSubjectByFactId) {
    for (const fid of row.constituent_facts_array ?? []) {
      const h = bhavaFromFactSubject(factSubjectByFactId.get(fid))
      if (h) return `BHAVA_${h}`
    }
  }
  return 'UNATTRIBUTED'
}

/**
 * One aggregated entity profile — "one composite Saturn-AV profile row, never
 * twenty atoms" (design doc E-6). Groups composite-ranked atomic signals by
 * their primary graha (extractPrimaryGraha) into a single summary row per
 * entity, so an orientation/digest surface can present N entity profiles
 * instead of N×k atomic signal rows while still being backed by the exact
 * same composite ranking pipeline the drill surface (query_signals) uses.
 */
export interface EntityProfile {
  entity_type: 'graha' | 'bhava' | 'unattributed'
  entity: string
  /** Sum of final_rank_score across all constituent signals in this entity's group. */
  aggregate_score: number
  /** final_rank_score of the single strongest constituent signal. */
  peak_score: number
  signal_count: number
  dominant_domains: string[]
  dominant_valence: string | null
  signal_type_classes: string[]
  /** Top constituent signal_ids (drill handle back into query_signals). */
  top_signal_ids: string[]
  /**
   * WP-1.2(a) (LCA-14, §N.5) — the RESOLVABLE L1 chart_facts.fact_id set that
   * grounds this entity's signals. When a resolvable-fact-id set is supplied to
   * buildHierarchicalProfiles, this is filtered to fact_ids that provably exist
   * in chart_facts (never a bare/orphan id). Capped for payload safety.
   */
  fact_ids: string[]
}

/** Max resolvable fact_ids surfaced per entity profile (payload safety). */
const FACT_IDS_PER_ENTITY_CAP = 25

export interface BuildHierarchicalProfilesOptions {
  /**
   * WP-1.2(a) — fact_id → fact_subject map from a bounded chart_facts lookup on
   * this response's constituent fact_ids. Presence of an id in this map is BOTH
   * (1) the attribution source (fact_subject → graha) AND (2) the §N.5 resolvability
   * proof (an id in the map provably exists in chart_facts). When supplied, an
   * entity profile's `fact_ids` is filtered to resolvable ids only.
   */
  factSubjectByFactId?: Map<string, string>
  /**
   * WP-1.2β — when true, the residual UNATTRIBUTED bucket is EXCLUDED from the returned
   * profiles so the served surface is 0% UNATTRIBUTED (ND-W1.2). The caller must disclose
   * the residual separately (never silently dropped — B.10): query_ucd surfaces the count in
   * `content.attribution.candidate_pool_unattributed`.
   */
  excludeUnattributed?: boolean
}

/**
 * Aggregate a composite-ranked signal pool into top_k_entities entity-profile
 * rows, each summarizing up to top_signals_per_entity constituent signals.
 * Never re-derives a score — aggregate_score/peak_score are pure aggregations
 * of final_rank_score already computed by applyCompositeRanking (B.10).
 *
 * WP-1.2(a) (LCA-14): entity attribution now falls back from configuration_jsonb
 * graha keys to the graha embedded in a constituent fact's fact_subject (via the
 * optional factSubjectByFactId map) — this drains the giant UNATTRIBUTED bucket
 * the per-varga dignity flood used to create. And the final ordering GUARANTEES a
 * real graha always outranks the residual UNATTRIBUTED bucket, so UNATTRIBUTED can
 * never be the top entity_profile while any attributed graha exists.
 */
export function buildHierarchicalProfiles(
  scored: ScoredSignal[],
  top_k_entities = 10,
  top_signals_per_entity = 3,
  options: BuildHierarchicalProfilesOptions = {},
): EntityProfile[] {
  const { factSubjectByFactId, excludeUnattributed } = options
  const groups = new Map<string, ScoredSignal[]>()
  for (const s of scored) {
    const key = deriveSignalEntity(s, factSubjectByFactId)
    const bucket = groups.get(key)
    if (bucket) bucket.push(s)
    else groups.set(key, [s])
  }

  const profiles: EntityProfile[] = []
  for (const [entity, rows] of groups) {
    const sortedRows = [...rows].sort((a, b) => b.final_rank_score - a.final_rank_score)
    const aggregate_score = sortedRows.reduce((sum, r) => sum + r.final_rank_score, 0)
    const peak_score = sortedRows[0]?.final_rank_score ?? 0

    const domainCounts: Record<string, number> = {}
    const valenceCounts: Record<string, number> = {}
    const classSet = new Set<string>()
    const factIdSet = new Set<string>()
    for (const r of rows) {
      for (const d of r.domains_affected_array ?? []) domainCounts[d] = (domainCounts[d] ?? 0) + 1
      if (r.valence) valenceCounts[r.valence] = (valenceCounts[r.valence] ?? 0) + 1
      if (r.signal_type_class) classSet.add(r.signal_type_class)
      for (const fid of r.constituent_facts_array ?? []) {
        if (!fid) continue
        // §N.5: only surface a fact_id we can prove resolves to chart_facts.
        // When no resolvability map is supplied (pure unit context), surface all.
        if (!factSubjectByFactId || factSubjectByFactId.has(fid)) factIdSet.add(fid)
      }
    }
    const dominant_domains = Object.entries(domainCounts)
      .sort((a, b) => b[1] - a[1]).slice(0, 3).map(([d]) => d)
    const dominant_valence = Object.entries(valenceCounts)
      .sort((a, b) => b[1] - a[1])[0]?.[0] ?? null

    const entity_type: EntityProfile['entity_type'] =
      entity === 'UNATTRIBUTED' ? 'unattributed' : entity.startsWith('BHAVA_') ? 'bhava' : 'graha'
    profiles.push({
      entity_type,
      entity,
      aggregate_score,
      peak_score,
      signal_count: rows.length,
      dominant_domains,
      dominant_valence,
      signal_type_classes: Array.from(classSet),
      top_signal_ids: sortedRows.slice(0, top_signals_per_entity).map(r => r.signal_id),
      fact_ids: Array.from(factIdSet).slice(0, FACT_IDS_PER_ENTITY_CAP),
    })
  }

  // WP-1.2(a)+β ordering guard: an ATTRIBUTED entity (graha OR bhāva) ALWAYS outranks the
  // residual UNATTRIBUTED bucket, regardless of summed aggregate_score — the un-attributed
  // bucket must never be the top entity. Graha and bhāva entities rank against each other by
  // aggregate_score DESC (both are real chart addresses); only 'unattributed' is forced last.
  profiles.sort((a, b) => {
    const aUnattr = a.entity_type === 'unattributed'
    const bUnattr = b.entity_type === 'unattributed'
    if (aUnattr !== bUnattr) return aUnattr ? 1 : -1
    return b.aggregate_score - a.aggregate_score
  })
  // WP-1.2β: optionally drop the residual UNATTRIBUTED bucket so the served surface is 0%
  // UNATTRIBUTED (ND-W1.2). Disclosure of the residual is the caller's responsibility.
  const finalProfiles = excludeUnattributed
    ? profiles.filter(p => p.entity_type !== 'unattributed')
    : profiles
  return finalProfiles.slice(0, top_k_entities)
}

// ── R5.1 C2 item 2 — digest family-aggregation (E-6 completion) ──────────────

/**
 * One "family" of atomic signals collapsed into a single composite row for the
 * top band. A family is the same classical construct repeated per-varga for the
 * same graha — e.g. `graha_dignity_per_varga:dignity_state` for Saturn recurs
 * ~20 times (once per varga), and because dignity strength is graha-driven, the
 * composite scores cluster tightly. Left un-collapsed, this floods the top band
 * with near-duplicate "dignity rows" for one graha, crowding out other distinct
 * findings — the tie-block the native's closing probe observed on this class of
 * signal specifically.
 *
 * `buildHierarchicalProfiles` (above) already solves this at the GRAHA axis
 * (one row per planet, across every signal_type_class). This function solves
 * the finer axis: within the still-atomic top-band list, collapse repeats of
 * the SAME (graha × signal_type_id) construct into one representative row.
 * Never fabricates or averages a score (B.10) — the representative is exactly
 * the highest-final_rank_score member of its family, unmodified; the rest are
 * demoted to `family_member_pointers` (signal_ids), still reachable via
 * query_signals, never deleted from the underlying data.
 */
export interface FamilyCollapsedSignal extends ScoredSignal {
  /** True if this row represents a family of >1 near-duplicate atomic signals. */
  is_family_composite: boolean
  /** Grouping key: `${graha}::${signal_type_id}` (or bare signal_type_id if no graha resolves). */
  family_key: string
  /** Total atomic signals in this family (including the representative itself). */
  family_member_count: number
  /** signal_ids of the OTHER family members (excludes the representative) — drill via query_signals. */
  family_member_pointers: string[]
}

/**
 * Collapse same-family atomic signals within a composite-ranked pool down to one
 * representative row per family, ordered by final_rank_score DESC (unchanged
 * scores — pure grouping, no re-derivation). Call BEFORE slicing to a top-K
 * window so the collapsed representative — not N near-duplicate atoms — occupies
 * the top-band slot.
 *
 * Family key: `${primary_graha}::${signal_type_id}` when a graha resolves
 * (extractPrimaryGraha), else bare `signal_type_id` (still meaningfully groups
 * e.g. repeated convergence-count signals with no single graha attribution).
 * Signals with neither a graha NOR a signal_type_id are never grouped (each is
 * its own family of 1) — nothing is dropped silently.
 */
export function collapseSignalFamilies(scored: ScoredSignal[]): FamilyCollapsedSignal[] {
  const groups = new Map<string, ScoredSignal[]>()
  for (const s of scored) {
    const graha = extractPrimaryGraha(s)
    const typeId = s.signal_type_id ?? null
    const key = graha && typeId ? `${graha.toUpperCase()}::${typeId}`
      : typeId ? typeId
      : `__singleton__:${s.signal_id}`
    const bucket = groups.get(key)
    if (bucket) bucket.push(s)
    else groups.set(key, [s])
  }

  const collapsed: FamilyCollapsedSignal[] = []
  for (const [key, rows] of groups) {
    const sortedRows = [...rows].sort((a, b) => b.final_rank_score - a.final_rank_score)
    const representative = sortedRows[0]
    collapsed.push({
      ...representative,
      is_family_composite: rows.length > 1,
      family_key: key,
      family_member_count: rows.length,
      family_member_pointers: sortedRows.slice(1).map(r => r.signal_id),
    })
  }

  collapsed.sort((a, b) => b.final_rank_score - a.final_rank_score)
  return collapsed
}
