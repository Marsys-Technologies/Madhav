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
  DIGNITY_SCORE,
} from './priors_config'

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

interface MsrSignalRow {
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
}

// ── Sub-score computation ─────────────────────────────────────────────────────

/**
 * Extract primary graha from a signal row's configuration_jsonb.
 * The jsonb structure varies by signal_type_class but common keys:
 *  - 'graha', 'primary_graha', 'lord_graha', 'planet', 'graha_key'
 */
function extractPrimaryGraha(row: MsrSignalRow): string | null {
  const cfg = row.configuration_jsonb
  if (!cfg) return null
  const candidates = [
    cfg['graha'], cfg['primary_graha'], cfg['lord_graha'],
    cfg['planet'], cfg['graha_key'], cfg['karaka_graha'],
  ]
  for (const v of candidates) {
    if (typeof v === 'string' && v.length > 0) return v
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
  const ga = grahaAffinity(graha, domain)
  const vw = vargaWeight(varga, domain)
  // Normalize varga weight around 1.0 (D1 base = 1.0)
  return ga * vw
}

/**
 * intrinsic_strength:
 *   REAL shadbala (normalized) × dignity_score.
 *   Normalization: shadbala_total / 600 (600 rupa ≈ mean for balanced chart).
 *   If L1 context doesn't have this graha, fall back to 0.5 (neutral).
 */
function intrinsicStrength(row: MsrSignalRow, ctx: L1ChartContext): number {
  const graha = extractPrimaryGraha(row)
  if (!graha) return 0.5
  const canonical = graha.toUpperCase()
  const gInfo = ctx.graha_map[canonical]
  if (!gInfo) return 0.5
  const shabdala_norm = Math.min(gInfo.shadbala_total / 600, 1.0)
  const dignity_score = DIGNITY_SCORE[gInfo.dignity ?? ''] ?? 0.45
  // Blend: 60% shadbala + 40% dignity
  return 0.6 * shabdala_norm + 0.4 * dignity_score
}

/**
 * structural_role:
 *   Per BA-P2 brief: COALESCE(pagerank, f(yoga_membership, signature_class)).
 *   pagerank = 100% NULL (grounding G-5b); fallback is REQUIRED.
 *   Fallback: signal_type_class-based structural weight.
 *     configuration/yoga → 1.30 (chart-backbone: raja/dhana yogas)
 *     composite_state → 1.20 (multi-system)
 *     relationship → 1.15 (argala, parivartana)
 *     dasha_period → 1.10
 *     position/karaka_alignment → 1.00
 *     magnitude/birth_moment → 0.90
 *     others → 0.80
 */
function structuralRole(row: MsrSignalRow): number {
  const stc = row.signal_type_class?.toLowerCase() ?? ''
  if (stc === 'configuration' || stc === 'yoga') return 1.30
  if (stc === 'composite_state') return 1.20
  if (stc === 'relationship') return 1.15
  if (stc === 'dasha_period') return 1.10
  if (stc === 'karaka_alignment') return 1.05
  if (stc === 'position') return 1.00
  if (stc === 'magnitude' || stc === 'birth_moment') return 0.90
  return 0.80
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

  // Apply percentile and compute final score
  for (const s of scored) {
    const cls = s.signal_type_class ?? '_unknown'
    const pct = classPercentileFn[cls]?.(s.composite_score) ?? 1.0
    s.percentile_within_class = pct
    // Final = composite × percentile_within_class (within-class discrimination)
    s.final_rank_score = s.composite_score * pct
  }

  // Sort descending by final_rank_score
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
    note: 'Composite = class_prior × topic_relevance × intrinsic_strength × structural_role × temporal_activation × percentile_within_class.',
  }
}
